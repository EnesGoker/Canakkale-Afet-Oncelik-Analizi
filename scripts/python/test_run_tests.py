#!/usr/bin/env python3
"""Tier parsing, environment matching, per-module recording and exit codes of run_tests.py."""
from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
from tier_support import module_tier
import run_tests

TIER = module_tier(__file__)


def table(**modules):
    return {"format_version": 1,
            "tiers": {"stdlib": {"imports": []}, "absent": {"imports": ["canakkale_no_such_module_xyz"]}},
            "modules": modules or {"test_a": {"tier": "stdlib", "tests": 1}}}


def record(*outcomes, module="test_a", code=0):
    return {"module": module, "exit": code, "seconds": 0.0, "output": "",
            "tests_run": len(outcomes), "outcomes": [{"id": f"{module}.Case.test_{i}", "outcome": o, "reason": r}
                                                      for i, (o, r) in enumerate(outcomes)]}


@TIER.skip_unless_available
class TierSelection(unittest.TestCase):
    def test_parse_tiers_accepts_known_distinct_names(self):
        self.assertEqual(run_tests.parse_tiers(" stdlib , absent ", table()), ["stdlib", "absent"])

    def test_parse_tiers_rejects_unknown_duplicate_or_empty(self):
        for value in ("gdal", "stdlib,stdlib", " , "):
            with self.subTest(value=value), self.assertRaises(ValueError):
                run_tests.parse_tiers(value, table())

    def test_environment_must_match_named_tiers(self):
        self.assertEqual(run_tests.environment_errors(table(), ["stdlib"]), [])
        missing = run_tests.environment_errors(table(), ["stdlib", "absent"])
        self.assertTrue(any("absent tier is required" in error for error in missing))
        unnamed = run_tests.environment_errors(table(), [])
        self.assertTrue(any("stdlib tier is importable here but was not named" in error for error in unnamed))


@TIER.skip_unless_available
class ModuleProcesses(unittest.TestCase):
    def run_source(self, source, timeout=60):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "test_fixture_module.py").write_text(textwrap.dedent(source), encoding="utf-8")
            results = Path(folder) / "results"
            results.mkdir()
            with patch.object(run_tests, "SCRIPTS", Path(folder)):
                return run_tests.run_module("test_fixture_module", results, timeout)

    def test_outcomes_are_recorded_test_by_test(self):
        result = self.run_source("""
            import unittest
            class Case(unittest.TestCase):
                def test_pass(self): pass
                @unittest.skip("requires the 'gdal' test tier")
                def test_skip(self): pass
                def test_fail(self): self.fail("no")
        """)
        self.assertEqual(result["exit"], 1)
        outcomes = {row["id"].rsplit(".", 1)[1]: row for row in result["outcomes"]}
        self.assertEqual({k: v["outcome"] for k, v in outcomes.items()}, {"test_pass": "pass", "test_skip": "skip", "test_fail": "failure"})
        self.assertIn("'gdal' test tier", outcomes["test_skip"]["reason"])

    def test_import_error_is_an_error_outcome(self):
        result = self.run_source("import canakkale_no_such_module_xyz\n")
        self.assertEqual(result["exit"], 1)
        self.assertEqual([row["outcome"] for row in result["outcomes"]], ["error"])

    def test_timeout_reports_exit_124(self):
        result = self.run_source("""
            import time, unittest
            class Case(unittest.TestCase):
                def test_slow(self): time.sleep(30)
        """, timeout=2)
        self.assertEqual(result["exit"], 124)
        self.assertIn("Timed out", result["output"])


@TIER.skip_unless_available
class ExitCodes(unittest.TestCase):
    def main(self, argv, fake_table=None, records=(), check_errors=(), env_errors=()):
        fake_table = fake_table or table()
        modules = [r["module"] for r in records]
        with patch.object(run_tests.tier_support, "load_table", return_value=fake_table), \
                patch.object(run_tests.tier_support, "check_table", return_value=list(check_errors)), \
                patch.object(run_tests, "environment_errors", return_value=list(env_errors)), \
                patch.object(run_tests.tier_support, "discover_modules", return_value=modules), \
                patch.object(run_tests, "run_module", side_effect=list(records)) as runner, \
                patch.object(run_tests, "write_step_summary"), \
                patch("sys.stdout", new_callable=io.StringIO), patch("sys.stderr", new_callable=io.StringIO):
            return run_tests.main(argv), runner.call_count

    def test_matching_counts_pass_and_write_json(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "result.json"
            code, calls = self.main(["--tiers", "stdlib", "--json", str(target)], records=[record(("pass", ""))])
            self.assertEqual((code, calls), (0, 1))
            self.assertTrue(json.loads(target.read_text(encoding="utf-8"))["passed"])

    def test_failed_test_or_wrong_count_is_one(self):
        self.assertEqual(self.main(["--tiers", "stdlib"], records=[record(("failure", ""), code=1)])[0], 1)
        self.assertEqual(self.main(["--tiers", "stdlib"], records=[record(("pass", ""), ("pass", ""))])[0], 1)

    def test_skip_in_unnamed_tier_needs_its_reason(self):
        fake = table(test_a={"tier": "absent", "tests": 1})
        self.assertEqual(self.main(["--tiers", "stdlib"], fake, [record(("skip", "requires the 'absent' test tier"))])[0], 0)
        self.assertEqual(self.main(["--tiers", "stdlib"], fake, [record(("skip", "some other reason"))])[0], 1)

    def test_environment_mismatch_is_two_and_runs_nothing(self):
        self.assertEqual(self.main(["--tiers", "stdlib"], env_errors=["mismatch"]), (2, 0))

    def test_table_error_or_unknown_tier_is_one_and_runs_nothing(self):
        self.assertEqual(self.main(["--tiers", "stdlib"], check_errors=["stale table"]), (1, 0))
        self.assertEqual(self.main(["--tiers", "gdal"]), (1, 0))

    def test_existing_json_target_is_refused(self):
        with tempfile.NamedTemporaryFile() as existing, patch("sys.stderr", new_callable=io.StringIO), \
                patch.object(run_tests.tier_support, "load_table", return_value=table()), self.assertRaises(SystemExit) as raised:
            run_tests.main(["--tiers", "stdlib", "--json", existing.name])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
