#!/usr/bin/env python3
"""Public-source scope of the frozen baseline check, using temporary standard-library fixtures."""

import copy
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
import analysis_baseline as baseline

SCRIPT = Path(__file__).with_name("analysis_baseline.py")


class PublicSourceScopeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="canakkale-baseline-scope-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        references = [f"outputs/tables/reference_{i}.csv" for i in range(8)]
        paths = set(baseline.FIXED_INPUTS + references)
        paths.update(baseline.ANALYSIS + name + "_32635.tif" for name in baseline.CRITERIA)
        for name in paths:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"synthetic frozen file {name}\n".encode())
        with (self.root / baseline.WEIGHTS).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream, delimiter="\t")
            writer.writerow(["scenario_id", "criterion_order", "criterion_id", "raster_path", "weight"])
            for scenario in baseline.SCENARIOS:
                for index, name in enumerate(baseline.CRITERIA, 1):
                    writer.writerow([scenario, index, name, baseline.ANALYSIS + name + "_32635.tif", 1 / 11])
        manifest = {"format_version": 1, "baseline_id": "synthetic-v1", "aoi_rule": "template_equals_1",
                    "expected_aoi_cells": 18, "class_thresholds": [0.2, 0.4, 0.6, 0.8],
                    "normalization": copy.deepcopy(baseline.NORMALIZATION), "reference_tables": references,
                    "scenarios": baseline.weight_scenarios(self.root),
                    "files": [{"path": name, "size": (self.root / name).stat().st_size,
                               "sha256": baseline.sha256_file(self.root / name)} for name in sorted(paths)]}
        (self.root / baseline.MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
        self.data = sorted(name for name in paths if name.startswith("data/processed/"))
        self.kept = sorted(paths - set(self.data))
        self.selection = {"format_version": 1, "files": [*self.kept, str(baseline.MANIFEST)]}
        self.save_selection()
        self.data_bytes = {name: (self.root / name).read_bytes() for name in self.data}
        for name in self.data:
            (self.root / name).unlink()

    def save_selection(self):
        (self.root / baseline.PUBLIC_SELECTION).write_text(json.dumps(self.selection), encoding="utf-8")

    def restore(self, names):
        for name in names:
            (self.root / name).write_bytes(self.data_bytes[name])

    def verify(self, scope="public-source"):
        return baseline.verify_baseline(self.root, scope=scope)

    def test_fixture_has_the_real_record_split(self):
        self.assertEqual((len(self.data), len(self.kept)), (16, 11))

    def test_source_only_copy_passes_and_lists_every_skipped_file(self):
        result = self.verify()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(sorted(result["skipped_files"]), self.data)
        self.assertEqual((result["verified_files"], result["checked_files"], result["missing_files"]), (11, 27, []))
        self.assertEqual(result["skip_reason"], baseline.SKIP_REASON)

    def test_any_present_canonical_data_fails_and_points_to_the_full_scope(self):
        for names in ([self.data[0]], self.data[:5], self.data):
            with self.subTest(present=len(names)):
                self.restore(names)
                result = self.verify()
                self.assertFalse(result["passed"])
                self.assertIn(baseline.FULL_CHECK, result["errors"][-1])
                self.assertEqual(len(result["skipped_files"]), 16 - len(names))
        self.assertTrue(self.verify("full")["passed"])

    def test_missing_or_changed_published_file_fails(self):
        name = "scripts/bash/mcda_pipeline_commands.sh"
        target = self.root / name
        original = target.read_bytes()
        target.unlink()
        self.assertIn(f"Missing frozen file: {name}", self.verify()["errors"])
        changed = self.root / "outputs/tables/reference_3.csv"
        target.write_bytes(original)
        data = changed.read_bytes()
        changed.write_bytes(data[:-2] + b"X\n")
        self.assertIn("Changed frozen file: outputs/tables/reference_3.csv", self.verify()["errors"])

    def test_skip_definitions_must_agree(self):
        cases = {"data record published": [*self.selection["files"], self.data[0]],
                 "kept record unpublished": [name for name in self.selection["files"] if name != baseline.WEIGHTS]}
        for label, files in cases.items():
            with self.subTest(label=label):
                self.selection["files"] = files
                self.save_selection()
                result = self.verify()
                self.assertFalse(result["passed"])
                self.assertIn("Public-source omissions differ", " ".join(result["errors"]))

    def test_missing_selection_config_fails(self):
        (self.root / baseline.PUBLIC_SELECTION).unlink()
        self.assertFalse(self.verify()["passed"])

    def test_full_scope_reports_missing_data_honestly(self):
        result = self.verify("full")
        self.assertFalse(result["passed"])
        self.assertEqual((result["verified_files"], sorted(result["missing_files"]), result["skipped_files"]), (11, self.data, []))

    def test_command_line_output_and_exit_codes(self):
        command = [sys.executable, "-B", str(SCRIPT), "--check", "--project-root", str(self.root)]
        process = subprocess.run([*command, "--scope", "public-source"], capture_output=True, text=True, timeout=60)
        self.assertEqual(process.returncode, 0, process.stdout)
        self.assertIn("PASSED; 27 files checked: 11 verified, 16 skipped", process.stdout)
        for name in self.data:
            self.assertIn(f"SKIPPED ({baseline.SKIP_REASON}): {name}\n", process.stdout)
        self.restore(self.data[:1])
        process = subprocess.run([*command, "--scope", "public-source"], capture_output=True, text=True, timeout=60)
        self.assertEqual(process.returncode, 1)
        self.assertIn(baseline.FULL_CHECK, process.stdout)
        process = subprocess.run([*command, "--scope", "partial"], capture_output=True, text=True, timeout=60)
        self.assertEqual(process.returncode, 2)


if __name__ == "__main__":
    unittest.main()
