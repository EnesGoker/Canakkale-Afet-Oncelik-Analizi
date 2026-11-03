#!/usr/bin/env python3
"""OAT, Dirichlet, determinism, convergence, district-rank and saved-artifact contracts."""
from __future__ import annotations

import csv
from dataclasses import replace
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

sys.dont_write_bytecode = True
os.environ["GDAL_PAM_ENABLED"] = "NO"
from tier_support import module_tier

TIER = module_tier(__file__)
if TIER.available:
    import numpy as np
    from osgeo import gdal, osr
    import mcda_scenario_engine as engine
import generate_weight_perturbation as wp

ROOT = Path(__file__).resolve().parents[2]
IDS = ("first", "second", "third")
WEIGHTS = (0.5, 0.3, 0.2)


def config():
    return {"format_version": 1, "baseline_id": "test-frozen-v1", "output_dir": "outputs/analysis/test", "seed": 11,
            "kappas": [50, 100], "main_kappa": 100, "samples": 20,
            "convergence": {"kappa": 100, "snapshots": [10, 20], "reference_samples": 40,
                            "p99_abs_difference_limit": 1.0, "p_ge_050_area_relative_change_limit": 1.0},
            "oat_steps": [-0.2, 0.2], "normalizations": {"main": "top_share", "supplementary": "fixed_scale"},
            "probability_class_edges": [0.25, 0.5, 0.75, 0.9]}


def stack(n=60):
    rng = np.random.default_rng(7)
    vectors = tuple(rng.random(n, dtype=np.float32) * np.float32(0.5) for _ in IDS)
    aoi = np.zeros((2, n + 2), dtype=bool)
    aoi[0, 1:n // 2 + 1] = True
    aoi[1, 1:n // 2 + 1] = True
    projection = osr.SpatialReference()
    projection.ImportFromEPSG(32635)
    s = engine.CanonicalStack(IDS, WEIGHTS, vectors, aoi, np.repeat(np.arange(1, 4), n // 3).astype(np.int64),
                              tuple({"district_id": i, "district_name": f"İlçe {i}"} for i in range(1, 4)),
                              (400000., 100., 0., 4500000., 0., -100.), projection.ExportToWkt(), 0.01,
                              {"baseline_id": "test-frozen-v1", "baseline_manifest_sha256": "1" * 64})
    return replace(s, baseline_classes=engine.FixedScale().classes(s.raw(s.baseline_mapping())))


def analysis(cfg=None, s=None):
    cfg, s = cfg or config(), s or stack()
    weights = wp.sample_weights(cfg, s.baseline_weights)
    base = s.baseline_mapping()
    scenarios = {"baseline": base, "earthquake-heavy": {"first": .6, "second": .25, "third": .15}, "equal-weight": {k: 1 / 3 for k in IDS}}
    published = {name: engine.FixedScale().classes(s.raw(w)) for name, w in scenarios.items()}
    published["baseline"] = s.baseline_classes
    result = wp.analyze(s, cfg, weights, published, scenarios)
    result.update(seed_check={"seed_reproduced": None}, config_path="config/test.json", config_sha256="2" * 64)
    return result


@TIER.skip_unless_available
class PerturbationContracts(unittest.TestCase):
    def test_oat_rescales_others_proportionally(self):
        base = dict(zip(IDS, WEIGHTS))
        w = wp.oat_weights(base, "first", 0.2)
        self.assertAlmostEqual(w["first"], 0.6)
        self.assertAlmostEqual(sum(w.values()), 1.0, places=12)
        self.assertAlmostEqual(w["second"] / w["third"], 1.5)

    def test_oat_rejects_steps_leaving_unit_interval(self):
        with self.assertRaises(ValueError):
            wp.oat_weights({"a": 0.9, "b": 0.1}, "a", 0.2)

    def test_repository_config_is_valid(self):
        loaded = wp.load_config(ROOT / wp.DEFAULT_CONFIG)
        self.assertEqual((loaded["main_kappa"], loaded["samples"], loaded["seed"]), (100, 2000, 20261103))
        self.assertEqual(loaded["kappas"], [50, 100, 200])

    def test_config_rejections(self):
        cases = [("main_kappa", 75), ("samples", 70000), ("samples", 30), ("oat_steps", [0.0]),
                 ("probability_class_edges", [0.5, 0.25]), ("normalizations", {"main": "fixed_scale", "supplementary": "top_share"})]
        for key, value in cases:
            cfg = config()
            cfg[key] = value
            with self.subTest(key=key, value=value), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "c.json"
                path.write_text(json.dumps(cfg))
                with self.assertRaises(ValueError):
                    wp.load_config(path)

    def test_seeded_streams_are_repeatable_and_prefix_stable(self):
        first, second = wp.sample_weights(config(), WEIGHTS), wp.sample_weights(config(), WEIGHTS)
        for kappa in first:
            np.testing.assert_array_equal(first[kappa], second[kappa])
            np.testing.assert_allclose(first[kappa].sum(axis=1), 1.0, atol=1e-12)
        self.assertEqual(first[100].shape, (40, 3))
        self.assertFalse(np.array_equal(first[50][:20], first[100][:20]))
        longer = config()
        longer["convergence"]["reference_samples"] = 80
        np.testing.assert_array_equal(wp.sample_weights(longer, WEIGHTS)[100][:40], first[100])

    def test_probability_classes_use_exact_edges(self):
        counts = np.array([0, 1, 4, 5, 9, 10, 14, 15, 17, 18, 20])
        np.testing.assert_array_equal(wp.probability_classes(counts, 20, [0.25, 0.5, 0.75, 0.9]), [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5])
        self.assertEqual(wp.probability_labels([0.25, 0.5, 0.75, 0.9])[0], "P = 0")
        with self.assertRaises(ValueError):
            wp.probability_classes(np.array([21]), 20, [0.5])

    def test_counts_are_independent_of_sample_order_and_chunks(self):
        s = stack()
        models = wp.classifiers(s)
        base = {"high": s.baseline_classes >= 4}
        weights = wp.sample_weights(config(), WEIGHTS)[100][:20]
        forward, _, _ = wp.run_samples(s, weights, models, base)
        backward, _, _ = wp.run_samples(s, weights[::-1], models, base)
        first, _, _ = wp.run_samples(s, weights[:7], models, base)
        rest, _, _ = wp.run_samples(s, weights[7:], models, base)
        for name in models:
            np.testing.assert_array_equal(forward[name], backward[name])
            np.testing.assert_array_equal(forward[name], first[name] + rest[name])

    def test_text_roundtrip_of_weights_reproduces_counts(self):
        a = analysis()
        with tempfile.TemporaryDirectory() as folder:
            wp.write_outputs(a, Path(folder) / "out")
            saved = wp.read_weight_table(Path(folder) / "out" / wp.WEIGHTS_TABLE, config(), IDS)
        seeded = wp.sample_weights(config(), WEIGHTS)
        for kappa in seeded:
            np.testing.assert_array_equal(saved[kappa], seeded[kappa])

    def test_table_shapes_and_top_share_area_constant(self):
        a = analysis()
        oat = a["tables"][wp.OAT_TABLE][0]
        self.assertEqual(len(oat), len(IDS) * 2 * 2)
        top = [row for row in oat if row["normalization"] == "top_share"]
        base_cells = int((stack().baseline_classes >= 4).sum())
        self.assertTrue(all(row["high_pixel_count"] >= base_cells for row in top))
        self.assertEqual(len(a["tables"][wp.BRIDGE_TABLE][0]), 9)
        self.assertEqual(len(a["tables"][wp.WEIGHTS_TABLE][0]), 20 + 40)
        self.assertEqual(len(a["tables"][wp.RANK_TABLE][0]), 2 * 2 * 3)
        self.assertEqual(len(a["tables"][wp.KAPPA_TABLE][0]), 4)

    def test_bridge_baseline_rows_are_identity(self):
        rows = [r for r in analysis()["tables"][wp.BRIDGE_TABLE][0] if r["scenario_id"] == "baseline"]
        self.assertEqual({r["normalization"] for r in rows}, {wp.PUBLISHED, "top_share", "fixed_scale"})
        for row in rows:
            self.assertEqual((row["baseline_high_retention"], row["jaccard"], row["top5_same_order"]), (1.0, 1.0, True))
            self.assertAlmostEqual(row["delta_high_area_km2"], 0)

    def test_convergence_reference_row_and_refusal(self):
        a = analysis()
        rows = a["tables"][wp.CONVERGENCE_TABLE][0]
        reference = [r for r in rows if r["samples"] == 40]
        self.assertEqual(len(reference), 2)
        self.assertTrue(all(r["max_abs_difference"] is None and r["meets_criterion"] is None for r in reference))
        self.assertTrue(a["convergence_verdict"]["passed"])
        strict = config()
        strict["convergence"]["p99_abs_difference_limit"] = 0.0
        failed = analysis(strict)
        self.assertFalse(failed["convergence_verdict"]["passed"])
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
            wp.write_outputs(failed, Path(folder) / "out")

    def test_constant_baseline_samples_give_stable_ranks(self):
        s = stack()
        models = wp.classifiers(s)
        high = s.baseline_classes >= 4
        areas = engine.district_areas(high, s.district_ids, 3)
        weights = np.tile(np.array(WEIGHTS), (5, 1))
        _, records, _ = wp.run_samples(s, weights, models, {"high": high})
        rows = wp.rank_rows(100, s, records, {"high": high, "areas": areas})
        for row in rows:
            self.assertEqual(row["median_rank"], row["baseline_rank"])
            self.assertIn(row["top1_share"], (0.0, 1.0))

    def test_competition_rank_shares_zero_area_ties(self):
        s = stack()
        cells = np.array([[5, 0, 0], [0, 0, 0]])
        records = {name: {"districts": cells} for name in wp.NORMALIZATIONS}
        rows = wp.rank_rows(100, s, records, {"areas": np.array([0.05, 0.0, 0.0])})
        first = [r for r in rows if r["normalization"] == "top_share"]
        self.assertEqual([r["baseline_rank"] for r in first], [1, 2, 2])
        self.assertEqual([r["top1_share"] for r in first], [1.0, 0.5, 0.5])

    def test_probability_rows_conserve_cells(self):
        a = analysis()
        rows = a["tables"][wp.PROBABILITY_TABLE][0]
        province = [r for r in rows if r["scope"] == "province"]
        self.assertEqual(sum(r["pixel_count"] for r in province), a["n_cells"])
        self.assertEqual(len(rows), 4 * 6)


@TIER.skip_unless_available
class SavedArtifactContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "package"
        self.data = analysis()
        wp.write_outputs(self.data, self.output)

    def edit_csv(self, name, row, column, value):
        path = self.output / name
        rows = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8"))))
        rows[row][column] = value
        with path.open("w", newline="", encoding="utf-8") as stream:
            csv.writer(stream, lineterminator="\n").writerows(rows)

    def test_roundtrip_checks_all_files(self):
        report = wp.compare_outputs(self.data, self.output)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["checked_files"], len(wp.OUTPUT_FILES))
        self.assertEqual(report["checked_raster_cells"], self.data["aoi"].size)

    def test_missing_artifact_fails(self):
        for name in wp.OUTPUT_FILES:
            path = self.output / name
            content = path.read_bytes()
            path.unlink()
            with self.subTest(name=name):
                self.assertFalse(wp.compare_outputs(self.data, self.output)["passed"])
            path.write_bytes(content)

    def test_weight_digit_change_fails(self):
        path = self.output / wp.WEIGHTS_TABLE
        rows = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8"))))
        self.edit_csv(wp.WEIGHTS_TABLE, 1, 3, repr(float(rows[1][3]) + 1e-9))
        self.assertFalse(wp.compare_outputs(self.data, self.output)["passed"])

    def test_summary_value_change_fails(self):
        self.edit_csv(wp.OAT_TABLE, 1, 5 + len(IDS), "999")
        self.assertFalse(wp.compare_outputs(self.data, self.output)["passed"])

    def test_raster_value_and_outside_cell_change_fail(self):
        for row, column, value in ((0, 1, 3), (0, 0, 0)):
            path = self.output / wp.COUNT_FILE
            original = path.read_bytes()
            ds = gdal.Open(str(path), gdal.GA_Update)
            array = ds.GetRasterBand(1).ReadAsArray()
            array[row, column] = value if array[row, column] != value else value + 1
            ds.GetRasterBand(1).WriteArray(array)
            ds = None
            with self.subTest(cell=(row, column)):
                self.assertFalse(wp.compare_outputs(self.data, self.output)["passed"])
            path.write_bytes(original)

    def test_manifest_config_and_software_changes_fail(self):
        path = self.output / wp.MANIFEST_FILE
        original = path.read_text(encoding="utf-8")
        for kind in ("config", "software", "convergence"):
            manifest = json.loads(original)
            if kind == "config": manifest["config_sha256"] = "0" * 64
            if kind == "software": manifest["software"]["numpy"] = ""
            if kind == "convergence": manifest["convergence"]["passed"] = False
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.subTest(kind=kind):
                self.assertFalse(wp.compare_outputs(self.data, self.output)["passed"])
        path.write_text(original, encoding="utf-8")

    def test_read_only_check_does_not_change_files(self):
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        self.assertTrue(wp.compare_outputs(self.data, self.output)["passed"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_nonempty_and_symbolic_output_never_overwritten(self):
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        with self.assertRaises(ValueError):
            wp.write_outputs(self.data, self.output)
        alias = Path(self.temp.name) / "alias"
        alias.symlink_to(self.output, target_is_directory=True)
        with self.assertRaises(ValueError):
            wp.write_outputs(self.data, alias)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_failed_publication_rolls_back_owned_files(self):
        target = Path(self.temp.name) / "failed"
        original_link = os.link
        calls = []
        def fail_third(source, destination):
            calls.append(destination)
            if len(calls) == 3:
                raise OSError("simulated publication failure")
            return original_link(source, destination)
        with patch.object(wp.os, "link", side_effect=fail_third), self.assertRaises(OSError):
            wp.write_outputs(self.data, target)
        self.assertFalse(target.exists())

    def test_weight_table_reader_rejects_columns_and_gaps(self):
        self.edit_csv(wp.WEIGHTS_TABLE, 0, 3, "renamed")
        with self.assertRaises(ValueError):
            wp.read_weight_table(self.output / wp.WEIGHTS_TABLE, config(), IDS)
        self.edit_csv(wp.WEIGHTS_TABLE, 0, 3, IDS[0])
        self.edit_csv(wp.WEIGHTS_TABLE, 2, 1, "7")
        with self.assertRaises(ValueError):
            wp.read_weight_table(self.output / wp.WEIGHTS_TABLE, config(), IDS)

    def test_cli_seed_mismatch_fails_but_reports_stored_weight_check(self):
        data = dict(self.data, seed_check={"seed_reproduced": False})
        with patch.object(wp, "analyze_project", return_value=data), patch.object(wp, "load_config", return_value=config()), \
                patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(wp.main(["--check", "--json", "--output-dir", str(self.output)]), 1)
        result = json.loads(output.getvalue())
        self.assertFalse(result["passed"])
        self.assertTrue(result["artifact_comparison"]["passed"])
        self.assertTrue(any(error.startswith("Environment:") for error in result["errors"]))

    def test_cli_exit_codes_and_missing_package(self):
        for error, code in ((ImportError("numpy missing"), 2), (ValueError("frozen input changed"), 1)):
            with self.subTest(code=code), patch.object(wp, "analyze_project", side_effect=error), \
                    patch("sys.stdout", new_callable=io.StringIO) as output:
                self.assertEqual(wp.main(["--check", "--json"]), code)
                self.assertFalse(json.loads(output.getvalue())["passed"])
        target = Path(self.temp.name) / "absent"
        data = dict(self.data, seed_check={"seed_reproduced": True})
        with patch.object(wp, "analyze_project", return_value=data), patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(wp.main(["--check", "--json", "--output-dir", str(target)]), 1)
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
