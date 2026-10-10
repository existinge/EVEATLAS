"""Run: python -m unittest discover -s tests -v"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("signal_desk", Path(__file__).resolve().parents[1] / "tools" / "signal_desk.py")
desk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desk)

def sample(**overrides):
    item = {"claim":"Official account announced X search support", "source_url":"https://x.com/bot/status/2107949161878606089?utm_source=test",
            "published_date":"2026-10-08", "source_type":"official_announcement",
            "evidence":"The account announced the feature; actual coverage remains untested.",
            "decision":"usable_with_narrower_wording", "status":"needs_review"}
    item.update(overrides)
    return item

class SignalDeskTests(unittest.TestCase):
    def test_normalize_and_dedup(self):
        a = desk.validate(sample())
        b = desk.validate(sample(source_url="https://x.com/other/status/2107949161878606089"))
        self.assertEqual(a["event_id"], b["event_id"])
        self.assertNotIn("utm_source", a["source_url"])

    def test_review_gate(self):
        with self.assertRaises(ValueError):
            desk.validate(sample(status="cleared"))
        with self.assertRaises(ValueError):
            desk.validate(sample(status="cleared", reviewed_by="Eve", decision="blocked_until_checked"))

    def test_untrusted_and_missing_source(self):
        for url in ["http://example.com", "https://localhost/a", "https://user:pass@example.com"]:
            with self.assertRaises(ValueError):
                desk.validate(sample(source_url=url))
        with self.assertRaises(ValueError):
            desk.validate({"claim":"Unsupported"})

    def test_brief_only_cleared(self):
        pending = desk.validate(sample())
        cleared = desk.validate(sample(status="cleared", reviewed_by="human", practical_use="Review feedback"))
        self.assertEqual(desk.render_brief([pending])[1], [])
        self.assertEqual(len(desk.render_brief([cleared])[1]), 1)

    def test_run_receipt_and_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "input.json"
            source.write_text(json.dumps([sample(status="cleared", reviewed_by="human")]))
            output, receipt = desk.run(source, base / "db.sqlite", base / "runs")
            self.assertTrue((output / "brief.md").exists())
            self.assertEqual(receipt["brief_count"], 1)
            output2, receipt2 = desk.run(source, base / "db.sqlite", base / "runs")
            self.assertEqual(receipt2["accepted_count"], 0)
            self.assertEqual(receipt2["brief_count"], 0)

    def test_invalid_batch_is_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = desk.connect(Path(tmp) / "db.sqlite")
            try:
                with self.assertRaises(ValueError):
                    desk.ingest(db, [sample(), sample(source_url="http://bad")])
                self.assertEqual(db.execute("SELECT count(*) FROM findings").fetchone()[0], 0)
            finally:
                db.close()

    def test_duplicate_batch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = desk.connect(Path(tmp) / "db.sqlite")
            try:
                with self.assertRaises(ValueError):
                    desk.ingest(db, [sample(), sample()])
            finally:
                db.close()

if __name__ == "__main__":
    unittest.main()
