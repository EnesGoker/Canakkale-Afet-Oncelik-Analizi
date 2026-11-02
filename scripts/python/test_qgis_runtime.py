#!/usr/bin/env python3
"""Functional tests using tiny temporary QGIS raster/vector projects.

Run with the same QGIS Python runtime as check_qgis_runtime.py. No project data
is copied or edited. Without PyQGIS every test is skipped with the reason named;
a tier runner that requires the qgis tier counts that skip as a failure.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile


sys.dont_write_bytecode = True
from tier_support import module_tier

TIER = module_tier(__file__)
SCRIPT = Path(__file__).with_name("check_qgis_runtime.py")
CHILD_ENVIRONMENT = {"QT_QPA_PLATFORM": "offscreen", "GDAL_PAM_ENABLED": "NO"}
# exitQgis() unregisters GDAL/OGR drivers for the whole process, so the
# synthetic project is built in a child process, never in the test process.
FIXTURE = r'''
import gc
from pathlib import Path
import sys

from osgeo import gdal, ogr, osr
from qgis.core import Qgis, QgsApplication, QgsProject, QgsRasterLayer, QgsVectorLayer

gdal.UseExceptions()
template, profile = Path(sys.argv[1]), Path(sys.argv[2])
raster_file = template / "tiny.tif"
raster = gdal.GetDriverByName("GTiff").Create(str(raster_file), 2, 2, 1, gdal.GDT_Byte)
raster.SetGeoTransform((26, 0.01, 0, 40, 0, -0.01))
crs = osr.SpatialReference()
crs.ImportFromEPSG(4326)
raster.SetProjection(crs.ExportToWkt())
raster.GetRasterBand(1).Fill(1)
raster = None
vector = ogr.GetDriverByName("GPKG").CreateDataSource(str(template / "tiny.gpkg"))
vector.CreateLayer("points", crs, ogr.wkbPoint)
vector = None
app = QgsApplication([], False, str(profile))
app.initQgis()
project = QgsProject()
project.setFilePathStorage(Qgis.FilePathType.Relative)
raster_layer = QgsRasterLayer(str(raster_file), "Tiny raster", "gdal")
vector_layer = QgsVectorLayer(str(template / "tiny.gpkg") + "|layername=points", "Tiny vector", "ogr")
assert raster_layer.isValid() and vector_layer.isValid(), "Synthetic providers failed to initialize"
project.addMapLayer(raster_layer)
project.addMapLayer(vector_layer)
assert project.write(str(template / "tiny.qgs")), "Synthetic project write failed"
project.clear()
del raster_layer, vector_layer, project
gc.collect()
app.exitQgis()
'''


def child_environment():
    return dict(os.environ, **CHILD_ENVIRONMENT)


def process_state():
    from osgeo import gdal, ogr
    return {"environment": {name: os.environ.get(name) for name in CHILD_ENVIRONMENT},
            "exceptions": (gdal.GetUseExceptions(), ogr.GetUseExceptions()),
            "drivers": (gdal.GetDriverByName("GTiff") is not None, ogr.GetDriverByName("GPKG") is not None),
            "qgis_core_imported": "qgis.core" in sys.modules}


@TIER.skip_unless_available
class QgisRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state_before_fixture = process_state()
        cls.workspace = tempfile.TemporaryDirectory(prefix="canakkale-qgis-tests-")
        cls.template = Path(cls.workspace.name) / "template"
        cls.template.mkdir()
        profile = Path(cls.workspace.name) / "profile"
        profile.mkdir()
        process = subprocess.run([sys.executable, "-B", "-c", FIXTURE, str(cls.template), str(profile)],
                                 capture_output=True, text=True, timeout=120, env=child_environment())
        if process.returncode != 0:
            cls.workspace.cleanup()
            raise RuntimeError("Synthetic QGIS fixture failed:\n" + process.stdout + process.stderr)
        cls.state_after_fixture = process_state()

    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()

    def test_fixture_setup_leaves_the_test_process_untouched(self):
        self.assertEqual(self.state_after_fixture, self.state_before_fixture)
        self.assertEqual(self.state_after_fixture["drivers"], (True, True))
        self.assertFalse(self.state_after_fixture["qgis_core_imported"])
        self.assertLessEqual({"tiny.gpkg", "tiny.qgs", "tiny.tif"}, {path.name for path in self.template.iterdir()})

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(dir=self.workspace.name, prefix="case-")
        self.root = Path(self.folder.name)
        shutil.copytree(self.template, self.root, dirs_exist_ok=True)
        self.project = self.root / "tiny.qgs"

    def tearDown(self):
        self.folder.cleanup()

    def check(self, expected_code, filename="tiny.qgs"):
        process = subprocess.run(
            [sys.executable, str(SCRIPT), "--check", "--project-root", str(self.root), "--project-file", filename, "--json"],
            capture_output=True, text=True, timeout=30, env=child_environment(),
        )
        self.assertEqual(process.returncode, expected_code, process.stdout + process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result["passed"], expected_code == 0)
        return result, process

    def alter_project(self, mutate):
        tree = ET.parse(self.project)
        mutate(tree.getroot())
        tree.write(self.project, encoding="utf-8", xml_declaration=True)

    def test_valid_local_raster_and_vector(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        result, _ = self.check(0)
        self.assertTrue(result["project_read"])
        self.assertEqual(result["local_layer_count"], 2)
        self.assertEqual(result["invalid_local_layer_count"], 0)
        self.assertEqual(result["network_access"], "disabled")
        self.assertFalse(result["render_performed"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()})

    def test_valid_compressed_project(self):
        with zipfile.ZipFile(self.root / "tiny.qgz", "w", zipfile.ZIP_DEFLATED) as archive:
            archive.write(self.project, "tiny.qgs")
        result, _ = self.check(0, "tiny.qgz")
        self.assertTrue(result["project_read"])

    def test_absolute_project_argument(self):
        self.check(0, str(self.project))

    def test_unavailable_pyqgis_is_exit_two_and_not_passed(self):
        env = child_environment()
        env["PYTHONPATH"] = str(self.root / "no-python-modules")
        process = subprocess.run(
            [sys.executable, "-S", str(SCRIPT), "--project-root", str(self.root), "--project-file", "tiny.qgs", "--json"],
            capture_output=True, text=True, timeout=30, env=env,
        )
        self.assertEqual(process.returncode, 2, process.stdout + process.stderr)
        result = json.loads(process.stdout)
        self.assertFalse(result["passed"])
        self.assertFalse(result["project_read"])
        self.assertEqual(result["status"], "dependency_unavailable")

    def test_missing_project(self):
        result, _ = self.check(1, "missing.qgz")
        self.assertFalse(result["project_read"])

    def test_malformed_project(self):
        self.project.write_text("<qgis><broken>", encoding="utf-8")
        result, _ = self.check(1)
        self.assertFalse(result["project_read"])

    def test_corrupt_project_zip(self):
        (self.root / "bad.qgz").write_bytes(b"not a zip")
        self.check(1, "bad.qgz")

    def test_empty_project(self):
        self.project.write_text("<qgis><projectlayers/></qgis>", encoding="utf-8")
        result, _ = self.check(1)
        self.assertFalse(result["project_read"])

    def test_missing_raster(self):
        (self.root / "tiny.tif").unlink()
        result, _ = self.check(1)
        self.assertTrue(result["project_read"])
        self.assertEqual(result["invalid_local_layer_count"], 1)

    def test_corrupt_raster(self):
        (self.root / "tiny.tif").write_bytes(b"corrupt raster input")
        result, _ = self.check(1)
        self.assertTrue(result["project_read"])
        self.assertEqual(result["invalid_local_layer_count"], 1)

    def test_missing_gpkg_table_even_when_file_exists(self):
        def mutate(root):
            for layer in root.findall("./projectlayers/maplayer"):
                if layer.findtext("provider") == "ogr":
                    layer.find("datasource").text = "./tiny.gpkg|layername=missing_table"
        self.alter_project(mutate)
        result, _ = self.check(1)
        self.assertTrue((self.root / "tiny.gpkg").is_file())
        self.assertTrue(result["project_read"])
        self.assertEqual(result["invalid_local_layer_count"], 1)

    def test_runtime_cannot_silently_drop_declared_layer(self):
        def mutate(root):
            for layer in root.findall("./projectlayers/maplayer"):
                if layer.findtext("provider") == "ogr":
                    layer.set("type", "unsupported_layer_type")
        self.alter_project(mutate)
        result, _ = self.check(1)
        self.assertIn("XML", " ".join(result["errors"]))

    def test_web_layer_is_skipped_without_url_in_output(self):
        def mutate(root):
            parent = root.find("projectlayers")
            layer = copy.deepcopy(next(layer for layer in parent if layer.findtext("provider") == "gdal"))
            layer.find("id").text = "web_layer_test"
            layer.find("layername").text = "Offline web fixture"
            layer.find("provider").text = "wms"
            layer.find("datasource").text = "type=xyz&url=https://tiles.example.invalid/{z}/{x}/{y}.png?token=private_test_token"
            parent.append(layer)
        self.alter_project(mutate)
        result, process = self.check(0)
        self.assertEqual(result["local_layer_count"], 2)
        self.assertEqual(len(result["web_layers"]), 1)
        self.assertEqual(result["web_layers"][0]["status"], "skipped_offline")
        self.assertNotIn("private_test_token", process.stdout + process.stderr)
        self.assertNotIn("tiles.example.invalid", process.stdout + process.stderr)

    def test_local_source_outside_root_fails(self):
        def mutate(root):
            for layer in root.findall("./projectlayers/maplayer"):
                if layer.findtext("provider") == "gdal":
                    layer.find("datasource").text = str(self.template / "tiny.tif")
        self.alter_project(mutate)
        result, _ = self.check(1)
        self.assertIn("proje kökünün dışında", " ".join(result["errors"]))

    def test_remote_gdal_source_rejected_before_provider_read(self):
        def mutate(root):
            for layer in root.findall("./projectlayers/maplayer"):
                if layer.findtext("provider") == "gdal":
                    layer.find("datasource").text = "/vsicurl/https://raster.example.invalid/data.tif?token=private_test_token"
        self.alter_project(mutate)
        result, process = self.check(1)
        self.assertFalse(result["project_read"])
        self.assertNotIn("private_test_token", process.stdout + process.stderr)

    def test_non_file_provider_uri_rejected_before_provider_read(self):
        def mutate(root):
            for layer in root.findall("./projectlayers/maplayer"):
                if layer.findtext("provider") == "gdal":
                    layer.find("datasource").text = "/vsis3/example/data.tif"
        self.alter_project(mutate)
        result, _ = self.check(1)
        self.assertFalse(result["project_read"])


if __name__ == "__main__":
    unittest.main()
