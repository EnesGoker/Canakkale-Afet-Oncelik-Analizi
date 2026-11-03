#!/usr/bin/env python3
"""Weight perturbation of the frozen canonical MCDA: OAT steps and Dirichlet sampling.

Main measure (top_share): in every sample the cells holding the baseline
high-plus share (classes 4-5; class 5 by its own share) are selected by rank,
ties included. The high-plus area is therefore constant by definition and
P(high-plus) measures how stable the location is, not how large the area is.
Supplementary measure (fixed_scale): the canonical fixed scale and thresholds,
whose area changes mix level shifts with location changes; tables only.

Default --check recomputes everything from the canonical stack and the stored
weight samples and compares every saved cell, row and provenance field without
writing. --generate requires an explicit empty/new directory and never replaces
files. GIS dependencies are imported lazily, so --help needs standard Python only.
"""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = Path("config/weight_perturbation_v1.json")
COUNT_FILE = "high_plus_probability_count_32635.tif"
WEIGHTS_TABLE = "weight_samples.csv"
OAT_TABLE = "oat_summary.csv"
BRIDGE_TABLE = "scenario_bridge.csv"
MONTE_CARLO_TABLE = "monte_carlo_summary.csv"
KAPPA_TABLE = "kappa_summary.csv"
PROBABILITY_TABLE = "probability_area_summary.csv"
RANK_TABLE = "district_rank_stability.csv"
CONVERGENCE_TABLE = "convergence.csv"
MANIFEST_FILE = "weight_perturbation_manifest.json"
TABLE_FILES = (WEIGHTS_TABLE, OAT_TABLE, BRIDGE_TABLE, MONTE_CARLO_TABLE, KAPPA_TABLE, PROBABILITY_TABLE, RANK_TABLE, CONVERGENCE_TABLE)
OUTPUT_FILES = (COUNT_FILE, *TABLE_FILES, MANIFEST_FILE)
NODATA = 65535
NORMALIZATIONS = ("top_share", "fixed_scale")
BRIDGE_SCENARIOS = ("baseline", "earthquake-heavy", "equal-weight")
PUBLISHED = "published_v1"
SUMMARY_METRICS = ("high_area_km2", "very_high_pixel_count", "baseline_high_retention", "jaccard",
                   "spearman_rho", "spearman_rho_baseline_positive", "tie_excess_pixel_count")
QUANTILES = (("min", 0.0), ("p05", 0.05), ("p25", 0.25), ("median", 0.5), ("p75", 0.75), ("p95", 0.95), ("max", 1.0))
COMPARISON_METRICS = ("high_pixel_count", "high_area_km2", "delta_high_area_km2", "very_high_pixel_count",
                      "baseline_high_retention", "jaccard", "spearman_rho", "spearman_rho_baseline_positive",
                      "top5_districts", "top5_same_order", "top5_same_set")
MONTE_CARLO_COLUMNS = ("kappa", "normalization", "metric", "samples", "mean", *(name for name, _ in QUANTILES))
KAPPA_COLUMNS = ("kappa", "normalization", "samples", "expected_high_area_km2", "p_gt_0_area_km2", "p_ge_050_area_km2",
                 "p_ge_090_area_km2", "baseline_high_share_p_ge_050", "baseline_high_share_p_ge_090", "max_tie_excess_pixel_count",
                 "top5_same_set_share", "top5_same_order_share")
PROBABILITY_COLUMNS = ("scope", "district_id", "district_name", "aoi_cell_count", "aoi_area_km2", "probability_class",
                       "probability_range", "pixel_count", "area_km2", "share_of_scope_aoi_percent",
                       "baseline_high_pixel_count", "share_of_scope_baseline_high_percent")
RANK_COLUMNS = ("kappa", "normalization", "district_id", "district_name", "baseline_high_area_km2", "baseline_rank",
                "median_rank", "rank_q25", "rank_q75", "top1_share", "top3_share", "top5_share",
                "high_area_km2_p05", "high_area_km2_median", "high_area_km2_p95")
CONVERGENCE_COLUMNS = ("kappa", "normalization", "samples", "reference_samples", "max_abs_difference",
                       "p99_abs_difference_open_cells", "p_ge_050_area_km2", "p_ge_090_area_km2",
                       "p_ge_050_area_relative_change", "meets_criterion")


def _np():
    import numpy as np
    return np


def load_config(path: Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    kappas, samples = config.get("kappas"), config.get("samples")
    convergence = config.get("convergence", {})
    if config.get("format_version") != 1 or not isinstance(kappas, list) or not kappas or len(set(kappas)) != len(kappas):
        raise ValueError("Unsupported perturbation config or kappa list")
    if not all(isinstance(k, int) and k > 0 for k in kappas) or config.get("main_kappa") not in kappas:
        raise ValueError("Kappas must be positive integers and include the main kappa")
    if not isinstance(samples, int) or not 1 <= samples < NODATA:
        raise ValueError("The sample count must fit the UInt16 count raster")
    if convergence.get("kappa") not in kappas or not isinstance(convergence.get("reference_samples"), int) \
            or convergence["reference_samples"] < samples or convergence["reference_samples"] >= NODATA:
        raise ValueError("Convergence needs a known kappa and at least as many reference samples")
    snapshots = convergence.get("snapshots")
    if not isinstance(snapshots, list) or not snapshots or snapshots != sorted(set(snapshots)) or snapshots[-1] > convergence["reference_samples"] \
            or samples not in snapshots:
        raise ValueError("Convergence snapshots must increase, include the sample count and stay within the reference")
    steps = config.get("oat_steps")
    if not isinstance(steps, list) or not steps or any(not isinstance(s, float) or s == 0 or s <= -1 for s in steps):
        raise ValueError("OAT steps must be nonzero fractions greater than -1")
    edges = config.get("probability_class_edges")
    if not isinstance(edges, list) or not edges or edges != sorted(set(edges)) or not all(0 < e < 1 for e in edges):
        raise ValueError("Probability class edges must increase strictly within (0, 1)")
    if config.get("normalizations") != {"main": "top_share", "supplementary": "fixed_scale"}:
        raise ValueError("Main top_share and supplementary fixed_scale normalizations are required")
    return config


def sample_weights(config: dict, base_weights) -> dict:
    """Dirichlet rows per kappa, from numpy.random.default_rng([seed, kappa])."""
    np = _np()
    base = np.asarray(base_weights, dtype=np.float64)
    convergence = config["convergence"]
    result = {}
    for kappa in config["kappas"]:
        rows = convergence["reference_samples"] if kappa == convergence["kappa"] else config["samples"]
        result[kappa] = np.random.default_rng([config["seed"], kappa]).dirichlet(kappa * base, size=rows)
    return result


def oat_weights(base: dict, criterion: str, step: float) -> dict:
    """Scale one weight by (1 + step) and the others proportionally to keep the sum at one."""
    old = base[criterion]
    new = old * (1 + step)
    if not 0 <= new <= 1 or old >= 1:
        raise ValueError(f"OAT step leaves [0, 1]: {criterion} {step}")
    scale = (1 - new) / (1 - old)
    weights = {key: (new if key == criterion else value * scale) for key, value in base.items()}
    if not math.isclose(math.fsum(weights.values()), 1.0, rel_tol=0, abs_tol=1e-12):
        raise ValueError("OAT weights do not sum to one")
    return weights


def probability_classes(counts, samples: int, edges) -> "np.ndarray":
    """0 for P = 0; else 1 + number of edges e with P >= e, using exact integer arithmetic."""
    np = _np()
    counts = np.asarray(counts, dtype=np.int64)
    if counts.min() < 0 or counts.max() > samples:
        raise ValueError("Counts must lie within 0..samples")
    result = (counts > 0).astype(np.uint8)
    for edge in edges:
        fraction = Fraction(str(edge))
        result += (counts * fraction.denominator >= fraction.numerator * samples) & (counts > 0)
    return result


def probability_labels(edges) -> list[str]:
    text = [format(edge, "g") for edge in edges]
    return ["P = 0", f"0 < P < {text[0]}", *[f"{a} <= P < {b}" for a, b in zip(text, text[1:])], f"P >= {text[-1]}"]


def classifiers(stack):
    from mcda_scenario_engine import FixedScale, TopShare
    return {"top_share": TopShare.from_classes(stack.baseline_classes), "fixed_scale": FixedScale()}


def comparison_row(stack, analysis: str, scenario_id: str, criterion, delta, normalization: str, weights: dict,
                   high, very_high, baseline: dict) -> dict:
    from mcda_scenario_engine import compare
    result = compare(high, baseline["high"], stack, baseline["areas"])
    row = {"analysis": analysis, "scenario_id": scenario_id, "criterion_id": criterion, "delta": delta,
           "normalization": normalization, **{f"weight_{key}": float(weights[key]) for key in stack.criterion_ids},
           "high_pixel_count": result["high_cells"], "high_area_km2": result["high_area_km2"],
           "delta_high_area_km2": result["delta_area_km2"], "very_high_pixel_count": int(very_high.sum()),
           "baseline_high_retention": result["retention"], "jaccard": result["jaccard"],
           "spearman_rho": result["spearman_rho"], "spearman_rho_baseline_positive": result["spearman_rho_baseline_positive"],
           "top5_districts": ";".join(result["top5"]), "top5_same_order": result["top5"] == baseline["top5"],
           "top5_same_set": set(result["top5"]) == set(baseline["top5"])}
    return row


def comparison_columns(stack) -> tuple[str, ...]:
    return ("analysis", "scenario_id", "criterion_id", "delta", "normalization",
            *(f"weight_{key}" for key in stack.criterion_ids), *COMPARISON_METRICS)


def run_samples(stack, weights, models: dict, baseline: dict, snapshots=()):
    """Accumulate high-plus counts per normalization and per-sample district cells and set metrics."""
    np = _np()
    n, count = stack.n_cells, len(stack.districts)
    counts = {name: np.zeros(n, dtype=np.uint16) for name in models}
    records = {name: {"high": [], "very_high": [], "kept": [], "districts": []} for name in models}
    saved, wanted = {}, set(snapshots)
    for index, row in enumerate(weights, 1):
        raw = stack.raw([float(value) for value in row])
        for name, model in models.items():
            high, very_high = model.high_and_very_high(raw)
            counts[name] += high
            record = records[name]
            record["high"].append(int(high.sum()))
            record["very_high"].append(int(very_high.sum()))
            record["kept"].append(int((high & baseline["high"]).sum()))
            record["districts"].append(np.bincount(stack.district_ids[high], minlength=count + 1)[1:count + 1])
        if index in wanted:
            saved[index] = {name: value.copy() for name, value in counts.items()}
    for record in records.values():
        for key in ("high", "very_high", "kept"):
            record[key] = np.asarray(record[key], dtype=np.int64)
        record["districts"] = np.vstack(record["districts"]).astype(np.int64)
    return counts, records, saved


def sample_metrics(stack, records: dict, baseline: dict, top_share_cells: int) -> dict:
    from mcda_scenario_engine import spearman
    np = _np()
    base_n = int(baseline["high"].sum())
    base_areas = baseline["areas"]
    positive = base_areas > 0
    metrics = {}
    for name, record in records.items():
        areas = record["districts"] * stack.pixel_area_km2
        union = record["high"] + base_n - record["kept"]
        metrics[name] = {
            "high_area_km2": record["high"] * stack.pixel_area_km2,
            "very_high_pixel_count": record["very_high"].astype(np.float64),
            "baseline_high_retention": record["kept"] / base_n,
            "jaccard": np.where(union > 0, record["kept"] / np.maximum(union, 1), np.nan),
            "spearman_rho": np.array([np.nan if (v := spearman(a, base_areas)) is None else v for a in areas]),
            "spearman_rho_baseline_positive": np.array([np.nan if (v := spearman(a[positive], base_areas[positive])) is None else v for a in areas]),
        }
        if name == "top_share":
            metrics[name]["tie_excess_pixel_count"] = (record["high"] - top_share_cells).astype(np.float64)
    return metrics


def summary_rows(kappa: int, metrics: dict) -> list[dict]:
    np = _np()
    rows = []
    for name in NORMALIZATIONS:
        for metric in SUMMARY_METRICS:
            if metric not in metrics[name]:
                continue
            values = metrics[name][metric]
            defined = values[np.isfinite(values)]
            row = {"kappa": kappa, "normalization": name, "metric": metric, "samples": int(defined.size),
                   "mean": float(defined.mean()) if defined.size else None}
            for label, q in QUANTILES:
                row[label] = float(np.quantile(defined, q)) if defined.size else None
            rows.append(row)
    return rows


def kappa_rows(kappa: int, stack, counts: dict, records: dict, samples: int, baseline: dict, top_share_cells: int) -> list[dict]:
    from mcda_scenario_engine import top_names
    np = _np()
    rows = []
    base = baseline["high"]
    names = [d["district_name"] for d in stack.districts]
    for name in NORMALIZATIONS:
        tops = [top_names(cells, names) for cells in records[name]["districts"]]
        count = counts[name].astype(np.int64)
        half, ninety = 2 * count >= samples, 10 * count >= 9 * samples
        rows.append({"kappa": kappa, "normalization": name, "samples": samples,
                     "expected_high_area_km2": int(count.sum()) / samples * stack.pixel_area_km2,
                     "p_gt_0_area_km2": int((count > 0).sum()) * stack.pixel_area_km2,
                     "p_ge_050_area_km2": int(half.sum()) * stack.pixel_area_km2,
                     "p_ge_090_area_km2": int(ninety.sum()) * stack.pixel_area_km2,
                     "baseline_high_share_p_ge_050": int((half & base).sum()) / int(base.sum()),
                     "baseline_high_share_p_ge_090": int((ninety & base).sum()) / int(base.sum()),
                     "max_tie_excess_pixel_count": int(records[name]["high"].max() - top_share_cells) if name == "top_share" else None,
                     "top5_same_set_share": sum(set(t) == set(baseline["top5"]) for t in tops) / len(tops),
                     "top5_same_order_share": sum(t == baseline["top5"] for t in tops) / len(tops)})
    return rows


def rank_rows(kappa: int, stack, records: dict, baseline: dict) -> list[dict]:
    from mcda_scenario_engine import competition_ranks
    np = _np()
    rows = []
    base_ranks = competition_ranks(baseline["areas"])
    for name in NORMALIZATIONS:
        cells = records[name]["districts"]
        ranks = np.vstack([competition_ranks(row) for row in cells])
        areas = cells * stack.pixel_area_km2
        for index, district in enumerate(stack.districts):
            column = ranks[:, index]
            rows.append({"kappa": kappa, "normalization": name, "district_id": district["district_id"],
                         "district_name": district["district_name"], "baseline_high_area_km2": float(baseline["areas"][index]),
                         "baseline_rank": int(base_ranks[index]), "median_rank": float(np.median(column)),
                         "rank_q25": float(np.quantile(column, .25)), "rank_q75": float(np.quantile(column, .75)),
                         "top1_share": float((column <= 1).mean()), "top3_share": float((column <= 3).mean()),
                         "top5_share": float((column <= 5).mean()),
                         "high_area_km2_p05": float(np.quantile(areas[:, index], .05)),
                         "high_area_km2_median": float(np.median(areas[:, index])),
                         "high_area_km2_p95": float(np.quantile(areas[:, index], .95))})
    return rows


def probability_rows(stack, counts, samples: int, edges, baseline_high) -> list[dict]:
    np = _np()
    classes = probability_classes(counts, samples, edges)
    labels = probability_labels(edges)
    rows = []
    scopes = [("province", 0, "Çanakkale", np.ones(stack.n_cells, dtype=bool)),
              *[("district", d["district_id"], d["district_name"], stack.district_ids == d["district_id"]) for d in stack.districts]]
    for scope, district_id, name, mask in scopes:
        scope_n = int(mask.sum())
        base_n = int((baseline_high & mask).sum())
        for value, label in enumerate(labels):
            selected = mask & (classes == value)
            cells = int(selected.sum())
            base_cells = int((selected & baseline_high).sum())
            rows.append({"scope": scope, "district_id": district_id, "district_name": name, "aoi_cell_count": scope_n,
                         "aoi_area_km2": scope_n * stack.pixel_area_km2, "probability_class": value, "probability_range": label,
                         "pixel_count": cells, "area_km2": cells * stack.pixel_area_km2,
                         "share_of_scope_aoi_percent": cells / scope_n * 100, "baseline_high_pixel_count": base_cells,
                         "share_of_scope_baseline_high_percent": base_cells / base_n * 100 if base_n else None})
    for value in range(len(labels)):
        province = next(r for r in rows if r["scope"] == "province" and r["probability_class"] == value)
        for field in ("pixel_count", "baseline_high_pixel_count"):
            if sum(r[field] for r in rows if r["scope"] == "district" and r["probability_class"] == value) != province[field]:
                raise ValueError("District/province probability cell conservation failed")
    return rows


def convergence_rows(stack, kappa: int, saved: dict, config: dict) -> list[dict]:
    np = _np()
    settings = config["convergence"]
    reference = settings["reference_samples"]
    limit_p99, limit_area = settings["p99_abs_difference_limit"], settings["p_ge_050_area_relative_change_limit"]
    rows = []
    for name in NORMALIZATIONS:
        final = saved[reference][name].astype(np.int64)
        p_ref = final / reference
        open_cells = (final > 0) & (final < reference)
        area_ref = int((2 * final >= reference).sum()) * stack.pixel_area_km2
        for samples in (*settings["snapshots"], reference):
            count = saved[samples][name].astype(np.int64)
            area = int((2 * count >= samples).sum()) * stack.pixel_area_km2
            row = {"kappa": kappa, "normalization": name, "samples": samples, "reference_samples": reference,
                   "max_abs_difference": None, "p99_abs_difference_open_cells": None,
                   "p_ge_050_area_km2": area, "p_ge_090_area_km2": int((10 * count >= 9 * samples).sum()) * stack.pixel_area_km2,
                   "p_ge_050_area_relative_change": None, "meets_criterion": None}
            if samples != reference:
                difference = np.abs(count / samples - p_ref)
                row["max_abs_difference"] = float(difference.max())
                row["p99_abs_difference_open_cells"] = float(np.percentile(difference[open_cells], 99)) if open_cells.any() else 0.0
                row["p_ge_050_area_relative_change"] = (area - area_ref) / area_ref if area_ref else None
                row["meets_criterion"] = bool(row["p99_abs_difference_open_cells"] <= limit_p99 and row["p_ge_050_area_relative_change"] is not None
                                              and abs(row["p_ge_050_area_relative_change"]) <= limit_area)
            rows.append(row)
    return rows


def analyze(stack, config: dict, weights: dict, published_classes: dict, scenario_weights: dict) -> dict:
    """All perturbation tables and the main count vector from a verified canonical stack."""
    np = _np()
    from mcda_scenario_engine import district_areas, top_names
    models = classifiers(stack)
    count_districts = len(stack.districts)
    names = [d["district_name"] for d in stack.districts]
    base_high = stack.baseline_classes >= 4
    base_areas = district_areas(base_high, stack.district_ids, count_districts, stack.pixel_area_km2)
    baseline = {"high": base_high, "areas": base_areas, "top5": top_names(base_areas, names)}
    top_share_cells = models["top_share"].at_least[4]
    base_weights = stack.baseline_mapping()

    oat, bridge = [], []
    for criterion in stack.criterion_ids:
        for step in config["oat_steps"]:
            w = oat_weights(base_weights, criterion, step)
            raw = stack.raw(w)
            for name in NORMALIZATIONS:
                high, very_high = models[name].high_and_very_high(raw)
                oat.append(comparison_row(stack, "oat", f"oat:{criterion}:{step:+.2f}", criterion, step, name, w, high, very_high, baseline))
    for scenario_id in BRIDGE_SCENARIOS:
        w = scenario_weights[scenario_id]
        classes = np.asarray(published_classes[scenario_id])
        bridge.append(comparison_row(stack, "scenario_bridge", scenario_id, None, None, PUBLISHED, w, classes >= 4, classes == 5, baseline))
        raw = stack.raw(w)
        for name in NORMALIZATIONS:
            high, very_high = models[name].high_and_very_high(raw)
            bridge.append(comparison_row(stack, "scenario_bridge", scenario_id, None, None, name, w, high, very_high, baseline))

    samples = config["samples"]
    convergence = config["convergence"]
    monte, kappas, ranks, main_count, converge = [], [], [], None, []
    for kappa in config["kappas"]:
        table = weights[kappa]
        snapshots = (*convergence["snapshots"], convergence["reference_samples"]) if kappa == convergence["kappa"] else ()
        counts, records, saved = run_samples(stack, table, models, baseline, snapshots)
        if kappa == convergence["kappa"]:
            converge = convergence_rows(stack, kappa, saved, config)
            counts = saved[samples]
            records = {name: {key: value[:samples] for key, value in record.items()} for name, record in records.items()}
        if any(int(value.max()) > samples for value in counts.values()):
            raise ValueError("Counts exceed the sample count")
        monte += summary_rows(kappa, sample_metrics(stack, records, baseline, top_share_cells))
        kappas += kappa_rows(kappa, stack, counts, records, samples, baseline, top_share_cells)
        ranks += rank_rows(kappa, stack, records, baseline)
        if kappa == config["main_kappa"]:
            main_count = counts["top_share"].copy()
    decisive = next(r for r in converge if r["normalization"] == "top_share" and r["samples"] == samples)
    weight_rows = []
    for kappa in config["kappas"]:
        for index, row in enumerate(weights[kappa], 1):
            weight_rows.append({"kappa": kappa, "sample_id": index, "role": "main" if index <= samples else "convergence_only",
                                **{key: float(value) for key, value in zip(stack.criterion_ids, row)}})
    return {"n_cells": stack.n_cells, "aoi": stack.aoi, "grid": stack.grid, "projection": stack.projection,
            "pixel_area_km2": stack.pixel_area_km2, "criterion_ids": stack.criterion_ids,
            "count": main_count, "samples": samples, "config": config,
            "class_counts": models["top_share"].class_counts, "baseline_top5": baseline["top5"],
            "baseline_district_areas_km2": {name: float(value) for name, value in zip(names, base_areas)},
            "convergence_verdict": {"samples": samples, "reference_samples": convergence["reference_samples"],
                                    "p99_abs_difference_open_cells": decisive["p99_abs_difference_open_cells"],
                                    "p_ge_050_area_relative_change": decisive["p_ge_050_area_relative_change"],
                                    "passed": decisive["meets_criterion"]},
            "tables": {WEIGHTS_TABLE: (weight_rows, ("kappa", "sample_id", "role", *stack.criterion_ids)),
                       OAT_TABLE: (oat, comparison_columns(stack)), BRIDGE_TABLE: (bridge, comparison_columns(stack)),
                       MONTE_CARLO_TABLE: (monte, MONTE_CARLO_COLUMNS), KAPPA_TABLE: (kappas, KAPPA_COLUMNS),
                       PROBABILITY_TABLE: (probability_rows(stack, main_count, samples, config["probability_class_edges"], base_high), PROBABILITY_COLUMNS),
                       RANK_TABLE: (ranks, RANK_COLUMNS), CONVERGENCE_TABLE: (converge, CONVERGENCE_COLUMNS)},
            "metadata": dict(stack.metadata)}


def read_weight_table(path: Path, config: dict, criterion_ids) -> dict:
    np = _np()
    with Path(path).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["kappa", "sample_id", "role", *criterion_ids]:
            raise ValueError("Saved weight table columns differ")
        rows = list(reader)
    result = {}
    for kappa in config["kappas"]:
        selected = [row for row in rows if row["kappa"] == str(kappa)]
        if [row["sample_id"] for row in selected] != [str(i) for i in range(1, len(selected) + 1)] or not selected:
            raise ValueError(f"Saved weight table sample IDs differ for kappa {kappa}")
        result[kappa] = np.array([[float(row[key]) for key in criterion_ids] for row in selected], dtype=np.float64)
    if sum(len(v) for v in result.values()) != len(rows):
        raise ValueError("Saved weight table has rows for unknown kappas")
    return result


def analyze_project(root=ROOT, config_path=None, saved_dir=None) -> dict:
    """Load and verify the canonical stack; reproduce the seeded weights; compute every table."""
    os.environ["GDAL_PAM_ENABLED"] = "NO"
    np = _np()
    from analysis_baseline import weight_scenarios
    from generate_scenario_agreement import compute_scenario_classes
    from mcda_scenario_engine import load_canonical
    root = Path(root).resolve()
    config_path = Path(config_path) if config_path else root / DEFAULT_CONFIG
    config = load_config(config_path)
    stack = load_canonical(root)
    if stack.metadata["baseline_id"] != config["baseline_id"]:
        raise ValueError("The perturbation config names another baseline")
    seeded = sample_weights(config, stack.baseline_weights)
    weights, seed_check = seeded, {"seed_reproduced": None}
    if saved_dir is not None:
        saved = read_weight_table(Path(saved_dir) / WEIGHTS_TABLE, config, stack.criterion_ids)
        same = set(saved) == set(seeded) and all(saved[k].shape == seeded[k].shape and np.array_equal(saved[k], seeded[k]) for k in seeded)
        seed_check = {"seed_reproduced": bool(same)}
        weights = saved
    scenarios = weight_scenarios(root)
    loaded = {"criteria": dict(zip(stack.criterion_ids, stack.vectors)), "scenarios": scenarios, "baseline_class": stack.baseline_classes}
    published, _ = compute_scenario_classes(loaded)
    scenario_weights = {name: {row["criterion_id"]: row["weight"] for row in rows} for name, rows in scenarios.items()}
    analysis = analyze(stack, config, weights, published, scenario_weights)
    analysis["seed_check"] = seed_check
    analysis["config_path"] = config_path.resolve().relative_to(root).as_posix() if config_path.resolve().is_relative_to(root) else config_path.name
    analysis["config_sha256"] = hashlib.sha256(config_path.read_bytes()).hexdigest()
    return analysis


def raster_array(analysis):
    np = _np()
    vector = np.asarray(analysis["count"])
    if vector.shape != (int(analysis["aoi"].sum()),) or vector.dtype != np.dtype("uint16") or int(vector.max()) > analysis["samples"]:
        raise ValueError("Invalid probability count vector")
    array = np.full(analysis["aoi"].shape, NODATA, dtype=np.uint16)
    array[analysis["aoi"]] = vector
    return array


def _write_raster(stage: Path, analysis) -> None:
    from osgeo import gdal
    array = raster_array(analysis)
    dataset = gdal.GetDriverByName("GTiff").Create(str(stage / COUNT_FILE), array.shape[1], array.shape[0], 1, gdal.GDT_UInt16,
                                                   options=["COMPRESS=DEFLATE", "ZLEVEL=6", "TILED=YES"])
    if dataset is None:
        raise ValueError("Could not create the staged count GeoTIFF")
    dataset.SetGeoTransform(analysis["grid"])
    dataset.SetProjection(analysis["projection"])
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(NODATA)
    band.SetDescription(f"Samples (of {analysis['samples']}) with the cell in the baseline-share high-plus set; P = count / {analysis['samples']}")
    if band.WriteArray(array) != 0:
        raise ValueError("Could not write the staged count GeoTIFF")
    dataset.FlushCache()
    band = None
    dataset = None


def _manifest(analysis, stage: Path) -> dict:
    import numpy as np
    from osgeo import gdal
    config = analysis["config"]
    outputs = []
    for name in (COUNT_FILE, *TABLE_FILES):
        content = (stage / name).read_bytes()
        outputs.append({"path": name, "size": len(content), "sha256": hashlib.sha256(content).hexdigest()})
    return {
        "format_version": 1, "method": "Weight perturbation of the frozen canonical MCDA: OAT steps and Dirichlet(kappa * baseline weights) samples",
        "config": analysis["config_path"], "config_sha256": analysis["config_sha256"],
        "aoi_cells": analysis["n_cells"], "aoi_rule": "template_equals_1", "pixel_area_km2": analysis["pixel_area_km2"],
        "grid_shape": list(analysis["aoi"].shape), "geotransform": list(analysis["grid"]), "crs_epsg": 32635,
        "criterion_order": list(analysis["criterion_ids"]), "seed": config["seed"], "kappas": config["kappas"],
        "main_kappa": config["main_kappa"], "samples": analysis["samples"],
        "top_share_class_counts": {str(k): v for k, v in analysis["class_counts"].items()},
        "high_plus_definition": {
            "top_share": "Main measure. In each sample the cells holding the baseline class 4-5 cell count are selected by rank of the weighted raw score (k-th largest value, ties included); class 5 likewise by its baseline count. The high-plus area is constant by definition; P(high-plus) measures location stability, not area.",
            "fixed_scale": "Supplementary tables only. Canonical clip((raw - 0.029) / 0.473, 0, 1) and the 0.2/0.4/0.6/0.8 thresholds; area changes mix weight-driven level shifts with location changes.",
            PUBLISHED: "Bridge rows only: the published v1 sensitivity classes (baseline stored canonical classes; alternatives observed min-max per scenario), unchanged."},
        "count_raster": {"path": COUNT_FILE, "kappa": config["main_kappa"], "normalization": "top_share", "dtype": "UInt16",
                         "outside_aoi_nodata": NODATA, "probability": f"count / {analysis['samples']}",
                         "valid_zero_meaning": "The cell is never in the high-plus set; zero is valid AOI data, not NoData"},
        "probability_class_edges": config["probability_class_edges"],
        "baseline_top5_districts": analysis["baseline_top5"], "baseline_district_high_area_km2": analysis["baseline_district_areas_km2"],
        "district_ranking": "Districts ranked by high-plus area (km², descending); ties share the best rank (competition ranking). Spearman rho uses average ranks over all 12 districts and, separately, over the districts with nonzero baseline high-plus area",
        "convergence": analysis["convergence_verdict"],
        "interpretation_limit": "Perturbation explores weight uncertainty around one expert weight set with fixed criterion scores; it is neither an independent validation nor a hazard probability",
        "weights_modified": False, "baseline": analysis["metadata"],
        "software": {"python": sys.version.split()[0], "numpy": np.__version__, "gdal": gdal.VersionInfo("RELEASE_NAME")},
        "outputs": outputs,
    }


def write_outputs(analysis, output_dir) -> list[str]:
    """Stage the complete package, verify it, then exclusively publish each file."""
    from generate_scenario_agreement import _csv_bytes
    if analysis["convergence_verdict"]["passed"] is not True:
        raise ValueError("The convergence criterion is not met; nothing was written")
    contents = {name: _csv_bytes(rows, columns) for name, (rows, columns) in analysis["tables"].items()}
    raster_array(analysis)
    output_dir = Path(output_dir).absolute()
    if output_dir.is_symlink() or (output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir()))):
        raise ValueError("Output directory must be empty or new; content is never overwritten")
    if not output_dir.parent.is_dir():
        raise ValueError("Output directory parent must already exist")
    published, created = [], False
    try:
        with tempfile.TemporaryDirectory(prefix=".weight-perturbation-stage-", dir=output_dir.parent) as temporary:
            stage = Path(temporary)
            for name, content in contents.items():
                (stage / name).write_bytes(content)
            _write_raster(stage, analysis)
            (stage / MANIFEST_FILE).write_text(json.dumps(_manifest(analysis, stage), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
            check = compare_outputs(analysis, stage)
            if not check["passed"]:
                raise ValueError("Staged artifact validation failed: " + "; ".join(check["errors"]))
            try:
                output_dir.mkdir()
                created = True
            except FileExistsError:
                if output_dir.is_symlink() or not output_dir.is_dir() or any(output_dir.iterdir()):
                    raise ValueError("Output directory changed or contains existing content")
            for name in OUTPUT_FILES:
                path = output_dir / name
                os.link(stage / name, path)
                published.append((path, path.stat().st_ino))
    except BaseException:
        for path, inode in reversed(published):
            if path.exists() and path.stat().st_ino == inode:
                path.unlink()
        if created and output_dir.exists() and not any(output_dir.iterdir()):
            output_dir.rmdir()
        raise
    return list(OUTPUT_FILES)


def compare_outputs(analysis, output_dir) -> dict:
    """Compare every saved cell, grid, table value and provenance field."""
    np = _np()
    from osgeo import gdal, osr
    from generate_scenario_agreement import _compare_rows, _read_csv
    report = {"passed": False, "checked_files": 0, "checked_raster_cells": 0, "checked_table_rows": 0, "errors": []}
    output_dir = Path(output_dir)
    try:
        expected = raster_array(analysis)
        for name in OUTPUT_FILES:
            if not (output_dir / name).is_file() or (output_dir / name).is_symlink():
                raise ValueError(f"Missing or symbolic-linked perturbation artifact: {name}")
            report["checked_files"] += 1
        target = osr.SpatialReference()
        target.ImportFromWkt(analysis["projection"])
        dataset = gdal.OpenEx(str(output_dir / COUNT_FILE), gdal.OF_RASTER | gdal.OF_READONLY)
        if dataset is None or dataset.RasterCount != 1 or (dataset.RasterYSize, dataset.RasterXSize) != expected.shape:
            raise ValueError("Saved count raster dimensions differ")
        band = dataset.GetRasterBand(1)
        spatial = osr.SpatialReference()
        if spatial.ImportFromWkt(dataset.GetProjectionRef()) != 0 or not spatial.IsSame(target) \
                or not np.allclose(dataset.GetGeoTransform(), analysis["grid"], atol=1e-9, rtol=0):
            raise ValueError("Saved count raster CRS/grid differs")
        if band.DataType != gdal.GDT_UInt16 or band.GetNoDataValue() != NODATA or not np.array_equal(band.ReadAsArray(), expected):
            raise ValueError("Saved count raster values/type/NoData differ")
        if not np.array_equal(band.GetMaskBand().ReadAsArray() != 0, analysis["aoi"]):
            raise ValueError("Saved count raster validity mask differs")
        report["checked_raster_cells"] += expected.size
        band = None
        dataset = None
        for name, (rows, columns) in analysis["tables"].items():
            fields, _ = _read_csv(output_dir / name)
            if fields != list(columns):
                raise ValueError(f"Saved CSV column order differs: {name}")
            report["checked_table_rows"] += _compare_rows(output_dir / name, rows, tolerance=0 if name == WEIGHTS_TABLE else 1e-10)
        saved = json.loads((output_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
        wanted = _manifest(analysis, output_dir)
        if set(saved) != set(wanted):
            raise ValueError("Saved perturbation manifest fields differ")
        for key, value in wanted.items():
            if key != "software" and saved[key] != value:
                raise ValueError(f"Saved perturbation manifest differs: {key}")
        if not isinstance(saved["software"], dict) or set(saved["software"]) != {"python", "numpy", "gdal"} \
                or not all(isinstance(v, str) and v for v in saved["software"].values()):
            raise ValueError("Saved software provenance is malformed")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, RuntimeError, csv.Error) as error:
        report["errors"].append(str(error))
    report["passed"] = not report["errors"]
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="Read-only recomputation and saved artifact check (default)")
    modes.add_argument("--generate", action="store_true", help="Generate the package in an explicit empty/new output directory")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path, help=f"Default PROJECT_ROOT/{DEFAULT_CONFIG}")
    parser.add_argument("--output-dir", type=Path, help="Check defaults to PROJECT_ROOT/<config output_dir>")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.generate and args.output_dir is None:
        parser.error("--generate requires --output-dir")
    os.environ["GDAL_PAM_ENABLED"] = "NO"
    result = {"passed": False, "mode": "generate" if args.generate else "check", "errors": []}
    code = 1
    try:
        config_path = args.config or args.project_root / DEFAULT_CONFIG
        target = args.output_dir or args.project_root / load_config(config_path)["output_dir"]
        analysis = analyze_project(args.project_root, config_path, None if args.generate else target)
        result.update({"baseline_id": analysis["metadata"]["baseline_id"], "aoi_cells": analysis["n_cells"],
                       "samples": analysis["samples"], "kappas": analysis["config"]["kappas"],
                       "convergence": analysis["convergence_verdict"], **analysis["seed_check"]})
        if args.generate:
            result["generated_files"] = write_outputs(analysis, target)
        else:
            result["artifact_comparison"] = compare_outputs(analysis, target)
            if analysis["seed_check"]["seed_reproduced"] is not True:
                result["errors"].append("Environment: the seeded Dirichlet stream differs from weight_samples.csv; "
                                        "results were verified from the stored weights (see artifact_comparison)")
            if not result["artifact_comparison"]["passed"]:
                result["errors"] += result["artifact_comparison"]["errors"]
            if result["errors"]:
                raise ValueError("; ".join(result["errors"]))
        result["passed"] = True
        code = 0
    except ImportError as error:
        result.update({"dependency_unavailable": True})
        result["errors"].append(f"Required analysis dependency unavailable: {error}")
        code = 2
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, csv.Error) as error:
        if str(error) not in result["errors"] and not result["errors"]:
            result["errors"].append(str(error))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    else:
        print(f"Weight perturbation: {'PASSED' if result['passed'] else 'FAILED'} ({result['mode']})")
        for error in result["errors"]:
            print(error)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
