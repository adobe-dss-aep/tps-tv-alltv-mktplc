import json
import pathlib
import re
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

    def test_my_team_is_a_standalone_widget_skill(self):
        text = skill_text("tps-tv-alltv-my-team")
        self.assertIn("name: tps-tv-alltv-my-team\n", text)
        self.assertIn("# My Team", text)
        self.assertIn("`tps-tv-myteam` is the widget's name", text)
        self.assertIn("renders the widget in one call", text)
        self.assertIn("Call once per new ask", text)
        self.assertIn("empty argument object `{}`", text)
        self.assertIn("advertised schema", text)
        self.assertNotIn("reference/", text)

    def test_my_team_preserves_identity_and_other_readout_preferences(self):
        text = skill_text("tps-tv-alltv-my-team")
        self.assertIn("Omit `displayName` and `email`", text)
        self.assertIn("testing-only identity overrides", text)
        self.assertIn("only\n   opens the signed-in user's team", text)
        self.assertIn("not overwrite `presentationPreference.useWidget`", text)
        self.assertIn("errors explicitly", text)
        self.assertIn("not a successful\n   widget display", text)

    def test_my_team_does_not_gather_member_pipelines(self):
        text = skill_text("tps-tv-alltv-my-team")
        self.assertIn("Do not call `tps_tv_read_tpsc_user_summary`", text)
        self.assertIn("does not require the CXL context provider", text)
        self.assertIn("or run the summary refresh phase", text)
        self.assertIn("subsequent person's pipeline request", text)
        self.assertIn("`tps-tv-tvall-my-opp-summary`", text)

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

    def test_summary_discovers_workfront_before_tpsc_fetch(self):
        discovery = self.summary.index("## Step 0a: Discover Workfront")
        fetch = self.summary.index("## Step 1: Fetch")
        self.assertLess(discovery, fetch)
        phase = self.summary[discovery:fetch]
        for tool in (
            "insights_read_docs", "insights_list_entities",
            "insights_search_fields", "insights_get_field_paths",
            "insights_find_workfront_data",
        ):
            self.assertIn(tool, phase)
        self.assertIn("server namespaces", phase)
        self.assertIn("does not discover the separate Workfront", self.summary)
        self.assertIn('enrichment "optional"', self.summary)

    def test_summary_refresh_phase_is_self_contained(self):
        checks = self.summary.index("## Step 2: Mandatory native timestamp calls")
        refresh = self.summary.index("## Step 3: Refresh records changed today")
        gate = self.summary.index("## Step 4: Completion gate")
        for document in ("mcp-usage", "conditions", "implicit-patterns", "dates"):
            self.assertIn(document, self.summary[checks:refresh])
        phase = self.summary[refresh:gate]
        self.assertIn("insights_find_workfront_data", phase)
        self.assertIn("issue-rooted", phase)
        self.assertIn("project-rooted", phase)
        self.assertIn("lastUpdateDate", phase)
        for field in (
            "requeststage", "requesthealth", "blockerinfo", "latestcomment",
            "techcasestatus", "techriskcomments",
        ):
            self.assertIn(field, phase)
        self.assertIn("not a delegated execution step", self.summary)

    def test_summary_checks_large_portfolios_and_reports_query_evidence(self):
        self.assertIn("No project-count cutoff", self.summary)
        self.assertIn("Do not sample", self.summary)
        self.assertIn("skip project-only entries", self.summary)
        self.assertIn("report the unchecked counts", self.summary)
        gate = self.summary[self.summary.index("## Step 4: Completion gate"):]
        self.assertIn("Workfront freshness", gate)
        self.assertIn("timestamp-query", gate)
        self.assertIn("field-refresh-query", gate)
        self.assertIn("missing-ID entries", gate)
        self.assertIn("this invocation's evidence", gate)

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


    def test_detail_references_are_adapter_only(self):
        shared = {
            "context-provider.md",
            "context-schema.json",
            "same-day-refresh.md",
            "widget-preference.md",
        }
        for name in READ_SKILLS[1:]:
            with self.subTest(skill=name):
                expected = set(shared)
                if name == "tps-tv-tvall-request-details":
                    expected.add("tpsc-request-details-submission-schema.json")
                reference = SKILLS / name / "reference"
                self.assertEqual(
                    {path.name for path in reference.iterdir()}, expected
                )
                for resource in re.findall(
                    r"`(reference/[a-zA-Z0-9_.-]+)`", skill_text(name)
                ):
                    self.assertTrue((SKILLS / name / resource).is_file(), resource)
                self.assertIn("not an extraction", skill_text(name))

    def test_request_upload_submission_copies_match(self):
        filename = "tpsc-request-details-submission-schema.json"
        request = SKILLS / "tps-tv-tvall-request-details" / "reference" / filename
        upload = SKILLS / "tps-tv-tvall-add-to-sharepoint" / "reference" / filename
        self.assertEqual(request.read_bytes(), upload.read_bytes())


if __name__ == "__main__":
    unittest.main()
