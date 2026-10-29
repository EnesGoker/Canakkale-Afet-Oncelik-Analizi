#!/usr/bin/env python3
"""Open QGIS with private CARTO request authentication, without editing a project.

Only the GUI process receives the key-file path. The key is added to approved
HTTPS tile requests in memory, never to layer URLs, saved projects or logs.
--check validates local prerequisites without launching QGIS or using the web.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

sys.dont_write_bytecode = True
HOSTS = frozenset({"basemaps.cartocdn.com", "a.basemaps.cartocdn.com",
                   "b.basemaps.cartocdn.com", "c.basemaps.cartocdn.com"})
TILE_PATH = re.compile(r"/light_all/[0-9]{1,2}/[0-9]+/[0-9]+(?:@2x)?\.png\Z")
ROOT = Path(__file__).resolve().parents[2]
_HOOK_STATE = None


def validate_key(key: str) -> str:
    if (not isinstance(key, str) or not key or len(key) > 4096
            or any(ord(c) < 33 or ord(c) > 126 for c in key)):
        raise ValueError("CARTO anahtarı boş veya geçersiz.")
    return key


def read_key(key_file: str | Path | None, environ: dict | None = None) -> str:
    env = os.environ if environ is None else environ
    filename = key_file or env.get("CARTO_BASEMAPS_KEY_FILE")
    if filename:
        try:
            with Path(filename).expanduser().open(encoding="utf-8") as handle:
                key = handle.read(4098).strip()
        except (OSError, UnicodeError):
            raise ValueError("Özel CARTO anahtar dosyası okunamıyor.") from None
        return validate_key(key)
    return validate_key(env.get("CARTO_BASEMAPS_API_KEY", ""))


def authenticated_url(url: str, key: str) -> str:
    """Leave every URL outside the exact approved tile scope untouched."""
    try:
        parts = urlsplit(url)
        allowed = (parts.scheme == "https" and parts.hostname in HOSTS
                   and parts.port in (None, 443) and not parts.username
                   and not parts.password and not parts.fragment
                   and TILE_PATH.fullmatch(parts.path))
    except (TypeError, ValueError):
        return url
    if not allowed:
        return url
    validate_key(key)
    query = [(name, value) for name, value in parse_qsl(parts.query, keep_blank_values=True)
             if name.lower() not in {"key", "api_key"}]
    query.append(("key", key))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def install_request_auth(key: str, project_path: str | None = None) -> dict:
    """Install QGIS's request hook; providers and project XML stay unchanged."""
    global _HOOK_STATE
    validate_key(key)
    from qgis.core import QgsNetworkAccessManager, QgsProject
    from qgis.PyQt.QtCore import QUrl

    manager = QgsNetworkAccessManager.instance()
    previous = getattr(manager, "_canakkale_carto_hook", None)
    if previous:
        QgsNetworkAccessManager.removeRequestPreprocessor(previous[0])

    expected_project = Path(project_path).resolve() if project_path else None

    def authenticate(request):
        if expected_project is not None:
            current = QgsProject.instance().fileName()
            if not current or Path(current).resolve() != expected_project:
                return
        before = request.url().toString()
        after = authenticated_url(before, key)
        if after != before:
            request.setUrl(QUrl(after))

    identifier = QgsNetworkAccessManager.setRequestPreprocessor(authenticate)
    # Retain the callable while C++ can call it. No credential is stored in QGIS settings.
    manager._canakkale_carto_hook = (identifier, authenticate)
    _HOOK_STATE = (manager, identifier, authenticate)
    return {"installed": True, "scope": "CARTO light_all HTTPS tile requests",
            "project_urls_modified": False, "key_saved_to_settings": False}


def start_in_qgis() -> None:
    """Entry point used by --code after QGIS has initialized its Python runtime."""
    from qgis.core import QgsProject, Qgis
    from qgis.utils import iface

    project = QgsProject.instance()
    dirty_before = project.isDirty()
    result = {"installed": False, "qgis_version": Qgis.QGIS_VERSION}
    try:
        result.update(install_request_auth(read_key(None), project.fileName()))
        result.update(project_path=project.fileName(),
                      project_dirty_before=dirty_before, project_dirty_after=project.isDirty())
        if iface:
            iface.mapCanvas().refreshAllLayers()
    except (ValueError, ImportError, AttributeError, RuntimeError, TypeError):
        result["error"] = "CARTO erişimi kurulamadı; anahtar dosyasını ve QGIS Python desteğini kontrol edin."
        if iface:
            iface.messageBar().pushWarning("CARTO", result["error"])
    status_file = os.environ.get("CANAKKALE_CARTO_STATUS_FILE")
    if status_file:
        # Optional explicit diagnostic destination; no key or request URL is written.
        with Path(status_file).open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")


def qgis_executable(selection: str | None) -> Path:
    value = selection or os.environ.get("QGIS_BIN")
    candidates = []
    if value:
        selected = Path(value).expanduser()
        candidates.extend([selected] if not selected.is_dir() else
                          [selected / name for name in ("QGIS", "qgis", "qgis.exe")])
    else:
        candidates.append(Path("/Applications/QGIS.app/Contents/MacOS/QGIS"))
        candidates.extend(Path(p) for name in ("qgis", "qgis-bin.exe")
                          if (p := shutil.which(name)))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    raise ValueError("QGIS çalıştırıcısı bulunamadı; --qgis-bin belirtin.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT / "qgis/canakkale_disaster_priority.qgz")
    parser.add_argument("--key-file", type=Path)
    parser.add_argument("--qgis-bin")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--status-file", type=Path, help="Optional new private diagnostic JSON file")
    args = parser.parse_args(argv)
    try:
        read_key(args.key_file)
        binary = qgis_executable(args.qgis_bin)
        project = args.project.expanduser().resolve()
        if not project.is_file() or project.suffix.lower() not in {".qgs", ".qgz"}:
            raise ValueError("Açılacak QGS/QGZ projesi bulunamadı.")
        if args.status_file and (args.status_file.exists() or not args.status_file.parent.is_dir()):
            raise ValueError("Tanı dosyası yeni olmalı ve üst klasörü mevcut olmalı.")
        if args.check:
            print(json.dumps({"status": "ready", "network_authentication": "not_tested",
                              "project_modified": False, "launch_performed": False}))
            return 0
        env = os.environ.copy()
        # Keep an isolated GDAL/Conda environment from contaminating the GUI's Python/PROJ.
        for name in ("PYTHONHOME", "PYTHONPATH", "GDAL_DATA", "PROJ_DATA", "PROJ_LIB"):
            env.pop(name, None)
        if env.get("QT_QPA_PLATFORM") == "offscreen":
            env.pop("QT_QPA_PLATFORM")
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["CANAKKALE_CARTO_SCRIPT_DIR"] = str(Path(__file__).resolve().parent)
        private_file = args.key_file or env.get("CARTO_BASEMAPS_KEY_FILE")
        if private_file:
            env["CARTO_BASEMAPS_KEY_FILE"] = str(Path(private_file).expanduser().resolve())
            env.pop("CARTO_BASEMAPS_API_KEY", None)
        if args.status_file:
            env["CANAKKALE_CARTO_STATUS_FILE"] = str(args.status_file.resolve())
        else:
            env.pop("CANAKKALE_CARTO_STATUS_FILE", None)
        startup = Path(__file__).resolve().with_name("qgis_carto_startup.py")
        subprocess.Popen([str(binary), "--code", str(startup), "--project", str(project)],
                         env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        print("QGIS açılışı başlatıldı. Canlı CARTO görünümünü QGIS'te kontrol edin.")
        return 0
    except (ValueError, OSError):
        print("CARTO açılışı hazırlanamadı. Proje/anahtar dosyasını ve QGIS yolunu kontrol edin.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
