#!/usr/bin/env python3
"""Compare high/very-high classes across the three frozen MCDA scenarios.

Default --check recomputes the full AOI and checks six saved artifacts without
writing. --generate requires an explicit empty/new directory and never replaces
files. GIS dependencies are imported lazily, so --help needs standard Python only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = Path("outputs/analysis/scenario_agreement_v1")
BASELINE_MANIFEST = Path("config/analysis_baseline_v1.json")
DISTRICT_VECTOR = Path("data/processed/admin/canakkale_districts_32635.gpkg")
DISTRICT_LAYER = "canakkale_districts_32635"
SCENARIOS = ("baseline", "earthquake-heavy", "equal-weight")
BITS = {"baseline": 1, "earthquake-heavy": 2, "equal-weight": 4}
SCENARIO_NAMES = {"baseline": "Baseline", "earthquake-heavy": "Deprem ağırlıklı", "equal-weight": "Eşit ağırlık"}
COUNT_FILE = "scenario_agreement_count_32635.tif"
MEMBERSHIP_FILE = "scenario_agreement_membership_32635.tif"
COUNT_TABLE = "agreement_count_summary.csv"
MEMBERSHIP_TABLE = "agreement_membership_summary.csv"
COMPARISON_TABLE = "scenario_high_area_comparison.csv"
MANIFEST_FILE = "scenario_agreement_manifest.json"
RASTER_FILES = (COUNT_FILE, MEMBERSHIP_FILE)
TABLE_FILES = (COUNT_TABLE, MEMBERSHIP_TABLE, COMPARISON_TABLE)
OUTPUT_FILES = (*RASTER_FILES, *TABLE_FILES, MANIFEST_FILE)
NODATA = 255
BASE_COLUMNS = ("scope", "district_id", "district_name", "aoi_cell_count", "aoi_area_km2")
COUNT_COLUMNS = (*BASE_COLUMNS, "agreement_count", "pixel_count", "area_km2", "share_of_scope_aoi_percent")
MEMBERSHIP_COLUMNS = (*BASE_COLUMNS, "membership_code", "scenario_ids", "pixel_count", "area_km2", "share_of_scope_aoi_percent")
COMPARISON_COLUMNS = (*BASE_COLUMNS, "scenario_id", "high_pixel_count", "high_area_km2", "high_share_of_scope_aoi_percent", "baseline_high_pixel_count", "baseline_high_area_km2", "persistent_pixel_count", "persistent_area_km2", "added_pixel_count", "added_area_km2", "removed_pixel_count", "removed_area_km2", "union_pixel_count", "union_area_km2", "jaccard_percent", "baseline_high_retention_percent", "scenario_high_overlap_baseline_percent")


def _np():
    import numpy as np
    return np


def validate_grid(aoi, grid, projection):
    np = _np()
    if not isinstance(aoi, np.ndarray) or aoi.ndim != 2 or aoi.dtype != np.dtype(bool) or not aoi.any():
        raise ValueError("A nonempty two-dimensional boolean AOI is required")
    if len(grid) != 6 or not all(math.isfinite(float(v)) for v in grid):
        raise ValueError("A finite six-value geotransform is required")
    if grid[1] <= 0 or grid[5] >= 0 or grid[2] != 0 or grid[4] != 0:
        raise ValueError("An unrotated north-up grid is required")
    if not isinstance(projection, str) or not projection.strip():
        raise ValueError("A nonempty raster CRS is required")
    return abs(float(grid[1]) * float(grid[5])) / 1_000_000


def compute_scenario_classes(loaded):
    """Reuse the frozen sensitivity arithmetic, including Float32 operation order."""
    np = _np()
    from generate_sensitivity_tables import weighted_score, classify_normalized
    criteria = loaded["criteria"]
    scenarios = loaded["scenarios"]
    if set(scenarios) != set(SCENARIOS) or not criteria:
        raise ValueError("Exactly the three frozen scenarios and nonempty criteria are required")
    n = len(loaded["baseline_class"])
    if n == 0:
        raise ValueError("The AOI cannot be empty")
    arrays = {}
    ids = [row["criterion_id"] for row in scenarios["baseline"]]
    if len(ids) != len(set(ids)) or set(ids) != set(criteria):
        raise ValueError("Criterion IDs must be unique and exactly match the scenarios")
    for key, values in criteria.items():
        values = np.asarray(values)
        if values.dtype != np.dtype("float32") or values.shape != (n,) or not np.isfinite(values).all() or np.any((values < 0) | (values > 1)):
            raise ValueError(f"{key}: finite aligned one-dimensional Float32 scores in [0,1] are required")
        arrays[key] = values
    baseline = np.asarray(loaded["baseline_class"])
    if baseline.shape != (n,) or baseline.dtype.kind not in "iu" or np.any((baseline < 1) | (baseline > 5)):
        raise ValueError("Baseline classes must be aligned integer values 1..5")
    valid = np.ones(n, dtype=bool)
    classes, stats = {}, {}
    for scenario_id in SCENARIOS:
        rows = scenarios[scenario_id]
        if [row["criterion_id"] for row in rows] != ids:
            raise ValueError(f"{scenario_id}: criterion order differs from baseline")
        weights = [row["weight"] for row in rows]
        if not all(isinstance(w, (int, float)) and math.isfinite(w) and 0 <= w <= 1 for w in weights) or not math.isclose(sum(weights), 1.0, abs_tol=1e-6):
            raise ValueError(f"{scenario_id}: invalid scenario weights")
        _, normalized, stats[scenario_id] = weighted_score({"scenario_id": scenario_id, "criteria": rows}, arrays, valid)
        if not np.isfinite(normalized).all():
            raise ValueError(f"{scenario_id}: nonfinite normalized scores")
        classes[scenario_id] = baseline.copy() if scenario_id == "baseline" else classify_normalized(normalized, valid)
    return classes, stats


def validate_district_assignment(district_ids, districts, n_cells):
    np = _np()
    ids = np.asarray(district_ids)
    if ids.shape != (n_cells,) or ids.dtype.kind not in "iu":
        raise ValueError("District IDs must be an aligned one-dimensional integer vector")
    metadata_ids = [row["district_id"] for row in districts]
    names = [row["district_name"] for row in districts]
    if not metadata_ids or metadata_ids != list(range(1, len(districts) + 1)):
        raise ValueError("District metadata IDs must be unique and consecutive, ordered from one")
    if len(set(names)) != len(names) or not all(isinstance(n, str) and n.strip() for n in names):
        raise ValueError("District names must be unique and nonempty")
    if any(not math.isfinite(float(row["district_area_km2"])) or row["district_area_km2"] <= 0 for row in districts):
        raise ValueError("District geometry areas must be positive and finite")
    if set(np.unique(ids).tolist()) != set(metadata_ids):
        raise ValueError("Every AOI cell must belong to one known district, with nonempty coverage for every district")


def compute_agreement(classes, district_ids, districts, pixel_area_km2=0.01):
    """Count high classes (4 or 5), preserve all eight memberships and sum by AOI."""
    np = _np()
    if set(classes) != set(SCENARIOS):
        raise ValueError("Exactly the three named scenario class vectors are required")
    baseline = np.asarray(classes["baseline"])
    n = baseline.size
    if n == 0 or baseline.ndim != 1:
        raise ValueError("Nonempty one-dimensional scenario class vectors are required")
    if not math.isfinite(pixel_area_km2) or pixel_area_km2 <= 0:
        raise ValueError("Pixel area must be positive and finite")
    high = {}
    for scenario_id in SCENARIOS:
        array = np.asarray(classes[scenario_id])
        if array.shape != (n,) or array.dtype.kind not in "iu" or np.any((array < 1) | (array > 5)):
            raise ValueError(f"{scenario_id}: aligned integer classes 1..5 are required before thresholding")
        high[scenario_id] = array >= 4
    validate_district_assignment(district_ids, districts, n)
    district_ids = np.asarray(district_ids)
    membership = np.zeros(n, dtype=np.uint8)
    count = np.zeros(n, dtype=np.uint8)
    for scenario_id in SCENARIOS:
        membership += high[scenario_id].astype(np.uint8) * BITS[scenario_id]
        count += high[scenario_id]
    if not np.array_equal(count, np.asarray([int(i).bit_count() for i in membership], dtype=np.uint8)):
        raise ValueError("Scenario membership and agreement count are inconsistent")
    counts, memberships, comparisons = [], [], []
    scopes = [("province", 0, "Çanakkale", np.ones(n, dtype=bool)), *[("district", row["district_id"], row["district_name"], district_ids == row["district_id"]) for row in districts]]
    for scope, district_id, district_name, mask in scopes:
        scope_n = int(mask.sum())
        base = dict(scope=scope, district_id=district_id, district_name=district_name, aoi_cell_count=scope_n, aoi_area_km2=scope_n * pixel_area_km2)
        for value in range(4):
            cells = int(np.count_nonzero(count[mask] == value))
            counts.append({**base, "agreement_count": value, "pixel_count": cells, "area_km2": cells * pixel_area_km2, "share_of_scope_aoi_percent": cells / scope_n * 100})
        for value in range(8):
            cells = int(np.count_nonzero(membership[mask] == value))
            memberships.append({**base, "membership_code": value, "scenario_ids": ";".join(s for s in SCENARIOS if value & BITS[s]), "pixel_count": cells, "area_km2": cells * pixel_area_km2, "share_of_scope_aoi_percent": cells / scope_n * 100})
        baseline_high = high["baseline"] & mask
        baseline_n = int(baseline_high.sum())
        for scenario_id in SCENARIOS:
            selected = high[scenario_id] & mask
            high_n = int(selected.sum())
            persistent = int((selected & baseline_high).sum())
            added = high_n - persistent
            removed = baseline_n - persistent
            union = high_n + baseline_n - persistent
            comparisons.append({**base, "scenario_id": scenario_id,
                "high_pixel_count": high_n, "high_area_km2": high_n * pixel_area_km2, "high_share_of_scope_aoi_percent": high_n / scope_n * 100,
                "baseline_high_pixel_count": baseline_n, "baseline_high_area_km2": baseline_n * pixel_area_km2,
                "persistent_pixel_count": persistent, "persistent_area_km2": persistent * pixel_area_km2,
                "added_pixel_count": added, "added_area_km2": added * pixel_area_km2,
                "removed_pixel_count": removed, "removed_area_km2": removed * pixel_area_km2,
                "union_pixel_count": union, "union_area_km2": union * pixel_area_km2,
                "jaccard_percent": persistent / union * 100 if union else None,
                "baseline_high_retention_percent": persistent / baseline_n * 100 if baseline_n else None,
                "scenario_high_overlap_baseline_percent": persistent / high_n * 100 if high_n else None})
    # Every district is a disjoint AOI partition; prove each table conserves cells.
    for rows, key, values in ((counts, "agreement_count", range(4)), (memberships, "membership_code", range(8))):
        for value in values:
            provincial = next(row["pixel_count"] for row in rows if row["scope"] == "province" and row[key] == value)
            if sum(row["pixel_count"] for row in rows if row["scope"] == "district" and row[key] == value) != provincial:
                raise ValueError("District/province cell conservation failed")
    for scenario_id in SCENARIOS:
        provincial = next(row for row in comparisons if row["scope"] == "province" and row["scenario_id"] == scenario_id)
        for field in ("high_pixel_count", "persistent_pixel_count", "added_pixel_count", "removed_pixel_count", "union_pixel_count"):
            if sum(row[field] for row in comparisons if row["scope"] == "district" and row["scenario_id"] == scenario_id) != provincial[field]:
                raise ValueError("District/province scenario conservation failed")
    return {"n_cells": n, "classes": {key: np.asarray(value).copy() for key, value in classes.items()}, "agreement_count": count, "membership": membership, "district_ids": district_ids.copy(), "districts": districts, "pixel_area_km2": pixel_area_km2, "count_rows": counts, "membership_rows": memberships, "comparison_rows": comparisons}


def load_district_assignment(root, aoi, grid, projection):
    """Use the existing SQLite feature order and GDAL default cell-center rule."""
    np = _np()
    from osgeo import gdal, ogr, osr
    validate_grid(aoi, grid, projection)
    expected = osr.SpatialReference()
    expected.ImportFromEPSG(32635)
    target = osr.SpatialReference()
    if target.ImportFromWkt(projection) != 0 or not target.IsSame(expected):
        raise ValueError("The frozen grid must use EPSG:32635")
    source = ogr.Open(str(Path(root) / DISTRICT_VECTOR), 0)
    if source is None:
        raise ValueError("District vector could not be opened read-only")
    layer = source.GetLayerByName(DISTRICT_LAYER)
    if layer is None or layer.GetSpatialRef() is None or not layer.GetSpatialRef().IsSame(target):
        raise ValueError("District layer or CRS differs from the frozen grid")
    sql = ("SELECT CAST(fid AS INTEGER) AS qa_district_id, district_name, "
           "ST_Area(geom)/1000000.0 AS district_area_km2, geom "
           f"FROM {DISTRICT_LAYER}")
    selected = source.ExecuteSQL(sql, dialect="SQLite")
    if selected is None:
        raise ValueError("District SQLite selection failed")
    districts = [{"district_id": int(f.GetField("qa_district_id")), "district_name": f.GetField("district_name"), "district_area_km2": float(f.GetField("district_area_km2"))} for f in selected]
    if [row["district_id"] for row in districts] != list(range(1, 13)):
        raise ValueError("Expected the original twelve districts in FID order 1..12")
    def rasterize(*, coverage=False):
        selected.ResetReading()
        ds = gdal.GetDriverByName("MEM").Create("", aoi.shape[1], aoi.shape[0], 1, gdal.GDT_UInt16)
        ds.SetGeoTransform(grid)
        ds.SetProjection(projection)
        ds.GetRasterBand(1).Fill(0)
        arguments = {"burn_values": [1], "options": ["MERGE_ALG=ADD"]} if coverage else {"options": ["ATTRIBUTE=qa_district_id"]}
        code = gdal.RasterizeLayer(ds, [1], selected, **arguments)
        if code != 0:
            raise ValueError("District cell-center rasterization failed")
        return ds.GetRasterBand(1).ReadAsArray()
    try:
        assigned = rasterize()
        coverage = rasterize(coverage=True)
    finally:
        source.ReleaseResultSet(selected)
    if np.any(coverage[aoi] != 1):
        raise ValueError("District cell-center coverage is missing or overlapping inside the AOI")
    ids = assigned[aoi].copy()
    validate_district_assignment(ids, districts, int(aoi.sum()))
    return ids, districts


def _read_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def _compare_rows(path, expected, tolerance=1e-8):
    fields, saved = _read_csv(path)
    if not fields or len(saved) != len(expected) or len(fields) != len(set(fields)):
        raise ValueError(f"CSV rows/columns differ: {Path(path).name}")
    for actual, wanted in zip(saved, expected):
        if set(actual) != set(fields) or any(value is None for value in actual.values()) or set(fields) != set(wanted):
            raise ValueError(f"CSV fields differ: {Path(path).name}")
        for key in fields:
            value = wanted[key]
            text = actual[key]
            if value is None:
                valid = text == ""
            elif isinstance(value, bool):
                valid = text == str(value)
            elif isinstance(value, int):
                valid = text == str(value)
            elif isinstance(value, float):
                parsed = float(text)
                valid = math.isfinite(parsed) and abs(parsed - value) <= tolerance
            else:
                valid = text == value
            if not valid:
                raise ValueError(f"Saved CSV value differs: {Path(path).name} / {key}")
    return len(saved)


def compare_reference_tables(root, analysis, stats):
    """Numerically reproduce the old distributions, transitions and district rows."""
    np = _np()
    import generate_sensitivity_tables as old
    scenarios = old.load_weight_scenarios(Path(root))
    classes = analysis["classes"]
    baseline = classes["baseline"]
    valid = np.ones(analysis["n_cells"], dtype=bool)
    baseline_high = int((baseline >= 4).sum())
    expected = {}
    for key, function in (("mcda_sensitivity_class_distribution.csv", lambda s, c: old.class_distribution(c, valid, s)),
                          ("mcda_sensitivity_class_transition.csv", lambda s, c: old.transition_rows(s, c, baseline, valid)),
                          ("mcda_sensitivity_scenario_summary.csv", lambda s, c: [old.summarize_scenario(s, c, baseline, valid, stats[s["scenario_id"]], baseline_high)]),
                          ("mcda_sensitivity_top_districts.csv", lambda s, c: old.top_district_rows(s, c, analysis["district_ids"], analysis["districts"]))):
        expected[key] = [row for scenario_id in SCENARIOS for row in function(scenarios[scenario_id], classes[scenario_id])]
    expected["mcda_class_distribution.csv"] = [{key: value for key, value in row.items() if key not in {"scenario_id", "scenario_label", "scenario_role"}} for row in old.class_distribution(baseline, valid, scenarios["baseline"])]
    district_rows = []
    for district in analysis["districts"]:
        for class_value, label in old.CLASS_LABELS.items():
            cells = int(((analysis["district_ids"] == district["district_id"]) & (baseline == class_value)).sum())
            area = cells * analysis["pixel_area_km2"]
            province_total = int((baseline == class_value).sum())
            district_rows.append({**district, "class_value": class_value, "class_label": label, "pixel_count": cells, "area_km2": area, "district_share_percent": area / district["district_area_km2"] * 100, "province_class_share_percent": cells / province_total * 100 if province_total else 0.0})
    expected["mcda_class_area_by_district.csv"] = district_rows
    checks = []
    for name, rows in expected.items():
        checks.append({"path": "outputs/tables/" + name, "rows_checked": _compare_rows(Path(root) / "outputs/tables" / name, rows), "passed": True})
    return {"passed": True, "numeric_tables_checked": len(checks), "checks": checks, "all_eight_reference_csv_checksums_verified_by_frozen_loader": True}


def analyze_project(root=ROOT):
    os.environ["GDAL_PAM_ENABLED"] = "NO"
    from analysis_baseline import load_frozen_inputs, NORMALIZATION
    root = Path(root).resolve()
    loaded = load_frozen_inputs(root)
    area = validate_grid(loaded["aoi"], loaded["grid"], loaded["projection"])
    if not math.isclose(area, 0.01, rel_tol=0, abs_tol=1e-12):
        raise ValueError("The frozen analysis requires 100 m cells (0.01 km²)")
    classes, stats = compute_scenario_classes(loaded)
    ids, districts = load_district_assignment(root, loaded["aoi"], loaded["grid"], loaded["projection"])
    analysis = compute_agreement(classes, ids, districts, area)
    if analysis["n_cells"] != int(loaded["aoi"].sum()):
        raise ValueError("Scenario vectors and template AOI differ")
    analysis.update({"aoi": loaded["aoi"], "grid": loaded["grid"], "projection": loaded["projection"], "raw_statistics": stats})
    analysis["reference_validation"] = compare_reference_tables(root, analysis, stats)
    manifest_bytes = (root / BASELINE_MANIFEST).read_bytes()
    frozen = json.loads(manifest_bytes)
    analysis["metadata"] = {
        "baseline_id": loaded["baseline_id"], "baseline_manifest": BASELINE_MANIFEST.as_posix(),
        "baseline_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "frozen_files_verified": len(frozen["files"]), "normalization": NORMALIZATION,
        "district_vector": DISTRICT_VECTOR.as_posix(), "district_layer": DISTRICT_LAYER,
        "district_assignment": "Original SQLite selection / ascending source FID 1..12; GDAL default cell-center rasterization, no ALL_TOUCHED; coverage must equal one for every AOI cell",
        "district_geometry_areas_km2": districts,
        "reference_validation": analysis["reference_validation"],
    }
    return analysis


def _csv_bytes(rows, columns):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if set(row) != set(columns):
            raise ValueError("Table rows and columns differ")
        writer.writerow({key: format(value, ".17g") if isinstance(value, float) else value for key, value in row.items()})
    return stream.getvalue().encode("utf-8")


def raster_arrays(analysis):
    np = _np()
    validate_grid(analysis["aoi"], analysis["grid"], analysis["projection"])
    arrays = {}
    for name, key in ((COUNT_FILE, "agreement_count"), (MEMBERSHIP_FILE, "membership")):
        vector = np.asarray(analysis[key])
        maximum = 3 if key == "agreement_count" else 7
        if vector.shape != (int(analysis["aoi"].sum()),) or vector.dtype != np.dtype("uint8") or np.any(vector > maximum):
            raise ValueError("Invalid agreement raster vector")
        array = np.full(analysis["aoi"].shape, NODATA, dtype=np.uint8)
        array[analysis["aoi"]] = vector
        arrays[name] = array
    expected_count = np.asarray([i.bit_count() for i in range(8)], dtype=np.uint8)[analysis["membership"]]
    if not np.array_equal(expected_count, analysis["agreement_count"]):
        raise ValueError("Agreement raster count and membership are inconsistent")
    return arrays


def _write_rasters(stage, analysis):
    from osgeo import gdal
    for name, array in raster_arrays(analysis).items():
        dataset = gdal.GetDriverByName("GTiff").Create(str(stage / name), array.shape[1], array.shape[0], 1, gdal.GDT_Byte, options=["COMPRESS=DEFLATE", "ZLEVEL=6", "TILED=YES"])
        if dataset is None:
            raise ValueError("Could not create staged agreement GeoTIFF")
        dataset.SetGeoTransform(analysis["grid"])
        dataset.SetProjection(analysis["projection"])
        band = dataset.GetRasterBand(1)
        band.SetNoDataValue(NODATA)
        band.SetDescription("Number of scenarios in high/very-high class" if name == COUNT_FILE else "Scenario membership bits: baseline=1; earthquake-heavy=2; equal-weight=4")
        if band.WriteArray(array) != 0:
            raise ValueError("Could not write staged agreement GeoTIFF")
        dataset.FlushCache()
        band = None
        dataset = None


def _manifest(analysis, stage):
    import numpy as np
    from osgeo import gdal
    outputs = []
    for name in (*RASTER_FILES, *TABLE_FILES):
        content = (stage / name).read_bytes()
        outputs.append({"path": name, "size": len(content), "sha256": hashlib.sha256(content).hexdigest()})
    return {
        "format_version": 1, "method": "Descriptive spatial agreement of three scenario high/very-high class masks",
        "aoi_cells": analysis["n_cells"], "aoi_rule": "template_equals_1", "pixel_area_km2": analysis["pixel_area_km2"],
        "grid_shape": list(analysis["aoi"].shape), "geotransform": list(analysis["grid"]), "crs_epsg": 32635,
        "scenario_order": list(SCENARIOS), "membership_bits": BITS, "high_classes": [4, 5],
        "outside_aoi_nodata": NODATA, "valid_zero_meaning": "No scenario assigns a high/very-high class; zero is valid AOI data, not NoData",
        "share_denominator": "All template-AOI cell centers assigned to the current province or district, including cells with zero agreement; district vector geometry area is not the share denominator",
        "undefined_ratios": "Empty high-set union, empty baseline-high set or empty scenario-high set produces a blank CSV ratio, not zero or an invented perfect agreement",
        "interpretation_limit": "Agreement among these three prescribed scenarios is neither probability, independent model validation nor a pure weight-effect experiment; baseline and alternatives use different documented normalization policies",
        "weights_modified": False, "baseline": analysis.get("metadata", {}),
        "software": {"python": sys.version.split()[0], "numpy": np.__version__, "gdal": gdal.VersionInfo("RELEASE_NAME")},
        "outputs": outputs,
    }


def write_outputs(analysis, output_dir):
    """Stage the complete six-file package, then exclusively publish each file."""
    table_contents = {COUNT_TABLE: _csv_bytes(analysis["count_rows"], COUNT_COLUMNS), MEMBERSHIP_TABLE: _csv_bytes(analysis["membership_rows"], MEMBERSHIP_COLUMNS), COMPARISON_TABLE: _csv_bytes(analysis["comparison_rows"], COMPARISON_COLUMNS)}
    raster_arrays(analysis)  # Validate all grid/mask vectors before touching disk.
    output_dir = Path(output_dir).absolute()
    if output_dir.is_symlink() or (output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir()))):
        raise ValueError("Output directory must be empty or new; content is never overwritten")
    if not output_dir.parent.is_dir():
        raise ValueError("Output directory parent must already exist")
    published, created = [], False
    try:
        with tempfile.TemporaryDirectory(prefix=".scenario-agreement-stage-", dir=output_dir.parent) as temporary:
            stage = Path(temporary)
            for name, content in table_contents.items():
                (stage / name).write_bytes(content)
            _write_rasters(stage, analysis)
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


def compare_outputs(analysis, output_dir):
    """Compare every saved cell, grid, mask, table value, and provenance field."""
    np = _np()
    from osgeo import gdal, osr
    report = {"passed": False, "checked_files": 0, "checked_raster_cells": 0, "checked_table_rows": 0, "errors": []}
    output_dir = Path(output_dir)
    try:
        arrays = raster_arrays(analysis)
        for name in OUTPUT_FILES:
            if not (output_dir / name).is_file() or (output_dir / name).is_symlink():
                raise ValueError(f"Missing or symbolic-linked scenario artifact: {name}")
            report["checked_files"] += 1
        target = osr.SpatialReference()
        target.ImportFromWkt(analysis["projection"])
        for name, expected in arrays.items():
            dataset = gdal.OpenEx(str(output_dir / name), gdal.OF_RASTER | gdal.OF_READONLY)
            if dataset is None or dataset.RasterCount != 1 or (dataset.RasterYSize, dataset.RasterXSize) != expected.shape:
                raise ValueError(f"Saved raster dimensions differ: {name}")
            band = dataset.GetRasterBand(1)
            spatial = osr.SpatialReference()
            projection_valid = spatial.ImportFromWkt(dataset.GetProjectionRef()) == 0 and bool(spatial.IsSame(target))
            if not projection_valid or not np.allclose(dataset.GetGeoTransform(), analysis["grid"], atol=1e-9, rtol=0):
                raise ValueError(f"Saved raster CRS/grid differs: {name}")
            if band.DataType != gdal.GDT_Byte or band.GetNoDataValue() != NODATA or not np.array_equal(band.ReadAsArray(), expected):
                raise ValueError(f"Saved raster values/type/NoData differ: {name}")
            mask = band.GetMaskBand().ReadAsArray() != 0
            if not np.array_equal(mask, analysis["aoi"]):
                raise ValueError(f"Saved raster validity mask differs: {name}")
            report["checked_raster_cells"] += expected.size
            band = None
            dataset = None
        for name, key in ((COUNT_TABLE, "count_rows"), (MEMBERSHIP_TABLE, "membership_rows"), (COMPARISON_TABLE, "comparison_rows")):
            columns = {COUNT_TABLE: COUNT_COLUMNS, MEMBERSHIP_TABLE: MEMBERSHIP_COLUMNS, COMPARISON_TABLE: COMPARISON_COLUMNS}[name]
            fields, _ = _read_csv(output_dir / name)
            if fields != list(columns):
                raise ValueError(f"Saved CSV column order differs: {name}")
            report["checked_table_rows"] += _compare_rows(output_dir / name, analysis[key], tolerance=1e-10)
        saved = json.loads((output_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
        expected = _manifest(analysis, output_dir)
        if set(saved) != set(expected):
            raise ValueError("Saved agreement manifest fields differ")
        for key, value in expected.items():
            if key != "software" and saved[key] != value:
                raise ValueError(f"Saved agreement manifest differs: {key}")
        if not isinstance(saved["software"], dict) or set(saved["software"]) != {"python", "numpy", "gdal"} or not all(isinstance(v, str) and v for v in saved["software"].values()):
            raise ValueError("Saved software provenance is malformed")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, RuntimeError, csv.Error) as error:
        report["errors"].append(str(error))
    report["passed"] = not report["errors"]
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="Read-only full-AOI recomputation and saved artifact check (default)")
    modes.add_argument("--generate", action="store_true", help="Generate six artifacts in an explicit empty/new output directory")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, help=f"Check defaults to PROJECT_ROOT/{DEFAULT_OUTPUT}")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.generate and args.output_dir is None:
        parser.error("--generate requires --output-dir")
    os.environ["GDAL_PAM_ENABLED"] = "NO"
    result = {"passed": False, "mode": "generate" if args.generate else "check", "errors": []}
    code = 1
    try:
        analysis = analyze_project(args.project_root)
        result.update({"baseline_id": analysis["metadata"]["baseline_id"], "aoi_cells": analysis["n_cells"], "scenario_count": 3, "district_count": len(analysis["districts"]), "reference_validation": analysis["reference_validation"]})
        if args.generate:
            result["generated_files"] = write_outputs(analysis, args.output_dir)
        else:
            result["artifact_comparison"] = compare_outputs(analysis, args.output_dir or args.project_root / DEFAULT_OUTPUT)
            if not result["artifact_comparison"]["passed"]:
                raise ValueError("; ".join(result["artifact_comparison"]["errors"]))
        result["passed"] = True
        code = 0
    except ImportError as error:
        result.update({"dependency_unavailable": True})
        result["errors"].append(f"Required analysis dependency unavailable: {error}")
        code = 2
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, csv.Error) as error:
        result["errors"].append(str(error))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    else:
        print(f"Scenario spatial agreement: {'PASSED' if result['passed'] else 'FAILED'} ({result['mode']})")
        for error in result["errors"]:
            print(error)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
