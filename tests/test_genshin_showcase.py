import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from genshin_showcase import summarize


class TestShowcase(unittest.TestCase):
    def test_parses_realistic_minimal_fixture(self):
        payload = {
            "playerInfo": {"nickname": "Fixture", "level": 60},
            "avatarInfoList": [{
                "avatarId": 10000002,
                "propMap": {"4001": {"val": "90"}},
                "promoteLevel": 6,
                "skillLevelMap": {"1": 10},
                "equipList": [{"itemId": 11501, "weapon": {"level": 90, "promoteLevel": 6}}]
            }]
        }
        result = summarize(payload, "654252915")
        self.assertEqual(result["characters"][0]["avatar_id"], 10000002)
        self.assertEqual(result["characters"][0]["weapon"]["level"], 90)
        self.assertTrue(result["showcase_only"])

    def test_fails_closed_if_missing_profile(self):
        with self.assertRaises(ValueError):
            summarize({"avatarInfoList": []}, "654252915")

    def test_invalid_characters_field(self):
        with self.assertRaises(ValueError):
            summarize({"playerInfo": {}, "avatarInfoList": "wrong"}, "654252915")


if __name__ == "__main__":
    unittest.main()
