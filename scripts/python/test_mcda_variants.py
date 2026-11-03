#!/usr/bin/env python3
"""Variant weights, merged criteria, alternative thresholds, flood evidence and saved-artifact contracts."""
from __future__ import annotations

import copy
from dataclasses import replace
import json
import math
import os
from pathlib import Path
import tempfile
import unittest
import sys

sys.dont_write_bytecode = True
os.environ["GDAL_PAM_ENABLED"] = "NO"
from tier_support import module_tier

TIER = module_tier(__file__)
if TIER.available:
    import numpy as np
    from osgeo import gdal, ogr, osr
    import mcda_scenario_engine as engine
import generate_mcda_variants as mv

ROOT = Path(__file__).resolve().parents[2]
IDS = ("earthquake_pga_score", "flood_score", "landcover_sensitivity_score", "tree_cover_score", "road_accessibility_difficulty_score")
WEIGHTS = (0.4, 0.2, 0.15, 0.1, 0.15)
MEMBERS = ["landcover_sensitivity_score", "tree_cover_score"]


def config():
    return {"format_version": 1, "baseline_id": "test-frozen-v1", "output_dir": "outputs/analysis/test",
            "scenarios": [
                {"id": "flood_weight_zero", "group": "flood", "role": "main", "remove": ["flood_score"]},
                {"id": "vegetation_mean_reduced", "group": "vegetation", "role": "main",
                 "merge": {"criteria": MEMBERS, "into": "vegetation_score", "method": "mean", "block_weight": "largest_member"}},
                {"id": "vegetation_mean_same_block", "group": "vegetation", "role": "supplementary",
                 "merge": {"criteria": MEMBERS, "into": "vegetation_score", "method": "mean", "block_weight": "sum"}},
                {"id": "vegetation_drop_tree", "group": "vegetation", "role": "supplementary", "remove": ["tree_cover_score"]},
                {"id": "vegetation_separate_reduced", "group": "vegetation", "role": "supplementary",
                 "rescale": {"criteria": MEMBERS, "block_weight": "largest_member"}}],
            "classification": {"methods": ["equal_interval", "quantile", "natural_breaks"], "natural_breaks_bins": 100},
            "flood_evidence": {"hydrorivers": "rivers.gpkg", "flood_depth": "depth.tif", "upstream_area_thresholds_km2": [150, 500],
                               "source_findings": [{"id": "nodata_meaning", "status": "unverified", "finding": "Not defined.",
                                                    "source": "https://example.org/readme"}]}}


def projection():
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(32635)
    return srs.ExportToWkt()


def stack(n=90):
    rng = np.random.default_rng(5)
    vectors = [rng.random(n, dtype=np.float32) * np.float32(0.55) for _ in IDS]
    vectors[1] = np.where(rng.random(n) < 0.2, vectors[1], 0).astype(np.float32)  # sparse flood
    for vector in vectors:
        vector[:4] = np.float32(0.5)  # class 5 cells without clipping at 1
    aoi = np.zeros((3, n // 3 + 2), dtype=bool)
    aoi[:, 1:n // 3 + 1] = True
    s = engine.CanonicalStack(IDS, WEIGHTS, tuple(vectors), aoi, np.repeat(np.arange(1, 4), n // 3).astype(np.int64),
                              tuple({"district_id": i, "district_name": f"İlçe {i}"} for i in range(1, 4)),
                              (400000., 100., 0., 4500000., 0., -100.), projection(), 0.01,
                              {"baseline_id": "test-frozen-v1", "baseline_manifest_sha256": "1" * 64})
    return replace(s, baseline_classes=engine.FixedScale().classes(s.raw(s.baseline_mapping())))


def analysis(cfg=None, s=None):
    cfg, s = cfg or config(), s or stack()
    distances = {150: np.arange(s.n_cells, dtype=np.float32) * 10, 500: np.arange(s.n_cells, dtype=np.float32) * 20}
    result = mv.analyze(s, cfg, distances, {"valid": 12, "zero": 0, "min": 0.1})
    result.update(config_path="config/test.json", config_sha256="2" * 64,
                  inputs={"hydrorivers": {"path": "rivers.gpkg", "sha256": "3" * 64}, "flood_depth": {"path": "depth.tif", "sha256": "4" * 64}})
    return result


def rows(result, table):
    return result["tables"][table][0]


@TIER.skip_unless_available
class VariantWeights(unittest.TestCase):
    def test_remove_spreads_weight_in_proportion(self):
        base = dict(zip(IDS, WEIGHTS))
        w = mv.scenario_weights(base, config()["scenarios"][0])
        self.assertEqual(w["flood_score"], 0.0)
        self.assertAlmostEqual(w["earthquake_pga_score"], 0.5)
        self.assertAlmostEqual(math.fsum(w.values()), 1.0, places=12)
        self.assertAlmostEqual(w["landcover_sensitivity_score"] / w["road_accessibility_difficulty_score"], 1.0)

    def test_largest_member_block_matches_canonical_derivation(self):
        base = {"a": 0.9, "landcover_sensitivity_score": 0.06, "tree_cover_score": 0.04}
        spec = config()["scenarios"][1]
        w = mv.scenario_weights(base, spec)
        self.assertAlmostEqual(w["vegetation_score"], 0.06 / 0.96)
        self.assertAlmostEqual(w["vegetation_score"], 0.0625)
        self.assertAlmostEqual(w["a"], 0.9 / 0.96)
        self.assertEqual((w["landcover_sensitivity_score"], w["tree_cover_score"]), (0.0, 0.0))

    def test_rescale_keeps_members_separate_at_the_reduced_block(self):
        base = {"a": 0.9, "landcover_sensitivity_score": 0.06, "tree_cover_score": 0.04}
        w = mv.scenario_weights(base, config()["scenarios"][4])
        merged = mv.scenario_weights(base, config()["scenarios"][1])
        self.assertAlmostEqual(w["landcover_sensitivity_score"], 0.0375)
        self.assertAlmostEqual(w["tree_cover_score"], 0.025)
        self.assertAlmostEqual(w["landcover_sensitivity_score"] + w["tree_cover_score"], merged["vegetation_score"])
        self.assertAlmostEqual(w["a"], merged["a"])
        self.assertNotIn("vegetation_score", w)

    def test_sum_block_keeps_other_weights(self):
        base = dict(zip(IDS, WEIGHTS))
        w = mv.scenario_weights(base, config()["scenarios"][2])
        self.assertAlmostEqual(w["vegetation_score"], 0.25)
        for key in ("earthquake_pga_score", "flood_score", "road_accessibility_difficulty_score"):
            self.assertEqual(w[key], base[key])

    def test_invalid_weight_specs_rejected(self):
        base = dict(zip(IDS, WEIGHTS))
        bad = [{"id": "x", "remove": ["missing"]}, {"id": "x", "remove": list(IDS)},
               {"id": "x", "merge": {"criteria": ["missing", "flood_score"], "into": "v", "block_weight": "sum"}},
               {"id": "x", "merge": {"criteria": MEMBERS, "into": "flood_score", "block_weight": "sum"}}]
        for spec in bad:
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                mv.scenario_weights(base, spec)

    def test_merged_mean_equals_reweighted_members(self):
        s = stack()
        spec = config()["scenarios"][2]
        merged = mv.scenario_raw(s, spec, mv.scenario_weights(s.baseline_mapping(), spec))
        direct = s.raw({**s.baseline_mapping(), "landcover_sensitivity_score": 0.125, "tree_cover_score": 0.125})
        np.testing.assert_allclose(merged, direct, rtol=0, atol=1e-6)
        self.assertEqual(merged.dtype, np.float32)


@TIER.skip_unless_available
class ConfigContracts(unittest.TestCase):
    def write(self, cfg):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(cfg, handle)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return Path(handle.name)

    def test_repository_config_is_valid_and_names_the_decided_scenarios(self):
        cfg = mv.load_config(ROOT / mv.DEFAULT_CONFIG)
        self.assertEqual([s["id"] for s in cfg["scenarios"]],
                         ["flood_weight_zero", "vegetation_mean_reduced", "vegetation_mean_same_block", "vegetation_drop_tree",
                          "vegetation_separate_reduced"])
        self.assertEqual([s["role"] for s in cfg["scenarios"]], ["main", "main", "supplementary", "supplementary", "supplementary"])
        self.assertFalse(any("weight_mask" in json.dumps(s) for s in cfg["scenarios"]))

    def test_bad_configs_rejected(self):
        mutations = [
            lambda c: c["scenarios"].append(copy.deepcopy(c["scenarios"][0])),
            lambda c: c["scenarios"][0].update(id="baseline"),
            lambda c: c["scenarios"][0].update(role="other"),
            lambda c: c["scenarios"][0].update(merge=c["scenarios"][1]["merge"]),
            lambda c: c["scenarios"][1]["merge"].update(method="max"),
            lambda c: c["scenarios"][1]["merge"].update(block_weight="half"),
            lambda c: c["scenarios"][4]["rescale"].update(block_weight="sum"),
            lambda c: c["scenarios"][4].update(remove=["flood_score"]),
            lambda c: c["classification"].update(methods=["quantile"]),
            lambda c: c["flood_evidence"].update(upstream_area_thresholds_km2=[500, 150]),
            lambda c: c["flood_evidence"].update(source_findings=[]),
            lambda c: c.update(format_version=2),
        ]
        for index, mutate in enumerate(mutations):
            cfg = config()
            mutate(cfg)
            with self.subTest(index=index), self.assertRaises(ValueError):
                mv.load_config(self.write(cfg))


@TIER.skip_unless_available
class AnalysisContracts(unittest.TestCase):
    def test_baseline_rows_are_identity_in_both_measures(self):
        result = analysis()
        for row in rows(result, mv.SUMMARY_TABLE)[:2]:
            self.assertEqual(row["scenario_id"], "baseline")
            self.assertEqual((row["jaccard"], row["baseline_high_retention"], row["very_high_jaccard"]), (1.0, 1.0, 1.0))
            self.assertTrue(row["top5_same_order"])

    def test_every_variant_has_both_measures_and_weights_sum_to_one(self):
        result = analysis()
        summary = rows(result, mv.SUMMARY_TABLE)
        self.assertEqual(len(summary), 2 * 6)
        self.assertEqual({r["normalization"] for r in summary}, set(mv.NORMALIZATIONS))
        totals = {}
        for row in rows(result, mv.WEIGHTS_TABLE):
            totals.setdefault(row["scenario_id"], []).append(row["weight"])
        for scenario, values in totals.items():
            self.assertAlmostEqual(math.fsum(values), 1.0, places=12, msg=scenario)
        flood = [r for r in rows(result, mv.WEIGHTS_TABLE) if r["scenario_id"] == "flood_weight_zero" and r["criterion_id"] == "flood_score"]
        self.assertEqual(flood[0]["weight"], 0.0)

    def test_top_share_keeps_the_baseline_cell_count(self):
        result = analysis()
        base = [r for r in rows(result, mv.SUMMARY_TABLE) if r["scenario_id"] == "baseline" and r["normalization"] == "top_share"][0]
        for row in rows(result, mv.SUMMARY_TABLE):
            if row["normalization"] == "top_share":
                self.assertGreaterEqual(row["high_pixel_count"], base["high_pixel_count"])
                self.assertLessEqual(row["high_pixel_count"] - base["high_pixel_count"], 2)

    def test_district_rows_rank_by_area(self):
        result = analysis()
        districts = rows(result, mv.DISTRICT_TABLE)
        self.assertEqual(len(districts), 6 * 2 * 3)
        for scenario in {r["scenario_id"] for r in districts}:
            part = [r for r in districts if r["scenario_id"] == scenario and r["normalization"] == "top_share"]
            ordered = sorted(part, key=lambda r: -r["high_area_km2"])
            self.assertEqual(ordered[0]["rank"], 1)

    def test_classification_rows_and_distribution(self):
        result = analysis()
        summary = {r["method"]: r for r in rows(result, mv.CLASS_SUMMARY_TABLE)}
        self.assertEqual(list(summary), list(mv.METHODS))
        self.assertEqual(summary["equal_interval"]["same_class_as_equal_interval_percent"], 100.0)
        self.assertIsNone(summary["equal_interval"]["goodness_of_variance_fit"])
        self.assertIsNotNone(summary["natural_breaks"]["goodness_of_variance_fit"])
        province = [r for r in rows(result, mv.CLASS_DISTRIBUTION_TABLE) if r["method"] == "quantile" and r["scope"] == "province"]
        self.assertEqual([r["pixel_count"] for r in province], [18] * 5)
        self.assertEqual(len(rows(result, mv.CLASS_DISTRIBUTION_TABLE)), 3 * 4 * 5)

    def test_flood_evidence_counts_and_findings(self):
        s = stack()
        result = analysis(s=s)
        evidence = {r["evidence_id"]: r for r in rows(result, mv.FLOOD_TABLE)}
        flood = s.vectors[1] > 0
        high = engine.TopShare.from_classes(s.baseline_classes).high_plus(s.raw(s.baseline_mapping()))
        self.assertEqual(evidence["flood_score_positive_cells"]["value"], int(flood.sum()))
        self.assertEqual(evidence["baseline_high_plus_with_flood"]["value"], int((high & flood).sum()))
        self.assertEqual(evidence["nodata_meaning"]["value"], "unverified")
        self.assertIn("flood_cell_distance_upland_ge_500_km2_max", evidence)
        self.assertNotIn("coverage", " ".join(r["scenario_id"] for r in rows(result, mv.SUMMARY_TABLE)))

    def test_analysis_is_deterministic(self):
        first, second = analysis(), analysis()
        self.assertEqual(first["tables"], second["tables"])


@TIER.skip_unless_available
class GisInputs(unittest.TestCase):
    def test_river_distances_filter_by_upstream_area(self):
        s = stack()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "rivers.gpkg"
            source = ogr.GetDriverByName("GPKG").CreateDataSource(str(path))
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(32635)
            layer = source.CreateLayer("rivers", srs, ogr.wkbLineString)
            layer.CreateField(ogr.FieldDefn("UPLAND_SKM", ogr.OFTReal))
            for upland, x in ((200.0, 400150.0), (800.0, 402950.0)):
                feature = ogr.Feature(layer.GetLayerDefn())
                feature.SetField("UPLAND_SKM", upland)
                feature.SetGeometry(ogr.CreateGeometryFromWkt(f"LINESTRING ({x} 4500000, {x} 4499700)"))
                layer.CreateFeature(feature)
            source = layer = None
            distances = mv.river_distances(s, path, [150, 500])
        self.assertEqual(distances[150].shape, (s.n_cells,))
        self.assertTrue(np.all(distances[150] <= distances[500]))
        self.assertGreater(float(distances[500].max()), float(distances[150].min()))
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(ValueError):
            path = Path(temporary) / "empty.gpkg"
            source = ogr.GetDriverByName("GPKG").CreateDataSource(str(path))
            layer = source.CreateLayer("rivers", None, ogr.wkbLineString)
            layer.CreateField(ogr.FieldDefn("UPLAND_SKM", ogr.OFTReal))
            source = layer = None
            mv.river_distances(s, path, [150])

    def test_depth_statistics_ignore_nodata(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "depth.tif"
            dataset = gdal.GetDriverByName("GTiff").Create(str(path), 3, 2, 1, gdal.GDT_Float32)
            band = dataset.GetRasterBand(1)
            band.SetNoDataValue(-9999)
            band.WriteArray(np.array([[-9999, 0.5, 2.0], [-9999, -9999, 0.1]], dtype=np.float32))
            band = dataset = None
            stats = mv.depth_statistics(path)
        self.assertEqual((stats["valid"], stats["zero"]), (3, 0))
        self.assertAlmostEqual(stats["min"], 0.1, places=6)


@TIER.skip_unless_available
class SavedArtifacts(unittest.TestCase):
    def setUp(self):
        self.result = analysis()
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.out = Path(self.temporary.name) / "variants"
        mv.write_outputs(self.result, self.out)

    def test_round_trip_passes(self):
        report = mv.compare_outputs(self.result, self.out)
        self.assertTrue(report["passed"], report["errors"])
        self.assertEqual(report["checked_files"], len(mv.OUTPUT_FILES))

    def test_refuses_to_overwrite(self):
        with self.assertRaises(ValueError):
            mv.write_outputs(self.result, self.out)

    def test_changed_table_value_is_detected(self):
        path = self.out / mv.SUMMARY_TABLE
        text = path.read_text(encoding="utf-8").splitlines()
        text[3] = text[3].replace(",main,", ",supplementary,", 1)
        path.chmod(0o644)
        path.unlink()
        path.write_text("\n".join(text) + "\n", encoding="utf-8")
        self.assertFalse(mv.compare_outputs(self.result, self.out)["passed"])

    def test_changed_manifest_and_missing_file_are_detected(self):
        manifest = json.loads((self.out / mv.MANIFEST_FILE).read_text(encoding="utf-8"))
        manifest["flood_coverage_variant"] = "mask"
        (self.out / mv.MANIFEST_FILE).unlink()
        (self.out / mv.MANIFEST_FILE).write_text(json.dumps(manifest), encoding="utf-8")
        self.assertFalse(mv.compare_outputs(self.result, self.out)["passed"])
        (self.out / mv.FLOOD_TABLE).unlink()
        self.assertFalse(mv.compare_outputs(self.result, self.out)["passed"])

    def test_manifest_records_inputs_and_no_coverage_variant(self):
        manifest = json.loads((self.out / mv.MANIFEST_FILE).read_text(encoding="utf-8"))
        self.assertEqual(manifest["inputs"]["hydrorivers"]["sha256"], "3" * 64)
        self.assertTrue(manifest["flood_coverage_variant"].startswith("None"))
        self.assertFalse(manifest["weights_modified"])


if __name__ == "__main__":
    unittest.main()
