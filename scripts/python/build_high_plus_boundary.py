#!/usr/bin/env python3
"""Baseline high-plus outline drawn over map 14 (weight perturbation probability).

Input: the frozen canonical class raster (classes 4-5 = high-plus) and the AOI
template. Output: one GeoJSON polygon layer (EPSG:32635, whole-metre cell
corners) that QGIS draws as an outline only, at
outputs/maps/layers/baseline_high_plus_boundary_32635.geojson. Polygons are
4-connected cell groups as returned by GDAL Polygonize, sorted by area and
first vertex, and written with fixed separators, so the bytes are reproducible.
The layer is derived from the canonical data and, like it, is not part of the
public source edition.

Default --check rebuilds the layer in memory and compares its bytes with the
saved file without writing. --generate --output <new file> writes a new file
and refuses to replace an existing one. Both print a JSON record with the
SHA-256 values. GIS dependencies are imported lazily, so --help needs standard
Python only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
CLASS_RASTER = "data/processed/analysis/mcda_priority_class_32635.tif"
TEMPLATE = "data/processed/analysis/analysis_template_100m_32635.tif"
OUTPUT = "outputs/maps/layers/baseline_high_plus_boundary_32635.geojson"
LAYER_NAME = "baseline_high_plus_boundary_32635"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(class_raster: Path, template: Path) -> tuple[bytes, dict]:
    """Return the GeoJSON bytes and a summary for one class raster and AOI template."""
    from osgeo import gdal, ogr, osr
    import numpy as np

    gdal.UseExceptions()
    classes_ds = gdal.Open(str(class_raster))
    template_ds = gdal.Open(str(template))
    classes = classes_ds.GetRasterBand(1).ReadAsArray()
    aoi = template_ds.GetRasterBand(1).ReadAsArray() == 1
    if classes.shape != aoi.shape or classes_ds.GetGeoTransform() != template_ds.GetGeoTransform():
        raise ValueError("class raster and AOI template grids differ")
    mask = (aoi & (classes >= 4) & (classes <= 5)).astype(np.uint8)
    memory = gdal.GetDriverByName("MEM").Create("", mask.shape[1], mask.shape[0], 1, gdal.GDT_Byte)
    memory.SetGeoTransform(classes_ds.GetGeoTransform())
    memory.SetProjection(classes_ds.GetProjection())
    band = memory.GetRasterBand(1)
    band.WriteArray(mask)
    vector = ogr.GetDriverByName("MEM").CreateDataSource("")
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(32635)
    layer = vector.CreateLayer("polygons", srs, ogr.wkbPolygon)
    layer.CreateField(ogr.FieldDefn("value", ogr.OFTInteger))
    gdal.Polygonize(band, band, layer, 0, [])
    rings = []
    for feature in layer:
        geometry = feature.GetGeometryRef()
        coords = [[[round(x), round(y)] for x, y, *_ in geometry.GetGeometryRef(i).GetPoints()]
                  for i in range(geometry.GetGeometryCount())]
        rings.append((round(geometry.GetArea()), coords))
    rings.sort(key=lambda item: (-item[0], item[1][0][0]))
    cells = int(mask.sum())
    cell_area = abs(classes_ds.GetGeoTransform()[1] * classes_ds.GetGeoTransform()[5])
    if round(sum(area for area, _ in rings)) != round(cells * cell_area):
        raise ValueError("polygon area differs from the high-plus cell area")
    features = [{"type": "Feature", "properties": {"id": i + 1, "area_m2": area},
                 "geometry": {"type": "Polygon", "coordinates": coords}} for i, (area, coords) in enumerate(rings)]
    collection = {"type": "FeatureCollection", "name": LAYER_NAME,
                  "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::32635"}}, "features": features}
    data = (json.dumps(collection, separators=(",", ":")) + "\n").encode("utf-8")
    return data, {"polygons": len(features), "high_plus_cells": cells, "area_km2": cells * cell_area / 1e6,
                  "connectivity": 4}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="Rebuild in memory and compare with the saved file (default)")
    modes.add_argument("--generate", action="store_true", help="Write a new file at --output; never replaces a file")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, help=f"--generate: new file path; --check default PROJECT_ROOT/{OUTPUT}")
    args = parser.parse_args(argv)
    if args.generate and args.output is None:
        parser.error("--generate requires --output")
    root = args.project_root.resolve()
    target = (args.output or root / OUTPUT).absolute()
    if args.generate and target.exists():
        print(f"ERROR: output exists, nothing written: {target}", file=sys.stderr)
        return 1
    try:
        data, summary = build(root / CLASS_RASTER, root / TEMPLATE)
    except (RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    record = {"mode": "generate" if args.generate else "check", "output_sha256": sha256(data), **summary,
              "inputs": {name: sha256((root / name).read_bytes()) for name in (CLASS_RASTER, TEMPLATE)}}
    if args.generate:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
        from osgeo import ogr
        check = ogr.Open(str(target))
        if check is None or check.GetLayer(0).GetFeatureCount() != summary["polygons"]:
            print("ERROR: GDAL cannot read the written GeoJSON back", file=sys.stderr)
            return 1
    else:
        try:
            saved = target.read_bytes()
        except OSError as error:
            print(f"ERROR: saved layer cannot be read: {error}", file=sys.stderr)
            return 1
        record["saved_sha256"] = sha256(saved)
        record["identical"] = saved == data
    print(json.dumps(record, ensure_ascii=False, indent=1))
    return 0 if record.get("identical", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
