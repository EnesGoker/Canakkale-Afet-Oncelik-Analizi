#!/usr/bin/env python3
"""Run canonical QA using an isolated GDAL/NumPy profile and native macOS QGIS.

The runtimes are supplied explicitly; this entry point installs nothing.
Temporary shims support paths containing spaces and isolate PROJ/GDAL data.
All calculation checks and tolerances remain in run_canonical_qa.sh.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def prepare_environment(prefix: Path, overlay: Path, qgis_app: Path, temporary: Path,
                        parent: dict | None = None) -> dict:
    prefix, overlay, qgis_app = prefix.resolve(), overlay.resolve(), qgis_app.resolve()
    python = prefix / "bin/python"
    contents = qgis_app / "Contents"
    resources = contents / "Resources/qgis"
    required = [python, prefix / "bin/gdalinfo", prefix / "share/gdal",
                prefix / "share/proj/proj.db", overlay / "numpy/__init__.py",
                contents / "MacOS/python", resources / "python", resources / "gdal",
                resources / "proj/proj.db"]
    if not all(p.exists() for p in required):
        raise ValueError("GIS ortamı, NumPy overlay veya QGIS paketi eksik; kurulum profilini kontrol edin.")
    env = dict(os.environ if parent is None else parent)
    for key in ("PYTHONHOME", "PYTHONPATH", "PROJ_LIB", "QGIS_BIN",
                "DYLD_LIBRARY_PATH", "DYLD_FALLBACK_LIBRARY_PATH", "GDALINFO",
                "GDAL_TRANSLATE", "GDAL_RASTERIZE", "GDALWARP", "GDALDEM",
                "GDALSRSINFO", "GDAL_BUILDVRT", "OGRINFO", "OGR2OGR"):
        env.pop(key, None)
    env.update(PATH=str(prefix / "bin") + os.pathsep + env.get("PATH", ""),
               PYTHONPATH=str(overlay), PYTHON_BIN=str(python), GDAL_PYTHON_BIN=str(python),
               GDAL_BIN=str(prefix / "bin"), PROJ_DATA=str(prefix / "share/proj"),
               GDAL_DATA=str(prefix / "share/gdal"), GDAL_PAM_ENABLED="NO",
               PYTHONDONTWRITEBYTECODE="1", QT_QPA_PLATFORM="offscreen")

    def shim(name: str, body: str) -> str:
        path = temporary / name
        path.write_text("#!/bin/sh\nset -eu\n" + body + "\n", encoding="utf-8")
        path.chmod(0o700)
        return str(path)

    for variable, module in (("GDAL_CALC", "gdal_calc"), ("GDAL_PROXIMITY", "gdal_proximity")):
        env[variable] = shim(module, "exec " + shlex.quote(str(python))
                             + " -m osgeo_utils." + module + ' "$@"')
    qgis_body = "unset PROJ_LIB DYLD_LIBRARY_PATH DYLD_FALLBACK_LIBRARY_PATH\n"
    for key, value in {"PROJ_DATA": resources / "proj", "GDAL_DATA": resources / "gdal",
                       "PYTHONPATH": resources / "python"}.items():
        qgis_body += "export " + key + "=" + shlex.quote(str(value)) + "\n"
    qgis_body += "exec " + shlex.quote(str(contents / "MacOS/python")) + ' "$@"'
    env["QGIS_PYTHON_BIN"] = shim("qgis-python", qgis_body)
    return env


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gdal-prefix", type=Path, required=True)
    parser.add_argument("--numpy-overlay", type=Path, required=True)
    parser.add_argument("--qgis-app", type=Path, default=Path("/Applications/QGIS.app"))
    parser.add_argument("--project-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        root = args.project_root.expanduser().resolve()
        entry = root / "scripts/bash/run_canonical_qa.sh"
        if not entry.is_file():
            raise ValueError("Proje QA giriş dosyası bulunamadı.")
        with tempfile.TemporaryDirectory(prefix="canakkale-qa-runtime-") as folder:
            env = prepare_environment(args.gdal_prefix.expanduser(), args.numpy_overlay.expanduser(),
                                      args.qgis_app.expanduser(), Path(folder))
            return subprocess.run(["bash", str(entry), "--check"], cwd=root, env=env).returncode
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
