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
    def test_fail_closed_stream(self):
        x=self.base();x["stream"]["region_verified"]=False
        self.assertIn("stream_unverified",review(x,{})["blockers"])
    def test_fail_closed_coercion(self):
        x=self.base();x["healthy_consent"]=False
        self.assertIn("consent_unverified",review(x,{})["blockers"])
    def test_no_quota_filler(self):
        r=run({"known_titles":[],"candidates":[dict(title="Unconfirmed")]})
        self.assertEqual(r["verified"],0)
    def test_unicode_titles(self):
        self.assertEqual(key("宇田川町で待っててよ。"),key("宇田川町で待っててよ"))
if __name__=="__main__":unittest.main()
