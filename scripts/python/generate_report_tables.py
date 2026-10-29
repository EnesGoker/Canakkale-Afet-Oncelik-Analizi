#!/usr/bin/env python3
"""Canonical processed katmanlardan rapora hazır tablolar üretir."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


DISTRICT_LAYER = "canakkale_districts_32635"
DISTRICT_VECTOR = Path("data/processed/admin/canakkale_districts_32635.gpkg")
MCDA_CLASS_RASTER = Path("data/processed/analysis/mcda_priority_class_32635.tif")
PIXEL_AREA_KM2 = 0.01

CLASS_LABELS = {
    1: "Çok düşük",
    2: "Düşük",
    3: "Orta",
    4: "Yüksek",
    5: "Çok yüksek",
}

RASTER_LAYERS = [
    {
        "layer_id": "earthquake_pga_score",
        "display_name": "Deprem PGA skoru",
        "role": "criterion",
        "path": Path("data/processed/analysis/earthquake_pga_score_32635.tif"),
    },
    {
        "layer_id": "fault_proximity_score",
        "display_name": "Fay yakınlık skoru",
        "role": "criterion",
        "path": Path("data/processed/analysis/fault_proximity_score_32635.tif"),
    },
    {
        "layer_id": "site_condition_score",
        "display_name": "Zemin koşulu skoru",
        "role": "criterion",
        "path": Path("data/processed/analysis/site_condition_score_32635.tif"),
    },
    {
        "layer_id": "population_exposure_score",
        "display_name": "Nüfus maruziyet skoru",
        "role": "criterion",
        "path": Path("data/processed/analysis/population_exposure_score_32635.tif"),
    },
    {
        "layer_id": "building_exposure_density_score",
        "display_name": "Yapı maruziyet yoğunluk skoru",
        "role": "criterion",
        "path": Path("data/processed/analysis/building_exposure_density_score_32635.tif"),
    },
    {
        "layer_id": "flood_score",
        "display_name": "Taşkın skoru",
        "role": "criterion",
        "path": Path("data/processed/analysis/flood_score_32635.tif"),
    },
    {
        "layer_id": "hydrography_proximity_score",
        "display_name": "Hidrografya yakınlık skoru",
        "role": "criterion",
        "path": Path("data/processed/analysis/hydrography_proximity_score_32635.tif"),
    },
    {
        "layer_id": "slope_score",
        "display_name": "Eğim skoru",
        "role": "criterion",
        "path": Path("data/processed/analysis/slope_score_32635.tif"),
    },
    {
        "layer_id": "landcover_sensitivity_score",
        "display_name": "Arazi örtüsü duyarlılık skoru",
        "role": "criterion",
        "path": Path("data/processed/analysis/landcover_sensitivity_score_32635.tif"),
    },
    {
        "layer_id": "tree_cover_score",
        "display_name": "Ağaç örtüsü skoru",
        "role": "criterion",
        "path": Path("data/processed/analysis/tree_cover_score_32635.tif"),
    },
    {
        "layer_id": "road_accessibility_difficulty_score",
        "display_name": "Yol erişim zorluğu skoru",
        "role": "criterion",
        "path": Path("data/processed/analysis/road_accessibility_difficulty_score_32635.tif"),
    },
    {
        "layer_id": "mcda_priority_score",
        "display_name": "MCDA öncelik skoru",
        "role": "mcda",
        "path": Path("data/processed/analysis/mcda_priority_score_32635.tif"),
    },
    {
        "layer_id": "mcda_priority_score_normalized",
        "display_name": "MCDA normalize öncelik skoru",
        "role": "mcda",
        "path": Path("data/processed/analysis/mcda_priority_score_normalized_32635.tif"),
    },
    {
        "layer_id": "mcda_priority_class",
        "display_name": "MCDA öncelik sınıfı",
        "role": "mcda",
        "path": MCDA_CLASS_RASTER,
    },
]


class TableError(RuntimeError):
    """Tablo üretimi QA başarısız olduğunda kullanılır."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Çanakkale MCDA projesi için canonical rapor tabloları üretir."
    )
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def tool(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise TableError(f"Gerekli tool environment variable eksik: {name}")
    return value


def command_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GDAL_PAM_ENABLED"] = "NO"
    return env


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        env=command_env(),
    )
    if result.returncode != 0:
        message = [
            f"Komut exit code {result.returncode} ile başarısız oldu:",
            " ".join(args),
        ]
        if result.stdout.strip():
            message.append("stdout:")
            message.append(result.stdout.strip())
        if result.stderr.strip():
            message.append("stderr:")
            message.append(result.stderr.strip())
        raise TableError("\n".join(message))
    return result


def gdalinfo_json(path: Path, stats: bool = False) -> dict[str, Any]:
    args = [tool("GDALINFO"), "-json"]
    if stats:
        args.append("-stats")
    args.append(str(path))
    return json.loads(run_command(args).stdout)


def ogrinfo_json(path: Path, sql: str) -> dict[str, Any]:
    args = [
        tool("OGRINFO"),
        "-json",
        "-features",
        "-dialect",
        "SQLite",
        "-sql",
        sql,
        str(path),
    ]
    return json.loads(run_command(args).stdout)


def require_inputs(project_root: Path) -> None:
    required = [DISTRICT_VECTOR, MCDA_CLASS_RASTER]
    required.extend(layer["path"] for layer in RASTER_LAYERS)
    missing = [str(path) for path in required if not (project_root / path).is_file()]
    if missing:
        raise TableError("Gerekli canonical girdiler eksik:\n" + "\n".join(missing))


def assert_close(name: str, actual: float, expected: float, tolerance: float = 1e-6) -> None:
    if abs(actual - expected) > tolerance:
        raise TableError(f"{name} uyuşmuyor: beklenen {expected}, gelen {actual}")


def raster_grid(info: dict[str, Any]) -> dict[str, Any]:
    gt = info["geoTransform"]
    width, height = info["size"]
    minx = gt[0]
    maxy = gt[3]
    maxx = gt[0] + width * gt[1]
    miny = gt[3] + height * gt[5]
    return {
        "width": int(width),
        "height": int(height),
        "gt": [float(value) for value in gt],
        "minx": float(minx),
        "miny": float(miny),
        "maxx": float(maxx),
        "maxy": float(maxy),
        "pixel_size_x": float(gt[1]),
        "pixel_size_y": abs(float(gt[5])),
    }


def validate_common_grid(reference: dict[str, Any], info: dict[str, Any], rel_path: Path) -> None:
    grid = raster_grid(info)
    if grid["width"] != reference["width"] or grid["height"] != reference["height"]:
        raise TableError(f"{rel_path} için raster boyutu uyuşmuyor")

    for idx, (actual, expected) in enumerate(zip(grid["gt"], reference["gt"])):
        assert_close(f"GeoTransform[{idx}] for {rel_path}", actual, expected, tolerance=1e-4)


def translate_to_envi(src: Path, dst: Path, output_type: str) -> None:
    run_command(
        [
            tool("GDAL_TRANSLATE"),
            "-q",
            "-of",
            "ENVI",
            "-ot",
            output_type,
            str(src),
            str(dst),
        ]
    )


def read_array(path: Path, dtype: np.dtype[Any], shape: tuple[int, int]) -> np.ndarray:
    array = np.fromfile(path, dtype=dtype)
    expected = shape[0] * shape[1]
    if array.size != expected:
        raise TableError(f"{path} için beklenmeyen array boyutu: beklenen {expected}, gelen {array.size}")
    return array.reshape(shape)


def create_district_id_layer(project_root: Path, temp_dir: Path) -> Path:
    output = temp_dir / "district_ids.gpkg"
    sql = (
        "SELECT CAST(fid AS INTEGER) AS qa_district_id, "
        "district_name, "
        "ST_Area(geom)/1000000.0 AS district_area_km2, "
        "geom "
        f"FROM {DISTRICT_LAYER}"
    )
    run_command(
        [
            tool("OGR2OGR"),
            "-f",
            "GPKG",
            str(output),
            str(project_root / DISTRICT_VECTOR),
            "-dialect",
            "SQLite",
            "-sql",
            sql,
            "-nln",
            "district_ids",
            "-lco",
            "FID=gpkg_fid",
        ]
    )
    return output


def rasterize_district_ids(
    district_layer: Path,
    output_raster: Path,
    reference_grid: dict[str, Any],
) -> None:
    run_command(
        [
            tool("GDAL_RASTERIZE"),
            "-q",
            "-a",
            "qa_district_id",
            "-tr",
            str(reference_grid["pixel_size_x"]),
            str(reference_grid["pixel_size_y"]),
            "-te",
            str(reference_grid["minx"]),
            str(reference_grid["miny"]),
            str(reference_grid["maxx"]),
            str(reference_grid["maxy"]),
            "-a_nodata",
            "0",
            "-ot",
            "Int16",
            "-of",
            "GTiff",
            "-l",
            "district_ids",
            str(district_layer),
            str(output_raster),
        ]
    )


def load_districts(project_root: Path) -> list[dict[str, Any]]:
    sql = (
        "SELECT CAST(fid AS INTEGER) AS qa_district_id, "
        "district_name, "
        "ST_Area(geom)/1000000.0 AS district_area_km2 "
        f"FROM {DISTRICT_LAYER} ORDER BY fid"
    )
    info = ogrinfo_json(project_root / DISTRICT_VECTOR, sql)
    features = info["layers"][0].get("features", [])
    districts = []
    for feature in features:
        props = feature["properties"]
        districts.append(
            {
                "district_id": int(props["qa_district_id"]),
                "district_name": props["district_name"],
                "district_area_km2": float(props["district_area_km2"]),
            }
        )

    expected_ids = list(range(1, 13))
    ids = [district["district_id"] for district in districts]
    if ids != expected_ids:
        raise TableError(f"Beklenen district id değerleri 1..12, gelen {ids}")
    return districts


def build_class_distribution(class_array: np.ndarray) -> tuple[list[dict[str, Any]], dict[int, int]]:
    valid_mask = (class_array >= 1) & (class_array <= 5)
    invalid_values = sorted(int(value) for value in np.unique(class_array[~valid_mask]) if value != 0)
    if invalid_values:
        raise TableError(f"0..5 dışında beklenmeyen MCDA class değerleri: {invalid_values}")

    valid_pixels = int(valid_mask.sum())
    if valid_pixels == 0:
        raise TableError("MCDA class rasterında geçerli class pikseli yok.")

    rows = []
    counts: dict[int, int] = {}
    for class_value, label in CLASS_LABELS.items():
        pixel_count = int((class_array == class_value).sum())
        counts[class_value] = pixel_count
        area = pixel_count * PIXEL_AREA_KM2
        rows.append(
            {
                "class_value": class_value,
                "class_label": label,
                "pixel_count": pixel_count,
                "area_km2": area,
                "share_of_aoi_percent": area / (valid_pixels * PIXEL_AREA_KM2) * 100.0,
            }
        )

    if sum(counts.values()) != valid_pixels:
        raise TableError("Class dağılımı geçerli MCDA piksellerinin toplamıyla eşleşmiyor.")

    return rows, counts


def build_district_class_table(
    class_array: np.ndarray,
    district_array: np.ndarray,
    districts: list[dict[str, Any]],
    global_class_counts: dict[int, int],
) -> tuple[list[dict[str, Any]], int]:
    valid_class_mask = (class_array >= 1) & (class_array <= 5)
    missing_district_pixels = int(((district_array == 0) & valid_class_mask).sum())
    if missing_district_pixels != 0:
        raise TableError(f"District id değeri olmayan class pikselleri: {missing_district_pixels}")

    district_ids = sorted(int(value) for value in np.unique(district_array[district_array > 0]))
    if district_ids != list(range(1, 13)):
        raise TableError(f"Beklenen rasterize district id değerleri 1..12, gelen {district_ids}")

    rows = []
    class_totals = {class_value: 0 for class_value in CLASS_LABELS}
    for district in districts:
        district_mask = district_array == district["district_id"]
        for class_value, label in CLASS_LABELS.items():
            pixel_count = int((district_mask & (class_array == class_value)).sum())
            class_totals[class_value] += pixel_count
            area = pixel_count * PIXEL_AREA_KM2
            global_count = global_class_counts[class_value]
            rows.append(
                {
                    "district_id": district["district_id"],
                    "district_name": district["district_name"],
                    "district_area_km2": district["district_area_km2"],
                    "class_value": class_value,
                    "class_label": label,
                    "pixel_count": pixel_count,
                    "area_km2": area,
                    "district_share_percent": area / district["district_area_km2"] * 100.0,
                    "province_class_share_percent": (
                        pixel_count / global_count * 100.0 if global_count else 0.0
                    ),
                }
            )

    if len(rows) != 60:
        raise TableError(f"Beklenen 60 district-class satırı, gelen {len(rows)}")

    if class_totals != global_class_counts:
        raise TableError(
            "District class toplamları global class toplamlarıyla eşleşmiyor: "
            f"{class_totals} vs {global_class_counts}"
        )

    return rows, missing_district_pixels


def numeric_stat(band: dict[str, Any], key: str) -> float | None:
    value = band.get(key)
    if value is None:
        stats = band.get("metadata", {}).get("", {})
        value = stats.get(f"STATISTICS_{key.upper()}")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def valid_percent(band: dict[str, Any]) -> float | None:
    value = band.get("metadata", {}).get("", {}).get("STATISTICS_VALID_PERCENT")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_raster_statistics(project_root: Path, reference_grid: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for layer in RASTER_LAYERS:
        path = project_root / layer["path"]
        info = gdalinfo_json(path, stats=True)
        validate_common_grid(reference_grid, info, layer["path"])
        band = info["bands"][0]
        rows.append(
            {
                "layer_id": layer["layer_id"],
                "display_name": layer["display_name"],
                "role": layer["role"],
                "path": str(layer["path"]),
                "width": int(info["size"][0]),
                "height": int(info["size"][1]),
                "pixel_size_x_m": reference_grid["pixel_size_x"],
                "pixel_size_y_m": reference_grid["pixel_size_y"],
                "nodata": band.get("noDataValue"),
                "minimum": numeric_stat(band, "minimum"),
                "maximum": numeric_stat(band, "maximum"),
                "mean": numeric_stat(band, "mean"),
                "stddev": numeric_stat(band, "stdDev"),
                "valid_percent": valid_percent(band),
            }
        )

    criterion_count = sum(1 for row in rows if row["role"] == "criterion")
    if criterion_count != 11:
        raise TableError(f"Beklenen 11 criterion rasterı, gelen {criterion_count}")
    return rows


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.4f}"
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) for column in columns})


def write_markdown_table(
    path: Path,
    title: str,
    rows: list[dict[str, Any]],
    columns: list[str],
    note: str,
) -> None:
    with path.open("w", encoding="utf-8") as stream:
        stream.write(f"# {title}\n\n")
        stream.write(f"{note}\n\n")
        stream.write("| " + " | ".join(columns) + " |\n")
        stream.write("| " + " | ".join("---" for _ in columns) + " |\n")
        for row in rows:
            values = [format_value(row.get(column)).replace("|", "\\|") for column in columns]
            stream.write("| " + " | ".join(values) + " |\n")


def write_manifest(
    path: Path,
    output_dir: Path,
    class_rows: list[dict[str, Any]],
    district_rows: list[dict[str, Any]],
    raster_rows: list[dict[str, Any]],
    missing_district_pixels: int,
) -> None:
    valid_pixels = sum(int(row["pixel_count"]) for row in class_rows)
    valid_area = sum(float(row["area_km2"]) for row in class_rows)
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    files = [
        "mcda_class_distribution.csv",
        "mcda_class_distribution.md",
        "mcda_class_area_by_district.csv",
        "mcda_class_area_by_district.md",
        "criterion_raster_statistics.csv",
        "criterion_raster_statistics.md",
        "report_tables_manifest.md",
    ]
    output_label = str(output_dir) if not output_dir.is_absolute() else output_dir.name

    with path.open("w", encoding="utf-8") as stream:
        stream.write("# Rapor Tabloları Manifesti\n\n")
        stream.write(f"Üretim zamanı (UTC): `{generated}`\n\n")
        stream.write("Girdi seviyesi: canonical `data/processed` katmanları.\n\n")
        stream.write("## Dosyalar\n\n")
        for file_name in files:
            stream.write(f"- `{output_label}/{file_name}`\n")
        stream.write("\n## QA Özeti\n\n")
        stream.write(f"- MCDA class satırları: `{len(class_rows)}`\n")
        stream.write(f"- İlçe-class satırları: `{len(district_rows)}`\n")
        stream.write(f"- Raster istatistik satırları: `{len(raster_rows)}`\n")
        stream.write(f"- Geçerli MCDA class pikselleri: `{valid_pixels}`\n")
        stream.write(f"- Geçerli MCDA class alanı (km2): `{valid_area:.2f}`\n")
        stream.write(f"- District id olmayan class pikselleri: `{missing_district_pixels}`\n")


def generate(project_root: Path, output_dir: Path) -> None:
    project_root = project_root.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    require_inputs(project_root)

    class_info = gdalinfo_json(project_root / MCDA_CLASS_RASTER)
    reference_grid = raster_grid(class_info)
    shape = (reference_grid["height"], reference_grid["width"])

    with tempfile.TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)
        class_bin = temp_dir / "mcda_priority_class.bin"
        translate_to_envi(project_root / MCDA_CLASS_RASTER, class_bin, "Byte")
        class_array = read_array(class_bin, np.dtype("uint8"), shape)

        district_layer = create_district_id_layer(project_root, temp_dir)
        district_tif = temp_dir / "district_ids.tif"
        district_bin = temp_dir / "district_ids.bin"
        rasterize_district_ids(district_layer, district_tif, reference_grid)
        translate_to_envi(district_tif, district_bin, "Int16")
        district_array = read_array(district_bin, np.dtype("int16"), shape)

        districts = load_districts(project_root)
        class_rows, global_class_counts = build_class_distribution(class_array)
        district_rows, missing_district_pixels = build_district_class_table(
            class_array, district_array, districts, global_class_counts
        )
        raster_rows = build_raster_statistics(project_root, reference_grid)

    class_columns = [
        "class_value",
        "class_label",
        "pixel_count",
        "area_km2",
        "share_of_aoi_percent",
    ]
    district_columns = [
        "district_id",
        "district_name",
        "district_area_km2",
        "class_value",
        "class_label",
        "pixel_count",
        "area_km2",
        "district_share_percent",
        "province_class_share_percent",
    ]
    raster_columns = [
        "layer_id",
        "display_name",
        "role",
        "path",
        "width",
        "height",
        "pixel_size_x_m",
        "pixel_size_y_m",
        "nodata",
        "minimum",
        "maximum",
        "mean",
        "stddev",
        "valid_percent",
    ]

    write_csv(output_dir / "mcda_class_distribution.csv", class_rows, class_columns)
    write_markdown_table(
        output_dir / "mcda_class_distribution.md",
        "MCDA Sınıf Dağılımı",
        class_rows,
        class_columns,
        "Alan değerleri canonical 100 m grid hücre alanı olan 0.01 km2 üzerinden hesaplanır.",
    )

    write_csv(output_dir / "mcda_class_area_by_district.csv", district_rows, district_columns)
    write_markdown_table(
        output_dir / "mcda_class_area_by_district.md",
        "İlçeye Göre MCDA Sınıf Alanı",
        district_rows,
        district_columns,
        "Satırlar 12 ilçeyi ve 1-5 MCDA sınıflarını kapsar.",
    )

    write_csv(output_dir / "criterion_raster_statistics.csv", raster_rows, raster_columns)
    write_markdown_table(
        output_dir / "criterion_raster_statistics.md",
        "Kriter Raster İstatistikleri",
        raster_rows,
        raster_columns,
        "Tüm rasterlar, istatistikler yazılmadan önce canonical MCDA gridine göre doğrulanır.",
    )

    write_manifest(
        output_dir / "report_tables_manifest.md",
        output_dir,
        class_rows,
        district_rows,
        raster_rows,
        missing_district_pixels,
    )

    print("Rapor tabloları üretildi:")
    print(f"- çıktı_dizini: {output_dir}")
    print(f"- mcda_class_satırları: {len(class_rows)}")
    print(f"- district_class_satırları: {len(district_rows)}")
    print(f"- raster_istatistik_satırları: {len(raster_rows)}")
    print(f"- geçerli_mcda_class_pikselleri: {sum(row['pixel_count'] for row in class_rows)}")
    print(f"- district_id_olmayan_class_pikselleri: {missing_district_pixels}")


def main() -> int:
    args = parse_args()
    try:
        generate(args.project_root, args.output_dir)
    except TableError as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
