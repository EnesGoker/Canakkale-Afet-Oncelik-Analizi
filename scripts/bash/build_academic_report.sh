#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Çanakkale Afet Öncelik Analizi
# Akademik Rapor Builder
# ============================================================
#
# Amaç:
#   Tanımlı canonical rapor varlıklarından A4 akademik DOCX raporu üretir.
#
# Güvenlik:
#   Varsayılan mod --build'dir. Yalnızca outputs/report altına yazar.
#   Girdi/tool doğrulaması için --check modu geçici dizinde build yapar.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/project_env.sh"

MODE="${1:---build}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PYTHON_SCRIPT="scripts/python/build_academic_report.py"
OUTPUT_DIR="outputs/report"
TEMP_DIR=""

usage() {
  cat <<'EOF'
Kullanım:
  scripts/bash/build_academic_report.sh --build
  scripts/bash/build_academic_report.sh --check

Modlar:
  --build   Akademik DOCX raporunu outputs/report altına yazar.
  --check   Girdi/tool QA için raporu geçici dizinde build eder.

Python gereksinimleri:
  python-docx ve Pillow bulunan Python 3.

Opsiyonel ortam:
  PYTHON_BIN   Kullanılacak Python executable.
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
  PYTHON_BIN="$(resolve_python)"

  require_tool "$PYTHON_BIN"
  require_file "$PYTHON_SCRIPT"

  "$PYTHON_BIN" - <<'PY'
import docx  # noqa: F401
import PIL   # noqa: F401
PY
}

run_builder() {
  local output_dir="$1"
  "$PYTHON_BIN" "$PYTHON_SCRIPT" \
    --project-root "$PROJECT_DIR" \
    --output-dir "$output_dir"
}

run_check() {
  prepare_runtime
  TEMP_DIR="$(mktemp -d)"

  echo "Akademik rapor builder"
  echo "Proje kökü: script konumundan çözüldü"
  echo "Mod: --check"
  echo "Çıktı: geçici QA dizini"

  run_builder "$TEMP_DIR/report"

  echo ""
  echo "Akademik rapor build kontrolü geçti."
}

run_build() {
  prepare_runtime

  echo "Akademik rapor builder"
  echo "Proje kökü: script konumundan çözüldü"
  echo "Mod: --build"
  echo "Çıktı: $OUTPUT_DIR"

  mkdir -p "$OUTPUT_DIR"
  run_builder "$OUTPUT_DIR"

  echo ""
  echo "Akademik rapor DOCX başarıyla üretildi."
}

case "$MODE" in
  --build)
    run_build
    ;;
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
