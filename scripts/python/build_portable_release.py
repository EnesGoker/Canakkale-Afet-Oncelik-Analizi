#!/usr/bin/env python3
"""Plan or build a self-contained portable QGIS release with SHA256 checksums.

The default / --check mode never writes files. --build creates an archive;
existing output files are always preserved. No files are uploaded.
This is a local technical package, not a public distribution rights approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import zipfile

# --check must not create __pycache__ when importing the shared checker.
sys.dont_write_bytecode = True

from check_portability import CHUNK_SIZE, MANIFEST_FILE, PROJECT_ROOT, audit_project, is_lfs_pointer, sha256_file


ARCHIVE_ROOT = "canakkale-disaster-priority"
ARCHIVE_NAME = f"{ARCHIVE_ROOT}-portable.zip"
ASSET_LIMIT = 2 * 1024**3
ROOT_FILES = (
    "README.md", "README.en.md", ".gitignore", ".gitattributes", "requirements.txt",
    "LICENSE", "LICENSE_SCOPE.md", "PUBLICATION_STATUS.md",
)
INCLUDE_DIRS = (
    "config", "docs", "scripts", "qgis", "data/processed", "data/reference",
    "data/raw/admin", "data/raw/earthquake/afad_tdth", "outputs",
)
SKIP_DIR_NAMES = {"__pycache__", ".git", ".pytest_cache", ".mypy_cache", ".ruff_cache", "__MACOSX"}
SKIP_NAMES = {".DS_Store", "Thumbs.db", ".directory"}
PRIVATE_PATHS = {
    Path("outputs/report/canakkale_disaster_priority_academic_report.pages"),
    Path("outputs/report/canakkale_disaster_priority_academic_report.docx"),
    Path("outputs/report/canakkale_disaster_priority_public_report.pages"),
    Path("AGENTS.md"),
    Path("docs/portfolio_roadmap.md"),
    Path("docs/baseline_startup_summary.md"),
    Path("docs/publication_preparation_summary.md"),
    Path("docs/dokumantasyon_dil_standardi.md"),
}
INTERNAL_STAGE_SUMMARY = re.compile(r"[^/]+_stage[0-9]+_summary\.md")
SKIP_SUFFIXES = (".pyc", ".pyo", ".tmp", ".bak", ".save", ".swp", ".swo", ".lock", ".qgd", ".qgd-wal", ".qgd-shm", ".gpkg-wal", ".gpkg-shm", ".gpkg-journal", ".aux.xml", "~")


def excluded(path: Path, project_root: Path, output_dir: Path) -> bool:
    relative = path.relative_to(project_root)
    return (
        path.is_symlink()
        or relative in PRIVATE_PATHS
        or (relative.is_relative_to("outputs/report") and path.suffix.lower() == ".pages")
        or (relative.parent == Path("docs") and INTERNAL_STAGE_SUMMARY.fullmatch(relative.name) is not None)
        or relative.is_relative_to(".codex/internal")
        or path.is_relative_to(output_dir)
        or relative.is_relative_to("outputs/temp")
        or relative.is_relative_to("data/processed/analysis/archive")
        or any(part in SKIP_DIR_NAMES for part in relative.parts)
        or path.name in SKIP_NAMES
        or path.name.startswith("._")
        or path.name.lower().endswith(SKIP_SUFFIXES)
    )


def collect_files(project_root: Path, output_dir: Path) -> list[Path]:
    selected: set[Path] = set()
    for name in ROOT_FILES:
        path = project_root / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Gerekli proje dosyası eksik: {name}")
        selected.add(path)
    for name in INCLUDE_DIRS:
        directory = project_root / name
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError(f"Gerekli proje dizini eksik: {name}")
        for current, dirs, names in os.walk(directory, followlinks=False):
            current_path = Path(current)
            dirs[:] = sorted(item for item in dirs if not excluded(current_path / item, project_root, output_dir))
            for item in sorted(names):
                path = current_path / item
                if path.is_file() and not excluded(path, project_root, output_dir):
                    selected.add(path)
    return sorted(selected, key=lambda path: path.relative_to(project_root).as_posix())


def build_archive(project_root: Path, files: list[Path], output_dir: Path) -> Path:
    archive_path = output_dir / ARCHIVE_NAME
    partial_path = output_dir / f"{ARCHIVE_NAME}.partial"
    checksum_path = output_dir / f"{ARCHIVE_NAME}.sha256"
    checksum_partial = output_dir / f"{ARCHIVE_NAME}.sha256.partial"
    for path in (archive_path, partial_path, checksum_path, checksum_partial):
        if path.exists() or path.is_symlink():
            raise ValueError(f"Mevcut dosyanın üzerine yazılmayacak: {path}. Yeni bir --output-dir seçin.")
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_entries: list[dict[str, object]] = []
    start = time.monotonic()
    last_update = start
    owns_partial = False
    owns_checksum_partial = False
    try:
        with zipfile.ZipFile(partial_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
            owns_partial = True
            for index, path in enumerate(files, 1):
                relative = path.relative_to(project_root).as_posix()
                # Hash exactly the bytes placed in the archive, in a single streaming pass.
                digest = hashlib.sha256()
                byte_count = 0
                before = path.stat()
                info = zipfile.ZipInfo.from_file(path, arcname=f"{ARCHIVE_ROOT}/{relative}")
                info.compress_type = zipfile.ZIP_DEFLATED
                with path.open("rb") as source, archive.open(info, "w", force_zip64=True) as target:
                    for chunk in iter(lambda: source.read(CHUNK_SIZE), b""):
                        target.write(chunk)
                        digest.update(chunk)
                        byte_count += len(chunk)
                        now = time.monotonic()
                        if now - last_update >= 10:
                            print(f"Paketleniyor: {index}/{len(files)} dosya ({now - start:.0f} sn)", flush=True)
                            last_update = now
                after = path.stat()
                if byte_count != before.st_size or after.st_size != before.st_size or after.st_mtime_ns != before.st_mtime_ns:
                    raise ValueError(f"Paketleme sırasında kaynak değişti: {relative}; yeniden deneyin.")
                manifest_entries.append({"path": relative, "size": byte_count, "sha256": digest.hexdigest()})
                now = time.monotonic()
                if now - last_update >= 10 or index == len(files):
                    print(f"Paketleniyor: {index}/{len(files)} dosya ({now - start:.0f} sn)", flush=True)
                    last_update = now
            manifest = {
                "format_version": 1,
                "archive_root": ARCHIVE_ROOT,
                "checksum_scope": "All payload files; portable_manifest.json excludes its own checksum.",
                "files": manifest_entries,
            }
            archive.writestr(f"{ARCHIVE_ROOT}/{MANIFEST_FILE}", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        size = partial_path.stat().st_size
        if size >= ASSET_LIMIT:
            raise ValueError("ZIP boyutu 2 GiB sınırına ulaştı; paketi bölmek gerekir.")
        checksum = sha256_file(partial_path)
        with checksum_partial.open("x", encoding="utf-8") as stream:
            owns_checksum_partial = True
            stream.write(f"{checksum}  {ARCHIVE_NAME}\n")
        # Check once more before publishing the completed local artifacts.
        if archive_path.exists() or checksum_path.exists() or archive_path.is_symlink() or checksum_path.is_symlink():
            raise ValueError("Hedef dosya paketleme sırasında oluşturuldu; üzerine yazılmayacak.")
        os.replace(partial_path, archive_path)
        os.replace(checksum_partial, checksum_path)
    except BaseException:
        if owns_partial:
            partial_path.unlink(missing_ok=True)
        if owns_checksum_partial:
            checksum_partial.unlink(missing_ok=True)
        raise
    print(f"ZIP hazır: {archive_path} ({size / 1024**2:.2f} MiB)", flush=True)
    print(f"SHA256: {checksum_path}", flush=True)
    return archive_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Paket planını salt okunur kontrol et (varsayılan)")
    mode.add_argument("--build", action="store_true", help="Taşınabilir ZIP ve SHA256 dosyasını oluştur")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT, help="Paketlenecek proje kökü")
    parser.add_argument("--output-dir", type=Path, help="Çıktı dizini; varsayılan: <proje>/outputs/temp/releases")
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir else project_root / "outputs/temp/releases"
    try:
        errors, local_files, _ = audit_project(project_root)
        if errors:
            raise ValueError("QGIS taşınabilirlik kontrolü başarısız:\n" + "\n".join(errors))
        files = collect_files(project_root, output_dir)
        omitted = local_files - set(files)
        if omitted:
            raise ValueError("QGIS kaynakları paket planında eksik:\n" + "\n".join(path.relative_to(project_root).as_posix() for path in sorted(omitted)))
        for path in files:
            if is_lfs_pointer(path):
                raise ValueError(f"Git LFS işaretçisi paketlenemez; gerçek veriyi indirin: {path.relative_to(project_root)}")
        total = sum(path.stat().st_size for path in files)
        print(f"Paket planı: {len(files)} dosya, {total / 1024**2:.2f} MiB sıkıştırılmamış veri.", flush=True)
        print(f"Arşiv kökü: {ARCHIVE_ROOT}/; {len(local_files)} QGIS yerel kaynağı dahil.", flush=True)
        print("Yerel teknik paket; kamuya dağıtım durumu için PUBLICATION_STATUS.md dosyasını inceleyin.", flush=True)
        if args.build:
            build_archive(project_root, files, output_dir)
        else:
            print("Salt okunur kontrol tamamlandı. Paket oluşturmak için --build kullanın.")
        return 0
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as error:
        print(f"HATA: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
