#!/usr/bin/env python3
"""Check QGIS file paths and, optionally, a portable release manifest.

This command uses only Python's standard library and never modifies files.
The manifest covers payload files; it cannot contain its own checksum.

--scope public-source checks a copy of the public source edition, which omits
the data layers. The omitted local layers are derived twice, as the layers
missing from the public selection config and as the layers the public
packaging policy can never select; both sets must be equal, each omitted
layer must be absent and is listed as skipped, and every other check still
applies. A layer present in that scope is a failure: use the full scope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import ntpath
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import parse_qsl, unquote, urlsplit
import xml.etree.ElementTree as ET
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_FILE = Path("qgis/canakkale_disaster_priority.qgz")
MANIFEST_FILE = "portable_manifest.json"
LFS_HEADER = b"version https://git-lfs.github.com/spec/v1"
CHUNK_SIZE = 1024 * 1024
MISSING_LAYER = "Eksik katman dosyası: "
PUBLIC_SELECTION = Path("config/public_source_release_v1.json")
FULL_CHECK = "python3 scripts/python/check_portability.py --check"
DATA_HINT = (
    "Eksik yerel katmanlar: Kamu kaynak sürümü (GitHub, v0.1.x) kanonik veri katmanlarını içermez; "
    "bu kopyada eksik olmaları beklenir. Kaynak kopyasını bu kapsamla denetleyin: "
    f"{FULL_CHECK} --scope public-source. Tam QGIS görünümü kanonik veri klasörünü gerektirir; "
    "bu veriler kamuya açık bir paketle henüz dağıtılmıyor (PUBLICATION_STATUS.md)."
)


def is_lfs_pointer(path: Path) -> bool:
    with path.open("rb") as stream:
        return stream.read(len(LFS_HEADER)).startswith(LFS_HEADER)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_web_source(source: str) -> bool:
    try:
        if urlsplit(source).scheme.lower() in {"http", "https"}:
            return True
        return any(
            key == "url" and urlsplit(unquote(value)).scheme.lower() in {"http", "https"}
            for key, value in parse_qsl(source, keep_blank_values=True)
        )
    except ValueError:
        return False


def audit_project(project_root: Path) -> tuple[list[str], set[Path], int]:
    """Return errors, unique local source paths, and unique web source count."""
    project_root = project_root.resolve()
    project_file = project_root / PROJECT_FILE
    errors: list[str] = []
    local_files: set[Path] = set()
    web_sources: set[str] = set()
    if not project_file.is_file():
        return [f"QGIS projesi bulunamadı: {PROJECT_FILE.as_posix()}"], local_files, 0
    try:
        if is_lfs_pointer(project_file):
            return [f"QGIS projesi gerçek dosya yerine Git LFS işaretçisi: {PROJECT_FILE}"], local_files, 0
        with zipfile.ZipFile(project_file) as archive:
            qgs_files = [name for name in archive.namelist() if name.endswith(".qgs")]
            if len(qgs_files) != 1:
                return ["QGZ paketi tam olarak bir QGS dosyası içermeli."], local_files, 0
            root = ET.fromstring(archive.read(qgs_files[0]))
    except (OSError, zipfile.BadZipFile, ET.ParseError, RuntimeError) as error:
        return [f"QGIS projesi okunamadı: {error}"], local_files, 0

    absolute = root.find("./properties/Paths/Absolute")
    if absolute is None or (absolute.text or "").strip().lower() != "false":
        errors.append("QGIS Paths/Absolute ayarı false olmalı (göreli yollar).")

    sources = {element.text.strip() for element in root.iter("datasource") if element.text and element.text.strip()}
    sources.update(
        element.attrib["source"].strip()
        for element in root.iter("layer-tree-layer")
        if element.attrib.get("source", "").strip()
    )
    if not sources:
        errors.append("QGIS projesinde kontrol edilecek katman kaynağı bulunamadı.")
    for source in sorted(sources):
        if is_web_source(source):
            web_sources.add(source)
            continue
        local_name = source.split("|", 1)[0].strip()
        if Path(local_name).is_absolute() or ntpath.isabs(local_name) or re.match(r"^[A-Za-z]:", local_name) or local_name.lower().startswith("file:"):
            errors.append(f"Mutlak yerel katman yolu: {local_name}")
            continue
        local_path = project_file.parent / local_name
        if any(path.is_symlink() for path in (local_path, *local_path.parents) if path.is_relative_to(project_root)):
            errors.append(f"Sembolik bağlantı içeren katman yolu paketlenemez: {local_name}")
            continue
        local_file = local_path.resolve()
        try:
            relative_name = local_file.relative_to(project_root).as_posix()
        except ValueError:
            errors.append(f"Proje klasörünün dışına çıkan katman yolu: {local_name}")
            continue
        local_files.add(local_file)
        if not local_file.is_file():
            errors.append(f"{MISSING_LAYER}{relative_name}")
            continue
        try:
            if is_lfs_pointer(local_file):
                errors.append(f"Gerçek veri yerine Git LFS işaretçisi: {relative_name}")
        except OSError as error:
            errors.append(f"Katman okunamadı: {relative_name}: {error}")
    return errors, local_files, len(web_sources)


def public_source_omissions(project_root: Path, local_names: set[str]) -> set[str]:
    """Return the QGIS local layers the public source edition omits; both definitions must agree."""
    from build_public_source_release import approved_shape, safe_relative
    selection = json.loads((project_root / PUBLIC_SELECTION).read_text(encoding="utf-8"))
    published = {row if isinstance(row, str) else row["path"] for row in selection["files"]}
    unselected = {name for name in local_names if name not in published}
    unpublishable = set()
    for name in local_names:
        try:
            approved_shape(safe_relative(name))
        except ValueError:
            unpublishable.add(name)
    if not unselected or unselected != unpublishable:
        raise ValueError("Kamu kaynak kapsamının iki tanımı (seçim listesi ve paketleme politikası) uyuşmuyor: "
                         + ", ".join(sorted(unselected ^ unpublishable) or ["atlanacak yerel katman yok"]))
    return unselected


def verify_manifest(project_root: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    manifest_path = project_root / MANIFEST_FILE
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"{MANIFEST_FILE} okunamadı: {error}"], 0
    if not isinstance(manifest, dict) or manifest.get("format_version") != 1 or not isinstance(manifest.get("files"), list):
        return ["Portable manifest biçimi geçersiz."], 0
    seen: set[str] = set()
    verified = 0
    for entry in manifest["files"]:
        if not isinstance(entry, dict):
            errors.append("Manifest dosya kaydı geçersiz.")
            continue
        name, size, digest = entry.get("path"), entry.get("size"), entry.get("sha256")
        if not isinstance(name, str) or not name or "\\" in name or PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or re.match(r"^[A-Za-z]:", name):
            errors.append(f"Manifest yolu geçersiz: {name!r}")
            continue
        if name in seen or name == MANIFEST_FILE:
            errors.append(f"Manifest yolu tekrarlı veya kendi kendine referans veriyor: {name}")
            continue
        seen.add(name)
        if type(size) is not int or size < 0 or not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            errors.append(f"Manifest boyut/SHA256 kaydı geçersiz: {name}")
            continue
        path = project_root / name
        if path.is_symlink() or not path.resolve().is_relative_to(project_root) or not path.is_file():
            errors.append(f"Manifest dosyası eksik veya güvenli bir yerel dosya değil: {name}")
            continue
        try:
            if path.stat().st_size != size:
                errors.append(f"Dosya boyutu uyuşmuyor: {name}")
            elif sha256_file(path) != digest:
                errors.append(f"SHA256 uyuşmuyor: {name}")
            else:
                verified += 1
        except OSError as error:
            errors.append(f"Manifest dosyası okunamadı: {name}: {error}")
    if not seen:
        errors.append("Manifest dosya listesi boş.")
    return errors, verified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT, help="Kontrol edilecek proje kökü")
    parser.add_argument("--check", action="store_true", help="Salt okunur kontrol (varsayılan)")
    parser.add_argument("--verify-manifest", action="store_true", help="Portable paketin dosya boyutlarını ve SHA256 değerlerini de doğrula")
    parser.add_argument("--scope", choices=("full", "public-source"), default="full",
                        help="full: bütün yerel katmanlar bulunmalı (varsayılan); public-source: dağıtılmayan katmanlar listelenip atlanır")
    args = parser.parse_args()
    if args.scope == "public-source" and args.verify_manifest:
        parser.error("--verify-manifest yalnız tam kapsamda (portable paket) kullanılır")
    project_root = args.project_root.resolve()
    errors, local_files, web_count = audit_project(project_root)
    skipped: list[str] = []
    if args.scope == "public-source":
        names = {path.relative_to(project_root).as_posix() for path in local_files}
        try:
            omitted = public_source_omissions(project_root, names)
        except (OSError, ValueError, KeyError, TypeError) as error:
            errors.append(str(error))
            omitted = set()
        present = sorted(name for name in omitted if (project_root / name).exists() or (project_root / name).is_symlink())
        skipped = sorted(omitted - set(present))
        errors = [error for error in errors if not (error.startswith(MISSING_LAYER) and error[len(MISSING_LAYER):] in omitted)]
        errors += [f"Kamu kaynak kapsamında dağıtılmayan yerel katman bulundu: {name}" for name in present]
        if present:
            errors.append(f"Bu kopyada kanonik veri var ({len(present)}/{len(omitted)} katman); tam kapsamla denetleyin: {FULL_CHECK}")
    if args.verify_manifest:
        manifest_errors, verified = verify_manifest(project_root)
        errors.extend(manifest_errors)
        print(f"Manifest: {verified} dosya doğrulandı.")
    for name in skipped:
        print(f"ATLANDI (kamu kaynak sürümünde dağıtılmaz): {name}")
    if errors:
        for error in errors:
            print(f"HATA: {error}", file=sys.stderr)
        if args.scope == "full" and any(error.startswith(MISSING_LAYER) for error in errors):
            print(DATA_HINT, file=sys.stderr)
        return 1
    if args.scope == "public-source":
        print(f"QGIS taşınabilirlik kontrolü (kamu kaynak kapsamı) geçti: {len(skipped)} yerel katman listelenip atlandı, "
              f"{len(local_files) - len(skipped)} yerel dosya doğrulandı, {web_count} web kaynağı; göreli yollar.")
        return 0
    print(f"QGIS taşınabilirlik kontrolü geçti: {len(local_files)} yerel dosya, {web_count} web kaynağı; göreli yollar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
