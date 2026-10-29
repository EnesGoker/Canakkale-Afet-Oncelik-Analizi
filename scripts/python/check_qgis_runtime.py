#!/usr/bin/env python3
"""Read a QGIS project with PyQGIS and validate its local file providers.

Read-only: a disposable QGIS profile is used, network access is disabled, and
no maps are rendered. Web layer connectivity is explicitly outside this check.
Exit codes: 0 passed, 1 failed, 2 the required PyQGIS runtime is unavailable.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import parse_qsl, unquote, urlsplit
import xml.etree.ElementTree as ET
import zipfile


sys.dont_write_bytecode = True
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_FILE = Path("qgis/canakkale_disaster_priority.qgz")
LOCAL_PROVIDERS = {"gdal", "ogr", "spatialite"}
WEB_PROVIDERS = {"wms", "xyz", "wfs", "arcgismapserver", "arcgisfeatureserver", "vectortile"}


def web_source(source: str, provider: str) -> bool:
    if provider.lower() in WEB_PROVIDERS:
        return True
    if re.search(r"(?:https?|ftp)://", source, re.IGNORECASE):
        return True
    try:
        if urlsplit(source).scheme.lower() in {"http", "https"}:
            return True
        return any(
            key.lower() == "url" and urlsplit(unquote(value)).scheme.lower() in {"http", "https"}
            for key, value in parse_qsl(source, keep_blank_values=True)
        )
    except ValueError:
        return False


def read_layer_specs(project_file: Path) -> list[dict[str, str | bool]]:
    """Read the declared layer IDs independently, before QGIS loads providers."""
    if project_file.suffix.lower() == ".qgz":
        with zipfile.ZipFile(project_file) as archive:
            names = [name for name in archive.namelist() if name.lower().endswith(".qgs")]
            if len(names) != 1:
                raise ValueError("QGZ paketi tam olarak bir QGS dosyası içermeli.")
            root = ET.fromstring(archive.read(names[0]))
    else:
        root = ET.parse(project_file).getroot()
    if root.tag != "qgis":
        raise ValueError("Dosya bir QGIS projesi değil.")
    specs = []
    seen = set()
    for element in root.findall("./projectlayers/maplayer"):
        layer_id = (element.findtext("id") or "").strip()
        name = (element.findtext("layername") or "").strip() or "(adsız katman)"
        provider = (element.findtext("provider") or "").strip()
        source = (element.findtext("datasource") or "").strip()
        if not layer_id or layer_id in seen:
            raise ValueError("Projedeki katman kimlikleri eksik veya tekrarlı.")
        seen.add(layer_id)
        remote = web_source(source, provider)
        if remote and provider.lower() not in WEB_PROVIDERS:
            raise ValueError("Qt ağ kapatma denetimi dışındaki uzak sağlayıcı bu çevrim dışı kontrolde desteklenmiyor.")
        if not remote and source.lower().startswith("/vsi"):
            raise ValueError("Sanal dosya sistemi kaynağı çevrim dışı yerel kontrolde desteklenmiyor.")
        if not remote and provider not in LOCAL_PROVIDERS:
            raise ValueError(f"Desteklenmeyen yerel sağlayıcı: {provider or '(boş)'}; katman: {name}.")
        specs.append({"id": layer_id, "name": name, "provider": provider, "source": source, "web": remote})
    if not specs or all(spec["web"] for spec in specs):
        raise ValueError("Projede doğrulanacak yerel dosya katmanı bulunamadı.")
    return specs


def check_local_uri_types(specs, registry) -> None:
    """Reject virtual/network/database URIs before a provider can open them.

    Qt's offline switch covers the declared web layers. GDAL/OGR also support
    network access outside Qt, so only ordinary local file URIs are accepted.
    """
    for spec in specs:
        if spec["web"]:
            continue
        filename = registry.decodeUri(spec["provider"], spec["source"]).get("path")
        if not isinstance(filename, str) or not filename:
            raise ValueError("Yerel sağlayıcı dosya yolu çözülemedi.")
        has_uri_scheme = re.match(r"^[a-z][a-z0-9+.-]*:", filename, re.IGNORECASE)
        is_windows_path = re.match(r"^[a-z]:[\\/]", filename, re.IGNORECASE)
        if filename.lower().startswith("/vsi") or (has_uri_scheme and not is_windows_path):
            raise ValueError("Sanal dosya sistemi veya bağlantı URI'si çevrim dışı yerel kontrolde desteklenmiyor.")


def inspect_project(project, specs, project_root, project_file, registry) -> tuple[list, list, list]:
    """Keep all provider objects in this scope so they die before exitQgis()."""
    errors, local_layers, web_layers = [], [], []
    loaded = project.mapLayers()
    expected_ids = {spec["id"] for spec in specs}
    if set(loaded) != expected_ids:
        errors.append("QGIS'in yüklediği katmanlar proje XML'indeki katman listesiyle eşleşmiyor.")
    for spec in specs:
        row = {"name": spec["name"], "provider": spec["provider"]}
        layer = loaded.get(spec["id"])
        if spec["web"]:
            row.update(status="skipped_offline", message="ATLANDI: web bağlantısı ve döşeme erişimi sınanmadı.")
            web_layers.append(row)
            continue
        row["valid"] = False
        if layer is None:
            row["error"] = "Yerel katman QGIS tarafından yüklenmedi."
        else:
            uri = registry.decodeUri(spec["provider"], layer.source())
            filename = uri.get("path")
            if not isinstance(filename, str) or not filename:
                row["error"] = "Sağlayıcıdan yerel dosya yolu çözülemedi."
            else:
                path = Path(filename)
                if not path.is_absolute():
                    path = project_file.parent / path
                path = path.resolve()
                if not path.is_relative_to(project_root):
                    row["error"] = "Yerel katman proje kökünün dışında."
                else:
                    row["path"] = path.relative_to(project_root).as_posix()
                    if not path.is_file():
                        row["error"] = "Yerel katman dosyası eksik."
                    elif not layer.isValid():
                        row["error"] = "QGIS sağlayıcısı katmanı geçersiz buldu (dosya içeriği/alt katman kontrol edilmeli)."
                    else:
                        row["valid"] = True
        if not row["valid"]:
            errors.append(f"{row['name']}: {row['error']}")
        local_layers.append(row)
    return errors, local_layers, web_layers


def audit_project(project_root: Path, project_file: Path) -> tuple[dict, int]:
    project_root = project_root.resolve()
    if not project_file.is_absolute():
        project_file = project_root / project_file
    project_file = project_file.resolve()
    result = {
        "format_version": 1,
        "status": "failed",
        "passed": False,
        "project": project_file.relative_to(project_root).as_posix() if project_file.is_relative_to(project_root) else "(proje kökü dışında)",
        "project_read": False,
        "network_access": "not_initialized",
        "render_performed": False,
        "local_layers": [],
        "local_layer_count": 0,
        "invalid_local_layer_count": 0,
        "web_layers": [],
        "errors": [],
    }
    if not project_file.is_relative_to(project_root):
        result["errors"].append("QGIS proje dosyası belirtilen proje kökünün içinde olmalı.")
        return result, 1
    if not project_file.is_file():
        result["errors"].append("QGIS proje dosyası bulunamadı.")
        return result, 1
    try:
        specs = read_layer_specs(project_file)
    except (OSError, ET.ParseError, zipfile.BadZipFile, RuntimeError):
        result["errors"].append("QGIS proje dosyası okunamadı veya QGS/QGZ içeriği bozuk.")
        return result, 1
    except ValueError as error:
        result["errors"].append(str(error))
        return result, 1
    result["declared_layer_count"] = len(specs)
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["GDAL_PAM_ENABLED"] = "NO"
    try:
        from qgis.core import Qgis, QgsApplication, QgsNetworkAccessManager, QgsProject, QgsProviderRegistry
        from qgis.PyQt.QtNetwork import QNetworkAccessManager
    except (ImportError, OSError):
        result["status"] = "dependency_unavailable"
        result["errors"].append("PyQGIS kullanılamıyor. QGIS'in Python ortamıyla çalıştırın; gerçek proje okuması yapılmadı.")
        return result, 2
    app = None
    project = None
    runtime_ready = False
    try:
        with tempfile.TemporaryDirectory(prefix="canakkale-qgis-qa-") as profile:
            app = QgsApplication([], False, profile)
            app.initQgis()
            manager = QgsNetworkAccessManager.instance()
            manager.setNetworkAccessible(QNetworkAccessManager.NotAccessible)
            if manager.networkAccessible() != QNetworkAccessManager.NotAccessible:
                raise RuntimeError("Ağ erişimi kapatılamadı.")
            result["network_access"] = "disabled"
            del manager
            runtime_ready = True
            check_local_uri_types(specs, QgsProviderRegistry.instance())
            project = QgsProject()
            result["qgis_version"] = Qgis.QGIS_VERSION
            result["project_read"] = bool(project.read(str(project_file)))
            if not result["project_read"]:
                result["errors"].append("QgsProject.read() proje dosyasını açamadı.")
            else:
                errors, local_layers, web_layers = inspect_project(
                    project, specs, project_root, project_file, QgsProviderRegistry.instance()
                )
                result["errors"].extend(errors)
                result["local_layers"] = local_layers
                result["web_layers"] = web_layers
                result["local_layer_count"] = len(local_layers)
                result["invalid_local_layer_count"] = sum(not row["valid"] for row in local_layers)
            project.clear()
            project = None
            gc.collect()
            app.exitQgis()
            app = None
    except Exception as error:
        # Provider exceptions may contain credentials or machine-specific paths.
        result["errors"].append(f"QGIS çalışma zamanı kontrolü tamamlanamadı ({type(error).__name__}).")
        if not runtime_ready:
            result["status"] = "dependency_unavailable"
    finally:
        if project is not None:
            project.clear()
            project = None
        gc.collect()
        if app is not None:
            app.exitQgis()
    if result["status"] == "dependency_unavailable":
        return result, 2
    result["passed"] = bool(result["project_read"] and result["local_layer_count"] and not result["errors"])
    result["status"] = "passed" if result["passed"] else "failed"
    return result, 0 if result["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Salt okunur kontrol (varsayılan)")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT, help="Kontrol edilecek proje kökü")
    parser.add_argument("--project-file", type=Path, default=PROJECT_FILE, help="Proje köküne göre QGS/QGZ dosyası veya mutlak yol")
    parser.add_argument("--json", action="store_true", help="Sonucu stdout'a JSON olarak yaz")
    args = parser.parse_args()
    result, code = audit_project(args.project_root, args.project_file)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for error in result["errors"]:
            print(f"HATA: {error}", file=sys.stderr)
        for row in result["web_layers"]:
            print(f"ATLANDI: {row['name']} ({row['provider']}); web bağlantısı sınanmadı.")
        if code == 0:
            print(f"QGIS gerçek okuma kontrolü geçti: {result['local_layer_count']} yerel katman geçerli; ağ kapalı, harita çizilmedi.")
        elif code == 2:
            print("QGIS kontrolü ÇALIŞTIRILAMADI; başarılı sayılmadı.", file=sys.stderr)
        else:
            print("QGIS gerçek okuma kontrolü BAŞARISIZ.", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
