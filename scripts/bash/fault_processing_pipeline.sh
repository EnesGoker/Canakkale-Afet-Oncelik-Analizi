#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Çanakkale Afet Öncelik Analizi
# Canonical Fault Proximity Validation Script
# ============================================================
#
# Amaç:
#   Raw MTA shapefile gerektirmeden kabul edilmiş canonical fault vector
#   katmanını ve türetilmiş fault proximity score rasterını doğrular.
#
# Canonical input politikası:
#   Bu script data/processed/faults ve data/processed/analysis kullanır.
#   Eski raw pathleri okumaz ve proje çıktılarını rebuild etmez.
#
# Güvenlik:
#   Varsayılan ve tek operasyonel mod --check'tir. Script, score formülünü
#   doğrulamak için sistem temp dizini altında geçici rasterlar oluşturur;
#   proje verisi read-only kalır.
#
# Kaynak seceresi:
#   Fault kaynağı MTA Türkiye Diri Fay Haritası veri paketi olarak dokümante edilir. Raw shapefile
#   upstream kaynaktır; canonical pipeline inputu değildir.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/project_env.sh"

GDALINFO="${GDALINFO:-}"
GDAL_CALC="${GDAL_CALC:-}"
GDAL_RASTERIZE="${GDAL_RASTERIZE:-}"
GDAL_PROXIMITY="${GDAL_PROXIMITY:-}"
OGRINFO="${OGRINFO:-}"

ANALYSIS_DIR="data/processed/analysis"
FAULT_DIR="data/processed/faults"

TEMPLATE="$ANALYSIS_DIR/analysis_template_100m_32635.tif"
FAULT_VECTOR="$FAULT_DIR/canakkale_faults_final_32635.gpkg"
FAULT_LAYER="canakkale_faults_final_32635"
FAULT_SCORE="$ANALYSIS_DIR/fault_proximity_score_32635.tif"

EXPECTED_SIZE="Size is 1586, 1423"
EXPECTED_CRS='PROJCRS["WGS 84 / UTM zone 35N"'
EXPECTED_ORIGIN="Origin = (386392.705599999986589,4509726.272499999962747)"
EXPECTED_PIXEL_SIZE="Pixel Size = (100.000000000000000,-100.000000000000000)"
EXPECTED_LOWER_RIGHT="Lower Right (  544992.706, 4367426.272)"
EXPECTED_EXTENT_ARGS=(386392.7056 4367426.2725 544992.7056 4509726.2725)

FAULT_DECAY_DISTANCE_M="10000"
FORMULA_TOLERANCE="0.0001"
TEMP_DIR=""
MODE="${1:---check}"

configure_tools() {
  GDALINFO="$(resolve_tool GDALINFO gdalinfo)"
  GDAL_CALC="$(resolve_tool GDAL_CALC gdal_calc.py)"
  GDAL_RASTERIZE="$(resolve_tool GDAL_RASTERIZE gdal_rasterize)"
  GDAL_PROXIMITY="$(resolve_tool GDAL_PROXIMITY gdal_proximity.py)"
  OGRINFO="$(resolve_tool OGRINFO ogrinfo)"
}

usage() {
  cat <<'EOF'
Kullanım:
  scripts/bash/fault_processing_pipeline.sh --check

Mod:
  --check   Canonical fault vector ve fault proximity score katmanını doğrular.

Notlar:
  Bu script raw MTA shapefile gerektirmez.
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

ogr_sql_value() {
  local key="$1"
  local sql="$2"
  local value

  value="$(
    run_geo "$OGRINFO" -ro -q -sql "$sql" "$FAULT_VECTOR" |
      awk -v key="$key" '$1 == key {print $4; exit}'
  )"

  if [[ -z "$value" ]]; then
    echo "$FAULT_VECTOR içinden $key okunamadı" >&2
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

print_vector_summary() {
  local sql feature_count total_length min_length max_length

  sql="SELECT COUNT(*) AS feature_count, SUM(ST_Length(geom)) AS total_length_m, MIN(ST_Length(geom)) AS min_length_m, MAX(ST_Length(geom)) AS max_length_m FROM ${FAULT_LAYER}"
  feature_count="$(ogr_sql_value "feature_count" "$sql")"
  total_length="$(ogr_sql_value "total_length_m" "$sql")"
  min_length="$(ogr_sql_value "min_length_m" "$sql")"
  max_length="$(ogr_sql_value "max_length_m" "$sql")"

  echo ""
  echo "Vektör özeti: $FAULT_VECTOR"
  echo "Layer: $FAULT_LAYER"
  echo "Feature sayısı: $feature_count"
  echo "Toplam uzunluk (m): $total_length"
  echo "Minimum obje uzunluğu (m): $min_length"
  echo "Maximum obje uzunluğu (m): $max_length"
}

validate_required_inputs() {
  configure_tools
  require_tool "$GDALINFO"
  require_tool "$GDAL_CALC"
  require_tool "$GDAL_RASTERIZE"
  require_tool "$GDAL_PROXIMITY"
  require_tool "$OGRINFO"

  project_cd_root

  require_file "$TEMPLATE"
  require_file "$FAULT_VECTOR"
  require_file "$FAULT_SCORE"

  check_grid "$TEMPLATE" "0"
  check_grid "$FAULT_SCORE" "-9999"
}

validate_fault_vector() {
  local info feature_count min_length total_length
  local sql

  info="$(run_geo "$OGRINFO" -ro -so -al "$FAULT_VECTOR")"

  require_info_pattern "$info" "Layer name: $FAULT_LAYER" "Fault layer adı uyuşmuyor" "$FAULT_VECTOR"
  require_info_pattern "$info" "Geometry: Multi Line String" "Fault geometry type uyuşmuyor" "$FAULT_VECTOR"
  require_info_pattern "$info" 'ID["EPSG",32635]' "Fault vector CRS uyuşmuyor; beklenen EPSG:32635" "$FAULT_VECTOR"
  require_info_pattern "$info" "length_m: Real" "Fault vector length_m alanını içermiyor" "$FAULT_VECTOR"

  feature_count="$(awk '/Feature Count:/ {print $3; exit}' <<<"$info")"
  assert_float_gte "$feature_count" "1" "Fault vector en az bir feature içermeli"

  sql="SELECT COUNT(*) AS feature_count, SUM(ST_Length(geom)) AS total_length_m, MIN(ST_Length(geom)) AS min_length_m FROM ${FAULT_LAYER}"
  total_length="$(ogr_sql_value "total_length_m" "$sql")"
  min_length="$(ogr_sql_value "min_length_m" "$sql")"

  assert_float_gte "$total_length" "1000" "Fault toplam uzunluğu beklenmedik şekilde düşük"
  assert_float_gte "$min_length" "10" "Fault vector 10 m altında clipped sliver geometri içeriyor"
}

validate_fault_score_stats() {
  local score_min score_max score_valid

  score_min="$(metadata_stat "$FAULT_SCORE" "STATISTICS_MINIMUM")"
  score_max="$(metadata_stat "$FAULT_SCORE" "STATISTICS_MAXIMUM")"
  score_valid="$(metadata_stat "$FAULT_SCORE" "STATISTICS_VALID_PERCENT")"

  assert_float_gte "$score_min" "0" "Fault proximity score minimum >= 0 olmalı"
  assert_float_lte "$score_max" "1.000001" "Fault proximity score maximum <= 1 olmalı"
  assert_float_between "$score_valid" "43" "44" "Fault proximity score valid AOI yüzdesi beklenmedik şekilde değişti"
}

validate_score_formula() {
  local binary_raster distance_raster diff_raster diff_max

  TEMP_DIR="$(mktemp -d)"
  binary_raster="$TEMP_DIR/fault_binary_100m_32635.tif"
  distance_raster="$TEMP_DIR/fault_distance_100m_32635.tif"
  diff_raster="$TEMP_DIR/fault_score_diff.tif"

  run_geo "$GDAL_RASTERIZE" \
    -burn 1 \
    -tr 100 100 \
    -te "${EXPECTED_EXTENT_ARGS[@]}" \
    -a_nodata 0 \
    -ot Byte \
    -of GTiff \
    -l "$FAULT_LAYER" \
    "$FAULT_VECTOR" \
    "$binary_raster" >/dev/null

  run_geo "$GDAL_PROXIMITY" \
    "$binary_raster" \
    "$distance_raster" \
    -values 1 \
    -distunits GEO \
    -ot Float32 \
    -nodata -9999 >/dev/null

  run_geo "$GDAL_CALC" \
    -A "$distance_raster" \
    -B "$FAULT_SCORE" \
    -M "$TEMPLATE" \
    --outfile="$diff_raster" \
    --calc="where(M==1, abs(B - maximum(1 - minimum(A/${FAULT_DECAY_DISTANCE_M},1),0)), -9999)" \
    --type=Float32 \
    --NoDataValue=-9999 \
    --hideNoData \
    --quiet \
    --overwrite

  diff_max="$(metadata_stat "$diff_raster" "STATISTICS_MAXIMUM")"
  assert_float_lte "$diff_max" "$FORMULA_TOLERANCE" \
    "Fault proximity score canonical vector-derived proximity formülüyle eşleşmiyor"

  echo ""
  echo "Formül kontrolü: fault proximity score maksimum mutlak fark = $diff_max"
}

run_check() {
  validate_required_inputs
  validate_fault_vector
  validate_fault_score_stats
  validate_score_formula

  echo ""
  echo "Canonical fault proximity validation geçti."
  echo "Proje kökü: script konumundan çözüldü"
  echo "Mod: --check"
  echo "Kaynak seviyesi: processed-canonical"
  echo "Upstream kaynak: MTA Türkiye Diri Fay Haritası veri paketi"

  print_vector_summary
  print_raster_stats "$FAULT_SCORE"
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
