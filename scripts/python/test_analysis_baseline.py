#!/usr/bin/env python3
"""Test frozen-input rejection and AOI-only selection using temporary fixtures."""

import copy
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
import numpy as np
import analysis_baseline as baseline


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="canakkale-baseline-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.references = [f"outputs/tables/reference_{i}.csv" for i in range(8)]
        paths = set(baseline.FIXED_INPUTS + self.references)
        paths.update(baseline.ANALYSIS + name + "_32635.tif" for name in baseline.CRITERIA)
        for name in paths:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"synthetic frozen file\n")
        with (self.root / baseline.WEIGHTS).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream, delimiter="\t")
            writer.writerow(["scenario_id", "criterion_order", "criterion_id", "raster_path", "weight"])
            for scenario in baseline.SCENARIOS:
                for index, name in enumerate(baseline.CRITERIA, 1):
                    writer.writerow([scenario, index, name, baseline.ANALYSIS + name + "_32635.tif", 1 / 11])
        self.manifest = {"format_version": 1, "baseline_id": "synthetic-v1", "aoi_rule": "template_equals_1",
                         "expected_aoi_cells": 18, "class_thresholds": [0.2, 0.4, 0.6, 0.8],
                         "normalization": copy.deepcopy(baseline.NORMALIZATION), "reference_tables": self.references,
                         "scenarios": baseline.weight_scenarios(self.root),
                         "files": [{"path": name, "size": (self.root / name).stat().st_size,
                                    "sha256": baseline.sha256_file(self.root / name)} for name in sorted(paths)]}
        self.save()

    def save(self):
        (self.root / baseline.MANIFEST).write_text(json.dumps(self.manifest), encoding="utf-8")

    def test_unchanged_snapshot_passes_without_writes(self):
        before = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertTrue(baseline.verify_baseline(self.root)["passed"])
        self.assertEqual(before, {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_changed_file_rejected_even_when_size_matches(self):
        (self.root / baseline.TEMPLATE).write_bytes(b"SYNTHETIC FROZEN FILE\n")
        self.assertFalse(baseline.verify_baseline(self.root)["passed"])

    def test_missing_file_rejected(self):
        (self.root / baseline.OUTPUTS[0]).unlink()
        self.assertFalse(baseline.verify_baseline(self.root)["passed"])

    def test_parent_and_absolute_paths_rejected(self):
        for name in ("../outside", str(self.root / "absolute"), "C:\\outside.tif"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                baseline.local_path(self.root, name)

    def test_duplicate_file_record_rejected(self):
        self.manifest["files"].append(self.manifest["files"][0]); self.save()
        self.assertFalse(baseline.verify_baseline(self.root)["passed"])

    def test_uncovered_criterion_rejected(self):
        name = self.manifest["scenarios"]["baseline"][0]["raster_path"]
        self.manifest["files"] = [row for row in self.manifest["files"] if row["path"] != name]; self.save()
        self.assertFalse(baseline.verify_baseline(self.root)["passed"])

    def test_changed_manifest_weight_rejected(self):
        self.manifest["scenarios"]["baseline"][0]["weight"] = 0.9; self.save()
        self.assertFalse(baseline.verify_baseline(self.root)["passed"])

    def test_changed_mask_or_normalization_policy_rejected(self):
        for key, value in (("aoi_rule", "from_classes"), ("normalization", {}), ("class_thresholds", [0.1]), ("expected_aoi_cells", 0)):
            with self.subTest(key=key):
                saved = copy.deepcopy(self.manifest[key]); self.manifest[key] = value; self.save()
                self.assertFalse(baseline.verify_baseline(self.root)["passed"])
                self.manifest[key] = saved

    def test_aoi_selection_excludes_valid_spill_and_does_not_alias_input(self):
        data = np.array([[0.05, 0.3], [np.nan, 0.6]], dtype=np.float32)
        original = data.copy(); mask = np.array([[False, True], [False, True]])
        selected = baseline.select_aoi_values(data, mask)
        np.testing.assert_array_equal(selected, np.array([0.3, 0.6], dtype=np.float32))
        selected[0] = 1
        np.testing.assert_array_equal(data, original)

    def test_invalid_shape_or_nonboolean_mask_rejected(self):
        for mask in (np.ones((3, 2), dtype=bool), np.ones((2, 2), dtype=np.uint8)):
            with self.subTest(dtype=str(mask.dtype)), self.assertRaises(ValueError):
                baseline.select_aoi_values(np.ones((2, 2)), mask)


if __name__ == "__main__":
    unittest.main()
