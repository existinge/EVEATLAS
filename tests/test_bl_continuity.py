"""Private BL continuity regression tests (synthetic title data only)."""
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from bl_continuity import norm, run, build_index, check_candidate

class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.base={"watch":[
            {"Title":"The Rose Chapter","Status":"Completed","Country":"Japan","Year":2025,"Score":9},
            {"Title":"The Star","Status":"Maybe","Country":"Taiwan","Year":2022},
            {"Title":"The Star","Status":"Skip","Country":"Thailand","Year":2024}],
            "aliases":[{"Canonical Title":"The Rose Chapter","Alias":"Rose Story"}],
            "manual_overrides":[{"Title":"Hidden Garden","Status":"MANUAL-SEEN"}],
            "explicit_deltas":[],
            "r77_research_only":[{"title":"Summer Neon","region":"Korea","user_status":None}]}

    def test_normalization(self):
        self.assertEqual(norm(" ＲＯＳＥ—Story! "),"rosestory")
    def test_known_titles_are_blocked(self):
        i=build_index(self.base)
        for title in ("Rose Story","The Rose Chapter","Hidden Garden","Summer Neon"):
            self.assertEqual(check_candidate({"title":title},i)["gate"],"KNOWN_TRACKED")
    def test_research_record_does_not_shadow_watch(self):
        state={**self.base,"r77_research_only":[*self.base["r77_research_only"],
               {"title":"The Rose Chapter","region":"Japan"}]}
        result=check_candidate({"title":"The Rose Chapter"},build_index(state))
        self.assertEqual(result["gate"],"KNOWN_TRACKED")
        self.assertEqual(result["status"],"Completed")

    def test_homonyms_require_disambiguation(self):
        self.assertEqual(check_candidate({"title":"The Star"},build_index(self.base))["gate"],
                         "IDENTITY_UNRESOLVED")
    def test_explicit_seen_does_not_imply_completed_rating(self):
        r=run(self.base,feedback=[{"title":"Hidden Garden","status":"Seen"}])
        self.assertEqual(r["applied_feedback_count"],1)
        self.assertNotIn("Completed",str(r["candidate_audit"]))
    def test_fuzzy_name_requires_review(self):
        self.assertEqual(check_candidate({"title":"The Rose Chaptr"},build_index(self.base))["gate"],
                         "IDENTITY_UNRESOLVED")
    def test_incomplete_source_fails_closed(self):
        self.assertEqual(check_candidate({"title":"Brand New Couple"},build_index(self.base))["gate"],
                         "UNVERIFIED_NOVELTY")

if __name__=="__main__":
    unittest.main()
