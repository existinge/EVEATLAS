import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.identity import resolve,normalize
from engine.status import current_status,append_feedback,eligible_as_new
from engine.evidence import evidence_gate
from engine.scoring import score
from engine.ranking import triage

class Gates(unittest.TestCase):
 def test_alias(self):
  known=[{"id":"a","title":"Boys Be Brave!","aliases":["고백을 못하고"],"country":"South Korea"}]
  self.assertEqual(resolve("고백을 못하고",known)["state"],"matched")
 def test_ambiguous(self):
  self.assertEqual(resolve("Same",[{"id":"a","title":"Same"},{"id":"b","title":"Same"}])["state"],"ambiguous")
 def test_unresolved_not_verified(self):
  result=triage([{"title":"Never Heard Of","criteria":{k:8 for k in ["romance_payoff","acting_chemistry","plot_stakes","pursuit","visual_fit","pacing"]}}],[],[])
  self.assertEqual(len(result["unknown_discoveries"]),1)
  self.assertEqual(len(result["recommendations"]),0)
 def test_no_skip_is_not_watched(self):
  events=append_feedback([],{"production_id":"x","status":"no_skip","timestamp":"2026-10-27","source":"user"})
  self.assertEqual(current_status(events,"x"),"no_skip")
  self.assertFalse(eligible_as_new("no_skip"))
 def test_low_fit_still_discovered(self):
  result=triage([{"title":"New one","criteria":{k:1 for k in ["romance_payoff","acting_chemistry","plot_stakes","pursuit","visual_fit","pacing"]}}],[],[])
  self.assertEqual(result["unknown_discoveries"][0]["fit_score"],10)
 def test_evidence(self):
  self.assertFalse(evidence_gate({"evidence":{"completed":{"supported":True}}})["approved"])
 def test_score(self):
  self.assertEqual(score({k:10 for k in ["romance_payoff","acting_chemistry","plot_stakes","pursuit","visual_fit","pacing"]}),100)
 def test_prior_known_block(self):
  r=triage([{"title":"Crush on You"}],[{"id":"x","title":"Crush on You"}],[])
  self.assertEqual(len(r["excluded"]),1)

if __name__=="__main__":unittest.main()
