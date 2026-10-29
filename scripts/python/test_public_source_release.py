"""Publication boundaries, byte identity and deterministic source packaging."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import build_public_source_release as release


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
                     "docs/new\nline.md"]
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


if __name__ == "__main__":
    unittest.main()
