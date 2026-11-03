"""Publication boundaries, byte identity and deterministic source packaging."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import zlib

import build_public_source_release as release

MAP = "outputs/maps/png/01_ornek_harita.png"
# The 13 map PNGs exported before attribution was added (Author "MacAir" or no metadata).
# They must never be pinned for publication.
LEGACY_UNATTRIBUTED_SHA256 = {
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
}


def chunk(kind, body):
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))


def png(texts=(("Author", "Enes Göker"),), extra=()):
    """Smallest valid 1x1 grey PNG with QGIS-like tEXt chunks."""
    data = release.PNG_SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0))
    data += b"".join(chunk(b"tEXt", key.encode("latin-1") + b"\x00" + value.encode("latin-1"))
                     for key, value in texts)
    data += b"".join(chunk(kind, body) for kind, body in extra)
    return data + chunk(b"IDAT", zlib.compress(b"\x00\x00")) + chunk(b"IEND", b"")


class PublicSourceReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        # macOS spells its temporary root through the /var system symlink.
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / "project"
        self.root.mkdir()
        self.write("README.md", b"Public source\n")
        self.write("scripts/example.py", b"print('sample')\n")
        self.config = {"format_version": 1, "archive_root": release.ARCHIVE_ROOT,
                       "files": ["README.md", "scripts/example.py"]}

    def write(self, path, data):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target

    def test_unlisted_files_and_git_history_are_never_copied(self):
        for path in [".git/config", "docs/unreviewed.md", "outputs/report/private.pdf", "data/raw/secret.csv"]:
            self.write(path, b"PRIVATE_MUST_STAY_LOCAL")
        files = release.collect_files(self.root, self.config)
        archive_path = release.build_release(self.root, files, self.base / "out")
        with zipfile.ZipFile(archive_path) as archive:
            self.assertEqual(set(archive.namelist()), {
                f"{release.ARCHIVE_ROOT}/README.md", f"{release.ARCHIVE_ROOT}/scripts/example.py",
                f"{release.ARCHIVE_ROOT}/{release.MANIFEST_NAME}"})
            self.assertFalse(any(b"PRIVATE_MUST_STAY_LOCAL" in archive.read(name) for name in archive.namelist()))

    def test_rejects_traversal_hidden_private_binary_and_case_collision(self):
        bad_paths = ["../outside.md", "/tmp/outside.md", "docs/../README.md", "docs\\secret.md",
                     ".git/config", "docs/AGENTS.md", "outputs/report/a11y_report.json",
                     "docs/portfolio_roadmap.md", "docs/readme_stage8_summary.md", "data/raw/source.csv",
                     "outputs/maps/map.png", "docs/private.pdf", "docs/CON.md", "docs/file.md ",
                     "docs/new\nline.md", "AGENTS.md", "private/notes.md", "private/v0_1_1/plan.md",
                     "archive/drive_manifests/manifest.json", "config/carto_basemap.key", "scripts/.env",
                     "docs/service.pem"]
        for path in bad_paths:
            with self.subTest(path=path):
                config = dict(self.config, files=[path])
                with self.assertRaises(ValueError):
                    release.collect_files(self.root, config)
        config = dict(self.config, files=["README.md", {"source": "README.md", "path": "readme.MD"}])
        with self.assertRaises(ValueError):
            release.collect_files(self.root, config)

    def test_rejects_symlink_file_and_parent(self):
        outside = self.base / "outside.md"
        outside.write_text("private")
        (self.root / "docs").symlink_to(self.base, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            release.collect_files(self.root, dict(self.config, files=["docs/outside.md"]))
        (self.root / "README.md").unlink()
        (self.root / "README.md").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            release.collect_files(self.root, self.config)

    def test_output_must_be_empty_external_and_not_symlinked(self):
        files = release.collect_files(self.root, self.config)
        output = self.base / "out"
        output.mkdir()
        sentinel = output / "keep"
        sentinel.write_text("existing")
        for folder in [output, self.root / "export", self.base]:
            with self.subTest(folder=folder), self.assertRaises(ValueError):
                release.build_release(self.root, files, folder)
        self.assertEqual(sentinel.read_text(), "existing")
        alias = self.base / "alias"
        alias.symlink_to(output, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            release.build_release(self.root, files, alias / "nested")

    def test_manifest_tree_archive_and_checksum_are_byte_identical_and_deterministic(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        files = release.collect_files(self.root, self.config)
        first = release.build_release(self.root, files, self.base / "one")
        # Source mtimes and order have no effect on the generated package.
        (self.root / "README.md").touch()
        second = release.build_release(self.root, release.collect_files(self.root, dict(
            self.config, files=list(reversed(self.config["files"])))), self.base / "two")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        expected_sha = hashlib.sha256(first.read_bytes()).hexdigest()
        self.assertEqual((first.parent / (release.ARCHIVE_NAME + ".sha256")).read_text(),
                         f"{expected_sha}  {release.ARCHIVE_NAME}\n")
        tree = first.parent / release.ARCHIVE_ROOT
        manifest = json.loads((tree / release.MANIFEST_NAME).read_text())
        with zipfile.ZipFile(first) as archive:
            for entry in manifest["files"]:
                data = (tree / entry["path"]).read_bytes()
                self.assertEqual(data, archive.read(f"{release.ARCHIVE_ROOT}/{entry['path']}"))
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])
                self.assertEqual(len(data), entry["size"])
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_concurrent_tree_or_archive_creation_is_preserved_on_failure(self):
        files = release.collect_files(self.root, self.config)
        output = self.base / "tree_race"
        tree = output / release.ARCHIVE_ROOT
        original_mkdir = Path.mkdir

        def competing_tree(path, *args, **kwargs):
            if path == tree:
                original_mkdir(path)
                (path / "keep").write_bytes(b"concurrent tree")
                raise FileExistsError("A concurrent process created the tree")
            return original_mkdir(path, *args, **kwargs)

        with patch.object(Path, "mkdir", competing_tree), self.assertRaises(FileExistsError):
            release.build_release(self.root, files, output)
        self.assertEqual((tree / "keep").read_bytes(), b"concurrent tree")

        output = self.base / "archive_race"
        archive_path = output / release.ARCHIVE_NAME
        original_open = Path.open

        def competing_archive(path, mode="r", *args, **kwargs):
            if path == archive_path and mode == "xb":
                with original_open(path, "wb") as stream:
                    stream.write(b"concurrent archive")
                raise FileExistsError("A concurrent process created the archive")
            return original_open(path, mode, *args, **kwargs)

        with patch.object(Path, "open", competing_archive), self.assertRaises(FileExistsError):
            release.build_release(self.root, files, output)
        self.assertEqual(archive_path.read_bytes(), b"concurrent archive")
        self.assertFalse((output / release.ARCHIVE_ROOT).exists())

    def test_data_scaffold_is_empty_and_aggregate_inclusion_is_explicit(self):
        self.write("data/raw/.gitkeep", b"")
        self.write("outputs/tables/summary.csv", b"class,area\n1,2\n")
        config = dict(self.config, files=["data/raw/.gitkeep", "outputs/tables/summary.csv"])
        self.assertEqual(len(release.collect_files(self.root, config)), 2)
        self.write("data/raw/.gitkeep", b"hidden data")
        with self.assertRaisesRegex(ValueError, "empty"):
            release.collect_files(self.root, config)
        with self.assertRaisesRegex(ValueError, "remapped"):
            release.collect_files(self.root, dict(self.config, files=[
                {"source": "README.md", "path": "data/raw/.gitkeep"}]))

    def test_default_check_is_read_only_and_build_requires_explicit_output(self):
        config_path = self.root / "config/public_source_release_v1.json"
        self.write(config_path.relative_to(self.root), json.dumps(self.config).encode("utf-8"))
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(release.main(["--project-root", str(self.root)]), 0)
        self.assertEqual(release.main(["--build", "--project-root", str(self.root)]), 1)
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_source_change_after_validation_is_rejected_without_output(self):
        files = release.collect_files(self.root, self.config)
        self.write("README.md", b"changed\n")
        output = self.base / "out"
        with self.assertRaisesRegex(ValueError, "changed"):
            release.build_release(self.root, files, output)
        self.assertFalse(output.exists())

    def test_output_metadata_is_allowed_without_visual_or_report_payloads(self):
        names = ["outputs/maps/README.md", "outputs/maps/map_export_manifest.json",
                 "outputs/atlas/README.md", "outputs/report/public_report_manifest.json",
                 "outputs/figures/criterion_correlation_v1/figure_manifest.json"]
        for name in names:
            self.write(name, b"{}\n")
        self.assertEqual(len(release.collect_files(self.root, dict(self.config, files=names))), len(names))
        self.write("outputs/report/a11y_report.json", b"{}\n")
        with self.assertRaises(ValueError):
            release.collect_files(self.root, dict(self.config, files=["outputs/report/a11y_report.json"]))

    def test_qgz_rejects_unpinned_extra_members_and_mismatched_project(self):
        qgs = b"<qgis/>\n"
        self.write(release.QGS_NAME, qgs)
        qgz = self.root / release.QGZ_NAME
        with zipfile.ZipFile(qgz, "w") as archive:
            archive.writestr(Path(release.QGS_NAME).name, qgs)
        config = dict(self.config, files=[release.QGS_NAME, release.QGZ_NAME],
                      qgz_members={Path(release.QGS_NAME).name: release.digest(qgs)})
        self.assertEqual(len(release.collect_files(self.root, config)), 2)
        with zipfile.ZipFile(qgz, "a") as archive:
            archive.writestr("private_attachment.db", b"private")
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            release.collect_files(self.root, config)
        with zipfile.ZipFile(qgz, "w") as archive:
            archive.writestr(Path(release.QGS_NAME).name, b"<other/>\n")
        config["qgz_members"][Path(release.QGS_NAME).name] = release.digest(b"<other/>\n")
        with self.assertRaisesRegex(ValueError, "differ"):
            release.collect_files(self.root, config)


    def map_project(self, data=None, recorded=None, stems=("01_ornek_harita",)):
        data = png() if data is None else data
        self.write(MAP, data)
        sha = release.digest(data)
        self.write(release.MAP_EXPORT_MANIFEST, json.dumps(
            {"files": [{"path": MAP, "sha256": recorded or sha}]}).encode("utf-8"))
        self.write(release.MAP_LAYOUTS, json.dumps(
            {"layouts": [{"output_stem": stem} for stem in stems]}).encode("utf-8"))
        return dict(self.config, files=self.config["files"] + [MAP], map_images={MAP: sha})

    def test_n01_pinned_attributed_map_png_is_accepted_as_0644_binary(self):
        config = self.map_project()
        entry = {item.path: item for item in release.collect_files(self.root, config)}[MAP]
        self.assertEqual((entry.data, entry.mode), (png(), 0o644))
        archive_path = release.build_release(self.root, release.collect_files(self.root, config), self.base / "out")
        with zipfile.ZipFile(archive_path) as archive:
            self.assertEqual(archive.read(f"{release.ARCHIVE_ROOT}/{MAP}"), png())

    def test_n02_unpinned_map_png_is_rejected(self):
        config = self.map_project()
        self.write("outputs/maps/png/99_x.png", png())
        config["files"].append("outputs/maps/png/99_x.png")
        with self.assertRaisesRegex(ValueError, "not pinned"):
            release.collect_files(self.root, config)

    def test_n03_pinned_stem_with_other_suffix_is_rejected(self):
        for name in ["01_ornek_harita.tif", "01_ornek_harita.gpkg", "01_ornek_harita.pdf",
                     "01_ornek_harita.jpg", "01_ornek_harita.PNG", "01_ornek_harita.png.aux.xml"]:
            with self.subTest(name=name):
                path = f"outputs/maps/png/{name}"
                self.write(path, png())
                config = dict(self.config, files=self.config["files"] + [path], map_images={})
                with self.assertRaises(ValueError):
                    release.collect_files(self.root, config)

    def test_n04_data_suffixes_fail_with_data_message_everywhere(self):
        for path in ["data/processed/analysis/x.tif", "data/processed/admin/x.gpkg",
                     "outputs/maps/png/x.gpkg", "outputs/x.geojson", "outputs/maps/png/x.vrt",
                     "docs/x.zip", "outputs/tables/x.aux.xml", "scripts/x.TIF"]:
            with self.subTest(path=path):
                self.write(path, b"data")
                with self.assertRaisesRegex(ValueError, "Raw/derived data"):
                    release.collect_files(self.root, dict(self.config, files=[path]))

    def test_n05_geopackage_or_tiff_bytes_named_png_are_rejected(self):
        for data in [b"SQLite format 3\x00" + bytes(100), b"II*\x00" + bytes(100)]:
            with self.subTest(data=data[:4]):
                config = self.map_project(data)
                with self.assertRaisesRegex(ValueError, "not a PNG"):
                    release.collect_files(self.root, config)

    def test_n06_single_byte_change_after_pinning_is_rejected(self):
        config = self.map_project()
        changed = bytearray(png())
        changed[-20] ^= 1
        self.write(MAP, bytes(changed))
        with self.assertRaises(ValueError):
            release.collect_files(self.root, config)
        # A valid PNG with different bytes still fails on the pin.
        other = png(extra=((b"pHYs", struct.pack(">IIB", 11811, 11811, 1)),))
        self.write(MAP, other)
        self.write(release.MAP_EXPORT_MANIFEST, json.dumps(
            {"files": [{"path": MAP, "sha256": release.digest(other)}]}).encode("utf-8"))
        with self.assertRaisesRegex(ValueError, "pinned SHA-256"):
            release.collect_files(self.root, config)

    def test_n07_pin_must_match_the_map_export_manifest(self):
        config = self.map_project(recorded="0" * 64)
        with self.assertRaisesRegex(ValueError, "map_export_manifest"):
            release.collect_files(self.root, config)
        config = self.map_project(stems=("02_baska",))
        with self.assertRaisesRegex(ValueError, "no layout"):
            release.collect_files(self.root, config)

    def test_n08_truncated_or_text_png_is_rejected(self):
        for data in [png()[:-12], png() + b"trailing", b"not an image\n"]:
            with self.subTest(data=data[-8:]):
                config = self.map_project(data)
                with self.assertRaises(ValueError):
                    release.collect_files(self.root, config)

    def test_n09_png_text_outside_the_exact_allowlist_and_exif_are_rejected(self):
        itxt = b"Author\x00\x00\x00\x00\x00" + "MacAir".encode("utf-8")
        cases = {"other author": png(texts=(("Author", "MacAir"),)),
                 "two authors": png(texts=(("Author", "Enes Göker"), ("Author", "Enes Göker"))),
                 "case variant": png(texts=(("Author", "enes göker"),)),
                 "trailing space": png(texts=(("Author", "Enes Göker "),)),
                 "allowed author plus title": png(texts=(("Author", "Enes Göker"), ("Title", "x"))),
                 "QGIS GUI creator": png(texts=(("Author", "Enes Göker"), ("Creator", "QGIS 3.44.15-Solothurn"))),
                 "unknown key": png(texts=(("Comment", "x"),)),
                 "iTXt author": png(texts=(), extra=((b"iTXt", itxt),))}
        for case, data in cases.items():
            with self.subTest(case=case):
                config = self.map_project(data)
                with self.assertRaisesRegex(ValueError, "PNG text chunk not allowed"):
                    release.collect_files(self.root, config)
        config = self.map_project(png(extra=((b"eXIf", b"MM\x00*"),)))
        with self.assertRaisesRegex(ValueError, "PNG chunk not allowed in a map image: eXIf"):
            release.collect_files(self.root, config)

    def test_map_png_without_text_or_with_only_the_project_author_is_accepted(self):
        itxt = b"Author\x00\x00\x00\x00\x00" + "Enes Göker".encode("utf-8")
        for data in [png(texts=()), png(), png(texts=(), extra=((b"iTXt", itxt),))]:
            with self.subTest(data=data[33:60]):
                config = self.map_project(data)
                self.assertIn(MAP, {entry.path for entry in release.collect_files(self.root, config)})

    def test_n10_map_png_cannot_be_remapped(self):
        config = self.map_project()
        config["files"][-1] = {"source": MAP, "path": "outputs/maps/png/02_y.png"}
        config["map_images"] = {"outputs/maps/png/02_y.png": release.digest(png())}
        with self.assertRaisesRegex(ValueError, "remapped"):
            release.collect_files(self.root, config)

    def test_n11_case_variants_of_map_names_are_rejected(self):
        config = self.map_project()
        self.write("outputs/maps/png/01_ORNEK_harita.png", png())
        config["files"].append("outputs/maps/png/01_ORNEK_harita.png")
        with self.assertRaisesRegex(ValueError, "outside the public"):
            release.collect_files(self.root, config)

    def test_n12_symlinked_map_png_or_parent_is_rejected(self):
        config = self.map_project()
        outside = self.base / "outside.png"
        outside.write_bytes(png())
        (self.root / MAP).unlink()
        (self.root / MAP).symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            release.collect_files(self.root, config)
        (self.root / MAP).unlink()
        (self.root / "outputs/maps/png").rmdir()
        (self.root / "outputs/maps/png").symlink_to(self.base, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            release.collect_files(self.root, config)

    def test_n13_pins_and_selected_files_must_match_both_ways(self):
        config = self.map_project()
        with self.assertRaisesRegex(ValueError, "must match exactly"):
            release.collect_files(self.root, dict(config, files=self.config["files"]))
        with self.assertRaisesRegex(ValueError, "not pinned"):
            release.collect_files(self.root, dict(config, map_images={}))
        with self.assertRaisesRegex(ValueError, "map_images must map"):
            release.collect_files(self.root, dict(config, map_images={"docs/x.png": "0" * 64}))

    def test_n14_map_png_outside_the_png_folder_is_rejected(self):
        for path in ["outputs/maps/map.png", "outputs/maps/pdf/01_ornek_harita.png",
                     "outputs/figures/scenario_agreement_v1/x.png", "docs/01_ornek_harita.png"]:
            with self.subTest(path=path):
                self.write(path, png())
                with self.assertRaises(ValueError):
                    release.collect_files(self.root, dict(self.config, files=[path], map_images={}))

    def test_legacy_unattributed_map_pngs_are_not_pinned_and_cannot_be_selected(self):
        config = json.loads((release.PROJECT_ROOT / "config/public_source_release_v1.json").read_text(encoding="utf-8"))
        self.assertTrue(isinstance(config.get("map_images"), dict))
        self.assertFalse(LEGACY_UNATTRIBUTED_SHA256 & set(config["map_images"].values()))
        for path in sorted((release.PROJECT_ROOT / "outputs/maps/png").glob("*.png")):
            if release.digest(path.read_bytes()) not in LEGACY_UNATTRIBUTED_SHA256:
                continue
            name = path.relative_to(release.PROJECT_ROOT).as_posix()
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "not pinned"):
                release.collect_files(release.PROJECT_ROOT, dict(config, files=config["files"] + [name]))
            # Even if pinned, every legacy export fails on its SHA-256 before its metadata.
            pinned = dict(config, files=config["files"] + [name], map_images={name: release.digest(path.read_bytes())})
            with self.subTest(name=name, pinned=True), self.assertRaisesRegex(ValueError, "pre-v0.2 export"):
                release.collect_files(release.PROJECT_ROOT, pinned)

    def test_n15_all_13_legacy_sha256_values_are_rejected_with_a_reason(self):
        self.assertEqual(release.LEGACY_UNATTRIBUTED_MAP_SHA256, LEGACY_UNATTRIBUTED_SHA256)
        data = png(texts=())
        config = self.map_project(data)
        with patch.object(release, "LEGACY_UNATTRIBUTED_MAP_SHA256", frozenset({release.digest(data)})):
            with self.assertRaisesRegex(ValueError, "pre-v0.2 export without the visible attribution band"):
                release.collect_files(self.root, config)
            with self.assertRaisesRegex(ValueError, "pre-v0.2 export"):
                release.validate_map_png(MAP, data)
        self.assertIn(MAP, {entry.path for entry in release.collect_files(self.root, config)})

    def test_built_tree_contains_no_data_suffix_and_only_pinned_binaries(self):
        config = self.map_project()
        archive_path = release.build_release(self.root, release.collect_files(self.root, config), self.base / "out")
        tree = archive_path.parent / release.ARCHIVE_ROOT
        names = [path.relative_to(tree).as_posix() for path in tree.rglob("*") if path.is_file()]
        self.assertFalse([name for name in names if name.casefold().endswith(release.DATA_SUFFIXES)])
        binaries = [name for name in names if b"\x00" in (tree / name).read_bytes()]
        self.assertEqual(binaries, [MAP])


if __name__ == "__main__":
    unittest.main()
