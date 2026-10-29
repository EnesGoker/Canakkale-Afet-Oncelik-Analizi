#!/usr/bin/env python3
"""Regression checks for private content exclusion in local portable archives.

Uses synthetic files in a temporary directory; no project data is changed.
Run: python3 scripts/python/test_release_privacy.py
"""

import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from build_portable_release import ARCHIVE_ROOT, INCLUDE_DIRS, ROOT_FILES, build_archive, collect_files, excluded
from check_portability import MANIFEST_FILE


class ReleasePrivacyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        self.output = self.root / "outputs/temp/releases"
        for directory in INCLUDE_DIRS:
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        for name in ROOT_FILES:
            (self.root / name).write_text("synthetic test fixture\n", encoding="utf-8")
        self.private = (
            "outputs/report/canakkale_disaster_priority_academic_report.pages",
            "outputs/report/canakkale_disaster_priority_academic_report.docx",
            "outputs/report/canakkale_disaster_priority_public_report.pages",
            "outputs/report/unlisted_local_archive.pages",
            "outputs/temp/old-release.zip",
            "data/processed/analysis/archive/old_result.tif",
            "AGENTS.md",
            ".codex/internal/private_notes.md",
            "docs/portfolio_roadmap.md",
            "docs/baseline_startup_summary.md",
            "docs/publication_preparation_summary.md",
            "docs/qa_stage2_summary.md",
            "docs/methodology_stage3_summary.md",
            "docs/correlation_stage4_summary.md",
            "docs/scenario_agreement_stage5_summary.md",
            "docs/map_layout_stage6_summary.md",
            "docs/report_stage7_summary.md",
            "docs/readme_stage8_summary.md",
            "docs/dokumantasyon_dil_standardi.md",
            "docs/release_stage19_summary.md",
        )
        self.public = (
            "outputs/report/canakkale_disaster_priority_public_report.docx",
            "docs/qa/stage3_boundary_findings.md",
            "docs/methodology_notes.md",
            "docs/qa/readme_stage8_summary.md",
        )
        for name in self.private:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"PRIVATE_FIXTURE_MUST_NOT_APPEAR")
        for name in self.public:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"PUBLIC_FIXTURE")
        link_name = "docs/private-report-link.pages"
        (self.root / link_name).symlink_to(self.root / self.private[0])
        self.private += (link_name,)

    def test_archive_keeps_public_report_and_licenses_without_private_payload(self):
        archive_path = build_archive(self.root, collect_files(self.root, self.output), self.output)
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            manifest = json.loads(archive.read(f"{ARCHIVE_ROOT}/{MANIFEST_FILE}"))
            manifest_paths = {entry["path"] for entry in manifest["files"]}
            for name in self.private:
                self.assertNotIn(f"{ARCHIVE_ROOT}/{name}", names)
                self.assertNotIn(name, manifest_paths)
            for name in (*self.public, "README.md", "README.tr.md", "LICENSE", "LICENSE_SCOPE.md", "PUBLICATION_STATUS.md"):
                self.assertIn(f"{ARCHIVE_ROOT}/{name}", names)
                self.assertIn(name, manifest_paths)
            self.assertFalse(any(b"PRIVATE_FIXTURE_MUST_NOT_APPEAR" in archive.read(name) for name in names))
        for name in self.private:
            self.assertEqual((self.root / name).read_bytes(), b"PRIVATE_FIXTURE_MUST_NOT_APPEAR")

    def test_private_paths_are_explicitly_excluded(self):
        for name in self.private:
            with self.subTest(path=name):
                self.assertTrue(excluded(self.root / name, self.root, self.output))
        for name in self.public:
            with self.subTest(path=name):
                self.assertFalse(excluded(self.root / name, self.root, self.output))

    def test_missing_license_prevents_package_selection(self):
        (self.root / "LICENSE").unlink()
        with self.assertRaisesRegex(ValueError, "LICENSE"):
            collect_files(self.root, self.output)

    def test_existing_archive_is_preserved(self):
        files = collect_files(self.root, self.output)
        archive_path = build_archive(self.root, files, self.output)
        original = archive_path.read_bytes()
        with self.assertRaisesRegex(ValueError, "Mevcut dosyanın"):
            build_archive(self.root, files, self.output)
        self.assertEqual(archive_path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
