#!/usr/bin/env python3
"""Argument, target and precondition contracts of setup_locked_gis_runtime.sh (no network, no install)."""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
from tier_support import module_tier

TIER = module_tier(__file__)
ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/bash/setup_locked_gis_runtime.sh"


@TIER.skip_unless_available
class RuntimeSetupContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "home"
        self.home.mkdir()

    def run_script(self, *args):
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(self.home)}
        return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, env=env, timeout=60,
                              cwd=self.temp.name)

    def test_bash_syntax(self):
        self.assertEqual(subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True).returncode, 0)

    def test_missing_or_unknown_mode_prints_usage_with_exit_two(self):
        for args in ((), ("verify",), ("bogus", str(Path(self.temp.name) / "rt"))):
            result = self.run_script(*args)
            with self.subTest(args=args):
                self.assertEqual(result.returncode, 2)
                self.assertIn("setup_locked_gis_runtime.sh install <dir>", result.stderr)

    def test_target_inside_project_is_refused(self):
        result = self.run_script("verify", str(ROOT / "runtime-inside"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("must be outside the project", result.stderr)
        self.assertFalse((ROOT / "runtime-inside").exists())

    def test_verify_of_empty_target_reports_incomplete(self):
        target = Path(self.temp.name) / "rt"
        target.mkdir()
        result = self.run_script("verify", str(target))
        self.assertEqual(result.returncode, 1)
        self.assertIn("runtime is incomplete", result.stderr)
        self.assertEqual(list(target.iterdir()), [])

    def test_install_into_existing_target_stops_before_download(self):
        target = Path(self.temp.name) / "rt"
        target.mkdir()
        result = self.run_script("install", str(target))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stderr, "target already exists|locked for macOS arm64")
        self.assertEqual(list(target.iterdir()), [])

    def test_run_with_incomplete_runtime_does_not_execute_the_command(self):
        marker = Path(self.temp.name) / "marker"
        result = self.run_script("run", str(Path(self.temp.name) / "rt"), "touch", str(marker))
        self.assertEqual(result.returncode, 1)
        self.assertFalse(marker.exists())

    def test_pins_match_the_lock_files(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertRegex(text, r'MICROMAMBA_SHA256="[0-9a-f]{64}"')
        numpy = re.search(r'EXPECTED_NUMPY="([^"]+)"', text).group(1)
        lock = ROOT / "config/qa_runtime_macos_arm64"
        self.assertIn(f"numpy-{numpy}-", (lock / "numpy-accelerate.requirements.txt").read_text(encoding="utf-8"))
        self.assertTrue((lock / "conda-full-explicit.txt").is_file() and (lock / "package_sha256.json").is_file())


if __name__ == "__main__":
    unittest.main()
