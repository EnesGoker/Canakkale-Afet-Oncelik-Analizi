#!/usr/bin/env python3
"""Test runtime failure/skip reporting with isolated synthetic checker scripts."""

import contextlib
import io
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest import mock

from run_integrity_checks import CHECKS, aggregate_exit_code, execute_check, main, resolve_runtime, runtime_environment


class IntegrityRunnerTests(unittest.TestCase):
    def execute_fixture(self, body):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "checker.py"
            script.write_text(body, encoding="utf-8")
            return execute_check(sys.executable, runtime_environment(sys.executable, os.environ), script, Path(directory))

    def test_actual_failing_checker_is_not_skipped(self):
        result = self.execute_fixture('print(\'{"passed": false}\'); raise SystemExit(1)')
        self.assertEqual(result["status"], "failed")
        self.assertEqual(aggregate_exit_code([result]), 1)

    def test_actual_dependency_skip_remains_incomplete(self):
        result = self.execute_fixture('print(\'{"passed": false, "message": "missing dependency"}\'); raise SystemExit(2)')
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(aggregate_exit_code([result]), 2)

    def test_success_requires_successful_evidence(self):
        passed = self.execute_fixture('print(\'{"passed": true}\')')
        inconsistent = self.execute_fixture('print(\'{"passed": false}\')')
        self.assertEqual(aggregate_exit_code([passed]), 0)
        self.assertEqual(aggregate_exit_code([inconsistent]), 1)

    def test_invalid_json_and_crash_fail(self):
        for body in ('print("unexpected output")', 'raise SystemExit(17)'):
            with self.subTest(body=body):
                self.assertEqual(self.execute_fixture(body)["status"], "failed")

    def test_failed_check_takes_precedence_over_skip(self):
        self.assertEqual(aggregate_exit_code([{"status": "skipped"}, {"status": "failed"}]), 1)

    def test_invalid_explicit_runtime_does_not_fall_back(self):
        with mock.patch("run_integrity_checks.shutil.which", return_value=None):
            with self.assertRaisesRegex(ValueError, "QGIS_PYTHON_BIN"):
                resolve_runtime(("qgis.core",), "QGIS_PYTHON_BIN", {"QGIS_PYTHON_BIN": "missing-fixture-python"})

    def test_missing_runtimes_cli_never_claims_full_pass(self):
        with mock.patch("run_integrity_checks.resolve_runtime", return_value=None), mock.patch.object(sys, "argv", ["runner"]):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main()
        self.assertEqual(code, 2)
        self.assertEqual(output.getvalue().count("ATLANDI:"), len(CHECKS))
        self.assertNotIn("GEÇTİ:", output.getvalue())
        self.assertNotIn("Zorunlu bütünlük kontrolleri geçti.", output.getvalue())

    def test_explicit_runtime_crash_is_failure(self):
        for code in (1, -11, 17):
            with self.subTest(code=code), mock.patch("run_integrity_checks.subprocess.run", return_value=subprocess.CompletedProcess([], code)):
                with self.assertRaisesRegex(ValueError, "GDAL_PYTHON_BIN"):
                    resolve_runtime(("numpy",), "GDAL_PYTHON_BIN", {"GDAL_PYTHON_BIN": sys.executable})

    def test_explicit_runtime_launch_error_is_failure(self):
        for error in (OSError("fixture"), subprocess.TimeoutExpired("fixture", 15)):
            with self.subTest(error=type(error).__name__), mock.patch("run_integrity_checks.subprocess.run", side_effect=error):
                with self.assertRaisesRegex(ValueError, "GDAL_PYTHON_BIN"):
                    resolve_runtime(("numpy",), "GDAL_PYTHON_BIN", {"GDAL_PYTHON_BIN": sys.executable})

    def test_explicit_runtime_missing_module_is_skipped(self):
        with mock.patch("run_integrity_checks.subprocess.run", return_value=subprocess.CompletedProcess([], 2)):
            self.assertIsNone(resolve_runtime(("numpy",), "GDAL_PYTHON_BIN", {"GDAL_PYTHON_BIN": sys.executable}))


if __name__ == "__main__":
    unittest.main()
