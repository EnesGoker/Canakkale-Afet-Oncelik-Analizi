#!/usr/bin/env python3
"""Read-only numerical traceability of eight existing criterion rasters.

These are equivalent transformations reconstructed from current local artifacts,
not proof of the commands originally used. PGA and slope scale constants were numerically estimated; their historical
selection remains undocumented. The flood divisor has a local history record.
All rasterization/resampling products exist only in GDAL memory.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys
from xml.sax.saxutils import escape

sys.dont_write_bytecode = True
import check_mcda_integrity as common
BASIS = "Numerically reconstructed equivalent formula; historical command provenance not established"
# Equivalent parameters fitted to existing source/score pairs, not physical
# thresholds or claimed full-source min/max statistics. Do not refit on a run:
# freezing them allows changed source/score artifacts to fail this check.
# Flood divisor is independently present in local processing history entry 74;
# clipping/array alignment here remains an equivalent reconstruction.
AFFINE = {
    "earthquake_pga_score": ("data/processed/earthquake/canakkale_afad_tdth_pga10_aoi_masked_32635.tif", 0.29773420095947556, 0.438076138475815),
    "slope_score": ("data/processed/dem/canakkale_slope_degrees_32635.tif", 0.0, 40.20227432106767),
    "flood_score": ("data/processed/flood/canakkale_flood_rp100_depth_32635.tif", 0.0, 10.0526208878),
}
LANDCOVER_LOOKUP = {10: .60, 20: .50, 30: .40, 40: .30, 50: .20, 60: .20, 80: .05, 90: .50}
TREE_SOURCE = "data/processed/landcover/canakkale_tree_cover_density_2021_32635.tif"
LAND_SOURCE = "data/processed/landcover/canakkale_worldcover_2021_32635.tif"
BUILDING_SOURCE = "data/processed/analysis/building_density_final_grid_100m_32635.gpkg"
DISTANCE_SOURCES = {
    "hydrography_proximity_score": ("data/processed/hydrography/canakkale_hydrography_hybrid_clean_32635.gpkg", 1000.0, True),
    "road_accessibility_difficulty_score": ("data/processed/osm/canakkale_osm_roads_32635.gpkg", 2000.0, False),
}


def same_crs(wkt, osr):
    actual, expected = osr.SpatialReference(), osr.SpatialReference()
    expected.ImportFromEPSG(32635)
    return bool(wkt and actual.ImportFromWkt(wkt) == 0 and actual.IsSame(expected))


def open_source(root, relative, gdal, osr, np, expected_nodata, value_range):
    path = common.inside_path(root, relative)
    source = gdal.OpenEx(str(path), gdal.OF_RASTER | gdal.OF_READONLY)
    if source is None or source.RasterCount != 1 or not same_crs(source.GetProjection(), osr):
        raise common.ValidationError(f"Expected single-band EPSG:32635 source: {relative}")
    band = source.GetRasterBand(1)
    if band.GetNoDataValue() != expected_nodata:
        raise common.ValidationError(f"Unexpected source NoData metadata: {relative}")
    transform = source.GetGeoTransform()
    if transform[1] <= 0 or transform[5] >= 0 or transform[2] != 0 or transform[4] != 0:
        raise common.ValidationError(f"Expected north-up source grid: {relative}")
    observed = set()
    for row in range(0, source.RasterYSize, 256):
        array = band.ReadAsArray(0, row, source.RasterXSize, min(256, source.RasterYSize - row))
        valid = array != expected_nodata
        values = array[valid]
        if np.any(~np.isfinite(values)) or np.any(values < value_range[0]) or np.any(values > value_range[1]):
            raise common.ValidationError(f"Nonfinite or out-of-range source values: {relative}")
        if relative == LAND_SOURCE:
            observed.update(np.unique(values).tolist())
    if relative == LAND_SOURCE and not observed.issubset(LANDCOVER_LOOKUP):
        raise common.ValidationError(f"Unobserved land-cover classes have no reconstructed score: {sorted(observed - LANDCOVER_LOOKUP.keys())}")
    return source


def warp_to_template(source, template, gdal, method):
    grid = template["grid"]
    height, width = template["array"].shape
    bounds = [grid[0], grid[3] + height * grid[5], grid[0] + width * grid[1], grid[3]]
    target = gdal.Warp("", source, format="MEM", outputBounds=bounds, width=width, height=height,
                       dstSRS="EPSG:32635", resampleAlg=method, dstNodata=-9999, outputType=gdal.GDT_Float32)
    return target.ReadAsArray()


def landcover_average(source, template, gdal):
    # Apply class scores before averaging. Averaging class IDs or assigning a
    # dominant 100 m class is a different operation and does not reproduce this
    # existing continuous score surface. The virtual LUT avoids a 900 MB copy.
    lookup = ",".join(f"{key}:{value}" for key, value in LANDCOVER_LOOKUP.items())
    xml = (f'<VRTDataset rasterXSize="{source.RasterXSize}" rasterYSize="{source.RasterYSize}">'
           f'<SRS>{escape(source.GetProjection())}</SRS>'
           f'<GeoTransform>{",".join(map(str, source.GetGeoTransform()))}</GeoTransform>'
           '<VRTRasterBand dataType="Float32" band="1"><NoDataValue>-9999</NoDataValue><ComplexSource>'
           f'<SourceFilename relativeToVRT="0">{escape(source.GetDescription())}</SourceFilename>'
           f'<SourceBand>1</SourceBand><NODATA>0</NODATA><LUT>{lookup}</LUT>'
           '</ComplexSource></VRTRasterBand></VRTDataset>')
    virtual = gdal.Open(xml)
    return warp_to_template(virtual, template, gdal, "average")


def vector_raster(root, relative, template, gdal, ogr, osr, attribute=None):
    source = ogr.Open(str(common.inside_path(root, relative)), 0)
    if source is None or source.GetLayerCount() != 1:
        raise common.ValidationError(f"Expected one readable vector layer: {relative}")
    layer = source.GetLayer(0)
    crs = layer.GetSpatialRef()
    if crs is None or not same_crs(crs.ExportToWkt(), osr):
        raise common.ValidationError(f"Expected EPSG:32635 vector source: {relative}")
    if layer.GetFeatureCount() == 0:
        raise common.ValidationError(f"Empty vector source: {relative}")
    height, width = template["array"].shape
    target = gdal.GetDriverByName("MEM").Create("", width, height, 1, gdal.GDT_Float32)
    target.SetGeoTransform(template["grid"])
    target.SetProjection(crs.ExportToWkt())
    target.GetRasterBand(1).Fill(0)
    options = [f"ATTRIBUTE={attribute}"] if attribute else []
    # Default GDAL line/centre rasterization; ALL_TOUCHED would change results.
    gdal.RasterizeLayer(target, [1], layer, burn_values=[] if attribute else [1], options=options)
    return target


def building_attributes(root):
    path = common.inside_path(root, BUILDING_SOURCE)
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as database:
        table = "building_density_final_grid_100m_32635"
        count, invalid, maximum = database.execute(
            f'SELECT COUNT(*), SUM(CASE WHEN grid_area_m2 IS NULL OR grid_area_m2<=0 '
            f'OR grid_area_m2>1.7976931348623157e308 OR building_area_m2 IS NULL OR building_area_m2<0 '
            f'OR building_area_m2>1.7976931348623157e308 OR building_density_score IS NULL '
            f'OR building_density_score<0 OR building_density_score>1 THEN 1 ELSE 0 END), '
            f'MAX(ABS(building_density_score-MIN(1.0,building_area_m2/grid_area_m2))) FROM "{table}"'
        ).fetchone()
    if not count or invalid or maximum is None or maximum > common.TOLERANCE:
        raise common.ValidationError("Building area ratio and saved density attributes disagree or contain invalid values")
    return {"attribute_rows": count, "attribute_maximum_absolute_difference": maximum}


def compare(expected, actual, aoi, np):
    values = expected[aoi].astype(np.float64)
    stored = actual[aoi].astype(np.float64)
    finite = np.isfinite(values) & np.isfinite(stored)
    errors = np.abs(values[finite] - stored[finite])
    mismatches = int(np.count_nonzero(~finite) + np.count_nonzero(errors > common.TOLERANCE))
    return {"compared_aoi_cells": int(aoi.sum()), "mismatch_aoi_cells": mismatches,
            "maximum_absolute_difference_aoi": float(errors.max()) if errors.size else None,
            "absolute_tolerance": common.TOLERANCE}


def check_project(root, np, gdal, ogr, osr):
    root = Path(root).resolve()
    report = common.new_report()
    report["summary"].update(numerical_basis=BASIS, expected_criteria=8)
    gdal.UseExceptions()
    gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")
    try:
        relative = common.ANALYSIS / "analysis_template_100m_32635.tif"
        template = common.read_raster(common.inside_path(root, relative), relative, report, np, gdal, osr, kind="template")
        aoi = template["array"] == 1
        if not aoi.any() or not np.all((template["array"] == 0) | aoi) or not np.array_equal(template["mask"], aoi):
            raise common.ValidationError("Template must define a nonempty binary AOI with matching GDAL mask")
        report["summary"]["aoi_cells"] = int(aoi.sum())
        names = list(AFFINE) + ["tree_cover_score", "landcover_sensitivity_score", "building_exposure_density_score"] + list(DISTANCE_SOURCES)
        for name in names:
            try:
                details = {"numerical_basis": BASIS}
                if name in AFFINE:
                    source_path, minimum, span = AFFINE[name]
                    source = open_source(root, source_path, gdal, osr, np, -9999, (0, 1.5 if name.startswith("earthquake") else 90 if name.startswith("slope") else 10000))
                    aligned = warp_to_template(source, template, gdal, "bilinear")
                    missing = aligned == -9999
                    expected = np.clip((np.where(missing, minimum, aligned).astype(np.float64) - minimum) / span, 0, 1)
                    details.update(resampling="bilinear", equivalent_minimum=minimum, equivalent_range=span,
                                   parameter_basis="local_processing_history_74_divisor" if name == "flood_score" else "numerically_estimated_current_artifacts",
                                   historical_parameter_selection="divisor_recorded_original_selection_rationale_unresolved" if name == "flood_score" else "unresolved",
                                   source_nodata_aoi_cells=int(np.count_nonzero(missing & aoi)),
                                   upper_clipped_aoi_cells=int(np.count_nonzero((aligned > minimum + span) & aoi)))
                elif name == "tree_cover_score":
                    source = open_source(root, TREE_SOURCE, gdal, osr, np, 255, (0, 100))
                    aligned = warp_to_template(source, template, gdal, "average")
                    missing = aligned == -9999
                    expected = np.where(missing, 0, aligned) / np.float32(100)
                    details.update(resampling="average", divisor=100, source_nodata_aoi_cells=int(np.count_nonzero(missing & aoi)))
                elif name == "landcover_sensitivity_score":
                    source = open_source(root, LAND_SOURCE, gdal, osr, np, 0, (0, 100))
                    expected = landcover_average(source, template, gdal)
                    if np.any(expected[aoi] == -9999):
                        raise common.ValidationError("Reconstructed land-cover source does not cover the AOI")
                    details.update(resampling="average_after_10m_class_lookup", observed_class_lookup=LANDCOVER_LOOKUP)
                elif name == "building_exposure_density_score":
                    details.update(building_attributes(root))
                    expected = vector_raster(root, BUILDING_SOURCE, template, gdal, ogr, osr, "building_density_score").ReadAsArray()
                else:
                    vector_path, cutoff, inverse = DISTANCE_SOURCES[name]
                    binary = vector_raster(root, vector_path, template, gdal, ogr, osr)
                    distance = gdal.GetDriverByName("MEM").Create("", binary.RasterXSize, binary.RasterYSize, 1, gdal.GDT_Float32)
                    distance.SetGeoTransform(template["grid"])
                    gdal.ComputeProximity(binary.GetRasterBand(1), distance.GetRasterBand(1), ["VALUES=1", "DISTUNITS=GEO"])
                    expected = np.clip(1 - distance.ReadAsArray() / cutoff if inverse else distance.ReadAsArray() / cutoff, 0, 1)
                    details.update(distance_units="metres", equivalent_cutoff=cutoff, rasterization="GDAL default, ALL_TOUCHED disabled")
                relative = common.ANALYSIS / f"{name}_32635.tif"
                stored = common.read_raster(common.inside_path(root, relative), relative, report, np, gdal, osr, template)
                if not np.all(np.isfinite(stored["array"][aoi])) or np.any((stored["array"][aoi] < 0) | (stored["array"][aoi] > 1)) or not np.all(stored["mask"][aoi]):
                    raise common.ValidationError(f"Invalid stored AOI scores or mask: {name}")
                details.update(compare(expected, stored["array"], aoi, np))
                common.record(report, f"equivalent_formula:{name}", "failed" if details["mismatch_aoi_cells"] else "passed",
                              "Equivalent numerical formula compared across all AOI cells", **details)
            except (common.ValidationError, OSError, RuntimeError, ValueError, sqlite3.Error) as exc:
                common.record(report, f"equivalent_formula:{name}", "failed", str(exc))
        common.record(report, "historical_transform_provenance", "warning",
                      "Equivalent formulas do not establish original commands; historical PGA/slope parameter selection and full original transform commands remain unresolved")
    except (common.ValidationError, OSError, RuntimeError) as exc:
        common.record(report, "required_inputs", "failed", str(exc))
    failed = sum(item["status"] == "failed" for item in report["checks"])
    checked = sum(item["name"].startswith("equivalent_formula:") and item["status"] == "passed" for item in report["checks"])
    report["summary"].update(failed_checks=failed, verified_equivalent_formulas=checked,
                             warning_count=sum(item["status"] == "warning" for item in report["checks"]))
    report["passed"] = not failed and checked == 8
    report["status"] = "passed" if report["passed"] else "failed"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Read-only validation (default)")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        import numpy as np
        from osgeo import gdal, ogr, osr
        gdal.UseExceptions()
        if osr.SpatialReference().ImportFromEPSG(32635) != 0:
            raise RuntimeError("PROJ EPSG database is unavailable")
    except (ImportError, OSError, RuntimeError) as exc:
        report = common.new_report()
        report["status"] = "unavailable"
        common.record(report, "dependencies", "unavailable", str(exc))
        common.emit_report(report, args.json)
        return 2
    report = check_project(args.project_root, np, gdal, ogr, osr)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    else:
        print(f"Criterion equivalent-formula audit: {report['status'].upper()}")
        print(f"Verified equivalent formulas: {report['summary']['verified_equivalent_formulas']}/8; tolerance 1e-6; read-only")
        for item in report["checks"]:
            if item["status"] in {"failed", "warning"}:
                print(f"{item['status'].upper()} {item['name']}: {item['message']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
