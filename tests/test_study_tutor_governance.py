"""Static smoke tests for Atlas's vendored Socratic tutor governance."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class StudyTutorGovernanceTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / name).read_text(encoding="utf-8-sig")

    def test_vendored_skill_is_discoverable_and_has_consent_gate(self):
        skill = self.read(".agents/skills/socratic-tutor/SKILL.md")
        self.assertIn('name: "socratic-tutor"', skill)
        self.assertIn("confirm intent before starting", skill)
        self.assertIn("two", self.read("02-Agents/Skills/study-tutor-governance.md").lower())

    def test_agent_entrypoint_and_registry_route_study(self):
        self.assertIn("02-Agents/Skills/study-tutor-governance.md", self.read("AGENTS.md"))
        self.assertIn("Study tutor (Socratic)", self.read("02-Agents/Agent Registry.md"))
        self.assertIn("01-Projects/Study Tutor Modes.md", self.read("AGENTS.md"))

    def test_learner_privacy_and_study_adapters(self):
        governance = self.read("02-Agents/Skills/study-tutor-governance.md")
        for phrase in ["Japanese / N4", "Thai / additional languages",
                       "Python / programming", "Public-repo boundary",
                       "two independent checks", "one active question"]:
            self.assertIn(phrase, governance)
        self.assertIn("MIT License", self.read(".agents/skills/socratic-tutor/LICENSE.md"))
        self.assertIn("Jane Street", self.read(".agents/skills/socratic-tutor/UPSTREAM.md"))

if __name__ == "__main__":
    unittest.main()
