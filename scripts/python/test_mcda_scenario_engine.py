#!/usr/bin/env python3
"""Score arithmetic, classifier, weight-mask and read-only contracts of the shared engine."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
from tier_support import module_tier

TIER = module_tier(__file__)
if TIER.available:
    import numpy as np
    import mcda_scenario_engine as engine

IDS = ("first", "second", "third")
WEIGHTS = (0.5, 0.3, 0.2)


def stack(n=12, weights=WEIGHTS):
    rng = np.random.default_rng(7)
    vectors = tuple(rng.random(n, dtype=np.float32) for _ in IDS)
    aoi = np.zeros((3, n), dtype=bool)
    aoi[1] = True
    ids = np.repeat(np.arange(1, 4), n // 3).astype(np.int64)
    districts = tuple({"district_id": i, "district_name": f"İlçe {i}"} for i in range(1, 4))
    return engine.CanonicalStack(IDS, tuple(weights), vectors, aoi, ids, districts)


@TIER.skip_unless_available
class ScoreArithmetic(unittest.TestCase):
    def test_raw_repeats_canonical_expression_bit_for_bit(self):
        s = stack()
        expected = s.vectors[0] * 0.5 + s.vectors[1] * 0.3 + s.vectors[2] * 0.2
        raw = s.raw(s.baseline_mapping())
        self.assertEqual(raw.dtype, np.float32)
        np.testing.assert_array_equal(raw.view(np.uint32), expected.view(np.uint32))

    def test_float64_scalar_weights_cannot_upcast(self):
        s = stack()
        self.assertEqual((s.vectors[0] * np.float64(0.5)).dtype, np.float64)  # the NEP 50 trap
        raw = s.raw({key: np.float64(value) for key, value in s.baseline_mapping().items()})
        self.assertEqual(raw.dtype, np.float32)
        np.testing.assert_array_equal(raw.view(np.uint32), s.raw(s.baseline_mapping()).view(np.uint32))

    def test_sequence_and_mapping_weights_agree(self):
        s = stack()
        np.testing.assert_array_equal(s.raw(list(WEIGHTS)), s.raw(dict(zip(IDS, WEIGHTS))))
        with self.assertRaises(ValueError):
            s.raw([0.5, 0.5])

    def test_rejects_weights_not_summing_to_one(self):
        with self.assertRaises(ValueError):
            stack().raw({"first": 0.5, "second": 0.3, "third": 0.3})

    def test_rejects_negative_large_nonfinite_or_boolean_weights(self):
        for bad in (-0.1, 1.5, float("nan"), True, "0.2"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                stack().raw({"first": 0.5, "second": 0.3, "third": bad})

    def test_rejects_missing_or_unknown_criteria(self):
        with self.assertRaises(ValueError):
            stack().raw({"first": 0.7, "second": 0.3})
        with self.assertRaises(ValueError):
            stack().raw({"first": 0.5, "second": 0.3, "third": 0.1, "fourth": 0.1})

    def test_rejects_invalid_vectors(self):
        s = stack()
        for vector in (s.vectors[0].astype(np.float64), np.full(12, 1.5, np.float32), np.full(12, np.nan, np.float32), np.zeros(11, np.float32)):
            with self.subTest(dtype=vector.dtype, size=vector.size), self.assertRaises(ValueError):
                engine.CanonicalStack(IDS, WEIGHTS, (vector, *s.vectors[1:]), s.aoi, s.district_ids, s.districts)

    def test_stack_rejects_aoi_and_district_mismatch(self):
        s = stack()
        with self.assertRaises(ValueError):
            replace(s, aoi=np.ones((2, 2), dtype=bool))
        with self.assertRaises(ValueError):
            replace(s, district_ids=s.district_ids[:-1])
        with self.assertRaises(ValueError):
            replace(s, districts=s.districts[:2])

    def test_overrides_replace_or_append_criteria(self):
        s = stack()
        replacement = np.linspace(0, 1, 12, dtype=np.float32)
        raw = s.raw({"first": 0.5, "second": 0.3, "third": 0.2}, overrides={"second": replacement})
        expected = s.vectors[0] * 0.5 + replacement * 0.3 + s.vectors[2] * 0.2
        np.testing.assert_array_equal(raw, expected)
        raw = s.raw({"first": 0.5, "second": 0.0, "third": 0.2, "merged": 0.3}, overrides={"merged": replacement})
        expected = s.vectors[0] * 0.5 + s.vectors[1] * 0.0 + s.vectors[2] * 0.2 + replacement * 0.3
        np.testing.assert_array_equal(raw, expected)
        with self.assertRaises(ValueError):
            s.raw({"first": 0.5, "second": 0.3, "third": 0.2}, overrides={"second": replacement.astype(np.float64)})


@TIER.skip_unless_available
class WeightMask(unittest.TestCase):
    def test_full_coverage_keeps_plain_sum(self):
        s = stack()
        raw = s.raw(s.baseline_mapping(), weight_mask={"third": np.ones(12, dtype=bool)})
        np.testing.assert_array_equal(raw.view(np.uint32), s.raw(s.baseline_mapping()).view(np.uint32))

    def test_uncovered_cell_redistributes_weight(self):
        s = stack()
        mask = np.ones(12, dtype=bool)
        mask[4] = False
        raw = s.raw(s.baseline_mapping(), weight_mask={"third": mask})
        expected = (0.5 * float(s.vectors[0][4]) + 0.3 * float(s.vectors[1][4])) / 0.8
        self.assertEqual(raw[4], np.float32(expected))
        others = np.arange(12) != 4
        np.testing.assert_array_equal(raw[others], s.raw(s.baseline_mapping())[others])

    def test_cell_without_covered_weight_rejected(self):
        s = stack()
        none = np.ones(12, dtype=bool)
        none[0] = False
        with self.assertRaises(ValueError):
            s.raw(s.baseline_mapping(), weight_mask={key: none for key in IDS})

    def test_mask_shape_type_and_name_rejected(self):
        s = stack()
        for mask in ({"third": np.ones(11, dtype=bool)}, {"third": np.ones(12)}, {"unknown": np.ones(12, dtype=bool)}):
            with self.subTest(mask=list(mask)), self.assertRaises(ValueError):
                s.raw(s.baseline_mapping(), weight_mask=mask)


@TIER.skip_unless_available
class Classifiers(unittest.TestCase):
    def test_fixed_scale_threshold_value_belongs_to_upper_class(self):
        scale = engine.FixedScale(minimum=0.0, value_range=1.0)
        raw = np.array([0.2, 0.4, 0.6, 0.8], dtype=np.float32)
        np.testing.assert_array_equal(scale.classes(raw), [2, 3, 4, 5])
        below = np.nextafter(raw, np.float32(0))
        np.testing.assert_array_equal(scale.classes(below), [1, 2, 3, 4])

    def test_fixed_scale_clips_and_matches_combined_call(self):
        scale = engine.FixedScale()
        raw = np.array([-1.0, 0.0, 0.029, 0.3128, 0.4074, 0.6, 2.0], dtype=np.float32)
        np.testing.assert_array_equal(scale.classes(raw)[[0, 1, 2, -1]], [1, 1, 1, 5])
        high, very = scale.high_and_very_high(raw)
        np.testing.assert_array_equal(high, scale.high_plus(raw))
        np.testing.assert_array_equal(very, scale.very_high(raw))
        np.testing.assert_array_equal(high, scale.classes(raw) >= 4)

    def test_top_share_reproduces_class_counts_without_ties(self):
        raw = np.random.default_rng(3).permutation(np.arange(20, dtype=np.float32))
        classes = engine.FixedScale(minimum=0, value_range=19).classes(raw)
        top = engine.TopShare.from_classes(classes)
        np.testing.assert_array_equal(top.classes(raw), classes)
        self.assertEqual(top.class_counts, {c: int((classes == c).sum()) for c in range(1, 6)})

    def test_top_share_includes_ties_at_the_boundary(self):
        top = engine.TopShare({1: 6, 2: 0, 3: 0, 4: 2, 5: 0})
        raw = np.array([0.1, 0.2, 0.3, 0.5, 0.5, 0.5, 0.2, 0.1], dtype=np.float32)
        high = top.high_plus(raw)
        np.testing.assert_array_equal(high, raw == np.float32(0.5))
        self.assertEqual(int(high.sum()), 3)
        self.assertFalse(top.very_high(raw).any())

    def test_top_share_combined_call_matches_separate_sets(self):
        raw = np.random.default_rng(5).random(50, dtype=np.float32)
        top = engine.TopShare({1: 20, 2: 10, 3: 10, 4: 7, 5: 3})
        high, very = top.high_and_very_high(raw)
        np.testing.assert_array_equal(high, top.high_plus(raw))
        np.testing.assert_array_equal(very, top.very_high(raw))
        self.assertEqual((int(high.sum()), int(very.sum())), (10, 3))

    def test_top_share_rejects_bad_counts_and_lengths(self):
        with self.assertRaises(ValueError):
            engine.TopShare({1: 1, 2: 1, 3: 1, 4: 1})
        with self.assertRaises(ValueError):
            engine.TopShare({1: 1, 2: 1, 3: 1, 4: 1, 5: -1})
        with self.assertRaises(ValueError):
            engine.TopShare({1: 2, 2: 0, 3: 0, 4: 1, 5: 1}).high_plus(np.zeros(3, dtype=np.float32))

    def test_baseline_reproduction_guard(self):
        s = stack()
        raw = s.raw(s.baseline_mapping())
        classes = engine.FixedScale().classes(raw)
        verified = engine.verify_baseline_reproduction(s, raw.copy(), classes)
        self.assertTrue(verified.metadata["baseline_raw_bit_exact"])
        np.testing.assert_array_equal(verified.baseline_classes, classes)
        changed = raw.copy()
        changed[0] = np.nextafter(changed[0], np.float32(2))
        with self.assertRaises(ValueError):
            engine.verify_baseline_reproduction(s, changed, classes)
        wrong = classes.copy()
        wrong[0] = 1 if wrong[0] != 1 else 2
        with self.assertRaises(ValueError):
            engine.verify_baseline_reproduction(s, raw, wrong)
        with self.assertRaises(ValueError):
            engine.verify_baseline_reproduction(s, raw.astype(np.float64), classes)


def brute_force_jenks(values, weights, classes):
    """Smallest within-class squared deviation over every contiguous partition."""
    from itertools import combinations
    x, w = np.asarray(values, float), np.asarray(weights, float)

    def ssd(part_x, part_w):
        mean = (part_w * part_x).sum() / part_w.sum()
        return float((part_w * (part_x - mean) ** 2).sum())
    best = None
    for cuts in combinations(range(1, x.size), classes - 1):
        edges = (0, *cuts, x.size)
        cost = sum(ssd(x[a:b], w[a:b]) for a, b in zip(edges, edges[1:]))
        if best is None or cost < best[0] - 1e-12:
            best = (cost, cuts)
    return best


@TIER.skip_unless_available
class AlternativeBreaks(unittest.TestCase):
    def test_quantile_breaks_are_observed_values_with_equal_shares(self):
        raw = (np.arange(1, 101, dtype=np.float32) * np.float32(0.004) + np.float32(0.029))
        quantile = engine.QuantileBreaks.fit(raw)
        norm = engine.FixedScale().normalized(raw)
        self.assertTrue(all(b in set(norm.tolist()) for b in quantile.breaks))
        self.assertEqual(np.bincount(quantile.classes(raw), minlength=6)[1:].tolist(), [20] * 5)
        self.assertEqual(int(quantile.high_plus(raw).sum()), 40)
        self.assertEqual(int(quantile.very_high(raw).sum()), 20)

    def test_break_value_belongs_to_upper_class(self):
        scale = engine.FixedScale()
        raw = np.array([0.4, 0.6], dtype=np.float32) * scale.range + scale.minimum
        norm = scale.normalized(raw)
        quantile = engine.QuantileBreaks((0.1, float(norm[0]), float(norm[1]), 0.99), scale)
        self.assertEqual(quantile.classes(raw).tolist(), [3, 4])
        self.assertEqual(quantile.high_plus(raw).tolist(), [False, True])

    def test_quantile_rejects_bad_breaks(self):
        for bad in ((0.2, 0.4, 0.6), (0.2, 0.2, 0.6, 0.8), (0.8, 0.6, 0.4, 0.2)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                engine.QuantileBreaks(bad)
        with self.assertRaises(ValueError):
            engine.QuantileBreaks.fit(np.zeros(4, dtype=np.float32))

    def test_fisher_jenks_equals_brute_force(self):
        rng = np.random.default_rng(3)
        for trial in range(6):
            values = np.sort(rng.choice(np.arange(40), size=9, replace=False)).astype(float)
            weights = rng.integers(1, 20, size=9).astype(float)
            cuts, gvf = engine.fisher_jenks(values, weights, 4)
            cost, expected = brute_force_jenks(values, weights, 4)
            with self.subTest(trial=trial):
                self.assertEqual(cuts, expected)
                mean = (weights * values).sum() / weights.sum()
                self.assertAlmostEqual(gvf, 1 - cost / float((weights * (values - mean) ** 2).sum()), places=12)

    def test_fisher_jenks_separates_obvious_groups(self):
        values = np.array([1, 2, 3, 20, 21, 40, 41, 60, 80, 81], float)
        cuts, gvf = engine.fisher_jenks(values, np.ones(10), 5)
        self.assertEqual(cuts, (3, 5, 7, 8))
        self.assertGreater(gvf, 0.99)

    def test_fisher_jenks_rejects_invalid_input(self):
        for values, weights in (([1, 2, 3], [1, 1, 1]), ([1, 1, 2, 3, 4], [1] * 5), ([1, 2, 3, 4, 5], [1, 1, 0, 1, 1])):
            with self.subTest(values=values), self.assertRaises(ValueError):
                engine.fisher_jenks(values, weights, 5)

    def test_score_bins_floor_and_last_bin(self):
        self.assertEqual(engine.score_bins(np.array([0.0, 0.0009, 0.001, 0.5, 0.9999, 1.0]), 1000).tolist(),
                         [0, 0, 1, 500, 999, 999])

    def test_natural_breaks_fit_matches_weighted_bins_and_classes_follow_bins(self):
        scale = engine.FixedScale()
        norm = np.concatenate([np.full(30, 0.105), np.full(20, 0.305), np.full(10, 0.505), np.full(5, 0.705), np.full(2, 0.905)])
        raw = (norm.astype(np.float32) * scale.range + scale.minimum).astype(np.float32)
        natural = engine.NaturalBreaks.fit(raw, bins=100)
        bins = engine.score_bins(scale.normalized(raw), 100)
        self.assertEqual(natural.break_bins, tuple(int(b) for b in sorted(set(bins.tolist()))[1:]))
        self.assertEqual(np.bincount(natural.classes(raw), minlength=6)[1:].tolist(), [30, 20, 10, 5, 2])
        self.assertEqual(int(natural.high_plus(raw).sum()), 7)
        self.assertEqual(int(natural.very_high(raw).sum()), 2)
        self.assertAlmostEqual(natural.gvf, 1.0)
        self.assertEqual(natural.breaks, tuple(b / 100 for b in natural.break_bins))

    def test_natural_breaks_is_deterministic(self):
        raw = stack(n=300).raw(WEIGHTS)
        first, second = engine.NaturalBreaks.fit(raw), engine.NaturalBreaks.fit(raw.copy())
        self.assertEqual((first.break_bins, first.gvf), (second.break_bins, second.gvf))

    def test_natural_breaks_rejects_bad_bins(self):
        for bad in ((0, 10, 20, 30), (10, 10, 20, 30), (10, 20, 30, 1000), (10, 20, 30)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                engine.NaturalBreaks(bad, bins=1000)


@TIER.skip_unless_available
class ComparisonsAndRanks(unittest.TestCase):
    def test_average_and_competition_ranks_with_ties(self):
        np.testing.assert_array_equal(engine.average_ranks([3, 1, 3, 0]), [1.5, 3, 1.5, 4])
        np.testing.assert_array_equal(engine.competition_ranks([3, 1, 3, 0, 0]), [1, 3, 1, 4, 4])

    def test_spearman_known_values_and_constant_side(self):
        self.assertAlmostEqual(engine.spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
        self.assertAlmostEqual(engine.spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
        self.assertIsNone(engine.spearman([1, 1, 1], [1, 2, 3]))

    def test_top_names_keep_district_order_for_ties(self):
        self.assertEqual(engine.top_names([1, 5, 5, 0], ["a", "b", "c", "d"], 3), ["b", "c", "a"])

    def test_compare_retention_jaccard_and_districts(self):
        s = stack()
        base = np.zeros(12, dtype=bool)
        base[[0, 1, 4, 5]] = True
        high = np.zeros(12, dtype=bool)
        high[[0, 1, 8, 9]] = True
        result = engine.compare(high, base, s)
        self.assertEqual((result["high_cells"], result["retention"], result["jaccard"]), (4, 0.5, 2 / 6))
        self.assertAlmostEqual(result["delta_area_km2"], 0)
        np.testing.assert_allclose(result["district_areas_km2"], [0.02, 0, 0.02])
        self.assertEqual(result["top5"], ["İlçe 1", "İlçe 3", "İlçe 2"])

    def test_run_scenario_uses_classifier(self):
        s = stack()
        top = engine.TopShare({1: 6, 2: 2, 3: 1, 4: 2, 5: 1})
        result = engine.run_scenario(s, engine.Scenario("base", s.baseline_mapping()), top)
        self.assertEqual((int(result.high_plus.sum()), int(result.very_high.sum())), (3, 1))
        self.assertEqual(result.raw.dtype, np.float32)

    def test_engine_has_no_write_path(self):
        source = Path(engine.__file__).read_text(encoding="utf-8")
        for token in (".write(", "write_bytes", "write_text", "GA_Update", "Create(", "unlink", "mkdir", "WriteArray", '"w"', "'w'"):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
