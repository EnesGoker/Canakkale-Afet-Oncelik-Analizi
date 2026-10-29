#!/usr/bin/env bash

# Portable bash scriptleri için ortak proje/runtime yardımcıları.
# Bu dosya scripts/bash altındaki scriptlerden source edilir.

PROJECT_ENV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$PROJECT_ENV_DIR/../../.." && pwd)"

PROJ_LIB="${PROJ_LIB:-}"
PROJ_DATA="${PROJ_DATA:-}"

project_cd_root() {
  cd "$PROJECT_DIR"
}

die() {
  echo "$*" >&2
  exit 1
}

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    die "Gerekli dosya eksik: $path"
  fi
}

require_tool() {
  local path="$1"
  if [[ ! -x "$path" ]]; then
    die "Gerekli executable eksik: $path"
  fi
}

resolve_tool() {
  local env_name="$1"
  local tool_name="$2"
  local configured="${!env_name:-}"
  local candidate
  local dir

  if [[ -n "$configured" ]]; then
    if [[ "$configured" == */* ]]; then
      [[ -x "$configured" ]] || die "Ayarlanmış $env_name executable değil: $configured"
      printf '%s\n' "$configured"
      return 0
    fi

    candidate="$(command -v "$configured" || true)"
    [[ -n "$candidate" ]] || die "Ayarlanmış $env_name PATH içinde bulunamadı: $configured"
    printf '%s\n' "$candidate"
    return 0
  fi

  for dir in "${GDAL_BIN:-}" "${QGIS_BIN:-}"; do
    if [[ -n "$dir" && -x "$dir/$tool_name" ]]; then
      printf '%s\n' "$dir/$tool_name"
      return 0
    fi
  done

  candidate="$(command -v "$tool_name" || true)"
  if [[ -n "$candidate" ]]; then
    printf '%s\n' "$candidate"
    return 0
  fi

  cat >&2 <<EOF
Gerekli araç eksik: $tool_name
Aracı PATH içine ekleyerek, $env_name değişkenini ayarlayarak veya GDAL_BIN/QGIS_BIN değerini gerekli GDAL/QGIS komut satırı araçlarını içeren dizine vererek sağlayın.
EOF
  exit 1
}

run_geo() {
  local env_args=()

  # İstatistik okuması --check sırasında raster yanına .aux.xml yazmamalı.
  if [[ "${MODE:-}" == "--check" ]]; then
    env_args+=("GDAL_PAM_ENABLED=NO")
  fi

  if [[ -n "$PROJ_LIB" ]]; then
    env_args+=("PROJ_LIB=$PROJ_LIB")
  fi

  if [[ -n "$PROJ_DATA" ]]; then
    env_args+=("PROJ_DATA=$PROJ_DATA")
  fi

  if ((${#env_args[@]})); then
    env "${env_args[@]}" "$@"
  else
    "$@"
  fi
}
