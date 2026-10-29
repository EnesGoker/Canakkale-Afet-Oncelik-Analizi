"""QGIS --code bootstrap; loaded only by open_qgis_with_carto.py."""
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
_script_dir = Path(os.environ.pop("CANAKKALE_CARTO_SCRIPT_DIR")).resolve()
sys.path.insert(0, str(_script_dir))
from open_qgis_with_carto import start_in_qgis

start_in_qgis()
