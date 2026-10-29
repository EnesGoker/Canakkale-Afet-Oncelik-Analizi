#!/usr/bin/env python3
"""Real GIS map render, semantic tampering and read-only provenance checks."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
os.environ["GDAL_PAM_ENABLED"] = "NO"

import numpy as np
from osgeo import gdal, ogr, osr
from PIL import Image
import plot_scenario_agreement as plotting

gdal.UseExceptions(); ogr.UseExceptions(); osr.UseExceptions()


def snapshot(directory):
    return {path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in directory.rglob("*") if path.is_file()}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_fixture(root):
    """Eight complete membership combinations plus one outside-AOI cell.

    The plotter checks CSV provenance, not their numerical schema; the
    numerical agreement engine owns that separate validation contract.
    """
    sources = root / plotting.SOURCE_DIR
    sources.mkdir(parents=True)
    crs = osr.SpatialReference(); crs.ImportFromEPSG(32635)
    grid = (500000.0, 100.0, 0.0, 4450000.0, 0.0, -100.0)
    aoi = np.ones((3, 3), dtype=np.uint8); aoi[-1, -1] = 0
    membership = np.arange(9, dtype=np.uint8).reshape(3, 3); membership[-1, -1] = 255
    count = np.array([[0, 1, 1], [2, 1, 2], [2, 3, 255]], dtype=np.uint8)
    for path, array, nodata in (
        (root / plotting.TEMPLATE, aoi, 0),
        (sources / plotting.COUNT_FILE, count, 255),
        (sources / plotting.MEMBERSHIP_FILE, membership, 255),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        dataset = gdal.GetDriverByName("GTiff").Create(str(path), 3, 3, 1, gdal.GDT_Byte)
        dataset.SetGeoTransform(grid); dataset.SetProjection(crs.ExportToWkt())
        dataset.GetRasterBand(1).SetNoDataValue(nodata)
        dataset.GetRasterBand(1).WriteArray(array)
        dataset = None
    vector_path = root / plotting.DISTRICTS
    vector_path.parent.mkdir(parents=True, exist_ok=True)
    vector = ogr.GetDriverByName("GPKG").CreateDataSource(str(vector_path))
    layer = vector.CreateLayer("canakkale_districts_32635", crs, ogr.wkbPolygon)
    layer.CreateField(ogr.FieldDefn("district_name", ogr.OFTString))
    feature = ogr.Feature(layer.GetLayerDefn()); feature.SetField("district_name", "Çan — örnek ilçe")
    feature.SetGeometry(ogr.CreateGeometryFromWkt(
        "POLYGON ((500000 4450000, 500300 4450000, 500300 4449700, "
        "500000 4449700, 500000 4450000))"))
    layer.CreateFeature(feature); feature = None; layer = None; vector = None
    for name in plotting.SOURCE_FILES[2:]:
        (sources / name).write_text("fixture,value\nsmall,1\n", encoding="utf-8")
    baseline_path = root / plotting.BASELINE_FILE
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(baseline_path, {
        "format_version": 1, "baseline_id": "tiny-scenario-map-v1", "expected_aoi_cells": 8,
        "files": [plotting.file_record(root / name, name.as_posix())
                  for name in (plotting.TEMPLATE, plotting.DISTRICTS)],
    })
    write_json(sources / plotting.ANALYSIS_MANIFEST, {
        "format_version": 1, "baseline": {"baseline_id": "tiny-scenario-map-v1",
            "baseline_manifest_sha256": plotting.file_record(baseline_path)["sha256"]},
        "outputs": [plotting.file_record(sources / name) for name in plotting.SOURCE_FILES],
    })
    return sources


class ScenarioMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # One actual A3 render serves all cases; no full project data or
        # persistent Matplotlib font cache is required.
        cls.temporary = tempfile.TemporaryDirectory(prefix="scenario-map-tests-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.shared = Path(cls.temporary.name)
        cls.shared_sources = create_fixture(cls.shared)
        cls.shared_figures = cls.shared / plotting.MAP_DIR
        cls.shared_figures.parent.mkdir(parents=True)
        cls.source_before = snapshot(cls.shared)
        previous_cache = os.environ.get("MPLCONFIGDIR")
        plotting.generate_map(plotting.read_sources(cls.shared_sources, cls.shared), cls.shared_figures)
        cls.cache_restored = os.environ.get("MPLCONFIGDIR") == previous_cache
        cls.source_after = {name: digest for name, digest in snapshot(cls.shared).items()
                            if not name.startswith(plotting.MAP_DIR.as_posix() + "/")}

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="scenario-map-case-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "fixture"
        shutil.copytree(self.shared, self.root)
        self.sources = self.root / plotting.SOURCE_DIR
        self.figures = self.root / plotting.MAP_DIR

    def rehash_outputs(self):
        path = self.sources / plotting.ANALYSIS_MANIFEST
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["outputs"] = [plotting.file_record(self.sources / name) for name in plotting.SOURCE_FILES]
        write_json(path, manifest)

    def rehash_references(self):
        path = self.root / plotting.BASELINE_FILE
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["files"] = [plotting.file_record(self.root / name, name.as_posix())
                             for name in (plotting.TEMPLATE, plotting.DISTRICTS)]
        write_json(path, manifest)
        analysis_path = self.sources / plotting.ANALYSIS_MANIFEST
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        analysis["baseline"]["baseline_manifest_sha256"] = plotting.file_record(path)["sha256"]
        write_json(analysis_path, analysis)

    def update_raster(self, name, mutate):
        dataset = gdal.Open(str(self.sources / name), gdal.GA_Update)
        mutate(dataset)
        dataset = None
        self.rehash_outputs()

    @staticmethod
    def set_cell(dataset, row, column, value):
        array = dataset.ReadAsArray(); array[row, column] = value
        dataset.GetRasterBand(1).WriteArray(array)

    def test_actual_a3_png_pdf_manifest_and_unicode_roundtrip(self):
        self.assertEqual(self.source_before, self.source_after)
        self.assertTrue(self.cache_restored)
        with Image.open(self.figures / plotting.PNG_FILE) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (4960, 3507))
            self.assertAlmostEqual(image.info["dpi"][0], 300, places=2)
            image.verify()
        pdf = (self.figures / plotting.PDF_FILE).read_bytes()
        self.assertTrue(pdf.startswith(b"%PDF-"))
        dimensions = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", pdf)
        self.assertIsNotNone(dimensions)
        self.assertAlmostEqual(float(dimensions.group(1)), 420 / 25.4 * 72, places=4)
        self.assertAlmostEqual(float(dimensions.group(2)), 297 / 25.4 * 72, places=4)
        sources = plotting.read_sources(self.sources, self.root)
        self.assertEqual(sources["counts"], [1, 3, 3, 1])
        self.assertEqual(sources["districts"][0]["name"], "Çan — örnek ilçe")
        self.assertTrue(plotting.check_saved_map(sources, self.figures)["passed"])
        saved = json.loads((self.figures / plotting.MAP_MANIFEST).read_text(encoding="utf-8"))
        self.assertEqual(saved["page"], "A3 landscape")
        self.assertEqual(saved["png_dpi"], 300)
        self.assertEqual(set(path.name for path in self.figures.iterdir()),
                         {plotting.PNG_FILE, plotting.PDF_FILE, plotting.MAP_MANIFEST})

    def test_unrehashed_raster_change_is_rejected(self):
        path = self.sources / plotting.COUNT_FILE
        path.write_bytes(path.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "Source checksum/size mismatch"):
            plotting.read_sources(self.sources, self.root)

    def test_rehashed_count_membership_bounds_and_disagreement_are_rejected(self):
        originals = {name: (self.sources / name).read_bytes()
                     for name in (plotting.COUNT_FILE, plotting.MEMBERSHIP_FILE)}
        for name, row, column, value in (
            (plotting.COUNT_FILE, 0, 0, 4),
            (plotting.MEMBERSHIP_FILE, 0, 0, 8),
            (plotting.COUNT_FILE, 0, 0, 1),
            (plotting.MEMBERSHIP_FILE, 0, 0, 7),
        ):
            with self.subTest(name=name, value=value):
                for filename, content in originals.items(): (self.sources / filename).write_bytes(content)
                self.update_raster(name, lambda ds: self.set_cell(ds, row, column, value))
                with self.assertRaisesRegex(ValueError, "class values|differs from scenario membership"):
                    plotting.read_sources(self.sources, self.root)

    def test_rehashed_wrong_nodata_or_valid_mask_is_rejected(self):
        path = self.sources / plotting.COUNT_FILE; original = path.read_bytes()
        mutations = {
            "nodata": lambda ds: ds.GetRasterBand(1).SetNoDataValue(254),
            "inside_missing": lambda ds: self.set_cell(ds, 0, 0, 255),
            "outside_valid": lambda ds: self.set_cell(ds, 2, 2, 0),
        }
        for name, mutation in mutations.items():
            with self.subTest(case=name):
                path.write_bytes(original)
                self.update_raster(plotting.COUNT_FILE, mutation)
                with self.assertRaisesRegex(ValueError, "NoData 255|mask differs|outside NoData"):
                    plotting.read_sources(self.sources, self.root)

    def test_rehashed_raster_grid_or_crs_is_rejected(self):
        path = self.sources / plotting.COUNT_FILE; original = path.read_bytes()
        wrong_crs = osr.SpatialReference(); wrong_crs.ImportFromEPSG(32634)
        mutations = {
            "grid": lambda ds: ds.SetGeoTransform((500001, 100, 0, 4450000, 0, -100)),
            "crs": lambda ds: ds.SetProjection(wrong_crs.ExportToWkt()),
        }
        for name, mutation in mutations.items():
            with self.subTest(case=name):
                path.write_bytes(original)
                self.update_raster(plotting.COUNT_FILE, mutation)
                with self.assertRaisesRegex(ValueError, "grid/CRS differs"):
                    plotting.read_sources(self.sources, self.root)

    def test_missing_frozen_reference_or_rehashed_empty_district_name_is_rejected(self):
        path = self.root / plotting.DISTRICTS; original = path.read_bytes()
        path.unlink()
        with self.assertRaises(OSError): plotting.read_sources(self.sources, self.root)
        path.write_bytes(original)
        vector = ogr.Open(str(path), 1); layer = vector.GetLayerByName("canakkale_districts_32635")
        feature = layer.GetNextFeature(); feature.SetField("district_name", "")
        layer.SetFeature(feature); feature = None; layer = None; vector = None
        self.rehash_references()
        with self.assertRaisesRegex(ValueError, "geometry/name is missing"):
            plotting.read_sources(self.sources, self.root)

    def test_saved_png_or_pdf_tampering_is_rejected(self):
        sources = plotting.read_sources(self.sources, self.root)
        for name in (plotting.PNG_FILE, plotting.PDF_FILE):
            path = self.figures / name; original = path.read_bytes()
            with self.subTest(name=name):
                try:
                    path.write_bytes(original + b"changed")
                    with self.assertRaisesRegex(ValueError, re.escape(name)):
                        plotting.check_saved_map(sources, self.figures)
                finally: path.write_bytes(original)

    def test_changed_source_or_baseline_invalidates_saved_map(self):
        baseline_path = self.root / plotting.BASELINE_FILE
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        baseline["note"] = "A valid baseline metadata change still invalidates the saved provenance"
        write_json(baseline_path, baseline)
        with self.assertRaisesRegex(ValueError, "baseline manifest checksum"):
            plotting.read_sources(self.sources, self.root)
        self.rehash_references()
        with self.assertRaisesRegex(ValueError, "contract differs: sources"):
            plotting.check_saved_map(plotting.read_sources(self.sources, self.root), self.figures)
        baseline["baseline_id"] = "different-baseline-v2"
        write_json(baseline_path, baseline)
        with self.assertRaisesRegex(ValueError, "baseline identity differ"):
            plotting.read_sources(self.sources, self.root)

    def test_nonempty_or_symlink_output_is_never_overwritten(self):
        sources = plotting.read_sources(self.sources, self.root)
        before = snapshot(self.root)
        with self.assertRaisesRegex(ValueError, "never overwritten"):
            plotting.generate_map(sources, self.figures)
        self.assertEqual(snapshot(self.root), before)
        target = self.root / "empty-directory"; target.mkdir()
        link = self.root / "symlink-output"; link.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "never overwritten"):
            plotting.generate_map(sources, link)
        self.assertEqual(list(target.iterdir()), [])

    def test_check_cli_uses_no_matplotlib_and_writes_no_cache_or_project_file(self):
        before = snapshot(self.root)
        bootstrap = """
import importlib.abc
import sys
class BlockMatplotlib(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'matplotlib' or fullname.startswith('matplotlib.'):
            raise AssertionError('--check imported Matplotlib')
sys.meta_path.insert(0, BlockMatplotlib())
sys.path.insert(0, sys.argv[1])
import plot_scenario_agreement as plotting
sys.argv = ['plot_scenario_agreement.py', '--check', '--project-root', sys.argv[2], '--json']
result = plotting.main()
assert not any(name == 'matplotlib' or name.startswith('matplotlib.') for name in sys.modules)
raise SystemExit(result)
"""
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["MPLCONFIGDIR"] = str(self.root / "must-not-create-font-cache")
        completed = subprocess.run(
            [sys.executable, "-c", bootstrap, str(Path(plotting.__file__).parent), str(self.root)],
            capture_output=True, text=True, cwd=self.root, env=environment, timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["passed"])
        self.assertFalse(Path(environment["MPLCONFIGDIR"]).exists())
        self.assertEqual(snapshot(self.root), before)


if __name__ == "__main__":
    unittest.main()
