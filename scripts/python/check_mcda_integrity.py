#!/usr/bin/env python3
"""Read-only checks of the canonical MCDA grid, masks and stored arithmetic.

The AOI comes exclusively from template == 1. No statistics, rasters or sidecars
are written. Exit codes: 0 passed (possibly with warnings), 1 failed, 2 missing
NumPy/GDAL dependencies. ``--json`` writes the complete report to stdout.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path


sys.dont_write_bytecode = True

ANALYSIS = Path("data/processed/analysis")
CRITERIA = (
    "earthquake_pga_score", "fault_proximity_score", "site_condition_score",
    "population_exposure_score", "building_exposure_density_score", "flood_score",
    "hydrography_proximity_score", "slope_score", "landcover_sensitivity_score",
    "tree_cover_score", "road_accessibility_difficulty_score",
)
TOLERANCE = 1e-6
THRESHOLDS = (0.2, 0.4, 0.6, 0.8)
# Open boundary finding: the saved land-cover input has 5,272 outside-AOI cells.
# Stage 3 investigates/isolate this; stage 2 reports it, without changing data.
# This exception never permits nonfinite/out-of-range values or output spill.
KNOWN_BOUNDARY_FINDING = "landcover_sensitivity_score"
KNOWN_BOUNDARY_MAX_CELLS = 5272


class ValidationError(Exception):
    """A required project input cannot be validated."""


def new_report():
    return {"schema_version": 1, "status": "failed", "passed": False, "summary": {}, "checks": [], "rasters": []}


def record(report, name, status, message, **details):
    item = {"name": name, "status": status, "message": message}
    if details:
        item["details"] = details
    report["checks"].append(item)


def inside_path(root, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValidationError(f"Path must be relative and cannot traverse parents: {relative}")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise ValidationError(f"Path escapes project root: {relative}")
    if not resolved.is_file():
        raise ValidationError(f"Required file missing: {relative}")
    return resolved


def load_config(root, report):
    path = inside_path(root, "config/mcda_weights.tsv")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"scenario_id", "scenario_role", "criterion_order", "criterion_id", "raster_path", "weight"}
        if not required.issubset(reader.fieldnames or []):
            raise ValidationError("Weight configuration is missing required columns")
        rows = [row for row in reader if row.get("scenario_id") == "baseline"]
    if len(rows) != len(CRITERIA):
        raise ValidationError(f"Expected 11 baseline criteria, found {len(rows)}")
    if len({row["criterion_id"] for row in rows}) != len(CRITERIA):
        raise ValidationError("Baseline criterion IDs must be distinct")
    try:
        rows.sort(key=lambda row: int(row["criterion_order"]))
        orders = [int(row["criterion_order"]) for row in rows]
    except (TypeError, ValueError) as exc:
        raise ValidationError("Criterion orders must be integers") from exc
    if orders != list(range(1, 12)) or [row["criterion_id"] for row in rows] != list(CRITERIA):
        raise ValidationError("Baseline criteria/order differ from the canonical WLC order")
    for row in rows:
        if any(row.get(key) in (None, "") for key in required):
            raise ValidationError("Baseline rows cannot contain empty required fields")
        if row["scenario_role"] != "canonical":
            raise ValidationError("Baseline rows must have canonical role")
        try:
            weight = float(row["weight"])
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"Invalid weight for {row['criterion_id']}") from exc
        if not math.isfinite(weight) or not 0 <= weight <= 1:
            raise ValidationError(f"Weight must be finite and in [0,1]: {row['criterion_id']}")
        row["weight_value"] = weight
        # The existing production script binds these filenames explicitly.
        # Reject a config path it would silently ignore rather than check it.
        row["path"] = inside_path(root, row["raster_path"])
        expected = ANALYSIS / f"{row['criterion_id']}_32635.tif"
        if Path(row["raster_path"]) != expected:
            raise ValidationError(f"Noncanonical raster path for {row['criterion_id']}")
    total = math.fsum(row["weight_value"] for row in rows)
    if abs(total - 1.0) > TOLERANCE:
        raise ValidationError(f"Baseline weights sum to {total}, expected 1")
    report["summary"].update(criterion_count=len(rows), weight_sum=total)
    record(report, "baseline_config", "passed", "11 distinct, ordered baseline criteria and valid weights")
    return rows


def load_policy(root, report):
    source = inside_path(root, "scripts/bash/mcda_pipeline_commands.sh").read_text(encoding="utf-8")
    constants = []
    for key in ("MCDA_MIN_RAW", "MCDA_RANGE"):
        matches = re.findall(rf'^{key}="([^"]+)"\s*$', source, re.MULTILINE)
        if len(matches) != 1:
            raise ValidationError(f"Cannot uniquely read {key} from the production script")
        try:
            constants.append(float(matches[0]))
        except ValueError as exc:
            raise ValidationError(f"Invalid normalization constant {key}") from exc
    if constants != [0.029, 0.473]:
        raise ValidationError("Canonical rounded normalization constants have changed; policy review required")
    compact = re.sub(r"\s+", "", source)
    classification = "where(A<0.2,1,where(A<0.4,2,where(A<0.6,3,where(A<0.8,4,5))))"
    normalization = "minimum(maximum((A-${MCDA_MIN_RAW})/${MCDA_RANGE},0),1)"
    if classification not in compact or normalization not in compact:
        raise ValidationError("Production normalization/clipping or class thresholds need policy review")
    report["summary"]["normalization"] = {"minimum": constants[0], "range": constants[1], "clipping": [0, 1]}
    report["summary"]["class_thresholds"] = list(THRESHOLDS)
    record(report, "canonical_policy", "passed", "Production constants, clipping and thresholds match the preserved policy")
    return constants


def read_raster(path, relative, report, np, gdal, osr, reference=None, kind="continuous"):
    try:
        dataset = gdal.OpenEx(str(path), gdal.OF_RASTER | gdal.OF_READONLY)
        if dataset is None:
            raise ValidationError(f"Cannot open raster: {relative}")
        if dataset.RasterCount != 1:
            raise ValidationError(f"Expected one raster band: {relative}")
        band = dataset.GetRasterBand(1)
        array = band.ReadAsArray()
        mask = band.GetMaskBand().ReadAsArray() != 0
        if array is None or mask.shape != array.shape:
            raise ValidationError(f"Cannot read raster array/mask: {relative}")
        grid = dataset.GetGeoTransform()
        projection = dataset.GetProjectionRef()
        crs = osr.SpatialReference()
        if not projection or crs.ImportFromWkt(projection) != 0:
            raise ValidationError(f"Missing/invalid CRS: {relative}")
        expected_crs = osr.SpatialReference()
        expected_crs.ImportFromEPSG(32635)
        if not crs.IsSame(expected_crs):
            raise ValidationError(f"Expected EPSG:32635: {relative}")
        if not np.allclose([grid[1], grid[2], grid[4], grid[5]], [100, 0, 0, -100], rtol=0, atol=1e-9):
            raise ValidationError(f"Expected north-up 100 m grid: {relative}")
        if reference is not None:
            if array.shape != reference["array"].shape:
                raise ValidationError(f"Grid shape differs from template: {relative}")
            if not np.allclose(grid, reference["grid"], rtol=0, atol=1e-8):
                raise ValidationError(f"Grid transform differs from template: {relative}")
        if kind == "continuous" and band.DataType != gdal.GDT_Float32:
            raise ValidationError(f"Expected Float32 score raster: {relative}")
        if kind in {"template", "class"} and array.dtype.kind not in "iu":
            raise ValidationError(f"Expected integer {kind} raster: {relative}")
        expected_nodata = -9999 if kind == "continuous" else 0
        nodata = band.GetNoDataValue()
        if nodata != expected_nodata:
            raise ValidationError(f"NoData metadata must be {expected_nodata}: {relative}")
        result = {"array": array, "mask": mask, "grid": grid, "nodata": expected_nodata}
        record(report, f"metadata:{relative}", "passed", "Single band, CRS, grid, type and NoData metadata verified")
        result["report"] = {"path": str(relative), "kind": kind, "dtype": gdal.GetDataTypeName(band.DataType),
                            "shape": list(array.shape), "nodata": nodata}
        report["rasters"].append(result["report"])
        return result
    except ValidationError:
        raise
    except (RuntimeError, ValueError, TypeError) as exc:
        raise ValidationError(f"Unreadable raster {relative}: {exc}") from exc


def validate_pixels(raster, aoi, report, np, label, allow_spill=False, classes=False):
    array, mask, nodata = raster["array"], raster["mask"], raster["nodata"]
    values = array[aoi]
    finite = np.isfinite(values)
    upper, lower = (5, 1) if classes else (1 + TOLERANCE, -TOLERANCE)
    counts = {
        "aoi_nodata_cells": int(np.count_nonzero(values == nodata)),
        "aoi_nonfinite_cells": int(np.count_nonzero(~finite)),
        "aoi_mask_invalid_cells": int(np.count_nonzero(~mask[aoi])),
        "aoi_range_error_cells": int(np.count_nonzero(finite & ((values < lower) | (values > upper)))),
        "outside_non_nodata_cells": int(np.count_nonzero(array[~aoi] != nodata)),
        "outside_mask_valid_cells": int(np.count_nonzero(mask[~aoi])),
        "mask_value_mismatch_cells": int(np.count_nonzero(mask != (array != nodata))),
    }
    valid_values = values[finite & (values != nodata)]
    counts["minimum_aoi"] = float(valid_values.min()) if valid_values.size else None
    counts["maximum_aoi"] = float(valid_values.max()) if valid_values.size else None
    raster["report"].update(counts)
    bad = [key for key in ("aoi_nodata_cells", "aoi_nonfinite_cells", "aoi_mask_invalid_cells", "aoi_range_error_cells", "mask_value_mismatch_cells") if counts[key]]
    spill = counts["outside_non_nodata_cells"]
    if spill or counts["outside_mask_valid_cells"]:
        if allow_spill:
            spill_values = array[(~aoi) & (array != nodata)]
            invalid_spill = int(np.count_nonzero(~np.isfinite(spill_values) | (spill_values < -TOLERANCE) | (spill_values > 1 + TOLERANCE)))
            raster["report"]["outside_invalid_score_cells"] = invalid_spill
            if invalid_spill:
                bad.append("outside_invalid_score_cells")
            if spill > KNOWN_BOUNDARY_MAX_CELLS:
                bad.append("known_boundary_finding_expanded")
            record(report, f"boundary:{label}", "warning", "Known land-cover boundary finding remains open; input spill is excluded by template AOI", outside_non_nodata_cells=spill, outside_mask_valid_cells=counts["outside_mask_valid_cells"], maximum_accepted_spill_cells=KNOWN_BOUNDARY_MAX_CELLS)
        else:
            bad.append("outside_aoi_not_nodata")
    status = "failed" if bad else "passed"
    record(report, f"pixels:{label}", status, "; ".join(bad) if bad else "Finite scores, ranges and AOI/mask consistency verified", **counts)
    return not bad


def compare_output(raster, expected, aoi, report, np, label, tolerance):
    actual = raster["array"][aoi]
    finite = np.isfinite(actual) & np.isfinite(expected)
    differences = np.abs(actual[finite].astype(np.float64) - expected[finite].astype(np.float64))
    mismatches = int(np.count_nonzero(differences > tolerance) + np.count_nonzero(~finite))
    maximum = float(differences.max()) if differences.size else None
    raster["report"].update(maximum_absolute_difference_aoi=maximum, mismatch_aoi_cells=mismatches, absolute_tolerance=tolerance)
    record(report, f"arithmetic:{label}", "failed" if mismatches else "passed", "Independent recomputation compared to stored output", mismatch_aoi_cells=mismatches, maximum_absolute_difference_aoi=maximum, absolute_tolerance=tolerance)


def check_project(root, np, gdal, osr):
    root = Path(root).resolve()
    report = new_report()
    gdal.UseExceptions()
    gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")
    report["summary"]["gdal_version"] = gdal.VersionInfo("--version")
    try:
        rows = load_config(root, report)
        minimum, span = load_policy(root, report)
        template_rel = ANALYSIS / "analysis_template_100m_32635.tif"
        template = read_raster(inside_path(root, template_rel), template_rel, report, np, gdal, osr, kind="template")
        aoi = template["array"] == 1
        count = int(np.count_nonzero(aoi))
        binary = bool(np.all((template["array"] == 0) | aoi))
        mask_matches = bool(np.array_equal(template["mask"], aoi))
        report["summary"].update(aoi_cells=count, outside_aoi_cells=int(aoi.size - count), shape=list(aoi.shape))
        if not count or not binary or not mask_matches:
            raise ValidationError("Template must contain a nonempty binary 0/1 AOI with matching GDAL mask")
        record(report, "template_aoi", "passed", "AOI independently defined by template == 1", aoi_cells=count)
        expected_raw = np.zeros(count, dtype=np.float32)
        inputs_ok = True
        for row in rows:
            try:
                raster = read_raster(row["path"], row["raster_path"], report, np, gdal, osr, template)
                okay = validate_pixels(raster, aoi, report, np, row["criterion_id"], allow_spill=row["criterion_id"] == KNOWN_BOUNDARY_FINDING)
                inputs_ok = inputs_ok and okay
                # Match the authoritative ordered Float32 expression. Avoid
                # float64 accumulation, sample subsets or rescaling criteria.
                expected_raw += raster["array"][aoi] * np.float32(row["weight_value"])
            except ValidationError as exc:
                inputs_ok = False
                record(report, f"criterion:{row['criterion_id']}", "failed", str(exc))
        expected_normalized = np.clip((expected_raw - np.float32(minimum)) / np.float32(span), 0, 1)
        expected_class = np.ones(count, dtype=np.uint8)
        for threshold in THRESHOLDS:
            expected_class += expected_normalized >= np.float32(threshold)
        outputs = (
            ("mcda_priority_score", expected_raw, "continuous", TOLERANCE),
            ("mcda_priority_score_normalized", expected_normalized, "continuous", TOLERANCE),
            ("mcda_priority_class", expected_class, "class", 0),
        )
        for name, expected, kind, tolerance in outputs:
            relative = ANALYSIS / f"{name}_32635.tif"
            try:
                raster = read_raster(inside_path(root, relative), relative, report, np, gdal, osr, template, kind=kind)
                validate_pixels(raster, aoi, report, np, name, classes=kind == "class")
                if inputs_ok:
                    compare_output(raster, expected, aoi, report, np, name, tolerance)
            except ValidationError as exc:
                record(report, f"output:{name}", "failed", str(exc))
        if not inputs_ok:
            record(report, "independent_recomputation", "failed", "Output arithmetic cannot pass while canonical inputs fail validation")
    except (ValidationError, OSError, csv.Error) as exc:
        record(report, "required_inputs", "failed", str(exc))
    failed = sum(item["status"] == "failed" for item in report["checks"])
    warnings = sum(item["status"] == "warning" for item in report["checks"])
    report["summary"].update(failed_checks=failed, warning_count=warnings)
    report["status"] = "failed" if failed else "passed"
    report["passed"] = report["status"] == "passed"
    return report


def emit_report(report, as_json):
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
        return
    print(f"MCDA integrity: {report['status'].upper()}")
    summary = report["summary"]
    if "aoi_cells" in summary:
        print(f"Criteria: {summary['criterion_count']}; AOI cells: {summary['aoi_cells']}; weight sum: {summary['weight_sum']:.12g}")
        print("Raw/normalized tolerance: 1e-6 absolute; classes: exact; mode: read-only")
    for item in report["checks"]:
        if item["status"] in {"failed", "warning", "unavailable"}:
            details = f" ({json.dumps(item['details'], ensure_ascii=False)})" if item.get("details") else ""
            print(f"{item['status'].upper()} {item['name']}: {item['message']}{details}")
    if "failed_checks" in summary:
        print(f"Failed checks: {summary['failed_checks']}; warnings: {summary['warning_count']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Read-only validation (the default)")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--json", action="store_true", help="Write the complete JSON report to stdout")
    args = parser.parse_args(argv)
    try:
        import numpy as np
        from osgeo import gdal, osr
        # Imports alone do not establish that the geospatial runtime works:
        # a missing PROJ database must be reported as unavailable, not bad data.
        gdal.UseExceptions()
        probe = osr.SpatialReference()
        if probe.ImportFromEPSG(32635) != 0:
            raise RuntimeError("The PROJ EPSG database is unavailable")
    except (ImportError, OSError, RuntimeError) as exc:
        report = new_report()
        report["status"] = "unavailable"
        record(report, "dependencies", "unavailable", f"Working NumPy/GDAL bindings and PROJ resources are required: {exc}")
        emit_report(report, args.json)
        return 2
    report = check_project(args.project_root.resolve(), np, gdal, osr)
    emit_report(report, args.json)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
