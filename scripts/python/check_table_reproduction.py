#!/usr/bin/env python3
"""Regenerate report or sensitivity tables and compare them byte for byte.

The generator runs unchanged in a child process inside a temporary sandbox
with the relative output directory outputs/tables, so path labels in its
manifest match the saved ones. Its clock is pinned to the single
"Üretim zamanı (UTC)" line of the saved manifest; a missing, repeated or
malformed line fails the check. Every expected file must exist on both sides
with identical bytes, and the generator must write nothing else. Project
files are never written. Exit 0: all identical; 1: difference or failure;
2: a required dependency is unavailable (not a success).
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = Path(__file__).resolve().parent
OUTPUT_DIR = Path("outputs/tables")
STAMP_PREFIX = "Üretim zamanı (UTC):"
STAMP = re.compile(r"Üretim zamanı \(UTC\): `(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00)`")
GDAL_TOOLS = ("GDALINFO", "GDAL_TRANSLATE", "GDAL_RASTERIZE", "OGRINFO", "OGR2OGR")
TABLE_SETS = {
    "report": {
        "title": "Rapor tabloları", "module": "generate_report_tables", "manifest": "report_tables_manifest.md",
        "requires_env": GDAL_TOOLS,
        "files": ["mcda_class_distribution.csv", "mcda_class_distribution.md", "mcda_class_area_by_district.csv",
                  "mcda_class_area_by_district.md", "criterion_raster_statistics.csv", "criterion_raster_statistics.md",
                  "report_tables_manifest.md"],
    },
    "sensitivity": {
        "title": "Duyarlılık tabloları", "module": "generate_sensitivity_tables", "manifest": "mcda_sensitivity_manifest.md",
        "requires_env": GDAL_TOOLS,
        "files": ["mcda_sensitivity_scenario_summary.csv", "mcda_sensitivity_scenario_summary.md",
                  "mcda_sensitivity_interpretation.csv", "mcda_sensitivity_interpretation.md",
                  "mcda_sensitivity_class_distribution.csv", "mcda_sensitivity_class_distribution.md",
                  "mcda_sensitivity_top_districts.csv", "mcda_sensitivity_top_districts.md",
                  "mcda_sensitivity_class_transition.csv", "mcda_sensitivity_class_transition.md",
                  "mcda_sensitivity_manifest.md"],
    },
}
CHILD = r'''
import datetime as clock
from pathlib import Path
import sys

sys.dont_write_bytecode = True
scripts, module_name, project_root, stamp = sys.argv[1:5]
sys.path.insert(0, scripts)
try:
    module = __import__(module_name)
except ImportError as error:
    print(f"Gerekli modül yüklenemedi: {error.name}", file=sys.stderr)
    raise SystemExit(2)
if getattr(module, "datetime", None) is not clock.datetime:
    print("Üretici saati beklenen datetime.datetime adıyla okumuyor; saat sabitlenemedi.", file=sys.stderr)
    raise SystemExit(1)
recorded = clock.datetime.fromisoformat(stamp)


class RecordedClock(clock.datetime):
    @classmethod
    def now(cls, tz=None):
        if tz is None:
            raise RuntimeError("Saat dilimsiz now() çağrısı beklenmiyordu.")
        return recorded.astimezone(tz)


module.datetime = RecordedClock
module.generate(Path(project_root), Path("outputs/tables"))
'''


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def recorded_stamp(manifest: Path) -> str:
    """Return the saved generation time; raise ValueError unless exactly one valid line exists."""
    if not manifest.is_file():
        raise ValueError(f"Kayıtlı manifest yok: {OUTPUT_DIR / manifest.name}")
    lines = [line for line in manifest.read_text(encoding="utf-8").splitlines() if line.startswith(STAMP_PREFIX)]
    if len(lines) != 1:
        raise ValueError(f"Kayıtlı manifestte tam bir '{STAMP_PREFIX}' satırı olmalı; bulunan: {len(lines)}")
    match = STAMP.fullmatch(lines[0])
    if not match:
        raise ValueError(f"Kayıtlı manifestteki üretim zamanı satırı geçersiz: {lines[0]!r}")
    datetime.fromisoformat(match.group(1))
    return match.group(1)


def first_difference(left: bytes, right: bytes) -> int:
    a, b = left.split(b"\n"), right.split(b"\n")
    for number, (x, y) in enumerate(zip(a, b), 1):
        if x != y:
            return number
    return min(len(a), len(b)) + 1


def check_tables(table_set: dict, project_root: Path = ROOT, scripts_dir: Path = SCRIPTS,
                 python: str = sys.executable) -> dict:
    project_root = Path(project_root).resolve()
    recorded_dir = project_root / OUTPUT_DIR
    result = {"table_set": table_set["title"], "passed": False, "status": "failed", "pinned_generated_utc": None,
              "files": [], "extra_files": [], "errors": []}
    try:
        result["pinned_generated_utc"] = recorded_stamp(recorded_dir / table_set["manifest"])
    except (OSError, UnicodeError, ValueError) as error:
        result["errors"].append(str(error))
        return result
    missing_env = [name for name in table_set.get("requires_env", ()) if not os.environ.get(name)]
    if missing_env:
        result["status"] = "dependency_unavailable"
        result["errors"].append("Gerekli GDAL/OGR araç değişkenleri eksik: " + ", ".join(missing_env))
        return result
    with tempfile.TemporaryDirectory(prefix="canakkale-table-check-") as sandbox:
        sandbox = Path(sandbox)
        process = subprocess.run([python, "-B", "-c", CHILD, str(scripts_dir), table_set["module"],
                                  str(project_root), result["pinned_generated_utc"]],
                                 cwd=sandbox, capture_output=True, text=True, timeout=1800)
        if process.returncode != 0:
            result["status"] = "dependency_unavailable" if process.returncode == 2 else "failed"
            detail = (process.stderr.strip() or process.stdout.strip()).splitlines()[-12:]
            result["errors"].append(f"Üretici çalıştırılamadı (çıkış {process.returncode}): " + " / ".join(detail))
            return result
        generated_dir = sandbox / OUTPUT_DIR
        written = sorted(path.relative_to(sandbox).as_posix() for path in sandbox.rglob("*") if path.is_file())
        expected = [(OUTPUT_DIR / name).as_posix() for name in table_set["files"]]
        result["extra_files"] = [name for name in written if name not in expected]
        for name in table_set["files"]:
            produced, saved = generated_dir / name, recorded_dir / name
            row = {"path": (OUTPUT_DIR / name).as_posix()}
            if not produced.is_file():
                row["status"] = "not_generated"
            elif not saved.is_file():
                row.update(status="not_recorded", sha256_generated=sha256(produced.read_bytes()))
            else:
                new, old = produced.read_bytes(), saved.read_bytes()
                row.update(status="identical" if new == old else "different",
                           sha256_generated=sha256(new), sha256_recorded=sha256(old))
                if new != old:
                    row["first_different_line"] = first_difference(new, old)
            result["files"].append(row)
    bad = [row["path"] for row in result["files"] if row["status"] != "identical"]
    if bad:
        result["errors"].append("Kayıtlı çıktıyla bayt bayt aynı olmayan dosyalar: " + ", ".join(bad))
    if result["extra_files"]:
        result["errors"].append("Üretici beklenmeyen dosya yazdı: " + ", ".join(result["extra_files"]))
    result["passed"] = not result["errors"]
    result["status"] = "passed" if result["passed"] else "failed"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table-set", required=True, choices=sorted(TABLE_SETS))
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    table_set = TABLE_SETS[args.table_set]
    result = check_tables(table_set, args.project_root)
    code = 0 if result["passed"] else 2 if result["status"] == "dependency_unavailable" else 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    print(f"{table_set['title']}: kayıtlı {OUTPUT_DIR.as_posix()} dosyalarıyla bayt bayt karşılaştırma")
    if result["pinned_generated_utc"]:
        print(f"Sabit üretim zamanı (kayıtlı manifestten): {result['pinned_generated_utc']}")
    labels = {"identical": "AYNI", "different": "FARKLI", "not_generated": "ÜRETİLMEDİ", "not_recorded": "KAYITLI DOSYA YOK"}
    for row in result["files"]:
        line = f"  {labels[row['status']]:<17} {row['path']}"
        if row["status"] == "different":
            line += f" (ilk fark: satır {row['first_different_line']})"
        print(line)
    for error in result["errors"]:
        print(f"HATA: {error}", file=sys.stderr)
    total = len(table_set["files"])
    if code == 0:
        print(f"GEÇTİ: {total}/{total} dosya kayıtlı çıktıyla bayt bayt aynı.")
    elif code == 2:
        print("ATLANDI: karşılaştırma yapılamadı; başarılı sayılmaz.", file=sys.stderr)
    else:
        same = sum(row["status"] == "identical" for row in result["files"])
        print(f"BAŞARISIZ: {same}/{total} dosya aynı; ayrıntılar yukarıda.", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
