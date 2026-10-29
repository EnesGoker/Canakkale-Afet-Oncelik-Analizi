#!/usr/bin/env python3
"""Meaningful numerical, mask, corruption and non-overwrite contracts."""
from __future__ import annotations

import copy
import csv
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

sys.dont_write_bytecode = True
os.environ["GDAL_PAM_ENABLED"] = "NO"
import numpy as np
from osgeo import gdal, ogr, osr
import generate_scenario_agreement as sa


def districts():
    return [{"district_id": 1, "district_name": "Bir", "district_area_km2": .04}, {"district_id": 2, "district_name": "İki", "district_area_km2": .04}]


def fixture():
    membership = np.arange(8, dtype=np.uint8)
    classes = {name: np.where(membership & bit, 4, 3).astype(np.uint8) for name, bit in sa.BITS.items()}
    result = sa.compute_agreement(classes, np.repeat(np.array([1, 2], dtype=np.uint16), 4), districts())
    aoi = np.array([[True, True, False, True, True], [True, True, False, True, True]])
    projection = osr.SpatialReference()
    projection.ImportFromEPSG(32635)
    result.update(aoi=aoi, grid=(400000., 100., 0., 4500000., 0., -100.), projection=projection.ExportToWkt(), metadata={"baseline_id": "test-frozen-v1", "baseline_manifest_sha256": "1" * 64})
    return result


def score_fixture():
    return {"criteria": {"first": np.linspace(0, 1, 8, dtype=np.float32), "second": np.linspace(1, 0, 8, dtype=np.float32) ** 2},
        "scenarios": {name: [{"criterion_id": "first", "weight": .6}, {"criterion_id": "second", "weight": .4}] for name in sa.SCENARIOS},
        "baseline_class": np.array([5, 4, 3, 2, 1, 2, 3, 4], dtype=np.uint8)}


class NumericalContracts(unittest.TestCase):
    def test_all_eight_memberships_have_expected_identity(self):
        result = fixture()
        np.testing.assert_array_equal(result["membership"], np.arange(8))
        np.testing.assert_array_equal(result["agreement_count"], [0, 1, 1, 2, 1, 2, 2, 3])

    def test_gain_loss_and_jaccard(self):
        for row in fixture()["comparison_rows"][:3]:
            self.assertEqual(row["high_pixel_count"], 4)
            if row["scenario_id"] != "baseline":
                self.assertEqual((row["persistent_pixel_count"], row["added_pixel_count"], row["removed_pixel_count"], row["union_pixel_count"]), (2, 2, 2, 6))
                self.assertAlmostEqual(row["jaccard_percent"], 100 / 3)

    def test_each_table_partitions_districts_and_province(self):
        result = fixture()
        for key, grouping in (("count_rows", "agreement_count"), ("membership_rows", "membership_code")):
            rows = result[key]
            for province in (r for r in rows if r["scope"] == "province"):
                district = [r for r in rows if r["scope"] == "district" and r[grouping] == province[grouping]]
                self.assertEqual(sum(r["pixel_count"] for r in district), province["pixel_count"])
                self.assertAlmostEqual(sum(r["area_km2"] for r in district), province["area_km2"])
        self.assertEqual(len(result["count_rows"]), 12)
        self.assertEqual(len(result["membership_rows"]), 24)
        self.assertEqual(len(result["comparison_rows"]), 9)

    def test_high_uses_class_four_and_five(self):
        result = fixture()
        classes = {name: np.array([1, 2, 3, 4, 5, 1, 2, 3], dtype=np.uint8) for name in sa.SCENARIOS}
        out = sa.compute_agreement(classes, result["district_ids"], districts())
        np.testing.assert_array_equal(out["agreement_count"], [0, 0, 0, 3, 3, 0, 0, 0])

    def test_no_high_sets_have_undefined_ratios(self):
        result = fixture()
        out = sa.compute_agreement({n: np.ones(8, dtype=np.uint8) for n in sa.SCENARIOS}, result["district_ids"], districts())
        for row in out["comparison_rows"]:
            self.assertIsNone(row["jaccard_percent"])
            self.assertIsNone(row["baseline_high_retention_percent"])
            self.assertIsNone(row["scenario_high_overlap_baseline_percent"])
        self.assertEqual(out["count_rows"][0]["share_of_scope_aoi_percent"], 100)

    def test_rejects_class_nodata_before_threshold(self):
        for invalid in (0, 6, 255):
            data = fixture()
            data["classes"]["baseline"][0] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                sa.compute_agreement(data["classes"], data["district_ids"], districts())

    def test_rejects_shape_float_and_missing_scenario(self):
        for mode in ("shape", "float", "missing"):
            data = fixture()
            if mode == "shape": data["classes"]["baseline"] = data["classes"]["baseline"][:-1]
            if mode == "float": data["classes"]["baseline"] = data["classes"]["baseline"].astype(float)
            if mode == "missing": del data["classes"]["equal-weight"]
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                sa.compute_agreement(data["classes"], data["district_ids"], districts())

    def test_rejects_missing_unknown_or_misaligned_districts(self):
        data = fixture()
        for ids in (np.array([0] * 8), np.array([1] * 8), np.array([1, 2]), np.array([1.] * 8)):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                sa.compute_agreement(data["classes"], ids, districts())

    def test_rejects_district_identity_and_name_anomalies(self):
        data = fixture()
        for mode in ("duplicate_id", "same_name", "empty_name", "bad_area"):
            rows = districts()
            if mode == "duplicate_id": rows[1]["district_id"] = 1
            if mode == "same_name": rows[1]["district_name"] = rows[0]["district_name"]
            if mode == "empty_name": rows[1]["district_name"] = ""
            if mode == "bad_area": rows[1]["district_area_km2"] = float("nan")
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                sa.compute_agreement(data["classes"], data["district_ids"], rows)

    def test_rejects_invalid_pixel_area(self):
        data = fixture()
        for area in (0, -1, float("nan"), float("inf")):
            with self.subTest(area=area), self.assertRaises(ValueError):
                sa.compute_agreement(data["classes"], data["district_ids"], districts(), area)

    def test_canonical_baseline_classes_preserved(self):
        loaded = score_fixture()
        result, _ = sa.compute_scenario_classes(loaded)
        np.testing.assert_array_equal(result["baseline"], loaded["baseline_class"])
        self.assertFalse(np.array_equal(result["baseline"], result["earthquake-heavy"]))

    def test_alternative_arithmetic_and_thresholds_match_frozen_function(self):
        from generate_sensitivity_tables import weighted_score, classify_normalized
        loaded = score_fixture()
        classes, stats = sa.compute_scenario_classes(loaded)
        valid = np.ones(8, bool)
        for name in sa.SCENARIOS[1:]:
            _, normalized, expected_stats = weighted_score({"scenario_id": name, "criteria": loaded["scenarios"][name]}, loaded["criteria"], valid)
            np.testing.assert_array_equal(classes[name], classify_normalized(normalized, valid))
            self.assertEqual(stats[name], expected_stats)
        np.testing.assert_array_equal(classify_normalized(np.array([0, .1999, .2, .4, .6, .8, 1], dtype=np.float32), np.ones(7, bool)), [1, 1, 2, 3, 4, 5, 5])

    def test_rejects_nonfinite_out_of_range_or_wrong_dtype_scores(self):
        for value in (float("nan"), float("inf"), -0.1, 1.1, "float64"):
            loaded = score_fixture()
            if value == "float64": loaded["criteria"]["first"] = loaded["criteria"]["first"].astype(np.float64)
            else: loaded["criteria"]["first"][0] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                sa.compute_scenario_classes(loaded)

    def test_rejects_zero_alternative_range(self):
        loaded = score_fixture()
        loaded["scenarios"]["earthquake-heavy"] = [{"criterion_id": "first", "weight": 1.}, {"criterion_id": "second", "weight": 0.}]
        loaded["criteria"]["first"][:] = .5
        with self.assertRaises(RuntimeError):
            sa.compute_scenario_classes(loaded)

    def test_rejects_criterion_order_missing_or_nonunit_weights(self):
        for mode in ("order", "missing", "weight", "nan"):
            loaded = score_fixture()
            if mode == "order": loaded["scenarios"]["equal-weight"].reverse()
            if mode == "missing": del loaded["criteria"]["second"]
            if mode == "weight": loaded["scenarios"]["equal-weight"][0]["weight"] = .8
            if mode == "nan": loaded["scenarios"]["equal-weight"][0]["weight"] = float("nan")
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                sa.compute_scenario_classes(loaded)

    def test_rejects_bad_grid_aoi_or_missing_crs(self):
        data = fixture()
        for aoi, grid, crs in ((data["aoi"].astype(np.uint8), data["grid"], data["projection"]), (np.zeros((2, 2), bool), data["grid"], data["projection"]), (data["aoi"], (0, 100, 1, 0, 0, -100), data["projection"]), (data["aoi"], data["grid"], ""), (data["aoi"], (0, 100, 0, 0, 0, 100), data["projection"])):
            with self.subTest(grid=grid, crs=crs), self.assertRaises(ValueError):
                sa.validate_grid(aoi, grid, crs)

    def test_zero_is_valid_and_outside_is_nodata(self):
        data = fixture()
        arrays = sa.raster_arrays(data)
        self.assertEqual(arrays[sa.COUNT_FILE][0, 0], 0)
        self.assertTrue(np.all(arrays[sa.COUNT_FILE][~data["aoi"]] == 255))
        self.assertEqual(int((arrays[sa.COUNT_FILE] != 255).sum()), 8)

    def test_rejects_count_membership_mismatch(self):
        data = fixture()
        data["agreement_count"][0] = 1
        with self.assertRaises(ValueError):
            sa.raster_arrays(data)

    def test_district_cell_center_coverage_rejects_holes_overlaps_and_wrong_crs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / sa.DISTRICT_VECTOR
            path.parent.mkdir(parents=True)
            grid = (400000., 100., 0., 4500000., 0., -100.)
            target = osr.SpatialReference(); target.ImportFromEPSG(32635)
            for mode in ("valid", "hole", "overlap", "wrong_crs"):
                if path.exists(): path.unlink()
                source_crs = osr.SpatialReference(); source_crs.ImportFromEPSG(4326 if mode == "wrong_crs" else 32635)
                source = ogr.GetDriverByName("GPKG").CreateDataSource(str(path))
                layer = source.CreateLayer(sa.DISTRICT_LAYER, source_crs, ogr.wkbPolygon)
                layer.CreateField(ogr.FieldDefn("district_name", ogr.OFTString))
                for index in range(12):
                    x = 400000 + 100 * index
                    left = 400000 if mode == "overlap" and index == 11 else x
                    right = x + 100
                    if mode == "hole" and index == 0: left, right = 399000, 399100
                    geometry = ogr.CreateGeometryFromWkt(f"POLYGON (({left} 4499900, {right} 4499900, {right} 4500000, {left} 4500000, {left} 4499900))")
                    feature = ogr.Feature(layer.GetLayerDefn()); feature.SetField("district_name", f"İlçe {index + 1}"); feature.SetGeometry(geometry)
                    self.assertEqual(layer.CreateFeature(feature), 0)
                layer = None; source = None
                with self.subTest(mode=mode):
                    if mode == "valid":
                        ids, metadata = sa.load_district_assignment(root, np.ones((1, 12), bool), grid, target.ExportToWkt())
                        np.testing.assert_array_equal(ids, np.arange(1, 13))
                        self.assertEqual(len(metadata), 12)
                    else:
                        with self.assertRaises(ValueError):
                            sa.load_district_assignment(root, np.ones((1, 12), bool), grid, target.ExportToWkt())


class SavedArtifactContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "package"
        self.data = fixture()
        sa.write_outputs(self.data, self.output)

    def test_roundtrip_checks_all_files_and_all_cells(self):
        report = sa.compare_outputs(self.data, self.output)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["checked_files"], 6)
        self.assertEqual(report["checked_raster_cells"], self.data["aoi"].size * 2)
        self.assertEqual(report["checked_table_rows"], 45)
        ds = gdal.Open(str(self.output / sa.COUNT_FILE))
        self.assertEqual(ds.GetRasterBand(1).GetMaskBand().ReadAsArray()[0, 0], 255)
        self.assertEqual(ds.GetRasterBand(1).GetMaskBand().ReadAsArray()[0, 2], 0)

    def test_missing_any_artifact_fails_without_writes(self):
        for name in sa.OUTPUT_FILES:
            path = self.output / name
            content = path.read_bytes()
            path.unlink()
            with self.subTest(name=name):
                self.assertFalse(sa.compare_outputs(self.data, self.output)["passed"])
                self.assertFalse(path.exists())
            path.write_bytes(content)

    def test_saved_csv_count_change_fails(self):
        path = self.output / sa.COUNT_TABLE
        rows = list(csv.reader(io.StringIO(path.read_text())))
        rows[1][6] = "99"
        with path.open("w", newline="") as stream: csv.writer(stream).writerows(rows)
        self.assertFalse(sa.compare_outputs(self.data, self.output)["passed"])

    def test_saved_csv_column_order_change_fails(self):
        path = self.output / sa.MEMBERSHIP_TABLE
        rows = list(csv.reader(io.StringIO(path.read_text())))
        rows[0][0], rows[0][1] = rows[0][1], rows[0][0]
        with path.open("w", newline="") as stream: csv.writer(stream).writerows(rows)
        self.assertFalse(sa.compare_outputs(self.data, self.output)["passed"])

    def test_saved_csv_undefined_ratio_becoming_zero_fails(self):
        path = self.output / sa.COMPARISON_TABLE
        rows = list(csv.reader(io.StringIO(path.read_text())))
        affected = next(row for row in rows[1:] if row[-1] == "")
        affected[-1] = "0"
        with path.open("w", newline="") as stream: csv.writer(stream).writerows(rows)
        self.assertFalse(sa.compare_outputs(self.data, self.output)["passed"])

    def test_saved_raster_valid_zero_becoming_nodata_fails(self):
        ds = gdal.Open(str(self.output / sa.COUNT_FILE), gdal.GA_Update)
        array = ds.GetRasterBand(1).ReadAsArray()
        array[0, 0] = 255
        ds.GetRasterBand(1).WriteArray(array)
        ds = None
        self.assertFalse(sa.compare_outputs(self.data, self.output)["passed"])

    def test_saved_raster_outside_becoming_valid_zero_fails(self):
        ds = gdal.Open(str(self.output / sa.COUNT_FILE), gdal.GA_Update)
        array = ds.GetRasterBand(1).ReadAsArray()
        array[0, 2] = 0
        ds.GetRasterBand(1).WriteArray(array)
        ds = None
        self.assertFalse(sa.compare_outputs(self.data, self.output)["passed"])

    def test_saved_raster_shifted_grid_fails(self):
        ds = gdal.Open(str(self.output / sa.MEMBERSHIP_FILE), gdal.GA_Update)
        ds.SetGeoTransform((400001, 100, 0, 4500000, 0, -100))
        ds = None
        self.assertFalse(sa.compare_outputs(self.data, self.output)["passed"])

    def test_saved_raster_wrong_crs_and_nodata_fails(self):
        for kind in ("crs", "nodata"):
            path = self.output / sa.MEMBERSHIP_FILE
            original = path.read_bytes()
            ds = gdal.Open(str(path), gdal.GA_Update)
            if kind == "crs":
                projection = osr.SpatialReference(); projection.ImportFromEPSG(4326); ds.SetProjection(projection.ExportToWkt())
            else: ds.GetRasterBand(1).SetNoDataValue(0)
            ds = None
            with self.subTest(kind=kind): self.assertFalse(sa.compare_outputs(self.data, self.output)["passed"])
            path.write_bytes(original)

    def test_stale_baseline_and_hash_manifest_fail(self):
        path = self.output / sa.MANIFEST_FILE
        original = path.read_text()
        for kind in ("baseline", "checksum", "bit_identity", "software"):
            manifest = json.loads(original)
            if kind == "baseline": manifest["baseline"]["baseline_manifest_sha256"] = "stale"
            if kind == "checksum": manifest["outputs"][0]["sha256"] = "0" * 64
            if kind == "bit_identity": manifest["membership_bits"]["baseline"] = 4
            if kind == "software": manifest["software"]["numpy"] = ""
            path.write_text(json.dumps(manifest))
            with self.subTest(kind=kind): self.assertFalse(sa.compare_outputs(self.data, self.output)["passed"])
        path.write_text(original)

    def test_read_only_check_does_not_change_files(self):
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        self.assertTrue(sa.compare_outputs(self.data, self.output)["passed"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_nonempty_and_symbolic_output_never_overwritten(self):
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        with self.assertRaises(ValueError): sa.write_outputs(self.data, self.output)
        alias = Path(self.temp.name) / "alias"
        alias.symlink_to(self.output, target_is_directory=True)
        with self.assertRaises(ValueError): sa.write_outputs(self.data, alias)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_failed_publication_rolls_back_only_owned_files(self):
        target = Path(self.temp.name) / "failed"
        original_link = os.link
        calls = []
        def fail_second(source, destination):
            calls.append(destination)
            if len(calls) == 2: raise OSError("simulated disk publication failure")
            return original_link(source, destination)
        with patch.object(sa.os, "link", side_effect=fail_second), self.assertRaises(OSError):
            sa.write_outputs(self.data, target)
        self.assertFalse(target.exists())
        self.assertEqual({p.name for p in Path(self.temp.name).iterdir()}, {"package"})

    def test_reference_csv_changed_count_rejected(self):
        path = Path(self.temp.name) / "reference.csv"
        path.write_text("value,pixel_count\nBir,2\n", encoding="utf-8")
        self.assertEqual(sa._compare_rows(path, [{"value": "Bir", "pixel_count": 2}]), 1)
        with self.assertRaises(ValueError): sa._compare_rows(path, [{"value": "Bir", "pixel_count": 3}])

    def test_cli_dependency_unavailable_is_two_and_failed_inputs_one(self):
        for error, code in ((ImportError("numpy missing"), 2), (ValueError("frozen input changed"), 1)):
            with self.subTest(code=code), patch.object(sa, "analyze_project", side_effect=error), patch("sys.stdout", new_callable=io.StringIO) as output:
                self.assertEqual(sa.main(["--check", "--json"]), code)
                self.assertFalse(json.loads(output.getvalue())["passed"])

    def test_cli_missing_saved_package_fails_without_generation(self):
        target = Path(self.temp.name) / "absent"
        with patch.object(sa, "analyze_project", return_value={**self.data, "reference_validation": {"passed": True}}), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(sa.main(["--check", "--json", "--output-dir", str(target)]), 1)
            self.assertFalse(json.loads(output.getvalue())["passed"])
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
