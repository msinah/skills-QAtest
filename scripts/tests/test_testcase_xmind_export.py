import contextlib
import io
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
EXPORTERS = [
    ROOT / "skills/zh/testing-types/test-case-writing/scripts/export_xmind.py",
    ROOT / "skills/en/testing-types/test-case-writing/scripts/export_xmind.py",
    ROOT / "skills/zh/testing-types/testcase-writer-plus/scripts/export_xmind.py",
    ROOT / "skills/en/testing-types/testcase-writer-plus/scripts/export_xmind.py",
]


def load_exporter(path: Path, index: int):
    spec = importlib.util.spec_from_file_location(f"xmind_exporter_{index}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestcaseXmindExportTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.directory = Path(self.temp_dir.name)
        self.template = self.directory / "blank.xmind"
        self.input_path = self.directory / "cases.json"
        self.payload = {
            "title": "Order test cases",
            "cases": [
                {
                    "case_id": "TC-001",
                    "title": "Submit order",
                    "priority": "P0",
                    "type": "positive",
                    "trace": ["REQ-1"],
                    "preconditions": ["User is signed in"],
                    "test_data": ["Valid item"],
                    "steps": ["Open page", "Submit"],
                    "expected_result": ["Order is created"],
                }
            ],
            "traceability": [{"trace": "REQ-1", "case_ids": ["TC-001"]}],
            "assumptions": ["None"],
        }
        self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")
        sheets = [{
            "id": "sheet-id",
            "class": "sheet",
            "rootTopic": {
                "id": "root-id",
                "title": "Blank",
                "children": {"attached": []},
            },
        }]
        with zipfile.ZipFile(self.template, "w") as archive:
            archive.writestr("content.json", json.dumps(sheets))
            archive.writestr("preserved-entry.txt", "keep")

    def test_all_bilingual_exporters_preserve_template_and_case_data(self):
        for index, path in enumerate(EXPORTERS):
            with self.subTest(path=path):
                exporter = load_exporter(path, index)
                output = self.directory / f"cases-{index}.xmind"
                language = "zh" if index % 2 == 0 else "en"
                exporter.export(self.input_path, self.template, output, language)

                with zipfile.ZipFile(output) as archive:
                    self.assertEqual(archive.testzip(), None)
                    self.assertEqual(archive.read("preserved-entry.txt"), b"keep")
                    sheets = json.loads(archive.read("content.json"))

                root = sheets[0]["rootTopic"]
                self.assertEqual(root["title"], "Order test cases")
                topics = root["children"]["attached"]
                serialized = json.dumps(topics, ensure_ascii=False)
                for expected in ("TC-001", "Submit order", "REQ-1", "Open page", "Order is created"):
                    self.assertIn(expected, serialized)

                ids = []

                def collect(node):
                    if isinstance(node, dict):
                        if "id" in node:
                            ids.append(node["id"])
                        for value in node.values():
                            collect(value)
                    elif isinstance(node, list):
                        for value in node:
                            collect(value)

                collect(sheets)
                self.assertEqual(len(ids), len(set(ids)))

    def test_empty_cases_are_rejected(self):
        for index, path in enumerate(EXPORTERS):
            with self.subTest(path=path):
                exporter = load_exporter(path, index)
                bad_input = self.directory / f"empty-{index}.json"
                bad_input.write_text(json.dumps({"cases": []}), encoding="utf-8")
                with self.assertRaises(ValueError):
                    exporter.export(
                        bad_input,
                        self.template,
                        self.directory / f"bad-{index}.xmind",
                        "zh",
                    )

    def test_bundled_templates_and_team_field_order(self):
        self.payload["fields"] = [
            {"key": "priority", "label": "Severity"},
            {"key": "case_id", "label": "Identifier"},
            {"key": "steps", "label": "Actions"},
        ]
        self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")
        for index, path in enumerate(EXPORTERS):
            with self.subTest(path=path):
                exporter = load_exporter(path, index + 10)
                self.assertTrue(exporter.DEFAULT_TEMPLATE.is_file())
                output = self.directory / f"bundled-{index}.xmind"
                language = "zh" if index % 2 == 0 else "en"
                exporter.export(self.input_path, exporter.DEFAULT_TEMPLATE, output, language)
                with zipfile.ZipFile(output) as archive:
                    sheets = json.loads(archive.read("content.json"))
                root = sheets[0]["rootTopic"]
                case = root["children"]["attached"][0]["children"]["attached"][0]
                labels = [child["title"].split(":", 1)[0] for child in case["children"]["attached"]]
                expected = ["Severity", "Identifier", "Actions"]
                self.assertEqual(labels, expected)
                self.assertTrue(all("titleUnedited" in node for node in case["children"]["attached"]))

    def test_cli_defaults_to_the_bundled_template(self):
        exporter = load_exporter(EXPORTERS[0], 30)
        output = self.directory / "cli-default.xmind"
        with patch.object(sys, "argv", [
            "export_xmind.py",
            "--input", str(self.input_path),
            "--output", str(output),
        ]), contextlib.redirect_stdout(io.StringIO()):
            exporter.main()
        self.assertTrue(output.is_file())

    def test_test_points_layout_is_compact_and_keeps_case_data_available(self):
        self.payload["layout"] = "test-points"
        self.payload["groups"] = [{"title": "Checkout", "case_ids": ["TC-001"]}]
        self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")

        for index, path in enumerate(EXPORTERS):
            with self.subTest(path=path):
                exporter = load_exporter(path, index + 40)
                output = self.directory / f"test-points-{index}.xmind"
                language = "zh" if index % 2 == 0 else "en"
                exporter.export(self.input_path, exporter.DEFAULT_TEMPLATE, output, language)

                with zipfile.ZipFile(output) as archive:
                    sheets = json.loads(archive.read("content.json"))

                branches = sheets[0]["rootTopic"]["children"]["attached"]
                self.assertEqual([branch["title"] for branch in branches], ["Checkout"])
                case = branches[0]["children"]["attached"][0]
                self.assertEqual(case["title"], "Submit order")
                details = case["children"]["attached"]
                expected_labels = ["操作步骤", "预期结果"] if language == "zh" else ["Steps", "Expected result"]
                self.assertEqual([detail["title"].split(":", 1)[0] for detail in details], expected_labels)
                serialized = json.dumps(details, ensure_ascii=False)
                self.assertIn("Open page", serialized)
                self.assertIn("Order is created", serialized)
                self.assertNotIn("REQ-1", json.dumps(branches, ensure_ascii=False))

    def test_test_points_layout_can_include_supporting_sections(self):
        self.payload["layout"] = "test-points"
        self.payload["include_supporting_sections"] = True
        self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")
        exporter = load_exporter(EXPORTERS[0], 50)
        output = self.directory / "test-points-supporting.xmind"
        exporter.export(self.input_path, exporter.DEFAULT_TEMPLATE, output, "zh")
        with zipfile.ZipFile(output) as archive:
            sheets = json.loads(archive.read("content.json"))
        titles = [topic["title"] for topic in sheets[0]["rootTopic"]["children"]["attached"]]
        self.assertIn("追踪矩阵", titles)
        self.assertIn("假设与缺口", titles)

    def test_unknown_layout_is_rejected(self):
        self.payload["layout"] = "unknown"
        self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")
        exporter = load_exporter(EXPORTERS[0], 60)
        with self.assertRaises(ValueError):
            exporter.export(
                self.input_path,
                exporter.DEFAULT_TEMPLATE,
                self.directory / "unknown-layout.xmind",
                "zh",
            )

    def test_unknown_case_id_in_group_is_rejected(self):
        self.payload["groups"] = [{"title": "Checkout", "case_ids": ["TC-404"]}]
        self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")
        exporter = load_exporter(EXPORTERS[0], 70)
        with self.assertRaisesRegex(ValueError, "TC-404"):
            exporter.export(
                self.input_path,
                exporter.DEFAULT_TEMPLATE,
                self.directory / "unknown-case-id.xmind",
                "zh",
            )

    def test_supporting_sections_flag_must_be_boolean(self):
        self.payload["layout"] = "test-points"
        self.payload["include_supporting_sections"] = "false"
        self.input_path.write_text(json.dumps(self.payload), encoding="utf-8")
        exporter = load_exporter(EXPORTERS[0], 80)
        with self.assertRaises(ValueError):
            exporter.export(
                self.input_path,
                exporter.DEFAULT_TEMPLATE,
                self.directory / "invalid-supporting-flag.xmind",
                "zh",
            )


if __name__ == "__main__":
    unittest.main()
