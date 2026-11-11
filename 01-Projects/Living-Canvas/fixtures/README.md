# Example fixtures — not test results

seed-concepts.json contains two prepared concept nodes with Japanese/Thai/English labels and a simple scene object. sample-events.jsonl is a contrived stream: a Japanese partial, decider preview, ASR correction, interruption, topic epoch change, a deliberately stale decider proposal and an unknown Thai utterance. These fixtures DO NOT imply the system has been implemented or tested.

Expected assertions after T01/T02:
- p1 is never treated as an authoritative semantic fact, and must be reversible.
- Correction e3 invalidates dependent provisional p1.
- Interrupt e4 clears leftover speculative actions for t1.
- Topic epoch advances to 2 after e5.
- p-stale from epoch 1 is rejected, with no committed canvas change.
- Thai observation e7 is preserved as text tagged th-TH; e8 requests a planner update.
- Replaying events yields same final semantic and scene revisions.
- No fabricated forest or unrelated picture appears merely because multilingual input arrived.

Agent: implement the test harness from these assertions, and record failures explicitly. Future fixtures should include approved PLAN_COMMITTED/SCENE_COMMITTED transitions, duplicate IDs, and reordered transport events.
