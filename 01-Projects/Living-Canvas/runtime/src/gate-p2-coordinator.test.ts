// Gate P2 acceptance tests (T02). Runs under `node --test`.
//
// P2 requirement: a deterministic coordinator that "receives fast-decider
// proposals, validates them against canonical semantic state, and commits only
// authorized scene actions." The coordinator is the ONLY authority that may
// authorize a new scene commit; an externally supplied SCENE_COMMITTED must not
// bypass it (I1/PROTOCOL authority invariant).
//
// Stoplight contract (validateProposal, always PURE):
//   GREEN  = no hard failures AND authoritative evidence (every evidence event
//            is live, final, and matched to a target concept) AND reversible
//            -> coordinator authors DECIDER_PROPOSAL then synthesizes
//            SCENE_COMMITTED `volition-<proposalId>`.
//   YELLOW = no hard failures AND (authoritative evidence incomplete OR action
//            is preview-grade) AND the action is a reversible preview-grade
//            action (emphasize|deEmphasize|revealHint) -> SCENE_PROVISIONAL
//            `provisional-<proposalId>` is staged; never a commit.
//   RED    = any hard failure: stale-epoch, stale-semantic-revision,
//            expired-proposal (self-expiry or past current session time),
//            unsupported-action, invalid-object-id, unknown-concept,
//            revoked-plan, ineligible-branch, expired-permission,
//            action-not-permitted, stale-evidence, incompatible-evidence,
//            preview-only-action, not-reversible-by-decider.
//
// No LLM/model is present anywhere in this loop; proceeds in a deterministic
// store. Every test builds a fresh Coordinator on the canonical seed
// (seed-concepts.json: nature.tree active|planRevision 1|expires 600000,
// obj-tree-1). Monotonic session time is strictly non-decreasing per test.

import { test } from "node:test";
import assert from "node:assert/strict";
import { loadSeed } from "./fixtures.ts";
import { Coordinator } from "./coordinator.ts";

function fresh(extraConcept?: Record<string, unknown>, extraObject?: Record<string, unknown>) {
  const seed = loadSeed();
  if (extraConcept) seed.concepts = { ...seed.concepts, ...extraConcept };
  if (extraObject) seed.visualObjects = { ...seed.visualObjects, ...extraObject };
  return new Coordinator(seed);
}

// -- envelope builders (mirror gate-p1 shapes) --------------------------------

const ENV = (over: Record<string, unknown> = {}) => ({
  schemaVersion: "0.1",
  sessionId: "s-demo",
  topicEpoch: 1,
  observationRevision: 1,
  semanticRevision: 1,
  sceneRevision: 0,
  emittedAtMs: 800,
  correlationId: "c1",
  turnId: "t1",
  source: "test",
  ...over,
});

/** LIVE, FINAL evidence that matches seed concept nature.tree ("tree" @ en-US). */
function treeEvidence(over: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    kind: "OBSERVATION_FINAL",
    ...ENV({ emittedAtMs: 600, correlationId: "c-obs", ...over }),
    payload: { languageTag: "en-US", text: "tree", isFinal: true },
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
      parameters: { attention: 0.8 },
      confidence: null,
      evidenceEventIds: [],
      reversible: true,
      expiresAtSessionMs: 100_000,
      ...payload,
    },
  };
}

function extCommit(payload: Record<string, unknown>, over: Record<string, unknown> = {}): Record<string, unknown> {
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

function extRevert(payload: Record<string, unknown>, over: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    kind: "SCENE_REVERTED",
    ...ENV(over),
    payload: { ...payload },
  };
}

// -- 1. GREEN: coordinator commits a valid emphasis on authority ---------------

test("P2.1 GREEN proposal tags final trees, is committed by the coordinator", () => {
  const c = fresh();
  const cid = "ev-tree-1";
  assert.equal(c.ingest(treeEvidence({ eventId: cid })).status, "applied");

  const out = c.ingest(
    proposal(
      { proposalId: "p-ok", evidenceEventIds: [cid], expiresAtSessionMs: 100_000 },
      { eventId: "p-ok-e", emittedAtMs: 800, correlationId: "c-ok" },
    ),
  );

  assert.equal(out.status, "applied", "coordinator must apply a GREEN scene commit");
  assert.equal(out.kind, "SCENE_COMMITTED");
  assert.equal((out as { decision: { status: string; authority: string } }).decision.status, "GREEN");
  assert.equal((out as { decision: { status: string; authority: string } }).decision.authority, "commit");

  const st = c.getState();
  assert.equal(st.committedSceneActions.length, 1, "exactly one committed scene action");
  assert.equal(st.committedSceneActions[0].proposalId, "p-ok");
  assert.equal(st.committedSceneActions[0].sourceEventId, "volition-p-ok", "commit authored with volition event id");
  assert.equal(st.commitCount, 1);
  assert.equal(st.pendingProposals.length, 0, "commit consumes the pending proposal");
  assert.equal(st.visualObjects["obj-tree-1"].attention, 0.8, "emphasis reflected deterministically");
  // the authored DECIDER_PROPOSAL and the synthesized SCENE_COMMITTED are both in the log
  const kinds = c.getLog().map((e) => e.kind);
  assert.ok(kinds.includes("DECIDER_PROPOSAL"));
  assert.ok(kinds.includes("SCENE_COMMITTED"));
  const authored = c.getLog().find((e) => e.kind === "SCENE_COMMITTED");
  assert.equal(authored.source, "coordinator");
});

// -- 2. YELLOW: incomplete evidence stages a provisional preview, never commits --

test("P2.2 YELLOW proposal with no authoritative evidence only stages a preview", () => {
  const c = fresh();
  const out = c.ingest(
    proposal({ proposalId: "p-prev", evidenceEventIds: [] }, { eventId: "p-prev-e", emittedAtMs: 800, correlationId: "c-prev" }),
  );

  assert.equal(out.status, "applied");
  assert.equal(out.kind, "SCENE_PROVISIONAL", "YELLOW stages SCENE_PROVISIONAL, not SCENE_COMMITTED");
  assert.equal((out as { decision: { status: string } }).decision.status, "YELLOW");
  assert.equal((out as { decision: { authority: string } }).decision.authority, "preview");

  const st = c.getState();
  assert.equal(st.committedSceneActions.length, 0, "scene is NOT committed");
  assert.equal(st.provisionalSceneActions.length, 1, "preview staged");
  assert.equal(st.provisionalSceneActions[0].sourceEventId, "provisional-p-prev");
  assert.equal(st.sceneRevision, 0, "preview does not advance scene revision");
  assert.equal(st.visualObjects["obj-tree-1"].attention, 0, "preview does not mutate committed scene");
});

// -- 3. RED matrix: every hard failure rejects cleanly, scene untouched --------

function assertRejected(c: Coordinator, out: { status: string; reason: string; sceneBefore: number; sceneAfter: number }, reason: string, before: string) {
  assert.equal(out.status, "rejected", `must reject with ${reason}`);
  assert.equal(out.reason, reason);
  assert.equal(out.sceneBefore, 0, "no mutation before a rejected proposal");
  assert.equal(out.sceneAfter, 0, "rejected proposal never advances sceneRevision");
  const st = c.getState();
  assert.equal(st.committedSceneActions.length, 0);
  assert.equal(st.provisionalSceneActions.length, 0);
  assert.equal(st.pendingProposals.length, 0, "rejected proposal is never even authored");
  assert.equal(JSON.stringify(st), before, "canonical state is byte-unchanged after rejection");
}

test("P2.3a stale epoch is RED", () => {
  const c = fresh();
  const before = JSON.stringify(c.getState());
  const out = c.ingest(proposal({ proposalId: "p-epoch" }, { eventId: "p-epoch-e", topicEpoch: 2, emittedAtMs: 800 }));
  assertRejected(c, out, "stale-epoch", before);
  assert.ok(c.rejectLog.length === 1 && c.rejectLog[0].reasons.includes("stale-epoch"));
});

test("P2.3b stale semantic revision is RED", () => {
  const c = fresh();
  const before = JSON.stringify(c.getState());
  const out = c.ingest(proposal({ proposalId: "p-sem" }, { eventId: "p-sem-e", semanticRevision: 0, emittedAtMs: 800 }));
  assertRejected(c, out, "stale-semantic-revision", before);
});

test("P2.3c expired proposal (self-expiry) is RED", () => {
  const c = fresh();
  const before = JSON.stringify(c.getState());
  // born at 800 with its own expiry at 800 -> already past its own lifetime
  const self = c.ingest(
    proposal({ proposalId: "p-xp", expiresAtSessionMs: 800 }, { eventId: "p-xp-e", emittedAtMs: 800 }),
  );
  assertRejected(c, self, "expired-proposal", before);
});

test("P2.3d expired proposal (past current session time) is RED", () => {
  const c = fresh();
  // advance session time to 600
  const cid = "ev-tt";
  c.ingest(treeEvidence({ eventId: cid, emittedAtMs: 600 }));
  const before = JSON.stringify(c.getState());
  // proposal born at 700 with expiry 550: later than its birth (550 > 700 is
  // false, so self-expiry does not fire) but already behind the session clock
  // of 600 -> expired-proposal via current-session-time
  const out = c.ingest(
    proposal({ proposalId: "p-xp2", expiresAtSessionMs: 550 }, { eventId: "p-xp2-e", emittedAtMs: 700 }),
  );
  assertRejected(c, out, "expired-proposal", before);
});

test("P2.3e unsupported action is RED", () => {
  const c = fresh();
  const before = JSON.stringify(c.getState());
  const out = c.ingest(proposal({ proposalId: "p-u", actionType: "explode" }, { eventId: "p-u-e", emittedAtMs: 800 }));
  assertRejected(c, out, "unsupported-action", before);
});

test("P2.3f invalid object id is RED", () => {
  const c = fresh();
  const before = JSON.stringify(c.getState());
  const out = c.ingest(
    proposal({ proposalId: "p-obj", targetObjectIds: ["obj-missing"] }, { eventId: "p-obj-e", emittedAtMs: 800 }),
  );
  assertRejected(c, out, "invalid-object-id", before);
});

test("P2.3g unknown concept (object references non-existent concept) is RED", () => {
  const c = fresh(undefined, {
    "obj-ghost": { conceptId: "nature.ghost", recipeId: "r", position: { x: 0, y: 0 }, attention: 0 },
  });
  const before = JSON.stringify(c.getState());
  const out = c.ingest(
    proposal({ proposalId: "p-ghost", targetObjectIds: ["obj-ghost"] }, { eventId: "p-ghost-e", emittedAtMs: 800 }),
  );
  assertRejected(c, out, "unknown-concept", before);
});

test("P2.3h ineligible branch (concept not active) is RED", () => {
  const c = fresh(undefined, {
    "obj-forest-1": { conceptId: "nature.forest", recipeId: "recipe.forest", position: { x: 0, y: 0 }, attention: 0 },
  });
  const before = JSON.stringify(c.getState());
  const out = c.ingest(
    proposal({ proposalId: "p-fst", targetObjectIds: ["obj-forest-1"] }, { eventId: "p-fst-e", emittedAtMs: 800 }),
  );
  assertRejected(c, out, "ineligible-branch", before);
});

test("P2.3i revoked plan (concept plan always ahead of proposal) is RED", () => {
  const c = fresh(
    {
      "nature.q": {
        labelByLanguage: { "en-US": "q" },
        relationships: [],
        visualRecipeId: "r.q",
        allowedActions: ["emphasize"],
        status: "active",
        planRevision: 5,
        expiresAtSessionMs: 600000,
      },
    },
    { "obj-q-1": { conceptId: "nature.q", recipeId: "r.q", position: { x: 0, y: 0 }, attention: 0 } },
  );
  const before = JSON.stringify(c.getState());
  // concept plan revision 5 is always ahead of this proposal's semanticRevision 1
  // (envelope semanticRevision defaults to 1 from ENV)
  const out = c.ingest(
    proposal({ proposalId: "p-q", targetObjectIds: ["obj-q-1"] }, { eventId: "p-q-e", emittedAtMs: 800 }),
  );
  assertRejected(c, out, "revoked-plan", before);
});

test("P2.3j expired permission (concept authority lapsed before proposal) is RED", () => {
  const c = fresh(
    {
      "nature.e": {
        labelByLanguage: { "en-US": "e" },
        relationships: [],
        visualRecipeId: "r.e",
        allowedActions: ["emphasize"],
        status: "active",
        planRevision: 1,
        expiresAtSessionMs: 500, // permission dies before any 800ms proposal
      },
    },
    { "obj-e-1": { conceptId: "nature.e", recipeId: "r.e", position: { x: 0, y: 0 }, attention: 0 } },
  );
  const before = JSON.stringify(c.getState());
  const out = c.ingest(
    proposal({ proposalId: "p-e", targetObjectIds: ["obj-e-1"] }, { eventId: "p-e-e", emittedAtMs: 800 }),
  );
  assertRejected(c, out, "expired-permission", before);
});

test("P2.3k action not permitted on the target concept is RED", () => {
  const c = fresh();
  const before = JSON.stringify(c.getState());
  // connect is a known action but not in nature.tree's allowedActions
  const out = c.ingest(proposal({ proposalId: "p-ap", actionType: "connect" }, { eventId: "p-ap-e", emittedAtMs: 800 }));
  assertRejected(c, out, "action-not-permitted", before);
});

test("P2.3l non-reversible proposal is RED (decider has no commit authority)", () => {
  const c = fresh();
  const before = JSON.stringify(c.getState());
  const out = c.ingest(
    proposal({ proposalId: "p-nr", reversible: false }, { eventId: "p-nr-e", emittedAtMs: 800 }),
  );
  assertRejected(c, out, "not-reversible-by-decider", before);
});

test("P2.3m incomplete evidence on a non-preview-grade action is RED (preview-only-action)", () => {
  const c = fresh();
  const before = JSON.stringify(c.getState());
  // move is permitted on nature.tree but is NOT preview-grade and evidence is empty
  const out = c.ingest(proposal({ proposalId: "p-mv", actionType: "move" }, { eventId: "p-mv-e", emittedAtMs: 800 }));
  assertRejected(c, out, "preview-only-action", before);
});

test("P2.3n incompatible evidence (matched to a different concept) is RED", () => {
  const c = fresh();
  const cid = "ev-forest";
  c.ingest({
    kind: "OBSERVATION_FINAL",
    ...ENV({ eventId: cid, emittedAtMs: 600, correlationId: "c-forest" }),
    payload: { languageTag: "en-US", text: "forest", isFinal: true },
  });
  const before = JSON.stringify(c.getState());
  // evidence matched nature.forest, but targets are nature.tree
  const out = c.ingest(
    proposal({ proposalId: "p-ice", evidenceEventIds: [cid] }, { eventId: "p-ice-e", emittedAtMs: 800 }),
  );
  assertRejected(c, out, "incompatible-evidence", before);
});

test("P2.3o stale/superseded evidence is RED", () => {
  const c = fresh();
  const before = JSON.stringify(c.getState());
  // "ghost-ev" was never observed -> stale-evidence
  const out = c.ingest(
    proposal({ proposalId: "p-se", evidenceEventIds: ["ev-does-not-exist"] }, { eventId: "p-se-e", emittedAtMs: 800 }),
  );
  assertRejected(c, out, "stale-evidence", before);
});

// -- 4. idempotency: a decided proposal and a synthesized commit apply once ----

test("P2.4 duplicate GREEN proposal and duplicate synthesized commit never double-apply", () => {
  const c = fresh();
  const cid = "ev-tree-1";
  c.ingest(treeEvidence({ eventId: cid }));

  const p = proposal({ proposalId: "p-id", evidenceEventIds: [cid] }, { eventId: "p-id-e", emittedAtMs: 800, correlationId: "c-id" });
  assert.equal(c.ingest(p).status, "applied");

  // same DECIDER_PROPOSAL event again -> store dedupe, no re-decision, no double scene work
  const again = c.ingest(p);
  assert.equal(again.status, "rejected");
  assert.equal(again.reason, "skipped-duplicate");

  // replay the exact synthesized SCENE_COMMITTED (found in the canonical log) -> skipped-duplicate
  const committed = c.getLog().find((e) => e.kind === "SCENE_COMMITTED");
  assert.ok(committed, "log must contain the synthesized SCENE_COMMITTED");
  const replay = c.ingest(committed);
  assert.equal(replay.status, "skipped-duplicate");

  const st = c.getState();
  assert.equal(st.commitCount, 1, "scene committed exactly once");
  assert.equal(st.committedSceneActions.length, 1);
  assert.equal(st.visualObjects["obj-tree-1"].attention, 0.8);
});

test("P2.4b a second, distinct SCENE_COMMITTED for the same proposal is refused (no-valid-source)", () => {
  const c = fresh();
  const cid = "ev-tree-1";
  c.ingest(treeEvidence({ eventId: cid }));
  assert.equal(
    c.ingest(proposal({ proposalId: "p-x", evidenceEventIds: [cid] }, { eventId: "p-x-e", emittedAtMs: 800 })).status,
    "applied",
  );
  // grant still exists for p-x (fingerprint matches a legit commit), but the proposal
  // is already consumed -> the reducer refuses to re-invent a second scene action.
  const out = c.ingest(extCommit({ proposalId: "p-x" }, { eventId: "p-x-c2", emittedAtMs: 900 }));
  assert.equal(out.status, "rejected");
  assert.equal(out.reason, "no-valid-source");
  assert.equal(c.getState().commitCount, 1);
});

// -- 5. authority invariant (I1): external SCENE_COMMITTED cannot bypass --------

test("P2.5 external SCENE_COMMITTED without a coordinator grant is refused byte-unchanged", () => {
  const c = fresh();
  const before = JSON.stringify(c.getState());
  const forged = extCommit(
    { proposalId: "p-forged" },
    { eventId: "forged-c", emittedAtMs: 800, source: "attacker", correlationId: "c-forge" },
  );
  const out = c.ingest(forged);
  assert.equal(out.status, "rejected");
  assert.equal(out.reason, "not-coordinator-authoritative");
  assert.equal(out.sceneBefore, 0);
  assert.equal(out.sceneAfter, 0);
  assert.equal(JSON.stringify(c.getState()), before, "canonical snapshot byte-unchanged: authority invariant holds");
  assert.equal(c.getState().commitCount, 0);
  assert.equal(c.getState().committedSceneActions.length, 0);
});

test("P2.5b external SCENE_COMMITTED diverging from the granted fingerprint is refused and grant revoked", () => {
  const c = fresh();
  const cid = "ev-tree-1";
  c.ingest(treeEvidence({ eventId: cid }));
  assert.equal(
    c.ingest(proposal({ proposalId: "p-g", evidenceEventIds: [cid] }, { eventId: "p-g-e", emittedAtMs: 800 })).status,
    "applied",
  );
  // attacker sends the same proposalId but a different action than granted
  const tampered = extCommit(
    { proposalId: "p-g", actionType: "hide", parameters: {} },
    { eventId: "tamper-c", emittedAtMs: 900, source: "attacker" },
  );
  const out = c.ingest(tampered);
  assert.equal(out.status, "rejected");
  assert.equal(out.reason, "authority-fingerprint-mismatch");

  // having revoked the grant, even an exact re-send cannot commit
  const retry = c.ingest(extCommit({ proposalId: "p-g" }, { eventId: "retry-c", emittedAtMs: 950, source: "attacker" }));
  assert.equal(retry.status, "rejected");
  assert.equal(retry.reason, "not-coordinator-authoritative");
  assert.equal(c.getState().committedSceneActions.length, 1, "only the coordinator's own commit remains");
});

test("P2.5c external SCENE_PROVISIONAL cannot invent a preview (not staged by coordinator)", () => {
  const c = fresh();
  const out = c.ingest({
    kind: "SCENE_PROVISIONAL",
    ...ENV({ eventId: "fake-prov", emittedAtMs: 800 }),
    payload: { proposalId: "p-nostage", targetObjectIds: ["obj-tree-1"], actionType: "emphasize", reversible: true },
  });
  assert.equal(out.status, "rejected");
  assert.equal(out.reason, "not-coordinator-authoritative");
  assert.equal(c.getState().provisionalSceneActions.length, 0);
});

// -- 6. legitimate reversal via provenance --------------------------------------

test("P2.6 SCENE_REVERTED reverts a committed action by proposalId or correlationId", () => {
  const c = fresh();
  const cid = "ev-tree-1";
  c.ingest(treeEvidence({ eventId: cid }));

  assert.equal(
    c.ingest(proposal({ proposalId: "p-a", evidenceEventIds: [cid] }, { eventId: "p-a-e", emittedAtMs: 800, correlationId: "c-a" })).status,
    "applied",
  );
  assert.equal(
    c.ingest(proposal({ proposalId: "p-b", evidenceEventIds: [cid] }, { eventId: "p-b-e", emittedAtMs: 900, correlationId: "c-b" })).status,
    "applied",
  );
  assert.equal(c.getState().committedSceneActions.length, 2);

  // revert by proposalId
  const r1 = c.ingest(extRevert({ proposalId: "p-a" }, { eventId: "rev-a", emittedAtMs: 1000 }));
  assert.equal(r1.status, "applied");
  assert.equal(c.getState().committedSceneActions.map((a) => a.proposalId).join(","), "p-b");

  // revert by correlationId
  const r2 = c.ingest(extRevert({ correlationId: "c-b" }, { eventId: "rev-b", emittedAtMs: 1100 }));
  assert.equal(r2.status, "applied");
  assert.equal(c.getState().committedSceneActions.length, 0);
});

test("P2.6b a reversal referencing nothing (no valid source) is refused", () => {
  const c = fresh();
  const out = c.ingest(extRevert({ proposalId: "p-nope" }, { eventId: "rev-x", emittedAtMs: 800 }));
  assert.equal(out.status, "rejected");
  assert.equal(out.reason, "no-valid-source");
});

// -- 7. interruption invalidates speculative state but preserves the scene -----

test("P2.7 USER_INTERRUPT clears staged previews while the committed scene survives", () => {
  const c = fresh();
  const cid = "ev-tree-1";
  c.ingest(treeEvidence({ eventId: cid }));

  // one committed action (stable scene)
  assert.equal(
    c.ingest(proposal({ proposalId: "p-committed", evidenceEventIds: [cid] }, { eventId: "p-c-e", emittedAtMs: 800 })).status,
    "applied",
  );
  // one outstanding speculative preview
  assert.equal(c.getState().visualObjects["obj-tree-1"].attention, 0.8);
  assert.equal(
    c.ingest(proposal({ proposalId: "p-preview" }, { eventId: "p-pv-e", emittedAtMs: 900, correlationId: "c-pv" })).status,
    "applied",
  );
  assert.equal(c.getState().provisionalSceneActions.length, 1);

  // interrupt
  const intr = c.ingest({ kind: "USER_INTERRUPT", ...ENV({ eventId: "intr-1", emittedAtMs: 1000 }), payload: {} });
  assert.equal(intr.status, "applied");

  const st = c.getState();
  assert.equal(st.provisionalSceneActions.length, 0, "outstanding preview invalidated");
  assert.equal(st.pendingProposals.length, 0, "outstanding proposal invalidated");
  assert.equal(st.committedSceneActions.length, 1, "stable scene not destroyed");
  assert.equal(st.committedSceneActions[0].proposalId, "p-committed");
  assert.equal(st.visualObjects["obj-tree-1"].attention, 0.8, "committed emphasis untouched");

  // the coordinator's own preview store no longer authorizes an external provisional
  const re = c.ingest({
    kind: "SCENE_PROVISIONAL",
    ...ENV({ eventId: "late-pv", emittedAtMs: 1100 }),
    payload: { proposalId: "p-preview", targetObjectIds: ["obj-tree-1"], actionType: "emphasize", reversible: true },
  });
  assert.equal(re.reason, "not-coordinator-authoritative");
});

// -- 8. USER_ACTION override terminates matching previews, never the scene -----

test("P2.8 USER_ACTION targeting a previewed object terminates that preview", () => {
  const c = fresh();
  assert.equal(
    c.ingest(proposal({ proposalId: "p-ov", evidenceEventIds: [] }, { eventId: "p-ov-e", emittedAtMs: 800, correlationId: "c-ov" })).status,
    "applied",
  );
  assert.equal(c.getState().provisionalSceneActions.length, 1);

  const out = c.ingest({
    kind: "USER_ACTION",
    ...ENV({ eventId: "ua-1", emittedAtMs: 900, correlationId: "c-ua" }),
    payload: { actionType: "show", targetObjectIds: ["obj-tree-1"] },
  });
  assert.equal(out.status, "applied");

  // preview authority is gone: an external provisional for that proposal is refused
  const re = c.ingest({
    kind: "SCENE_PROVISIONAL",
    ...ENV({ eventId: "late-ov", emittedAtMs: 1000 }),
    payload: { proposalId: "p-ov", targetObjectIds: ["obj-tree-1"], actionType: "emphasize", reversible: true },
  });
  assert.equal(re.reason, "not-coordinator-authoritative");
  // and nothing was ever committed
  assert.equal(c.getState().committedSceneActions.length, 0);
});

// -- 9. epoch advance clears old speculative previews (I6) ----------------------

test("P2.9 advanced topic epoch clears old speculative previews and old grants", () => {
  const c = fresh();
  assert.equal(
    c.ingest(proposal({ proposalId: "p-old" }, { eventId: "p-old-e", emittedAtMs: 800 })).status,
    "applied",
  );
  assert.equal(c.getState().provisionalSceneActions.length, 1);

  const adv = c.ingest({
    kind: "TOPIC_EPOCH_ADVANCED",
    ...ENV({ eventId: "epoch-2", topicEpoch: 2, emittedAtMs: 900 }),
    payload: { reason: "new topic" },
  });
  assert.equal(adv.status, "applied");

  const st = c.getState();
  assert.equal(st.topicEpoch, 2);
  assert.equal(st.provisionalSceneActions.length, 0, "old-topic speculative previews cleared (I6)");
  assert.equal(st.pendingProposals.length, 0);
  assert.equal(st.committedSceneActions.length, 0);

  // old-topic preview can no longer be staged
  const re = c.ingest({
    kind: "SCENE_PROVISIONAL",
    ...ENV({ eventId: "late-old", emittedAtMs: 1000 }),
    payload: { proposalId: "p-old", targetObjectIds: ["obj-tree-1"], actionType: "emphasize", reversible: true },
  });
  assert.equal(re.reason, "not-coordinator-authoritative");
});

// -- 10. rejected proposals leave sceneRevision untouched ------------------------

test("P2.10 a RED proposal never advances scene revision or state", () => {
  const c = fresh();
  const cid = "ev-tree-1";
  c.ingest(treeEvidence({ eventId: cid }));
  const before = JSON.stringify(c.getState());
  const bad = c.ingest(
    proposal({ proposalId: "p-bad", actionType: "connect" }, { eventId: "p-bad-e", emittedAtMs: 800 }),
  );
  assert.equal(bad.status, "rejected");
  assert.equal(bad.sceneBefore, 0);
  assert.equal(bad.sceneAfter, 0);
  assert.equal(JSON.stringify(c.getState()), before);
});

// -- 11. latency: coordinator hops recorded separately from any model work ------

test("P2.11 latencyReport records stoplight/commit/previewStage/forward hops", () => {
  const c = fresh();
  const cid = "ev-tree-1";
  c.ingest(treeEvidence({ eventId: cid }));
  c.ingest(treeEvidence({ eventId: "ev-2", emittedAtMs: 610 }));
  c.ingest(treeEvidence({ eventId: "ev-3", emittedAtMs: 620 }));

  // GREEN (1 commit hop + stoplight)
  c.ingest(proposal({ proposalId: "p-l1", evidenceEventIds: [cid] }, { eventId: "p-l1-e", emittedAtMs: 800 }));
  // YELLOW (1 preview stage hop + stoplight)
  c.ingest(proposal({ proposalId: "p-l2", evidenceEventIds: [] }, { eventId: "p-l2-e", emittedAtMs: 900 }));
  // RED (1 stoplight hop only — the important separation)
  c.ingest(proposal({ proposalId: "p-l3", actionType: "connect" }, { eventId: "p-l3-e", emittedAtMs: 1000 }));
  // one more forward
  c.ingest({ kind: "OBSERVATION_FINAL", ...ENV({ eventId: "ev-4", emittedAtMs: 620 }), payload: { languageTag: "ja-JP", text: "木", isFinal: true } });

  const report = c.latencyReport();
  assert.equal(report.length, 4);
  const byHop = Object.fromEntries(report.map((r) => [r.hop, r]));
  assert.ok(byHop.stoplight.n >= 3, `stoplight hops >= 3, got ${byHop.stoplight.n}`);
  assert.ok(byHop.commit.n >= 1, `commit hops >= 1, got ${byHop.commit.n}`);
  assert.ok(byHop.previewStage.n >= 1, `previewStage hops >= 1, got ${byHop.previewStage.n}`);
  assert.ok(byHop.forward.n >= 4, `forward hops >= 4, got ${byHop.forward.n}`);
  for (const r of report) {
    assert.ok(Number.isFinite(r.medianMs) && r.medianMs >= 0, `${r.hop} median finite`);
    assert.ok(Number.isFinite(r.p95Ms) && Number.isFinite(r.maxMs), `${r.hop} percentiles finite`);
  }
});