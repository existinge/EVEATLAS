import importlib.util
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location("atlas_loop",Path(__file__).resolve().parents[1]/"tools"/"atlas_loop.py")
loop=importlib.util.module_from_spec(spec);spec.loader.exec_module(loop)

def task(id="a",deps=None,content="ok",contains="ok",max_attempts=3):
    return {"id":id,"name":id,"worker":"local","deps":deps or [],"acceptance":{"content":content,"contains":contains},"max_attempts":max_attempts}

class LoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=loop.connect(Path(self.tmp.name)/"loop.db")
    def tearDown(self):
        self.db.close();self.tmp.cleanup()
    def test_dependency_order_and_codex_gate(self):
        rid=loop.create_run(self.db,"sample",[task(),task("b",["a"])])
        self.assertEqual(loop.tick(self.db,rid),"RUNNING")
        self.assertEqual(loop.tick(self.db,rid),"AWAITING_FINAL_REVIEW")
        self.assertEqual(loop.status(self.db,rid)["run"]["status"],"AWAITING_FINAL_REVIEW")
        with self.assertRaises(ValueError):loop.final_review(self.db,rid,"approved","looks good","gemini")
        self.assertEqual(loop.final_review(self.db,rid,"approved","Codex manual review receipt"),"COMPLETE")
    def test_bad_output_retries_then_blocks(self):
        rid=loop.create_run(self.db,"broken",[task(contains="missing",max_attempts=2)])
        self.assertEqual(loop.tick(self.db,rid),"RUNNING")
        self.assertEqual(loop.tick(self.db,rid),"RUNNING")
        self.assertEqual(loop.tick(self.db,rid),"BLOCKED")
    def test_cycles_and_missing_deps(self):
        with self.assertRaises(ValueError):loop.validate_plan([task("a",["b"]),task("b",["a"])])
        with self.assertRaises(ValueError):loop.validate_plan([task("a",["not_found"])])
    def test_provider_never_simulated(self):
        r=task();r["worker"]="codex"
        rid=loop.create_run(self.db,"no fake work",[r])
        loop.tick(self.db,rid)
        self.assertEqual(loop.status(self.db,rid)["tasks"][0]["state"],"REPAIR_PENDING")
    def test_approval_single_use(self):
        rid=loop.create_run(self.db,"approval",[task()])
        aid=loop.request_approval(self.db,rid,"publish",3)
        loop.decide_approval(self.db,aid,False)
        with self.assertRaises(ValueError):loop.decide_approval(self.db,aid,True)
    def test_pause(self):
        rid=loop.create_run(self.db,"pause",[task()])
        with self.db:self.db.execute("UPDATE runs SET paused=1 WHERE id=?",(rid,))
        self.assertEqual(loop.tick(self.db,rid),"QUEUED")

if __name__=="__main__":unittest.main()
