import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from atlas_brain import Worker, choose_worker, retry_advice

class BrainTests(unittest.TestCase):
    def test_route_by_capability_and_budget(self):
        workers=[Worker("heavy",frozenset(["code"]),True,90,priority=5),
                 Worker("cheap",frozenset(["code"]),True,20,priority=6),
                 Worker("unavailable",frozenset(["code"]),False,1,priority=1)]
        self.assertEqual(choose_worker(["code"],workers,30)["worker"],"cheap")
    def test_critical_pauses_routing(self):
        w=[Worker("cheap",frozenset(["code"]),True,20)]
        self.assertEqual(choose_worker(["code"],w,100,[{"severity":"critical"}])["action"],"hold")
    def test_no_fit_escalates(self):
        self.assertEqual(choose_worker(["vision"],[],100)["action"],"escalate")
    def test_repeated_failure_switches(self):
        self.assertEqual(retry_advice(2,3,["fail-A","fail-A"])["action"],"switch_strategy")
        self.assertEqual(retry_advice(3,3,[])["action"],"escalate")

if __name__=="__main__":unittest.main()
