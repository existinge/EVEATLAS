import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS=Path(__file__).resolve().parents[1]/"tools"
sys.path.insert(0,str(TOOLS))
import atlas_loop as loop
import atlas_treasurer as treasurer

class TreasurerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"ledger.sqlite"
        self.db=loop.connect(self.path)
        self.run=loop.create_run(self.db,"test",[
            {"id":"one","worker":"local","acceptance":{"content":"ok","contains":"ok"}}],budget=1.00)
    def tearDown(self):
        self.db.close();self.tmp.cleanup()
    def test_atomic_budget_cap(self):
        a=treasurer.reserve(self.db,self.run,"one","provider","model","0.60")
        second=loop.connect(self.path)
        try:
            with self.assertRaises(ValueError):
                treasurer.reserve(second,self.run,"one","provider","model","0.50")
        finally:second.close()
        treasurer.reconcile(self.db,a,"0.40","provider_reported",100,50)
        self.assertEqual(treasurer.snapshot(self.db,self.run)["available_cents"],60)
    def test_idempotent_reserve_and_reconcile(self):
        a=treasurer.reserve(self.db,self.run,"one","p","m",0.30,reservation_id="unique")
        self.assertEqual(treasurer.reserve(self.db,self.run,"one","p","m",0.30,reservation_id="unique"),a)
        with self.assertRaises(ValueError):
            treasurer.reserve(self.db,self.run,"one","p","different",0.30,reservation_id="unique")
        treasurer.reconcile(self.db,a,0.20,"gateway_metered")
        treasurer.reconcile(self.db,a,0.20,"gateway_metered")
        with self.assertRaises(ValueError):
            treasurer.reconcile(self.db,a,0.10,"gateway_metered")
    def test_unknown_cost_fails_closed(self):
        a=treasurer.reserve(self.db,self.run,"one","p","m",0.80)
        treasurer.mark_uncertain(self.db,a,"timeout after request")
        self.assertEqual(treasurer.snapshot(self.db,self.run)["available_cents"],20)
        self.assertTrue(any(x["severity"]=="critical" for x in treasurer.advise(self.db,self.run)["recommendations"]))
        with self.assertRaises(ValueError):
            treasurer.release(self.db,a,"not safe")
    def test_no_negative_or_fake_source(self):
        for amount in [-1,"NaN","Infinity"]:
            with self.assertRaises(ValueError):treasurer.cents(amount)
        a=treasurer.reserve(self.db,self.run,"one","p","m",0.10)
        with self.assertRaises(ValueError):treasurer.reconcile(self.db,a,0,"worker_claimed")
    def test_overrun_alert(self):
        a=treasurer.reserve(self.db,self.run,"one","p","m",0.30)
        treasurer.reconcile(self.db,a,1.20,"invoice_verified")
        self.assertTrue(treasurer.snapshot(self.db,self.run)["over_budget"])
        self.assertGreater(self.db.execute("SELECT count(*) FROM cost_incidents").fetchone()[0],0)
    def test_no_paid_dispatch_without_balance(self):
        a=treasurer.reserve(self.db,self.run,"one","p","m",1.00)
        self.assertEqual(treasurer.snapshot(self.db,self.run)["available_cents"],0)
        with self.assertRaises(ValueError):treasurer.reserve(self.db,self.run,"one","p","m",0.01)

if __name__=="__main__":unittest.main()
