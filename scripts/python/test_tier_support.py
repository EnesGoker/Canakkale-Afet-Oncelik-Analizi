#!/usr/bin/env python3
"""Tier table, discovery-time skip and outcome-count checks using temporary fixtures."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
import tier_support as tiers

SCRIPT = Path(__file__).with_name("tier_support.py")
MODULE_A = """import unittest

class Alpha(unittest.TestCase):
    def test_one(self):
        pass

    def test_two(self):
        pass

    def helper(self):
        pass
"""
MODULE_B = """import unittest
from unittest import TestCase

class Base(TestCase):
    def test_base(self):
        pass

class Child(Base):
    def test_child(self):
        pass

class NotATest:
    def test_ignored(self):
        pass

SOURCE = '''
class Hidden(unittest.TestCase):
    def test_hidden(self):
        pass
'''
"""


class TierTableTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="canakkale-tier-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "test_alpha.py").write_text(MODULE_A, encoding="utf-8")
        (self.root / "test_beta.py").write_text(MODULE_B, encoding="utf-8")
        (self.root / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")
        self.table = {"format_version": 1,
                      "tiers": {"stdlib": {"imports": []}, "absent": {"imports": ["canakkale_missing_module_for_tests"]}},
                      "modules": {"test_alpha": {"tier": "stdlib", "tests": 2}, "test_beta": {"tier": "absent", "tests": 3}}}
        self.table_path = self.root / "tiers.json"
        self.save()

    def save(self, text=None):
        self.table_path.write_text(text or json.dumps(self.table), encoding="utf-8")

    def test_repository_table_matches_test_files(self):
        table = tiers.load_table()
        self.assertEqual(tiers.check_table(table), [])
        self.assertEqual(set(table["modules"]), set(tiers.discover_modules()))
        self.assertEqual(sum(tiers.tier_totals(table).values()), sum(row["tests"] for row in table["modules"].values()))

    def test_static_count_matches_the_unittest_loader(self):
        for name, expected in (("test_alpha", 2), ("test_beta", 3)):
            with self.subTest(name=name):
                path = self.root / f"{name}.py"
                spec = importlib.util.spec_from_file_location(f"canakkale_fixture_{name}", path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                loaded = unittest.defaultTestLoader.loadTestsFromModule(module).countTestCases()
                self.assertEqual(tiers.static_test_count(path), expected)
                self.assertEqual(loaded, expected)

    def test_fixture_table_passes(self):
        self.assertEqual(tiers.check_table(tiers.load_table(self.table_path), self.root), [])

    def test_added_or_removed_test_method_fails(self):
        path = self.root / "test_alpha.py"
        path.write_text(MODULE_A + "\n    def test_three(self):\n        pass\n", encoding="utf-8")
        self.assertIn("test_alpha: 3 test methods on disk, 2 in the tier table",
                      tiers.check_table(tiers.load_table(self.table_path), self.root))
        path.write_text(MODULE_A.replace("    def test_two(self):\n        pass\n", ""), encoding="utf-8")
        self.assertIn("test_alpha: 1 test methods on disk, 2 in the tier table",
                      tiers.check_table(tiers.load_table(self.table_path), self.root))

    def test_added_or_removed_module_fails(self):
        (self.root / "test_gamma.py").write_text(MODULE_A, encoding="utf-8")
        self.assertIn("Test module not in the tier table: test_gamma",
                      tiers.check_table(tiers.load_table(self.table_path), self.root))
        (self.root / "test_gamma.py").unlink()
        (self.root / "test_beta.py").unlink()
        self.assertIn("Tier table lists a missing test module: test_beta",
                      tiers.check_table(tiers.load_table(self.table_path), self.root))

    def test_invalid_tables_rejected(self):
        cases = {
            "format": dict(self.table, format_version=2),
            "unknown tier": dict(self.table, modules={"test_alpha": {"tier": "gis", "tests": 2}}),
            "zero tests": dict(self.table, modules={"test_alpha": {"tier": "stdlib", "tests": 0}}),
            "bool count": dict(self.table, modules={"test_alpha": {"tier": "stdlib", "tests": True}}),
            "extra key": dict(self.table, modules={"test_alpha": {"tier": "stdlib", "tests": 2, "note": "x"}}),
            "bad name": dict(self.table, modules={"alpha": {"tier": "stdlib", "tests": 2}}),
            "imports": dict(self.table, tiers={"stdlib": {"imports": "numpy"}}),
        }
        for label, table in cases.items():
            with self.subTest(label=label):
                self.save(json.dumps(table))
                with self.assertRaises(ValueError):
                    tiers.load_table(self.table_path)
        self.save('{"format_version": 1, "tiers": {"stdlib": {"imports": []}}, '
                  '"modules": {"test_alpha": {"tier": "stdlib", "tests": 2}, "test_alpha": {"tier": "stdlib", "tests": 2}}}')
        with self.assertRaises(ValueError):
            tiers.load_table(self.table_path)

    def test_check_command_reports_totals_and_fails_on_mismatch(self):
        command = [sys.executable, "-B", str(SCRIPT), "--check", "--table", str(self.table_path), "--scripts-dir", str(self.root)]
        process = subprocess.run(command, capture_output=True, text=True, timeout=60)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("PASSED; 2 modules, 5 tests (stdlib 2, absent 3)", process.stdout)
        (self.root / "test_gamma.py").write_text(MODULE_A, encoding="utf-8")
        process = subprocess.run(command, capture_output=True, text=True, timeout=60)
        self.assertEqual(process.returncode, 1)
        self.assertIn("FAILED", process.stdout)
        self.assertIn("test_gamma", process.stderr)


class TierAvailabilityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="canakkale-tier-probe-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.table_path = self.root / "tiers.json"
        self.table_path.write_text(json.dumps({
            "format_version": 1,
            "tiers": {"stdlib": {"imports": []}, "absent": {"imports": ["json", "canakkale_missing_module_for_tests"]}},
            "modules": {"test_alpha": {"tier": "stdlib", "tests": 1}, "test_beta": {"tier": "absent", "tests": 1}}}),
            encoding="utf-8")

    @staticmethod
    def run_case(tier):
        @tier.skip_unless_available
        class Case(unittest.TestCase):
            def test_runs(self):
                pass
        result = unittest.TestResult()
        unittest.defaultTestLoader.loadTestsFromTestCase(Case).run(result)
        return result

    def test_unavailable_tier_skips_each_test_and_names_the_import(self):
        tier = tiers.module_tier(str(self.root / "test_beta.py"), self.table_path)
        self.assertFalse(tier.available)
        self.assertEqual(tier.missing, "canakkale_missing_module_for_tests")
        result = self.run_case(tier)
        self.assertEqual((result.testsRun, len(result.skipped), len(result.errors)), (1, 1, 0))
        self.assertIn("'absent' test tier", result.skipped[0][1])
        self.assertIn("canakkale_missing_module_for_tests", result.skipped[0][1])

    def test_available_tier_runs_tests(self):
        tier = tiers.module_tier(str(self.root / "test_alpha.py"), self.table_path)
        self.assertTrue(tier.available)
        result = self.run_case(tier)
        self.assertEqual((result.testsRun, len(result.skipped)), (1, 0))
        self.assertTrue(result.wasSuccessful())

    def test_unregistered_module_is_an_error(self):
        with self.assertRaises(LookupError):
            tiers.module_tier(str(self.root / "test_gamma.py"), self.table_path)

    def test_probe_imports_only_in_a_child_process(self):
        marker = self.root / "imported.txt"
        (self.root / "canakkale_probe_marker.py").write_text(
            f"from pathlib import Path\nPath({str(marker)!r}).write_text('child')\n", encoding="utf-8")
        path = os.pathsep.join(filter(None, (str(self.root), os.environ.get("PYTHONPATH"))))
        with mock.patch.dict(os.environ, {"PYTHONPATH": path}), mock.patch.dict(tiers._missing_cache, clear=True):
            self.assertIsNone(tiers.missing_import(("canakkale_probe_marker",)))
        self.assertEqual(marker.read_text(), "child")
        self.assertNotIn("canakkale_probe_marker", sys.modules)


class OutcomeVerificationTests(unittest.TestCase):
    table = {"format_version": 1, "tiers": {"stdlib": {"imports": []}, "gis": {"imports": ["osgeo.gdal"]}},
             "modules": {"test_alpha": {"tier": "stdlib", "tests": 2}, "test_beta": {"tier": "gis", "tests": 1}}}
    reason = "requires the 'gis' test tier; osgeo.gdal is not importable here (config/test_tiers_v1.json)"

    def outcomes(self):
        return [{"id": "test_alpha.Alpha.test_one", "outcome": "pass"},
                {"id": "test_alpha.Alpha.test_two", "outcome": "pass"},
                {"id": "test_beta.Beta.test_map", "outcome": "skip", "reason": self.reason}]

    def test_matching_outcomes_pass_and_are_counted(self):
        errors, summary = tiers.verify_outcomes(self.table, self.outcomes(), {"stdlib"})
        self.assertEqual(errors, [])
        self.assertEqual(summary, {"stdlib": {"expected": 2, "passed": 2, "skipped": 0},
                                   "gis": {"expected": 1, "passed": 0, "skipped": 1}})

    def test_skip_in_a_required_tier_fails(self):
        errors, _ = tiers.verify_outcomes(self.table, self.outcomes(), {"stdlib", "gis"})
        self.assertIn("test_beta.Beta.test_map: skip, expected pass (gis tier)", errors)

    def test_failures_missing_and_unexpected_outcomes_fail(self):
        rows = self.outcomes()
        rows[0]["outcome"] = "failure"
        rows.pop(1)
        rows.append({"id": "unittest.loader._FailedTest.test_gamma", "outcome": "error"})
        errors, _ = tiers.verify_outcomes(self.table, rows, {"stdlib"})
        self.assertIn("test_alpha.Alpha.test_one: failure, expected pass (stdlib tier)", errors)
        self.assertIn("test_alpha: 1 test outcomes, 2 in the tier table", errors)
        self.assertTrue(any(error.startswith("Unexpected test outcome outside the tier table") for error in errors))

    def test_skip_reason_must_name_the_tier(self):
        rows = self.outcomes()
        rows[2]["reason"] = "skipped for another reason"
        errors, _ = tiers.verify_outcomes(self.table, rows, {"stdlib"})
        self.assertIn("test_beta.Beta.test_map: skip reason does not name the gis tier", errors)


if __name__ == "__main__":
    unittest.main()
