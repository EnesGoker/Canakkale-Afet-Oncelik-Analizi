#!/usr/bin/env python3
"""Describe Pearson correlations of the frozen, unweighted criterion scores.

The default --check is read-only. --generate requires an explicit empty or new
output directory and refuses to overwrite any existing content. NumPy/GDAL are
loaded after argument parsing, so --help works without the GIS dependencies.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
BASELINE_MANIFEST = Path("config/analysis_baseline_v1.json")
MATRIX_FILE = "criterion_pearson_correlation.csv"
STATISTICS_FILE = "criterion_correlation_statistics.csv"
MANIFEST_FILE = "criterion_correlation_manifest.json"
OUTPUT_FILES = (MATRIX_FILE, STATISTICS_FILE, MANIFEST_FILE)
MATRIX_TOLERANCE = 1e-12
NEAR_CONSTANT_EPS_MULTIPLIER = 64
STATISTIC_COLUMNS = (
    "criterion_id", "display_name_tr", "aoi_cell_count", "finite_count",
    "nonfinite_count", "nodata_count", "zero_count", "zero_fraction",
    "minimum", "maximum", "mean", "std_population",
)


def validate_correlation(matrix, n_criteria: int) -> None:
    """Reject an invalid result; never repair its diagonal, symmetry or bounds."""
    import numpy as np
    matrix = np.asarray(matrix)
    if matrix.shape != (n_criteria, n_criteria):
        raise ValueError("Correlation matrix has the wrong shape")
    if not np.isfinite(matrix).all():
        raise ValueError("Correlation matrix contains a nonfinite value")
    if not np.allclose(matrix, matrix.T, rtol=0, atol=MATRIX_TOLERANCE):
        raise ValueError("Correlation matrix is not symmetric")
    if not np.allclose(np.diag(matrix), 1.0, rtol=0, atol=MATRIX_TOLERANCE):
        raise ValueError("Correlation matrix diagonal differs from one")
    if np.any(np.abs(matrix) > 1.0 + MATRIX_TOLERANCE):
        raise ValueError("Correlation matrix contains a value outside [-1, 1]")


def compute_correlation(vectors, criterion_ids, display_names=None) -> dict:
    """Compute descriptive correlations using the same full AOI for every pair.

    vectors must contain one finite, equally sized, one-dimensional vector per
    criterion. The frozen loader already verifies the score rasters' NoData,
    alignment and template mask. Zeros are retained as valid stored scores.
    """
    import numpy as np
    ids = list(criterion_ids)
    if len(ids) < 2 or len(set(ids)) != len(ids) or not all(isinstance(item, str) and item for item in ids):
        raise ValueError("At least two unique, nonempty criterion IDs are required")
    if set(vectors) != set(ids):
        raise ValueError("Criterion vectors must exactly match the ordered criterion IDs")
    names = dict(display_names or {})
    if names and set(names) != set(ids):
        raise ValueError("Display names must exactly match the criterion IDs")
    arrays = []
    n_cells = None
    for criterion_id in ids:
        original = np.asarray(vectors[criterion_id])
        if original.ndim != 1 or original.dtype.kind not in "iuf":
            raise ValueError(f"{criterion_id}: a one-dimensional real numeric vector is required")
        array = np.asarray(original, dtype=np.float64)
        if n_cells is None:
            n_cells = len(array)
        if len(array) != n_cells or len(array) < 2:
            raise ValueError(f"{criterion_id}: at least two equally aligned AOI values are required")
        if not np.isfinite(array).all():
            raise ValueError(f"{criterion_id}: NaN or infinity is not permitted; no pairwise deletion is performed")
        arrays.append(array)

    values = np.stack(arrays)
    magnitudes = np.maximum(np.max(np.abs(values), axis=1), np.finfo(np.float64).tiny)
    # Ordinary scores retain their original values. Extreme-only positive
    # rescaling prevents overflow/underflow in the reusable numerical core.
    scales = np.where((magnitudes < 1e-100) | (magnitudes > 1e100), magnitudes, 1.0)
    scaled = values / scales[:, None]
    scaled_means = scaled.mean(axis=1, dtype=np.float64)
    means = scaled_means * scales
    centered = scaled - scaled_means[:, None]
    cross_products = centered @ centered.T
    # Use the same accumulated moments in numerator and denominator. Mixing a
    # separate einsum reduction with a BLAS product drifts for million-cell
    # sparse vectors even when each reduction is reasonable on its own.
    sum_squares = np.diag(cross_products).copy()
    scaled_standard_deviations = np.sqrt(sum_squares / n_cells)
    standard_deviations = scaled_standard_deviations * scales
    thresholds = NEAR_CONSTANT_EPS_MULTIPLIER * np.finfo(np.float64).eps * (magnitudes / scales)
    unstable = ~np.isfinite(standard_deviations) | (scaled_standard_deviations <= thresholds)
    if np.any(unstable):
        bad = ", ".join(ids[index] for index in np.flatnonzero(unstable))
        raise ValueError(f"Constant or numerically near-constant criterion vector: {bad}")

    # Center first instead of subtracting two large raw second moments.
    # Keep the ordinary-score arithmetic deterministic; guard the squared
    # moment product for intermediate magnitudes that require no input scaling.
    limits = np.finfo(np.float64)
    if np.max(sum_squares) > np.sqrt(limits.max) or np.min(sum_squares) < np.sqrt(limits.tiny):
        norms = np.sqrt(sum_squares)
        denominator = np.outer(norms, norms)
    else:
        denominator = np.sqrt(np.outer(sum_squares, sum_squares))
    correlation = cross_products / denominator
    validate_correlation(correlation, len(ids))
    statistics = []
    for index, criterion_id in enumerate(ids):
        zero_count = int(np.count_nonzero(values[index] == 0))
        statistics.append({
            "criterion_id": criterion_id,
            "display_name_tr": names.get(criterion_id, criterion_id),
            "aoi_cell_count": n_cells,
            "finite_count": n_cells,
            "nonfinite_count": 0,
            "nodata_count": 0,
            "zero_count": zero_count,
            "zero_fraction": zero_count / n_cells,
            "minimum": float(values[index].min()),
            "maximum": float(values[index].max()),
            "mean": float(means[index]),
            "std_population": float(standard_deviations[index]),
        })
    return {
        "criterion_ids": ids,
        "display_names": {item: names.get(item, item) for item in ids},
        "n_cells": n_cells,
        "correlation": correlation,
        "statistics": statistics,
        "numeric_policy": {
            "dtype": "float64",
            "algorithm": "centered cross-products divided by their own diagonal norms; positive max-absolute rescaling only for extreme magnitudes outside [1e-100, 1e100]",
            "standard_deviation_ddof": 0,
            "near_constant_rule": "std_population <= 64 * float64_epsilon * max(abs(values))",
            "matrix_validation_absolute_tolerance": MATRIX_TOLERANCE,
            "matrix_values_repaired_or_clipped": False,
        },
    }


def analyze_project(root=ROOT) -> dict:
    """Verify the complete frozen baseline before exposing any AOI criterion."""
    os.environ["GDAL_PAM_ENABLED"] = "NO"
    from analysis_baseline import load_frozen_inputs
    root = Path(root).resolve()
    loaded = load_frozen_inputs(root)
    manifest_bytes = (root / BASELINE_MANIFEST).read_bytes()
    baseline = json.loads(manifest_bytes)
    ids = [row["criterion_id"] for row in baseline["scenarios"]["baseline"]]
    with (root / "config/mcda_weights.tsv").open(encoding="utf-8", newline="") as stream:
        names = {row["criterion_id"]: row["display_name_tr"] for row in csv.DictReader(stream, delimiter="\t") if row["scenario_id"] == "baseline"}
    analysis = compute_correlation(loaded["criteria"], ids, names)
    if analysis["n_cells"] != baseline["expected_aoi_cells"]:
        raise ValueError("Correlation AOI cell count differs from the frozen baseline")
    analysis["metadata"] = {
        "baseline_id": loaded["baseline_id"],
        "baseline_manifest": BASELINE_MANIFEST.as_posix(),
        "baseline_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "baseline_checked_files": len(baseline["files"]),
        "aoi_rule": baseline["aoi_rule"],
        "source_criterion_files": [entry for entry in baseline["files"] if entry["path"] in {row["raster_path"] for row in baseline["scenarios"]["baseline"]}],
    }
    return analysis


def _format_csv(value):
    return format(value, ".17g") if isinstance(value, float) else value


def output_contents(analysis, metadata=None) -> dict:
    """Return deterministic UTF-8 artifact bytes without touching the disk."""
    import numpy as np
    ids = analysis["criterion_ids"]
    validate_correlation(analysis["correlation"], len(ids))
    if len(analysis["statistics"]) != len(ids) or [row["criterion_id"] for row in analysis["statistics"]] != ids:
        raise ValueError("Statistics rows do not match the correlation criterion order")
    matrix_stream = io.StringIO(newline="")
    writer = csv.writer(matrix_stream, lineterminator="\n")
    writer.writerow(["criterion_id", *ids])
    for criterion_id, row in zip(ids, analysis["correlation"]):
        writer.writerow([criterion_id, *(format(float(value), ".17g") for value in row)])
    statistics_stream = io.StringIO(newline="")
    writer = csv.DictWriter(statistics_stream, fieldnames=STATISTIC_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in analysis["statistics"]:
        if any(isinstance(value, float) and not np.isfinite(value) for value in row.values()):
            raise ValueError("Statistics contain a nonfinite value")
        writer.writerow({key: _format_csv(value) for key, value in row.items()})
    contents = {
        MATRIX_FILE: matrix_stream.getvalue().encode("utf-8"),
        STATISTICS_FILE: statistics_stream.getvalue().encode("utf-8"),
    }
    manifest = {
        "format_version": 1,
        "method": "Pearson product-moment correlation",
        "scope": "Descriptive spatial association of unweighted stored criterion scores across every template-AOI cell",
        "aoi_cells": analysis["n_cells"],
        "criterion_ids": ids,
        "display_names_tr": analysis["display_names"],
        "sampling": "none; all AOI cells",
        "missing_data": "No pairwise deletion or imputation; frozen canonical QA requires every AOI criterion value to be finite and not NoData",
        "zero_scores": "Retained, including source NoData values historically converted to zero; no new recoding is performed",
        "weights_applied": False,
        "weights_modified": False,
        "p_values_computed": False,
        "interpretation_limit": "Spatial cells are not assumed independent; no significance, causality, model validation or automatic weight decision follows from these coefficients",
        "numeric_policy": analysis["numeric_policy"],
        "baseline": dict(analysis.get("metadata", {}) if metadata is None else metadata),
        "software": {"python": sys.version.split()[0], "numpy": np.__version__},
        "outputs": [{"path": name, "size": len(content), "sha256": hashlib.sha256(content).hexdigest()} for name, content in contents.items()],
    }
    contents[MANIFEST_FILE] = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    return contents


def write_outputs(analysis, output_dir, metadata=None) -> list[str]:
    """Stage all bytes, then publish without replacing any existing file.

    The manifest is linked last and identifies the two complete CSV artifacts.
    Failed publication rolls back only files linked by this call. All input and
    serialization validation finishes before any directory is created.
    """
    contents = output_contents(analysis, metadata)
    output_dir = Path(output_dir).absolute()
    if output_dir.is_symlink():
        raise ValueError("The output directory must not be a symbolic link")
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise ValueError("Output directory must be empty or new; existing content is never overwritten")
    if not output_dir.parent.is_dir():
        raise ValueError("Output directory parent must already exist")
    created_directory = False
    published = []
    try:
        with tempfile.TemporaryDirectory(prefix=".correlation-stage-", dir=output_dir.parent) as temporary:
            stage = Path(temporary)
            for name, content in contents.items():
                (stage / name).write_bytes(content)
            try:
                output_dir.mkdir()
                created_directory = True
            except FileExistsError:
                if output_dir.is_symlink() or not output_dir.is_dir() or any(output_dir.iterdir()):
                    raise ValueError("Output directory changed or contains existing content")
            for name in OUTPUT_FILES:
                target = output_dir / name
                os.link(stage / name, target)  # Exclusive publication: never overwrite.
                published.append((target, target.stat().st_ino))
    except BaseException:
        for target, inode in reversed(published):
            if target.exists() and target.stat().st_ino == inode:
                target.unlink()
        if created_directory and output_dir.exists() and not any(output_dir.iterdir()):
            output_dir.rmdir()
        raise
    return list(OUTPUT_FILES)


def compare_outputs(analysis, output_dir, metadata=None) -> dict:
    """Read and check every saved coefficient, statistic and provenance field."""
    import numpy as np
    report = {"passed": False, "checked_files": 0, "errors": []}
    output_dir = Path(output_dir)
    try:
        expected_contents = output_contents(analysis, metadata)
        contents = {}
        for name in OUTPUT_FILES:
            path = output_dir / name
            if not path.is_file():
                raise ValueError(f"Missing correlation artifact: {name}")
            contents[name] = path.read_bytes()
            report["checked_files"] += 1
        ids = analysis["criterion_ids"]
        rows = list(csv.reader(io.StringIO(contents[MATRIX_FILE].decode("utf-8"), newline="")))
        if len(rows) != len(ids) + 1 or rows[0] != ["criterion_id", *ids]:
            raise ValueError("Saved correlation matrix has incorrect labels, order or row count")
        if any(len(row) != len(ids) + 1 or row[0] != ids[index] for index, row in enumerate(rows[1:])):
            raise ValueError("Saved correlation matrix row labels or lengths differ")
        saved_matrix = np.asarray([[float(value) for value in row[1:]] for row in rows[1:]], dtype=np.float64)
        validate_correlation(saved_matrix, len(ids))
        if not np.allclose(saved_matrix, analysis["correlation"], rtol=0, atol=MATRIX_TOLERANCE):
            raise ValueError("Saved correlation coefficients differ from the recomputed full-AOI values")
        reader = csv.DictReader(io.StringIO(contents[STATISTICS_FILE].decode("utf-8"), newline=""))
        if reader.fieldnames != list(STATISTIC_COLUMNS):
            raise ValueError("Saved statistics column labels or order differ")
        saved_statistics = list(reader)
        if len(saved_statistics) != len(ids):
            raise ValueError("Saved statistics row count differs")
        integer_fields = {"aoi_cell_count", "finite_count", "nonfinite_count", "nodata_count", "zero_count"}
        for saved, expected in zip(saved_statistics, analysis["statistics"]):
            if set(saved) != set(STATISTIC_COLUMNS) or any(value is None for value in saved.values()):
                raise ValueError("Saved statistics contain missing or extra cells")
            for key, value in expected.items():
                if key in {"criterion_id", "display_name_tr"}:
                    valid = saved[key] == value
                elif key in integer_fields:
                    valid = int(saved[key]) == value
                else:
                    parsed = float(saved[key])
                    valid = np.isfinite(parsed) and abs(parsed - value) <= MATRIX_TOLERANCE
                if not valid:
                    raise ValueError(f"Saved statistic differs: {expected['criterion_id']} / {key}")
        saved_manifest = json.loads(contents[MANIFEST_FILE])
        expected_manifest = json.loads(expected_contents[MANIFEST_FILE])
        if set(saved_manifest) != set(expected_manifest):
            raise ValueError("Saved correlation manifest fields differ")
        for key, value in expected_manifest.items():
            if key not in {"software", "outputs"} and saved_manifest[key] != value:
                raise ValueError(f"Saved correlation manifest differs: {key}")
        software = saved_manifest["software"]
        if not isinstance(software, dict) or set(software) != {"python", "numpy"} or not all(isinstance(value, str) and value for value in software.values()):
            raise ValueError("Saved software provenance is missing or malformed")
        actual_outputs = [{"path": name, "size": len(contents[name]), "sha256": hashlib.sha256(contents[name]).hexdigest()} for name in (MATRIX_FILE, STATISTICS_FILE)]
        if saved_manifest["outputs"] != actual_outputs:
            raise ValueError("Saved artifact sizes or checksums differ from their manifest")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, csv.Error) as error:
        report["errors"].append(str(error))
    report["passed"] = not report["errors"]
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Read-only full-input recomputation and saved-artifact comparison (default)")
    mode.add_argument("--generate", action="store_true", help="Generate three artifacts in an explicit empty or new directory")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, help="Artifact directory; check defaults to PROJECT_ROOT/outputs/tables/criterion_correlation_v1")
    parser.add_argument("--json", action="store_true", help="Write a machine-readable result to standard output")
    args = parser.parse_args(argv)
    if args.generate and args.output_dir is None:
        parser.error("--generate requires --output-dir")
    result = {"passed": False, "mode": "generate" if args.generate else "check", "errors": []}
    exit_code = 1
    try:
        analysis = analyze_project(args.project_root)
        result.update({"baseline_id": analysis["metadata"]["baseline_id"], "aoi_cells": analysis["n_cells"], "criterion_count": len(analysis["criterion_ids"]), "pair_count": len(analysis["criterion_ids"]) * (len(analysis["criterion_ids"]) - 1) // 2})
        if args.generate:
            result["generated_files"] = write_outputs(analysis, args.output_dir)
        else:
            comparison = compare_outputs(analysis, args.output_dir or args.project_root / "outputs/tables/criterion_correlation_v1")
            result["artifact_comparison"] = comparison
            if not comparison["passed"]:
                raise ValueError("; ".join(comparison["errors"]))
        result["passed"] = True
        exit_code = 0
    except ImportError as error:
        result["errors"].append(f"Required analysis dependency unavailable: {error}")
        result["dependency_unavailable"] = True
        exit_code = 2
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, csv.Error) as error:
        result["errors"].append(str(error))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    else:
        print(f"Criterion Pearson correlation: {'PASSED' if result['passed'] else 'FAILED'} ({result['mode']})")
        for error in result["errors"]:
            print(error)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
