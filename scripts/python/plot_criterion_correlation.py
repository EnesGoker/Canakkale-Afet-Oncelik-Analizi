#!/usr/bin/env python3
"""Export a Turkish Pearson figure, or verify its saved source/file hashes.

--check never imports Matplotlib or writes files. --generate requires an
explicit empty/new output directory and never replaces existing content.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True

from generate_correlation_analysis import MATRIX_FILE, STATISTICS_FILE, MANIFEST_FILE, validate_correlation

ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = Path("outputs/tables/criterion_correlation_v1")
FIGURE_DIR = Path("outputs/figures/criterion_correlation_v1")
PNG_FILE = "criterion_pearson_correlation.png"
PDF_FILE = "criterion_pearson_correlation.pdf"
FIGURE_MANIFEST = "criterion_correlation_figure_manifest.json"
SHORT_LABELS = {
    "earthquake_pga_score": "Deprem\nPGA",
    "fault_proximity_score": "Fay\nyakınlığı",
    "site_condition_score": "Zemin\n(VS30)",
    "population_exposure_score": "Nüfus\nmaruziyeti",
    "building_exposure_density_score": "Yapı\nyoğunluğu",
    "flood_score": "Taşkın",
    "hydrography_proximity_score": "Hidrografya\nyakınlığı",
    "slope_score": "Eğim",
    "landcover_sensitivity_score": "Arazi örtüsü\nduyarlılığı",
    "tree_cover_score": "Ağaç\nörtüsü",
    "road_accessibility_difficulty_score": "Yol erişim\nzorluğu",
}


def file_record(path):
    content = path.read_bytes()
    return {"path": path.name, "size": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def read_sources(directory):
    """Validate source identity, complete CSV shape, counts and matrix values."""
    import numpy as np
    directory = Path(directory)
    manifest = json.loads((directory / MANIFEST_FILE).read_text(encoding="utf-8"))
    ids = manifest["criterion_ids"]
    if not isinstance(ids, list) or len(ids) < 2 or len(set(ids)) != len(ids):
        raise ValueError("Invalid criterion order in source manifest")
    records = manifest["outputs"]
    if len(records) != 2 or {row["path"] for row in records} != {MATRIX_FILE, STATISTICS_FILE}:
        raise ValueError("Source manifest must identify the two analysis CSVs")
    for record in records:
        if file_record(directory / record["path"]) != record:
            raise ValueError(f"Source checksum/size mismatch: {record['path']}")
    with (directory / MATRIX_FILE).open(encoding="utf-8", newline="") as stream:
        rows = list(csv.reader(stream))
    if rows[0] != ["criterion_id", *ids] or len(rows) != len(ids) + 1:
        raise ValueError("Matrix CSV columns or row count differ from the source manifest")
    if any(len(row) != len(ids) + 1 for row in rows[1:]) or [row[0] for row in rows[1:]] != ids:
        raise ValueError("Matrix CSV criterion order or row width is invalid")
    matrix = np.array([[float(value) for value in row[1:]] for row in rows[1:]], dtype=np.float64)
    validate_correlation(matrix, len(ids))
    with (directory / STATISTICS_FILE).open(encoding="utf-8", newline="") as stream:
        statistics = list(csv.DictReader(stream))
    if [row["criterion_id"] for row in statistics] != ids:
        raise ValueError("Statistics criterion order differs from the matrix")
    n_cells = manifest["aoi_cells"]
    if not isinstance(n_cells, int) or n_cells < 2:
        raise ValueError("Invalid source AOI cell count")
    if any(int(row["aoi_cell_count"]) != n_cells or int(row["finite_count"]) != n_cells for row in statistics):
        raise ValueError("Statistics AOI counts differ from the source manifest")
    if any(int(row["nonfinite_count"]) != 0 or int(row["nodata_count"]) != 0 for row in statistics):
        raise ValueError("Statistics contain invalid AOI cells")
    names = manifest["display_names_tr"]
    if set(names) != set(ids) or [names[item] for item in ids] != [row["display_name_tr"] for row in statistics]:
        raise ValueError("Source display names differ between statistics and manifest")
    return {"criterion_ids": ids, "matrix": matrix, "manifest": manifest,
            "sources": [file_record(directory / name) for name in (MATRIX_FILE, STATISTICS_FILE, MANIFEST_FILE)]}


def check_saved_figure(sources, output_dir):
    output_dir = Path(output_dir)
    manifest = json.loads((output_dir / FIGURE_MANIFEST).read_text(encoding="utf-8"))
    if manifest.get("format_version") != 1 or manifest.get("sources") != sources["sources"]:
        raise ValueError("Figure manifest refers to different source artifacts")
    if manifest.get("baseline_id") != sources["manifest"]["baseline"]["baseline_id"]:
        raise ValueError("Figure baseline identity differs from the source analysis")
    if manifest.get("criterion_ids") != sources["criterion_ids"] or manifest.get("aoi_cells") != sources["manifest"]["aoi_cells"]:
        raise ValueError("Figure criterion order or AOI count differs from its source")
    if manifest.get("color_limits") != [-1, 1] or manifest.get("annotation_decimals") != 2:
        raise ValueError("Figure rendering contract differs from the saved version")
    records = manifest.get("outputs", [])
    if len(records) != 2 or {row["path"] for row in records} != {PNG_FILE, PDF_FILE}:
        raise ValueError("Figure manifest must identify both PNG and PDF")
    for record in records:
        if file_record(output_dir / record["path"]) != record:
            raise ValueError(f"Figure checksum/size mismatch: {record['path']}")
    return {"passed": True, "checked_files": 3, "message": "PNG/PDF and source hashes match the saved figure manifest."}


def generate_figure(sources, output_dir):
    output_dir = Path(output_dir).absolute()
    if output_dir.is_symlink() or (output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir()))):
        raise ValueError("Figure output directory must be empty or new; existing content is never overwritten")
    if not output_dir.parent.is_dir():
        raise ValueError("Figure output directory parent must already exist")
    published, created_directory = [], False
    with tempfile.TemporaryDirectory(prefix="criterion-figure-") as scratch:
        # Keep the font cache outside the project. Checking saved figures never
        # imports this optional plotting dependency.
        prior_config = os.environ.get("MPLCONFIGDIR")
        os.environ["MPLCONFIGDIR"] = scratch
        try:
            import matplotlib
            matplotlib.use("Agg")
            from matplotlib import pyplot as plt
            from matplotlib.colors import Normalize
            ids, matrix = sources["criterion_ids"], sources["matrix"]
            labels = [SHORT_LABELS.get(item, sources["manifest"]["display_names_tr"][item]) for item in ids]
            with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 11, "pdf.fonttype": 42}):
                figure = plt.figure(figsize=(15.0, 13.0), facecolor="white")
                axis = figure.add_axes((0.16, 0.16, 0.72, 0.72))
                cmap, norm = plt.get_cmap("RdBu_r"), Normalize(-1, 1)
                shown = axis.imshow(matrix, cmap=cmap, norm=norm, interpolation="nearest")
                axis.set_xticks(range(len(ids)), labels=labels, fontsize=10)
                axis.set_yticks(range(len(ids)), labels=labels, fontsize=11)
                axis.tick_params(axis="both", which="both", length=0, pad=10)
                axis.set_xticks([item - 0.5 for item in range(len(ids) + 1)], minor=True)
                axis.set_yticks([item - 0.5 for item in range(len(ids) + 1)], minor=True)
                axis.grid(which="minor", color="white", linewidth=0.8)
                for spine in axis.spines.values():
                    spine.set_visible(False)
                for row in range(len(ids)):
                    for column in range(len(ids)):
                        value = float(matrix[row, column])
                        red, green, blue, _ = cmap(norm(value))
                        luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
                        label = "0.00" if abs(value) < 0.005 else f"{value:.2f}"
                        axis.text(column, row, label, ha="center", va="center", fontsize=11,
                                  color="white" if luminance < 0.55 else "#17222c")
                color_axis = figure.add_axes((0.90, 0.25, 0.018, 0.52))
                colorbar = figure.colorbar(shown, cax=color_axis, ticks=[-1, -0.5, 0, 0.5, 1])
                colorbar.set_label("Pearson r", labelpad=12)
                figure.text(0.51, 0.96, "Çanakkale · Kriterler arası korelasyon", ha="center", fontsize=23, weight="bold", color="#17222c")
                count = f"{sources['manifest']['aoi_cells']:,}".replace(",", ".")
                figure.text(0.51, 0.925, f"Pearson r · {len(ids)} kriter · {count} AOI hücresi · 100 m", ha="center", fontsize=13, color="#465665")
                figure.text(0.51, 0.060, "Tüm AOI hücreleri · Ağırlıklandırılmamış 0–1 skorlar · Mekânsal bağımlılık içerir", ha="center", fontsize=11, color="#465665")
                figure.text(0.51, 0.037, "Skor sıfırları korunur; kaynak NoData → 0 davranışı yorum belgesinde açıklanır.", ha="center", fontsize=10, color="#465665")
                try:
                    with tempfile.TemporaryDirectory(prefix=".figure-stage-", dir=output_dir.parent) as staging:
                        stage = Path(staging)
                        figure.savefig(stage / PNG_FILE, dpi=200, facecolor="white")
                        figure.savefig(stage / PDF_FILE, facecolor="white", metadata={"Title": "Çanakkale kriterler arası Pearson korelasyonu", "Author": "Enes Göker", "CreationDate": None, "ModDate": None})
                        manifest = {"format_version": 1, "baseline_id": sources["manifest"]["baseline"]["baseline_id"],
                                    "criterion_ids": ids, "aoi_cells": sources["manifest"]["aoi_cells"],
                                    "sources": sources["sources"], "color_limits": [-1, 1], "annotation_decimals": 2,
                                    "matplotlib": matplotlib.__version__, "outputs": [file_record(stage / name) for name in (PNG_FILE, PDF_FILE)]}
                        (stage / FIGURE_MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
                        try:
                            output_dir.mkdir()
                            created_directory = True
                        except FileExistsError:
                            if output_dir.is_symlink() or not output_dir.is_dir() or any(output_dir.iterdir()):
                                raise ValueError("Figure target became nonempty during generation")
                        for name in (PNG_FILE, PDF_FILE, FIGURE_MANIFEST):
                            os.link(stage / name, output_dir / name)
                            target = output_dir / name
                            published.append((target, target.stat().st_ino))
                finally:
                    plt.close(figure)
        except BaseException:
            for path, inode in reversed(published):
                try:
                    if path.lstat().st_ino == inode:
                        path.unlink()
                except FileNotFoundError:
                    pass
            if created_directory:
                try:
                    output_dir.rmdir()
                except OSError:
                    pass
            raise
        finally:
            if prior_config is None:
                os.environ.pop("MPLCONFIGDIR", None)
            else:
                os.environ["MPLCONFIGDIR"] = prior_config
    return [PNG_FILE, PDF_FILE, FIGURE_MANIFEST]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--generate", action="store_true")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.generate and args.output_dir is None:
        parser.error("--generate requires an explicit --output-dir")
    try:
        sources = read_sources(args.source_dir or args.project_root / TABLE_DIR)
        target = args.output_dir or args.project_root / FIGURE_DIR
        if args.generate:
            result = {"passed": True, "outputs": generate_figure(sources, target)}
        else:
            result = check_saved_figure(sources, target)
        code = 0
    except (ImportError, ModuleNotFoundError) as error:
        result, code = {"passed": False, "message": f"Required module unavailable: {error.name}"}, 2
    except (OSError, ValueError, KeyError, TypeError, IndexError, csv.Error) as error:
        result, code = {"passed": False, "message": str(error)}, 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    else:
        print(("GEÇTİ: " if code == 0 else "ATLANDI: " if code == 2 else "HATA: ") + result.get("message", ", ".join(result.get("outputs", []))))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
