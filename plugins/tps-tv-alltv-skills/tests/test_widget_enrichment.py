import copy
import json
import pathlib
import runpy
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "map_widget_enrichment.py"
HELPER = runpy.run_path(str(SCRIPT))


class WidgetEnrichmentTests(unittest.TestCase):
    def setUp(self):
        self.provider = {
            "meta": {
                "schema_version": "2.1",
                "context_scope": "anchor_only",
                "context_profile": "widget_enrichment",
                "enrichment_fields": sorted(HELPER["ENRICHMENT_FIELDS"]),
                "workfront_ids": {
                    "program_id": "account-a", "project_id": "project-a",
                    "request_id": "issue-a",
                },
            },
            "account_firmographics": {"sub_name": "SUB"},
            "record_links": {
                "primary_opportunity_project": "project-link",
                "tv_request_issue": "request-link",
            },
            "objectives": "Request goals",
            "use_cases": ["Selected use case"],
            "products_in_scope": ["Product"],
            "timeline": {"proposed_due": "2026-10-15"},
            "influenced_pipeline_usd": {
                "net_new_usd": 100, "renewed_arr_usd": 50,
                "grand_total_usd": 150, "note": "Primary-only",
            },
            "engagement": {"latest_update": "Must not overwrite native comment"},
        }
        self.payload = {
            "accounts": [
                {"tpsaccountid": "other-account", "sub_name": "Other"},
                {"tpsaccountid": "account-a", "sub_name": "Old", "native": "preserved"},
            ],
            "projects": [
                {"tpsprojectid": "other-project", "objectives": "Sibling"},
                {
                    "tpsprojectid": "project-a", "tpsaccountid": "account-a",
                    "objectives": "Old", "activity": [{"note": "History"}],
                    "requests": [{"tpsrequestid": "nested", "latestcomment": "Nested"}],
                    "techriskcomments": "Fresh correction",
                },
            ],
            "requests": [
                {"tpsrequestid": "other-issue", "products_in_scope": ["Sibling"]},
                {
                    "tpsrequestid": "issue-a", "tpsprojectid": "project-a",
                    "tpsaccountid": "account-a", "is_primary": True,
                    "latestcomment": "Fresh correction",
                    "activity": [{"note": "Request history"}],
                    "sharepoint": {"countassets": 1, "assets": [{"name": "Asset"}]},
                },
            ],
        }

    def test_request_maps_by_guid_and_preserves_native_data(self):
        original = copy.deepcopy(self.payload)
        result, report = HELPER["map_enrichment"]("request", self.provider, self.payload)
        self.assertEqual(result["accounts"][1]["sub_name"], "SUB")
        self.assertEqual(result["projects"][1]["objectives"], "Request goals")
        self.assertEqual(result["requests"][1]["tv_request_link"], "request-link")
        self.assertEqual(result["projects"][1]["primary_opportunity_link"], "project-link")
        self.assertEqual(result["requests"][1]["latestcomment"], "Fresh correction")
        self.assertEqual(result["projects"][1]["techriskcomments"], "Fresh correction")
        self.assertEqual(result["requests"][1]["sharepoint"], original["requests"][1]["sharepoint"])
        self.assertEqual(result["requests"][1]["activity"], original["requests"][1]["activity"])
        for collection in ("accounts", "projects", "requests"):
            self.assertEqual(result[collection][0], original[collection][0])
        self.assertEqual(self.payload, original)
        self.assertEqual(set(report["applied_paths"]), HELPER["ENRICHMENT_FIELDS"])
        self.assertNotIn("meta", result)
        self.assertNotIn("presentationPreference", result)

    def test_opportunity_preserves_nested_requests_without_request_enrichment(self):
        self.provider["meta"]["workfront_ids"]["request_id"] = None
        del self.payload["requests"]
        result, report = HELPER["map_enrichment"]("opportunity", self.provider, self.payload)
        project = result["projects"][1]
        self.assertEqual(project["requests"], self.payload["projects"][1]["requests"])
        self.assertNotIn("primary_opportunity_link", project)
        self.assertNotIn("record_links.tv_request_issue", report["applied_paths"])
        self.assertEqual(project["influenced_pipeline_usd"]["renewed_arr_usd"], 50)
        self.assertEqual(project["influenced_pipeline_usd"]["net_new_usd"], 100)

    def test_selected_empty_clears_but_unselected_placeholder_does_not(self):
        self.provider["meta"]["enrichment_fields"] = ["account_firmographics.sub_name"]
        self.provider["account_firmographics"]["sub_name"] = None
        self.provider["objectives"] = None
        result, report = HELPER["map_enrichment"]("request", self.provider, self.payload)
        self.assertIsNone(result["accounts"][1]["sub_name"])
        self.assertEqual(result["projects"][1]["objectives"], "Old")
        self.assertIn("objectives", report["skipped_paths"])

    def test_legacy_full_result_does_not_clear_from_unknown_null(self):
        del self.provider["meta"]["context_profile"]
        del self.provider["meta"]["enrichment_fields"]
        self.provider["objectives"] = None
        result, _ = HELPER["map_enrichment"]("request", self.provider, self.payload)
        self.assertEqual(result["projects"][1]["objectives"], "Old")

    def test_reduced_result_without_read_evidence_is_rejected(self):
        del self.provider["meta"]["enrichment_fields"]
        with self.assertRaisesRegex(ValueError, "read evidence"):
            HELPER["map_enrichment"]("request", self.provider, self.payload)

    def test_legacy_nested_placeholders_do_not_erase_native_enrichment(self):
        del self.provider["meta"]["context_profile"]
        del self.provider["meta"]["enrichment_fields"]
        self.payload["requests"][1]["timeline"] = {"proposed_due": "2026-10-20"}
        self.provider["timeline"] = {"proposed_due": None, "source": "Unresolved"}
        result, _ = HELPER["map_enrichment"]("request", self.provider, self.payload)
        self.assertEqual(result["requests"][1]["timeline"], {"proposed_due": "2026-10-20"})

    def test_zero_monetary_values_remain_confirmed_values(self):
        del self.provider["meta"]["context_profile"]
        del self.provider["meta"]["enrichment_fields"]
        self.provider["influenced_pipeline_usd"] = {
            "net_new_usd": 0, "renewed_arr_usd": 0, "grand_total_usd": 0,
        }
        result, _ = HELPER["map_enrichment"]("request", self.provider, self.payload)
        self.assertEqual(result["projects"][1]["influenced_pipeline_usd"]["net_new_usd"], 0)

    def test_wrong_scope_profile_or_selected_path_is_rejected(self):
        for field, value in (
            ("context_scope", "family"),
            ("context_profile", "unknown"),
            ("enrichment_fields", ["engagement.latest_update"]),
        ):
            with self.subTest(field=field):
                provider = copy.deepcopy(self.provider)
                provider["meta"][field] = value
                with self.assertRaises(ValueError):
                    HELPER["map_enrichment"]("request", provider, self.payload)

    def test_duplicate_missing_and_contradictory_anchor_ids_are_rejected(self):
        for variant in ("duplicate", "missing", "mismatch"):
            with self.subTest(variant=variant):
                payload = copy.deepcopy(self.payload)
                if variant == "duplicate":
                    payload["projects"].append(copy.deepcopy(payload["projects"][1]))
                elif variant == "missing":
                    payload["requests"].pop()
                else:
                    payload["requests"][1]["tpsprojectid"] = "wrong"
                with self.assertRaises(ValueError):
                    HELPER["map_enrichment"]("request", self.provider, payload)

    def test_large_history_is_preserved_not_truncated(self):
        history = [{"note": f"History {index} " + "x" * 100} for index in range(300)]
        self.payload["requests"][1]["activity"] = history
        result, _ = HELPER["map_enrichment"]("request", self.provider, self.payload)
        self.assertEqual(result["requests"][1]["activity"], history)
        self.assertEqual(len(result["requests"][1]["activity"]), 300)

    def test_cli_writes_exact_envelope_and_separate_measured_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            provider = root / "provider.json"
            payload = root / "payload.json"
            output = root / "output.json"
            provider.write_text(json.dumps(self.provider), encoding="utf-8")
            payload.write_text(json.dumps(self.payload), encoding="utf-8")
            process = subprocess.run(
                [sys.executable, str(SCRIPT), "request", str(provider), str(payload), str(output)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(set(result), {"accounts", "projects", "requests"})
            report = json.loads(process.stdout)
            self.assertGreaterEqual(report["mapping_ms"], 0)
            self.assertEqual(report["provider_file_bytes"], provider.stat().st_size)
            self.assertEqual(report["widget_data_bytes"], output.stat().st_size - 1)
            process = subprocess.run(
                [sys.executable, str(SCRIPT), "request", str(provider), str(payload), str(payload)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(process.returncode, 1)
            self.assertIn("must not overwrite", process.stderr)

    def test_mapping_references_match_executable_sources(self):
        copies = [
            (ROOT / "skills" / name / "reference" / "widget-mapping.md").read_bytes()
            for name in ("tps-tv-tvall-request-details", "tps-tv-tvall-opp-details")
        ]
        self.assertEqual(copies[0], copies[1])
        for path in HELPER["ENRICHMENT_FIELDS"]:
            self.assertIn(f"`{path}`", copies[0].decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
