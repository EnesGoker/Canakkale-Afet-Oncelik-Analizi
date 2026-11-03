#!/usr/bin/env python3
"""Validate or build the explicitly selected public source release.

The default --check is read-only. --build requires an empty directory outside
the project and writes a clean tree, deterministic ZIP and SHA-256 checksum.
Only exact allowlisted paths are copied; Git history is never copied. Selection
is a publication decision, not a blanket licence for unselected local files.
The only binary payloads are the QGZ template and map PNGs pinned by SHA-256 in
map_images; raw or derived data files are never publishable.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import struct
import sys
import unicodedata
import zipfile
import zlib

sys.dont_write_bytecode = True
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = "canakkale-afet-oncelik-analizi"
MANIFEST_NAME = "public_source_manifest.json"
ARCHIVE_NAME = f"{ARCHIVE_ROOT}-kaynak.zip"
ROOT_NAMES = {"README.md", "README.en.md", "LICENSE", "LICENSE_SCOPE.md",
              "PUBLICATION_STATUS.md", ".gitignore", ".gitattributes", "requirements.txt"}
TEXT_SUFFIXES = {".md", ".py", ".sh", ".json", ".txt", ".tsv", ".csv", ".yml", ".yaml"}
PRIVATE_NAMES = {"AGENTS.md", "portfolio_roadmap.md", "baseline_startup_summary.md",
                 "publication_preparation_summary.md", "dokumantasyon_dil_standardi.md",
                 "a11y_report.json"}
QGS_NAME = "qgis/canakkale_disaster_priority.qgs"
QGZ_NAME = "qgis/canakkale_disaster_priority.qgz"
MAP_EXPORT_MANIFEST = "outputs/maps/map_export_manifest.json"
MAP_LAYOUTS = "config/map_layouts_v1.json"
MAP_PNG_DIR = ("outputs", "maps", "png")
MAP_PNG_NAME = re.compile(r"[0-9]{2}_[a-z0-9_]+\.png")
MAP_AUTHOR = "Enes Göker"
# Exact PNG text allowlist. export_map_layouts.py turns QGIS metadata off, and then
# QGIS/Qt write no text chunk; a QGIS GUI export may carry only the project author.
MAP_TEXT_ALLOWED = {"Author": MAP_AUTHOR}
# Pre-v0.2 map PNGs without the visible attribution band (outputs/maps/png, 01-13).
LEGACY_UNATTRIBUTED_MAP_SHA256 = frozenset({
    "97becadce6f5fbf6ec71670b33ad321a6dbbaa33330118fed35861fbb3cbd440",
    "c757f1f5777eb0c1b3a58e3c695d4fa88662a27c15206a01f7272fbed321aa83",
    "1968265763171d4c9740b11e8355fc54ece40881eedbf736f7b3dbd7e38f2da4",
    "65dbc4bd26cfc429d54578dc4a4469afea9dd7e1632da899be20f6d5b59f0808",
    "e0d2cdce03f26a621d88672607a3265ebfce2cacec0f58cd307a97f4b70391ae",
    "acc3c0b0643deb3149933158159773bca9eeb26a9f1f1430791f907e4fe92087",
    "4b75c3f1af83c8873d9b371bd859cb2b4230dfb13292c594cc2d33eae133413b",
    "7a36a20d3b9635d1cb3e65abb2074c75972a36301cbf26209279c9c4df725c10",
    "895add6a29ed3b4db80acef385b7ce2980a66c7d01bd5f5eff9867154b21af36",
    "8df5a6881fe4ddda1382bacc5db48fea6ca2102a1276f3eb26a2eb2d15c98f20",
    "f528c874ceb2439a7bdfc19b8639027f77c1e8810c67b777555098b1a5d07c26",
    "ba5616e9b8d76e1d11bc6ac72b4305c057d4abe3d6cfa0e8d03d8f9c1731caf5",
    "9aac2d26f98b5a4eace32dac1e250ba53d2f9a23b8013d08488dcdfae6ab3cc6",
})
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_CHUNKS = {b"IHDR", b"PLTE", b"IDAT", b"IEND", b"pHYs", b"sRGB", b"gAMA", b"cHRM",
              b"tRNS", b"bKGD", b"tIME", b"tEXt", b"zTXt", b"iTXt"}
DATA_SUFFIXES = (".tif", ".tiff", ".gpkg", ".gpkg-wal", ".gpkg-shm", ".shp", ".shx", ".dbf", ".prj",
                 ".cpg", ".geojson", ".vrt", ".nc", ".aux.xml", ".ovr", ".zip", ".xlsx")


@dataclass(frozen=True)
class SelectedFile:
    source: Path
    path: str
    data: bytes
    mode: int


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_relative(value: object) -> PurePosixPath:
    if (not isinstance(value, str) or not value or "\\" in value
            or any(ord(character) < 32 or ord(character) == 127 for character in value)):
        raise ValueError("Selection paths must be non-empty POSIX relative paths")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError(f"Unsafe selection path: {value}")
    # Avoid alternate data streams, Windows device names, and checkout aliases.
    for part in path.parts:
        if ":" in part or part.rstrip(" .") != part or re.fullmatch(
                r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part):
            raise ValueError(f"Non-portable selection path: {value}")
    return path


def is_map_png(path: PurePosixPath) -> bool:
    return len(path.parts) == 4 and path.parts[:3] == MAP_PNG_DIR and bool(MAP_PNG_NAME.fullmatch(path.name))


def approved_shape(path: PurePosixPath) -> None:
    value = path.as_posix()
    if path.name.casefold().endswith(DATA_SUFFIXES):
        raise ValueError(f"Raw/derived data is never publishable: {value}")
    if (path.name in PRIVATE_NAMES or re.fullmatch(r".*_stage[0-9]+_summary\.md", path.name)
            or any(part.startswith(".") for part in path.parts
                   if part not in {".github", ".gitignore", ".gitattributes", ".gitkeep"})):
        raise ValueError(f"Private/hidden path is not publishable: {value}")
    if value in ROOT_NAMES or value in {QGS_NAME, QGZ_NAME} or is_map_png(path):
        return
    if path.parts[0] == "data" and path.name == ".gitkeep":
        return
    if path.parts[0] in {"scripts", "docs", "config", ".github"} and path.suffix in TEXT_SUFFIXES:
        return
    if (len(path.parts) > 2 and path.parts[0] == "outputs"
            and path.parts[1] in {"tables", "analysis"} and path.suffix in {".csv", ".md", ".json"}):
        return
    if value in {"outputs/maps/README.md", "outputs/maps/map_export_manifest.json",
                 "outputs/atlas/README.md", "outputs/report/public_report_manifest.json"}:
        return
    if (len(path.parts) == 4 and path.parts[:2] == ("outputs", "figures")
            and path.parts[2] in {"criterion_correlation_v1", "scenario_agreement_v1"}
            and path.name.endswith("_manifest.json")):
        return
    raise ValueError(f"Path is outside the public source/aggregate scope: {value}")


def no_symlinks(path: Path) -> None:
    for current in (path, *path.parents):
        if current.is_symlink():
            raise ValueError(f"Symlink is not allowed: {current.name}")


def png_text(kind: bytes, body: bytes) -> tuple[str, str]:
    key, separator, rest = body.partition(b"\x00")
    if not separator:
        raise ValueError("Malformed PNG text chunk")
    if kind == b"tEXt":
        value = rest.decode("latin-1")
    elif kind == b"zTXt":
        if rest[:1] != b"\x00":
            raise ValueError("Unsupported PNG text compression")
        value = zlib.decompress(rest[1:]).decode("latin-1")
    else:
        flag, method, rest = rest[:1], rest[1:2], rest[2:]
        _language, _, rest = rest.partition(b"\x00")
        _translated, _, text = rest.partition(b"\x00")
        value = (zlib.decompress(text) if flag == b"\x01" and method == b"\x00" else text).decode("utf-8")
    return key.decode("latin-1"), value


def validate_map_png(name: str, data: bytes) -> None:
    if not data.startswith(PNG_SIGNATURE) or data[12:16] != b"IHDR":
        raise ValueError(f"Map image is not a PNG: {name}")
    if digest(data) in LEGACY_UNATTRIBUTED_MAP_SHA256:
        raise ValueError(f"Map PNG is a pre-v0.2 export without the visible attribution band: {name}")
    offset, kinds, texts = len(PNG_SIGNATURE), [], []
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError(f"Truncated PNG chunk: {name}")
        length, kind = struct.unpack(">I4s", data[offset:offset + 8])
        body = data[offset + 8:offset + 8 + length]
        crc = data[offset + 8 + length:offset + 12 + length]
        if len(body) != length or len(crc) != 4 or struct.unpack(">I", crc)[0] != zlib.crc32(kind + body):
            raise ValueError(f"Corrupt PNG chunk: {name}")
        if kind not in PNG_CHUNKS:
            raise ValueError(f"PNG chunk not allowed in a map image: {kind.decode('latin-1')} in {name}")
        if kind in {b"tEXt", b"zTXt", b"iTXt"}:
            key, value = png_text(kind, body)
            if MAP_TEXT_ALLOWED.get(key) != value or key in texts:
                raise ValueError(f"PNG text chunk not allowed: only {MAP_TEXT_ALLOWED} once, in {name}")
            texts.append(key)
        kinds.append(kind)
        offset += 12 + length
        if kind == b"IEND":
            break
    if not kinds or kinds[-1] != b"IEND" or offset != len(data):
        raise ValueError(f"PNG must end with IEND: {name}")


def check_map_images(project_root: Path, pinned: dict, paths: dict[str, bytes]) -> None:
    selected = {name for name in paths if is_map_png(PurePosixPath(name))}
    if set(pinned) != selected:
        raise ValueError("map_images pins and selected map PNG files must match exactly")
    if not selected:
        return
    exports = json.loads((project_root / MAP_EXPORT_MANIFEST).read_text(encoding="utf-8"))
    recorded = {entry["path"]: entry["sha256"] for entry in exports["files"]}
    layouts = json.loads((project_root / MAP_LAYOUTS).read_text(encoding="utf-8"))
    stems = {layout["output_stem"] for layout in layouts["layouts"]}
    for name in sorted(selected):
        data = paths[name]
        validate_map_png(name, data)
        if digest(data) != pinned[name]:
            raise ValueError(f"Map PNG differs from its pinned SHA-256: {name}")
        if recorded.get(name) != pinned[name]:
            raise ValueError(f"Map PNG pin differs from {MAP_EXPORT_MANIFEST}: {name}")
        if PurePosixPath(name).stem not in stems:
            raise ValueError(f"Map PNG has no layout in {MAP_LAYOUTS}: {name}")


def collect_files(project_root: Path, config: dict) -> list[SelectedFile]:
    if not isinstance(config, dict) or config.get("format_version") != 1 or config.get("archive_root") != ARCHIVE_ROOT:
        raise ValueError("Unsupported public source selection format/root")
    rows = config.get("files")
    if not isinstance(rows, list) or not rows:
        raise ValueError("An explicit non-empty files allowlist is required")
    pinned = config.get("map_images", {})
    if not isinstance(pinned, dict) or not all(isinstance(name, str) and is_map_png(safe_relative(name))
                                               and isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
                                               for name, value in pinned.items()):
        raise ValueError("map_images must map map PNG paths to SHA-256 values")
    selected = []
    destinations = set()
    for row in rows:
        if isinstance(row, str):
            source_name = destination_name = row
        elif isinstance(row, dict) and set(row) == {"source", "path"}:
            source_name, destination_name = row["source"], row["path"]
        else:
            raise ValueError("Each selection entry must be a path or exact source/path mapping")
        source_relative = safe_relative(source_name)
        destination = safe_relative(destination_name)
        approved_shape(source_relative)
        approved_shape(destination)
        if ((source_relative.parts[0] in {"qgis", "data"} or destination.parts[0] in {"qgis", "data"}
             or is_map_png(source_relative) or is_map_png(destination))
                and source_relative != destination):
            raise ValueError("QGIS templates, map images and data scaffolding cannot be remapped")
        normalized = unicodedata.normalize("NFC", destination.as_posix()).casefold()
        if normalized in destinations or normalized == MANIFEST_NAME:
            raise ValueError(f"Duplicate/reserved destination: {destination}")
        destinations.add(normalized)
        source = project_root / source_relative
        no_symlinks(source)
        if not source.is_file():
            raise ValueError(f"Selected file is missing: {source_relative}")
        data = source.read_bytes()
        if source_relative.name == ".gitkeep":
            if data or destination.name != ".gitkeep":
                raise ValueError("Data scaffolding must contain empty .gitkeep files only")
        elif is_map_png(source_relative):
            if source_relative.as_posix() not in pinned:
                raise ValueError(f"Map PNG is not pinned in map_images: {source_relative}")
        elif source_relative.as_posix() != QGZ_NAME:
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ValueError(f"Expected UTF-8 source text: {source_relative}") from error
            if "\x00" in text or text.startswith("version https://git-lfs.github.com/spec/v1\n"):
                raise ValueError(f"Binary content or LFS pointer: {source_relative}")
        mode = 0o755 if destination.suffix in {".sh", ".py"} else 0o644
        selected.append(SelectedFile(source, destination.as_posix(), data, mode))
    paths = {entry.path: entry.data for entry in selected}
    check_map_images(project_root, pinned, paths)
    if QGZ_NAME in paths:
        allowed = config.get("qgz_members")
        if QGS_NAME not in paths or not isinstance(allowed, dict) or not allowed:
            raise ValueError("QGZ requires its QGS pair and pinned embedded member hashes")
        with zipfile.ZipFile(io.BytesIO(paths[QGZ_NAME])) as archive:
            members = archive.infolist()
            if len(members) != len(allowed) or {item.filename for item in members} != set(allowed):
                raise ValueError("Unexpected or duplicate QGZ member")
            for member in members:
                safe_relative(member.filename)
                if "/" in member.filename or Path(member.filename).suffix not in {".qgs", ".db"}:
                    raise ValueError("Unexpected QGZ attachment type")
                if stat.S_ISLNK(member.external_attr >> 16):
                    raise ValueError("QGZ symlink member is not allowed")
                data = archive.read(member)
                if digest(data) != allowed[member.filename]:
                    raise ValueError(f"QGZ member changed: {member.filename}")
            if archive.read(Path(QGS_NAME).name) != paths[QGS_NAME]:
                raise ValueError("Selected QGS and embedded QGS differ")
    return sorted(selected, key=lambda entry: entry.path)


def manifest_bytes(files: list[SelectedFile]) -> bytes:
    manifest = {"format_version": 1, "archive_root": ARCHIVE_ROOT,
                "package_kind": "public-source-and-selected-analytical-summaries",
                "checksum_scope": "All selected payloads; this manifest excludes its own hash.",
                "files": [{"path": entry.path, "size": len(entry.data), "sha256": digest(entry.data),
                           "mode": format(entry.mode, "04o")} for entry in files]}
    return (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def build_release(project_root: Path, files: list[SelectedFile], output_dir: Path) -> Path:
    no_symlinks(output_dir)
    output_dir = output_dir.resolve()
    project_root = project_root.resolve()
    if output_dir.is_relative_to(project_root) or project_root.is_relative_to(output_dir):
        raise ValueError("Output must be outside, and must not contain, the project")
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise ValueError("Output directory must be empty; existing contents are preserved")
    for entry in files:
        no_symlinks(entry.source)
        if entry.source.read_bytes() != entry.data:
            raise ValueError(f"Selected source changed after validation: {entry.path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    tree = output_dir / ARCHIVE_ROOT
    archive_path = output_dir / ARCHIVE_NAME
    checksum_path = output_dir / (ARCHIVE_NAME + ".sha256")
    payloads = [(entry.path, entry.data, entry.mode) for entry in files]
    payloads.append((MANIFEST_NAME, manifest_bytes(files), 0o644))
    owns_tree = owns_archive = owns_checksum = False
    try:
        tree.mkdir()
        owns_tree = True
        with archive_path.open("xb") as archive_stream:
            owns_archive = True
            with zipfile.ZipFile(archive_stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for relative, data, mode in sorted(payloads):
                    target = tree / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("xb") as stream:
                        stream.write(data)
                    target.chmod(mode)
                    info = zipfile.ZipInfo(f"{ARCHIVE_ROOT}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.external_attr = (stat.S_IFREG | mode) << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, data, compresslevel=9)
        with checksum_path.open("x", encoding="utf-8", newline="\n") as stream:
            owns_checksum = True
            stream.write(f"{digest(archive_path.read_bytes())}  {ARCHIVE_NAME}\n")
    except BaseException:
        if owns_tree:
            shutil.rmtree(tree, ignore_errors=True)
        if owns_archive:
            archive_path.unlink(missing_ok=True)
        if owns_checksum:
            checksum_path.unlink(missing_ok=True)
        raise
    return archive_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Read-only selection check (default)")
    mode.add_argument("--build", action="store_true", help="Build clean tree, ZIP and SHA-256 checksum")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--selection-config", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        no_symlinks(args.project_root)
        root = args.project_root.resolve()
        config_path = args.selection_config or root / "config/public_source_release_v1.json"
        no_symlinks(config_path)
        config = json.loads(config_path.read_text(encoding="utf-8"))
        files = collect_files(root, config)
        print(f"Public source selection: {len(files)} files, {sum(len(e.data) for e in files):,} bytes.")
        if args.build:
            if args.output_dir is None:
                raise ValueError("--build requires an explicit --output-dir")
            path = build_release(root, files, args.output_dir)
            print(f"Source ZIP: {path}")
            print(f"SHA-256: {digest(path.read_bytes())}")
        else:
            maps = sum(is_map_png(PurePosixPath(entry.path)) for entry in files)
            print(f"Read-only check passed; no files written. Pinned map PNGs: {maps}; "
                  "no source data or report binaries are selected.")
        return 0
    except (OSError, ValueError, zipfile.BadZipFile, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
