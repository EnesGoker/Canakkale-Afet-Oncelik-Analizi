#!/usr/bin/env python3
"""Small temporary source/score fixtures for numerical transformation auditing."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np
from osgeo import gdal, ogr, osr

import check_criterion_transformations as checker


gdal.UseExceptions()


class TransformationTests(unittest.TestCase):
    def test_direct_invocation_does_not_write_import_cache(self):
        folder = self.root / "script-copy"
        folder.mkdir()
        for name in ("check_criterion_transformations.py", "check_mcda_integrity.py"):
            shutil.copyfile(Path(__file__).with_name(name), folder / name)
        env = os.environ.copy()
        env.pop("PYTHONDONTWRITEBYTECODE", None)
        process = subprocess.run([sys.executable, str(folder / "check_criterion_transformations.py"), "--help"],
                                 env=env, capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertFalse(list(folder.rglob("*.pyc")))

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="criterion-transformations-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.grid = (400000, 100, 0, 4500000, 0, -100)
        self.crs = osr.SpatialReference()
        self.crs.ImportFromEPSG(32635)
        self.aoi = np.ones((4, 5), dtype=bool)
        self.aoi[-1, -1] = False
        self.write("data/processed/analysis/analysis_template_100m_32635.tif", self.aoi.astype(np.uint8), nodata=0, dtype=gdal.GDT_Byte)
        column = np.tile(np.arange(5), (4, 1)).astype(np.float32)
        source_values = {"earthquake_pga_score": .3 + column * .1, "slope_score": column * 10, "flood_score": column * 3}
        for name, array in source_values.items():
            source, minimum, span = checker.AFFINE[name]
            self.write(source, array)
            self.score(name, np.clip((array.astype(float) - minimum) / span, 0, 1))
        # Each 100 m cell contains four 50 m values. These independently known
        # averages expose accidental nearest-neighbour/category-mode processing.
        classes = np.tile(np.array([[10, 20], [40, 80]], dtype=np.uint8), (4, 5))
        self.write(checker.LAND_SOURCE, classes, nodata=0, dtype=gdal.GDT_Byte, pixel=50)
        self.score("landcover_sensitivity_score", np.full(self.aoi.shape, .3625))
        trees = np.tile(np.array([[0, 100], [0, 100]], dtype=np.uint8), (4, 5))
        self.write(checker.TREE_SOURCE, trees, nodata=255, dtype=gdal.GDT_Byte, pixel=50)
        self.score("tree_cover_score", np.full(self.aoi.shape, .5))
        for name, (relative, _, _) in checker.DISTANCE_SOURCES.items():
            self.vector(relative, "LINESTRING (400050 4500100,400050 4499500)")
            expected = 1 - column * .1 if name.startswith("hydro") else column * .05
            self.score(name, expected)
        self.vector(checker.BUILDING_SOURCE, "POLYGON ((400000 4500000,400500 4500000,400500 4499600,400000 4499600,400000 4500000))", building=True)
        self.score("building_exposure_density_score", np.full(self.aoi.shape, .2))

    def write(self, relative, array, nodata=-9999, dtype=gdal.GDT_Float32, pixel=100, crs=None):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        d = gdal.GetDriverByName("GTiff").Create(str(path), array.shape[1], array.shape[0], 1, dtype)
        grid = list(self.grid)
        grid[1], grid[5] = pixel, -pixel
        d.SetGeoTransform(grid)
        d.SetProjection((crs or self.crs).ExportToWkt())
        d.GetRasterBand(1).SetNoDataValue(nodata)
        d.GetRasterBand(1).WriteArray(array)
        d = None

    def score(self, name, array):
        values = np.where(self.aoi, array, -9999).astype(np.float32)
        self.write(f"data/processed/analysis/{name}_32635.tif", values)

    def vector(self, relative, wkt, building=False):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        d = ogr.GetDriverByName("GPKG").CreateDataSource(str(path))
        name = "building_density_final_grid_100m_32635" if building else "lines"
        layer = d.CreateLayer(name, self.crs, ogr.wkbPolygon if building else ogr.wkbLineString)
        if building:
            for field in ["grid_area_m2", "building_area_m2", "building_density_score"]:
                layer.CreateField(ogr.FieldDefn(field, ogr.OFTReal))
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
        if building:
            for key, value in {"grid_area_m2": 200000, "building_area_m2": 40000, "building_density_score": .2}.items():
                feature.SetField(key, value)
        layer.CreateFeature(feature)
        d = None

    def edit(self, relative, value, row=0, col=0):
        d = gdal.Open(str(self.root / relative), gdal.GA_Update)
        a = d.ReadAsArray()
        a[row, col] = value
        d.GetRasterBand(1).WriteArray(a)
        d = None

    def check(self):
        result = checker.check_project(self.root, np, gdal, ogr, osr)
        json.dumps(result, allow_nan=False)
        return result

    def assert_failure(self, text):
        result = self.check()
        self.assertFalse(result["passed"], result)
        self.assertIn(text, json.dumps([item for item in result["checks"] if item["status"] == "failed"]))

    def test_all_eight_formulas_and_provenance_limit(self):
        result = self.check()
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["summary"]["verified_equivalent_formulas"], 8)
        self.assertEqual(result["summary"]["warning_count"], 1)
        self.assertEqual(result["summary"]["aoi_cells"], 19)

    def test_changed_source_is_not_refitted_to_score(self):
        self.edit(checker.AFFINE["slope_score"][0], 25)
        self.assert_failure("mismatch_aoi_cells")

    def test_single_changed_score_fails(self):
        self.edit("data/processed/analysis/tree_cover_score_32635.tif", .51)
        self.assert_failure("mismatch_aoi_cells")

    def test_unknown_landcover_class_fails_without_invented_score(self):
        self.edit(checker.LAND_SOURCE, 70)
        self.assert_failure("Unobserved land-cover classes")

    def test_landcover_lookup_precedes_averaging(self):
        result = self.check()
        item = next(item for item in result["checks"] if item["name"] == "equivalent_formula:landcover_sensitivity_score")
        self.assertEqual(item["status"], "passed")
        # Dominant class/averaged class-code lookup would not yield .3625.
        self.assertLess(item["details"]["maximum_absolute_difference_aoi"], 1e-6)

    def test_average_excludes_landcover_nodata(self):
        self.edit(checker.LAND_SOURCE, 0, row=1, col=1)
        self.edit("data/processed/analysis/landcover_sensitivity_score_32635.tif", ( .6 + .5 + .3 ) / 3)
        self.assertTrue(self.check()["passed"])

    def test_landcover_hole_inside_aoi_fails(self):
        for row in [0, 1]:
            for col in [0, 1]:
                self.edit(checker.LAND_SOURCE, 0, row, col)
        self.assert_failure("does not cover the AOI")

    def test_tree_missing_source_cell_is_explicit_zero(self):
        for row in [0, 1]:
            for col in [0, 1]:
                self.edit(checker.TREE_SOURCE, 255, row, col)
        self.edit("data/processed/analysis/tree_cover_score_32635.tif", 0)
        result = self.check()
        self.assertTrue(result["passed"], result)
        item = next(item for item in result["checks"] if item["name"] == "equivalent_formula:tree_cover_score")
        self.assertEqual(item["details"]["source_nodata_aoi_cells"], 1)

    def test_bilinear_interpolation_preserves_known_spatial_gradient(self):
        source_path = "data/gradient.tif"
        self.write(source_path, np.array([[0, 1], [2, 3]], dtype=np.float32), pixel=200)
        source = gdal.Open(str(self.root / source_path))
        template = {"grid": self.grid, "array": np.ones((4, 4), dtype=np.uint8)}
        actual = checker.warp_to_template(source, template, gdal, "bilinear")
        expected = np.array([[0, .25, .75, 1], [.5, .75, 1.25, 1.5],
                             [1.5, 1.75, 2.25, 2.5], [2, 2.25, 2.75, 3]])
        np.testing.assert_allclose(actual, expected, atol=1e-7, rtol=0)

    def test_nonfinite_source_fails(self):
        self.edit(checker.AFFINE["slope_score"][0], np.nan)
        self.assert_failure("Nonfinite or out-of-range source")

    def test_source_range_is_checked(self):
        self.edit(checker.TREE_SOURCE, 150)
        self.assert_failure("Nonfinite or out-of-range source")

    def test_source_crs_is_checked(self):
        path = self.root / checker.TREE_SOURCE
        d = gdal.Open(str(path), gdal.GA_Update)
        crs = osr.SpatialReference()
        crs.ImportFromEPSG(4326)
        d.SetProjection(crs.ExportToWkt())
        d = None
        self.assert_failure("Expected single-band EPSG:32635")

    def test_changed_building_ratio_is_detected(self):
        d = ogr.Open(str(self.root / checker.BUILDING_SOURCE), 1)
        layer = d.GetLayer(0)
        feature = layer.GetNextFeature()
        feature.SetField("building_area_m2", 50000)
        layer.SetFeature(feature)
        d = None
        self.assert_failure("Building area ratio")

    def test_infinite_building_area_fails_before_clipping_hides_it(self):
        d = ogr.Open(str(self.root / checker.BUILDING_SOURCE), 1)
        layer = d.GetLayer(0)
        feature = layer.GetNextFeature()
        feature.SetField("building_area_m2", float("inf"))
        feature.SetField("building_density_score", 1.0)
        layer.SetFeature(feature)
        d = None
        self.assert_failure("Building area ratio")

    def test_missing_source_fails(self):
        (self.root / checker.TREE_SOURCE).unlink()
        self.assert_failure("Required file missing")

    def test_wrong_score_grid_fails(self):
        path = self.root / "data/processed/analysis/tree_cover_score_32635.tif"
        d = gdal.Open(str(path), gdal.GA_Update)
        grid = list(self.grid)
        grid[0] += 1
        d.SetGeoTransform(grid)
        d = None
        self.assert_failure("Grid transform differs")

    def test_read_only_leaves_fixture_content_and_file_list_unchanged(self):
        def inventory():
            return {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob("*") if p.is_file()}
        before = inventory()
        self.assertTrue(self.check()["passed"])
        self.assertEqual(inventory(), before)

    def test_cli_exit_failure_and_json(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = checker.main(["--check", "--project-root", str(self.root / "absent"), "--json"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["status"], "failed")


if __name__ == "__main__":
    unittest.main()
