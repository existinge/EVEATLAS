import io
import json
import sys
import tempfile
import unittest
import urllib.error
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import atlas_loop as loop
import atlas_providers as prov

def paid_task(id="draft", prompt="Summarize the plan", contains="OK", max_attempts=3, deps=None):
    return {"id": id, "name": id, "worker": "openclaw", "deps": deps or [], "max_attempts": max_attempts,
            "acceptance": {"prompt": prompt, "max_tokens": 200, "contains": contains}}

class FakeResponse(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): self.close()

ENV = {"ATLAS_ENABLE_OPENCLAW": "1", "ATLAS_OPENCLAW_URL": "http://127.0.0.1:18789",
       "ATLAS_OPENCLAW_TOKEN": "test-token", "ATLAS_OPENCLAW_MODEL": "deepseek-flash",
       "ATLAS_OPENCLAW_INPUT_USD_PER_MTOK": "0.3", "ATLAS_OPENCLAW_OUTPUT_USD_PER_MTOK": "1.2"}

class ConfigTests(unittest.TestCase):
    def test_off_by_default(self):
        env = dict(ENV); del env["ATLAS_ENABLE_OPENCLAW"]
        self.assertEqual(prov.configured_providers(env), {})
        self.assertEqual(prov.configured_providers({}), {})
    def test_enabled_requires_full_config(self):
        with self.assertRaises(ValueError): prov.configured_providers({"ATLAS_ENABLE_OPENCLAW": "1"})
        for missing in ("ATLAS_OPENCLAW_URL", "ATLAS_OPENCLAW_TOKEN", "ATLAS_OPENCLAW_MODEL", "ATLAS_OPENCLAW_INPUT_USD_PER_MTOK"):
            env = dict(ENV); del env[missing]
            with self.assertRaises(ValueError): prov.configured_providers(env)
        env = dict(ENV); del env["ATLAS_ENABLE_OPENCLAW"]
        self.assertIn("openclaw", prov.configured_providers(env, enable_openclaw=True))
    def test_provider_built_from_env_without_leaking_token(self):
        p = prov.configured_providers(ENV)["openclaw"]
        self.assertEqual((p.model, p.base_url), ("deepseek-flash", "http://127.0.0.1:18789"))
        self.assertNotIn("test-token", repr(p))
    def test_no_provider_key_env_used(self):
        src = (Path(prov.__file__)).read_text()
        self.assertNotIn("DEEPSEEK_API_KEY", src)
    def test_gateway_url_rules(self):
        ok = prov.validate_gateway_url
        self.assertEqual(ok("http://localhost:9000/"), "http://localhost:9000")
        self.assertEqual(ok("https://gw.example.com:443"), "https://gw.example.com:443")
        for bad in ("", "http://127.0.0.1", "http://10.0.0.5:8080", "ftp://127.0.0.1:1",
                    "http://u:p@127.0.0.1:1", "http://127.0.0.1:1/v1"):
            with self.assertRaises(ValueError): ok(bad)
    def test_registry_marks_openclaw_available_only_when_configured(self):
        names = lambda ws: {w.name for w in ws if w.available}
        self.assertNotIn("openclaw", names(loop.worker_registry()))
        self.assertIn("openclaw", names(loop.worker_registry(providers={"openclaw": prov.FakeProvider([])})))

class FakeGatewayTests(unittest.TestCase):
    """OpenClawProvider against an injected fake gateway opener; no network."""
    def make(self, opener, model="deepseek-flash"):
        return prov.OpenClawProvider("test-token", "http://127.0.0.1:18789", model, "1", "2", opener=opener)
    def gateway(self, payload, seen=None):
        def opener(req, timeout):
            if seen is not None:
                seen.update(url=req.full_url, auth=req.get_header("Authorization"), body=json.loads(req.data))
            return FakeResponse(json.dumps(payload).encode())
        return opener
    def test_request_shape_and_usage(self):
        seen = {}
        out = self.make(self.gateway({"model": "deepseek-flash", "choices": [{"message": {"content": "hi"}}],
                                      "usage": {"prompt_tokens": 10, "completion_tokens": 4}}, seen)).complete("hello", 50)
        self.assertEqual(seen["url"], "http://127.0.0.1:18789/v1/chat/completions")
        self.assertEqual(seen["auth"], "Bearer test-token")
        self.assertEqual((seen["body"]["model"], seen["body"]["max_tokens"], seen["body"]["stream"]), ("deepseek-flash", 50, False))
        self.assertEqual((out["text"], out["input_tokens"], out["output_tokens"]), ("hi", 10, 4))
    def test_model_passthrough(self):
        seen = {}
        self.make(self.gateway({"choices": [{"message": {"content": "x"}}]}, seen), model="deepseek-v4-pro").complete("p", 5)
        self.assertEqual(seen["body"]["model"], "deepseek-v4-pro")
    def test_missing_usage_is_none_not_zero(self):
        out = self.make(self.gateway({"choices": [{"message": {"content": "x"}}]})).complete("p", 5)
        self.assertEqual((out["input_tokens"], out["output_tokens"]), (None, None))
        out = self.make(self.gateway({"choices": [{"message": {"content": "x"}}], "usage": {"prompt_tokens": "3"}})).complete("p", 5)
        self.assertIsNone(out["input_tokens"])
    def test_errors_classified(self):
        def http(code):
            def opener(req, timeout): raise urllib.error.HTTPError(req.full_url, code, "x", {}, None)
            return opener
        with self.assertRaises(prov.ProviderError) as c: self.make(http(401)).complete("p", 5)
        self.assertFalse(c.exception.billable_unknown)
        with self.assertRaises(prov.ProviderError) as c: self.make(http(503)).complete("p", 5)
        self.assertTrue(c.exception.billable_unknown)
        def refused(req, timeout): raise urllib.error.URLError("refused")
        with self.assertRaises(prov.ProviderError) as c: self.make(refused).complete("p", 5)
        self.assertTrue(c.exception.billable_unknown)
        with self.assertRaises(prov.ProviderError): self.make(self.gateway({"choices": []})).complete("p", 5)
    def test_cost_math(self):
        p = prov.FakeProvider([], input_usd_per_mtok="1", output_usd_per_mtok="2")
        self.assertEqual(p.cost(1_000_000, 500_000), Decimal(2))
        self.assertEqual(prov.cost_cents_ceiling(Decimal("0.0001")), 1)

class PaidLoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = loop.connect(Path(self.tmp.name) / "loop.db")
    def tearDown(self):
        self.db.close(); self.tmp.cleanup()
    def approve(self, rid, allow=True):
        aid = self.db.execute("SELECT id FROM approvals WHERE run_id=? AND status='PENDING'", (rid,)).fetchone()[0]
        loop.decide_approval(self.db, aid, allow)
    def reservations(self, rid):
        return [dict(r) for r in self.db.execute("SELECT * FROM cost_reservations WHERE run_id=?", (rid,))]

    def test_end_to_end_with_fake_provider(self):
        fake = prov.FakeProvider(["Plan OK"])
        rid = loop.create_run(self.db, "paid e2e", [{"id": "prep", "name": "prep", "worker": "local", "deps": [],
                              "acceptance": {"content": "ready", "contains": "ready"}}, paid_task(deps=["prep"])], budget=1.0)
        out = loop.run_loop(self.db, rid, providers={"openclaw": fake}, sleep=lambda s: None)
        self.assertEqual(out["status"], "AWAITING_APPROVAL")
        self.assertEqual(fake.calls, [])            # nothing called before approval
        self.assertEqual(self.reservations(rid), [])  # nothing reserved before approval
        self.approve(rid)
        out = loop.run_loop(self.db, rid, providers={"openclaw": fake}, sleep=lambda s: None)
        self.assertEqual(out["status"], "AWAITING_FINAL_REVIEW")
        self.assertEqual(len(fake.calls), 1)
        (res,) = self.reservations(rid)
        self.assertEqual((res["state"], res["source"], res["input_tokens"], res["output_tokens"]),
                         ("settled", "gateway_metered", 100, 50))
        self.assertEqual(res["charged_cents"], 1)  # 100*1/1M + 50*2/1M USD, rounded up to a cent
        self.assertGreaterEqual(res["reserved_cents"], res["charged_cents"])
        task = [t for t in loop.status(self.db, rid)["tasks"] if t["worker"] == "openclaw"][0]
        self.assertEqual(json.loads(task["artifact"])["reservation_id"], res["reservation_id"])
        self.assertEqual(loop.final_review(self.db, rid, "approved", "manual review receipt"), "COMPLETE")

    def test_denied_approval_fails_without_call(self):
        fake = prov.FakeProvider(["OK"])
        rid = loop.create_run(self.db, "deny", [paid_task()])
        self.assertEqual(loop.tick(self.db, rid, providers={"openclaw": fake}), "AWAITING_APPROVAL")
        self.approve(rid, False)
        self.assertEqual(loop.tick(self.db, rid, providers={"openclaw": fake}), "FAILED")
        self.assertEqual(fake.calls, [])

    def test_budget_blocks_before_call(self):
        fake = prov.FakeProvider(["OK"], input_usd_per_mtok="100000", output_usd_per_mtok="100000")
        rid = loop.create_run(self.db, "poor", [paid_task()], budget=0.05)
        loop.tick(self.db, rid, providers={"openclaw": fake}); self.approve(rid)
        self.assertEqual(loop.tick(self.db, rid, providers={"openclaw": fake}), "BLOCKED")
        self.assertEqual((fake.calls, self.reservations(rid)), ([], []))

    def test_uncertain_charge_blocks_further_paid_dispatch(self):
        fake = prov.FakeProvider([prov.ProviderError("timeout", billable_unknown=True), "OK"])
        rid = loop.create_run(self.db, "unc", [paid_task()])
        loop.tick(self.db, rid, providers={"openclaw": fake}); self.approve(rid)
        loop.tick(self.db, rid, providers={"openclaw": fake}, backoff_base=0)
        self.assertEqual(self.reservations(rid)[0]["state"], "uncertain")
        self.assertEqual(loop.tick(self.db, rid, providers={"openclaw": fake}, backoff_base=0), "BLOCKED")
        self.assertEqual(len(fake.calls), 1)

    def test_rejected_request_released_then_retried(self):
        fake = prov.FakeProvider([prov.ProviderError("HTTP 400", billable_unknown=False), "OK"])
        rid = loop.create_run(self.db, "rel", [paid_task()])
        loop.tick(self.db, rid, providers={"openclaw": fake}); self.approve(rid)
        loop.tick(self.db, rid, providers={"openclaw": fake}, backoff_base=0)
        self.assertEqual(loop.tick(self.db, rid, providers={"openclaw": fake}, backoff_base=0), "AWAITING_FINAL_REVIEW")
        self.assertEqual(sorted(r["state"] for r in self.reservations(rid)), ["released", "settled"])

    def test_provider_task_requires_prompt(self):
        t = paid_task(); del t["acceptance"]["prompt"]
        rid = loop.create_run(self.db, "noprompt", [t])
        self.assertEqual(loop.tick(self.db, rid, providers={"openclaw": prov.FakeProvider(["OK"])}), "FAILED")

    def test_missing_usage_left_uncertain(self):
        fake = prov.FakeProvider(["OK", "OK"], input_tokens=None, output_tokens=None)
        rid = loop.create_run(self.db, "nousage", [paid_task(), paid_task("second")])
        loop.tick(self.db, rid, providers={"openclaw": fake}); self.approve(rid)
        self.assertEqual(loop.tick(self.db, rid, providers={"openclaw": fake}), "RUNNING")
        res = self.reservations(rid)[0]
        self.assertEqual((res["state"], res["charged_cents"]), ("uncertain", None))
        # unreconciled charge blocks the next paid dispatch until a human settles it
        self.assertEqual(loop.tick(self.db, rid, providers={"openclaw": fake}), "BLOCKED")
        self.assertEqual(len(fake.calls), 1)
    def test_not_enabled_never_calls(self):
        rid = loop.create_run(self.db, "off", [paid_task()])
        loop.tick(self.db, rid)
        self.assertEqual(loop.status(self.db, rid)["tasks"][0]["state"], "REPAIR_PENDING")
        self.assertEqual(self.reservations(rid), [])

if __name__ == "__main__": unittest.main()
