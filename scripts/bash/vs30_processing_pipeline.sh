#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Çanakkale Afet Öncelik Analizi
# Canonical VS30 / Site Condition Validation Script
# ============================================================
#
# Amaç:
#   Büyük raw USGS VS30 extract dosyasını gerektirmeden kabul edilmiş canonical
#   VS30 AOI rasterını ve türetilmiş site condition score katmanını doğrular.
#
# Canonical input politikası:
#   Bu script data/processed/vs30 ve data/processed/analysis kullanır.
#   Eski raw pathleri okumaz ve proje çıktılarını rebuild etmez.
#
# Güvenlik:
#   Varsayılan ve tek operasyonel mod --check'tir. Script sistem temp dizini
#   altında geçici dosyalar oluşturabilir; proje verisi read-only kalır.
#
# Kaynak seceresi:
#   VS30 kaynağı USGS Global VS30 Mosaic olarak dokümante edilir. Raw extract
#   upstream kaynaktır; canonical pipeline inputu değildir.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/project_env.sh"

GDALINFO="${GDALINFO:-}"
GDAL_CALC="${GDAL_CALC:-}"

ANALYSIS_DIR="data/processed/analysis"
VS30_DIR="data/processed/vs30"

TEMPLATE="$ANALYSIS_DIR/analysis_template_100m_32635.tif"
VS30_AOI="$VS30_DIR/vs30_aoi_100m_32635.tif"
SITE_SCORE="$ANALYSIS_DIR/site_condition_score_32635.tif"

EXPECTED_SIZE="Size is 1586, 1423"
EXPECTED_CRS='PROJCRS["WGS 84 / UTM zone 35N"'
EXPECTED_ORIGIN="Origin = (386392.705599999986589,4509726.272499999962747)"
EXPECTED_PIXEL_SIZE="Pixel Size = (100.000000000000000,-100.000000000000000)"
EXPECTED_LOWER_RIGHT="Lower Right (  544992.706, 4367426.272)"

VS30_MIN_REFERENCE="180.042"
VS30_MAX_REFERENCE="900.000"
FORMULA_TOLERANCE="0.0001"
TEMP_DIR=""
MODE="${1:---check}"

configure_tools() {
  GDALINFO="$(resolve_tool GDALINFO gdalinfo)"
  GDAL_CALC="$(resolve_tool GDAL_CALC gdal_calc.py)"
}

usage() {
  cat <<'EOF'
Kullanım:
  scripts/bash/vs30_processing_pipeline.sh --check

Mod:
  --check   Canonical VS30 AOI rasterını ve site condition score katmanını doğrular.

Notlar:
  Bu script raw USGS VS30 extract dosyasını gerektirmez.
  Proje çıktılarını overwrite veya rebuild etmez.
EOF
}

cleanup() {
  if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
    rm -rf "$TEMP_DIR"
  fi
}
trap cleanup EXIT

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "Gerekli dosya eksik: $path" >&2
    exit 1
  fi
}

require_tool() {
  local path="$1"
  if [[ ! -x "$path" ]]; then
    echo "Gerekli executable eksik: $path" >&2
    exit 1
  fi
}

require_info_pattern() {
  local info="$1"
  local pattern="$2"
  local message="$3"
  local path="$4"

  grep -Fq "$pattern" <<<"$info" || {
    echo "$message: $path" >&2
    exit 1
  }
}

check_grid() {
  local path="$1"
  local expected_nodata="$2"
  local info

  info="$(run_geo "$GDALINFO" "$path")"

  require_info_pattern "$info" "$EXPECTED_SIZE" "Grid boyutu uyuşmuyor" "$path"
  require_info_pattern "$info" "$EXPECTED_CRS" "CRS uyuşmuyor; beklenen EPSG:32635 / WGS 84 UTM zone 35N" "$path"
  require_info_pattern "$info" "$EXPECTED_ORIGIN" "Grid origin uyuşmuyor" "$path"
  require_info_pattern "$info" "$EXPECTED_PIXEL_SIZE" "Pixel size uyuşmuyor" "$path"
  require_info_pattern "$info" "$EXPECTED_LOWER_RIGHT" "Grid extent uyuşmuyor" "$path"
  require_info_pattern "$info" "NoData Value=$expected_nodata" "NoData uyuşmuyor" "$path"
}

metadata_stat() {
  local path="$1"
  local key="$2"
  local value

  value="$(
    run_geo "$GDALINFO" -json -stats "$path" |
      awk -F'"' -v key="$key" '$2 == key {print $4; exit}'
  )"

  if [[ -z "$value" ]]; then
    echo "$path içinden $key okunamadı" >&2
    exit 1
  fi

  printf '%s\n' "$value"
}

assert_float_lte() {
  local value="$1"
  local limit="$2"
  local message="$3"

  awk -v value="$value" -v limit="$limit" 'BEGIN { exit !(value <= limit) }' || {
    echo "$message: değer=$value limit=$limit" >&2
    exit 1
  }
}

assert_float_gte() {
  local value="$1"
  local limit="$2"
  local message="$3"

  awk -v value="$value" -v limit="$limit" 'BEGIN { exit !(value >= limit) }' || {
    echo "$message: değer=$value limit=$limit" >&2
    exit 1
  }
}

assert_float_between() {
  local value="$1"
  local min_value="$2"
  local max_value="$3"
  local message="$4"

  awk -v value="$value" -v min_value="$min_value" -v max_value="$max_value" \
    'BEGIN { exit !(value >= min_value && value <= max_value) }' || {
    echo "$message: değer=$value beklenen=[$min_value,$max_value]" >&2
    exit 1
  }
}

print_raster_stats() {
  local path="$1"

  echo ""
  echo "İstatistikler: $path"
  run_geo "$GDALINFO" -stats "$path" |
    grep -E "Size is|Pixel Size|Upper Left|Lower Right|NoData|Minimum|Maximum|Mean|StdDev|STATISTICS_VALID_PERCENT"
}

validate_required_inputs() {
  configure_tools
  require_tool "$GDALINFO"
  require_tool "$GDAL_CALC"

  project_cd_root

  require_file "$TEMPLATE"
  require_file "$VS30_AOI"
  require_file "$SITE_SCORE"

  check_grid "$TEMPLATE" "0"
  check_grid "$VS30_AOI" "-9999"
  check_grid "$SITE_SCORE" "-9999"
}

validate_vs30_stats() {
  local vs30_min vs30_max vs30_valid
  local score_min score_max score_valid

  vs30_min="$(metadata_stat "$VS30_AOI" "STATISTICS_MINIMUM")"
  vs30_max="$(metadata_stat "$VS30_AOI" "STATISTICS_MAXIMUM")"
  vs30_valid="$(metadata_stat "$VS30_AOI" "STATISTICS_VALID_PERCENT")"

  score_min="$(metadata_stat "$SITE_SCORE" "STATISTICS_MINIMUM")"
  score_max="$(metadata_stat "$SITE_SCORE" "STATISTICS_MAXIMUM")"
  score_valid="$(metadata_stat "$SITE_SCORE" "STATISTICS_VALID_PERCENT")"

  assert_float_gte "$vs30_min" "180" "VS30 minimum beklenen canonical aralığın dışında"
  assert_float_lte "$vs30_max" "900.001" "VS30 maximum beklenen canonical aralığın dışında"
  assert_float_between "$vs30_valid" "43" "44" "VS30 valid AOI yüzdesi beklenmedik şekilde değişti"

  assert_float_gte "$score_min" "0" "Site condition score minimum >= 0 olmalı"
  assert_float_lte "$score_max" "1.000001" "Site condition score maximum <= 1 olmalı"
  assert_float_between "$score_valid" "43" "44" "Site condition score valid AOI yüzdesi beklenmedik şekilde değişti"
}

validate_score_formula() {
  local diff_raster diff_max

  TEMP_DIR="$(mktemp -d)"
  diff_raster="$TEMP_DIR/site_condition_score_diff.tif"

  run_geo "$GDAL_CALC" \
    -A "$VS30_AOI" \
    -B "$SITE_SCORE" \
    -M "$TEMPLATE" \
    --outfile="$diff_raster" \
    --calc="where(M==1, abs(B - maximum(minimum((${VS30_MAX_REFERENCE}-A)/(${VS30_MAX_REFERENCE}-${VS30_MIN_REFERENCE}),1),0)), -9999)" \
    --type=Float32 \
    --NoDataValue=-9999 \
    --hideNoData \
    --quiet \
    --overwrite

  diff_max="$(metadata_stat "$diff_raster" "STATISTICS_MAXIMUM")"
  assert_float_lte "$diff_max" "$FORMULA_TOLERANCE" \
    "Site condition score canonical inverse VS30 formülüyle eşleşmiyor"

  echo ""
  echo "Formül kontrolü: site condition score maksimum mutlak fark = $diff_max"
}

run_check() {
  validate_required_inputs
  validate_vs30_stats
  validate_score_formula

  echo ""
  echo "Canonical VS30 / site condition validation geçti."
  echo "Proje kökü: script konumundan çözüldü"
  echo "Mod: --check"
  echo "Kaynak seviyesi: processed-canonical"
  echo "Upstream kaynak: USGS Global VS30 Mosaic"

  print_raster_stats "$VS30_AOI"
  print_raster_stats "$SITE_SCORE"
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
