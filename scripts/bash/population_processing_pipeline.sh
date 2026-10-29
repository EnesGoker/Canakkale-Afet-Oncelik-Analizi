#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Çanakkale Afet Öncelik Analizi
# Canonical Population Validation Script
# ============================================================
#
# Amaç:
#   Büyük raw WorldPop rasterını gerektirmeden kabul edilmiş canonical
#   population exposure katmanlarını doğrular.
#
# Canonical input politikası:
#   Bu script data/processed/population ve data/processed/analysis kullanır.
#   Eski raw pathleri okumaz ve proje çıktılarını rebuild etmez.
#
# Güvenlik:
#   Varsayılan ve tek operasyonel mod --check'tir. Script sistem temp dizini
#   altında geçici dosyalar oluşturabilir; proje verisi read-only kalır.
#
# Kaynak seceresi:
#   Population kaynağı WorldPop Turkey 2020 constrained, UN-adjusted population
#   olarak dokümante edilir. Raw raster upstream kaynaktır; bu proje
#   klasörü içinde canonical pipeline inputu değildir.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/project_env.sh"

GDALINFO="${GDALINFO:-}"
GDAL_CALC="${GDAL_CALC:-}"

ANALYSIS_DIR="data/processed/analysis"
POPULATION_DIR="data/processed/population"

TEMPLATE="$ANALYSIS_DIR/analysis_template_100m_32635.tif"
POP_COUNT="$POPULATION_DIR/population_count_aoi_100m_32635.tif"
POP_SCORE="$ANALYSIS_DIR/population_exposure_score_32635.tif"

EXPECTED_SIZE="Size is 1586, 1423"
EXPECTED_CRS='PROJCRS["WGS 84 / UTM zone 35N"'
EXPECTED_ORIGIN="Origin = (386392.705599999986589,4509726.272499999962747)"
EXPECTED_PIXEL_SIZE="Pixel Size = (100.000000000000000,-100.000000000000000)"
EXPECTED_LOWER_RIGHT="Lower Right (  544992.706, 4367426.272)"

POPULATION_MAX_REFERENCE="159.301"
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
  scripts/bash/population_processing_pipeline.sh --check

Mod:
  --check   Canonical population count ve population exposure score katmanlarını doğrular.

Notlar:
  Bu script raw WorldPop rasterı gerektirmez.
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
  require_file "$POP_COUNT"
  require_file "$POP_SCORE"

  check_grid "$TEMPLATE" "0"
  check_grid "$POP_COUNT" "-9999"
  check_grid "$POP_SCORE" "-9999"
}

validate_population_stats() {
  local count_min count_max count_valid
  local score_min score_max score_valid

  count_min="$(metadata_stat "$POP_COUNT" "STATISTICS_MINIMUM")"
  count_max="$(metadata_stat "$POP_COUNT" "STATISTICS_MAXIMUM")"
  count_valid="$(metadata_stat "$POP_COUNT" "STATISTICS_VALID_PERCENT")"

  score_min="$(metadata_stat "$POP_SCORE" "STATISTICS_MINIMUM")"
  score_max="$(metadata_stat "$POP_SCORE" "STATISTICS_MAXIMUM")"
  score_valid="$(metadata_stat "$POP_SCORE" "STATISTICS_VALID_PERCENT")"

  assert_float_gte "$count_min" "0" "Population count minimum AOI içinde negatif olmamalı"
  assert_float_lte "$count_max" "160" "Population count maximum beklenen canonical aralığın dışında"
  assert_float_between "$count_valid" "43" "44" "Population count valid AOI yüzdesi beklenmedik şekilde değişti"

  assert_float_gte "$score_min" "0" "Population score minimum >= 0 olmalı"
  assert_float_lte "$score_max" "1.000001" "Population score maximum <= 1 olmalı"
  assert_float_between "$score_valid" "43" "44" "Population score valid AOI yüzdesi beklenmedik şekilde değişti"
}

validate_score_formula() {
  local diff_raster diff_max

  TEMP_DIR="$(mktemp -d)"
  diff_raster="$TEMP_DIR/population_score_diff.tif"

  run_geo "$GDAL_CALC" \
    -A "$POP_COUNT" \
    -B "$POP_SCORE" \
    -M "$TEMPLATE" \
    --outfile="$diff_raster" \
    --calc="where(M==1, abs(B - (log1p(maximum(A,0))/log1p(${POPULATION_MAX_REFERENCE}))), -9999)" \
    --type=Float32 \
    --NoDataValue=-9999 \
    --hideNoData \
    --quiet \
    --overwrite

  diff_max="$(metadata_stat "$diff_raster" "STATISTICS_MAXIMUM")"
  assert_float_lte "$diff_max" "$FORMULA_TOLERANCE" \
    "Population exposure score canonical log-normalization formülüyle eşleşmiyor"

  echo ""
  echo "Formül kontrolü: population score maksimum mutlak fark = $diff_max"
}

run_check() {
  validate_required_inputs
  validate_population_stats
  validate_score_formula

  echo ""
  echo "Canonical population validation geçti."
  echo "Proje kökü: script konumundan çözüldü"
  echo "Mod: --check"
  echo "Kaynak seviyesi: processed-canonical"
  echo "Upstream kaynak: WorldPop Turkey 2020 constrained UN-adjusted population"

  print_raster_stats "$POP_COUNT"
  print_raster_stats "$POP_SCORE"
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
