#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Çanakkale Afet Öncelik Analizi
# MCDA Sensitivity / Robustness Tablo Generator
# ============================================================
#
# Amaç:
#   config/mcda_weights.tsv içindeki baseline, earthquake-heavy ve equal-weight
#   senaryoları için küçük robustness tabloları üretir.
#
# Güvenlik:
#   Varsayılan mod --check'tir. Yalnızca geçici dizine yazar ve proje
#   verisine dokunmaz. Tabloları outputs/tables altına yazmak için --generate
#   kullanılır. Kalıcı senaryo rasterı üretmez.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/project_env.sh"

MODE="${1:---check}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PYTHON_SCRIPT="scripts/python/generate_sensitivity_tables.py"
OUTPUT_DIR="outputs/tables"
TEMP_DIR=""

GDALINFO="${GDALINFO:-}"
GDAL_TRANSLATE="${GDAL_TRANSLATE:-}"
GDAL_RASTERIZE="${GDAL_RASTERIZE:-}"
OGRINFO="${OGRINFO:-}"
OGR2OGR="${OGR2OGR:-}"

usage() {
  cat <<'EOF'
Kullanım:
  scripts/bash/generate_sensitivity_tables.sh --check
  scripts/bash/generate_sensitivity_tables.sh --generate

Modlar:
  --check      Sensitivity tablolarını geçici dizinde build eder ve QA çalıştırır.
  --generate   Sensitivity tablolarını outputs/tables altına yazar.

Araç bulma:
  GDAL/OGR araçları PATH, GDAL_BIN, QGIS_BIN veya açık araç değişkenleri
  üzerinden çözülür: GDALINFO, GDAL_TRANSLATE, GDAL_RASTERIZE, OGRINFO, OGR2OGR.

Python gereksinimleri:
  numpy bulunan Python 3.
EOF
}

cleanup() {
  if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
    rm -rf "$TEMP_DIR"
  fi
}
trap cleanup EXIT

resolve_python() {
  if [[ "$PYTHON_BIN" == */* ]]; then
    [[ -x "$PYTHON_BIN" ]] || die "Ayarlanmış PYTHON_BIN executable değil: $PYTHON_BIN"
    printf '%s\n' "$PYTHON_BIN"
    return 0
  fi

  local candidate
  candidate="$(command -v "$PYTHON_BIN" || true)"
  [[ -n "$candidate" ]] || die "Gerekli Python executable eksik: $PYTHON_BIN"
  printf '%s\n' "$candidate"
}

prepare_runtime() {
  project_cd_root

  GDALINFO="$(resolve_tool GDALINFO gdalinfo)"
  GDAL_TRANSLATE="$(resolve_tool GDAL_TRANSLATE gdal_translate)"
  GDAL_RASTERIZE="$(resolve_tool GDAL_RASTERIZE gdal_rasterize)"
  OGRINFO="$(resolve_tool OGRINFO ogrinfo)"
  OGR2OGR="$(resolve_tool OGR2OGR ogr2ogr)"

  PYTHON_BIN="$(resolve_python)"

  require_tool "$GDALINFO"
  require_tool "$GDAL_TRANSLATE"
  require_tool "$GDAL_RASTERIZE"
  require_tool "$OGRINFO"
  require_tool "$OGR2OGR"
  require_tool "$PYTHON_BIN"
  require_file "$PYTHON_SCRIPT"

  "$PYTHON_BIN" - <<'PY'
import numpy  # noqa: F401
PY

  export GDALINFO
  export GDAL_TRANSLATE
  export GDAL_RASTERIZE
  export OGRINFO
  export OGR2OGR
}

run_generator() {
  local output_dir="$1"

  "$PYTHON_BIN" "$PYTHON_SCRIPT" \
    --project-root "$PROJECT_DIR" \
    --output-dir "$output_dir"
}

run_check() {
  prepare_runtime

  TEMP_DIR="$(mktemp -d)"
  echo "MCDA sensitivity tablo generator"
  echo "Proje kökü: script konumundan çözüldü"
  echo "Mod: --check"
  echo "Çıktı: geçici QA dizini"

  run_generator "$TEMP_DIR/sensitivity_tables"

  echo ""
  echo "MCDA sensitivity tablo QA kontrolü geçti."
}

run_generate() {
  prepare_runtime

  echo "MCDA sensitivity tablo generator"
  echo "Proje kökü: script konumundan çözüldü"
  echo "Mod: --generate"
  echo "Çıktı: $OUTPUT_DIR"

  mkdir -p "$OUTPUT_DIR"
  run_generator "$OUTPUT_DIR"

  echo ""
  echo "MCDA sensitivity tabloları yazıldı."
}

case "$MODE" in
  --check)
    run_check
    ;;
  --generate)
    run_generate
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
