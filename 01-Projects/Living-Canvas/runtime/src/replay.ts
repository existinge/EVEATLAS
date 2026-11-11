// T01 deterministic replay entry point.
//
// Loads seed-concepts.json + sample-events.jsonl, replays the event log twice
// into two fully independent SharedStore instances, and asserts Gate P1:
// byte-equivalent canonical final snapshots (identical JSON + commitId).
//
// Usage:   node replay.ts            (assert + print report; exit 0)
//          node replay.ts --show-json   (also print final canonical JSON)
// Result:  prints PASS, commitId; non-zero exit on any divergence.

import { loadSeed, loadEvents } from "./fixtures.ts";
import { SharedStore } from "./store.ts";
import { canonicalJsonPretty } from "./canonical.ts";

const seedA = loadSeed();
const events = loadEvents();

const storeA = new SharedStore(seedA);
for (const evt of events) storeA.ingest(evt);

const seedB = loadSeed();
const storeB = new SharedStore(seedB);
for (const evt of events) storeB.ingest(evt);

const snapA = storeA.canonicalSnapshot();
const snapB = storeB.canonicalSnapshot();

const byteEquivalent = snapA.json === snapB.json && snapA.commitId === snapB.commitId;

function report(): void {
  const log = storeA.getLog();
  console.log("T01 REPLAY — sample-events.jsonl (8 events)");
  console.log("===========================================");
  for (const entry of log) {
    console.log(`  e#${entry.seq}  ${entry.eventId.padEnd(8)} ${entry.kind.padEnd(22)} -> ${entry.outcome}`);
  }
  const st = storeA.getState().stats;
  console.log("-------------------------------------------");
  console.log(`  applied=${st.applied} rejected=${st.rejected} skippedDuplicate=${st.skippedDuplicate} total=${st.total}`);
  console.log(`  interrupts=${st.interrupts} epochAdvances=${st.epochAdvances}`);
  console.log(`  final observationRevision=${storeA.getState().observationRevision}`);
  console.log(`  final semanticRevision=${storeA.getState().semanticRevision}`);
  console.log(`  final sceneRevision=${storeA.getState().sceneRevision}`);
  console.log(`  final topicEpoch=${storeA.getState().topicEpoch}`);
  console.log(`  final conversationLanguages=${storeA.getState().conversationLanguages.join(",")}`);
  console.log(`  final needsPlan=${storeA.getState().needsPlan.length}`);
  console.log(`  final committedSceneActions=${storeA.getState().committedSceneActions.length}`);
  console.log(`  final pendingProposals=${storeA.getState().pendingProposals.length}`);
  console.log(`  final commitId=${snapA.commitId}`);
  console.log(`  byteEquals(run2)=${byteEquivalent}`);
  for (const d of storeA.getState().diagnostics) console.log(`  diag: ${d}`);
}

report();

const showJson = process.argv.includes("--show-json");
if (showJson) {
  console.log("\nFINAL CANONICAL SNAPSHOT:");
  console.log(canonicalJsonPretty(storeA.getState()));
}

if (!byteEquivalent) {
  console.error("GATE P1 FAILED: two independent replays diverged.");
  process.exit(1);
}
console.log("\nGATE P1: PASS (two independent replays byte-equivalent).");