#!/usr/bin/env python3
"""Byte comparison, pinned-clock and failure contracts of check_table_reproduction.py.

A small fake generator mirrors the real ones: it writes a CRLF CSV and a
manifest whose path labels depend on a relative or absolute output directory
and whose time comes from datetime.now(timezone.utc).
"""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
import check_table_reproduction as reproduction

SCRIPT = Path(__file__).with_name("check_table_reproduction.py")
GENERATOR = '''from datetime import datetime, timezone
from pathlib import Path
MODE = {mode!r}


def generate(project_root, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    value = Path(project_root, "input.txt").read_text(encoding="utf-8").strip()
    (output_dir / "values.csv").write_bytes(f"name,value\\r\\nalpha,{{value}}\\r\\n".encode())
    if MODE == "ignores_clock":
        stamp = datetime.fromtimestamp(0, timezone.utc).isoformat()
    else:
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    label = str(output_dir) if not output_dir.is_absolute() else output_dir.name
    (output_dir / "values_manifest.md").write_text(
        f"# Manifest\\n\\nÜretim zamanı (UTC): `{{stamp}}`\\n\\n- `{{label}}/values.csv`\\n- `{{label}}/values_manifest.md`\\n",
        encoding="utf-8")
    if MODE == "extra_file":
        (output_dir / "unexpected.csv").write_text("x\\n", encoding="utf-8")
    if MODE == "raises":
        raise RuntimeError("generator failure")
'''
STAMP = "2026-06-04T12:57:56+00:00"


def manifest(stamp_lines):
    return ("# Manifest\n\n" + "".join(f"{line}\n\n" for line in stamp_lines)
            + "- `outputs/tables/values.csv`\n- `outputs/tables/values_manifest.md`\n")


class TableReproductionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="canakkale-table-reproduction-test-")
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        self.root, self.scripts = base / "project", base / "scripts"
        (self.root / "outputs/tables").mkdir(parents=True)
        self.scripts.mkdir()
        (self.root / "input.txt").write_text("42\n", encoding="utf-8")
        self.write_generator("normal")
        self.record("values.csv", b"name,value\r\nalpha,42\r\n")
        self.record("values_manifest.md", manifest([f"Üretim zamanı (UTC): `{STAMP}`"]).encode())
        self.table_set = {"title": "Örnek tablolar", "module": "fake_tables", "manifest": "values_manifest.md",
                          "files": ["values.csv", "values_manifest.md"]}

    def write_generator(self, mode):
        (self.scripts / "fake_tables.py").write_text(GENERATOR.format(mode=mode), encoding="utf-8")

    def record(self, name, data):
        (self.root / "outputs/tables" / name).write_bytes(data)

    def check(self):
        return reproduction.check_tables(self.table_set, self.root, self.scripts)

    def snapshot(self):
        return {path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.root.rglob("*") if path.is_file()}

    def test_identical_bytes_pass_with_the_recorded_clock_and_relative_labels(self):
        before = self.snapshot()
        result = self.check()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["pinned_generated_utc"], STAMP)
        self.assertEqual([row["status"] for row in result["files"]], ["identical", "identical"])
        self.assertEqual(before, self.snapshot())

    def test_one_changed_byte_fails_and_names_the_file_and_line(self):
        self.record("values.csv", b"name,value\r\nalpha,43\r\n")
        result = self.check()
        self.assertFalse(result["passed"])
        row = result["files"][0]
        self.assertEqual((row["path"], row["status"], row["first_different_line"]), ("outputs/tables/values.csv", "different", 2))

    def test_missing_recorded_file_fails(self):
        (self.root / "outputs/tables/values.csv").unlink()
        result = self.check()
        self.assertFalse(result["passed"])
        self.assertEqual(result["files"][0]["status"], "not_recorded")

    def test_missing_repeated_or_malformed_time_line_fails_before_generation(self):
        cases = {"missing": [], "repeated": [f"Üretim zamanı (UTC): `{STAMP}`"] * 2,
                 "malformed": ["Üretim zamanı (UTC): `2026-06-04 12:57:56`"]}
        for label, lines in cases.items():
            with self.subTest(label=label):
                self.record("values_manifest.md", manifest(lines).encode())
                result = self.check()
                self.assertFalse(result["passed"])
                self.assertIsNone(result["pinned_generated_utc"])
                self.assertEqual(result["files"], [])

    def test_generator_that_ignores_the_pinned_clock_fails(self):
        self.write_generator("ignores_clock")
        result = self.check()
        self.assertFalse(result["passed"])
        self.assertEqual(result["files"][1]["status"], "different")

    def test_unexpected_generated_file_fails(self):
        self.write_generator("extra_file")
        result = self.check()
        self.assertFalse(result["passed"])
        self.assertEqual(result["extra_files"], ["outputs/tables/unexpected.csv"])

    def test_generator_error_fails(self):
        self.write_generator("raises")
        result = self.check()
        self.assertEqual(result["status"], "failed")
        self.assertIn("generator failure", " ".join(result["errors"]))

    def test_missing_dependency_is_not_a_pass(self):
        (self.scripts / "fake_tables.py").write_text("import canakkale_missing_module_for_tests\n", encoding="utf-8")
        result = self.check()
        self.assertEqual((result["passed"], result["status"]), (False, "dependency_unavailable"))
        with mock.patch.dict(os.environ, {"GDALINFO": ""}):
            result = reproduction.check_tables(dict(self.table_set, requires_env=("GDALINFO",)), self.root, self.scripts)
        self.assertEqual(result["status"], "dependency_unavailable")

    def test_builtin_sets_match_the_saved_manifests(self):
        for name, table_set in reproduction.TABLE_SETS.items():
            with self.subTest(name=name):
                saved = (reproduction.ROOT / "outputs/tables" / table_set["manifest"]).read_text(encoding="utf-8")
                listed = re.findall(r"^- `outputs/tables/([^`]+)`$", saved, flags=re.M)
                self.assertEqual(listed, table_set["files"])
                reproduction.recorded_stamp(reproduction.ROOT / "outputs/tables" / table_set["manifest"])

    def test_command_without_gis_tools_never_reports_success(self):
        saved = reproduction.ROOT / "outputs/tables/report_tables_manifest.md"
        self.record("report_tables_manifest.md", saved.read_bytes())
        environment = {key: value for key, value in os.environ.items() if key not in reproduction.GDAL_TOOLS}
        for extra in ([], ["--json"]):
            with self.subTest(json=bool(extra)):
                process = subprocess.run([sys.executable, "-B", str(SCRIPT), "--table-set", "report", "--project-root", str(self.root), *extra],
                                         capture_output=True, text=True, timeout=120, env=environment)
                self.assertEqual(process.returncode, 2, process.stdout + process.stderr)
                self.assertNotIn("GEÇTİ", process.stdout + process.stderr)
                if extra:
                    self.assertEqual(json.loads(process.stdout)["status"], "dependency_unavailable")


if __name__ == "__main__":
    unittest.main()
