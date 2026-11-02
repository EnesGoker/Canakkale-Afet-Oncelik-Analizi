#!/usr/bin/env python3
"""Verify frozen analysis inputs and expose only template-AOI criterion values.

The default CLI is a standard-library checksum check. load_frozen_inputs()
additionally requires NumPy/GDAL and reruns the canonical arithmetic checker.
No source file is changed; changing a file does not regenerate this snapshot.

--scope public-source checks a copy of the public source edition, which omits
the canonical data. The omitted records are derived twice, as the manifest's
data/processed records and as the records missing from the public selection
config; both sets must be equal, every such file must be absent and is listed
as skipped, and every other record must match. Any canonical data present in
that scope is a failure: use the full scope for a copy with data.
"""

from __future__ import annotations

import argparse
import csv
import json
import ntpath
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from check_mcda_integrity import CRITERIA
from check_portability import sha256_file

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path("config/analysis_baseline_v1.json")
PUBLIC_SELECTION = "config/public_source_release_v1.json"
PUBLIC_OMITTED_PREFIX = "data/processed/"
SKIP_REASON = "not distributed in the public source edition"
FULL_CHECK = "python3 scripts/python/analysis_baseline.py --check"
WEIGHTS = "config/mcda_weights.tsv"
ANALYSIS = "data/processed/analysis/"
TEMPLATE = ANALYSIS + "analysis_template_100m_32635.tif"
OUTPUTS = [ANALYSIS + name + "_32635.tif" for name in (
    "mcda_priority_score", "mcda_priority_score_normalized", "mcda_priority_class",
)]
FIXED_INPUTS = [WEIGHTS, TEMPLATE, *OUTPUTS,
    "data/processed/admin/canakkale_districts_32635.gpkg",
    "scripts/bash/mcda_pipeline_commands.sh", "scripts/python/generate_sensitivity_tables.py",
]
SCENARIOS = ("baseline", "earthquake-heavy", "equal-weight")
NORMALIZATION = {
    "baseline": {"mode": "fixed", "minimum": 0.029, "range": 0.473, "clip": [0, 1]},
    "alternatives": {"mode": "observed_minmax_per_scenario", "class_thresholds": [0.2, 0.4, 0.6, 0.8]},
    "baseline_classes": "stored_verified_canonical",
}


def local_path(root: Path, name: str) -> Path:
    relative = Path(name)
    if relative.is_absolute() or ntpath.isabs(name) or ".." in relative.parts:
        raise ValueError("Baseline paths must be relative and inside the project")
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Baseline path escapes project root")
    return path


def weight_scenarios(root: Path) -> dict:
    with local_path(root, WEIGHTS).open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    scenarios = {}
    for name in SCENARIOS:
        selected = sorted((row for row in rows if row["scenario_id"] == name), key=lambda row: int(row["criterion_order"]))
        if [row["criterion_id"] for row in selected] != list(CRITERIA):
            raise ValueError("Baseline scenario criterion lists differ")
        scenarios[name] = [{"criterion_id": row["criterion_id"], "raster_path": row["raster_path"], "weight": float(row["weight"])} for row in selected]
    return scenarios


def public_source_omissions(root: Path, names: list[str]) -> set[str]:
    """Return the records the public source edition omits; both definitions must agree."""
    selection = json.loads(local_path(root, PUBLIC_SELECTION).read_text(encoding="utf-8"))
    published = {row if isinstance(row, str) else row["path"] for row in selection["files"]}
    by_prefix = {name for name in names if name.startswith(PUBLIC_OMITTED_PREFIX)}
    by_selection = {name for name in names if name not in published}
    if not by_prefix or by_prefix != by_selection:
        raise ValueError("Public-source omissions differ between the data/processed rule and the public "
                         "selection: " + ", ".join(sorted(by_prefix ^ by_selection) or ["no omitted records"]))
    return by_prefix


def verify_baseline(root=ROOT, manifest_path=MANIFEST, scope="full") -> dict:
    root = Path(root).resolve()
    result = {"passed": False, "scope": scope, "errors": [], "checked_files": 0, "verified_files": 0,
              "missing_files": [], "skipped_files": []}
    if scope not in ("full", "public-source"):
        raise ValueError(f"Unknown baseline scope: {scope}")
    try:
        manifest = json.loads(local_path(root, str(manifest_path)).read_text(encoding="utf-8"))
        if manifest["format_version"] != 1 or not manifest["baseline_id"]:
            raise ValueError("Unsupported baseline manifest")
        result["baseline_id"] = manifest["baseline_id"]
        if manifest["aoi_rule"] != "template_equals_1" or manifest["normalization"] != NORMALIZATION:
            raise ValueError("AOI or normalization policy differs from the frozen analysis contract")
        if manifest["class_thresholds"] != NORMALIZATION["alternatives"]["class_thresholds"]:
            raise ValueError("Class thresholds differ from the frozen analysis contract")
        if type(manifest["expected_aoi_cells"]) is not int or manifest["expected_aoi_cells"] <= 0:
            raise ValueError("Expected AOI cell count must be a positive integer")
        scenarios = weight_scenarios(root)
        if manifest["scenarios"] != scenarios:
            raise ValueError("Scenario definitions differ from the frozen manifest")
        records = manifest["files"]
        names = [entry["path"] for entry in records]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate baseline file record")
        required = set(FIXED_INPUTS) | {item["raster_path"] for item in scenarios["baseline"]}
        references = manifest["reference_tables"]
        if len(references) != 8 or len(set(references)) != 8:
            raise ValueError("Expected eight frozen reference CSV tables")
        required.update(references)
        if not required.issubset(names):
            raise ValueError("A required baseline input/reference is not covered by checksums")
        omitted = public_source_omissions(root, names) if scope == "public-source" else set()
        present = []
        for entry in records:
            path = local_path(root, entry["path"])
            if entry["path"] in omitted:
                if path.exists() or path.is_symlink():
                    present.append(entry["path"])
                    result["errors"].append(f"Canonical data file present in the public-source scope: {entry['path']}")
                else:
                    result["skipped_files"].append(entry["path"])
            elif not path.is_file():
                result["missing_files"].append(entry["path"])
                result["errors"].append(f"Missing frozen file: {entry['path']}")
            elif path.stat().st_size != entry["size"] or sha256_file(path) != entry["sha256"]:
                result["errors"].append(f"Changed frozen file: {entry['path']}")
            else:
                result["verified_files"] += 1
            result["checked_files"] += 1
        if present:
            result["errors"].append(f"This copy contains canonical data ({len(present)} of {len(omitted)} omitted "
                                    f"records); check it in the full scope instead: {FULL_CHECK}")
        if omitted:
            result["skip_reason"] = SKIP_REASON
    except (OSError, ValueError, KeyError, TypeError, csv.Error) as error:
        result["errors"].append(str(error))
    result["passed"] = not result["errors"]
    return result


def select_aoi_values(array, aoi):
    """Return a separate 1-D array; outside-AOI values never enter analyses."""
    import numpy as np
    if array.shape != aoi.shape or aoi.dtype != np.dtype(bool):
        raise ValueError("A matching boolean template AOI is required")
    return array[aoi].copy()


def load_frozen_inputs(root=ROOT, manifest_path=MANIFEST) -> dict:
    root = Path(root).resolve()
    verification = verify_baseline(root, manifest_path)
    if not verification["passed"]:
        raise ValueError("Frozen baseline validation failed: " + "; ".join(verification["errors"]))
    import numpy as np
    from osgeo import gdal, osr
    from check_mcda_integrity import check_project
    qa = check_project(root, np, gdal, osr)
    if not qa["passed"]:
        raise ValueError("Canonical numerical QA failed before loading analysis inputs")
    manifest = json.loads(local_path(root, str(manifest_path)).read_text(encoding="utf-8"))
    if qa["summary"]["aoi_cells"] != manifest["expected_aoi_cells"]:
        raise ValueError("AOI cell count differs from the frozen manifest")
    template = gdal.OpenEx(str(root / TEMPLATE), gdal.OF_RASTER | gdal.OF_READONLY)
    aoi = template.GetRasterBand(1).ReadAsArray() == 1
    result = {"baseline_id": verification["baseline_id"], "aoi": aoi,
              "grid": template.GetGeoTransform(), "projection": template.GetProjectionRef(),
              "scenarios": weight_scenarios(root), "criteria": {}}
    for row in result["scenarios"]["baseline"]:
        dataset = gdal.OpenEx(str(root / row["raster_path"]), gdal.OF_RASTER | gdal.OF_READONLY)
        result["criteria"][row["criterion_id"]] = select_aoi_values(dataset.GetRasterBand(1).ReadAsArray(), aoi)
    dataset = gdal.OpenEx(str(root / OUTPUTS[2]), gdal.OF_RASTER | gdal.OF_READONLY)
    result["baseline_class"] = select_aoi_values(dataset.GetRasterBand(1).ReadAsArray(), aoi)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Read-only checksum validation (default)")
    parser.add_argument("--scope", choices=("full", "public-source"), default="full",
                        help="full: every frozen file must match (default); public-source: canonical data is omitted")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = verify_baseline(args.project_root, scope=args.scope)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        label = "" if args.scope == "full" else " (public-source scope)"
        counts = [f"{result['verified_files']} verified"]
        counts += [f"{len(result['skipped_files'])} skipped"] if result["skipped_files"] else []
        counts += [f"{len(result['missing_files'])} missing"] if result["missing_files"] else []
        print(f"Frozen analysis baseline{label}: {'PASSED' if result['passed'] else 'FAILED'}; "
              f"{result['checked_files']} files checked: {', '.join(counts)}")
        for name in result["skipped_files"]:
            print(f"SKIPPED ({SKIP_REASON}): {name}")
        for error in result["errors"]:
            print(error)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
