#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/project_env.sh"
project_cd_root

echo "=== PROJE KÖKÜ ==="
pwd
echo ""

echo "=== ÜST SEVİYE ==="
find . -maxdepth 1 -print | sort
echo ""

echo "=== QGIS PROJE DOSYALARI ==="
find qgis -maxdepth 1 \( -name "*.qgz" -o -name "*.qgs" -o -name "*.qgz~" -o -name "*.qgs~" \) -print -exec ls -lh {} \;
echo ""

echo "=== PROCESSED DOSYALARI ==="
find data/processed -maxdepth 3 -type f | sort
echo ""

echo "=== TEMP / LOCK DOSYALARI ==="
find . \( -name "*.gpkg-shm" -o -name "*.gpkg-wal" -o -name "*.qgz~" -o -name "*.qgs~" -o -name ".DS_Store" \) -print
echo ""

echo "=== BOYUT ÖZETİ ==="
du -sh . data data/raw data/processed qgis docs scripts outputs 2>/dev/null || true
