#!/usr/bin/env python3
"""Baseline high-plus outline: polygons from a synthetic class raster, byte determinism and CLI modes."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import sys

sys.dont_write_bytecode = True
os.environ["GDAL_PAM_ENABLED"] = "NO"
from tier_support import module_tier

TIER = module_tier(__file__)
if TIER.available:
    import numpy as np
    from osgeo import gdal, osr
    gdal.UseExceptions()
    osr.UseExceptions()
import build_high_plus_boundary as hb

GEOTRANSFORM = (400000.0, 100.0, 0.0, 4500000.0, 0.0, -100.0)


def write_raster(path: Path, array, geotransform=GEOTRANSFORM) -> None:
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(32635)
    ds = gdal.GetDriverByName("GTiff").Create(str(path), array.shape[1], array.shape[0], 1, gdal.GDT_Byte)
    ds.SetGeoTransform(geotransform)
    ds.SetProjection(srs.ExportToWkt())
    ds.GetRasterBand(1).WriteArray(array)
    ds.FlushCache()
    ds = None


def synthetic_root(root: Path, geotransform=GEOTRANSFORM) -> None:
    """Two high-plus groups (4 + 2 cells), a diagonal-only cell and a class-5 cell outside the AOI."""
    classes = np.array([[4, 5, 1, 1, 1, 1],
                        [5, 4, 1, 1, 4, 1],
                        [1, 1, 3, 1, 4, 1],
                        [1, 1, 1, 5, 1, 5]], dtype=np.uint8)
    aoi = np.ones(classes.shape, dtype=np.uint8)
    aoi[3, 5] = 0
    (root / Path(hb.CLASS_RASTER).parent).mkdir(parents=True)
    write_raster(root / hb.CLASS_RASTER, classes, geotransform)
    write_raster(root / hb.TEMPLATE, aoi)


def run_cli(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = hb.main(list(args))
    return code, out.getvalue(), err.getvalue()


@TIER.skip_unless_available
class Build(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        synthetic_root(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_polygons_follow_four_connected_high_plus_cells_inside_the_aoi(self):
        data, summary = hb.build(self.root / hb.CLASS_RASTER, self.root / hb.TEMPLATE)
        layer = json.loads(data)
        self.assertEqual(summary, {"polygons": 3, "high_plus_cells": 7, "area_km2": 0.07, "connectivity": 4})
        self.assertEqual([f["properties"]["area_m2"] for f in layer["features"]], [40000, 20000, 10000])
        self.assertEqual([f["properties"]["id"] for f in layer["features"]], [1, 2, 3])
        self.assertEqual(layer["features"][0]["geometry"]["coordinates"][0][0], [400000, 4500000])
        self.assertEqual(layer["crs"]["properties"]["name"], "urn:ogc:def:crs:EPSG::32635")

    def test_bytes_are_identical_across_runs_and_whole_metre(self):
        first, _ = hb.build(self.root / hb.CLASS_RASTER, self.root / hb.TEMPLATE)
        second, _ = hb.build(self.root / hb.CLASS_RASTER, self.root / hb.TEMPLATE)
        self.assertEqual(first, second)
        self.assertTrue(first.endswith(b"}\n"))
        self.assertNotIn(b" ", first)
        for feature in json.loads(first)["features"]:
            for ring in feature["geometry"]["coordinates"]:
                self.assertTrue(all(isinstance(v, int) for point in ring for v in point))

    def test_grid_mismatch_is_refused(self):
        other = self.root / "other"
        synthetic_root(other, (400050.0, 100.0, 0.0, 4500000.0, 0.0, -100.0))
        with self.assertRaisesRegex(ValueError, "grids differ"):
            hb.build(other / hb.CLASS_RASTER, self.root / hb.TEMPLATE)


@TIER.skip_unless_available
class Modes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        synthetic_root(self.root)
        self.target = self.root / hb.OUTPUT

    def tearDown(self):
        self.tmp.cleanup()

    def test_generate_writes_a_new_file_and_check_finds_it_identical(self):
        code, out, _ = run_cli("--generate", "--project-root", str(self.root), "--output", str(self.target))
        self.assertEqual(code, 0)
        written = self.target.read_bytes()
        self.assertEqual(json.loads(out)["output_sha256"], hb.sha256(written))
        code, out, _ = run_cli("--project-root", str(self.root))
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["identical"])
        self.assertEqual(self.target.read_bytes(), written)

    def test_generate_refuses_an_existing_file(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b"keep")
        code, _, err = run_cli("--generate", "--project-root", str(self.root), "--output", str(self.target))
        self.assertEqual(code, 1)
        self.assertIn("output exists", err)
        self.assertEqual(self.target.read_bytes(), b"keep")

    def test_check_fails_on_changed_bytes_without_writing(self):
        run_cli("--generate", "--project-root", str(self.root), "--output", str(self.target))
        self.target.write_bytes(self.target.read_bytes().replace(b'"id":1', b'"id":9'))
        changed = self.target.read_bytes()
        code, out, _ = run_cli("--check", "--project-root", str(self.root))
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out)["identical"])
        self.assertEqual(self.target.read_bytes(), changed)

    def test_check_reports_a_missing_saved_layer(self):
        code, _, err = run_cli("--project-root", str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("saved layer cannot be read", err)
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()
