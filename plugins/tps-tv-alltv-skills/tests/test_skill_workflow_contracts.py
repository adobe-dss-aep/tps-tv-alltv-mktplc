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
        self.summary_preference = (
            SKILLS / READ_SKILLS[0] / "reference" / "widget-preference.md"
        ).read_text(encoding="utf-8")

        self.preference = (SKILLS / READ_SKILLS[1] / "reference" / "widget-preference.md").read_text(encoding="utf-8")

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

    def test_summary_is_tpsc_only_including_failures_and_refresh_requests(self):
        self.assertIn("The only data source is `tps_tv_read_tpsc_user_summary`", self.summary)
        self.assertIn("In no circumstances use the Workfront connector", self.summary)
        self.assertIn("never perform a Workfront check, even on an explicit refresh request", self.summary)
        self.assertIn("Do not invoke a context provider or detail skill", self.summary)
        self.assertNotIn("insights_", self.summary)
        self.assertNotIn("same-day-refresh.md", self.summary)
        self.assertNotIn("native-id-dictionary.md", self.summary)
        tools = set(re.findall(r"`(tps_tv_[a-z_]+)`", self.summary))
        self.assertEqual(tools, {"tps_tv_read_tpsc_user_summary", "tps_tv_read_tpsc_user_summary_widget"})

    def test_summary_defaults_to_conversation_without_onboarding(self):
        self.assertIn("Conversational text is the default", self.summary)
        self.assertIn("Do not ask a widget-versus-text onboarding question", self.summary)
        self.assertIn("model judgment", self.summary)
        self.assertIn("no explicit choice", self.summary_preference)
        self.assertIn('"useWidget": false, "source": "default"', self.summary_preference)

    def test_summary_requires_explicit_opt_in_not_inference(self):
        self.assertIn("earlier explicit readout opt-in", self.summary)
        self.assertIn("Never infer widget opt-in", self.summary_preference)
        self.assertIn("inferred/default/unknown provenance", self.summary_preference)
        self.assertIn("without erasing the explicit preference", self.summary)
        self.assertIn("unmodified by external", self.summary)

    def test_summary_has_no_workfront_resources(self):
        resources = SKILLS / READ_SKILLS[0] / "reference"
        self.assertEqual({path.name for path in resources.iterdir()}, {"widget-preference.md"})

    def test_details_still_require_workfront_freshness(self):
        copies = [
            (SKILLS / name / "reference" / "same-day-refresh.md").read_bytes()
            for name in READ_SKILLS[1:]
        ]
        self.assertEqual(copies[0], copies[1])
        text = copies[0].decode("utf-8")
        self.assertIn("On **every new ask**", text)
        self.assertIn("timestamp", text)
        for name in READ_SKILLS[1:]:
            self.assertIn("reference/same-day-refresh.md", skill_text(name))

    def test_preference_is_recovered_not_redefaulted(self):
        self.assertIn("Both `useWidget: true` and `useWidget: false`", self.preference)
        self.assertIn("false as missing", self.preference)
        self.assertIn("most recent explicit choice", self.preference)
        self.assertIn("does not erase", self.preference)
        self.assertNotIn("## One-time summary onboarding", self.preference)

    def test_detail_preference_reference_copies_match(self):
        contents = [
            (SKILLS / name / "reference" / "widget-preference.md").read_bytes()
            for name in READ_SKILLS[1:]
        ]
        self.assertEqual(contents[0], contents[1])
        self.assertNotEqual(contents[0], (SKILLS / READ_SKILLS[0] / "reference" / "widget-preference.md").read_bytes())

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
        self.assertIn("Only a separate user request", handoff)

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
            "widget-mapping.md",
            "native-id-dictionary.md",
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

    def test_details_select_profile_by_content_and_execute_mapping(self):
        for name in READ_SKILLS[1:]:
            with self.subTest(skill=name):
                text = skill_text(name)
                self.assertIn("context_profile: widget_enrichment", text)
                self.assertIn("context_profile: full", text)
                self.assertIn("`useWidget` alone never selects", text)
                self.assertIn("Read and execute `reference/widget-mapping.md`", text)
                self.assertIn("meta.enrichment_fields", text)
                self.assertIn("template nulls/empties never", text)

    def test_native_id_dictionary_is_shared_and_loaded_before_reads(self):
        provider = ROOT.parent / "cxl-workbench-alltv" / "skills" / "get-tps-central-context"
        dictionary = (provider / "reference" / "native-id-dictionary.md").read_bytes()
        for name in READ_SKILLS[1:]:
            with self.subTest(skill=name):
                self.assertEqual(
                    (SKILLS / name / "reference" / "native-id-dictionary.md").read_bytes(),
                    dictionary,
                )
                self.assertIn("reference/native-id-dictionary.md", skill_text(name))
        text = dictionary.decode("utf-8")
        for mapping in (
            "| `tpsrequestid` | `issue.id` |",
            "| `tpsprojectid` | `project.id` |",
            "| `tpsaccountid` | `program.id` |",
        ):
            self.assertIn(mapping, text)
        self.assertIn("tpscrequestid", text)
        self.assertIn("project.project_ID", text)
        self.assertIn("No exact issue/program connector field IDs", text)
        self.assertIn("once per session/root", " ".join(text.split()))
        self.assertIn('{"value": "<native ID>"}', text)
        self.assertIn("reference/native-id-dictionary.md", (provider / "SKILL.md").read_text(encoding="utf-8"))

    def test_request_upload_submission_copies_match(self):
        filename = "tpsc-request-details-submission-schema.json"
        request = SKILLS / "tps-tv-tvall-request-details" / "reference" / filename
        upload = SKILLS / "tps-tv-tvall-add-to-sharepoint" / "reference" / filename
        self.assertEqual(request.read_bytes(), upload.read_bytes())


if __name__ == "__main__":
    unittest.main()
