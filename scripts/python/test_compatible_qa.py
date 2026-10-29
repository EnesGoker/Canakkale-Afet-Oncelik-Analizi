"""Runtime isolation, safe quoting, and canonical exit propagation."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import run_compatible_qa as runner


class CompatibleQaTests(unittest.TestCase):
    def fixture(self, folder):
        base = Path(folder)
        prefix = base / "GIS space ' dollar$"
        overlay = base / "numpy overlay"
        app = base / "QGIS app"
        for name in ["bin/python", "bin/gdalinfo", "share/gdal/.keep", "share/proj/proj.db"]:
            p = prefix / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("")
        for root, name in [(overlay, "numpy/__init__.py"),
                           (app, "Contents/MacOS/python"),
                           (app, "Contents/Resources/qgis/python/.keep"),
                           (app, "Contents/Resources/qgis/gdal/.keep"),
                           (app, "Contents/Resources/qgis/proj/proj.db")]:
            p = root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("")
        return prefix, overlay, app

    def test_foreign_gis_environment_is_not_inherited(self):
        with tempfile.TemporaryDirectory() as folder:
            prefix, overlay, app = self.fixture(folder)
            env = runner.prepare_environment(prefix, overlay, app, Path(folder),
                    {"PATH": "/usr/bin", "PYTHONHOME": "/foreign", "QGIS_BIN": "/foreign",
                     "PROJ_LIB": "/foreign", "DYLD_LIBRARY_PATH": "/foreign",
                     "GDALINFO": "/foreign/gdalinfo", "GDAL_TRANSLATE": "/foreign/gdal_translate",
                     "GDAL_RASTERIZE": "/foreign/gdal_rasterize", "OGRINFO": "/foreign/ogrinfo",
                     "OGR2OGR": "/foreign/ogr2ogr"})
            self.assertEqual(env["PYTHONPATH"], str(overlay.resolve()))
            self.assertEqual(env["PROJ_DATA"], str(prefix.resolve() / "share/proj"))
            for key in ["PYTHONHOME", "QGIS_BIN", "PROJ_LIB", "DYLD_LIBRARY_PATH", "GDALINFO",
                        "GDAL_TRANSLATE", "GDAL_RASTERIZE", "OGRINFO", "OGR2OGR"]:
                self.assertNotIn(key, env)

    def test_shell_shim_preserves_space_quote_and_argument_boundaries(self):
        with tempfile.TemporaryDirectory() as folder:
            prefix, overlay, app = self.fixture(folder)
            # A harmless stand-in reports the exact argument vector of the shim.
            python = prefix / "bin/python"
            python.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
            python.chmod(0o700)
            env = runner.prepare_environment(prefix, overlay, app, Path(folder), {"PATH": "/usr/bin:/bin"})
            result = subprocess.run([env["GDAL_CALC"], "one argument", "literal$()"],
                                    env=env, text=True, capture_output=True, check=True)
            self.assertEqual(result.stdout.splitlines(), ["-m", "osgeo_utils.gdal_calc", "one argument", "literal$()"])

    def test_missing_runtime_is_rejected_before_qa(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                runner.prepare_environment(Path(folder), Path(folder), Path(folder), Path(folder), {})

    def test_canonical_failure_exit_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            prefix, overlay, app = self.fixture(folder)
            project = Path(folder) / "project"
            entry = project / "scripts/bash/run_canonical_qa.sh"
            entry.parent.mkdir(parents=True)
            entry.write_text("exit 1\n")
            with patch.object(runner.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)) as execute:
                result = runner.main(["--gdal-prefix", str(prefix), "--numpy-overlay", str(overlay),
                                      "--qgis-app", str(app), "--project-root", str(project)])
            self.assertEqual(result, 1)
            self.assertEqual(execute.call_args.args[0][-1], "--check")


if __name__ == "__main__":
    unittest.main()
