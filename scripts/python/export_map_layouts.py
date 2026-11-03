#!/usr/bin/env python3
"""Export the approved QGIS layouts without editing their design or project.

``--check`` uses only the standard library and checks the saved project/outputs.
``--generate`` needs PyQGIS, an explicit empty output directory, and explicit
``--allow-web-basemap`` when a selected layout contains a web basemap.
Exit codes: 0 success; 1 invalid input/export; 2 PyQGIS unavailable.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from collections import Counter
import gc
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = Path("config/map_layouts_v1.json")


class DependencyUnavailable(RuntimeError):
    """The actual QGIS export could not start in this interpreter."""


class MapRenderingFailure(ValueError):
    """Export failure carrying counts/categories, never provider URLs/messages."""

    def __init__(self, message: str, diagnostics: dict):
        super().__init__(message)
        self.diagnostics = diagnostics


def carto_source_with_key(source: str, key: str) -> str:
    """Add a transient CARTO key to the nested URL of an approved XYZ URI.

    The returned value is for an in-memory provider only. Neither input nor key
    is ever included in validation errors; callers must not write the URI.
    """
    if (not isinstance(key, str) or not key or len(key) > 4096
            or any(ord(character) < 33 or ord(character) > 126 for character in key)):
        raise ValueError("CARTO çalışma zamanı anahtarı boş veya geçersiz.")
    message = "Çalışma zamanı anahtarı yalnız onaylı CARTO light_all HTTPS altlığına uygulanabilir."
    try:
        pairs = parse_qsl(source, keep_blank_values=True)
        urls = [value for name, value in pairs if name == "url"]
        if len(urls) != 1:
            raise ValueError(message)
        parts = urlsplit(urls[0])
        allowed_hosts = {"basemaps.cartocdn.com", "a.basemaps.cartocdn.com",
                         "b.basemaps.cartocdn.com", "c.basemaps.cartocdn.com"}
        if (parts.scheme.lower() != "https" or parts.hostname not in allowed_hosts
                or parts.port not in (None, 443) or parts.username or parts.password
                or parts.fragment or not parts.path.startswith("/light_all/")):
            raise ValueError(message)
        # CARTO's documented basemap parameter is "key":
        # https://www.carto.com/basemaps/apikey/
        query = [(name, value) for name, value in parse_qsl(parts.query, keep_blank_values=True)
                 if name.lower() not in {"key", "api_key"}]
        query.append(("key", key))
        url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))
        # QGIS's encoded XYZ URI keeps URL scheme/path separators literal.
        # Escaping ':' produces a provider URL with an unknown protocol.
        return urlencode([(name, url if name == "url" else value) for name, value in pairs], safe=":/?")
    except (ValueError, TypeError, AttributeError):
        raise ValueError(message) from None


def select_records(contract: dict, layouts: str | None = None) -> list[dict]:
    """Select numeric layout prefixes while retaining the approved atlas order."""
    records = contract["layouts"]
    if layouts is None:
        return list(records)
    tokens = [token.strip() for token in layouts.split(",")]
    if not tokens or any(not token.isdigit() or len(token) > 2 for token in tokens):
        raise ValueError("Düzen seçimi 14 veya 01,02 biçiminde olmalı.")
    numbers = [int(token) for token in tokens]
    known = {int(record["output_stem"][:2]) for record in records}
    if len(set(numbers)) != len(numbers) or not set(numbers).issubset(known):
        raise ValueError("Düzen seçimi tekrarlı veya bilinmeyen bir numara içeriyor.")
    return [record for record in records if int(record["output_stem"][:2]) in numbers]


def validate_output_dir(output_dir: Path) -> Path:
    path = Path(output_dir).expanduser().absolute()
    if path.is_symlink() or (path.exists() and (not path.is_dir() or any(path.iterdir()))):
        raise ValueError("Çıktı klasörü yeni veya tamamen boş olmalı; mevcut dosyalar değiştirilmez.")
    return path


@contextmanager
def staged_output(output_dir: Path):
    """Publish a complete new output tree; a failed export leaves no partial tree."""
    target = validate_output_dir(output_dir)
    existed = target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".canakkale-map-export-", dir=target.parent) as temporary:
        stage = Path(temporary) / "complete"
        stage.mkdir()
        yield stage
        # Recheck after rendering so an intervening user file is never removed.
        validate_output_dir(target)
        if existed:
            if not target.exists():
                raise ValueError("Çıktı klasörü dışa aktarım sırasında değişmiş.")
            target.rmdir()  # Only an empty directory can be removed.
        elif target.exists():
            raise ValueError("Çıktı klasörü dışa aktarım sırasında başka bir işlem tarafından oluşturulmuş.")
        try:
            stage.rename(target)
        except OSError:
            if existed and not target.exists():
                target.mkdir()
            raise


def load_export_inputs(root: Path, contract_path: Path = CONTRACT) -> dict:
    """Validate approved inputs before the first output exists (no export check)."""
    from check_map_layouts import (
        project_path, sha256_file, source_path, validate_contract, validate_layout,
    )

    root = root.resolve()
    path = contract_path if contract_path.is_absolute() else project_path(root, contract_path.as_posix())
    path = path.resolve()
    if not path.is_relative_to(root):
        raise ValueError("Düzen sözleşmesi proje kökünün içinde olmalı.")
    contract = json.loads(path.read_text(encoding="utf-8"))
    validate_contract(contract)
    qgs = project_path(root, contract["project_qgs"])
    qgz = project_path(root, contract["project_qgz"])
    content = qgs.read_bytes()
    with zipfile.ZipFile(qgz) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".qgs")]
        if len(names) != 1 or archive.read(names[0]) != content:
            raise ValueError("QGS ve QGZ aynı onaylı projeyi içermeli.")
    xml = ET.fromstring(content)
    nodes = xml.findall("./projectlayers/maplayer")
    layers = {(node.findtext("id") or "").strip(): node for node in nodes}
    if xml.tag != "qgis" or len(layers) != len(nodes) or "" in layers:
        raise ValueError("QGIS katman kimlikleri eksik veya tekrarlı.")
    for layer in nodes:
        source_path(root, qgs.parent, layer.findtext("datasource") or "", layer.findtext("provider") or "")
    for node in xml.iter():
        if "source" in node.attrib and ("provider" in node.attrib or "providerKey" in node.attrib):
            source_path(root, qgs.parent, node.get("source", ""), node.get("provider", node.get("providerKey", "")))
    layout_nodes = xml.findall("./Layouts/Layout")
    layouts = {node.get("name"): node for node in layout_nodes}
    if (len(layouts) != len(layout_nodes)
            or set(layouts) != {record["layout_name"] for record in contract["layouts"]}):
        raise ValueError("QGIS projesi sözleşmedeki onaylı düzenlerin tamamını ve yalnız onları içermeli.")
    thematic = {record["thematic_layer_id"] for record in contract["layouts"]}
    for record in contract["layouts"]:
        layer = layers.get(record["thematic_layer_id"])
        if layer is None or source_path(root, qgs.parent, layer.findtext("datasource") or "", layer.findtext("provider") or "") != project_path(root, record["raster_path"]):
            raise ValueError("Tematik katman onaylı raster yoluyla eşleşmiyor.")
        validate_layout(layouts[record["layout_name"]], record, thematic, layers)
    return {"contract": contract, "qgs_path": qgs, "layers": layers,
            "project_qgs_sha256": sha256_file(qgs), "contract_sha256": sha256_file(path)}


def selected_web_layers(inputs: dict, records: list[dict]) -> list[str]:
    from check_map_layouts import WEB_PROVIDERS

    ids = {layer_id for record in records for layer_id in record["layer_ids_ordered"]}
    return sorted(layer_id for layer_id in ids
                  if (inputs["layers"][layer_id].findtext("provider") or "").lower() in WEB_PROVIDERS)


def inspect_export(path: Path, relative: str) -> dict:
    from check_map_layouts import sha256_file

    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("QGIS beklenen harita dosyasını oluşturmadı.")
    with path.open("rb") as stream:
        header = stream.read(24)
    row = {"path": relative, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
    if path.suffix == ".png":
        if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            raise ValueError("Oluşturulan PNG başlığı geçersiz.")
        row["width_px"], row["height_px"] = struct.unpack(">II", header[16:24])
        if row["width_px"] < 4900 or row["height_px"] < 3400:
            raise ValueError("Harita PNG çözünürlüğü A3/300 DPI için yetersiz.")
    elif path.suffix == ".pdf":
        if not header.startswith(b"%PDF-"):
            raise ValueError("Oluşturulan PDF başlığı geçersiz.")
        row["page_count"] = 1  # Single-page layout asserted before export.
    else:
        raise ValueError("Desteklenmeyen harita biçimi.")
    return row


def render_qgis(root: Path, inputs: dict, records: list[dict], stage: Path,
                allow_web_basemap: bool) -> dict:
    """Lazy PyQGIS worker; all Qt/provider state lives in a disposable profile."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["GDAL_PAM_ENABLED"] = "NO"
    try:
        from qgis.core import (
            Qgis, QgsApplication, QgsLayoutExporter, QgsLayoutItemMap,
            QgsMapLayerStyle, QgsNetworkAccessManager, QgsProject, QgsProviderRegistry, QgsSettings,
        )
        from qgis.PyQt.QtNetwork import QNetworkAccessManager, QNetworkDiskCache, QNetworkRequest
    except (ImportError, OSError) as error:
        raise DependencyUnavailable("PyQGIS kullanılamıyor; QGIS'in Python ortamıyla çalıştırın.") from error
    from check_qgis_runtime import check_local_uri_types, inspect_project, read_layer_specs

    app = project = None
    network_errors, network_successes, messages = [], [], []
    output_rows = []
    web_ids = selected_web_layers(inputs, records)

    def apply_runtime_authentication():
        # Read secrets only after the saved project/local providers are loaded.
        # Provider replacement and style restoration are strictly in memory.
        key = os.environ.get("CARTO_BASEMAPS_API_KEY")
        if not web_ids:
            return "not_supplied"
        if not key:
            raise ValueError("CARTO altlığı için CARTO_BASEMAPS_API_KEY çalışma zamanı ortamında sağlanmalı.")
        for layer_id in web_ids:
            layer = project.mapLayer(layer_id)
            authenticated_source = carto_source_with_key(layer.source(), key)
            style = QgsMapLayerStyle()
            style.readFromLayer(layer)
            layer.setDataSource(authenticated_source, layer.name(), layer.providerType())
            style.writeToLayer(layer)
            if not layer.isValid():
                raise ValueError("CARTO çalışma zamanı bağlantısı QGIS tarafından açılamadı.")
        return "runtime_environment"

    def reply_finished(reply):
        status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if int(reply.error()) != 0 or (status is not None and int(status) >= 400):
            network_errors.append(f"http_{int(status)}" if status is not None and int(status) >= 400
                                  else f"qt_network_error_{int(reply.error())}")
        else:
            network_successes.append("web_request_succeeded")

    def request_timeout(*_):
        network_errors.append("web_request_timed_out")

    def log_message(message, tag, level):
        if level == Qgis.Critical and any(word in tag.lower() for word in ("wms", "network", "raster")):
            messages.append("critical_map_provider_message")

    def diagnostics(map_item=None, export_code=None):
        result = {"network_error_count": len(network_errors),
                  "network_timeout_count": network_errors.count("web_request_timed_out"),
                  "network_failure_categories": dict(sorted(Counter(network_errors).items())),
                  "map_render_error_count": len(map_item.renderingErrors()) if map_item is not None else 0,
                  "critical_provider_message_count": len(messages),
                  "web_successful_requests": len(network_successes)}
        if export_code is not None:
            result["qgis_export_code"] = int(export_code)
        return result

    try:
        with tempfile.TemporaryDirectory(prefix="canakkale-qgis-export-profile-") as profile:
            app = QgsApplication([], False, profile)
            app.initQgis()
            cache_dir = str(Path(profile) / "network-cache")
            QgsSettings().setValue("cache/directory", cache_dir)
            QgsNetworkAccessManager.setTimeout(20000)
            manager = QgsNetworkAccessManager.instance()
            cache = QNetworkDiskCache(manager)
            cache.setCacheDirectory(cache_dir)
            manager.setCache(cache)
            manager.setNetworkAccessible(QNetworkAccessManager.Accessible if allow_web_basemap else QNetworkAccessManager.NotAccessible)
            manager.finished.connect(reply_finished)
            manager.requestTimedOut.connect(request_timeout)
            QgsApplication.messageLog().messageReceived.connect(log_message)
            specs = read_layer_specs(inputs["qgs_path"])
            check_local_uri_types(specs, QgsProviderRegistry.instance())
            project = QgsProject()
            if not project.read(str(inputs["qgs_path"])):
                raise ValueError("QGIS onaylı projeyi açamadı.")
            errors, local, web = inspect_project(project, specs, root, inputs["qgs_path"], QgsProviderRegistry.instance())
            if errors or not local or any(not row["valid"] for row in local):
                raise ValueError("QGIS yerel katman doğrulaması başarısız; hiçbir çıktı yayımlanmadı.")
            if any(project.mapLayer(layer_id) is None or not project.mapLayer(layer_id).isValid() for layer_id in web_ids):
                raise ValueError("Seçilen web altlığı QGIS tarafından geçersiz bulundu.")
            authentication = apply_runtime_authentication()
            (stage / "png").mkdir()
            if any(record.get("pdf_export", True) for record in records):
                (stage / "pdf").mkdir()
            for record in records:
                layout = project.layoutManager().layoutByName(record["layout_name"])
                if layout is None or layout.pageCollection().pageCount() != 1:
                    raise ValueError("Her harita düzeni tek sayfa olmalı.")
                page_size = layout.pageCollection().page(0).pageSize()
                if abs(page_size.width() - 420) > 0.01 or abs(page_size.height() - 297) > 0.01:
                    raise ValueError("Onaylı A3 yatay sayfa boyutu değişmiş.")
                maps = [item for item in layout.items() if isinstance(item, QgsLayoutItemMap)]
                if len(maps) != 1 or [layer.id() for layer in maps[0].layers()] != record["layer_ids_ordered"]:
                    raise ValueError("QGIS'in yüklediği harita katman sırası sözleşmeyle eşleşmiyor.")
                exporter = QgsLayoutExporter(layout)
                png = QgsLayoutExporter.ImageExportSettings()
                png.dpi, png.exportMetadata, png.generateWorldFile = 300, False, False
                pdf = QgsLayoutExporter.PdfExportSettings()
                pdf.dpi, pdf.exportMetadata, pdf.appendGeoreference = 300, False, False
                pdf.writeGeoPdf = False
                kinds = (("png", png), ("pdf", pdf)) if record.get("pdf_export", True) else (("png", png),)
                for kind, settings in kinds:
                    relative = f"{kind}/{record['output_stem']}.{kind}"
                    path = stage / relative
                    result = exporter.exportToImage(str(path), settings) if kind == "png" else exporter.exportToPdf(str(path), settings)
                    app.processEvents()
                    if result != QgsLayoutExporter.Success:
                        raise MapRenderingFailure(f"QGIS {kind.upper()} dışa aktarımını tamamlayamadı.", diagnostics(maps[0], result))
                    if maps[0].renderingErrors() or network_errors or messages:
                        raise MapRenderingFailure("Harita/altlık çiziminde hata oluştu; eksik görünümlü çıktı kabul edilmedi.", diagnostics(maps[0], result))
                    output_rows.append(inspect_export(path, relative))
                print(f"Tamamlandı: {record['layout_name']} ({' ve '.join(k.upper() for k, _ in kinds)})", file=sys.stderr, flush=True)
            app.processEvents()
            if web_ids and (network_errors or not network_successes):
                raise MapRenderingFailure("Web altlığının başarılı döşeme erişimi doğrulanamadı; çıktı kabul edilmedi.", diagnostics())
            result = {"qgis_version": Qgis.QGIS_VERSION, "local_layer_count": len(local),
                      "web_layer_count": len(web), "selected_web_layer_count": len(web_ids),
                      "network_timeout_ms": 20000, "web_successful_requests": len(network_successes),
                      "network_error_count": len(network_errors), "authentication": authentication,
                      "files": output_rows}
            del exporter, maps, layout, manager, cache
            project.clear()
            project = None
            gc.collect()
            app.exitQgis()
            app = None
            return result
    finally:
        if project is not None:
            project.clear()
            project = None
        gc.collect()
        if app is not None:
            app.exitQgis()


def generate_exports(root: Path, output_dir: Path, layouts: str | None = None,
                     allow_web_basemap: bool = False, contract_path: Path = CONTRACT) -> tuple[dict, int]:
    from check_map_layouts import sha256_file

    root = root.resolve()
    report = {"format_version": 1, "status": "failed", "passed": False, "errors": [],
              "project_modified": False, "writes_performed": False}
    try:
        inputs = load_export_inputs(root, contract_path)
        records = select_records(inputs["contract"], layouts)
        if selected_web_layers(inputs, records) and not allow_web_basemap:
            raise ValueError("Seçilen düzende web altlığı var; çizmek için --allow-web-basemap açıkça belirtilmeli.")
        validate_output_dir(output_dir)
        with staged_output(output_dir) as stage:
            try:
                worker = render_qgis(root, inputs, records, stage, allow_web_basemap)
            finally:
                # Also verify after a failed provider/export, before rollback.
                report["project_modified"] = sha256_file(inputs["qgs_path"]) != inputs["project_qgs_sha256"]
            if report["project_modified"]:
                raise ValueError("QGS dosyası dışa aktarım sırasında değişti; çıktı yayımlanmadı.")
            report.update(worker)
            report.update(status="passed", passed=True, writes_performed=True,
                          project_qgs=inputs["contract"]["project_qgs"],
                          project_qgs_sha256=inputs["project_qgs_sha256"],
                          contract_sha256=inputs["contract_sha256"],
                          layout_names=[record["layout_name"] for record in records],
                          dpi=300, page_format="A3 landscape", source_project_unchanged=True,
                          network_access="configured_web_basemap_allowed" if allow_web_basemap else "disabled",
                          pdf_page_validation="one-page QGIS layout checked before successful PDF export")
            (stage / "export_run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return report, 0
    except DependencyUnavailable as error:
        report.update(status="dependency_unavailable", passed=False, writes_performed=False)
        report["errors"].append(str(error))
        return report, 2
    except (ValueError, OSError, KeyError, TypeError, ET.ParseError, zipfile.BadZipFile, RuntimeError) as error:
        report.update(status="failed", passed=False, writes_performed=False)
        if isinstance(error, MapRenderingFailure):
            report["render_diagnostics"] = error.diagnostics
        # Provider/filesystem exception messages can contain personal local paths.
        report["errors"].append(str(error) if isinstance(error, ValueError) else f"Harita dışa aktarımı tamamlanamadı ({type(error).__name__}).")
        return report, 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--generate", action="store_true")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--layouts", help="14 veya 01,02; belirtilmezse sözleşmedeki bütün düzenler")
    parser.add_argument("--allow-web-basemap", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        if args.output_dir is not None or args.layouts is not None or args.allow_web_basemap:
            parser.error("--check çıktı üretme seçeneklerini kabul etmez.")
        from check_map_layouts import audit_project
        report, code = audit_project(args.project_root, args.contract)
    else:
        if args.output_dir is None:
            parser.error("--generate için --output-dir zorunlu.")
        report, code = generate_exports(args.project_root, args.output_dir, args.layouts, args.allow_web_basemap, args.contract)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("Harita düzenleri: " + report["status"])
        for error in report.get("errors", []):
            print(error)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
