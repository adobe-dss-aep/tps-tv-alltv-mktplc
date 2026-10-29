import json
import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]


class PublicDistributionTests(unittest.TestCase):
    def test_marketplace_and_plugin_names_match(self):
        marketplace = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        names = [entry["name"] for entry in marketplace["plugins"]]
        self.assertEqual(set(names), {"tps-tv-alltv-skills", "cxl-workbench-alltv"})
        self.assertEqual(len(names), len(set(names)))
        for entry in marketplace["plugins"]:
            manifest = json.loads(
                (ROOT / entry["source"] / ".claude-plugin" / "plugin.json")
                .read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["name"], entry["name"])

    def test_skills_are_public_and_local_references_exist(self):
        skills = list((ROOT / "plugins").glob("*/skills/*/SKILL.md"))
        self.assertEqual(len(skills), 6)
        self.assertIn("tps-tv-alltv-my-team", {skill.parent.name for skill in skills})
        for skill in skills:
            with self.subTest(skill=skill.parent.name):
                text = skill.read_text(encoding="utf-8")
                frontmatter = text.split("---", 2)[1]
                self.assertRegex(frontmatter, r"visibility: public")
                self.assertRegex(frontmatter, rf"name: {re.escape(skill.parent.name)}\n")
                for match in re.finditer(r"`(reference/[a-zA-Z0-9_.-]+)`", text):
                    self.assertTrue((skill.parent / match.group(1)).is_file(), match.group(1))

    def test_no_private_asset_files_or_connector_declaration(self):
        for path in (ROOT / "plugins").rglob("*"):
            if not path.is_file():
                continue
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotEqual(path.name, ".mcp.json")
                self.assertNotIn(path.suffix.lower(), {".csv", ".xlsx", ".plugin"})
                self.assertFalse(path.name.startswith("field-map"))
                self.assertFalse(path.name.startswith("worked-examples"))
                if path.name.startswith("context-") and path.suffix == ".json":
                    self.assertEqual(path.name, "context-schema.json")

    def test_shared_provider_and_refresh_instructions_match(self):
        skills = ROOT / "plugins" / "tps-tv-alltv-skills" / "skills"
        details = ["tps-tv-tvall-request-details", "tps-tv-tvall-opp-details"]
        provider_copies = [
            (skills / name / "reference" / "context-provider.md").read_bytes()
            for name in details
        ]
        self.assertEqual(provider_copies[0], provider_copies[1])
        refresh_copies = [
            (skills / name / "reference" / "same-day-refresh.md").read_bytes()
            for name in details
        ]
        self.assertEqual(len(set(refresh_copies)), 1)
        self.assertIn(b"every new ask", refresh_copies[0])


if __name__ == "__main__":
    unittest.main()
