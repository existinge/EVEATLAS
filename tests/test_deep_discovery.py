import unittest
from tools.deep_discovery import key, exclusion_index, review, run

class DiscoveryTests(unittest.TestCase):
    def base(self):
        return dict(title="Fresh Title",aliases=["新作"],released=True,central_mm_romance=True,
                    healthy_consent=True,actual_gender_confusion=True,romantic_payoff=True,
                    stream=dict(official_url="https://example.org/episode",region_verified=True,english_subtitles_verified=True),
                    sources=["https://example.org/press"])
    def test_duplicate_alias(self):
        x=self.base()
        self.assertEqual(review(x,exclusion_index([dict(title="Older Name",aliases=["新作"],status="Watched")]))["disposition"],"blocked")
    def test_adaptations_are_distinct(self):
        x=self.base();x["title"]="Love Stage!! Thailand 2022";x["aliases"]=[]
        e=exclusion_index([dict(title="Love Stage!! Japan 2020",status="Watched")])
        self.assertEqual(review(x,e)["disposition"],"verified_candidate")
    def test_stream_access_is_metadata_not_a_gate(self):
        x=self.base();x["stream"]={}
        result=review(x,{})
        self.assertEqual(result["disposition"],"verified_candidate")
        self.assertIn("region_playback_untested",result["access"]["warnings"])
        self.assertIn("english_subtitles_unverified",result["access"]["warnings"])
        self.assertIn("official_stream_url_unverified",result["access"]["warnings"])
    def test_unknown_consent_stays_visible_but_not_verified(self):
        x=self.base();x["healthy_consent"]=False
        self.assertEqual(review(x,{})["disposition"],"research_lead")
        self.assertIn("consent_unverified",review(x,{})["research_gaps"])
    def test_no_quota_filler(self):
        r=run({"known_titles":[],"candidates":[dict(title="Unconfirmed")]})
        self.assertEqual(r["verified"],0)
        self.assertEqual(r["research_leads"],1)
        self.assertEqual(r["discovered"],1)
    def test_unicode_titles(self):
        self.assertEqual(key("宇田川町で待っててよ。"),key("宇田川町で待っててよ"))
    def test_broad_romance_does_not_require_niche_trope(self):
        x=self.base();x.pop("actual_gender_confusion")
        self.assertEqual(review(x,{})["disposition"],"verified_candidate")
    def test_niche_requires_trope_and_specific_evidence(self):
        x=self.base();x["discovery_profile"]="feminine_misidentification"
        self.assertIn("trope_evidence_missing",review(x,{})["blockers"])
        x["trope_evidence"]=["https://example.org/character"]
        self.assertEqual(review(x,{})["disposition"],"verified_candidate")
        x["actual_gender_confusion"]=False
        self.assertIn("trope_unverified",review(x,{})["blockers"])
        x["feminine_presenting_male"]=True
        self.assertEqual(review(x,{})["disposition"],"verified_candidate")
    def test_payload_profile_and_candidate_override(self):
        x=self.base();x.pop("actual_gender_confusion")
        payload=dict(discovery_profile="feminine_misidentification",candidates=[x])
        self.assertEqual(run(payload)["verified"],0)
        x["discovery_profile"]="broad_bl"
        self.assertEqual(run(payload)["verified"],1)
    def test_unknown_profile_fails_closed(self):
        x=self.base();x["discovery_profile"]="anything"
        self.assertIn("unknown_discovery_profile",review(x,{})["blockers"])
    def test_declared_flags_require_json_true(self):
        for field in ["released","central_mm_romance","healthy_consent","romantic_payoff"]:
            for value in ["false","true",1,None]:
                with self.subTest(field=field,value=value):
                    x=self.base();x[field]=value
                    self.assertEqual(review(x,{})["disposition"],"research_lead")
        for field in ["region_verified","english_subtitles_verified"]:
            x=self.base();x["stream"][field]="false"
            self.assertEqual(review(x,{})["disposition"],"verified_candidate")
            self.assertFalse(review(x,{})["access"][field])
    def test_niche_string_true_is_not_evidence(self):
        x=self.base();x["actual_gender_confusion"]="true"
        x["trope_evidence"]=["https://example.org/character"]
        self.assertIn("trope_unverified",review(x,{},"feminine_misidentification")["blockers"])
    def test_all_tracked_statuses_prevent_fresh_claim(self):
        for status in ["Unknown","MANUAL-SEEN","ALIAS-TO-CANONICAL","","Interested","Maybe"]:
            with self.subTest(status=status):
                self.assertEqual(review(self.base(),exclusion_index([dict(title="新作",status=status)]))["disposition"],"blocked")
    def test_missing_title_and_invalid_url_fail_closed(self):
        x=self.base();x["title"]=""
        self.assertIn("identity_unverified",review(x,{})["blockers"])
        for url in ["https://","http://example.org","https://user:password@example.org"]:
            x=self.base();x["stream"]["official_url"]=url;x["sources"]=[url]
            self.assertIn("official_stream_url_unverified",review(x,{})["access"]["warnings"])
            self.assertIn("missing_evidence",review(x,{})["research_gaps"])
    def test_known_title_not_promoted_to_lead(self):
        x=self.base();x["stream"]={}
        result=run({"known_titles":[{"title":"Fresh Title","status":"Maybe"}],"candidates":[x]})
        self.assertEqual(result["excluded"],1)
        self.assertEqual(result["discovered"],0)
    def test_missing_release_or_romance_is_a_lead(self):
        x=self.base();x["released"]=None;x["central_mm_romance"]=None
        result=review(x,{})
        self.assertEqual(result["disposition"],"research_lead")
        self.assertIn("release_unverified",result["research_gaps"])
        self.assertIn("central_romance_unverified",result["research_gaps"])
if __name__=="__main__":unittest.main()
