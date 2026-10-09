import copy
import json
import pathlib
import runpy
import unittest


ROOT = pathlib.Path(__file__).resolve().parent.parent
VALIDATOR = runpy.run_path(str(ROOT / "scripts" / "validate.py"))
SCHEMA = json.loads((ROOT / "schemas" / "context.schema.json").read_text(encoding="utf-8"))


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


class ContextContractTests(unittest.TestCase):
    def setUp(self):
        self.context = json.loads(
            (ROOT / "skills" / "get-tps-central-context" / "reference" / "context-schema.json")
            .read_text(encoding="utf-8"),
            object_pairs_hook=unique_object,
        )
        self.context["meta"]["generated_at"] = "2026-10-07T20:00:00Z"
        self.context["meta"]["anchor"]["type"] = "request_id"
        self.context["meta"]["anchor"]["value"] = "test-issue-guid"
        self.context["meta"]["workfront_ids"] = {
            "request_id": "test-issue-guid",
            "project_id": "test-project-guid",
            "program_id": "test-program-guid",
        }
        self.context["meta"]["context_scope"] = "anchor_only"
        self.context["pipeline_stage"]["status"] = "post_request"

    def errors(self, context):
        errors = []
        VALIDATOR["_validate"](context, SCHEMA, "", errors)
        VALIDATOR["validate_context_profile"](context, errors)
        return errors

    def test_request_context_matches_nested_contract(self):
        self.context["opportunity"]["opportunity_details"]["success_criteria"] = "Validated"
        self.assertEqual(self.errors(self.context), [])

    def test_opportunity_and_manual_contexts_allow_missing_request_ids(self):
        for anchor, status in (("opportunity_id", "pre_request"), ("manual", "needs_input")):
            with self.subTest(anchor=anchor):
                context = copy.deepcopy(self.context)
                context["meta"]["anchor"]["type"] = anchor
                context["meta"]["workfront_ids"]["request_id"] = None
                context["pipeline_stage"]["status"] = status
                self.assertEqual(self.errors(context), [])

    def test_family_scope_remains_supported(self):
        self.context["meta"]["context_scope"] = "family"
        self.assertEqual(self.errors(self.context), [])

    def test_reduced_profile_keeps_shape_and_declares_read_evidence(self):
        self.context["meta"]["context_profile"] = "widget_enrichment"
        self.context["meta"]["enrichment_fields"] = ["objectives"]
        self.context["data_quality_flags"] = ["Reduced enrichment; excluded deep context"]
        self.assertEqual(self.errors(self.context), [])
        self.context["meta"]["context_scope"] = "family"
        self.assertTrue(any("requires anchor_only" in error for error in self.errors(self.context)))

    def test_reduced_profile_requires_evidence_and_limitations(self):
        self.context["meta"]["context_profile"] = "widget_enrichment"
        errors = self.errors(self.context)
        self.assertTrue(any("enrichment_fields" in error for error in errors))
        self.assertTrue(any("data_quality_flags" in error for error in errors))
        self.context["meta"]["enrichment_fields"] = ["engagement.latest_update"]
        self.assertTrue(any("enrichment_fields" in error for error in self.errors(self.context)))

    def test_legacy_full_profile_and_invalid_profile(self):
        del self.context["meta"]["context_profile"]
        self.assertEqual(self.errors(self.context), [])
        self.context["meta"]["context_profile"] = "unknown"
        self.assertTrue(any("context_profile" in error for error in self.errors(self.context)))

    def test_root_details_do_not_replace_required_nested_details(self):
        self.context["opportunity_details"] = self.context["opportunity"].pop("opportunity_details")
        self.assertIn(
            "opportunity.opportunity_details: required property is missing",
            self.errors(self.context),
        )

    def test_old_schema_version_is_rejected(self):
        self.context["meta"]["schema_version"] = "2.0"
        self.assertTrue(any("meta.schema_version" in error for error in self.errors(self.context)))

    def test_missing_id_contract_and_invalid_scope_are_rejected(self):
        del self.context["meta"]["workfront_ids"]["project_id"]
        self.context["meta"]["context_scope"] = "unknown"
        errors = self.errors(self.context)
        self.assertTrue(any("meta.workfront_ids.project_id" in error for error in errors))
        self.assertTrue(any("meta.context_scope" in error for error in errors))

    def test_context_is_default_schema(self):
        expected = ROOT / "schemas" / "context.schema.json"
        self.assertEqual(VALIDATOR["resolve_schema"](None, "account.json"), expected)
        self.assertEqual(VALIDATOR["resolve_schema"]("context", "account.json"), expected)
        self.assertTrue(expected.is_file())

    def test_provider_profiles_project_fields_before_querying(self):
        skill = ROOT / "skills" / "get-tps-central-context"
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        profile = (skill / "reference" / "query-profiles.md").read_text(encoding="utf-8")
        self.assertIn("context_profile: full", text)
        self.assertIn("execute only the selected reads", text)
        self.assertIn("no documented projection capability", profile)
        self.assertIn("does not reduce Workfront response size", profile)
        self.assertIn("Do not fetch excluded fields", profile)
        self.assertIn("meta.enrichment_fields", profile)
        self.assertIn("not complete artifact-grounding context", " ".join(profile.split()))

    def test_adapter_common_fields_and_tpsc_nesting(self):
        skills = ROOT.parent / "tps-tv-alltv-skills" / "skills"
        common = set(self.context) - {"linked_opportunities"}
        for name in ("tps-tv-tvall-request-details", "tps-tv-tvall-opp-details"):
            with self.subTest(skill=name):
                path = skills / name / "reference" / "context-schema.json"
                shape = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
                self.assertLessEqual(common, set(shape))
                self.assertIn("opportunity_details", shape["opportunity"])
                self.assertEqual(
                    set(shape["tpsc"]["ids"]), {"tpsaccountid", "tpsprojectid", "tpsrequestid"}
                )
                self.assertIsInstance(shape["tpsc"]["requests"], list)
                if name == "tps-tv-tvall-opp-details":
                    self.assertEqual(shape["tpsc"]["requests"], [])
                    self.assertIsInstance(shape["tpsc"]["project"]["requests"], list)
                    self.assertIsInstance(shape["tpsc"]["project"]["activity"], list)
                    self.assertEqual(shape["tpsc"]["source"], "tps_tv_read_tpsc_opp_detail")
                else:
                    self.assertIn("activity", shape["tpsc"]["requests"][0])
                    self.assertIn("sharepoint", shape["tpsc"])


if __name__ == "__main__":
    unittest.main()
