#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Çanakkale Afet Öncelik Analizi
# Canonical 11 kriterli MCDA üretim scripti
# ============================================================
#
# Amaç:
#   11 kriterli MCDA priority score, normalized score ve
#   classified priority raster çıktılarını canonical processed kriter
#   rasterlarından rebuild eder.
#
# Canonical input politikası:
#   Bu script büyük raw source datasetleri gerektirmez. data/processed/analysis
#   içindeki kabul edilmiş canonical inputları kullanır.
#
# Güvenlik:
#   Varsayılan mod --check'tir. MCDA çıktılarını overwrite etmek için
#   --execute kullanılır. Mevcut çıktılar değiştirilmeden önce arşivlenir.
#
# Proje CRS:
#   EPSG:32635 - WGS 84 / UTM zone 35N
#
# Ortak analiz gridi:
#   Resolution: 100 m
#   Width: 1586
#   Height: 1423
#   Extent:
#     xmin: 386392.7056
#     ymin: 4367426.2725
#     xmax: 544992.7056
#     ymax: 4509726.2725
#
# Sürekli raster NoData: -9999
# Class raster AOI dışı / NoData: 0
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/project_env.sh"

GDAL_CALC="${GDAL_CALC:-}"
GDALINFO="${GDALINFO:-}"

ANALYSIS_DIR="data/processed/analysis"
TEMPLATE="$ANALYSIS_DIR/analysis_template_100m_32635.tif"
WEIGHT_CONFIG="config/mcda_weights.tsv"
WEIGHT_SCENARIO="baseline"

EXPECTED_SIZE="Size is 1586, 1423"
EXPECTED_CRS='PROJCRS["WGS 84 / UTM zone 35N"'
EXPECTED_ORIGIN="Origin = (386392.705599999986589,4509726.272499999962747)"
EXPECTED_PIXEL_SIZE="Pixel Size = (100.000000000000000,-100.000000000000000)"
EXPECTED_LOWER_RIGHT="Lower Right (  544992.706, 4367426.272)"

# 11 kriterli score rasterları.
EARTHQUAKE_SCORE="$ANALYSIS_DIR/earthquake_pga_score_32635.tif"
FAULT_SCORE="$ANALYSIS_DIR/fault_proximity_score_32635.tif"
SITE_SCORE="$ANALYSIS_DIR/site_condition_score_32635.tif"
POPULATION_SCORE="$ANALYSIS_DIR/population_exposure_score_32635.tif"
BUILDING_SCORE="$ANALYSIS_DIR/building_exposure_density_score_32635.tif"
FLOOD_SCORE="$ANALYSIS_DIR/flood_score_32635.tif"
HYDROGRAPHY_SCORE="$ANALYSIS_DIR/hydrography_proximity_score_32635.tif"
SLOPE_SCORE="$ANALYSIS_DIR/slope_score_32635.tif"
LANDCOVER_SCORE="$ANALYSIS_DIR/landcover_sensitivity_score_32635.tif"
TREE_COVER_SCORE="$ANALYSIS_DIR/tree_cover_score_32635.tif"
ROAD_DIFFICULTY_SCORE="$ANALYSIS_DIR/road_accessibility_difficulty_score_32635.tif"

# Nihai MCDA çıktıları.
MCDA_RAW="$ANALYSIS_DIR/mcda_priority_score_32635.tif"
MCDA_NORMALIZED="$ANALYSIS_DIR/mcda_priority_score_normalized_32635.tif"
MCDA_CLASS="$ANALYSIS_DIR/mcda_priority_class_32635.tif"

# Yuvarlanmış normalization sabitleri şu dosyada dokümante edilmiştir:
# docs/methodology/updated_mcda_methodology_note.md.
MCDA_MIN_RAW="0.029"
MCDA_RANGE="0.473"
MCDA_CALC=""

W_EARTHQUAKE_PGA=""
W_FAULT_PROXIMITY=""
W_SITE_CONDITION=""
W_POPULATION_EXPOSURE=""
W_BUILDING_EXPOSURE=""
W_FLOOD=""
W_HYDROGRAPHY=""
W_SLOPE=""
W_LANDCOVER=""
W_TREE_COVER=""
W_ROAD_DIFFICULTY=""

MODE="${1:---check}"

configure_tools() {
  GDAL_CALC="$(resolve_tool GDAL_CALC gdal_calc.py)"
  GDALINFO="$(resolve_tool GDALINFO gdalinfo)"
}

usage() {
  cat <<'EOF'
Kullanım:
  scripts/bash/mcda_pipeline_commands.sh --check
  scripts/bash/mcda_pipeline_commands.sh --execute

Modlar:
  --check     Canonical MCDA girdilerini doğrular ve mevcut çıktı istatistiklerini yazar.
  --execute   Mevcut MCDA çıktılarını arşivler; ardından raw, normalized ve
              classified MCDA rasterlarını 11 kriterden rebuild eder.

Ağırlık kaynağı:
  config/mcda_weights.tsv içindeki baseline senaryosu canonical MCDA için tek
  ağırlık kaynağıdır. Diğer senaryolar yalnızca robustness/sensitivity çıktıları
  için kullanılacaktır.
EOF
}

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
  local info
  info="$(run_geo "$GDALINFO" "$path")"

  require_info_pattern "$info" "$EXPECTED_SIZE" "Grid boyutu uyuşmuyor" "$path"
  require_info_pattern "$info" "$EXPECTED_CRS" "CRS uyuşmuyor; beklenen EPSG:32635 / WGS 84 UTM zone 35N" "$path"
  require_info_pattern "$info" "$EXPECTED_ORIGIN" "Grid origin uyuşmuyor" "$path"
  require_info_pattern "$info" "$EXPECTED_PIXEL_SIZE" "Pixel size uyuşmuyor" "$path"
  require_info_pattern "$info" "$EXPECTED_LOWER_RIGHT" "Grid extent uyuşmuyor" "$path"
}

assert_weight_number() {
  local weight="$1"
  local criterion_id="$2"
  awk -v weight="$weight" 'BEGIN {
    ok = (weight ~ /^(0(\.[0-9]+)?|1(\.0+)?)$/)
    exit(ok ? 0 : 1)
  }' || {
    echo "Geçersiz MCDA ağırlığı: $criterion_id -> $weight" >&2
    exit 1
  }
}

assign_weight() {
  local criterion_id="$1"
  local weight="$2"

  assert_weight_number "$weight" "$criterion_id"

  case "$criterion_id" in
    earthquake_pga_score)
      [[ -z "$W_EARTHQUAKE_PGA" ]] || { echo "Tekrarlı kriter ağırlığı: $criterion_id" >&2; exit 1; }
      W_EARTHQUAKE_PGA="$weight"
      ;;
    fault_proximity_score)
      [[ -z "$W_FAULT_PROXIMITY" ]] || { echo "Tekrarlı kriter ağırlığı: $criterion_id" >&2; exit 1; }
      W_FAULT_PROXIMITY="$weight"
      ;;
    site_condition_score)
      [[ -z "$W_SITE_CONDITION" ]] || { echo "Tekrarlı kriter ağırlığı: $criterion_id" >&2; exit 1; }
      W_SITE_CONDITION="$weight"
      ;;
    population_exposure_score)
      [[ -z "$W_POPULATION_EXPOSURE" ]] || { echo "Tekrarlı kriter ağırlığı: $criterion_id" >&2; exit 1; }
      W_POPULATION_EXPOSURE="$weight"
      ;;
    building_exposure_density_score)
      [[ -z "$W_BUILDING_EXPOSURE" ]] || { echo "Tekrarlı kriter ağırlığı: $criterion_id" >&2; exit 1; }
      W_BUILDING_EXPOSURE="$weight"
      ;;
    flood_score)
      [[ -z "$W_FLOOD" ]] || { echo "Tekrarlı kriter ağırlığı: $criterion_id" >&2; exit 1; }
      W_FLOOD="$weight"
      ;;
    hydrography_proximity_score)
      [[ -z "$W_HYDROGRAPHY" ]] || { echo "Tekrarlı kriter ağırlığı: $criterion_id" >&2; exit 1; }
      W_HYDROGRAPHY="$weight"
      ;;
    slope_score)
      [[ -z "$W_SLOPE" ]] || { echo "Tekrarlı kriter ağırlığı: $criterion_id" >&2; exit 1; }
      W_SLOPE="$weight"
      ;;
    landcover_sensitivity_score)
      [[ -z "$W_LANDCOVER" ]] || { echo "Tekrarlı kriter ağırlığı: $criterion_id" >&2; exit 1; }
      W_LANDCOVER="$weight"
      ;;
    tree_cover_score)
      [[ -z "$W_TREE_COVER" ]] || { echo "Tekrarlı kriter ağırlığı: $criterion_id" >&2; exit 1; }
      W_TREE_COVER="$weight"
      ;;
    road_accessibility_difficulty_score)
      [[ -z "$W_ROAD_DIFFICULTY" ]] || { echo "Tekrarlı kriter ağırlığı: $criterion_id" >&2; exit 1; }
      W_ROAD_DIFFICULTY="$weight"
      ;;
    *)
      echo "Bilinmeyen MCDA kriter id değeri: $criterion_id" >&2
      exit 1
      ;;
  esac
}

load_weight_config() {
  require_file "$WEIGHT_CONFIG"

  local line_number=0
  local count=0
  local sum="0"
  local scenario_id scenario_label scenario_role criterion_order criterion_id display_name raster_path weight block note

  while IFS=$'\t' read -r scenario_id scenario_label scenario_role criterion_order criterion_id display_name raster_path weight block note || [[ -n "${scenario_id:-}" ]]; do
    line_number=$((line_number + 1))

    if [[ $line_number -eq 1 ]]; then
      [[ "$scenario_id" == "scenario_id" ]] || {
        echo "MCDA ağırlık config header beklenen formatta değil: $WEIGHT_CONFIG" >&2
        exit 1
      }
      continue
    fi

    [[ -n "${scenario_id:-}" ]] || continue
    [[ "$scenario_id" == "$WEIGHT_SCENARIO" ]] || continue

    [[ -n "${criterion_id:-}" && -n "${weight:-}" ]] || {
      echo "Eksik MCDA ağırlık satırı: $WEIGHT_CONFIG:$line_number" >&2
      exit 1
    }

    assign_weight "$criterion_id" "$weight"
    count=$((count + 1))
    sum="$(awk -v current="$sum" -v add="$weight" 'BEGIN { printf "%.12f", current + add }')"
  done <"$WEIGHT_CONFIG"

  [[ $count -eq 11 ]] || {
    echo "Baseline MCDA için beklenen 11 ağırlık, gelen $count: $WEIGHT_CONFIG" >&2
    exit 1
  }

  for value in \
    "$W_EARTHQUAKE_PGA" \
    "$W_FAULT_PROXIMITY" \
    "$W_SITE_CONDITION" \
    "$W_POPULATION_EXPOSURE" \
    "$W_BUILDING_EXPOSURE" \
    "$W_FLOOD" \
    "$W_HYDROGRAPHY" \
    "$W_SLOPE" \
    "$W_LANDCOVER" \
    "$W_TREE_COVER" \
    "$W_ROAD_DIFFICULTY"; do
    [[ -n "$value" ]] || {
      echo "Baseline MCDA ağırlık setinde eksik kriter var: $WEIGHT_CONFIG" >&2
      exit 1
    }
  done

  awk -v sum="$sum" 'BEGIN {
    diff = sum - 1.0
    if (diff < 0) diff = -diff
    exit(diff <= 0.000001 ? 0 : 1)
  }' || {
    echo "Baseline MCDA ağırlıkları 1.00 toplamına eşit değil: $sum" >&2
    exit 1
  }

  MCDA_CALC="where(M==1, (A*${W_EARTHQUAKE_PGA})+(B*${W_FAULT_PROXIMITY})+(C*${W_SITE_CONDITION})+(D*${W_POPULATION_EXPOSURE})+(E*${W_BUILDING_EXPOSURE})+(F*${W_FLOOD})+(G*${W_HYDROGRAPHY})+(H*${W_SLOPE})+(I*${W_LANDCOVER})+(J*${W_TREE_COVER})+(K*${W_ROAD_DIFFICULTY}), -9999)"
}

print_stats() {
  local path="$1"
  echo ""
  echo "İstatistikler: $path"
  run_geo "$GDALINFO" -stats "$path" |
    grep -E "Size is|Pixel Size|Upper Left|Lower Right|NoData|Minimum|Maximum|Mean|STATISTICS_VALID_PERCENT"
}

validate_inputs() {
  configure_tools
  require_tool "$GDAL_CALC"
  require_tool "$GDALINFO"

  project_cd_root
  load_weight_config

  local rasters=(
    "$TEMPLATE"
    "$EARTHQUAKE_SCORE"
    "$FAULT_SCORE"
    "$SITE_SCORE"
    "$POPULATION_SCORE"
    "$BUILDING_SCORE"
    "$FLOOD_SCORE"
    "$HYDROGRAPHY_SCORE"
    "$SLOPE_SCORE"
    "$LANDCOVER_SCORE"
    "$TREE_COVER_SCORE"
    "$ROAD_DIFFICULTY_SCORE"
  )

  for raster in "${rasters[@]}"; do
    require_file "$raster"
    check_grid "$raster"
  done
}

archive_existing_outputs() {
  local archive_dir="$ANALYSIS_DIR/archive/pre_canonical_mcda_rebuild_$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$archive_dir"

  local outputs=(
    "$MCDA_RAW"
    "$MCDA_RAW.aux.xml"
    "$MCDA_NORMALIZED"
    "$MCDA_NORMALIZED.aux.xml"
    "$MCDA_CLASS"
    "$MCDA_CLASS.aux.xml"
  )

  for path in "${outputs[@]}"; do
    if [[ -f "$path" ]]; then
      mv "$path" "$archive_dir/"
      echo "Arşivlendi: $path -> $archive_dir/"
    fi
  done
}

run_check() {
  validate_inputs
  echo "Canonical MCDA girdi kontrolü geçti."
  echo "Proje kökü: script konumundan çözüldü"
  echo "Ağırlık config: $WEIGHT_CONFIG"
  echo "Ağırlık senaryosu: $WEIGHT_SCENARIO"
  echo "Mod: --check"

  for output in "$MCDA_RAW" "$MCDA_NORMALIZED" "$MCDA_CLASS"; do
    if [[ -f "$output" ]]; then
      print_stats "$output"
    else
      echo "Çıktı henüz bulunamadı: $output"
    fi
  done
}

run_execute() {
  validate_inputs
  echo "Canonical MCDA girdi kontrolü geçti."
  echo "Proje kökü: script konumundan çözüldü"
  echo "Ağırlık config: $WEIGHT_CONFIG"
  echo "Ağırlık senaryosu: $WEIGHT_SCENARIO"
  echo "Mod: --execute"

  archive_existing_outputs

  echo ""
  echo "[1/3] Raw 11 kriterli weighted MCDA score rebuild ediliyor..."

  run_geo "$GDAL_CALC" \
    -A "$EARTHQUAKE_SCORE" \
    -B "$FAULT_SCORE" \
    -C "$SITE_SCORE" \
    -D "$POPULATION_SCORE" \
    -E "$BUILDING_SCORE" \
    -F "$FLOOD_SCORE" \
    -G "$HYDROGRAPHY_SCORE" \
    -H "$SLOPE_SCORE" \
    -I "$LANDCOVER_SCORE" \
    -J "$TREE_COVER_SCORE" \
    -K "$ROAD_DIFFICULTY_SCORE" \
    -M "$TEMPLATE" \
    --outfile="$MCDA_RAW" \
    --calc="$MCDA_CALC" \
    --type=Float32 \
    --NoDataValue=-9999 \
    --hideNoData \
    --overwrite

  print_stats "$MCDA_RAW"

  echo ""
  echo "[2/3] Normalized MCDA score rebuild ediliyor..."

  run_geo "$GDAL_CALC" \
    -A "$MCDA_RAW" \
    -M "$TEMPLATE" \
    --outfile="$MCDA_NORMALIZED" \
    --calc="where(M==1, minimum(maximum((A-${MCDA_MIN_RAW})/${MCDA_RANGE},0),1), -9999)" \
    --type=Float32 \
    --NoDataValue=-9999 \
    --hideNoData \
    --overwrite

  print_stats "$MCDA_NORMALIZED"

  echo ""
  echo "[3/3] Beş sınıflı MCDA priority raster rebuild ediliyor..."

  run_geo "$GDAL_CALC" \
    -A "$MCDA_NORMALIZED" \
    -M "$TEMPLATE" \
    --outfile="$MCDA_CLASS" \
    --calc="where(M==1, where(A<0.2,1,where(A<0.4,2,where(A<0.6,3,where(A<0.8,4,5)))), 0)" \
    --type=Int16 \
    --NoDataValue=0 \
    --hideNoData \
    --overwrite

  print_stats "$MCDA_CLASS"

  echo ""
  echo "Canonical 11 kriterli MCDA rebuild çıktıları yazıldı."
}

case "$MODE" in
  --check)
    run_check
    ;;
  --execute)
    run_execute
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
