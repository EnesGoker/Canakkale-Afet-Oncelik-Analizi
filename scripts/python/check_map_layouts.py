#!/usr/bin/env python3
"""Read-only QGIS layout and saved map export integrity check.

Only the Python standard library is required. Actual provider loading is checked
separately by check_qgis_runtime.py. PDF page counts are recorded and verified at
export time; this check validates the recorded files' bytes, not a PDF renderer.
Exit codes: 0 passed; 1 missing, stale or invalid project/contract/exports.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
from qgis_identity import validate_metadata_revision

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = Path("config/map_layouts_v1.json")
MAP_TYPE = "65639"
LEGEND_TYPE = "65642"
WEB_PROVIDERS = {"wms", "xyz", "wfs", "vectortile", "arcgismapserver", "arcgisfeatureserver"}
AGREEMENT_COLORS = ["#e2e5e9", "#f8d36a", "#e98747", "#542788"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def xml_sha256(element: ET.Element) -> str:
    """Stable attribute order/indentation independent hash; child order matters."""
    canonical = ET.canonicalize(ET.tostring(element, encoding="unicode"), strip_text=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def project_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or "\\" in relative:
        raise ValueError("Sözleşme/manifest yolları proje köküne göre göreli olmalı.")
    result = (root / relative).resolve()
    if not result.is_relative_to(root) or result == root:
        raise ValueError("Sözleşme/manifest yolu proje kökünün dışında.")
    return result


def source_path(root: Path, project_dir: Path, source: str, provider: str) -> Path | None:
    if provider.lower() in WEB_PROVIDERS:
        return None  # No network call; availability is explicitly outside this check.
    if provider not in {"gdal", "ogr", "spatialite"}:
        raise ValueError("Bilinmeyen yerel katman sağlayıcısı.")
    filename = source.split("|", 1)[0]
    if (not filename or Path(filename).is_absolute() or "\\" in filename
            or re.match(r"^[a-z][a-z0-9+.-]*:", filename, re.IGNORECASE)
            or filename.startswith("/vsi")):
        raise ValueError("Yerel katman kaynağı taşınabilir göreli dosya yolu değil.")
    path = (project_dir / filename).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Yerel katman kaynağı proje kökünün dışında.")
    if not path.is_file():
        raise ValueError("Yerel katman kaynağı eksik.")
    return path


def validate_contract(contract: dict) -> None:
    if not isinstance(contract, dict) or contract.get("format_version") != 1:
        raise ValueError("Harita sözleşmesinin sürümü geçersiz.")
    records = contract.get("layouts")
    if not isinstance(records, list) or len(records) != 13:
        raise ValueError("Harita sözleşmesi tam 13 düzen içermeli.")
    names, stems, thematic = [], [], []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Düzen sözleşmesi satırı geçersiz.")
        for key in ("layout_name", "output_stem", "thematic_layer_id", "raster_path", "layout_sha256"):
            if not isinstance(record.get(key), str) or not record[key]:
                raise ValueError("Düzen sözleşmesinde zorunlu alan eksik.")
        if not re.fullmatch(r"[0-9]{2}_[a-z0-9_]+", record["output_stem"]):
            raise ValueError("Düzen çıktı adı geçersiz.")
        ids = record.get("layer_ids_ordered")
        styles = record.get("expected_layer_style_hashes")
        if (not isinstance(ids, list) or not ids or any(not isinstance(v, str) or not v for v in ids)
                or len(set(ids)) != len(ids) or record["thematic_layer_id"] not in ids):
            raise ValueError("Düzenin sıralı katman kümesi geçersiz.")
        if not isinstance(styles, dict) or set(styles) != set(ids):
            raise ValueError("Düzen stil sözleşmesi katman kümesiyle eşleşmiyor.")
        hashes = [record["layout_sha256"], *styles.values()]
        if any(not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{64}", v) for v in hashes):
            raise ValueError("Düzen sözleşmesinde SHA-256 alanı geçersiz.")
        names.append(record["layout_name"])
        stems.append(record["output_stem"])
        thematic.append(record["thematic_layer_id"])
    if any(len(set(values)) != 13 for values in (names, stems, thematic)):
        raise ValueError("Düzen adları, çıktı adları ve tematik katmanlar benzersiz olmalı.")
    if [stem[:2] for stem in stems] != [f"{i:02d}" for i in range(1, 14)]:
        raise ValueError("Düzenler 01–13 çıktı sırasıyla kaydedilmeli.")



def validate_agreement_style(style: ET.Element) -> None:
    shader = style.find(".//colorrampshader")
    if shader is None or shader.get("colorRampType") != "EXACT":
        raise ValueError("13. haritanın renk enterpolasyonu EXACT olmalı.")
    items = shader.findall("item")
    try:
        values = [float(item.get("value", "nan")) for item in items]
    except ValueError:
        raise ValueError("13. haritanın renk sınıf değerleri geçersiz.") from None
    if values != [0.0, 1.0, 2.0, 3.0]:
        raise ValueError("13. haritanın renk değerleri tam 0, 1, 2, 3 olmalı.")
    if [item.get("color", "").lower() for item in items] != AGREEMENT_COLORS:
        raise ValueError("13. haritanın kullanıcı tarafından onaylanan renkleri değişmiş.")
    if any(item.get("alpha") != "255" or not item.get("label", "").strip() for item in items):
        raise ValueError("13. haritanın sınıf açıklaması/opaklığı geçersiz.")
    legend = shader.find("rampLegendSettings")
    if legend is None or legend.get("useContinuousLegend") != "0":
        raise ValueError("13. haritada sürekli lejant kapalı olmalı.")


def validate_layout(layout: ET.Element, record: dict, all_thematic_ids: set[str], layers: dict) -> None:
    maps = layout.findall(f"LayoutItem[@type='{MAP_TYPE}']")
    legends = layout.findall(f"LayoutItem[@type='{LEGEND_TYPE}']")
    if len(maps) != 1 or len(legends) != 1:
        raise ValueError("Her düzende tam bir harita ve bir lejant bulunmalı.")
    map_item, legend = maps[0], legends[0]
    if map_item.get("keepLayerSet") != "true" or map_item.get("followPreset", "false") != "false":
        raise ValueError("Harita katman kümesi kilitli olmalı; tema izleme kapalı olmalı.")
    ids = [(e.text or "").strip() for e in map_item.findall("./LayerSet/Layer")]
    if ids != record["layer_ids_ordered"]:
        raise ValueError("Haritanın sıralı katman kümesi sözleşmeyle eşleşmiyor.")
    if any(layer_id not in layers for layer_id in ids):
        raise ValueError("Harita kümesindeki katman projede tanımlı değil.")
    entries = map_item.findall("./LayerStyles/LayerStyle")
    style_ids = [e.get("layerid") for e in entries]
    if len(set(style_ids)) != len(style_ids) or set(style_ids) != set(ids):
        raise ValueError("Kilitli katman stilleri harita katman kümesini tam karşılamıyor.")
    styles = {}
    for entry in entries:
        style = entry.find("qgis")
        if style is None or xml_sha256(style) != record["expected_layer_style_hashes"][entry.get("layerid")]:
            raise ValueError("Kilitli katman stili sözleşmeyle eşleşmiyor.")
        styles[entry.get("layerid")] = style
    if not map_item.get("uuid") or legend.get("map_uuid") != map_item.get("uuid"):
        raise ValueError("Lejant bu düzenin harita UUID'sine bağlı değil.")
    legend_ids = [e.get("id") for e in legend.findall(".//layer-tree-layer")]
    if (len(set(legend_ids)) != len(legend_ids) or not set(legend_ids).issubset(set(ids))
            or set(legend_ids) & all_thematic_ids != {record["thematic_layer_id"]}):
        raise ValueError("Lejant eksik/yanlış tematik katman içeriyor.")
    if set(ids) & all_thematic_ids != {record["thematic_layer_id"]}:
        raise ValueError("Harita kümesi başka bir haritanın tematik katmanını içeriyor.")
    if record["output_stem"].startswith("13_"):
        validate_agreement_style(styles[record["thematic_layer_id"]])
    if xml_sha256(layout) != record["layout_sha256"]:
        raise ValueError("Düzenin sayfa tasarımı/içeriği onaylı sözleşmeden farklı.")


def validate_exports(root: Path, contract: dict, qgs_path: Path) -> tuple[int, str]:
    manifest_path = project_path(root, contract["export_manifest"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (not isinstance(manifest, dict) or type(manifest.get("format_version")) is not int
            or manifest["format_version"] not in (1, 2)):
        raise ValueError("Harita çıktı manifesti geçersiz.")
    if manifest["format_version"] == 1:
        if manifest.get("project_qgs_sha256") != sha256_file(qgs_path):
            raise ValueError("Harita çıktıları güncel QGS dosyasıyla eşleşmiyor; yeniden dışa aktarılmalı.")
    else:
        validate_metadata_revision(qgs_path.read_bytes(), project_path(root, contract["project_qgz"]).read_bytes(),
                                   manifest.get("project_qgs_sha256"), manifest.get("metadata_revision"))
    expected = {f"outputs/maps/{kind}/{r['output_stem']}.{kind}" for r in contract["layouts"] for kind in ("png", "pdf")}
    atlas = contract["atlas_path"]
    project_path(root, atlas)
    if atlas in expected:
        raise ValueError("Atlas yolu tekil harita yollarından farklı olmalı.")
    expected.add(atlas)
    rows = manifest.get("files")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Harita çıktı manifestinin dosya listesi geçersiz.")
    paths = [row.get("path") for row in rows]
    if any(not isinstance(p, str) for p in paths) or len(set(paths)) != len(paths) or set(paths) != expected:
        raise ValueError("Harita manifesti tam 13 PNG, 13 PDF ve bir atlas içermeli.")
    for row in rows:
        path = project_path(root, row["path"])
        if not path.is_file():
            raise ValueError(f"Harita çıktısı eksik: {row['path']}")
        if (type(row.get("size_bytes")) is not int or row["size_bytes"] <= 0
                or path.stat().st_size != row["size_bytes"] or row.get("sha256") != sha256_file(path)):
            raise ValueError(f"Harita çıktısının boyutu/SHA-256 özeti değişmiş: {row['path']}")
        with path.open("rb") as stream:
            header = stream.read(24)
        if path.suffix.lower() == ".png":
            if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
                raise ValueError("Harita PNG başlığı geçersiz.")
            width, height = struct.unpack(">II", header[16:24])
            if not width or not height:
                raise ValueError("Harita PNG boyutları geçersiz.")
            if "width_px" in row and (row["width_px"], row.get("height_px")) != (width, height):
                raise ValueError("Harita PNG boyutları manifestle eşleşmiyor.")
        elif path.suffix.lower() == ".pdf":
            if not header.startswith(b"%PDF-"):
                raise ValueError("Harita PDF başlığı geçersiz.")
            if row.get("page_count") != (13 if row["path"] == atlas else 1):
                raise ValueError("Kaydedilen PDF sayfa kontrolü eksik/yanlış.")
        else:
            raise ValueError("Harita manifestinde desteklenmeyen çıktı biçimi.")
    return len(rows), contract["export_manifest"]


def audit_project(project_root: Path, contract_path: Path = CONTRACT) -> tuple[dict, int]:
    root = project_root.resolve()
    result = {"format_version": 1, "status": "failed", "passed": False, "layout_count": 0,
              "export_count": 0, "errors": [], "network_access": "not_used", "writes_performed": False,
              "pdf_validation": "saved-file SHA-256; page counts recorded at export, not reparsed"}
    try:
        path = contract_path if contract_path.is_absolute() else project_path(root, contract_path.as_posix())
        path = path.resolve()
        if not path.is_relative_to(root):
            raise ValueError("Harita sözleşmesi proje kökünün içinde olmalı.")
        contract = json.loads(path.read_text(encoding="utf-8"))
        validate_contract(contract)
        qgs_path = project_path(root, contract["project_qgs"])
        qgz_path = project_path(root, contract["project_qgz"])
        qgs_bytes = qgs_path.read_bytes()
        with zipfile.ZipFile(qgz_path) as archive:
            names = [name for name in archive.namelist() if name.lower().endswith(".qgs")]
            if len(names) != 1 or archive.read(names[0]) != qgs_bytes:
                raise ValueError("QGS ve QGZ içindeki proje XML'i birebir eşleşmiyor.")
        xml = ET.fromstring(qgs_bytes)
        if xml.tag != "qgis":
            raise ValueError("Dosya bir QGIS projesi değil.")
        nodes = xml.findall("./projectlayers/maplayer")
        layer_ids = [(e.findtext("id") or "").strip() for e in nodes]
        if not layer_ids or any(not v for v in layer_ids) or len(set(layer_ids)) != len(layer_ids):
            raise ValueError("Proje katman kimlikleri eksik/tekrarlı.")
        layers = dict(zip(layer_ids, nodes))
        for layer in nodes:
            source_path(root, qgs_path.parent, layer.findtext("datasource") or "", layer.findtext("provider") or "")
        for node in xml.iter():
            if "source" in node.attrib and ("provider" in node.attrib or "providerKey" in node.attrib):
                source_path(root, qgs_path.parent, node.get("source", ""), node.get("provider", node.get("providerKey", "")))
        layout_nodes = xml.findall("./Layouts/Layout")
        layout_names = [e.get("name") for e in layout_nodes]
        expected_names = [r["layout_name"] for r in contract["layouts"]]
        if len(set(layout_names)) != len(layout_names) or set(layout_names) != set(expected_names):
            raise ValueError("Proje düzenleri tam 13 onaylı düzenle eşleşmiyor.")
        layouts = dict(zip(layout_names, layout_nodes))
        all_thematic = {r["thematic_layer_id"] for r in contract["layouts"]}
        for record in contract["layouts"]:
            layer = layers.get(record["thematic_layer_id"])
            if layer is None:
                raise ValueError("Tematik katman projede eksik.")
            resolved = source_path(root, qgs_path.parent, layer.findtext("datasource") or "", layer.findtext("provider") or "")
            if resolved != project_path(root, record["raster_path"]):
                raise ValueError("Tematik katmanın dosya yolu sözleşmeyle eşleşmiyor.")
            try:
                validate_layout(layouts[record["layout_name"]], record, all_thematic, layers)
            except ValueError as error:
                raise ValueError(f"{record['layout_name']}: {error}") from None
        result["layout_count"] = len(layout_nodes)
        result["export_count"], result["export_manifest"] = validate_exports(root, contract, qgs_path)
    except ValueError as error:
        result["errors"].append(str(error))
    except (OSError, ET.ParseError, zipfile.BadZipFile, KeyError, TypeError, RuntimeError, struct.error):
        result["errors"].append("Harita sözleşmesi, QGIS projesi veya çıktı manifesti okunamadı/eksik/bozuk.")
    result["passed"] = not result["errors"]
    result["status"] = "passed" if result["passed"] else "failed"
    return result, 0 if result["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Salt okunur kontrol (varsayılan)")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result, code = audit_project(args.project_root, args.contract)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Harita düzenleri: {result['status']} · {result['layout_count']} düzen · {result['export_count']} çıktı")
        for error in result["errors"]:
            print(f"HATA: {error}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
