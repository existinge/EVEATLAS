"""Synthetic regressions for documented identity-gate failure modes; no private ledger."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.firecrawl_research import IdentityIndex,build_index,run_round,FirecrawlProvider,live_batches,strict_gate

class ResearchGateTests(unittest.TestCase):
    def setUp(self):
        self.checkpoint={"watch":[
            {"Title":"Unfollow","Status":"Completed","Score":6,"Country":"South Korea","Year":2026},
            {"Title":"Unfollow","Status":"Plan to Watch","Score":6,"Country":"South Korea","Year":2026},
            {"Title":"Check in to You","Status":"Watching / Caught Up","Score":8},
            {"Title":"Hold on, Harutora-kun","Status":"Watching / Caught Up","Score":7}],
            "aliases":[{"Canonical Title":"Check in to You","Alias":"\ub108\uc5d0\uac8c \uccb4\ud06c\uc778","Normalized Alias":"#NAME?"}],
            "manual_overrides":[{"Title":"Manual only","Status":"MANUAL-SEEN"}],
            "explicit_deltas":[{"title":"Bad Kid Good Partner","status":"Skip","source":"R66 explicit"}],
            "research_discovery_log":[{"titles":["Old research lead"],"candidates":[{"title":"Prior production","aliases":["Native name"]}]}],
            "canonical_baseline":{"watch_count":4,"alias_count":1,"manual_override_count":1}}
        self.idx=build_index(self.checkpoint)
    def test_skip_and_completed_duplicate_and_backlog(self):
        cases=[("Bad Kid Good Partner","Skip",None),("UNFOLLOW","Completed",6),("Check In to You","Watching / Caught Up",8),("Hold on Harutora-kun","Watching / Caught Up",7)]
        for title,status,score in cases:
            m=self.idx.check({"title":title});self.assertEqual(m["state"],"known");self.assertEqual(m["effective"]["status"],status);self.assertEqual(m["effective"]["score"],score)
    def test_alias_formula_ignored_and_status_linked(self):
        m=self.idx.check({"title":"\ub108\uc5d0\uac8c \uccb4\ud06c\uc778"});self.assertEqual(m["effective"]["status"],"Watching / Caught Up")
        self.assertNotIn("name",self.idx.by_key)
    def test_history_only_and_manual(self):
        for title in ("Old research lead","Native name","Manual only"):
            self.assertEqual(self.idx.check({"title":title})["state"],"known")
    def test_r78_archive_entries(self):
        history={"watch_records":[{"Title":"Older archive only","Status":"Completed"}],"source_sheets":{"R43 Audit":[["Candidate","Notes"],["Research only earlier","other"]]},"latest_explicit_overlay":[]}
        i=build_index(self.checkpoint,historical=history)
        for title in ("Older archive only","Research only earlier"):
            self.assertEqual(i.check({"title":title})["state"],"known")
    def test_pre_evidence_block_and_iterative_batches(self):
        called=[]
        batches=[{"id":"a","candidates":[{"title":"Unfollow"},{"title":"Bad Kid Good Partner"}]},{"id":"b","candidates":[{"title":"Synthetic novel production"}]}]
        r=run_round(self.idx,batches,lambda c:called.append(c["title"]) or c,identity_review=lambda c:{**c,"identity_verified_new":True,"identity_review_sources":["https://example.invalid/identity"]})
        self.assertEqual(called,["Synthetic novel production"]);self.assertEqual(len(r["receipts"]),2);self.assertEqual(len(r["recommendations"]),0)
    def test_native_alias_recheck_before_verify(self):
        called=[]
        r=run_round(self.idx,[{"id":"a","candidates":[{"title":"Unknown local title"}]}],lambda c:called.append(c),identity_review=lambda c:{**c,"aliases":["Unfollow"],"identity_verified_new":True,"identity_review_sources":["https://example.invalid/identity"]})
        self.assertFalse(called);self.assertEqual(len(r["excluded"]),1)
    def test_fuzzy_quarantine(self):
        m=self.idx.check({"title":"Hold on Harutora-kun 2"});self.assertEqual(m["state"],"quarantine")
    def test_unreviewed_not_scraped(self):
        called=[]
        r=run_round(self.idx,[{"id":"a","candidates":[{"title":"Some unheard name"}]}],lambda c:called.append(c))
        self.assertFalse(called);self.assertEqual(len(r["quarantine"]),1)
    def test_provider_operations_and_catalog_replay(self):
        calls=[]
        def transport(op,args):
            calls.append((op,args));return {"json":{"titles":[{"title":"Synthetic novel production"}]}}
        p=FirecrawlProvider(transport);p.search("public query");p.map("https://example.invalid");p.crawl("https://example.invalid",2,["/catalog"])
        receipts=[];b=list(live_batches(p,[{"id":"c","operation":"catalog","url":"https://example.invalid/catalog"}],receipts))
        self.assertEqual([op for op,_ in calls],["search","map","crawl","scrape"]);self.assertEqual(b[0]["candidates"][0]["title"],"Synthetic novel production")
        self.assertNotIn("checkpoint",str(calls))
    def test_short_vertical_and_unverified_rejected(self):
        r=strict_gate({"country":"Japan","runtime_minutes":40,"format":"vertical"});self.assertFalse(r["approved"]);self.assertIn("substantial_runtime",r["reasons"]);self.assertIn("format",r["reasons"])
    def test_fail_closed_missing_watch(self):
        with self.assertRaises(ValueError):build_index({"watch":[]})

if __name__=="__main__":unittest.main()
