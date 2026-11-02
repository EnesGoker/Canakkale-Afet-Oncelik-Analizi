#!/usr/bin/env python3
"""Small independent arithmetic, corruption and no-write correlation tests."""

from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True

from tier_support import module_tier

TIER = module_tier(__file__)
if TIER.available:
    import numpy as np
import generate_correlation_analysis as correlation


def fixture_analysis():
    result = correlation.compute_correlation(
        {"a": np.array([0, 1, 2, 3], dtype=np.float32),
         "b": np.array([3, 1, 0, 0], dtype=np.float32),
         "c": np.array([0, 0, 0, 1], dtype=np.float32)},
        ["a", "b", "c"], {"a": "Ölçüt A", "b": "Ölçüt B", "c": "Ölçüt C"},
    )
    result["metadata"] = {"baseline_id": "tiny-test-v1", "baseline_manifest_sha256": "0" * 64, "aoi_rule": "template_equals_1"}
    return result


def directory_snapshot(root):
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()}


@TIER.skip_unless_available
class CorrelationArithmeticTests(unittest.TestCase):
    def test_hand_computed_positive_negative_and_zero(self):
        vectors = {"a": [0, 1, 2], "b": [2, 1, 0], "c": [1, 0, 1]}
        result = correlation.compute_correlation(vectors, ["a", "b", "c"])
        np.testing.assert_allclose(result["correlation"], [[1, -1, 0], [-1, 1, 0], [0, 0, 1]], atol=1e-14, rtol=0)

    def test_independent_numpy_corrcoef_agrees(self):
        source = np.random.default_rng(531).normal(size=(5, 1001))
        ids = [f"c{index}" for index in range(len(source))]
        result = correlation.compute_correlation(dict(zip(ids, source)), ids)
        np.testing.assert_allclose(result["correlation"], np.corrcoef(source), rtol=0, atol=2e-14)

    def test_all_cells_and_zeros_retained(self):
        result = fixture_analysis()
        stats = result["statistics"][2]
        self.assertEqual(result["n_cells"], 4)
        self.assertEqual(stats["zero_count"], 3)
        self.assertEqual(stats["zero_fraction"], .75)
        self.assertEqual(stats["finite_count"], 4)
        self.assertEqual(stats["nodata_count"], 0)
        self.assertAlmostEqual(stats["mean"], .25)
        self.assertAlmostEqual(stats["std_population"], np.sqrt(3 / 16))

    def test_order_and_turkish_names_preserved(self):
        result = correlation.compute_correlation({"b": [3, 1, 0], "a": [0, 1, 2]}, ["a", "b"], {"a": "Ölçüt", "b": "İkinci"})
        self.assertEqual(result["criterion_ids"], ["a", "b"])
        self.assertEqual(result["statistics"][0]["display_name_tr"], "Ölçüt")

    def test_neither_mutates_nor_shares_input_arrays(self):
        a = np.array([0, .2, .8, 1], dtype=np.float32)
        b = a[::-1].copy()
        before = a.copy()
        result = correlation.compute_correlation({"a": a, "b": b}, ["a", "b"])
        np.testing.assert_array_equal(a, before)
        result["correlation"][:] = 0
        np.testing.assert_array_equal(a, before)

    def test_relative_small_sparse_values_remain_valid(self):
        for scale in (1e-8, 1e-200, 1e200):
            result = correlation.compute_correlation({"a": [0, 0, 0, scale], "b": [0, 0, scale, 0]}, ["a", "b"])
            self.assertAlmostEqual(result["correlation"][0, 1], -1 / 3)
            self.assertGreater(result["statistics"][0]["std_population"], 0)

    def test_large_offset_with_resolvable_variation(self):
        a = 1e12 + np.arange(10, dtype=np.float64)
        result = correlation.compute_correlation({"a": a, "b": -a}, ["a", "b"])
        self.assertAlmostEqual(result["correlation"][0, 1], -1)

    def test_intermediate_extreme_magnitudes_do_not_overflow_norm_products(self):
        for scale in (1e-90, 1e90):
            result = correlation.compute_correlation({"a": [0, 0, 0, scale], "b": [0, 0, scale, 0]}, ["a", "b"])
            np.testing.assert_allclose(result["correlation"], [[1, -1 / 3], [-1 / 3, 1]], rtol=0, atol=1e-14)

    def test_million_cell_sparse_repeated_vectors_have_consistent_norms(self):
        a = np.zeros(1000003, dtype=np.float32)
        a[::71] = .25
        b = np.full(len(a), .4, dtype=np.float32)
        b[::137] = .8
        result = correlation.compute_correlation({"a": a, "b": b}, ["a", "b"])
        correlation.validate_correlation(result["correlation"], 2)
        np.testing.assert_allclose(result["correlation"], np.corrcoef([a, b]), rtol=0, atol=1e-12)

    def test_constant_and_nearconstant_rejected(self):
        for values in ([0, 0, 0], [.5, .5, .5], [.5, .5 + np.finfo(float).eps, .5]):
            with self.subTest(values=values), self.assertRaisesRegex(ValueError, "Constant or numerically near-constant"):
                correlation.compute_correlation({"a": values, "b": [0, 1, 2]}, ["a", "b"])

    def test_nan_and_infinity_rejected_without_dropping_cells(self):
        for invalid in (np.nan, np.inf, -np.inf):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "NaN or infinity"):
                correlation.compute_correlation({"a": [0, invalid, 1], "b": [0, 1, 2]}, ["a", "b"])

    def test_missing_extra_duplicate_or_empty_criterion_rejected(self):
        cases = [({"a": [0, 1]}, ["a", "b"]),
                 ({"a": [0, 1], "b": [0, 1], "c": [0, 1]}, ["a", "b"]),
                 ({"a": [0, 1]}, ["a", "a"]),
                 ({"a": [0, 1]}, []),
                 ({"a": [0, 1], "": [0, 1]}, ["a", ""])]
        for vectors, ids in cases:
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                correlation.compute_correlation(vectors, ids)

    def test_bad_shape_empty_single_cell_and_nonreal_rejected(self):
        for values in ([], [1], [[0, 1]], [0, 1, 2, 3], [0j, 1j, 2j], ["0", "1", "2"]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                correlation.compute_correlation({"a": values, "b": [0, 1, 2]}, ["a", "b"])

    def test_missing_display_name_rejected(self):
        with self.assertRaisesRegex(ValueError, "Display names"):
            correlation.compute_correlation({"a": [0, 1], "b": [1, 0]}, ["a", "b"], {"a": "A"})

    def test_invalid_matrix_not_repaired(self):
        matrices = [np.array([[1, 2], [2, 1.]]), np.array([[.9, 0], [0, 1.]]),
                    np.array([[1, .2], [.3, 1.]]), np.array([[1, np.nan], [np.nan, 1.]]), np.eye(3)]
        for matrix in matrices:
            saved = matrix.copy()
            with self.subTest(matrix=matrix), self.assertRaises(ValueError):
                correlation.validate_correlation(matrix, 2)
            np.testing.assert_array_equal(matrix, saved)

    def test_matrix_tolerance_is_explicit(self):
        correlation.validate_correlation(np.array([[1 + 2e-13, .1], [.1, 1.]]), 2)
        with self.assertRaises(ValueError):
            correlation.validate_correlation(np.array([[1 + 2e-11, .1], [.1, 1.]]), 2)


@TIER.skip_unless_available
class CorrelationArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "artifacts"
        self.analysis = fixture_analysis()

    def publish(self):
        correlation.write_outputs(self.analysis, self.output)

    def update_manifest_hash(self, filename):
        path = self.output / correlation.MANIFEST_FILE
        manifest = json.loads(path.read_text(encoding="utf-8"))
        content = (self.output / filename).read_bytes()
        entry = next(row for row in manifest["outputs"] if row["path"] == filename)
        entry.update({"size": len(content), "sha256": hashlib.sha256(content).hexdigest()})
        path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    def test_roundtrip_deterministic_and_unicode(self):
        first = correlation.output_contents(self.analysis)
        self.assertEqual(first, correlation.output_contents(self.analysis))
        self.publish()
        self.assertTrue(correlation.compare_outputs(self.analysis, self.output)["passed"])
        self.assertIn("Ölçüt", (self.output / correlation.STATISTICS_FILE).read_text(encoding="utf-8"))
        manifest = json.loads((self.output / correlation.MANIFEST_FILE).read_text(encoding="utf-8"))
        self.assertFalse(manifest["p_values_computed"])
        self.assertFalse(manifest["weights_modified"])

    def test_float17_roundtrip_preserves_coefficients(self):
        self.publish()
        with (self.output / correlation.MATRIX_FILE).open(encoding="utf-8", newline="") as stream:
            rows = list(csv.reader(stream))
        parsed = np.asarray([[float(cell) for cell in row[1:]] for row in rows[1:]])
        np.testing.assert_array_equal(parsed, self.analysis["correlation"])

    def test_existing_target_or_unrelated_content_never_overwritten(self):
        for existing_file in (correlation.MATRIX_FILE, "unrelated.txt"):
            with self.subTest(existing_file=existing_file):
                self.output.mkdir(exist_ok=True)
                target = self.output / existing_file
                target.write_text("untouched", encoding="utf-8")
                before = directory_snapshot(self.root)
                with self.assertRaisesRegex(ValueError, "empty or new"):
                    self.publish()
                self.assertEqual(directory_snapshot(self.root), before)
                target.unlink()

    def test_existing_empty_directory_allowed(self):
        self.output.mkdir()
        self.publish()
        self.assertEqual(set(path.name for path in self.output.iterdir()), set(correlation.OUTPUT_FILES))

    def test_invalid_analysis_creates_no_directory(self):
        self.analysis["correlation"][0, 1] = np.inf
        with self.assertRaises(ValueError):
            self.publish()
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.iterdir()), [])

    def test_output_symlink_rejected(self):
        other = self.root / "other"
        other.mkdir()
        self.output.symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            self.publish()
        self.assertEqual(list(other.iterdir()), [])

    def test_failed_publication_rolls_back_only_owned_files(self):
        real_link = correlation.os.link
        calls = 0
        def fail_second_link(source, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected publication failure")
            return real_link(source, target)
        with mock.patch.object(correlation.os, "link", side_effect=fail_second_link), self.assertRaises(OSError):
            self.publish()
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.iterdir()), [])

    def test_missing_artifact_or_extra_matrix_row_fails_readonly(self):
        self.publish()
        path = self.output / correlation.MANIFEST_FILE
        saved = path.read_bytes()
        path.unlink()
        before = directory_snapshot(self.root)
        self.assertFalse(correlation.compare_outputs(self.analysis, self.output)["passed"])
        self.assertEqual(directory_snapshot(self.root), before)
        path.write_bytes(saved)
        with (self.output / correlation.MATRIX_FILE).open("a", encoding="utf-8") as stream:
            stream.write("extra,1,2,3\n")
        self.assertFalse(correlation.compare_outputs(self.analysis, self.output)["passed"])

    def test_wrong_labels_order_or_cell_counts_fail(self):
        self.publish()
        path = self.output / correlation.MATRIX_FILE
        saved = path.read_text(encoding="utf-8")
        for text in (saved.replace("criterion_id,a,b,c", "criterion_id,b,a,c"), saved.replace("a,", "wrong,", 1), saved.replace(",0.999", ",missing", 1)):
            if text == saved:
                continue
            with self.subTest(text=text):
                path.write_text(text, encoding="utf-8")
                self.assertFalse(correlation.compare_outputs(self.analysis, self.output)["passed"])
        path.write_text(saved.replace("criterion_id,a,b,c", "criterion_id,a,b"), encoding="utf-8")
        self.assertFalse(correlation.compare_outputs(self.analysis, self.output)["passed"])

    def test_changed_finite_matrix_value_fails_even_with_updated_checksum(self):
        self.publish()
        path = self.output / correlation.MATRIX_FILE
        rows = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8"))))
        rows[1][2] = rows[2][1] = "0.12345"
        stream = io.StringIO(newline="")
        csv.writer(stream, lineterminator="\n").writerows(rows)
        path.write_text(stream.getvalue(), encoding="utf-8")
        self.update_manifest_hash(correlation.MATRIX_FILE)
        report = correlation.compare_outputs(self.analysis, self.output)
        self.assertFalse(report["passed"])
        self.assertIn("coefficients differ", report["errors"][0])

    def test_nan_inf_and_out_of_bounds_saved_matrix_fail(self):
        self.publish()
        path = self.output / correlation.MATRIX_FILE
        saved = path.read_text(encoding="utf-8")
        original_rows = list(csv.reader(io.StringIO(saved)))
        for invalid in ("nan", "inf", "1.5"):
            rows = [row.copy() for row in original_rows]
            rows[1][2] = rows[2][1] = invalid
            stream = io.StringIO(newline="")
            csv.writer(stream, lineterminator="\n").writerows(rows)
            path.write_text(stream.getvalue(), encoding="utf-8")
            self.update_manifest_hash(correlation.MATRIX_FILE)
            self.assertFalse(correlation.compare_outputs(self.analysis, self.output)["passed"])

    def test_changed_statistic_fails_even_with_updated_checksum(self):
        self.publish()
        path = self.output / correlation.STATISTICS_FILE
        saved = path.read_text(encoding="utf-8")
        reader = csv.DictReader(io.StringIO(saved))
        original_rows = list(reader)
        for key, changed in (("zero_count", "2"), ("mean", "nan"), ("finite_count", "5"), ("std_population", "0.7")):
            rows = [row.copy() for row in original_rows]
            rows[0][key] = changed
            stream = io.StringIO(newline="")
            writer = csv.DictWriter(stream, fieldnames=reader.fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            path.write_text(stream.getvalue(), encoding="utf-8")
            self.update_manifest_hash(correlation.STATISTICS_FILE)
            self.assertFalse(correlation.compare_outputs(self.analysis, self.output)["passed"])

    def test_stale_baseline_and_changed_manifest_fail(self):
        self.publish()
        path = self.output / correlation.MANIFEST_FILE
        original = json.loads(path.read_text(encoding="utf-8"))
        for key, value in (("baseline", {"baseline_id": "wrong"}), ("aoi_cells", 5), ("p_values_computed", True), ("weights_applied", True)):
            manifest = original.copy()
            manifest[key] = value
            path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertFalse(correlation.compare_outputs(self.analysis, self.output)["passed"])

    def test_csv_checksum_mismatch_fails(self):
        self.publish()
        path = self.output / correlation.MATRIX_FILE
        path.write_bytes(path.read_bytes() + b"\n")
        self.assertFalse(correlation.compare_outputs(self.analysis, self.output)["passed"])

    def test_check_cli_never_writes_and_missing_output_fails(self):
        before = directory_snapshot(self.root)
        with mock.patch.object(correlation, "analyze_project", return_value=self.analysis), contextlib.redirect_stdout(io.StringIO()) as output:
            code = correlation.main(["--check", "--project-root", str(self.root), "--json"])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(output.getvalue())["passed"])
        self.assertEqual(directory_snapshot(self.root), before)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_generate_then_check_cli_passes_without_changing_files(self):
        arguments = ["--project-root", str(self.root), "--output-dir", str(self.output), "--json"]
        with mock.patch.object(correlation, "analyze_project", return_value=self.analysis), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(correlation.main(["--generate", *arguments]), 0)
        before = directory_snapshot(self.root)
        with mock.patch.object(correlation, "analyze_project", return_value=self.analysis), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(correlation.main(["--check", *arguments]), 0)
        self.assertTrue(json.loads(output.getvalue())["passed"])
        self.assertEqual(directory_snapshot(self.root), before)

    def test_invalid_inputs_generate_and_missing_dependency_leave_no_files(self):
        for error, expected_code in ((ValueError("bad frozen data"), 1), (ImportError("missing GDAL"), 2)):
            with mock.patch.object(correlation, "analyze_project", side_effect=error), contextlib.redirect_stdout(io.StringIO()) as output:
                code = correlation.main(["--generate", "--output-dir", str(self.output), "--json"])
            self.assertEqual(code, expected_code)
            self.assertFalse(json.loads(output.getvalue())["passed"])
            self.assertEqual(list(self.root.iterdir()), [])

    def test_help_runs_without_site_packages(self):
        process = subprocess.run([sys.executable, "-S", str(Path(correlation.__file__)), "--help"], capture_output=True, text=True, check=False)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("--generate", process.stdout)


if __name__ == "__main__":
    unittest.main()
