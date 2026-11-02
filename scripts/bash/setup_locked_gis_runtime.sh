#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Çanakkale Afet Öncelik Analizi
# Locked macOS arm64 GDAL test runtime
# ============================================================
#
#   setup_locked_gis_runtime.sh install <dir>   build the runtime in a new <dir>
#   setup_locked_gis_runtime.sh verify <dir>    check an existing runtime
#   setup_locked_gis_runtime.sh run <dir> <command> [args...]
#
# install downloads micromamba at a fixed version and SHA-256, creates the
# conda environment from config/qa_runtime_macos_arm64/conda-full-explicit.txt
# (117 packages, each archive checked against package_sha256.json) and adds
# the hash-pinned NumPy 2.4.4 Accelerate wheel as a separate overlay.
# verify checks the micromamba binary, that the installed package set equals
# the lock list, and the Python, GDAL and NumPy versions. run executes a
# command with the runtime's GDAL, PROJ data and NumPy overlay selected, as
# run_compatible_qa.py does for the analysis tools. Nothing in the project is
# written; <dir> must be outside it.
# ============================================================

MICROMAMBA_VERSION="2.5.0-2"
MICROMAMBA_URL="https://github.com/mamba-org/micromamba-releases/releases/download/${MICROMAMBA_VERSION}/micromamba-osx-arm64"
MICROMAMBA_SHA256="22953898e3cfd63c680d696a204c7858ce7f10a10c271bda7e6defd63370ee41"
EXPECTED_PYTHON="3.12.16"
EXPECTED_GDAL="3.12.3"
EXPECTED_NUMPY="2.4.4"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOCK_DIR="$PROJECT_ROOT/config/qa_runtime_macos_arm64"
LOCK_FILE="$LOCK_DIR/conda-full-explicit.txt"

usage() {
  sed -n '9,11p' "${BASH_SOURCE[0]}" | sed 's/^# *//' >&2
  exit 2
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

[[ $# -ge 2 ]] || usage
MODE="$1"
TARGET="$2"
shift 2
[[ "$TARGET" == /* ]] || TARGET="$PWD/$TARGET"
ENV_PREFIX="$TARGET/env"
OVERLAY="$TARGET/numpy-pypi-$EXPECTED_NUMPY"
MICROMAMBA="$TARGET/bin/micromamba"

case "$TARGET/" in
  "$PROJECT_ROOT"/*) fail "the runtime directory must be outside the project: $TARGET" ;;
esac

with_runtime() {
  env -u PYTHONHOME -u PROJ_LIB -u DYLD_LIBRARY_PATH -u DYLD_FALLBACK_LIBRARY_PATH \
    PATH="$ENV_PREFIX/bin:$PATH" PYTHONPATH="$OVERLAY" \
    PROJ_DATA="$ENV_PREFIX/share/proj" GDAL_DATA="$ENV_PREFIX/share/gdal" \
    GDAL_PAM_ENABLED=NO PYTHONDONTWRITEBYTECODE=1 "$@"
}

verify_runtime() {
  [[ -x "$MICROMAMBA" && -x "$ENV_PREFIX/bin/python" && -f "$OVERLAY/numpy/__init__.py" ]] \
    || fail "runtime is incomplete: $TARGET"
  echo "$MICROMAMBA_SHA256  $MICROMAMBA" | shasum -a 256 -c --status \
    || fail "micromamba SHA-256 does not match $MICROMAMBA_VERSION"
  with_runtime "$ENV_PREFIX/bin/python" -I -B - "$LOCK_FILE" "$ENV_PREFIX" "$OVERLAY" \
    "$EXPECTED_PYTHON" "$EXPECTED_GDAL" "$EXPECTED_NUMPY" <<'PY'
import json, platform, sys
from pathlib import Path
lock, prefix, overlay, want_python, want_gdal, want_numpy = sys.argv[1:]
locked = {line.rsplit("/", 1)[1].split("#")[0].removesuffix(".conda").removesuffix(".tar.bz2")
          for line in Path(lock).read_text(encoding="utf-8").splitlines() if line.startswith("https://")}
installed = set()
for path in (Path(prefix) / "conda-meta").glob("*.json"):
    meta = json.loads(path.read_text(encoding="utf-8"))
    installed.add(f"{meta['name']}-{meta['version']}-{meta['build']}")
errors = [f"installed but not locked: {name}" for name in sorted(installed - locked)]
errors += [f"locked but not installed: {name}" for name in sorted(locked - installed)]
sys.path.insert(0, overlay)
import numpy
from osgeo import gdal
if platform.python_version() != want_python:
    errors.append(f"Python {platform.python_version()}, expected {want_python}")
if gdal.VersionInfo("RELEASE_NAME") != want_gdal:
    errors.append(f"GDAL {gdal.VersionInfo('RELEASE_NAME')}, expected {want_gdal}")
if numpy.__version__ != want_numpy or not Path(numpy.__file__).resolve().is_relative_to(Path(overlay).resolve()):
    errors.append(f"NumPy {numpy.__version__} from {numpy.__file__}, expected {want_numpy} from the overlay")
for error in errors:
    print(f"ERROR: {error}", file=sys.stderr)
print(f"Locked GDAL runtime: {'PASSED' if not errors else 'FAILED'}; {len(installed)} of {len(locked)} locked packages "
      f"installed; Python {platform.python_version()}, GDAL {gdal.VersionInfo('RELEASE_NAME')}, NumPy {numpy.__version__} (overlay)")
raise SystemExit(1 if errors else 0)
PY
}

install_runtime() {
  [[ "$(uname -s)/$(uname -m)" == "Darwin/arm64" ]] || fail "this runtime is locked for macOS arm64"
  [[ ! -e "$TARGET" ]] || fail "target already exists: $TARGET"
  # conda-forge binaries carry a 255-character prefix placeholder; a longer
  # prefix cannot be written into them and leaves unsigned, unusable binaries.
  [[ ${#ENV_PREFIX} -le 255 ]] || fail "environment path is ${#ENV_PREFIX} characters; use one of at most 255"
  mkdir -p "$TARGET/bin"
  curl --fail --silent --show-error --location --retry 3 --output "$MICROMAMBA" "$MICROMAMBA_URL"
  echo "$MICROMAMBA_SHA256  $MICROMAMBA" | shasum -a 256 -c - || fail "micromamba download does not match its SHA-256"
  chmod 755 "$MICROMAMBA"
  "$MICROMAMBA" create --yes --no-rc --root-prefix "$TARGET/mamba-root" --prefix "$ENV_PREFIX" --file "$LOCK_FILE"
  "$ENV_PREFIX/bin/python" -I -B - "$LOCK_DIR/package_sha256.json" "$TARGET/mamba-root/pkgs" <<'PY'
import hashlib, json, sys
from pathlib import Path
table, cache = sys.argv[1:]
rows = json.loads(Path(table).read_text(encoding="utf-8"))["packages"]
bad = []
for row in rows:
    path = Path(cache) / row["file"]
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
        bad.append(row["file"])
for name in bad:
    print(f"ERROR: package archive missing or SHA-256 differs: {name}", file=sys.stderr)
print(f"Package archives: {len(rows) - len(bad)} of {len(rows)} match package_sha256.json")
raise SystemExit(1 if bad else 0)
PY
  "$ENV_PREFIX/bin/python" -m pip install --disable-pip-version-check --no-cache-dir --no-deps \
    --only-binary=:all: --require-hashes --target "$OVERLAY" -r "$LOCK_DIR/numpy-accelerate.requirements.txt"
}

case "$MODE" in
  install)
    install_runtime
    verify_runtime
    ;;
  verify)
    verify_runtime
    ;;
  run)
    [[ $# -ge 1 ]] || usage
    [[ -x "$ENV_PREFIX/bin/python" ]] || fail "runtime is incomplete: $TARGET"
    with_runtime "$@"
    ;;
  *)
    usage
    ;;
esac
