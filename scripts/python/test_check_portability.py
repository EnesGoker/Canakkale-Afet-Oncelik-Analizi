#!/usr/bin/env python3
"""check_portability.py messages and public-source scope, using temporary QGZ fixtures."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.dont_write_bytecode = True
import check_portability as portability

SCRIPT = Path(__file__).with_name("check_portability.py")
LAYERS = ["data/processed/analysis/a_score_32635.tif", "data/processed/admin/districts_32635.gpkg",
          "outputs/analysis/agreement_v1/count_32635.tif"]
WEB = "type=xyz&url=https://tiles.example.invalid/{z}/{x}/{y}.png"


class PortabilityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="canakkale-portability-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.selection = {"format_version": 1, "files": ["qgis/canakkale_disaster_priority.qgz", "README.md"]}
        self.write_project([f"../{name}" for name in LAYERS[:2]] + [f"../{LAYERS[2]}|layername=count", WEB])
        (self.root / "config").mkdir()
        self.save_selection()

    def write_project(self, sources):
        layers = "".join(f"<maplayer><datasource>{source.replace('&', '&amp;')}</datasource></maplayer>" for source in sources)
        qgs = f"<qgis><properties><Paths><Absolute>false</Absolute></Paths></properties><projectlayers>{layers}</projectlayers></qgis>"
        (self.root / "qgis").mkdir(exist_ok=True)
        with zipfile.ZipFile(self.root / portability.PROJECT_FILE, "w") as archive:
            archive.writestr("canakkale_disaster_priority.qgs", qgs)

    def save_selection(self):
        (self.root / portability.PUBLIC_SELECTION).write_text(json.dumps(self.selection), encoding="utf-8")

    def add_layers(self, names):
        for name in names:
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_bytes(b"layer")

    def run_check(self, *extra):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "--check", "--project-root", str(self.root), *extra],
                              capture_output=True, text=True, timeout=60)

    def test_full_scope_passes_with_all_layers(self):
        self.add_layers(LAYERS)
        process = self.run_check()
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("3 yerel dosya, 1 web kaynağı", process.stdout)

    def test_missing_layer_hint_states_the_actual_release(self):
        process = self.run_check()
        self.assertEqual(process.returncode, 1)
        for name in LAYERS:
            self.assertIn(f"HATA: {portability.MISSING_LAYER}{name}", process.stderr)
        self.assertIn(portability.DATA_HINT, process.stderr)
        self.assertIn("--scope public-source", process.stderr)
        self.assertNotIn("portable.zip", process.stderr)
        self.assertNotIn("LFS", process.stderr)

    def test_hint_is_not_printed_for_other_errors(self):
        self.write_project(["/absolute/layer.tif"])
        process = self.run_check()
        self.assertEqual(process.returncode, 1)
        self.assertIn("Mutlak yerel katman yolu", process.stderr)
        self.assertNotIn(portability.DATA_HINT, process.stderr)

    def test_public_scope_lists_every_omitted_layer(self):
        process = self.run_check("--scope", "public-source")
        self.assertEqual(process.returncode, 0, process.stderr)
        for name in LAYERS:
            self.assertIn(f"ATLANDI (kamu kaynak sürümünde dağıtılmaz): {name}\n", process.stdout)
        self.assertIn("3 yerel katman listelenip atlandı, 0 yerel dosya doğrulandı, 1 web kaynağı", process.stdout)

    def test_public_scope_fails_when_any_omitted_layer_is_present(self):
        for names in (LAYERS[:1], LAYERS):
            with self.subTest(present=len(names)):
                self.add_layers(names)
                process = self.run_check("--scope", "public-source")
                self.assertEqual(process.returncode, 1)
                self.assertIn(f"dağıtılmayan yerel katman bulundu: {names[0]}", process.stderr)
                self.assertIn(portability.FULL_CHECK, process.stderr)
                self.assertEqual(process.stdout.count("ATLANDI"), len(LAYERS) - len(names))

    def test_public_scope_definitions_must_agree(self):
        self.selection["files"].append(LAYERS[0])
        self.save_selection()
        process = self.run_check("--scope", "public-source")
        self.assertEqual(process.returncode, 1)
        self.assertIn("iki tanımı", process.stderr)
        self.selection["files"].remove(LAYERS[0])
        self.save_selection()
        self.write_project([f"../{name}" for name in LAYERS] + ["../outputs/tables/summary.csv"])
        process = self.run_check("--scope", "public-source")
        self.assertEqual(process.returncode, 1)
        self.assertIn("outputs/tables/summary.csv", process.stderr)

    def test_public_scope_keeps_other_checks(self):
        self.write_project([f"../{name}" for name in LAYERS] + ["/absolute/layer.tif"])
        process = self.run_check("--scope", "public-source")
        self.assertEqual(process.returncode, 1)
        self.assertIn("Mutlak yerel katman yolu", process.stderr)
        (self.root / portability.PROJECT_FILE).unlink()
        self.assertEqual(self.run_check("--scope", "public-source").returncode, 1)

    def test_public_scope_rejects_manifest_verification(self):
        process = self.run_check("--scope", "public-source", "--verify-manifest")
        self.assertEqual(process.returncode, 2)


if __name__ == "__main__":
    unittest.main()
