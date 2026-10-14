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
    def test_bad_output_retries_then_fails(self):
        rid=loop.create_run(self.db,"broken",[task(contains="missing",max_attempts=3)])
        self.assertEqual(loop.tick(self.db,rid,backoff_base=0),"RUNNING")
        # second identical failure: brain advises switch_strategy, no alternate worker -> FAILED
        self.assertEqual(loop.tick(self.db,rid,backoff_base=0),"FAILED")
        t=loop.status(self.db,rid)["tasks"][0]
        self.assertEqual((t["state"],t["attempts"]),("FAILED",2))
        self.assertEqual(loop.tick(self.db,rid),"FAILED")
    def test_retry_cap_reaches_failed(self):
        rid=loop.create_run(self.db,"cap",[task(contains="missing",max_attempts=1)])
        self.assertEqual(loop.tick(self.db,rid,backoff_base=0),"FAILED")
        kinds=[r[0] for r in self.db.execute("SELECT kind FROM events WHERE run_id=?",(rid,))]
        self.assertIn("failed",kinds)
    def test_backoff_delays_retry(self):
        import datetime as dt
        t0=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
        rid=loop.create_run(self.db,"backoff",[task(contains="missing",max_attempts=3)])
        loop.tick(self.db,rid,backoff_base=10,clock=lambda:t0)
        loop.tick(self.db,rid,backoff_base=10,clock=lambda:t0+dt.timedelta(seconds=5))
        self.assertEqual(loop.status(self.db,rid)["tasks"][0]["attempts"],1)
        loop.tick(self.db,rid,backoff_base=10,clock=lambda:t0+dt.timedelta(seconds=11))
        self.assertEqual(loop.status(self.db,rid)["tasks"][0]["attempts"],2)
        self.assertEqual(loop.backoff_seconds(3,10),40)
        self.assertEqual(loop.backoff_seconds(50,10),loop.BACKOFF_MAX_SECONDS)
    def test_switch_strategy_fails_closed_without_alternative(self):
        r=task();r["worker"]="deepseek";r["max_attempts"]=4
        rid=loop.create_run(self.db,"switch",[r])
        loop.tick(self.db,rid,backoff_base=0);loop.tick(self.db,rid,backoff_base=0)
        # no LLM adapter is available, so switching cannot succeed and the task fails closed
        self.assertEqual(loop.status(self.db,rid)["tasks"][0]["state"],"FAILED")
        r=task();r["worker"]="command";r["acceptance"]={"argv":["bad"]};r["max_attempts"]=4
        rid=loop.create_run(self.db,"switch2",[r])
        loop.tick(self.db,rid,backoff_base=0)
        loop.tick(self.db,rid,backoff_base=0)
        t=loop.status(self.db,rid)["tasks"][0]
        self.assertEqual(t["state"],"FAILED")
    def test_critical_incident_blocks(self):
        rid=loop.create_run(self.db,"crit",[task()])
        with self.db:loop.treasurer.incident(self.db,rid,"critical","test",{})
        self.assertEqual(loop.tick(self.db,rid),"BLOCKED")
    def test_approval_levels(self):
        rid=loop.create_run(self.db,"lv",[task()])
        self.assertTrue(loop.request_approval(self.db,rid,"publish","external"))
        with self.assertRaises(ValueError):loop.request_approval(self.db,rid,"x","read")
        with self.assertRaises(ValueError):loop.request_approval(self.db,rid,"x","bogus")
    def test_control_transitions(self):
        with self.assertRaises(ValueError):loop.control(self.db,"run-missing","pause")
        rid=loop.create_run(self.db,"ctl",[task()])
        with self.assertRaises(ValueError):loop.control(self.db,rid,"resume")
        loop.control(self.db,rid,"pause")
        with self.assertRaises(ValueError):loop.control(self.db,rid,"pause")
        self.assertEqual(loop.tick(self.db,rid),"QUEUED")
        self.assertEqual(loop.control(self.db,rid,"resume"),"QUEUED")
        self.assertEqual(loop.control(self.db,rid,"cancel"),"CANCELLED")
        for a in ("resume","pause","cancel"):
            with self.assertRaises(ValueError):loop.control(self.db,rid,a)
        rid=loop.create_run(self.db,"done",[task()])
        loop.tick(self.db,rid);loop.final_review(self.db,rid,"approved","receipt")
        with self.assertRaises(ValueError):loop.control(self.db,rid,"resume")
        with self.assertRaises(ValueError):loop.control(self.db,rid,"cancel")
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
    def test_run_loop_completes_to_review_gate(self):
        rid=loop.create_run(self.db,"run",[task(),task("b",["a"])])
        out=loop.run_loop(self.db,rid,sleep=lambda s:self.fail("no sleep needed"))
        self.assertEqual((out["status"],out["ticks"],out["stopped"]),("AWAITING_FINAL_REVIEW",2,"run_state"))
    def test_run_loop_backs_off_then_fails(self):
        import datetime as dt
        now=[dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)];slept=[]
        def sleep(s):slept.append(s);now[0]+=dt.timedelta(seconds=s)
        rid=loop.create_run(self.db,"bad",[task(contains="missing",max_attempts=3)])
        out=loop.run_loop(self.db,rid,backoff_base=5,sleep=sleep,clock=lambda:now[0])
        self.assertEqual(out["status"],"FAILED")
        self.assertEqual(slept,[5])
    def test_run_loop_caps(self):
        rid=loop.create_run(self.db,"cap",[task(),task("b",["a"])])
        self.assertEqual(loop.run_loop(self.db,rid,max_ticks=1)["stopped"],"max_ticks")
        rid=loop.create_run(self.db,"slow",[task(contains="missing",max_attempts=3)])
        out=loop.run_loop(self.db,rid,backoff_base=100,max_seconds=10,sleep=lambda s:self.fail("must not sleep past cap"))
        self.assertEqual(out["stopped"],"max_seconds")
        with self.assertRaises(ValueError):loop.run_loop(self.db,rid,max_ticks=0)
    def test_run_loop_respects_pause_and_cancel(self):
        rid=loop.create_run(self.db,"p",[task()])
        loop.control(self.db,rid,"pause")
        self.assertEqual(loop.run_loop(self.db,rid)["stopped"],"paused")
        loop.control(self.db,rid,"cancel")
        self.assertEqual(loop.run_loop(self.db,rid)["status"],"CANCELLED")
    def test_run_cli_end_to_end(self):
        import subprocess,sys,json
        tool=str(Path(loop.__file__));dbp=str(Path(self.tmp.name)/"cli.db")
        plan=str(Path(loop.__file__).resolve().parents[1]/"examples"/"atlas-loop-plan.json")
        rid=json.loads(subprocess.check_output([sys.executable,tool,"--db",dbp,"start",plan]))["run_id"]
        out=json.loads(subprocess.check_output([sys.executable,tool,"--db",dbp,"run",rid,"--max-ticks","10"]))
        self.assertEqual(out["status"],"AWAITING_FINAL_REVIEW")

if __name__=="__main__":unittest.main()
