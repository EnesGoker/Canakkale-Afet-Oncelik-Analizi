#!/usr/bin/env python3
"""Negative MCDA regression checks using small independent temporary rasters.

Run with a Python interpreter that provides NumPy and GDAL. No project data is
read or changed; every fixture is removed with its temporary directory.
"""

from __future__ import annotations

import builtins
import contextlib
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np
from osgeo import gdal, osr

import check_mcda_integrity as checker


gdal.UseExceptions()
WEIGHTS = (.16, .12, .08, .14, .10, .10, .06, .08, .06, .04, .06)
RAW = "mcda_priority_score"
NORMALIZED = "mcda_priority_score_normalized"
CLASS = "mcda_priority_class"
TEMPLATE = "analysis_template_100m"


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="canakkale-mcda-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.analysis = self.root / "data/processed/analysis"
        self.analysis.mkdir(parents=True)
        (self.root / "config").mkdir()
        (self.root / "scripts/bash").mkdir(parents=True)
        self.aoi = np.array([[0, 1, 1, 1, 0], [1, 1, 0, 1, 1], [1, 1, 1, 1, 0], [0, 1, 0, 1, 1]], dtype=bool)
        self.grid = (400000, 100, 0, 4500000, 0, -100)
        crs = osr.SpatialReference()
        crs.ImportFromEPSG(32635)
        self.projection = crs.ExportToWkt()
        self.write(TEMPLATE, self.aoi.astype(np.uint8), nodata=0, dtype=gdal.GDT_Byte)
        self.rows = []
        products = []
        positions = np.arange(self.aoi.size).reshape(self.aoi.shape)
        # Every criterion varies across pixels and differs from its neighbours.
        # Levels span all five classes; differing perturbations expose changed
        # weights even when their total remains exactly one.
        for index, (criterion, weight) in enumerate(zip(checker.CRITERIA, WEIGHTS)):
            values = (.035 + .072 * (positions % 7) + .001 * (index + 1) * ((positions % 3) - 1)).astype(np.float32)
            values[~self.aoi] = -9999
            self.write(criterion, values)
            products.append(values * np.float32(weight))
            self.rows.append({"scenario_id": "baseline", "scenario_role": "canonical", "criterion_order": str(index + 1),
                              "criterion_id": criterion, "raster_path": f"data/processed/analysis/{criterion}_32635.tif", "weight": str(weight)})
        self.write_rows()
        (self.root / "scripts/bash/mcda_pipeline_commands.sh").write_text(
            'MCDA_MIN_RAW="0.029"\nMCDA_RANGE="0.473"\n'
            'minimum(maximum((A-${MCDA_MIN_RAW})/${MCDA_RANGE},0),1)\n'
            'where(A<0.2,1,where(A<0.4,2,where(A<0.6,3,where(A<0.8,4,5))))\n', encoding="utf-8")
        # Fixture arithmetic uses its own explicit formulas, not checker helpers
        # or an existing project result as an oracle.
        raw = products[0].copy()
        for product in products[1:]:
            raw = np.add(raw, product, dtype=np.float32)
        normalized = np.minimum(np.maximum((raw - np.float32(.029)) / np.float32(.473), 0), 1)
        classes = np.select([normalized < .2, normalized < .4, normalized < .6, normalized < .8], [1, 2, 3, 4], default=5).astype(np.uint8)
        raw[~self.aoi], normalized[~self.aoi], classes[~self.aoi] = -9999, -9999, 0
        self.write(RAW, raw)
        self.write(NORMALIZED, normalized)
        self.write(CLASS, classes, nodata=0, dtype=gdal.GDT_Byte)

    def path(self, name):
        return self.analysis / f"{name}_32635.tif"

    def write(self, name, values, nodata=-9999, dtype=gdal.GDT_Float32, grid=None, projection=None, bands=1):
        target = self.path(name)
        for suffix in ("", ".msk", ".aux.xml"):
            candidate = Path(str(target) + suffix)
            if candidate.exists():
                candidate.unlink()
        dataset = gdal.GetDriverByName("GTiff").Create(str(target), values.shape[1], values.shape[0], bands, dtype)
        dataset.SetGeoTransform(self.grid if grid is None else grid)
        dataset.SetProjection(self.projection if projection is None else projection)
        for index in range(1, bands + 1):
            band = dataset.GetRasterBand(index)
            if nodata is not None:
                band.SetNoDataValue(nodata)
            band.WriteArray(values)
        dataset = None

    def write_rows(self):
        with (self.root / "config/mcda_weights.tsv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, list(self.rows[0]), delimiter="\t")
            writer.writeheader()
            writer.writerows(self.rows)

    def edit_cell(self, name, value, inside=True):
        dataset = gdal.Open(str(self.path(name)), gdal.GA_Update)
        band = dataset.GetRasterBand(1)
        array = band.ReadAsArray()
        y, x = np.argwhere(self.aoi if inside else ~self.aoi)[0]
        array[y, x] = value
        band.WriteArray(array)
        dataset = None

    def check(self):
        return checker.check_project(self.root, np, gdal, osr)

    def assert_failed(self, text=None):
        report = self.check()
        self.assertEqual(report["status"], "failed", report)
        if text:
            failures = [item for item in report["checks"] if item["status"] == "failed"]
            self.assertIn(text, json.dumps(failures))
        json.dumps(report, allow_nan=False)
        return report

    def test_valid_fixture_has_all_classes_and_independent_aoi(self):
        report = self.check()
        self.assertEqual(report["status"], "passed", report)
        self.assertEqual(report["summary"]["aoi_cells"], int(self.aoi.sum()))
        self.assertEqual(report["summary"]["warning_count"], 0)
        values = gdal.Open(str(self.path(CLASS))).ReadAsArray()[self.aoi]
        self.assertEqual(set(values), {1, 2, 3, 4, 5})
        self.assertEqual(len([item for item in report["checks"] if item["name"].startswith("arithmetic:")]), 3)

    def test_missing_config(self):
        (self.root / "config/mcda_weights.tsv").unlink()
        self.assert_failed("Required file missing")

    def test_missing_input(self):
        self.path(checker.CRITERIA[0]).unlink()
        self.assert_failed("Required file missing")

    def test_missing_output_is_failure(self):
        self.path(NORMALIZED).unlink()
        self.assert_failed("Required file missing")

    def test_absolute_config_path(self):
        self.rows[0]["raster_path"] = str(self.path(checker.CRITERIA[0]))
        self.write_rows()
        self.assert_failed("must be relative")

    def test_parent_traversal_config_path(self):
        self.rows[0]["raster_path"] = "../outside.tif"
        self.write_rows()
        self.assert_failed("cannot traverse")

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            outside_file = Path(outside) / "outside.tif"
            outside_file.write_bytes(self.path(checker.CRITERIA[0]).read_bytes())
            self.path(checker.CRITERIA[0]).unlink()
            self.path(checker.CRITERIA[0]).symlink_to(outside_file)
            self.assert_failed("escapes project root")

    def test_duplicate_criterion_id(self):
        self.rows[1]["criterion_id"] = self.rows[0]["criterion_id"]
        self.write_rows()
        self.assert_failed("must be distinct")

    def test_duplicate_order(self):
        self.rows[1]["criterion_order"] = "1"
        self.write_rows()
        self.assert_failed("canonical WLC order")

    def test_wrong_baseline_role(self):
        self.rows[0]["scenario_role"] = "robustness"
        self.write_rows()
        self.assert_failed("canonical role")

    def test_nonfinite_weight(self):
        self.rows[0]["weight"] = "NaN"
        self.write_rows()
        self.assert_failed("must be finite")

    def test_infinite_weight(self):
        self.rows[0]["weight"] = "Inf"
        self.write_rows()
        self.assert_failed("must be finite")

    def test_negative_weight(self):
        self.rows[0]["weight"] = "-0.01"
        self.write_rows()
        self.assert_failed("must be finite")

    def test_weights_not_sum_one(self):
        self.rows[0]["weight"] = "0.15"
        self.write_rows()
        self.assert_failed("weights sum")

    def test_changed_weights_preserve_sum_but_stale_output_fails(self):
        self.rows[0]["weight"], self.rows[1]["weight"] = "0.14", "0.14"
        self.write_rows()
        self.assert_failed("arithmetic:mcda_priority_score")

    def test_changed_normalization_policy(self):
        path = self.root / "scripts/bash/mcda_pipeline_commands.sh"
        path.write_text(path.read_text().replace('"0.473"', '"0.474"'))
        self.assert_failed("constants have changed")

    def test_changed_class_threshold(self):
        path = self.root / "scripts/bash/mcda_pipeline_commands.sh"
        path.write_text(path.read_text().replace("A<0.4", "A<0.41"))
        self.assert_failed("thresholds need policy review")

    def test_crs_mismatch(self):
        crs = osr.SpatialReference()
        crs.ImportFromEPSG(32636)
        self.write(checker.CRITERIA[0], np.zeros(self.aoi.shape), projection=crs.ExportToWkt())
        self.assert_failed("Expected EPSG:32635")

    def test_shifted_grid(self):
        self.write(checker.CRITERIA[0], np.zeros(self.aoi.shape), grid=(400001, 100, 0, 4500000, 0, -100))
        self.assert_failed("transform differs")

    def test_wrong_resolution(self):
        self.write(checker.CRITERIA[0], np.zeros(self.aoi.shape), grid=(400000, 90, 0, 4500000, 0, -100))
        self.assert_failed("100 m grid")

    def test_wrong_shape(self):
        self.write(checker.CRITERIA[0], np.zeros((3, 5)))
        self.assert_failed("shape differs")

    def test_extra_band(self):
        self.write(checker.CRITERIA[0], np.zeros(self.aoi.shape), bands=2)
        self.assert_failed("one raster band")

    def test_wrong_score_type(self):
        self.write(checker.CRITERIA[0], np.zeros(self.aoi.shape), dtype=gdal.GDT_Float64)
        self.assert_failed("Expected Float32")

    def test_missing_nodata_metadata(self):
        self.write(checker.CRITERIA[0], np.zeros(self.aoi.shape), nodata=None)
        self.assert_failed("NoData metadata must be")

    def test_aoi_nodata(self):
        self.edit_cell(checker.CRITERIA[0], -9999)
        self.assert_failed("aoi_nodata_cells")

    def test_aoi_nan(self):
        self.edit_cell(checker.CRITERIA[0], np.nan)
        self.assert_failed("aoi_nonfinite_cells")

    def test_aoi_infinity(self):
        self.edit_cell(checker.CRITERIA[0], np.inf)
        self.assert_failed("aoi_nonfinite_cells")

    def test_aoi_out_of_range(self):
        self.edit_cell(checker.CRITERIA[0], 1.01)
        self.assert_failed("aoi_range_error_cells")

    def test_gdal_mask_hole_inside_aoi(self):
        dataset = gdal.Open(str(self.path(checker.CRITERIA[0])), gdal.GA_Update)
        band = dataset.GetRasterBand(1)
        band.CreateMaskBand(gdal.GMF_PER_DATASET)
        mask = np.where(self.aoi, 255, 0).astype(np.uint8)
        mask[tuple(np.argwhere(self.aoi)[0])] = 0
        band.GetMaskBand().WriteArray(mask)
        dataset = None
        self.assert_failed("aoi_mask_invalid_cells")

    def test_template_nonbinary_value(self):
        self.edit_cell(TEMPLATE, 2)
        self.assert_failed("binary 0/1 AOI")

    def test_template_gdal_mask_hole(self):
        dataset = gdal.Open(str(self.path(TEMPLATE)), gdal.GA_Update)
        band = dataset.GetRasterBand(1)
        band.CreateMaskBand(gdal.GMF_PER_DATASET)
        mask = np.where(self.aoi, 255, 0).astype(np.uint8)
        mask[tuple(np.argwhere(self.aoi)[0])] = 0
        band.GetMaskBand().WriteArray(mask)
        dataset = None
        self.assert_failed("matching GDAL mask")

    def test_other_input_spill_fails(self):
        self.edit_cell(checker.CRITERIA[0], .3, inside=False)
        self.assert_failed("outside_aoi_not_nodata")

    def test_known_landcover_spill_warns_explicitly(self):
        self.edit_cell("landcover_sensitivity_score", .3, inside=False)
        report = self.check()
        self.assertEqual(report["status"], "passed", report)
        warning = next(item for item in report["checks"] if item["status"] == "warning")
        self.assertEqual(warning["details"]["outside_non_nodata_cells"], 1)

    def test_known_landcover_invalid_spill_fails(self):
        self.edit_cell("landcover_sensitivity_score", np.nan, inside=False)
        self.assert_failed("outside_invalid_score_cells")

    def test_known_landcover_expansion_fails(self):
        self.edit_cell("landcover_sensitivity_score", .3, inside=False)
        with mock.patch.object(checker, "KNOWN_BOUNDARY_MAX_CELLS", 0):
            self.assert_failed("known_boundary_finding_expanded")

    def test_raw_single_cell_corruption(self):
        self.edit_cell(RAW, .4)
        self.assert_failed("arithmetic:mcda_priority_score")

    def test_score_difference_below_absolute_tolerance_passes(self):
        values = gdal.Open(str(self.path(RAW))).ReadAsArray()
        original = values[tuple(np.argwhere(self.aoi)[0])]
        self.edit_cell(RAW, original + np.float32(5e-7))
        self.assertEqual(self.check()["status"], "passed")

    def test_score_difference_above_absolute_tolerance_fails(self):
        values = gdal.Open(str(self.path(RAW))).ReadAsArray()
        original = values[tuple(np.argwhere(self.aoi)[0])]
        self.edit_cell(RAW, original + np.float32(2e-6))
        self.assert_failed("arithmetic:mcda_priority_score")

    def test_normalized_single_cell_corruption(self):
        self.edit_cell(NORMALIZED, .9)
        self.assert_failed("arithmetic:mcda_priority_score_normalized")

    def test_class_single_cell_corruption(self):
        self.edit_cell(CLASS, 5)
        self.assert_failed("arithmetic:mcda_priority_class")

    def test_output_nodata_hole_cannot_shrink_aoi(self):
        self.edit_cell(CLASS, 0)
        report = self.assert_failed("aoi_nodata_cells")
        self.assertEqual(report["summary"]["aoi_cells"], int(self.aoi.sum()))

    def test_output_outside_spill_fails(self):
        self.edit_cell(RAW, .4, inside=False)
        self.assert_failed("outside_aoi_not_nodata")

    def test_class_outside_spill_fails(self):
        self.edit_cell(CLASS, 1, inside=False)
        self.assert_failed("outside_aoi_not_nodata")

    def test_output_nan_fails_and_json_remains_valid(self):
        self.edit_cell(NORMALIZED, np.nan)
        self.assert_failed("aoi_nonfinite_cells")

    def test_cli_success_failure_and_default_check(self):
        command = [sys.executable, str(Path(checker.__file__)), "--project-root", str(self.root), "--json"]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout)["status"], "passed")
        self.path(RAW).unlink()
        result = subprocess.run(command + ["--check"], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout)["status"], "failed")

    def test_missing_dependencies_return_two_and_valid_json(self):
        original_import = builtins.__import__

        def unavailable(name, *args, **kwargs):
            if name == "numpy":
                raise ImportError("simulated missing NumPy")
            return original_import(name, *args, **kwargs)

        output = io.StringIO()
        with mock.patch("builtins.__import__", side_effect=unavailable), contextlib.redirect_stdout(output):
            code = checker.main(["--project-root", str(self.root), "--json"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "unavailable")

    def test_missing_proj_resources_return_two_and_valid_json(self):
        output = io.StringIO()
        with mock.patch.object(osr.SpatialReference, "ImportFromEPSG", side_effect=RuntimeError("simulated missing PROJ database")), contextlib.redirect_stdout(output):
            code = checker.main(["--project-root", str(self.root), "--json"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
