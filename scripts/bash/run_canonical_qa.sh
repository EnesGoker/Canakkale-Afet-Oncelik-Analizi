#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Çanakkale Afet Öncelik Analizi
# Canonical QA Runner
# ============================================================
#
# Amaç:
#   Read-only canonical proje kontrollerini tek giriş noktasından çalıştırır.
#
# Güvenlik:
#   Varsayılan ve tek operasyonel mod --check'tir. Bu runner proje
#   verisi oluşturmaz, üzerine yazmaz, taşımaz veya silmez. Geçici dosyalar
#   yalnızca sistem temp dizini altında oluşturulur.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/project_env.sh"

MODE="${1:---check}"
TEMP_DIR=""
INCOMPLETE_CHECKS=0

SLASH="/"
ICLOUD_PATTERN="i"
ICLOUD_PATTERN+="Cloud"
MOBILE_DOCS_PATTERN="Mobile"
MOBILE_DOCS_PATTERN+=" Documents"
OLD_PROJECT_PATTERN="canakkale-fault-line-"
OLD_PROJECT_PATTERN+="research"
DATASETS_PATTERN="datasets"
DATASETS_PATTERN+="$SLASH"
FAULT_RAW_PATTERN="DFY_GEO_"
FAULT_RAW_PATTERN+="WGS84"
DOWNLOADS_PATTERN="Down"
DOWNLOADS_PATTERN+="loads"

ABSOLUTE_PATH_PATTERN="${SLASH}Users${SLASH}|${SLASH}Volumes${SLASH}|Documents${SLASH}Projects|${ICLOUD_PATTERN}|${MOBILE_DOCS_PATTERN}|${OLD_PROJECT_PATTERN}|${DATASETS_PATTERN}|${FAULT_RAW_PATTERN}|${DOWNLOADS_PATTERN}|~${SLASH}Okulda|~${SLASH}Documents"
VRT_PATTERN='data/interim|\.vrt|canakkale_dem_mosaic|canakkale_worldcover_2021_mosaic|canakkale_tree_cover_density_2021_mosaic'

QGIS_PROJECT="qgis/canakkale_disaster_priority.qgz"
QGIS_QGS_NAME="canakkale_disaster_priority.qgs"

INTERIM_VRTS=(
  "data/interim/dem/canakkale_dem_mosaic_4326.vrt"
  "data/interim/landcover/canakkale_worldcover_2021_mosaic_4326.vrt"
  "data/interim/landcover/canakkale_tree_cover_density_2021_mosaic_3035.vrt"
)

CHECK_SCRIPTS=(
  "scripts/bash/mcda_pipeline_commands.sh"
  "scripts/bash/population_processing_pipeline.sh"
  "scripts/bash/vs30_processing_pipeline.sh"
  "scripts/bash/fault_processing_pipeline.sh"
  "scripts/bash/generate_report_tables.sh"
  "scripts/bash/generate_sensitivity_tables.sh"
)

SCRIPT_REFERENCE_FILES=(
  "scripts/bash/audit_project_tree.sh"
  "scripts/bash/mcda_pipeline_commands.sh"
  "scripts/bash/population_processing_pipeline.sh"
  "scripts/bash/vs30_processing_pipeline.sh"
  "scripts/bash/fault_processing_pipeline.sh"
  "scripts/bash/generate_report_tables.sh"
  "scripts/bash/generate_sensitivity_tables.sh"
)

ALL_BASH_SCRIPTS=(
  "scripts/bash/lib/project_env.sh"
  "scripts/bash/audit_project_tree.sh"
  "scripts/bash/mcda_pipeline_commands.sh"
  "scripts/bash/population_processing_pipeline.sh"
  "scripts/bash/vs30_processing_pipeline.sh"
  "scripts/bash/fault_processing_pipeline.sh"
  "scripts/bash/run_canonical_qa.sh"
  "scripts/bash/generate_report_tables.sh"
  "scripts/bash/generate_sensitivity_tables.sh"
  "scripts/bash/build_academic_report.sh"
)

PYTHON_SCRIPTS=(
  "scripts/python/generate_report_tables.py"
  "scripts/python/generate_sensitivity_tables.py"
  "scripts/python/build_academic_report.py"
  "scripts/python/run_integrity_checks.py"
  "scripts/python/check_mcda_integrity.py"
  "scripts/python/check_qgis_runtime.py"
  "scripts/python/test_mcda_integrity.py"
  "scripts/python/test_qgis_runtime.py"
  "scripts/python/test_integrity_runner.py"
  "scripts/python/check_criterion_transformations.py"
  "scripts/python/test_criterion_transformations.py"
  "scripts/python/analysis_baseline.py"
  "scripts/python/test_analysis_baseline.py"
  "scripts/python/generate_correlation_analysis.py"
  "scripts/python/test_correlation_analysis.py"
  "scripts/python/plot_criterion_correlation.py"
  "scripts/python/test_plot_criterion_correlation.py"
  "scripts/python/generate_scenario_agreement.py"
  "scripts/python/test_scenario_agreement.py"
  "scripts/python/plot_scenario_agreement.py"
  "scripts/python/test_plot_scenario_agreement.py"
  "scripts/python/check_map_layouts.py"
  "scripts/python/qgis_identity.py"
  "scripts/python/test_map_layouts.py"
  "scripts/python/test_qgis_identity.py"
  "scripts/python/open_qgis_with_carto.py"
  "scripts/python/qgis_carto_startup.py"
  "scripts/python/test_carto_runtime.py"
  "scripts/python/run_compatible_qa.py"
  "scripts/python/test_compatible_qa.py"
  "scripts/python/export_map_layouts.py"
  "scripts/python/test_export_map_layouts.py"
)

usage() {
  cat <<'EOF'
Kullanım:
  scripts/bash/run_canonical_qa.sh --check

Mod:
  --check   Read-only canonical QA kontrollerini çalıştırır.

Araç bulma:
  GDAL/QGIS araçları PATH, GDAL_BIN, QGIS_BIN veya GDALINFO, GDAL_CALC,
  OGRINFO, OGR2OGR ve QGIS_PROCESS gibi açık araç değişkenleriyle çözülür.

Kontroller:
  - bash/python script syntax kontrolleri
  - scripts, docs, data/interim ve QGIS XML için kişisel/yerel path audit
  - QGIS QGZ paketi, XML ve relative datasource bütünlüğü
  - gerçek QGIS proje okuma ve yerel katman geçerliliği (PyQGIS)
  - 11 kriterin CRS/grid, AOI/NoData ve skor aralığı kontrolü (GDAL Python/numpy)
  - baseline ham/normalize skor ve sınıfların bağımsız yeniden hesabı
  - sabitlenmiş analiz girdilerinin checksum kontrolü
  - 8 kaynak–skor eşdeğer reçetesinin sayısal denetimi (tarihsel kanıt sınırı ayrı)
  - korelasyonun yeniden hesabı, kayıtlı CSV/manifest ve figür checksum kontrolü
  - üç senaryonun ortaklık rasterları, il/ilçe tabloları ve harita checksum kontrolü
  - 13 QGIS düzeni, katman/stil kilitleri, QGS/QGZ eşliği ve 27 harita/atlas checksum kontrolü
  - interim VRT XML ve path politikası
  - MCDA, population, VS30/site condition, fault, report table ve sensitivity --check scriptleri

Çıkış: 0 tüm zorunlu kontroller geçti; 1 başarısız; 2 eksik Python bağımlılığı
nedeniyle atlanan zorunlu kontrol var. Web tile bağlantısı çevrimdışı atlanır.
GIS Python seçimi: GDAL_PYTHON_BIN, QGIS_PYTHON_BIN veya QGIS_BIN içindeki Python.
EOF
}

cleanup() {
  if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
    rm -rf "$TEMP_DIR"
  fi
}
trap cleanup EXIT

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    die "Gerekli komut eksik: $command_name"
  fi
}

print_step() {
  local name="$1"
  echo ""
  echo "== $name =="
}

pass_step() {
  local name="$1"
  echo "GEÇTİ: $name"
}

prepare_temp_dir() {
  if [[ -z "$TEMP_DIR" ]]; then
    TEMP_DIR="$(mktemp -d)"
  fi
}

check_required_commands() {
  local step="Gerekli shell araçları"
  print_step "$step"

  require_command bash
  require_command find
  require_command grep
  require_command sort
  require_command awk
  require_command wc
  require_command perl
  require_command unzip
  require_command xmllint

  pass_step "$step"
}

check_bash_syntax() {
  local step="Script syntax"
  print_step "$step"

  local script
  for script in "${ALL_BASH_SCRIPTS[@]}"; do
    require_file "$script"
    bash -n "$script"
  done

  local python_bin="${PYTHON_BIN:-python3}"
  if ! command -v "$python_bin" >/dev/null 2>&1; then
    die "Syntax kontrolü için gerekli Python executable eksik: $python_bin"
  fi

  for script in "${PYTHON_SCRIPTS[@]}"; do
    require_file "$script"
    "$python_bin" - "$script" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
compile(path.read_bytes(), str(path), "exec")
PY
  done

  pass_step "$step"
}

check_text_path_audit() {
  local step="Text path portability audit"
  print_step "$step"

  prepare_temp_dir
  local hits="$TEMP_DIR/text_path_hits.txt"

  local search_dirs=(scripts docs)
  if [[ -d data/interim ]]; then
    search_dirs+=(data/interim)
  fi

  find "${search_dirs[@]}" \
    -type f \
    \( -name "*.sh" -o -name "*.py" -o -name "*.md" -o -name "*.txt" -o -name "*.vrt" -o -name "*.xml" \) \
    -print0 |
    xargs -0 grep -nE "$ABSOLUTE_PATH_PATTERN" >"$hits" 2>/dev/null || true

  if [[ -s "$hits" ]]; then
    cat "$hits" >&2
    die "Metin dosyalarında kişisel/yerel path örüntüleri bulundu."
  fi

  echo "Kontrol edildi: ${search_dirs[*]}"
  pass_step "$step"
}

extract_qgis_project() {
  prepare_temp_dir

  require_file "$QGIS_PROJECT"
  unzip -p "$QGIS_PROJECT" "$QGIS_QGS_NAME" >"$TEMP_DIR/$QGIS_QGS_NAME"
}

check_qgis_project() {
  local step="QGIS proje taşınabilirliği"
  print_step "$step"

  prepare_temp_dir
  extract_qgis_project

  local qgs="$TEMP_DIR/$QGIS_QGS_NAME"
  local sources="$TEMP_DIR/qgis_relative_sources.txt"
  local missing="$TEMP_DIR/qgis_missing_sources.txt"
  local path_hits="$TEMP_DIR/qgis_path_hits.txt"

  unzip -Z1 "$QGIS_PROJECT" | awk -v name="$QGIS_QGS_NAME" '$0 == name { found = 1 } END { exit found ? 0 : 1 }' ||
    die "QGZ paketi $QGIS_QGS_NAME dosyasını içermiyor"

  xmllint --noout "$qgs"

  grep -nE "$ABSOLUTE_PATH_PATTERN" "$qgs" >"$path_hits" || true
  if [[ -s "$path_hits" ]]; then
    cat "$path_hits" >&2
    die "QGIS projesinde kişisel/yerel path örüntüleri bulundu."
  fi

  perl -ne 'while (/<datasource>([^<]*)<\/datasource>/g) { print "$1\n" } while (/source="([^"]*)"/g) { print "$1\n" }' "$qgs" |
    sort -u |
    awk '/^\.\.\// { sub(/\|.*/, ""); print }' |
    sort -u >"$sources"

  : >"$missing"
  local rel
  while IFS= read -r rel; do
    if [[ ! -e "qgis/$rel" ]]; then
      echo "$rel" >>"$missing"
    fi
  done <"$sources"

  if [[ -s "$missing" ]]; then
    cat "$missing" >&2
    die "Relative QGIS datasource dosyaları eksik."
  fi

  echo "Relative yerel QGIS kaynakları: $(wc -l <"$sources" | tr -d ' ')"
  echo "Eksik relative QGIS kaynakları: 0"

  pass_step "$step"
}

check_integrity_runtime() {
  local step="Gerçek QGIS ve MCDA bütünlük kontrolleri"
  print_step "$step"

  local status=0
  local python_bin="${PYTHON_BIN:-python3}"
  run_geo "$python_bin" scripts/python/run_integrity_checks.py --check || status=$?
  if [[ $status -eq 0 ]]; then
    pass_step "$step"
  elif [[ $status -eq 2 ]]; then
    INCOMPLETE_CHECKS=$((INCOMPLETE_CHECKS + 1))
    echo "ATLANDI: GIS Python bağımlılıkları nedeniyle bütünlük kontrolleri tamamlanamadı."
  else
    die "BAŞARISIZ: Gerçek QGIS veya MCDA bütünlük kontrolü."
  fi
}

check_interim_vrts() {
  local step="Interim VRT politikası"
  print_step "$step"

  prepare_temp_dir

  local vrt
  for vrt in "${INTERIM_VRTS[@]}"; do
    if [[ -f "$vrt" ]]; then
      xmllint --noout "$vrt"
    else
      echo "VRT dosyası mevcut değil; canonical input olarak beklenmiyor: $vrt"
    fi
  done

  local path_hits="$TEMP_DIR/interim_path_hits.txt"
  if [[ -d data/interim ]]; then
    grep -RInE "$ABSOLUTE_PATH_PATTERN" data/interim >"$path_hits" || true
    if [[ -s "$path_hits" ]]; then
      cat "$path_hits" >&2
      die "data/interim içinde kişisel/yerel path örüntüleri bulundu."
    fi

    if grep -RInE '<SourceFilename relativeToVRT="0">/' data/interim >/dev/null; then
      grep -RInE '<SourceFilename relativeToVRT="0">/' data/interim >&2
      die "Mutlak VRT SourceFilename girdileri bulundu."
    fi
  else
    echo "data/interim mevcut değil; canonical input olarak beklenmiyor."
  fi

  local qgs="$TEMP_DIR/$QGIS_QGS_NAME"
  if [[ ! -f "$qgs" ]]; then
    extract_qgis_project
    qgs="$TEMP_DIR/$QGIS_QGS_NAME"
  fi

  if grep -nE "$VRT_PATTERN" "$qgs" >/dev/null; then
    grep -nE "$VRT_PATTERN" "$qgs" >&2
    die "QGIS projesi interim VRT dosyalarına referans veriyor."
  fi

  if grep -nE "$VRT_PATTERN" "${SCRIPT_REFERENCE_FILES[@]}" >/dev/null; then
    grep -nE "$VRT_PATTERN" "${SCRIPT_REFERENCE_FILES[@]}" >&2
    die "Scriptler interim VRT dosyalarına referans veriyor."
  fi

  pass_step "$step"
}

run_canonical_script_checks() {
  local step="Canonical script kontrolleri"
  print_step "$step"

  local script
  for script in "${CHECK_SCRIPTS[@]}"; do
    echo ""
    echo "-- $script --"
    require_file "$script"
    bash "$script" --check
  done

  pass_step "$step"
}

run_check() {
  project_cd_root
  export GDAL_PAM_ENABLED=NO
  export PYTHONDONTWRITEBYTECODE=1

  echo "Canonical QA runner"
  echo "Proje kökü: script konumundan çözüldü"
  echo "Mod: --check"

  check_required_commands
  check_bash_syntax
  check_text_path_audit
  check_qgis_project
  check_integrity_runtime
  check_interim_vrts
  run_canonical_script_checks

  echo ""
  if [[ $INCOMPLETE_CHECKS -ne 0 ]]; then
    echo "Canonical QA tamamlanamadı: zorunlu bütünlük kontrolü atlandı."
    return 2
  fi
  echo "Canonical QA zorunlu kontrolleri geçti; web tile bağlantısı test edilmedi."
}

case "$MODE" in
  --check)
    run_check
    ;;
  -h|--help)
    usage
    ;;
  *)
    usage
    echo "Bilinmeyen mod: $MODE" >&2
    exit 1
    ;;
esac
