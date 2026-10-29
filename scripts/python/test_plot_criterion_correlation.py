#!/usr/bin/env python3
"""Small real-render, tampering and read-only figure provenance tests."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True

from PIL import Image
import generate_correlation_analysis as correlation
import plot_criterion_correlation as plotting


def snapshot(directory):
    return {path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in directory.rglob("*") if path.is_file()}


class CorrelationFigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # One genuine render serves all small copied fixtures. Source data and
        # Matplotlib's temporary font cache remain outside the project.
        cls.shared_temporary = tempfile.TemporaryDirectory(prefix="correlation-figure-tests-")
        cls.addClassCleanup(cls.shared_temporary.cleanup)
        cls.shared = Path(cls.shared_temporary.name)
        cls.shared_sources = cls.shared / "sources"
        cls.shared_figures = cls.shared / "figures"
        analysis = correlation.compute_correlation(
            {"a": [0, .25, .5, .75], "b": [1, .5, 0, .5], "c": [0, 0, .25, .75]},
            ["a", "b", "c"], {"a": "Ölçüt A", "b": "Ölçüt B", "c": "Ölçüt C"},
        )
        analysis["metadata"] = {"baseline_id": "tiny-figure-test-v1", "aoi_rule": "template_equals_1"}
        correlation.write_outputs(analysis, cls.shared_sources)
        cls.source_before = snapshot(cls.shared_sources)
        plotting.generate_figure(plotting.read_sources(cls.shared_sources), cls.shared_figures)
        cls.source_after = snapshot(cls.shared_sources)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="correlation-figure-case-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.sources = self.root / "sources"
        self.figures = self.root / "figures"
        shutil.copytree(self.shared_sources, self.sources)
        shutil.copytree(self.shared_figures, self.figures)
        self.matrix = self.sources / correlation.MATRIX_FILE
        self.statistics = self.sources / correlation.STATISTICS_FILE
        self.matrix_original = self.matrix.read_bytes()
        self.statistics_original = self.statistics.read_bytes()

    def refresh_source_hashes(self):
        path = self.sources / correlation.MANIFEST_FILE
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["outputs"] = [plotting.file_record(self.sources / name)
                               for name in (correlation.MATRIX_FILE, correlation.STATISTICS_FILE)]
        path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def read_csv(path):
        with path.open(encoding="utf-8", newline="") as stream:
            return list(csv.reader(stream))

    @staticmethod
    def write_csv(path, rows):
        with path.open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream, lineterminator="\n").writerows(rows)

    def test_real_render_png_pdf_and_saved_manifest_roundtrip(self):
        self.assertEqual(self.source_before, self.source_after)
        with Image.open(self.figures / plotting.PNG_FILE) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (3000, 2600))
            image.verify()
        self.assertTrue((self.figures / plotting.PDF_FILE).read_bytes().startswith(b"%PDF-"))
        source = plotting.read_sources(self.sources)
        result = plotting.check_saved_figure(source, self.figures)
        self.assertTrue(result["passed"])
        self.assertEqual(result["checked_files"], 3)
        saved = json.loads((self.figures / plotting.FIGURE_MANIFEST).read_text(encoding="utf-8"))
        self.assertEqual(saved["sources"], source["sources"])
        self.assertEqual(saved["baseline_id"], "tiny-figure-test-v1")
        self.assertEqual(saved["aoi_cells"], 4)
        self.assertEqual(saved["criterion_ids"], ["a", "b", "c"])

    def test_source_csv_checksum_change_rejected(self):
        self.matrix.write_bytes(self.matrix_original + b"\n")
        with self.assertRaisesRegex(ValueError, "Source checksum/size mismatch"):
            plotting.read_sources(self.sources)

    def test_rehashed_matrix_labels_still_rejected(self):
        for target, index in ((0, 1), (1, 0)):
            with self.subTest(target=target, index=index):
                self.matrix.write_bytes(self.matrix_original)
                rows = self.read_csv(self.matrix)
                rows[target][index] = "wrong_criterion"
                self.write_csv(self.matrix, rows)
                self.refresh_source_hashes()
                with self.assertRaisesRegex(ValueError, "columns|criterion order"):
                    plotting.read_sources(self.sources)

    def test_rehashed_numeric_shape_and_diagonal_corruption_rejected(self):
        cases = {
            "missing_column": lambda rows: rows[1].pop(),
            "missing_row": lambda rows: rows.pop(),
            "nonnumeric": lambda rows: rows[1].__setitem__(2, "not-a-number"),
            "nonfinite": lambda rows: rows[1].__setitem__(2, "nan"),
            "diagonal": lambda rows: rows[1].__setitem__(1, ".8"),
            "asymmetric": lambda rows: rows[1].__setitem__(2, ".123"),
        }
        for name, corrupt in cases.items():
            with self.subTest(case=name):
                self.matrix.write_bytes(self.matrix_original)
                rows = self.read_csv(self.matrix)
                corrupt(rows)
                self.write_csv(self.matrix, rows)
                self.refresh_source_hashes()
                with self.assertRaises(ValueError):
                    plotting.read_sources(self.sources)

    def test_rehashed_statistics_counts_and_display_names_rejected(self):
        cases = {"aoi_cell_count": "3", "finite_count": "3",
                 "nonfinite_count": "1", "nodata_count": "1", "display_name_tr": "Yanlış ad"}
        for column, invalid in cases.items():
            with self.subTest(column=column):
                self.statistics.write_bytes(self.statistics_original)
                rows = self.read_csv(self.statistics)
                rows[1][rows[0].index(column)] = invalid
                self.write_csv(self.statistics, rows)
                self.refresh_source_hashes()
                with self.assertRaisesRegex(ValueError, "counts|invalid AOI|display names"):
                    plotting.read_sources(self.sources)

    def test_saved_png_or_pdf_hash_change_rejected(self):
        sources = plotting.read_sources(self.sources)
        for name in (plotting.PNG_FILE, plotting.PDF_FILE):
            path = self.figures / name
            original = path.read_bytes()
            with self.subTest(name=name):
                try:
                    path.write_bytes(original + b"altered")
                    with self.assertRaisesRegex(ValueError, re.escape(name)):
                        plotting.check_saved_figure(sources, self.figures)
                finally:
                    path.write_bytes(original)

    def test_valid_rehashed_source_change_invalidates_saved_figure(self):
        rows = self.read_csv(self.matrix)
        rows[1][2] = rows[2][1] = ".123"
        self.write_csv(self.matrix, rows)
        self.refresh_source_hashes()
        changed = plotting.read_sources(self.sources)
        with self.assertRaisesRegex(ValueError, "different source artifacts"):
            plotting.check_saved_figure(changed, self.figures)

    def test_saved_figure_manifest_identity_and_render_contract_rejected(self):
        sources = plotting.read_sources(self.sources)
        path = self.figures / plotting.FIGURE_MANIFEST
        original = json.loads(path.read_text(encoding="utf-8"))
        cases = {"baseline_id": "wrong-v2", "criterion_ids": ["c", "b", "a"],
                 "aoi_cells": 3, "color_limits": [0, 1], "annotation_decimals": 1}
        for field, invalid in cases.items():
            with self.subTest(field=field):
                changed = dict(original)
                changed[field] = invalid
                path.write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
                with self.assertRaises(ValueError):
                    plotting.check_saved_figure(sources, self.figures)

    def test_nonempty_target_is_never_overwritten(self):
        before = snapshot(self.figures)
        with self.assertRaisesRegex(ValueError, "never overwritten"):
            plotting.generate_figure(plotting.read_sources(self.sources), self.figures)
        self.assertEqual(snapshot(self.figures), before)

    def test_check_cli_succeeds_with_matplotlib_import_blocked_and_no_writes(self):
        before = snapshot(self.root)
        # A fresh interpreter proves --check does not rely on an earlier
        # Matplotlib import or on the font cache created by the smoke render.
        bootstrap = """
import importlib.abc
import sys
from pathlib import Path
class BlockMatplotlib(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'matplotlib' or fullname.startswith('matplotlib.'):
            raise AssertionError('--check imported Matplotlib')
sys.meta_path.insert(0, BlockMatplotlib())
sys.path.insert(0, sys.argv[1])
import plot_criterion_correlation as plotting
sys.argv = ['plot_criterion_correlation.py', '--check', '--source-dir', sys.argv[2], '--output-dir', sys.argv[3], '--json']
result = plotting.main()
assert not any(name == 'matplotlib' or name.startswith('matplotlib.') for name in sys.modules)
raise SystemExit(result)
"""
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["MPLCONFIGDIR"] = str(self.root / "must-not-create-font-cache")
        completed = subprocess.run(
            [sys.executable, "-c", bootstrap, str(Path(plotting.__file__).parent),
             str(self.sources), str(self.figures)],
            capture_output=True, text=True, cwd=self.root, env=environment, timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["passed"])
        self.assertFalse(Path(environment["MPLCONFIGDIR"]).exists())
        self.assertEqual(snapshot(self.root), before)


if __name__ == "__main__":
    unittest.main()
