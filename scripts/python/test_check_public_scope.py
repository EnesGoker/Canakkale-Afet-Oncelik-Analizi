#!/usr/bin/env python3
"""Expected skip-list contract of check_public_scope.py, run against stub tools in a temporary tree."""
from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
from tier_support import module_tier
import check_public_scope as scope

TIER = module_tier(__file__)
FILES = ["data/processed/a.tif", "data/processed/b.tif"]
LAYERS = ["Katman A", "Katman B"]
BASELINE_STUB = """import json, sys
from pathlib import Path
state = json.loads((Path(__file__).resolve().parents[2] / "stub.json").read_text(encoding="utf-8"))
if state.get("baseline_text"):
    print(state["baseline_text"])
else:
    print(json.dumps({"passed": state["baseline_exit"] == 0, "verified_files": state["verified"], "skipped_files": state["files"]}))
raise SystemExit(state["baseline_exit"])
"""
PORTABILITY_STUB = """import json, sys
from pathlib import Path
state = json.loads((Path(__file__).resolve().parents[2] / "stub.json").read_text(encoding="utf-8"))
for name in state["layers"]:
    print("ATLANDI (kamu kaynak sürümünde dağıtılmaz): " + name)
print("Portability: PASSED")
raise SystemExit(state["portability_exit"])
"""


@TIER.skip_unless_available
class PublicScopeContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "scripts/python").mkdir(parents=True)
        (self.root / "config").mkdir()
        (self.root / "scripts/python/analysis_baseline.py").write_text(BASELINE_STUB, encoding="utf-8")
        (self.root / "scripts/python/check_portability.py").write_text(PORTABILITY_STUB, encoding="utf-8")
        self.expected = {"format_version": 1, "analysis_baseline": {"verified_files": 11, "skipped_files": FILES},
                         "check_portability": {"skipped_layers": LAYERS}}
        self.write_expected()
        self.state(files=FILES, layers=LAYERS)

    def write_expected(self):
        (self.root / scope.EXPECTED).write_text(json.dumps(self.expected), encoding="utf-8")

    def state(self, **changes):
        state = {"baseline_exit": 0, "verified": 11, "files": FILES, "layers": LAYERS, "portability_exit": 0, **changes}
        (self.root / "stub.json").write_text(json.dumps(state), encoding="utf-8")

    def run_check(self):
        with patch("sys.stdout", new_callable=io.StringIO) as out, patch("sys.stderr", new_callable=io.StringIO) as err:
            code = scope.main(["--project-root", str(self.root)])
        return code, out.getvalue() + err.getvalue()

    def test_exact_lists_pass(self):
        code, text = self.run_check()
        self.assertEqual(code, 0, text)
        self.assertIn("Public-source scope: PASSED", text)

    def test_extra_missing_or_duplicate_file_fails(self):
        for files, message in ((FILES + ["data/processed/c.tif"], "skipped but not expected"),
                               (FILES[:1], "expected to be skipped but was not"),
                               (FILES + FILES[:1], "duplicate entry")):
            self.state(files=files)
            with self.subTest(message=message):
                code, text = self.run_check()
                self.assertEqual(code, 1)
                self.assertIn(message, text)

    def test_layer_list_difference_fails(self):
        self.state(layers=LAYERS[:1] + ["Katman C"])
        code, text = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("check_portability: skipped but not expected: Katman C", text)
        self.assertIn("check_portability: expected to be skipped but was not: Katman B", text)

    def test_verified_count_difference_fails(self):
        self.state(verified=10)
        code, text = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("10 files verified, 11 expected", text)

    def test_tool_failure_or_missing_json_fails(self):
        for changes in ({"baseline_exit": 1}, {"baseline_text": "not json"}, {"portability_exit": 1}):
            self.state(**changes)
            with self.subTest(changes=changes):
                self.assertEqual(self.run_check()[0], 1)

    def test_unreadable_expectation_fails_before_running_tools(self):
        self.expected["format_version"] = 2
        self.write_expected()
        (self.root / "stub.json").unlink()
        code, text = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("could not be read", text)

    def test_compare_reports_each_difference(self):
        errors = scope.compare("x", ["a", "a", "c"], ["a", "b"])
        self.assertEqual(errors, ["x: duplicate entry a", "x: skipped but not expected: c", "x: expected to be skipped but was not: b"])


if __name__ == "__main__":
    unittest.main()
