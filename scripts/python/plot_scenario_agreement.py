#!/usr/bin/env python3
"""Render a geographic map of high-priority agreement across three scenarios.

--check validates saved map/source hashes without importing Matplotlib.
--generate requires a new or empty explicit output directory; no old output
is replaced. Formal QGIS layout/atlas integration is a separate step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
os.environ["GDAL_PAM_ENABLED"] = "NO"

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = Path("outputs/analysis/scenario_agreement_v1")
MAP_DIR = Path("outputs/figures/scenario_agreement_v1")
COUNT_FILE = "scenario_agreement_count_32635.tif"
MEMBERSHIP_FILE = "scenario_agreement_membership_32635.tif"
ANALYSIS_MANIFEST = "scenario_agreement_manifest.json"
SOURCE_FILES = (COUNT_FILE, MEMBERSHIP_FILE, "agreement_count_summary.csv",
                "agreement_membership_summary.csv", "scenario_high_area_comparison.csv")
BASELINE_FILE = Path("config/analysis_baseline_v1.json")
TEMPLATE = Path("data/processed/analysis/analysis_template_100m_32635.tif")
DISTRICTS = Path("data/processed/admin/canakkale_districts_32635.gpkg")
PNG_FILE = "scenario_high_agreement.png"
PDF_FILE = "scenario_high_agreement.pdf"
MAP_MANIFEST = "scenario_high_agreement_map_manifest.json"
COLORS = ["#e2e5e9", "#f8d36a", "#e98747", "#542788"]
LABELS = ["Hiçbir senaryoda", "Yalnız 1 senaryoda", "Yalnız 2 senaryoda", "Üç senaryoda da"]


def file_record(path, name=None):
    content = path.read_bytes()
    return {"path": name or path.name, "size": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def read_sources(directory, root=ROOT):
    """Read the verified package and its template/admin references, read-only."""
    import numpy as np
    from osgeo import gdal, ogr, osr
    gdal.UseExceptions(); ogr.UseExceptions(); osr.UseExceptions()
    directory, root = Path(directory), Path(root)
    manifest = json.loads((directory / ANALYSIS_MANIFEST).read_text(encoding="utf-8"))
    baseline = json.loads((root / BASELINE_FILE).read_text(encoding="utf-8"))
    if manifest.get("format_version") != 1:
        raise ValueError("Unsupported scenario analysis manifest")
    baseline_id = manifest.get("baseline", {}).get("baseline_id", manifest.get("baseline_id"))
    if baseline_id != baseline["baseline_id"]:
        raise ValueError("Map source and current frozen baseline identity differ")
    if manifest.get("baseline", {}).get("baseline_manifest_sha256") != file_record(root / BASELINE_FILE)["sha256"]:
        raise ValueError("Map source refers to a different frozen baseline manifest checksum")
    records = manifest["outputs"]
    if len(records) != len(SOURCE_FILES) or {row["path"] for row in records} != set(SOURCE_FILES):
        raise ValueError("Analysis manifest must identify two rasters and three CSVs")
    for record in records:
        if file_record(directory / record["path"]) != record:
            raise ValueError(f"Source checksum/size mismatch: {record['path']}")
    frozen = {row["path"]: row for row in baseline["files"]}
    for name in (TEMPLATE, DISTRICTS):
        if file_record(root / name, name.as_posix()) != frozen[name.as_posix()]:
            raise ValueError(f"Changed frozen map reference: {name.as_posix()}")
    template = gdal.OpenEx(str(root / TEMPLATE), gdal.OF_RASTER | gdal.OF_READONLY)
    if template is None:
        raise ValueError("Cannot open map template")
    aoi = template.GetRasterBand(1).ReadAsArray() == 1
    if not aoi.any() or int(aoi.sum()) != baseline["expected_aoi_cells"]:
        raise ValueError("Map AOI cell count differs from the baseline")
    grid, projection = template.GetGeoTransform(), template.GetProjectionRef()
    expected_crs = osr.SpatialReference(); expected_crs.ImportFromEPSG(32635)
    current_crs = osr.SpatialReference(); current_crs.ImportFromWkt(projection)
    if not current_crs.IsSame(expected_crs) or grid[1] != 100 or grid[5] != -100 or grid[2] != 0 or grid[4] != 0:
        raise ValueError("Map requires a north-up EPSG:32635 100 m grid")
    arrays = []
    for name, maximum in ((COUNT_FILE, 3), (MEMBERSHIP_FILE, 7)):
        dataset = gdal.OpenEx(str(directory / name), gdal.OF_RASTER | gdal.OF_READONLY)
        if dataset is None or dataset.RasterCount != 1:
            raise ValueError(f"Missing/single-band map raster required: {name}")
        band = dataset.GetRasterBand(1); array = band.ReadAsArray()
        crs = osr.SpatialReference(); crs.ImportFromWkt(dataset.GetProjectionRef())
        if array.shape != aoi.shape or dataset.GetGeoTransform() != grid or not crs.IsSame(current_crs):
            raise ValueError(f"Map raster grid/CRS differs: {name}")
        if band.DataType != gdal.GDT_Byte or band.GetNoDataValue() != 255:
            raise ValueError(f"Map raster must be Byte with NoData 255: {name}")
        if not np.array_equal(band.GetMaskBand().ReadAsArray() != 0, aoi):
            raise ValueError(f"Map raster mask differs from the template AOI: {name}")
        if np.any(array[aoi] > maximum) or np.any(array[~aoi] != 255):
            raise ValueError(f"Map raster class values or outside NoData differ: {name}")
        arrays.append(array)
    popcounts = np.array([0, 1, 1, 2, 1, 2, 2, 3], dtype=np.uint8)
    if not np.array_equal(arrays[0][aoi], popcounts[arrays[1][aoi]]):
        raise ValueError("Agreement count differs from scenario membership bits")
    vector = ogr.Open(str(root / DISTRICTS), 0)
    layer = vector.GetLayerByName("canakkale_districts_32635") if vector else None
    if layer is None or not layer.GetSpatialRef().IsSame(current_crs):
        raise ValueError("Missing district layer or mismatched map CRS")
    geometries = []
    for feature in layer:
        geometry = feature.GetGeometryRef()
        name = feature.GetField("district_name")
        if geometry is None or geometry.IsEmpty() or not isinstance(name, str) or not name:
            raise ValueError("District map geometry/name is missing")
        if geometry.GetGeometryName() not in ("POLYGON", "MULTIPOLYGON"):
            raise ValueError("District map geometry must be a polygon or multipolygon")
        point = geometry.PointOnSurface()
        geometries.append({"name": name, "geometry": json.loads(geometry.ExportToJson()), "point": [point.GetX(), point.GetY()]})
    if not geometries or len({item["name"] for item in geometries}) != len(geometries):
        raise ValueError("District map names must be nonempty and unique")
    sources = [file_record(directory / name) for name in (*SOURCE_FILES, ANALYSIS_MANIFEST)]
    sources += [file_record(root / name, name.as_posix()) for name in (BASELINE_FILE, TEMPLATE, DISTRICTS)]
    return {"array": arrays[0], "aoi": aoi, "grid": grid, "baseline_id": baseline_id,
            "counts": np.bincount(arrays[0][aoi], minlength=4).tolist(),
            "districts": geometries, "sources": sources}


def check_saved_map(sources, output_dir):
    output_dir = Path(output_dir)
    manifest = json.loads((output_dir / MAP_MANIFEST).read_text(encoding="utf-8"))
    expected = {"format_version": 1, "baseline_id": sources["baseline_id"], "sources": sources["sources"],
                "class_counts": sources["counts"], "colors": COLORS, "labels_tr": LABELS,
                "outside_nodata": 255, "grid_crs": "EPSG:32635", "grid_metres": 100,
                "page": "A3 landscape", "png_dpi": 300, "display_padding_metres": 4000}
    for name, value in expected.items():
        if manifest.get(name) != value:
            raise ValueError(f"Map source/rendering contract differs: {name}")
    records = manifest.get("outputs", [])
    if len(records) != 2 or {row["path"] for row in records} != {PNG_FILE, PDF_FILE}:
        raise ValueError("Map manifest must identify PNG and PDF")
    for record in records:
        if file_record(output_dir / record["path"]) != record:
            raise ValueError(f"Map checksum/size mismatch: {record['path']}")
    return {"passed": True, "checked_files": 3, "message": "Ortaklık haritası ve kaynak checksum'ları eşleşiyor."}


def _format_number(value, decimals=2):
    return f"{value:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def generate_map(sources, output_dir):
    import numpy as np
    output_dir = Path(output_dir).absolute()
    if output_dir.is_symlink() or (output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir()))):
        raise ValueError("Map output directory must be empty or new; existing files are never overwritten")
    if not output_dir.parent.is_dir():
        raise ValueError("Map output directory parent must already exist")
    published, created_directory = [], False
    with tempfile.TemporaryDirectory(prefix="scenario-map-fonts-") as scratch:
        prior = os.environ.get("MPLCONFIGDIR"); os.environ["MPLCONFIGDIR"] = scratch
        try:
            import matplotlib
            matplotlib.use("Agg")
            from matplotlib import pyplot as plt
            from matplotlib.colors import ListedColormap, BoundaryNorm
            from matplotlib.patches import Rectangle
            from matplotlib import patheffects
            with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 11, "pdf.fonttype": 42}):
                fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4), facecolor="white")
                axis = fig.add_axes((0.035, 0.10, 0.655, 0.81), facecolor="#f2f7fa")
                array, grid = sources["array"], sources["grid"]
                height, width = array.shape
                extent = (grid[0], grid[0] + width * grid[1], grid[3] + height * grid[5], grid[3])
                masked = np.ma.array(array, mask=~sources["aoi"])
                cmap = ListedColormap(COLORS); cmap.set_bad((0, 0, 0, 0))
                axis.imshow(masked, cmap=cmap, norm=BoundaryNorm([-0.5, .5, 1.5, 2.5, 3.5], 4),
                            extent=extent, origin="upper", interpolation="nearest", rasterized=True)
                for district in sources["districts"]:
                    geometry = district["geometry"]
                    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
                    for polygon in polygons:
                        for ring in polygon:
                            points = np.asarray(ring)
                            axis.plot(points[:, 0], points[:, 1], color="#4b5963", linewidth=0.48)
                    x, y = district["point"]
                    label = district["name"].replace("Çanakkale Merkez", "Merkez")
                    axis.text(x, y, label, ha="center", va="center", fontsize=8.5, color="#25303a",
                              path_effects=[patheffects.withStroke(linewidth=2.7, foreground="white", alpha=.94)])
                axis.set_xlim(extent[0] - 4000, extent[1] + 4000)
                axis.set_ylim(extent[2] - 4000, extent[3] + 4000)
                axis.set_xticks([]); axis.set_yticks([])
                for spine in axis.spines.values(): spine.set_edgecolor("#d4dde3")
                # Grid north and a 20 km UTM scale; neither needs a web basemap.
                arrow_x, arrow_y = extent[1] - 7000, extent[3] - 18000
                axis.annotate("", xy=(arrow_x, arrow_y + 10000), xytext=(arrow_x, arrow_y),
                              arrowprops={"arrowstyle": "-|>", "color": "#26333d", "lw": 1.4})
                axis.text(arrow_x, arrow_y + 12000, "K", ha="center", fontsize=12)
                axis.text(arrow_x, arrow_y - 3500, "Grid kuzeyi", ha="center", fontsize=7, color="#465665")
                scale_x, scale_y = extent[0] + 7000, extent[2] + 7000
                for index in range(2):
                    axis.add_patch(Rectangle((scale_x + index * 10000, scale_y), 10000, 1400,
                                             facecolor="#26333d" if index == 0 else "white", edgecolor="#26333d", linewidth=.8))
                for index in range(3):
                    axis.text(scale_x + index * 10000, scale_y + 2500, str(index * 10) + (" km" if index == 2 else ""), ha="center", fontsize=8)
                fig.text(.045, .965, "Çanakkale · Üç senaryoda yüksek öncelik ortaklığı", fontsize=22, weight="bold", color="#17222c")
                fig.text(.045, .932, "Baseline · Deprem ağırlıklı · Eşit ağırlıklı  |  100 m grid  |  EPSG:32635", fontsize=11.5, color="#465665")
                panel = fig.add_axes((.725, .15, .25, .72)); panel.axis("off")
                panel.text(0, 1, "Kaç senaryoda yüksek?", fontsize=16, weight="bold", color="#17222c", va="top")
                panel.text(0, .945, "Yüksek + çok yüksek sınıfların\naynı hücredeki ortaklığı", fontsize=11, color="#465665", va="top", linespacing=1.6)
                total = sum(sources["counts"])
                for value, (label, color, count) in enumerate(zip(LABELS, COLORS, sources["counts"])):
                    y = .825 - value * .135
                    panel.add_patch(Rectangle((0, y - .036), .07, .048, facecolor=color, edgecolor="#b2bbc2", linewidth=.5))
                    panel.text(.11, y, f"{value} · {label}", fontsize=11.5, weight="bold", va="center")
                    panel.text(.11, y - .047, f"{_format_number(count * .01)} km²  ·  %{_format_number(count / total * 100)}", fontsize=10.5, color="#465665")
                panel.axhline(.295, color="#d4dde3", linewidth=.8)
                panel.text(0, .26, "Nasıl okunmalı?", fontsize=12, weight="bold", va="top")
                panel.text(0, .21, "Yüksek sınıflar her senaryonun\nkendi göreli ölçeğine aittir.\nOrtaklık, seçilmiş üç senaryoyu\nkarşılaştırır.\n\n0, güvenli alan anlamına gelmez.\nAfet riskinin doğrulaması değildir.", fontsize=10.5, color="#465665", va="top", linespacing=1.55)
                fig.text(.045, .057, "Kaynak: Projenin 11 kriterli MCDA girdileri; idari geometri HGM, ilçe adları OSM. Sınırlar resmî nitelik taşımaz.", fontsize=9, color="#465665")
                fig.text(.045, .034, "Senaryo karşılaştırması ağırlık ve yeniden ölçeklemenin birleşik etkisini içerir.  |  Hazırlayan: Enes Göker · 2026", fontsize=9, color="#465665")
                try:
                    with tempfile.TemporaryDirectory(prefix=".scenario-map-stage-", dir=output_dir.parent) as staging:
                        stage = Path(staging)
                        fig.savefig(stage / PNG_FILE, dpi=300, facecolor="white")
                        fig.savefig(stage / PDF_FILE, dpi=300, facecolor="white", metadata={"Title": "Çanakkale üç senaryoda yüksek öncelik ortaklığı", "Author": "Enes Göker", "CreationDate": None, "ModDate": None})
                        manifest = {"format_version": 1, "baseline_id": sources["baseline_id"], "sources": sources["sources"],
                                    "class_counts": sources["counts"], "colors": COLORS, "labels_tr": LABELS,
                                    "outside_nodata": 255, "grid_crs": "EPSG:32635", "grid_metres": 100,
                                    "matplotlib": matplotlib.__version__, "page": "A3 landscape", "png_dpi": 300, "display_padding_metres": 4000,
                                    "outputs": [file_record(stage / name) for name in (PNG_FILE, PDF_FILE)]}
                        (stage / MAP_MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
                        try:
                            output_dir.mkdir(); created_directory = True
                        except FileExistsError:
                            if output_dir.is_symlink() or not output_dir.is_dir() or any(output_dir.iterdir()):
                                raise ValueError("Map output target became nonempty during generation")
                        for name in (PNG_FILE, PDF_FILE, MAP_MANIFEST):
                            target = output_dir / name; os.link(stage / name, target)
                            published.append((target, target.stat().st_ino))
                finally:
                    plt.close(fig)
        except BaseException:
            for path, inode in reversed(published):
                try:
                    if path.lstat().st_ino == inode: path.unlink()
                except FileNotFoundError:
                    pass
            if created_directory:
                try: output_dir.rmdir()
                except OSError: pass
            raise
        finally:
            if prior is None: os.environ.pop("MPLCONFIGDIR", None)
            else: os.environ["MPLCONFIGDIR"] = prior
    return [PNG_FILE, PDF_FILE, MAP_MANIFEST]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true"); modes.add_argument("--generate", action="store_true")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--source-dir", type=Path); parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.generate and args.output_dir is None: parser.error("--generate requires explicit --output-dir")
    try:
        sources = read_sources(args.source_dir or args.project_root / SOURCE_DIR, args.project_root)
        if args.generate:
            result = {"passed": True, "outputs": generate_map(sources, args.output_dir)}
        else:
            result = check_saved_map(sources, args.output_dir or args.project_root / MAP_DIR)
        code = 0
    except ImportError as error:
        result, code = {"passed": False, "message": f"Required map dependency unavailable: {error}"}, 2
    except (OSError, ValueError, KeyError, TypeError, IndexError, RuntimeError) as error:
        result, code = {"passed": False, "message": str(error)}, 1
    if args.json: print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    else: print(("GEÇTİ: " if code == 0 else "ATLANDI: " if code == 2 else "HATA: ") + result.get("message", ", ".join(result.get("outputs", []))))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
