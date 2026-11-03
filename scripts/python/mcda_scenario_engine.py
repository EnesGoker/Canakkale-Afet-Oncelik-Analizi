#!/usr/bin/env python3
"""Shared read-only MCDA scenario engine: canonical stack, weighted score and classifiers.

The canonical stack is loaded only after the frozen baseline manifest and the
canonical numerical QA pass. The weighted raw score repeats the canonical
expression order (A*w1 + B*w2 + ...) in Float32, applying each weight as a
Python float, so the baseline weights reproduce the frozen raw score bit for
bit; load_canonical() proves this before returning. Nothing here writes files.

Classifiers:
- FixedScale: the canonical fixed scale clip((raw - 0.029) / 0.473, 0, 1) and the
  0.2/0.4/0.6/0.8 thresholds, a threshold value belonging to the upper class.
- TopShare: rank-based classes holding the baseline class cell counts; each
  class boundary is the k-th largest raw value with ties included, so the
  baseline weights reproduce the canonical classes exactly and the high plus
  very-high area is constant by definition (it measures where, not how much).
- QuantileBreaks / NaturalBreaks: alternative thresholds on the same fixed-scale
  score (20 % quantiles; binned exact Fisher-Jenks), fitted once and then fixed.
  They show the effect of the threshold choice; the canonical classes stay
  equal-interval.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import hashlib
import math
from pathlib import Path
import sys
from typing import Mapping, Protocol, Sequence

import numpy as np

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
FIXED_MINIMUM = 0.029
FIXED_RANGE = 0.473
CLASS_THRESHOLDS = (0.2, 0.4, 0.6, 0.8)
HIGH_CLASS = 4
WEIGHT_SUM_TOLERANCE = 1e-6


@dataclass(frozen=True)
class CanonicalStack:
    """AOI-only criterion vectors in mcda_weights.tsv order, plus the district partition."""
    criterion_ids: tuple[str, ...]
    baseline_weights: tuple[float, ...]
    vectors: tuple[np.ndarray, ...]
    aoi: np.ndarray
    district_ids: np.ndarray
    districts: tuple[dict, ...] = ()
    grid: tuple[float, ...] = ()
    projection: str = ""
    pixel_area_km2: float = 0.01
    metadata: dict = field(default_factory=dict)
    baseline_classes: np.ndarray | None = None

    def __post_init__(self):
        n = validate_vectors(self.criterion_ids, self.vectors)
        if self.aoi.dtype != np.dtype(bool) or self.aoi.ndim != 2 or int(self.aoi.sum()) != n:
            raise ValueError("The boolean AOI must hold exactly one cell per vector element")
        ids = np.asarray(self.district_ids)
        if ids.shape != (n,) or ids.dtype.kind not in "iu" or (n and ids.min() < 1):
            raise ValueError("District IDs must be aligned positive integers")
        if self.districts and set(np.unique(ids).tolist()) != {row["district_id"] for row in self.districts}:
            raise ValueError("District IDs and district metadata differ")
        validate_weights(self.criterion_ids, dict(zip(self.criterion_ids, self.baseline_weights)))
        if not math.isfinite(self.pixel_area_km2) or self.pixel_area_km2 <= 0:
            raise ValueError("Pixel area must be positive and finite")

    @property
    def n_cells(self) -> int:
        return int(self.vectors[0].size)

    def baseline_mapping(self) -> dict[str, float]:
        return dict(zip(self.criterion_ids, self.baseline_weights))

    def raw(self, weights, overrides: Mapping[str, np.ndarray] | None = None,
            weight_mask: Mapping[str, np.ndarray] | None = None) -> np.ndarray:
        """Weighted raw score of the AOI cells (Float32, fixed criterion order).

        weights: a mapping by criterion ID, or a sequence in criterion order.
        overrides: replacement or additional criterion vectors (Float32, [0, 1]);
        an additional criterion follows the canonical ones in mapping order.
        weight_mask: boolean coverage per criterion; where a criterion is not
        covered its weight is zero and the cell's remaining weights are scaled by
        1 / (sum of covered weights). Fully covered cells keep the plain sum.
        """
        overrides = dict(overrides or {})
        vectors = dict(zip(self.criterion_ids, self.vectors))
        order = list(self.criterion_ids) + [key for key in overrides if key not in vectors]
        for key, vector in overrides.items():
            validate_vectors((key,), (vector,), self.n_cells)
            vectors[key] = vector
        if not isinstance(weights, Mapping):
            weights = list(weights)
            if len(weights) != len(order):
                raise ValueError("A weight sequence must follow the criterion order exactly")
            weights = dict(zip(order, weights))
        weights = validate_weights(order, weights)
        acc = None
        for key in order:
            term = vectors[key] * float(weights[key])  # Python float keeps Float32 (NEP 50)
            acc = term if acc is None else acc + term
        if acc.dtype != np.dtype("float32"):
            raise ValueError("The weighted score must stay Float32")
        if weight_mask:
            unknown = set(weight_mask) - set(order)
            if unknown:
                raise ValueError(f"Weight mask for unknown criteria: {sorted(unknown)}")
            masks = {}
            for key, mask in weight_mask.items():
                mask = np.asarray(mask)
                if mask.shape != (self.n_cells,) or mask.dtype != np.dtype(bool):
                    raise ValueError(f"{key}: the weight mask must be an aligned boolean vector")
                masks[key] = mask
            partial = ~np.logical_and.reduce(list(masks.values()))
            if partial.any():
                total = np.zeros(int(partial.sum()), dtype=np.float64)
                covered = np.zeros_like(total)
                for key in order:
                    cover = masks[key][partial] if key in masks else np.ones(total.size, dtype=bool)
                    covered += cover * weights[key]
                    total += cover * weights[key] * vectors[key][partial].astype(np.float64)
                if np.any(covered <= 0):
                    raise ValueError("A cell has no covered criterion weight")
                acc = acc.copy()
                acc[partial] = (total / covered).astype(np.float32)
        return acc


def validate_vectors(ids: Sequence[str], vectors: Sequence[np.ndarray], n: int | None = None) -> int:
    if not ids or len(ids) != len(vectors) or len(set(ids)) != len(ids):
        raise ValueError("Unique criterion IDs with one vector each are required")
    for key, vector in zip(ids, vectors):
        if not isinstance(vector, np.ndarray) or vector.dtype != np.dtype("float32") or vector.ndim != 1:
            raise ValueError(f"{key}: a one-dimensional Float32 vector is required")
        if n is None:
            n = vector.size
        if vector.size != n or n == 0:
            raise ValueError(f"{key}: vectors must be nonempty and aligned")
        if not np.isfinite(vector).all() or vector.min() < 0 or vector.max() > 1:
            raise ValueError(f"{key}: finite scores in [0, 1] are required")
    return int(n)


def validate_weights(order: Sequence[str], weights: Mapping[str, float]) -> dict[str, float]:
    if set(weights) != set(order):
        raise ValueError("Weights must name exactly the scenario criteria")
    values = {}
    for key in order:
        value = weights[key]
        if isinstance(value, bool) or not isinstance(value, (int, float, np.floating, np.integer)):
            raise ValueError(f"{key}: a numeric weight is required")
        value = float(value)
        if not math.isfinite(value) or value < 0 or value > 1:
            raise ValueError(f"{key}: weights must be finite and within [0, 1]")
        values[key] = value
    if not math.isclose(math.fsum(values.values()), 1.0, rel_tol=0, abs_tol=WEIGHT_SUM_TOLERANCE):
        raise ValueError("Weights must sum to one")
    return values


class Classifier(Protocol):
    def classes(self, raw: np.ndarray) -> np.ndarray: ...       # uint8 1..5
    def high_plus(self, raw: np.ndarray) -> np.ndarray: ...     # bool, classes 4 and 5


class FixedScale:
    """Canonical fixed scale; a threshold value belongs to the upper class."""
    name = "fixed_scale"

    def __init__(self, minimum: float = FIXED_MINIMUM, value_range: float = FIXED_RANGE,
                 thresholds: Sequence[float] = CLASS_THRESHOLDS):
        if not value_range > 0 or len(thresholds) != 4 or list(thresholds) != sorted(set(thresholds)):
            raise ValueError("A positive range and four increasing thresholds are required")
        self.minimum, self.range = np.float32(minimum), np.float32(value_range)
        self.thresholds = tuple(np.float32(t) for t in thresholds)

    def normalized(self, raw: np.ndarray) -> np.ndarray:
        return np.minimum(np.maximum((raw - self.minimum) / self.range, np.float32(0)), np.float32(1))

    def classes(self, raw: np.ndarray) -> np.ndarray:
        norm = self.normalized(raw)
        result = np.ones(raw.shape, dtype=np.uint8)
        for threshold in self.thresholds:
            result += norm >= threshold
        return result

    def high_plus(self, raw: np.ndarray) -> np.ndarray:
        return self.normalized(raw) >= self.thresholds[HIGH_CLASS - 2]

    def very_high(self, raw: np.ndarray) -> np.ndarray:
        return self.normalized(raw) >= self.thresholds[-1]

    def high_and_very_high(self, raw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        norm = self.normalized(raw)
        return norm >= self.thresholds[HIGH_CLASS - 2], norm >= self.thresholds[-1]


class TopShare:
    """Rank classes holding fixed cell counts; boundaries include ties."""
    name = "top_share"

    def __init__(self, class_counts: Mapping[int, int]):
        if set(class_counts) != {1, 2, 3, 4, 5} or any(int(v) < 0 for v in class_counts.values()):
            raise ValueError("Nonnegative cell counts for classes 1..5 are required")
        self.class_counts = {key: int(class_counts[key]) for key in range(1, 6)}
        self.n = sum(self.class_counts.values())
        # cumulative counts from the top: cells in class >= c
        self.at_least = {c: sum(self.class_counts[k] for k in range(c, 6)) for c in range(2, 6)}

    @classmethod
    def from_classes(cls, classes: np.ndarray) -> "TopShare":
        counts = np.bincount(np.asarray(classes), minlength=6)
        if counts[0] or counts.size != 6:
            raise ValueError("Classes 1..5 are required")
        return cls({c: int(counts[c]) for c in range(1, 6)})

    def threshold(self, raw: np.ndarray, cells: int) -> float | None:
        """k-th largest raw value; None when no cell is selected."""
        if raw.size != self.n:
            raise ValueError("Raw score length differs from the class counts")
        if cells == 0:
            return None
        return raw.dtype.type(np.partition(raw, raw.size - cells)[raw.size - cells])

    def select(self, raw: np.ndarray, at_least: int) -> np.ndarray:
        value = self.threshold(raw, self.at_least[at_least])
        return np.zeros(raw.shape, dtype=bool) if value is None else raw >= value

    def classes(self, raw: np.ndarray) -> np.ndarray:
        result = np.ones(raw.shape, dtype=np.uint8)
        for c in range(2, 6):
            result += self.select(raw, c)
        return result

    def high_plus(self, raw: np.ndarray) -> np.ndarray:
        return self.select(raw, HIGH_CLASS)

    def very_high(self, raw: np.ndarray) -> np.ndarray:
        return self.select(raw, 5)

    def high_and_very_high(self, raw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Both sets from one partition; equal to high_plus() and very_high()."""
        k4, k5 = self.at_least[HIGH_CLASS], self.at_least[5]
        if raw.size != self.n:
            raise ValueError("Raw score length differs from the class counts")
        if k5 == 0 or k4 == 0:
            return self.high_plus(raw), self.very_high(raw)
        values = np.partition(raw, sorted({raw.size - k4, raw.size - k5}))
        return raw >= values[raw.size - k4], raw >= values[raw.size - k5]


class QuantileBreaks:
    """Five classes on the fixed-scale score with breaks at its 20/40/60/80 % quantiles.

    Break q (q = 1..4) is the observed Float32 score at sorted position
    ceil(q * n / 5): classes below it hold ceil(q * n / 5) cells when there are
    no ties. No interpolation; fitted once and then held fixed; a break value
    belongs to the upper class.
    """
    name = "quantile"

    def __init__(self, breaks: Sequence[float], scale: FixedScale | None = None):
        breaks = tuple(np.float32(b) for b in breaks)
        if len(breaks) != 4 or list(breaks) != sorted(set(breaks)):
            raise ValueError("Four strictly increasing breaks are required")
        self.breaks, self.scale = breaks, scale or FixedScale()

    @classmethod
    def fit(cls, raw: np.ndarray, scale: FixedScale | None = None) -> "QuantileBreaks":
        scale = scale or FixedScale()
        values = scale.normalized(np.asarray(raw))
        n = values.size
        if n < 5:
            raise ValueError("Quantile breaks need at least five cells")
        ordered = np.sort(values)
        return cls(tuple(ordered[(q * n + 4) // 5] for q in range(1, 5)), scale)

    def classes(self, raw: np.ndarray) -> np.ndarray:
        norm = self.scale.normalized(raw)
        result = np.ones(raw.shape, dtype=np.uint8)
        for value in self.breaks:
            result += norm >= value
        return result

    def high_plus(self, raw: np.ndarray) -> np.ndarray:
        return self.scale.normalized(raw) >= self.breaks[HIGH_CLASS - 2]

    def very_high(self, raw: np.ndarray) -> np.ndarray:
        return self.scale.normalized(raw) >= self.breaks[-1]


def score_bins(norm: np.ndarray, bins: int) -> np.ndarray:
    """Bin index floor(bins * score) in Float64, the score 1 joining the last bin."""
    index = np.floor(np.asarray(norm, dtype=np.float64) * bins).astype(np.int64)
    return np.clip(index, 0, bins - 1)


def fisher_jenks(values, weights, classes: int = 5) -> tuple[tuple[int, ...], float]:
    """Exact weighted Fisher-Jenks on sorted distinct values.

    Returns the start indices of classes 2..k and the goodness of variance fit
    1 - SDCM / SDAM. Dynamic programming over all contiguous partitions.
    """
    x = np.asarray(values, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    n = x.size
    if x.shape != w.shape or n < classes or classes < 2 or np.any(np.diff(x) <= 0) or np.any(w <= 0):
        raise ValueError("Fisher-Jenks needs at least k strictly increasing values with positive weights")
    cw, cx, cxx = (np.concatenate(([0.0], np.cumsum(a))) for a in (w, w * x, w * x * x))

    def ssd(i, j):  # squared deviations of the values i..j-1 about their weighted mean
        s = cx[j] - cx[i]
        return np.maximum((cxx[j] - cxx[i]) - s * s / (cw[j] - cw[i]), 0.0)

    cost = np.full((classes + 1, n + 1), np.inf)
    start = np.zeros((classes + 1, n + 1), dtype=np.int64)
    cost[0, 0] = 0.0
    for k in range(1, classes + 1):
        for j in range(k, n + 1):
            i = np.arange(k - 1, j)
            total = cost[k - 1, i] + ssd(i, j)
            best = int(np.argmin(total))  # the first minimum keeps ties deterministic
            cost[k, j], start[k, j] = total[best], i[best]
    cuts, j = [], n
    for k in range(classes, 1, -1):
        j = int(start[k, j])
        cuts.append(j)
    total = float(ssd(0, n))
    return tuple(sorted(cuts)), (1.0 - float(cost[classes, n]) / total) if total > 0 else 1.0


class NaturalBreaks:
    """Five natural-break (Fisher-Jenks) classes on the fixed-scale score, binned.

    The score is binned as floor(bins * score); Fisher-Jenks runs exactly on the
    occupied bins weighted by their cell counts, so the result is deterministic
    and needs no sampling. Breaks are bin indices; a cell belongs to the class of
    its bin. The break value reported is the lower edge index / bins.
    """
    name = "natural_breaks"

    def __init__(self, break_bins: Sequence[int], bins: int = 1000, gvf: float | None = None,
                 scale: FixedScale | None = None):
        break_bins = tuple(int(b) for b in break_bins)
        if not isinstance(bins, int) or bins < 5 or len(break_bins) != 4 or list(break_bins) != sorted(set(break_bins)) \
                or break_bins[0] <= 0 or break_bins[-1] >= bins:
            raise ValueError("Four strictly increasing break bins inside (0, bins) are required")
        self.break_bins, self.bins, self.gvf, self.scale = break_bins, bins, gvf, scale or FixedScale()

    @property
    def breaks(self) -> tuple[float, ...]:
        return tuple(b / self.bins for b in self.break_bins)

    @classmethod
    def fit(cls, raw: np.ndarray, bins: int = 1000, scale: FixedScale | None = None) -> "NaturalBreaks":
        scale = scale or FixedScale()
        counts = np.bincount(score_bins(scale.normalized(np.asarray(raw)), bins), minlength=bins)
        occupied = np.flatnonzero(counts)
        cuts, gvf = fisher_jenks(occupied.astype(np.float64), counts[occupied], 5)
        return cls(tuple(int(occupied[c]) for c in cuts), bins, gvf, scale)

    def classes(self, raw: np.ndarray) -> np.ndarray:
        index = score_bins(self.scale.normalized(raw), self.bins)
        result = np.ones(raw.shape, dtype=np.uint8)
        for value in self.break_bins:
            result += index >= value
        return result

    def high_plus(self, raw: np.ndarray) -> np.ndarray:
        return score_bins(self.scale.normalized(raw), self.bins) >= self.break_bins[HIGH_CLASS - 2]

    def very_high(self, raw: np.ndarray) -> np.ndarray:
        return score_bins(self.scale.normalized(raw), self.bins) >= self.break_bins[-1]


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    weights: Mapping[str, float]
    overrides: Mapping[str, np.ndarray] = field(default_factory=dict)
    weight_mask: Mapping[str, np.ndarray] = field(default_factory=dict)


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    raw: np.ndarray
    high_plus: np.ndarray
    very_high: np.ndarray


def run_scenario(stack: CanonicalStack, scenario: Scenario, classifier) -> ScenarioResult:
    raw = stack.raw(scenario.weights, scenario.overrides, scenario.weight_mask)
    return ScenarioResult(scenario.scenario_id, raw, classifier.high_plus(raw), classifier.very_high(raw))


def district_areas(high: np.ndarray, district_ids: np.ndarray, district_count: int, pixel_area_km2: float = 0.01):
    """High-plus area by district ID 1..district_count (km²)."""
    return np.bincount(district_ids[high], minlength=district_count + 1)[1:district_count + 1] * pixel_area_km2


def average_ranks(values) -> np.ndarray:
    """Rank 1 = largest; tied values share their average rank."""
    values = np.asarray(values, dtype=np.float64)
    order = np.argsort(-values, kind="stable")
    ranks = np.empty(values.size, dtype=np.float64)
    ranks[order] = np.arange(1, values.size + 1)
    for value in np.unique(values):
        tied = values == value
        if tied.sum() > 1:
            ranks[tied] = ranks[tied].mean()
    return ranks


def competition_ranks(values) -> np.ndarray:
    """Rank 1 = largest; a tie takes the best rank (1 + number of strictly larger values)."""
    values = np.asarray(values, dtype=np.float64)
    return np.array([1 + int((values > value).sum()) for value in values], dtype=np.int64)


def spearman(first, second) -> float | None:
    """Spearman rho with average ranks; None when either side is constant."""
    a, b = average_ranks(first), average_ranks(second)
    if a.size < 2 or np.all(a == a[0]) or np.all(b == b[0]):
        return None
    return float(np.corrcoef(a, b)[0, 1])


def top_names(areas, names: Sequence[str], limit: int = 5) -> list[str]:
    """Largest areas first; equal areas keep district ID order."""
    order = np.argsort(-np.asarray(areas, dtype=np.float64), kind="stable")
    return [names[i] for i in order[:limit]]


def compare(high: np.ndarray, baseline_high: np.ndarray, stack: CanonicalStack, baseline_district_areas=None) -> dict:
    """Area change, retention, Jaccard and district rank agreement against the baseline set."""
    n_high, n_base = int(high.sum()), int(baseline_high.sum())
    kept = int((high & baseline_high).sum())
    union = n_high + n_base - kept
    count = len(stack.districts)
    names = [row["district_name"] for row in stack.districts]
    areas = district_areas(high, stack.district_ids, count, stack.pixel_area_km2)
    base = district_areas(baseline_high, stack.district_ids, count, stack.pixel_area_km2) if baseline_district_areas is None else baseline_district_areas
    positive = base > 0
    return {"high_cells": n_high, "high_area_km2": n_high * stack.pixel_area_km2,
            "delta_area_km2": (n_high - n_base) * stack.pixel_area_km2,
            "retention": kept / n_base if n_base else None, "jaccard": kept / union if union else None,
            "district_areas_km2": areas, "spearman_rho": spearman(areas, base),
            "spearman_rho_baseline_positive": spearman(areas[positive], base[positive]),
            "top5": top_names(areas, names)}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_canonical(root=ROOT) -> CanonicalStack:
    """Verify the frozen inputs, load the AOI stack and prove bit-exact baseline reproduction."""
    import os
    os.environ["GDAL_PAM_ENABLED"] = "NO"
    from osgeo import gdal
    from analysis_baseline import load_frozen_inputs, OUTPUTS, MANIFEST
    from generate_scenario_agreement import load_district_assignment, validate_grid
    root = Path(root).resolve()
    loaded = load_frozen_inputs(root)
    area = validate_grid(loaded["aoi"], loaded["grid"], loaded["projection"])
    rows = loaded["scenarios"]["baseline"]
    ids, districts = load_district_assignment(root, loaded["aoi"], loaded["grid"], loaded["projection"])
    stack = CanonicalStack(
        criterion_ids=tuple(row["criterion_id"] for row in rows),
        baseline_weights=tuple(float(row["weight"]) for row in rows),
        vectors=tuple(loaded["criteria"][row["criterion_id"]] for row in rows),
        aoi=loaded["aoi"], district_ids=ids.astype(np.int64), districts=tuple(districts),
        grid=tuple(loaded["grid"]), projection=loaded["projection"], pixel_area_km2=area,
        metadata={"baseline_id": loaded["baseline_id"], "baseline_manifest": MANIFEST.as_posix(),
                  "baseline_manifest_sha256": sha256(root / MANIFEST)})
    dataset = gdal.OpenEx(str(root / OUTPUTS[0]), gdal.OF_RASTER | gdal.OF_READONLY)
    stored = dataset.GetRasterBand(1).ReadAsArray()[stack.aoi]
    dataset = None
    return verify_baseline_reproduction(stack, stored, loaded["baseline_class"])


def verify_baseline_reproduction(stack: CanonicalStack, stored_raw: np.ndarray, stored_classes: np.ndarray) -> CanonicalStack:
    """Baseline weights must give the stored raw score bit for bit and the stored classes exactly."""
    raw = stack.raw(stack.baseline_mapping())
    stored_raw = np.asarray(stored_raw)
    if stored_raw.dtype != raw.dtype or stored_raw.shape != raw.shape or not np.array_equal(stored_raw.view(np.uint32), raw.view(np.uint32)):
        raise ValueError("Baseline weights do not reproduce the frozen raw score bit for bit")
    classes = FixedScale().classes(raw)
    if not np.array_equal(classes, np.asarray(stored_classes)):
        raise ValueError("The fixed scale does not reproduce the frozen baseline classes")
    if not np.array_equal(TopShare.from_classes(classes).classes(raw), classes):
        raise ValueError("Rank classes with the baseline counts do not reproduce the baseline classes")
    metadata = {**stack.metadata, "baseline_raw_bit_exact": True, "baseline_classes_exact": True,
                "top_share_reproduces_baseline_classes": True}
    return replace(stack, baseline_classes=classes, metadata=metadata)
