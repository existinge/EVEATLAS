import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from genshin_showcase import render_markdown, summarize


CHAR_META = {
    "10000087": {
        "NameTextMapHash": 1504902330,
        "SkillOrder": [10871, 10872, 10875],
        "SideIconName": "UI_AvatarIcon_Side_Neuvillette",
    }
}
LOC = {
    "en": {
        "1504902330": "Neuvillette",
        "4176922867": "Tome of the Eternal Flow",
        "4000000000": "Marechaussee Hunter",
    }
}


class TestShowcase(unittest.TestCase):
    def fixture(self):
        return {
            "ttl": 60,
            "playerInfo": {"nickname": "Fixture", "level": 60, "worldLevel": 9},
            "avatarInfoList": [{
                "avatarId": 10000087,
                "talentIdList": [1],
                "propMap": {"4001": {"val": "90"}},
                "skillLevelMap": {"10871": 10, "10872": 7, "10875": 6},
                "equipList": [
                    {
                        "itemId": 14514,
                        "weapon": {"level": 90, "promoteLevel": 6, "affixMap": {"1": 0}},
                        "flat": {"nameTextMapHash": 4176922867},
                    },
                    {
                        "itemId": 21501,
                        "reliquary": {"level": 21},
                        "flat": {"setNameTextMapHash": 4000000000},
                    },
                ],
            }],
        }

    def test_parses_named_character_weapon_talents_and_sets(self):
        result = summarize(self.fixture(), "654252915", CHAR_META, LOC)
        char = result["characters"][0]
        self.assertEqual(char["name"], "Neuvillette")
        self.assertEqual(char["level"], 90)
        self.assertEqual(char["constellation"], 1)
        self.assertEqual(char["talents"], {"normal": 10, "skill": 7, "burst": 6})
        self.assertEqual(char["weapon"]["name"], "Tome of the Eternal Flow")
        self.assertEqual(char["weapon"]["refinement"], 1)
        self.assertEqual(char["artifact_sets"], {"Marechaussee Hunter": 1})
        self.assertTrue(result["showcase_only"])

    def test_markdown_contains_character(self):
        result = summarize(self.fixture(), "654252915", CHAR_META, LOC)
        md = render_markdown(result)
        self.assertIn("Neuvillette", md)
        self.assertIn("10 / 7 / 6", md)

    def test_fails_closed_if_missing_profile(self):
        with self.assertRaises(ValueError):
            summarize({"avatarInfoList": []}, "654252915", CHAR_META, LOC)

    def test_invalid_characters_field(self):
        with self.assertRaises(ValueError):
            summarize({"playerInfo": {}, "avatarInfoList": "wrong"}, "654252915", CHAR_META, LOC)


if __name__ == "__main__":
    unittest.main()
