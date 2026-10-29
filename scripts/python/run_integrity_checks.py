#!/usr/bin/env python3
"""Run numerical and real QGIS checks using available GIS Python runtimes.

Exit 0: all required checks passed; 1: a check failed; 2: checks incomplete
because a runtime/dependency is unavailable. Never writes project files.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHECKS = (
    ("Sabitlenmiş analiz girdileri", "analysis_baseline.py", (), "PYTHON_BIN"),
    ("MCDA raster ve hesap bütünlüğü", "check_mcda_integrity.py", ("numpy", "osgeo.gdal"), "GDAL_PYTHON_BIN"),
    ("Kriter kaynak–skor sayısal eşdeğerliği", "check_criterion_transformations.py", ("numpy", "osgeo.gdal"), "GDAL_PYTHON_BIN"),
    ("Korelasyon yeniden hesabı ve kayıtlı CSV/manifest", "generate_correlation_analysis.py", ("numpy", "osgeo.gdal"), "GDAL_PYTHON_BIN"),
    ("Korelasyon figürü ve kaynak checksum'ları", "plot_criterion_correlation.py", ("numpy",), "GDAL_PYTHON_BIN"),
    ("Senaryo ortaklığı yeniden hesabı ve kayıtlı raster/tablolar", "generate_scenario_agreement.py", ("numpy", "osgeo.gdal"), "GDAL_PYTHON_BIN"),
    ("Senaryo ortaklık haritası ve kaynak checksum'ları", "plot_scenario_agreement.py", ("numpy", "osgeo.gdal"), "GDAL_PYTHON_BIN"),
    ("QGIS düzenleri, kilitli stiller ve kayıtlı harita/atlas dosyaları", "check_map_layouts.py", (), "PYTHON_BIN"),
    ("QGIS gerçek proje okuma ve yerel katmanlar", "check_qgis_runtime.py", ("qgis.core",), "QGIS_PYTHON_BIN"),
)


def runtime_environment(executable: str, source: dict[str, str]) -> dict[str, str]:
    env = source.copy()
    env.update(PYTHONDONTWRITEBYTECODE="1", GDAL_PAM_ENABLED="NO", QT_QPA_PLATFORM="offscreen")
    # macOS bundles may keep bindings outside the interpreter's default path.
    # Derive this from a selected executable/configuration, never a user path.
    for directory in (Path(executable).parent, Path(source.get("QGIS_BIN", "."))):
        resources = directory.parent / "Resources" / "qgis"
        bindings = resources / "python"
        if directory.name != "MacOS" or not bindings.is_dir():
            continue
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(bindings) + (os.pathsep + existing if existing else "")
        for variable, child in (("PROJ_DATA", "proj"), ("GDAL_DATA", "gdal")):
            if (resources / child).is_dir():
                env.setdefault(variable, str(resources / child))
        break
    return env


def resolve_runtime(modules: tuple[str, ...], variable: str, source: dict[str, str]):
    explicit = source.get(variable)
    candidates = [explicit] if explicit else [
        str(Path(source["QGIS_BIN"]) / "python") if source.get("QGIS_BIN") else None,
        str(Path(source["QGIS_BIN"]) / "python3") if source.get("QGIS_BIN") else None,
        source.get("PYTHON_BIN"), sys.executable, shutil.which("python3"),
    ]
    seen = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        executable = shutil.which(candidate)
        if not executable:
            if explicit:
                raise ValueError(f"Ayarlanmış {variable} çalıştırılabilir değil.")
            continue
        env = runtime_environment(executable, source)
        imports = "\n".join(f"    importlib.import_module({name!r})" for name in modules) or "    pass"
        probe = "import importlib, sys\ntry:\n" + imports + "\nexcept (ImportError, OSError):\n    sys.exit(2)\n"
        try:
            result = subprocess.run([executable, "-c", probe], env=env, capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired) as error:
            if explicit:
                raise ValueError(f"Ayarlanmış {variable} başlatılamadı ({type(error).__name__}).") from error
            continue
        if result.returncode == 0:
            return executable, env
        if explicit and result.returncode != 2:
            raise ValueError(f"Ayarlanmış {variable} modül denemesi başarısız (çıkış {result.returncode}).")
    return None


def execute_check(executable: str, env: dict[str, str], script: Path, root: Path) -> dict:
    try:
        result = subprocess.run(
            [executable, str(script), "--check", "--project-root", str(root), "--json"],
            env=env, capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"exit_code": 1, "status": "failed", "message": f"Kontrol çalıştırılamadı: {type(error).__name__}"}
    status = {0: "passed", 1: "failed", 2: "skipped"}.get(result.returncode, "failed")
    record = {"exit_code": result.returncode if result.returncode in (0, 1, 2) else 1, "status": status}
    try:
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict):
            raise ValueError("Kontrol sonucu JSON nesnesi olmalı")
        record["result"] = payload
        if result.returncode == 0 and payload.get("passed") is not True:
            record.update(exit_code=1, status="failed", message="Çıkış kodu ile kontrol sonucu tutarsız.")
    except (ValueError, TypeError):
        record.update(exit_code=1, status="failed", message="Kontrol geçerli JSON sonucu üretmedi.")
    if result.stderr.strip():
        record["diagnostic"] = result.stderr.strip()
    return record


def aggregate_exit_code(records: list[dict]) -> int:
    if any(record["status"] == "failed" for record in records):
        return 1
    if any(record["status"] == "skipped" for record in records):
        return 2
    return 0


def print_human_result(result: dict) -> None:
    summary = result.get("summary", {})
    if "aoi_cells" in summary:
        count = summary.get("criterion_count", summary.get("verified_equivalent_formulas", summary.get("expected_criteria")))
        print(f"  Kriter: {count}; AOI: {summary['aoi_cells']} hücre.")
        if "weight_sum" in summary:
            print(f"  Ağırlık toplamı: {summary['weight_sum']:.12g}.")
    if "checked_files" in result:
        if "baseline_id" in result:
            print(f"  Baseline: {result['baseline_id']}; dosya: {result['checked_files']}.")
        else:
            print(f"  Kontrol edilen kayıtlı dosya: {result['checked_files']}.")
    if "pair_count" in result:
        print(f"  Kriter: {result['criterion_count']}; AOI: {result['aoi_cells']} hücre; çift: {result['pair_count']}.")
        print(f"  Kayıtlı analiz dosyası: {result.get('artifact_comparison', {}).get('checked_files', 0)}.")
    if "scenario_count" in result:
        print(f"  Senaryo: {result['scenario_count']}; ilçe: {result['district_count']}; AOI: {result['aoi_cells']} hücre.")
        comparison = result.get("artifact_comparison", {})
        print(f"  Kayıtlı dosya: {comparison.get('checked_files', 0)}; raster hücresi: {comparison.get('checked_raster_cells', 0)}; tablo satırı: {comparison.get('checked_table_rows', 0)}.")
        print(f"  Sayısal karşılaştırılan eski CSV: {result.get('reference_validation', {}).get('numeric_tables_checked', 0)}.")
    if result.get("message"):
        print(f"  {result['message']}")
    for raster in result.get("rasters", []):
        if "mismatch_aoi_cells" in raster:
            print(f"  {Path(raster['path']).name}: farklı hücre {raster['mismatch_aoi_cells']}; en büyük mutlak fark {raster['maximum_absolute_difference_aoi']}.")
    for check in result.get("checks", []):
        if check["name"].startswith("equivalent_formula:") and check["status"] == "passed":
            details = check["details"]
            print(f"  {check['name'].split(':', 1)[1]}: farklı hücre {details['mismatch_aoi_cells']}; en büyük mutlak fark {details['maximum_absolute_difference_aoi']}.")
        if check["status"] not in ("passed",):
            label = {"warning": "UYARI", "failed": "HATA", "unavailable": "ATLANDI"}.get(check["status"], check["status"])
            details = " " + json.dumps(check["details"], ensure_ascii=False) if check.get("details") else ""
            print(f"  {label}: {check['message']}{details}")
    if "layout_count" in result:
        print(f"  QGIS düzeni: {result['layout_count']}; kayıtlı harita/atlas dosyası: {result.get('export_count', 0)}.")
        print("  PDF sayfa sayıları dışa aktarma anında kaydedilir; burada kayıtlı dosya checksum'ları denetlenir.")
    if "project_read" in result:
        print(f"  Proje okundu: {result['project_read']}; yerel katman: {result['local_layer_count']}; geçersiz: {result['invalid_local_layer_count']}.")
    for row in result.get("web_layers", []):
        print(f"  ATLANDI: {row['name']}; web bağlantısı/döşeme erişimi sınanmadı.")
    for error in result.get("errors", []):
        print(f"  HATA: {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Salt okunur kontrol (varsayılan)")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--json", action="store_true", help="Yapılandırılmış sonucu stdout'a yaz")
    args = parser.parse_args()
    root = args.project_root.resolve()
    records = []
    for label, filename, modules, variable in CHECKS:
        try:
            runtime = resolve_runtime(modules, variable, os.environ)
        except ValueError as error:
            records.append({"exit_code": 1, "status": "failed", "name": label, "message": str(error)})
            continue
        if runtime is None:
            record = {"exit_code": 2, "status": "skipped", "message": f"Gerekli Python modülleri kullanılamıyor: {', '.join(modules)}. {variable} ile uygun Python seçin."}
        else:
            executable, env = runtime
            record = execute_check(executable, env, Path(__file__).parent / filename, root)
        record["name"] = label
        records.append(record)
    code = aggregate_exit_code(records)
    if args.json:
        print(json.dumps({"exit_code": code, "passed": code == 0, "checks": records}, ensure_ascii=False, indent=2))
    else:
        for record in records:
            prefix = {"passed": "GEÇTİ", "failed": "BAŞARISIZ", "skipped": "ATLANDI"}[record["status"]]
            print(f"{prefix}: {record['name']}")
            if "message" in record:
                print(record["message"])
            if "result" in record:
                print_human_result(record["result"])
            if "diagnostic" in record:
                print(record["diagnostic"], file=sys.stderr)
        print({0: "Zorunlu bütünlük kontrolleri geçti.", 1: "Bütünlük kontrolü başarısız.", 2: "Bütünlük kontrolleri eksik: atlanan kontrol var."}[code])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
