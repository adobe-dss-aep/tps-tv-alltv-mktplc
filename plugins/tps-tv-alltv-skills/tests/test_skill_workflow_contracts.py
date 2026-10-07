import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
READ_SKILLS = (
    "tps-tv-tvall-my-opp-summary",
    "tps-tv-tvall-request-details",
    "tps-tv-tvall-opp-details",
)


def skill_text(name):
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


class SkillWorkflowContractTests(unittest.TestCase):
    """Check instruction wiring, not live model or connector execution."""

    def setUp(self):
        self.summary = skill_text(READ_SKILLS[0])
        self.preference = (
            SKILLS / READ_SKILLS[0] / "reference" / "widget-preference.md"
        ).read_text(encoding="utf-8")

    def test_summary_checks_native_timestamps_before_presenting(self):
        checks = self.summary.index("## Step 2: Mandatory native timestamp calls")
        refresh = self.summary.index("## Step 3: Refresh records changed today")
        gate = self.summary.index("## Step 4: Completion gate")
        self.assertLess(checks, refresh)
        self.assertLess(refresh, gate)
        self.assertIn("insights_find_workfront_data", self.summary[checks:refresh])
        self.assertIn("issue-rooted", self.summary[checks:refresh])
        self.assertIn("project-rooted", self.summary[checks:refresh])
        self.assertIn("tpscrequestid", self.summary[checks:refresh])
        self.assertIn("tpsprojectid", self.summary[checks:refresh])
        self.assertIn("lastUpdateDate", self.summary[checks:refresh])

    def test_summary_does_not_stop_at_reference_loading(self):
        self.assertIn("do not stop at loading the reference", self.summary)
        self.assertIn("No previous-ask record cache", self.summary)
        self.assertIn("freshnessEvidence", self.summary)
        self.assertIn("No entry remains `pending`", self.summary)
        self.assertIn("actual tool results", self.summary)
        self.assertIn("unrefreshed/partially refreshed TPSC snapshot", self.summary)

    def test_summary_onboarding_precedes_data_fetch(self):
        self.assertLess(
            self.summary.index("## Step 0: Resolve presentation"),
            self.summary.index("## Step 1: Fetch"),
        )
        self.assertIn("ask once, and wait", self.summary)
        self.assertIn("retain the original", self.summary)
        self.assertIn("Interactive", self.preference)
        self.assertIn("Conversational text", self.preference)
        self.assertIn("skip onboarding", self.preference)

    def test_preference_is_recovered_not_redefaulted(self):
        self.assertIn("Both `useWidget: true` and `useWidget: false`", self.preference)
        self.assertIn("Never treat", self.preference)
        self.assertIn("false as missing", self.preference)
        self.assertIn("most recent explicit choice", self.preference)
        self.assertIn("does not erase", self.preference)
        self.assertIn("does **not** mean `useWidget: false`", self.preference)
        self.assertIn("without silently changing the preference", self.preference)

    def test_all_preference_reference_copies_match(self):
        contents = [
            (SKILLS / name / "reference" / "widget-preference.md").read_bytes()
            for name in READ_SKILLS
        ]
        self.assertEqual(len(set(contents)), 1)

    def test_details_check_preference_on_fast_and_full_paths(self):
        for name in READ_SKILLS[1:]:
            with self.subTest(skill=name):
                text = skill_text(name)
                self.assertLess(
                    text.index("reference/widget-preference.md"),
                    text.index("### Step 0b:"),
                )
                self.assertIn("Immediately before output", text)
                self.assertIn(
                    "reference/widget-preference.md",
                    text[text.index("### Step 5:"):],
                )
                self.assertIn("presentationPreference", text)
                self.assertIn("preference change", text)

    def test_summary_handoff_carries_the_boolean(self):
        handoff = self.summary[self.summary.index("## Follow-up handoff"):]
        self.assertIn("presentationPreference", handoff)
        self.assertIn("tps-tv-tvall-request-details", handoff)
        self.assertIn("tps-tv-tvall-opp-details", handoff)
        self.assertIn("Do not invoke that provider for every summary row", self.summary)

    def test_adapted_shape_stores_preference_outside_widget_payload(self):
        for name in READ_SKILLS[1:]:
            with self.subTest(skill=name):
                shape = json.loads(
                    (SKILLS / name / "reference" / "context-schema.json")
                    .read_text(encoding="utf-8")
                )
                self.assertEqual(
                    shape["presentationPreference"], {"useWidget": None, "source": None}
                )
                self.assertNotIn("presentationPreference", shape["tpsc"])
                self.assertNotIn("presentationPreference", shape["meta"])
        self.assertIn("not in the provider source or widget `data`", self.preference)


if __name__ == "__main__":
    unittest.main()
