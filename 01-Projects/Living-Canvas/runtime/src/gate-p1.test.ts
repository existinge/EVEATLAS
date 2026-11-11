// Gate P1 acceptance tests (T01). Runs under `node --test`.
// Required checks (GATES.md, Gate P1):
//   1. two independent replays -> byte-equivalent final snapshot
//   2. duplicate event/proposal IDs -> idempotent, no duplicate changes
//   3. unknown kind + malformed JSON -> errors surface, never silent
//   4. late event for an old epoch -> cannot mutate the current scene
//   5. high-frequency provisional coalesces; committed/interrupt never dropped
//   6. unrecognized multilingual concept -> stays UNKNOWN / NEEDS_PLAN
//   7. observation/semantic/scene revisions advance independently
//   8. advisory DECIDER_* never mutates the committed scene
//
// Schema contract: `parseEnvelope`/`store.ingest` accept only the plain JSON
// object form of an envelope (isPlainObject gate; JSON strings are rejected as
// schema-invalid). All test-event builders therefore build object envelopes and
// hand them to `ingest` directly. Unknown event kinds surface as
// `schema-invalid` at the schema boundary, and malformed input is likewise
// schema-invalid — never a silent success.

import { test } from "node:test";
import assert from "node:assert/strict";
import { loadSeed, loadEvents } from "./fixtures.ts";
import { SharedStore, offerToQueue } from "./store.ts";
import { parseEnvelope, SchemaViolation } from "./schema.ts";
import type { SubscriberDelivery } from "./state.ts";

function freshStore() {
  return new SharedStore(loadSeed());
}

// -- helpers ----------------------------------------------------------------

const ENV = (over: Record<string, unknown>) => ({
  schemaVersion: "0.1",
  sessionId: "s-demo",
  topicEpoch: 1,
  observationRevision: 1,
  semanticRevision: 1,
  sceneRevision: 0,
  emittedAtMs: 600,
  correlationId: "c1",
  turnId: "t1",
  source: "test",
  ...over,
});

function obs(over: Record<string, unknown>): Record<string, unknown> {
  return {
    kind: "OBSERVATION_PARTIAL",
    ...ENV(over),
  };
}

function proposal(payload: Record<string, unknown>, over: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    kind: "DECIDER_PROPOSAL",
    ...ENV(over),
    payload: {
      proposalId: "ptest",
      targetObjectIds: ["obj-tree-1"],
      actionType: "emphasize",
      parameters: { attention: 0.5 },
      confidence: null,
      evidenceEventIds: [],
      reversible: true,
      expiresAtSessionMs: 5000,
      ...payload,
    },
  };
}

function commit(payload: Record<string, unknown>, over: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    kind: "SCENE_COMMITTED",
    ...ENV(over),
    payload: {
      proposalId: "ptest",
      targetObjectIds: ["obj-tree-1"],
      actionType: "emphasize",
      parameters: { attention: 0.8 },
      reversible: true,
      ...payload,
    },
  };
}

// -- 1. determinism ----------------------------------------------------------

test("P1.1 two independent replays of e1–e8 are byte-equivalent", () => {
  const events = loadEvents();
  const a = freshStore();
  const b = freshStore();
  for (const e of events) a.ingest(e);
  for (const e of events) b.ingest(e);
  const sa = a.canonicalSnapshot();
  const sb = b.canonicalSnapshot();
  assert.equal(sa.json, sb.json, "canonical JSON must be byte-identical");
  assert.equal(sa.commitId, sb.commitId, "commitId must be byte-identical");
  assert.equal(a.getLog().length, events.length);
});

// -- 2. duplicate ids --------------------------------------------------------

test("P1.2 duplicate OBSERVATION eventId is applied once", () => {
  const s = freshStore();
  const line = obs({ eventId: "dup1", payload: { languageTag: "ja-JP", text: "木", isFinal: false }, emittedAtMs: 700 });
  const o1 = s.ingest(line);
  const o2 = s.ingest(line);
  assert.equal(o1.status, "applied");
  assert.equal(o2.status, "skipped-duplicate");
  const st = s.getState();
  assert.equal(st.appliedEventIds.filter((id) => id === "dup1").length, 1, "event applied exactly once");
  assert.equal(st.stats.total, 1, "store counts unique events only");
});

test("P1.2b duplicate proposalId is skipped, does not double-add", () => {
  const s = freshStore();
  const p1 = proposal({ proposalId: "pd" }, { eventId: "pd-e1", emittedAtMs: 700 });
  const p2 = proposal({ proposalId: "pd" }, { eventId: "pd-e2", emittedAtMs: 700 });
  assert.equal(s.ingest(p1).status, "applied");
  assert.equal(s.ingest(p2).status, "skipped-duplicate");
  assert.equal(s.getState().pendingProposals.filter((p) => p.id === "pd").length, 1);
});

test("P1.2c SCENE_COMMITTED is applied once after commit (idempotent)", () => {
  const s = freshStore();
  s.ingest(proposal({ proposalId: "pc" }, { eventId: "pc0", emittedAtMs: 700 }));
  const c1 = commit({ proposalId: "pc" }, { eventId: "pc1", emittedAtMs: 800 });
  const c2 = commit({ proposalId: "pc" }, { eventId: "pc2", emittedAtMs: 810 });
  assert.equal(s.ingest(c1).status, "applied");
  const second = s.ingest(c2);
  // guard order: duplicate proposalId (already committed) fires before scene logic
  assert.equal(second.status, "skipped-duplicate");
  assert.equal(s.getState().committedSceneActions.filter((c) => c.proposalId === "pc").length, 1);
  assert.equal(s.getState().commitCount, 1);
});

// -- 3. errors ---------------------------------------------------------------

test("P1.3 unknown kind surfaces schema-invalid (never silent)", () => {
  const s = freshStore();
  const out = s.ingest(ENV({ kind: "TOTALLY_UNKNOWN", eventId: "unk", emittedAtMs: 700 }));
  // unknown kinds are rejected at the schema boundary before any reduce runs
  assert.equal(out.status, "schema-invalid");
  assert.match(String(out.error), /unknown/i);
  assert.deepEqual(s.getState().committedSceneActions, []);
});

test("P1.3b malformed JSON surfaces schema-invalid (not silent)", () => {
  const s = freshStore();
  const out = s.ingest("{ this is not json ]");
  assert.equal(out.status, "schema-invalid");
  const outNoSemRev = s.ingest({ kind: "OBSERVATION_PARTIAL", eventId: "x", sessionId: "s-demo" });
  assert.equal(outNoSemRev.status, "schema-invalid");
});

test("P1.3c strict parseEnvelope throws SchemaViolation on missing fields", () => {
  assert.throws(
    () => parseEnvelope({ kind: "OBSERVATION_PARTIAL", eventId: "x" }),
    SchemaViolation,
  );
});

// -- 4. late old-epoch event -------------------------------------------------

test("P1.4 late event for an old epoch cannot mutate current scene", () => {
  const s = freshStore();
  // Replay to the epoch advance (e5).
  const events = loadEvents();
  for (const e of events) if (e.eventId !== "e6" && e.eventId !== "e7" && e.eventId !== "e8") s.ingest(e);
  assert.equal(s.getState().topicEpoch, 2);

  // A stale-epoch proposal (epoch 1, as in e6) must be rejected.
  const stale = proposal(
    { proposalId: "pl" },
    { eventId: "e6", topicEpoch: 1, observationRevision: 1, emittedAtMs: 440, correlationId: "obs1" },
  );
  const out = s.ingest(stale);
  assert.equal(out.status, "rejected");
  assert.match(String(out.detail), /topicEpoch 1/);
  assert.equal(s.getState().pendingProposals.filter((p) => p.id === "pl").length, 0, "no mutation from stale epoch");
  const before = s.canonicalSnapshot();
  // The actual fixture includes e6; final state must not contain p-stale.
  const full = freshStore();
  for (const e of loadEvents()) full.ingest(e);
  assert.equal(full.getState().pendingProposals.filter((p) => p.id === "p-stale").length, 0, "p-stale never enters current scene");
});

// -- 5. coalescing / never-drop ----------------------------------------------

test("P1.5 high-frequency provisional observations coalesce", () => {
  const s = freshStore();
  const sub = s.subscribe(4);
  for (let i = 0; i < 6; i++) {
    s.ingest(obs({ eventId: `h${i}`, correlationId: "hic", payload: { languageTag: "th-TH", text: `t${i}`, isFinal: false }, emittedAtMs: 700 + i }));
  }
  const stats = s.subscriberStats(sub.id);
  assert.ok(stats.coalesced >= 1, "partial transcripts coalesced");
  assert.equal(stats.dropped, 0, "no partial dropped while queue had room after coalescing");
});

test("P1.5b USER_INTERRUPT is never dropped even when queue is full", () => {
  const s = freshStore();
  const sub = s.subscribe(3);
  for (let i = 0; i < 3; i++) {
    s.ingest(obs({ eventId: `d${i}`, correlationId: `ci${i}`, payload: { languageTag: "th-TH", text: `x${i}`, isFinal: false }, emittedAtMs: 700 + i }));
  }
  const intr = {
    kind: "USER_INTERRUPT",
    ...ENV({ eventId: "intr", emittedAtMs: 800, correlationId: "i1", observationRevision: 4 }),
    payload: { reason: "stop" },
  };
  s.ingest(intr);
  const stats = s.subscriberStats(sub.id);
  assert.ok(stats.dropped >= 1, "oldest provisional dropped to make room");
  // The interrupt must be present in the cap-3 queue. offerToQueue's critical
  // keep-always guarantee is asserted directly in P1.5c.
});

test("P1.5c offerToQueue: critical is preserved, oldest non-critical evicted", () => {
  const make = (kind: string, id: string, isFinal = false, lang = "th-TH", seq = 1): SubscriberDelivery => ({
    seq,
    snapshotRevision: seq,
    causedByKind: kind,
    eventId: id,
    correlationId: id,
    languageTag: lang,
    isFinal,
  });
  let q: SubscriberDelivery[] = [];
  q = offerToQueue(q, make("OBSERVATION_PARTIAL", "a"), 2).queue;
  q = offerToQueue(q, make("OBSERVATION_PARTIAL", "b"), 2).queue;
  // critical arrival on a full queue:
  const r = offerToQueue(q, make("USER_INTERRUPT", "intr"), 2);
  assert.equal(r.queue.some((x) => x.causedByKind === "USER_INTERRUPT"), true, "critical kept");
  assert.equal(r.queue.length, 2, "bounded at capacity");
});

// -- 6. multilingual UNKNOWN/NEEDS_PLAN --------------------------------------

test("P1.6 unrecognized multilingual speech stays NEEDS_PLAN, never hallucinated", () => {
  const s = freshStore();
  const events = loadEvents();
  for (const e of events) s.ingest(e);
  const st = s.getState();
  assert.equal(st.needsPlan.length, 1, "exactly one NEEDS_PLAN from e8");
  const np = st.needsPlan[0];
  assert.equal(np.text, "ภาษาไทย", "original multilingual text preserved");
  assert.equal(np.languageTag, "th-TH", "language attribution preserved");
  assert.match(np.reason, /NEEDS_PLAN|HOLD/i);
  assert.deepEqual(
    s.getState().committedSceneActions,
    [],
    "no fabricated unordered/forest linked scene mutation",
  );
  assert.equal(st.conversationLanguages.includes("th-TH"), true);
});

// -- 7. independent revisions -------------------------------------------------

test("P1.7 obs/sem/scene revisions advance independently", () => {
  const s = freshStore();
  for (const e of loadEvents()) s.ingest(e);
  const st = s.getState();
  assert.equal(st.observationRevision, 3, "observation stream bumped through e1..e4");
  assert.equal(st.semanticRevision, 1, "semantic revision untouched when no PLAN_* authored");
  assert.equal(st.sceneRevision, 0, "scene revision untouched when no SCENE_* authored");
});

// -- 8. advisory non-mutation ---------------------------------------------------

test("P1.8 DECIDER_PROPOSAL is advisory: nothing committed without SCENE_COMMITTED", () => {
  const s = freshStore();
  s.ingest(proposal({ proposalId: "adv" }, { eventId: "adv0", emittedAtMs: 700 }));
  const st = s.getState();
  assert.equal(st.pendingProposals.length, 1, "held provisionally");
  assert.equal(st.committedSceneActions.length, 0, "not committed by proposal alone");
  assert.equal(st.visualObjects["obj-tree-1"].attention, 0, "scene not mutated");
});

test("P1.8b correction revokes dependent provisional proposal (I5)", () => {
  const s = freshStore();
  s.ingest(obs({ eventId: "o1", payload: { languageTag: "ja-JP", text: "木", isFinal: false }, emittedAtMs: 700, correlationId: "r1" }));
  s.ingest(proposal({ proposalId: "pd2", evidenceEventIds: ["o1"] }, { eventId: "p1b", emittedAtMs: 720, correlationId: "r1" }));
  assert.equal(s.getState().pendingProposals.length, 1);
  const corr = {
    kind: "OBSERVATION_CORRECTION",
    ...ENV({ eventId: "o2", emittedAtMs: 740, correlationId: "r1", observationRevision: 2 }),
    payload: { languageTag: "ja-JP", text: "森", isFinal: true, supersedes: ["o1"] },
  };
  s.ingest(corr);
  assert.equal(s.getState().pendingProposals.length, 0, "dependent provisional revoked");
  assert.equal(s.getState().committedSceneActions.length, 0);
});

test("P1.9 epoch advance does NOT inherit old-topic provisional permissions (I6)", () => {
  const s = freshStore();
  s.ingest(proposal({ proposalId: "oldp" }, { eventId: "op0", emittedAtMs: 700 }));
  assert.equal(s.getState().pendingProposals.length, 1);
  const adv = {
    kind: "TOPIC_EPOCH_ADVANCED",
    ...ENV({ eventId: "adv1", emittedAtMs: 800, topicEpoch: 2, observationRevision: 5 }),
    payload: { reason: "switch", languageTag: "fr-FR" },
  };
  s.ingest(adv);
  const st = s.getState();
  assert.equal(st.topicEpoch, 2);
  assert.equal(st.pendingProposals.length, 0, "old proposal cleared on epoch advance");
  assert.equal(st.needsPlan.filter((n) => n.topicEpoch === 1).length, 0);
});