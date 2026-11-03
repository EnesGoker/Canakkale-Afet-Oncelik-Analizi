#!/usr/bin/env python3
"""MCDA variants of the frozen canonical model: flood weight, vegetation merge, alternative thresholds.

Scenario variants change the weights or combine criteria and are compared with
the baseline by the same two measures as the weight perturbation:
- top_share (main): the cells holding the baseline class 4-5 (and class 5) cell
  counts by rank of the weighted raw score; the high-plus area is constant by
  definition, so the comparison measures location.
- fixed_scale (supplementary): the canonical clip((raw - 0.029) / 0.473) scale
  and 0.2/0.4/0.6/0.8 thresholds; area changes include level shifts.

Alternative classification fits quantile and binned natural-break thresholds
on the baseline fixed-scale score only. It shows the effect of the threshold
choice; the canonical equal-interval classes are unchanged.

The flood evidence table records why the meaning of source flood NoData could
not be settled (no modelled-network or coverage layer) and how strongly the
baseline high and very-high classes depend on flood cells.

Default --check recomputes everything and compares every saved row and
provenance field without writing. --generate requires an explicit empty/new
directory and never replaces files. GIS dependencies are imported lazily, so
--help needs standard Python only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = Path("config/mcda_variants_v1.json")
WEIGHTS_TABLE = "variant_weights.csv"
SUMMARY_TABLE = "variant_summary.csv"
DISTRICT_TABLE = "variant_district_areas.csv"
CLASS_SUMMARY_TABLE = "classification_summary.csv"
CLASS_DISTRIBUTION_TABLE = "classification_distribution.csv"
FLOOD_TABLE = "flood_coverage_evidence.csv"
MANIFEST_FILE = "mcda_variants_manifest.json"
TABLE_FILES = (WEIGHTS_TABLE, SUMMARY_TABLE, DISTRICT_TABLE, CLASS_SUMMARY_TABLE, CLASS_DISTRIBUTION_TABLE, FLOOD_TABLE)
OUTPUT_FILES = (*TABLE_FILES, MANIFEST_FILE)
NORMALIZATIONS = ("top_share", "fixed_scale")
METHODS = ("equal_interval", "quantile", "natural_breaks")
BLOCK_RULES = ("largest_member", "sum")
WEIGHT_RULES = ("remove", "merge", "rescale")
FLOOD_ID = "flood_score"
CLASS_LABELS = {1: "Çok düşük", 2: "Düşük", 3: "Orta", 4: "Yüksek", 5: "Çok yüksek"}
WEIGHT_COLUMNS = ("scenario_id", "criterion_id", "weight")
SUMMARY_COLUMNS = ("scenario_id", "group", "role", "normalization", "high_pixel_count", "high_area_km2",
                   "delta_high_area_km2", "very_high_pixel_count", "very_high_area_km2", "baseline_high_retention",
                   "jaccard", "very_high_jaccard", "spearman_rho", "spearman_rho_baseline_positive",
                   "top5_districts", "top5_same_order", "top5_same_set")
DISTRICT_COLUMNS = ("scenario_id", "normalization", "district_id", "district_name", "high_area_km2", "rank",
                    "baseline_high_area_km2", "baseline_rank")
CLASS_SUMMARY_COLUMNS = ("method", "break_class_2", "break_class_3", "break_class_4", "break_class_5", "break_rule",
                         "goodness_of_variance_fit", "high_area_km2", "very_high_area_km2",
                         "same_class_as_equal_interval_percent", "high_jaccard_vs_equal_interval", "top5_districts")
CLASS_DISTRIBUTION_COLUMNS = ("method", "scope", "district_id", "district_name", "class_value", "class_label",
                              "pixel_count", "area_km2", "share_of_scope_percent")
FLOOD_COLUMNS = ("evidence_id", "category", "value", "unit", "note")


def _np():
    import numpy as np
    return np


def load_config(path: Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if config.get("format_version") != 1 or not isinstance(config.get("scenarios"), list) or not config["scenarios"]:
        raise ValueError("Unsupported variants config or empty scenario list")
    ids = [s.get("id") for s in config["scenarios"]]
    if len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids) or "baseline" in ids:
        raise ValueError("Scenario IDs must be unique, nonempty and differ from 'baseline'")
    for spec in config["scenarios"]:
        if spec.get("role") not in ("main", "supplementary") or not isinstance(spec.get("group"), str):
            raise ValueError(f"{spec['id']}: role must be main/supplementary and a group is required")
        if sum(key in spec for key in WEIGHT_RULES) != 1:
            raise ValueError(f"{spec['id']}: exactly one of remove/merge/rescale is required")
        if "remove" in spec and (not isinstance(spec["remove"], list) or not spec["remove"]):
            raise ValueError(f"{spec['id']}: remove needs criterion IDs")
        if "merge" in spec:
            merge = spec["merge"]
            if not isinstance(merge.get("criteria"), list) or len(merge["criteria"]) < 2 or merge.get("method") != "mean" \
                    or merge.get("block_weight") not in BLOCK_RULES or not isinstance(merge.get("into"), str):
                raise ValueError(f"{spec['id']}: merge needs two or more criteria, method mean, a block rule and a new ID")
        if "rescale" in spec:
            rescale = spec["rescale"]
            if not isinstance(rescale.get("criteria"), list) or len(rescale["criteria"]) < 2 \
                    or rescale.get("block_weight") != "largest_member":
                raise ValueError(f"{spec['id']}: rescale needs two or more criteria and the largest_member block rule")
    classification = config.get("classification", {})
    if classification.get("methods") != list(METHODS) or not isinstance(classification.get("natural_breaks_bins"), int) \
            or classification["natural_breaks_bins"] < 5:
        raise ValueError("Classification must list equal_interval, quantile, natural_breaks and an integer bin count")
    flood = config.get("flood_evidence", {})
    thresholds = flood.get("upstream_area_thresholds_km2")
    if not isinstance(thresholds, list) or not thresholds or thresholds != sorted(set(thresholds)) \
            or not all(isinstance(t, (int, float)) and t > 0 for t in thresholds):
        raise ValueError("Flood evidence needs increasing positive upstream-area thresholds")
    for key in ("hydrorivers", "flood_depth"):
        if not isinstance(flood.get(key), str) or not flood[key]:
            raise ValueError(f"Flood evidence needs the {key} path")
    if not isinstance(flood.get("source_findings"), list) or not flood["source_findings"]:
        raise ValueError("Flood evidence needs the source findings")
    return config


def scenario_weights(base: dict, spec: dict) -> dict:
    """Weights of one variant; removed weight is spread over the rest in proportion.

    rescale keeps the members as separate criteria and gives the block the same weight as
    merge/largest_member; inside the block the members keep their baseline proportions.
    """
    weights = dict(base)
    if "remove" in spec:
        removed = spec["remove"]
        if any(key not in base for key in removed):
            raise ValueError(f"{spec['id']}: unknown criterion to remove")
        share = math.fsum(base[key] for key in removed)
        if not 0 < share < 1:
            raise ValueError(f"{spec['id']}: removed weight must lie in (0, 1)")
        weights = {key: (0.0 if key in removed else value / (1 - share)) for key, value in base.items()}
    elif "rescale" in spec:
        members = spec["rescale"]["criteria"]
        if any(key not in base for key in members):
            raise ValueError(f"{spec['id']}: unknown criterion to rescale")
        block = math.fsum(base[key] for key in members)
        keep = max(base[key] for key in members)
        scale = 1 / (1 - (block - keep))
        weights = {key: value * scale * (keep / block if key in members else 1) for key, value in base.items()}
    else:
        merge = spec["merge"]
        members = merge["criteria"]
        if any(key not in base for key in members) or merge["into"] in base:
            raise ValueError(f"{spec['id']}: merge members must exist and the new ID must be new")
        block = math.fsum(base[key] for key in members)
        if merge["block_weight"] == "sum":
            weights = {key: (0.0 if key in members else value) for key, value in base.items()}
            weights[merge["into"]] = block
        else:  # largest_member: the block counts once, at its largest member weight
            keep = max(base[key] for key in members)
            scale = 1 / (1 - (block - keep))
            weights = {key: (0.0 if key in members else value * scale) for key, value in base.items()}
            weights[merge["into"]] = keep * scale
    if not math.isclose(math.fsum(weights.values()), 1.0, rel_tol=0, abs_tol=1e-12):
        raise ValueError(f"{spec['id']}: weights do not sum to one")
    return weights


def scenario_raw(stack, spec: dict, weights: dict):
    np = _np()
    if "merge" not in spec:
        return stack.raw(weights)
    vectors = dict(zip(stack.criterion_ids, stack.vectors))
    members = spec["merge"]["criteria"]
    mean = (sum(vectors[key].astype(np.float64) for key in members) / len(members)).astype(np.float32)
    return stack.raw(weights, overrides={spec["merge"]["into"]: mean})


def summary_row(stack, scenario_id, group, role, normalization, high, very_high, baseline) -> dict:
    from mcda_scenario_engine import compare
    result = compare(high, baseline[normalization]["high"], stack, baseline["areas"])
    base_vh = baseline[normalization]["very_high"]
    union = int((very_high | base_vh).sum())
    return {"scenario_id": scenario_id, "group": group, "role": role, "normalization": normalization,
            "high_pixel_count": result["high_cells"], "high_area_km2": result["high_area_km2"],
            "delta_high_area_km2": result["delta_area_km2"], "very_high_pixel_count": int(very_high.sum()),
            "very_high_area_km2": int(very_high.sum()) * stack.pixel_area_km2,
            "baseline_high_retention": result["retention"], "jaccard": result["jaccard"],
            "very_high_jaccard": int((very_high & base_vh).sum()) / union if union else None,
            "spearman_rho": result["spearman_rho"], "spearman_rho_baseline_positive": result["spearman_rho_baseline_positive"],
            "top5_districts": ";".join(result["top5"]), "top5_same_order": result["top5"] == baseline["top5"],
            "top5_same_set": set(result["top5"]) == set(baseline["top5"]), "_areas": result["district_areas_km2"]}


def district_rows(stack, scenario_id, normalization, areas, baseline) -> list[dict]:
    from mcda_scenario_engine import competition_ranks
    ranks, base_ranks = competition_ranks(areas), competition_ranks(baseline["areas"])
    return [{"scenario_id": scenario_id, "normalization": normalization, "district_id": int(d["district_id"]),
             "district_name": d["district_name"], "high_area_km2": float(areas[i]), "rank": int(ranks[i]),
             "baseline_high_area_km2": float(baseline["areas"][i]), "baseline_rank": int(base_ranks[i])}
            for i, d in enumerate(stack.districts)]


def classification_tables(stack, raw, bins: int, baseline_areas):
    from mcda_scenario_engine import CLASS_THRESHOLDS, FixedScale, QuantileBreaks, NaturalBreaks, compare
    np = _np()
    fixed = FixedScale()
    models = {"equal_interval": fixed, "quantile": QuantileBreaks.fit(raw, fixed), "natural_breaks": NaturalBreaks.fit(raw, bins, fixed)}
    rules = {"equal_interval": "Canonical fixed-scale thresholds; a threshold value belongs to the upper class",
             "quantile": "Observed fixed-scale score at sorted position ceil(q * n / 5), q = 1..4; ties go to the upper class",
             "natural_breaks": f"Exact weighted Fisher-Jenks on floor({bins} * score) bins; break = lower bin edge"}
    breaks = {"equal_interval": CLASS_THRESHOLDS, "quantile": tuple(float(b) for b in models["quantile"].breaks),
              "natural_breaks": models["natural_breaks"].breaks}
    equal = fixed.classes(raw)
    count = len(stack.districts)
    summary, distribution, classes = [], [], {}
    for method in METHODS:
        cls = models[method].classes(raw)
        classes[method] = cls
        high = cls >= 4
        both = int((high & (equal >= 4)).sum())
        either = int((high | (equal >= 4)).sum())
        result = compare(high, equal >= 4, stack, baseline_areas)
        summary.append({"method": method, **{f"break_class_{c}": breaks[method][c - 2] for c in range(2, 6)},
                        "break_rule": rules[method],
                        "goodness_of_variance_fit": models[method].gvf if method == "natural_breaks" else None,
                        "high_area_km2": int(high.sum()) * stack.pixel_area_km2,
                        "very_high_area_km2": int((cls == 5).sum()) * stack.pixel_area_km2,
                        "same_class_as_equal_interval_percent": float((cls == equal).mean() * 100),
                        "high_jaccard_vs_equal_interval": both / either if either else None,
                        "top5_districts": ";".join(result["top5"])})
        scopes = [("province", None, "Çanakkale", np.ones(cls.size, dtype=bool))]
        scopes += [("district", int(d["district_id"]), d["district_name"], stack.district_ids == int(d["district_id"])) for d in stack.districts]
        for scope, district_id, name, mask in scopes:
            counts = np.bincount(cls[mask], minlength=6)
            for c in range(1, 6):
                distribution.append({"method": method, "scope": scope, "district_id": district_id, "district_name": name,
                                     "class_value": c, "class_label": CLASS_LABELS[c], "pixel_count": int(counts[c]),
                                     "area_km2": int(counts[c]) * stack.pixel_area_km2,
                                     "share_of_scope_percent": float(counts[c] / int(mask.sum()) * 100)})
    return summary, distribution, {"models": models, "classes": classes}


def _share(part: int, whole: int):
    return part / whole if whole else None


def flood_rows(stack, findings, distances: dict, depth_stats: dict, baseline) -> list[dict]:
    """Counts, distances and source findings behind the flood decision (no coverage variant)."""
    np = _np()
    flood = dict(zip(stack.criterion_ids, stack.vectors))[FLOOD_ID] > 0
    high, very_high = baseline["top_share"]["high"], baseline["top_share"]["very_high"]
    rows = [
        {"evidence_id": "aoi_cells", "category": "count", "value": stack.n_cells, "unit": "cells", "note": "Template AOI cells"},
        {"evidence_id": "flood_score_positive_cells", "category": "count", "value": int(flood.sum()), "unit": "cells",
         "note": "flood_score > 0; every other AOI cell is source NoData mapped to 0"},
        {"evidence_id": "flood_score_positive_share", "category": "share", "value": float(flood.mean()), "unit": "fraction", "note": ""},
        {"evidence_id": "baseline_high_plus_cells", "category": "count", "value": int(high.sum()), "unit": "cells", "note": "Baseline classes 4-5"},
        {"evidence_id": "baseline_high_plus_with_flood", "category": "count", "value": int((high & flood).sum()), "unit": "cells", "note": ""},
        {"evidence_id": "baseline_high_plus_flood_share", "category": "share", "value": _share(int((high & flood).sum()), int(high.sum())), "unit": "fraction", "note": ""},
        {"evidence_id": "baseline_very_high_cells", "category": "count", "value": int(very_high.sum()), "unit": "cells", "note": "Baseline class 5"},
        {"evidence_id": "baseline_very_high_with_flood", "category": "count", "value": int((very_high & flood).sum()), "unit": "cells", "note": ""},
        {"evidence_id": "baseline_very_high_flood_share", "category": "share", "value": _share(int((very_high & flood).sum()), int(very_high.sum())), "unit": "fraction",
         "note": "Share of class 5 cells with a positive flood score"},
        {"evidence_id": "flood_depth_valid_cells", "category": "source_raster", "value": depth_stats["valid"], "unit": "cells",
         "note": "Processed 90 m depth raster, whole extent"},
        {"evidence_id": "flood_depth_zero_cells", "category": "source_raster", "value": depth_stats["zero"], "unit": "cells",
         "note": "Valid cells with depth 0; dry modelled cells would need such values"},
        {"evidence_id": "flood_depth_min_valid_m", "category": "source_raster", "value": depth_stats["min"], "unit": "m",
         "note": "Values exist only where water depth is positive"},
    ]
    for threshold, distance in distances.items():
        values = distance[flood]
        for label, q in (("p50", .5), ("p90", .9), ("p99", .99), ("max", 1.0)):
            rows.append({"evidence_id": f"flood_cell_distance_upland_ge_{threshold:g}_km2_{label}", "category": "distance",
                         "value": float(np.quantile(values, q)), "unit": "m",
                         "note": f"Distance of flood_score > 0 cells to HydroRIVERS reaches with UPLAND_SKM >= {threshold:g} km²"})
    for item in findings:
        rows.append({"evidence_id": item["id"], "category": "source_finding", "value": item["status"], "unit": "",
                     "note": f"{item['finding']} Source: {item['source']}"})
    return rows


def analyze(stack, config: dict, distances: dict, depth_stats: dict) -> dict:
    from mcda_scenario_engine import FixedScale, TopShare, district_areas, top_names
    base = stack.baseline_mapping()
    models = {"top_share": TopShare.from_classes(stack.baseline_classes), "fixed_scale": FixedScale()}
    raw = stack.raw(base)
    names = [d["district_name"] for d in stack.districts]
    baseline = {name: {"high": model.high_plus(raw), "very_high": model.very_high(raw)} for name, model in models.items()}
    baseline["areas"] = district_areas(baseline["top_share"]["high"], stack.district_ids, len(names), stack.pixel_area_km2)
    baseline["top5"] = top_names(baseline["areas"], names)
    weight_rows, summary, districts = [], [], []
    variants = [("baseline", "baseline", "reference", {"id": "baseline"}, base)]
    variants += [(s["id"], s["group"], s["role"], s, scenario_weights(base, s)) for s in config["scenarios"]]
    for scenario_id, group, role, spec, weights in variants:
        weight_rows += [{"scenario_id": scenario_id, "criterion_id": key, "weight": float(value)} for key, value in weights.items()]
        score = raw if scenario_id == "baseline" else scenario_raw(stack, spec, weights)
        for name in NORMALIZATIONS:
            row = summary_row(stack, scenario_id, group, role, name, models[name].high_plus(score), models[name].very_high(score), baseline)
            districts += district_rows(stack, scenario_id, name, row.pop("_areas"), baseline)
            summary.append(row)
    class_summary, class_distribution, fitted = classification_tables(stack, raw, config["classification"]["natural_breaks_bins"], baseline["areas"])
    tables = {WEIGHTS_TABLE: (weight_rows, WEIGHT_COLUMNS), SUMMARY_TABLE: (summary, SUMMARY_COLUMNS),
              DISTRICT_TABLE: (districts, DISTRICT_COLUMNS), CLASS_SUMMARY_TABLE: (class_summary, CLASS_SUMMARY_COLUMNS),
              CLASS_DISTRIBUTION_TABLE: (class_distribution, CLASS_DISTRIBUTION_COLUMNS),
              FLOOD_TABLE: (flood_rows(stack, config["flood_evidence"]["source_findings"], distances, depth_stats, baseline), FLOOD_COLUMNS)}
    return {"config": config, "tables": tables, "n_cells": stack.n_cells, "pixel_area_km2": stack.pixel_area_km2,
            "criterion_ids": stack.criterion_ids, "metadata": stack.metadata, "baseline_top5": baseline["top5"],
            "natural_breaks_gvf": fitted["models"]["natural_breaks"].gvf, "aoi_shape": list(stack.aoi.shape)}


def river_distances(stack, path: Path, thresholds) -> dict:
    """Distance (m) of every AOI cell to HydroRIVERS reaches at or above each upstream area, on the canonical grid."""
    from osgeo import gdal, ogr
    ny, nx = stack.aoi.shape
    source = ogr.Open(str(path))
    if source is None:
        raise ValueError(f"HydroRIVERS layer cannot be opened: {path.name}")
    layer = source.GetLayer(0)
    result = {}
    for threshold in thresholds:
        layer.SetAttributeFilter(f"UPLAND_SKM >= {float(threshold)!r}")
        if layer.GetFeatureCount() == 0:
            raise ValueError(f"No HydroRIVERS reach with UPLAND_SKM >= {threshold}")
        burn = gdal.GetDriverByName("MEM").Create("", nx, ny, 1, gdal.GDT_Byte)
        burn.SetGeoTransform(stack.grid)
        burn.SetProjection(stack.projection)
        if gdal.RasterizeLayer(burn, [1], layer, burn_values=[1], options=["ALL_TOUCHED=TRUE"]) != 0:
            raise ValueError("HydroRIVERS rasterization failed")
        proximity = gdal.GetDriverByName("MEM").Create("", nx, ny, 1, gdal.GDT_Float32)
        proximity.SetGeoTransform(stack.grid)
        proximity.SetProjection(stack.projection)
        if gdal.ComputeProximity(burn.GetRasterBand(1), proximity.GetRasterBand(1), ["VALUES=1", "DISTUNITS=GEO"]) != 0:
            raise ValueError("River distance computation failed")
        result[threshold] = proximity.GetRasterBand(1).ReadAsArray()[stack.aoi]
        burn = proximity = None
    layer.SetAttributeFilter(None)
    return result


def depth_statistics(path: Path) -> dict:
    from osgeo import gdal
    np = _np()
    dataset = gdal.OpenEx(str(path), gdal.OF_RASTER | gdal.OF_READONLY)
    if dataset is None:
        raise ValueError(f"Flood depth raster cannot be opened: {path.name}")
    band = dataset.GetRasterBand(1)
    values = band.ReadAsArray()
    nodata = band.GetNoDataValue()
    valid = np.isfinite(values) & ((values != nodata) if nodata is not None else True)
    dataset = None
    return {"valid": int(valid.sum()), "zero": int((values[valid] == 0).sum()), "min": float(values[valid].min())}


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyze_project(root: Path, config_path: Path) -> dict:
    from mcda_scenario_engine import load_canonical
    root = Path(root).resolve()
    config = load_config(config_path)
    stack = load_canonical(root)
    if stack.metadata["baseline_id"] != config.get("baseline_id"):
        raise ValueError("Config baseline ID differs from the frozen baseline")
    flood = config["flood_evidence"]
    analysis = analyze(stack, config, river_distances(stack, root / flood["hydrorivers"], flood["upstream_area_thresholds_km2"]),
                       depth_statistics(root / flood["flood_depth"]))
    analysis["config_path"] = config_path.resolve().relative_to(root).as_posix() if config_path.resolve().is_relative_to(root) else config_path.name
    analysis["config_sha256"] = _sha(config_path)
    analysis["inputs"] = {key: {"path": flood[key], "sha256": _sha(root / flood[key])} for key in ("hydrorivers", "flood_depth")}
    return analysis


def _manifest(analysis, stage: Path) -> dict:
    import numpy as np
    from osgeo import gdal
    config = analysis["config"]
    outputs = []
    for name in TABLE_FILES:
        content = (stage / name).read_bytes()
        outputs.append({"path": name, "size": len(content), "sha256": hashlib.sha256(content).hexdigest()})
    return {
        "format_version": 1, "method": "Scenario variants and alternative thresholds of the frozen canonical MCDA",
        "config": analysis["config_path"], "config_sha256": analysis["config_sha256"],
        "aoi_cells": analysis["n_cells"], "aoi_rule": "template_equals_1", "pixel_area_km2": analysis["pixel_area_km2"],
        "grid_shape": analysis["aoi_shape"], "crs_epsg": 32635, "criterion_order": list(analysis["criterion_ids"]),
        "scenarios": [{"id": s["id"], "group": s["group"], "role": s["role"], "label_tr": s.get("label_tr", "")} for s in config["scenarios"]],
        "high_plus_definition": {
            "top_share": "Main measure. The cells holding the baseline class 4-5 cell count (class 5 likewise) by rank of the weighted raw score, ties included; the area is constant by definition and the comparison measures location.",
            "fixed_scale": "Supplementary. Canonical clip((raw - 0.029) / 0.473, 0, 1) with 0.2/0.4/0.6/0.8 thresholds; area changes include weight-driven level shifts."},
        "merge_rule": "Merged criterion = arithmetic mean of the member scores (Float64, stored as Float32); block_weight 'largest_member' keeps the block at its largest member weight and spreads the rest of the block weight over all criteria in proportion, 'sum' keeps the block total; 'rescale' keeps the members separate at the largest_member block weight, in their baseline proportions",
        "classification": {"methods": list(METHODS), "fitted_on": "baseline fixed-scale score only", "natural_breaks_bins": config["classification"]["natural_breaks_bins"],
                           "natural_breaks_goodness_of_variance_fit": analysis["natural_breaks_gvf"],
                           "purpose": "Shows the effect of the threshold choice; not a replacement for the canonical equal-interval classes"},
        "flood_coverage_variant": "None. The source documents no NoData meaning and no modelled-network or coverage layer, so a 'not modelled' mask cannot be built; deriving coverage from flood_score > 0 would use the result as its own coverage",
        "inputs": analysis["inputs"], "baseline_top5_districts": analysis["baseline_top5"],
        "district_ranking": "Districts ranked by high-plus area (km², descending); ties share the best rank (competition ranking)",
        "interpretation_limit": "Variants test single modelling choices around the frozen canonical model; they are not validated alternatives or hazard probabilities",
        "weights_modified": False, "baseline": analysis["metadata"],
        "software": {"python": sys.version.split()[0], "numpy": np.__version__, "gdal": gdal.VersionInfo("RELEASE_NAME")},
        "outputs": outputs,
    }


def write_outputs(analysis, output_dir) -> list[str]:
    """Stage the complete package, verify it, then exclusively publish each file."""
    from generate_scenario_agreement import _csv_bytes
    contents = {name: _csv_bytes(rows, columns) for name, (rows, columns) in analysis["tables"].items()}
    output_dir = Path(output_dir).absolute()
    if output_dir.is_symlink() or (output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir()))):
        raise ValueError("Output directory must be empty or new; content is never overwritten")
    if not output_dir.parent.is_dir():
        raise ValueError("Output directory parent must already exist")
    published, created = [], False
    try:
        with tempfile.TemporaryDirectory(prefix=".mcda-variants-stage-", dir=output_dir.parent) as temporary:
            stage = Path(temporary)
            for name, content in contents.items():
                (stage / name).write_bytes(content)
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
    """Compare every saved table value and provenance field."""
    from generate_scenario_agreement import _compare_rows, _read_csv
    report = {"passed": False, "checked_files": 0, "checked_table_rows": 0, "errors": []}
    output_dir = Path(output_dir)
    try:
        for name in OUTPUT_FILES:
            if not (output_dir / name).is_file() or (output_dir / name).is_symlink():
                raise ValueError(f"Missing or symbolic-linked variant artifact: {name}")
            report["checked_files"] += 1
        for name, (rows, columns) in analysis["tables"].items():
            fields, _ = _read_csv(output_dir / name)
            if fields != list(columns):
                raise ValueError(f"Saved CSV column order differs: {name}")
            report["checked_table_rows"] += _compare_rows(output_dir / name, rows, tolerance=1e-10)
        saved = json.loads((output_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
        wanted = _manifest(analysis, output_dir)
        if set(saved) != set(wanted):
            raise ValueError("Saved variants manifest fields differ")
        for key, value in wanted.items():
            if key != "software" and saved[key] != value:
                raise ValueError(f"Saved variants manifest differs: {key}")
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
        analysis = analyze_project(args.project_root, config_path)
        result.update({"baseline_id": analysis["metadata"]["baseline_id"], "aoi_cells": analysis["n_cells"],
                       "scenarios": [s["id"] for s in analysis["config"]["scenarios"]],
                       "natural_breaks_gvf": analysis["natural_breaks_gvf"]})
        if args.generate:
            result["generated_files"] = write_outputs(analysis, target)
        else:
            result["artifact_comparison"] = compare_outputs(analysis, target)
            if not result["artifact_comparison"]["passed"]:
                result["errors"] += result["artifact_comparison"]["errors"]
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
        print(f"MCDA variants: {'PASSED' if result['passed'] else 'FAILED'} ({result['mode']})")
        for error in result["errors"]:
            print(error)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
