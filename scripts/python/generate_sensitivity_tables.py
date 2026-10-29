#!/usr/bin/env python3
"""MCDA ağırlık senaryoları için küçük robustness tabloları üretir."""

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


WEIGHT_CONFIG = Path("config/mcda_weights.tsv")
DISTRICT_LAYER = "canakkale_districts_32635"
DISTRICT_VECTOR = Path("data/processed/admin/canakkale_districts_32635.gpkg")
BASELINE_CLASS_RASTER = Path("data/processed/analysis/mcda_priority_class_32635.tif")
PIXEL_AREA_KM2 = 0.01

SCENARIO_ORDER = ["baseline", "earthquake-heavy", "equal-weight"]
EXPECTED_CRITERIA = [
    "earthquake_pga_score",
    "fault_proximity_score",
    "site_condition_score",
    "population_exposure_score",
    "building_exposure_density_score",
    "flood_score",
    "hydrography_proximity_score",
    "slope_score",
    "landcover_sensitivity_score",
    "tree_cover_score",
    "road_accessibility_difficulty_score",
]
WEIGHT_COLUMNS = [
    "scenario_id",
    "scenario_label",
    "scenario_role",
    "criterion_order",
    "criterion_id",
    "display_name_tr",
    "raster_path",
    "weight",
    "block_tr",
    "note_tr",
]
CLASS_LABELS = {
    1: "Çok düşük",
    2: "Düşük",
    3: "Orta",
    4: "Yüksek",
    5: "Çok yüksek",
}


class SensitivityError(RuntimeError):
    """Sensitivity tablo üretimi QA başarısız olduğunda kullanılır."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Çanakkale MCDA ağırlık senaryoları için robustness tabloları üretir."
    )
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def tool(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SensitivityError(f"Gerekli tool environment variable eksik: {name}")
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
        raise SensitivityError("\n".join(message))
    return result


def gdalinfo_json(path: Path) -> dict[str, Any]:
    return json.loads(run_command([tool("GDALINFO"), "-json", str(path)]).stdout)


def ogrinfo_json(path: Path, sql: str) -> dict[str, Any]:
    return json.loads(
        run_command(
            [
                tool("OGRINFO"),
                "-json",
                "-features",
                "-dialect",
                "SQLite",
                "-sql",
                sql,
                str(path),
            ]
        ).stdout
    )


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


def assert_close(name: str, actual: float, expected: float, tolerance: float = 1e-6) -> None:
    if abs(actual - expected) > tolerance:
        raise SensitivityError(f"{name} uyuşmuyor: beklenen {expected}, gelen {actual}")


def validate_common_grid(reference: dict[str, Any], info: dict[str, Any], rel_path: Path) -> None:
    grid = raster_grid(info)
    if grid["width"] != reference["width"] or grid["height"] != reference["height"]:
        raise SensitivityError(f"{rel_path} için raster boyutu uyuşmuyor")
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
        raise SensitivityError(f"{path} için beklenmeyen array boyutu: beklenen {expected}, gelen {array.size}")
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


def rasterize_district_ids(district_layer: Path, output_raster: Path, reference_grid: dict[str, Any]) -> None:
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
    ids = [district["district_id"] for district in districts]
    if ids != list(range(1, 13)):
        raise SensitivityError(f"Beklenen district id değerleri 1..12, gelen {ids}")
    return districts


def load_weight_scenarios(project_root: Path) -> dict[str, dict[str, Any]]:
    path = project_root / WEIGHT_CONFIG
    if not path.is_file():
        raise SensitivityError(f"MCDA ağırlık config eksik: {WEIGHT_CONFIG}")

    scenarios: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != WEIGHT_COLUMNS:
            raise SensitivityError("MCDA ağırlık config kolonları beklenen sözleşmeyle eşleşmiyor.")

        for row in reader:
            scenario_id = row["scenario_id"]
            scenarios.setdefault(
                scenario_id,
                {
                    "scenario_id": scenario_id,
                    "scenario_label": row["scenario_label"],
                    "scenario_role": row["scenario_role"],
                    "criteria": [],
                },
            )
            if scenarios[scenario_id]["scenario_label"] != row["scenario_label"]:
                raise SensitivityError(f"Senaryo etiketi tutarsız: {scenario_id}")
            try:
                order = int(row["criterion_order"])
                weight = float(row["weight"])
            except ValueError as exc:
                raise SensitivityError(f"Geçersiz ağırlık satırı: {scenario_id}/{row['criterion_id']}") from exc
            if weight < 0 or weight > 1:
                raise SensitivityError(f"Ağırlık 0-1 aralığı dışında: {scenario_id}/{row['criterion_id']}")
            scenarios[scenario_id]["criteria"].append(
                {
                    "order": order,
                    "criterion_id": row["criterion_id"],
                    "display_name": row["display_name_tr"],
                    "raster_path": Path(row["raster_path"]),
                    "weight": weight,
                }
            )

    if sorted(scenarios) != sorted(SCENARIO_ORDER):
        raise SensitivityError(f"Beklenen senaryolar {SCENARIO_ORDER}, gelen {sorted(scenarios)}")

    for scenario_id in SCENARIO_ORDER:
        criteria = sorted(scenarios[scenario_id]["criteria"], key=lambda item: item["order"])
        ids = [criterion["criterion_id"] for criterion in criteria]
        if ids != EXPECTED_CRITERIA:
            raise SensitivityError(f"{scenario_id} kriter seti beklenen değerlerle eşleşmiyor: {ids}")
        total = sum(float(criterion["weight"]) for criterion in criteria)
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            raise SensitivityError(f"{scenario_id} ağırlık toplamı 1.00 değil: {total:.12f}")
        scenarios[scenario_id]["criteria"] = criteria

    return {scenario_id: scenarios[scenario_id] for scenario_id in SCENARIO_ORDER}


def require_inputs(project_root: Path, scenarios: dict[str, dict[str, Any]]) -> None:
    required = [DISTRICT_VECTOR, BASELINE_CLASS_RASTER]
    for scenario in scenarios.values():
        required.extend(criterion["raster_path"] for criterion in scenario["criteria"])
    missing = sorted({str(path) for path in required if not (project_root / path).is_file()})
    if missing:
        raise SensitivityError("Gerekli canonical girdiler eksik:\n" + "\n".join(missing))


def classify_normalized(score: np.ndarray, valid_mask: np.ndarray) -> np.ndarray:
    class_array = np.zeros(score.shape, dtype=np.uint8)
    class_array[valid_mask & (score < 0.2)] = 1
    class_array[valid_mask & (score >= 0.2) & (score < 0.4)] = 2
    class_array[valid_mask & (score >= 0.4) & (score < 0.6)] = 3
    class_array[valid_mask & (score >= 0.6) & (score < 0.8)] = 4
    class_array[valid_mask & (score >= 0.8)] = 5
    return class_array


def weighted_score(
    scenario: dict[str, Any],
    criterion_arrays: dict[str, np.ndarray],
    valid_mask: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    raw = np.zeros(valid_mask.shape, dtype=np.float32)
    for criterion in scenario["criteria"]:
        raw += criterion_arrays[criterion["criterion_id"]] * np.float32(criterion["weight"])

    valid_raw = raw[valid_mask]
    raw_min = float(np.min(valid_raw))
    raw_max = float(np.max(valid_raw))
    raw_range = raw_max - raw_min
    if raw_range <= 0:
        raise SensitivityError(f"{scenario['scenario_id']} raw score range geçersiz: {raw_range}")

    normalized = np.zeros(raw.shape, dtype=np.float32)
    normalized[valid_mask] = np.clip((raw[valid_mask] - raw_min) / raw_range, 0.0, 1.0)
    stats = {
        "raw_min": raw_min,
        "raw_max": raw_max,
        "raw_mean": float(np.mean(valid_raw)),
        "raw_std": float(np.std(valid_raw)),
    }
    return raw, normalized, stats


def class_distribution(class_array: np.ndarray, valid_mask: np.ndarray, scenario: dict[str, Any]) -> list[dict[str, Any]]:
    valid_pixels = int(valid_mask.sum())
    rows = []
    for class_value, label in CLASS_LABELS.items():
        pixel_count = int((class_array == class_value).sum())
        area = pixel_count * PIXEL_AREA_KM2
        rows.append(
            {
                "scenario_id": scenario["scenario_id"],
                "scenario_label": scenario["scenario_label"],
                "scenario_role": scenario["scenario_role"],
                "class_value": class_value,
                "class_label": label,
                "pixel_count": pixel_count,
                "area_km2": area,
                "share_of_aoi_percent": area / (valid_pixels * PIXEL_AREA_KM2) * 100.0,
            }
        )
    return rows


def summarize_scenario(
    scenario: dict[str, Any],
    class_array: np.ndarray,
    baseline_class: np.ndarray,
    valid_mask: np.ndarray,
    stats: dict[str, float],
    baseline_high_pixels: int,
) -> dict[str, Any]:
    high_mask = (class_array >= 4) & valid_mask
    baseline_high_mask = (baseline_class >= 4) & valid_mask
    high_pixels = int(high_mask.sum())
    high_area = high_pixels * PIXEL_AREA_KM2
    valid_pixels = int(valid_mask.sum())
    intersection = int((high_mask & baseline_high_mask).sum())
    union = int((high_mask | baseline_high_mask).sum())
    agreement = int((class_array[valid_mask] == baseline_class[valid_mask]).sum())
    baseline_high_area = baseline_high_pixels * PIXEL_AREA_KM2

    return {
        "scenario_id": scenario["scenario_id"],
        "scenario_label": scenario["scenario_label"],
        "scenario_role": scenario["scenario_role"],
        **stats,
        "high_plus_pixel_count": high_pixels,
        "high_plus_area_km2": high_area,
        "high_plus_share_percent": high_pixels / valid_pixels * 100.0,
        "delta_high_plus_area_km2_vs_baseline": high_area - baseline_high_area,
        "delta_high_plus_share_point_vs_baseline": (high_pixels - baseline_high_pixels) / valid_pixels * 100.0,
        "class_agreement_with_baseline_percent": agreement / valid_pixels * 100.0,
        "baseline_high_plus_retention_percent": (
            intersection / baseline_high_pixels * 100.0 if baseline_high_pixels else 0.0
        ),
        "scenario_high_plus_overlap_baseline_percent": intersection / high_pixels * 100.0 if high_pixels else 0.0,
        "high_plus_jaccard_percent": intersection / union * 100.0 if union else 0.0,
    }


def top_district_rows(
    scenario: dict[str, Any],
    class_array: np.ndarray,
    district_array: np.ndarray,
    districts: list[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    high_mask = class_array >= 4
    ranked = []
    for district in districts:
        district_mask = district_array == district["district_id"]
        pixel_count = int((district_mask & high_mask).sum())
        area = pixel_count * PIXEL_AREA_KM2
        ranked.append(
            {
                "scenario_id": scenario["scenario_id"],
                "scenario_label": scenario["scenario_label"],
                "district_id": district["district_id"],
                "district_name": district["district_name"],
                "high_plus_pixel_count": pixel_count,
                "high_plus_area_km2": area,
                "district_share_percent": area / district["district_area_km2"] * 100.0,
            }
        )

    ranked.sort(key=lambda row: (-row["high_plus_area_km2"], row["district_name"]))
    rows = []
    for rank, row in enumerate(ranked[:limit], start=1):
        rows.append({"rank": rank, **row})
    return rows


def transition_rows(
    scenario: dict[str, Any],
    class_array: np.ndarray,
    baseline_class: np.ndarray,
    valid_mask: np.ndarray,
) -> list[dict[str, Any]]:
    valid_pixels = int(valid_mask.sum())
    rows = []
    for baseline_value, baseline_label in CLASS_LABELS.items():
        baseline_mask = valid_mask & (baseline_class == baseline_value)
        baseline_total = int(baseline_mask.sum())
        for scenario_value, scenario_label in CLASS_LABELS.items():
            pixel_count = int((baseline_mask & (class_array == scenario_value)).sum())
            rows.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "scenario_label": scenario["scenario_label"],
                    "baseline_class_value": baseline_value,
                    "baseline_class_label": baseline_label,
                    "scenario_class_value": scenario_value,
                    "scenario_class_label": scenario_label,
                    "pixel_count": pixel_count,
                    "area_km2": pixel_count * PIXEL_AREA_KM2,
                    "share_of_aoi_percent": pixel_count / valid_pixels * 100.0,
                    "share_of_baseline_class_percent": (
                        pixel_count / baseline_total * 100.0 if baseline_total else 0.0
                    ),
                }
            )
    return rows


def first_top_names(top_rows: list[dict[str, Any]], scenario_id: str, limit: int = 5) -> list[str]:
    rows = [row for row in top_rows if row["scenario_id"] == scenario_id]
    rows.sort(key=lambda row: int(row["rank"]))
    return [str(row["district_name"]) for row in rows[:limit]]


def interpretation_rows(
    summary_rows: list[dict[str, Any]],
    top_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_scenario = {row["scenario_id"]: row for row in summary_rows}
    baseline_top = first_top_names(top_rows, "baseline")
    rows = []

    baseline = by_scenario["baseline"]
    rows.append(
        {
            "scenario_id": "baseline",
            "scenario_label": baseline["scenario_label"],
            "interpretation_level": "Referans",
            "key_finding_tr": (
                f"Canonical baseline modelde yüksek+çok yüksek öncelik alanı "
                f"{baseline['high_plus_area_km2']:.2f} km2'dir."
            ),
            "stability_comment_tr": (
                "Bu senaryo nihai MCDA class rasterını temsil eder ve diğer senaryolar için "
                "karşılaştırma referansıdır."
            ),
            "top_district_comment_tr": "İlk beş ilçe: " + ", ".join(baseline_top) + ".",
            "report_sentence_tr": (
                "Baseline modelde yüksek ve çok yüksek öncelik sınıfları toplam "
                f"{baseline['high_plus_area_km2']:.2f} km2 alan kaplamaktadır."
            ),
        }
    )

    earthquake = by_scenario["earthquake-heavy"]
    earthquake_top = first_top_names(top_rows, "earthquake-heavy")
    same_top_order = earthquake_top == baseline_top
    rows.append(
        {
            "scenario_id": "earthquake-heavy",
            "scenario_label": earthquake["scenario_label"],
            "interpretation_level": "Orta düzey değişim",
            "key_finding_tr": (
                "Deprem ağırlıklı senaryoda yüksek+çok yüksek alan baseline'a göre "
                f"{earthquake['delta_high_plus_area_km2_vs_baseline']:.2f} km2 artmıştır."
            ),
            "stability_comment_tr": (
                f"Class agreement {earthquake['class_agreement_with_baseline_percent']:.2f}% ve "
                f"baseline yüksek+çok yüksek alan retention {earthquake['baseline_high_plus_retention_percent']:.2f}% "
                "olduğu için ana yüksek öncelik çekirdeği büyük ölçüde korunur; artış daha çok "
                "mevcut desenin genişlemesi olarak okunmalıdır."
            ),
            "top_district_comment_tr": (
                "İlk beş ilçe sıralaması baseline ile aynıdır: "
                + ", ".join(earthquake_top)
                + "."
                if same_top_order
                else "İlk beş ilçe kısmen değişmiştir: " + ", ".join(earthquake_top) + "."
            ),
            "report_sentence_tr": (
                "Deprem ağırlıklı robustness senaryosu, yüksek öncelik alanlarını genişletirken "
                "baseline yüksek öncelik çekirdeğinin büyük bölümünü korumaktadır."
            ),
        }
    )

    equal = by_scenario["equal-weight"]
    equal_top = first_top_names(top_rows, "equal-weight")
    entered = [name for name in equal_top if name not in baseline_top]
    left = [name for name in baseline_top if name not in equal_top]
    shift_note = "İlk beş ilçe listesi değişmemiştir."
    if entered or left:
        shift_note = (
            "İlk beş ilçe listesinde "
            + (", ".join(entered) + " senaryoya girmiştir" if entered else "yeni ilçe girişi yoktur")
            + "; "
            + (", ".join(left) + " listeden çıkmıştır" if left else "listeden çıkan ilçe yoktur")
            + "."
        )
    rows.append(
        {
            "scenario_id": "equal-weight",
            "scenario_label": equal["scenario_label"],
            "interpretation_level": "Belirgin değişim",
            "key_finding_tr": (
                "Eşit ağırlıklı senaryoda yüksek+çok yüksek alan baseline'a göre "
                f"{equal['delta_high_plus_area_km2_vs_baseline']:.2f} km2 artmıştır."
            ),
            "stability_comment_tr": (
                f"Class agreement {equal['class_agreement_with_baseline_percent']:.2f}% ve "
                f"baseline yüksek+çok yüksek alan retention {equal['baseline_high_plus_retention_percent']:.2f}% "
                "olduğu için sonuçlar baseline desenini tamamen kaybetmez; ancak ağırlık varsayımına "
                "belirgin duyarlılık gösterir."
            ),
            "top_district_comment_tr": shift_note + " Eşit ağırlık ilk beşi: " + ", ".join(equal_top) + ".",
            "report_sentence_tr": (
                "Eşit ağırlıklı senaryo, baseline'a göre daha geniş yüksek öncelik alanı üretmekte "
                "ve sonuçların ağırlık varsayımına duyarlı olduğunu göstermektedir."
            ),
        }
    )

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
    summary_rows: list[dict[str, Any]],
    interpretation_rows_out: list[dict[str, Any]],
    distribution_rows: list[dict[str, Any]],
    top_rows: list[dict[str, Any]],
    transition_rows_out: list[dict[str, Any]],
) -> None:
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    output_label = str(output_dir) if not output_dir.is_absolute() else output_dir.name
    files = [
        "mcda_sensitivity_scenario_summary.csv",
        "mcda_sensitivity_scenario_summary.md",
        "mcda_sensitivity_interpretation.csv",
        "mcda_sensitivity_interpretation.md",
        "mcda_sensitivity_class_distribution.csv",
        "mcda_sensitivity_class_distribution.md",
        "mcda_sensitivity_top_districts.csv",
        "mcda_sensitivity_top_districts.md",
        "mcda_sensitivity_class_transition.csv",
        "mcda_sensitivity_class_transition.md",
        "mcda_sensitivity_manifest.md",
    ]

    with path.open("w", encoding="utf-8") as stream:
        stream.write("# MCDA Sensitivity / Robustness Manifesti\n\n")
        stream.write(f"Üretim zamanı (UTC): `{generated}`\n\n")
        stream.write("Girdi seviyesi: canonical `data/processed` skor rasterları ve `config/mcda_weights.tsv`.\n\n")
        stream.write("Kalıcı senaryo rasterı üretilmez; senaryo skorları geçici array hesaplarıdır.\n\n")
        stream.write("## Dosyalar\n\n")
        for file_name in files:
            stream.write(f"- `{output_label}/{file_name}`\n")
        stream.write("\n## QA Özeti\n\n")
        stream.write(f"- Senaryo sayısı: `{len(summary_rows)}`\n")
        stream.write(f"- Yorum satırları: `{len(interpretation_rows_out)}`\n")
        stream.write(f"- Class dağılım satırları: `{len(distribution_rows)}`\n")
        stream.write(f"- Top district satırları: `{len(top_rows)}`\n")
        stream.write(f"- Class transition satırları: `{len(transition_rows_out)}`\n")
        stream.write("\n## Kısa Okuma\n\n")
        for row in summary_rows:
            if row["scenario_id"] == "baseline":
                stream.write("- `baseline`: canonical MCDA sınıf rasterı referans senaryodur.\n")
                continue
            delta = float(row["delta_high_plus_share_point_vs_baseline"])
            agreement = float(row["class_agreement_with_baseline_percent"])
            stream.write(
                f"- `{row['scenario_id']}`: yüksek+çok yüksek alan payı baseline'a göre "
                f"{delta:+.2f} yüzde puan değişti; class agreement `{agreement:.2f}%`.\n"
            )


def generate(project_root: Path, output_dir: Path) -> None:
    project_root = project_root.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    scenarios = load_weight_scenarios(project_root)
    require_inputs(project_root, scenarios)

    class_info = gdalinfo_json(project_root / BASELINE_CLASS_RASTER)
    reference_grid = raster_grid(class_info)
    shape = (reference_grid["height"], reference_grid["width"])

    with tempfile.TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)
        baseline_class_bin = temp_dir / "baseline_mcda_class.bin"
        translate_to_envi(project_root / BASELINE_CLASS_RASTER, baseline_class_bin, "Byte")
        baseline_class = read_array(baseline_class_bin, np.dtype("uint8"), shape)
        valid_mask = (baseline_class >= 1) & (baseline_class <= 5)
        valid_pixels = int(valid_mask.sum())
        if valid_pixels == 0:
            raise SensitivityError("Baseline MCDA class rasterında geçerli piksel yok.")

        district_layer = create_district_id_layer(project_root, temp_dir)
        district_tif = temp_dir / "district_ids.tif"
        district_bin = temp_dir / "district_ids.bin"
        rasterize_district_ids(district_layer, district_tif, reference_grid)
        translate_to_envi(district_tif, district_bin, "Int16")
        district_array = read_array(district_bin, np.dtype("int16"), shape)
        missing_district_pixels = int(((district_array == 0) & valid_mask).sum())
        if missing_district_pixels:
            raise SensitivityError(f"District id değeri olmayan baseline class pikselleri: {missing_district_pixels}")

        districts = load_districts(project_root)
        criterion_arrays: dict[str, np.ndarray] = {}
        for criterion_id in EXPECTED_CRITERIA:
            raster_path = scenarios["baseline"]["criteria"][EXPECTED_CRITERIA.index(criterion_id)]["raster_path"]
            info = gdalinfo_json(project_root / raster_path)
            validate_common_grid(reference_grid, info, raster_path)
            bin_path = temp_dir / f"{criterion_id}.bin"
            translate_to_envi(project_root / raster_path, bin_path, "Float32")
            array = read_array(bin_path, np.dtype("float32"), shape)
            if np.any(array[valid_mask] <= -9990):
                raise SensitivityError(f"{criterion_id} içinde baseline valid mask altında NoData değerleri var.")
            criterion_arrays[criterion_id] = array

        baseline_high_pixels = int(((baseline_class >= 4) & valid_mask).sum())
        summary_rows: list[dict[str, Any]] = []
        distribution_rows: list[dict[str, Any]] = []
        top_rows: list[dict[str, Any]] = []
        transition_rows_out: list[dict[str, Any]] = []

        for scenario_id in SCENARIO_ORDER:
            scenario = scenarios[scenario_id]
            _, normalized, stats = weighted_score(scenario, criterion_arrays, valid_mask)
            if scenario_id == "baseline":
                scenario_class = baseline_class.copy()
            else:
                scenario_class = classify_normalized(normalized, valid_mask)

            distribution_rows.extend(class_distribution(scenario_class, valid_mask, scenario))
            summary_rows.append(
                summarize_scenario(
                    scenario,
                    scenario_class,
                    baseline_class,
                    valid_mask,
                    stats,
                    baseline_high_pixels,
                )
            )
            top_rows.extend(top_district_rows(scenario, scenario_class, district_array, districts))
            transition_rows_out.extend(transition_rows(scenario, scenario_class, baseline_class, valid_mask))

    if len(summary_rows) != 3:
        raise SensitivityError(f"Beklenen 3 scenario summary satırı, gelen {len(summary_rows)}")
    if len(distribution_rows) != 15:
        raise SensitivityError(f"Beklenen 15 class distribution satırı, gelen {len(distribution_rows)}")
    if len(top_rows) != 15:
        raise SensitivityError(f"Beklenen 15 top district satırı, gelen {len(top_rows)}")
    if len(transition_rows_out) != 75:
        raise SensitivityError(f"Beklenen 75 class transition satırı, gelen {len(transition_rows_out)}")
    interpretation_rows_out = interpretation_rows(summary_rows, top_rows)
    if len(interpretation_rows_out) != 3:
        raise SensitivityError(f"Beklenen 3 interpretation satırı, gelen {len(interpretation_rows_out)}")

    summary_columns = [
        "scenario_id",
        "scenario_label",
        "scenario_role",
        "raw_min",
        "raw_max",
        "raw_mean",
        "raw_std",
        "high_plus_pixel_count",
        "high_plus_area_km2",
        "high_plus_share_percent",
        "delta_high_plus_area_km2_vs_baseline",
        "delta_high_plus_share_point_vs_baseline",
        "class_agreement_with_baseline_percent",
        "baseline_high_plus_retention_percent",
        "scenario_high_plus_overlap_baseline_percent",
        "high_plus_jaccard_percent",
    ]
    interpretation_columns = [
        "scenario_id",
        "scenario_label",
        "interpretation_level",
        "key_finding_tr",
        "stability_comment_tr",
        "top_district_comment_tr",
        "report_sentence_tr",
    ]
    distribution_columns = [
        "scenario_id",
        "scenario_label",
        "scenario_role",
        "class_value",
        "class_label",
        "pixel_count",
        "area_km2",
        "share_of_aoi_percent",
    ]
    top_columns = [
        "scenario_id",
        "scenario_label",
        "rank",
        "district_id",
        "district_name",
        "high_plus_pixel_count",
        "high_plus_area_km2",
        "district_share_percent",
    ]
    transition_columns = [
        "scenario_id",
        "scenario_label",
        "baseline_class_value",
        "baseline_class_label",
        "scenario_class_value",
        "scenario_class_label",
        "pixel_count",
        "area_km2",
        "share_of_aoi_percent",
        "share_of_baseline_class_percent",
    ]

    write_csv(output_dir / "mcda_sensitivity_scenario_summary.csv", summary_rows, summary_columns)
    write_markdown_table(
        output_dir / "mcda_sensitivity_scenario_summary.md",
        "MCDA Sensitivity Senaryo Özeti",
        summary_rows,
        summary_columns,
        "Baseline canonical class rasterıdır; alternatif senaryolar kalıcı raster üretmeden hesaplanır.",
    )
    write_csv(output_dir / "mcda_sensitivity_interpretation.csv", interpretation_rows_out, interpretation_columns)
    write_markdown_table(
        output_dir / "mcda_sensitivity_interpretation.md",
        "MCDA Sensitivity Kısa Yorumları",
        interpretation_rows_out,
        interpretation_columns,
        "Bu yorumlar sensitivity tablolarından otomatik üretilir ve rapor metnine kısa yorum olarak alınabilir.",
    )
    write_csv(output_dir / "mcda_sensitivity_class_distribution.csv", distribution_rows, distribution_columns)
    write_markdown_table(
        output_dir / "mcda_sensitivity_class_distribution.md",
        "MCDA Sensitivity Sınıf Dağılımı",
        distribution_rows,
        distribution_columns,
        "Alan değerleri canonical 100 m grid hücre alanı olan 0.01 km2 üzerinden hesaplanır.",
    )
    write_csv(output_dir / "mcda_sensitivity_top_districts.csv", top_rows, top_columns)
    write_markdown_table(
        output_dir / "mcda_sensitivity_top_districts.md",
        "MCDA Sensitivity İlk Beş İlçe",
        top_rows,
        top_columns,
        "Sıralama her senaryoda yüksek + çok yüksek sınıf alanına göre yapılır.",
    )
    write_csv(output_dir / "mcda_sensitivity_class_transition.csv", transition_rows_out, transition_columns)
    write_markdown_table(
        output_dir / "mcda_sensitivity_class_transition.md",
        "MCDA Sensitivity Class Transition",
        transition_rows_out,
        transition_columns,
        "Satırlar baseline class değerlerinden senaryo class değerlerine geçiş matrisini gösterir.",
    )
    write_manifest(
        output_dir / "mcda_sensitivity_manifest.md",
        output_dir,
        summary_rows,
        interpretation_rows_out,
        distribution_rows,
        top_rows,
        transition_rows_out,
    )

    print("MCDA sensitivity tabloları üretildi:")
    print(f"- çıktı_dizini: {output_dir}")
    print(f"- senaryo_sayısı: {len(summary_rows)}")
    print(f"- yorum_satırları: {len(interpretation_rows_out)}")
    print(f"- class_dağılım_satırları: {len(distribution_rows)}")
    print(f"- top_district_satırları: {len(top_rows)}")
    print(f"- transition_satırları: {len(transition_rows_out)}")


def main() -> int:
    args = parse_args()
    try:
        generate(args.project_root, args.output_dir)
    except SensitivityError as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
