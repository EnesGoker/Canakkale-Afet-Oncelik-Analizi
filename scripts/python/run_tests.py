#!/usr/bin/env python3
"""Run the unit tests for named tiers and check every count against the tier table.

--tiers names the test tiers this Python must provide, for example `stdlib` or
`stdlib,scientific,gdal`. config/test_tiers_v1.json is compared with the test
files first (tier_support.py --check). Each test module then runs in its own
process with this interpreter. Every test of a named tier must pass; every
test of any other tier must be skipped with a reason naming that tier. The
expected counts come only from the table, so a skipped tier is listed with its
reason and never counted as passed.

Exit codes: 0 every count matched; 1 a test failed or errored, or a count or
skip did not match the table; 2 the environment does not match --tiers (a
named tier cannot be imported, or a tier that was not named can be). Uses only
the standard library and writes nothing to the project.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parents[1]
sys.path.insert(0, str(SCRIPTS))
import tier_support  # noqa: E402

CHILD = r'''
import json, sys, unittest
scripts, result_path, module = sys.argv[1:]
sys.dont_write_bytecode = True
sys.path.insert(0, scripts)


class Recording(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rows = {}

    def record(self, test, outcome, reason=""):
        self.rows[test.id()] = {"id": test.id(), "outcome": outcome, "reason": reason}

    def addSuccess(self, test):
        super().addSuccess(test); self.record(test, "pass")

    def addFailure(self, test, err):
        super().addFailure(test, err); self.record(test, "failure")

    def addError(self, test, err):
        super().addError(test, err); self.record(test, "error")

    def addSkip(self, test, reason):
        super().addSkip(test, reason); self.record(test, "skip", reason)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err); self.record(test, "expected_failure")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test); self.record(test, "unexpected_success")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.record(test, "subtest_failure")


suite = unittest.defaultTestLoader.loadTestsFromName(module)
result = unittest.TextTestRunner(stream=sys.stdout, verbosity=1, resultclass=Recording).run(suite)
with open(result_path, "w", encoding="utf-8") as stream:
    json.dump({"tests_run": result.testsRun, "outcomes": list(result.rows.values())}, stream)
raise SystemExit(0 if result.wasSuccessful() else 1)
'''


def parse_tiers(value: str, table: dict) -> list[str]:
    names = [name.strip() for name in value.split(",") if name.strip()]
    unknown = [name for name in names if name not in table["tiers"]]
    if not names or unknown or len(set(names)) != len(names):
        raise ValueError(f"--tiers needs distinct names from: {', '.join(table['tiers'])}")
    return names


def environment_errors(table: dict, wanted: list[str]) -> list[str]:
    errors = []
    for name, tier in table["tiers"].items():
        missing = tier_support.missing_import(tuple(tier["imports"]))
        if name in wanted and missing is not None:
            errors.append(f"The {name} tier is required but {missing} is not importable with {sys.executable}")
        elif name not in wanted and missing is None:
            errors.append(f"The {name} tier is importable here but was not named in --tiers; "
                          "name it so that the expected counts are exact")
    return errors


def run_module(module: str, folder: Path, timeout: int) -> dict:
    result_path = folder / f"{module}.json"
    command = [sys.executable, "-B", "-c", CHILD, str(SCRIPTS), str(result_path), module]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    started = time.monotonic()
    try:
        process = subprocess.run(command, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=timeout)
        code, output = process.returncode, process.stdout + process.stderr
    except subprocess.TimeoutExpired as error:
        code, output = 124, f"Timed out after {timeout} s\n{error.stdout or ''}{error.stderr or ''}"
    record = {"module": module, "exit": code, "seconds": round(time.monotonic() - started, 2), "output": output}
    if result_path.exists():
        record.update(json.loads(result_path.read_text(encoding="utf-8")))
    else:
        record.update(tests_run=0, outcomes=[], result_missing=True)
    return record


def write_step_summary(lines: list[str]) -> None:
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with open(target, "a", encoding="utf-8") as stream:
            stream.write("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tiers", required=True, help="Comma-separated tiers this Python must provide")
    parser.add_argument("--timeout", type=int, default=1800, help="Seconds per test module (default 1800)")
    parser.add_argument("--json", type=Path, help="Also write the full result to this new file")
    args = parser.parse_args(argv)
    try:
        table = tier_support.load_table()
        wanted = parse_tiers(args.tiers, table)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.json is not None and args.json.exists():
        parser.error(f"--json target already exists: {args.json}")
    totals = tier_support.tier_totals(table)
    print(f"Python {sys.version.split()[0]} ({sys.executable}); tiers: {', '.join(wanted)}")
    errors = tier_support.check_table(table)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print("Test tier table: FAILED; no tests were run.")
        return 1
    print(f"Test tier table: {len(table['modules'])} modules, {sum(totals.values())} tests ("
          + ", ".join(f"{name} {count}" for name, count in totals.items()) + ")")
    errors = environment_errors(table, wanted)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print("Environment does not match --tiers; no tests were run.")
        return 2

    records = []
    with tempfile.TemporaryDirectory(prefix="canakkale-tests-") as folder:
        for module in tier_support.discover_modules():
            record = run_module(module, Path(folder), args.timeout)
            records.append(record)
            counts = {}
            for row in record["outcomes"]:
                counts[row["outcome"]] = counts.get(row["outcome"], 0) + 1
            detail = ", ".join(f"{count} {name}" for name, count in sorted(counts.items())) or "no outcomes"
            print(f"  {module} [{table['modules'][module]['tier']}]: {detail} (exit {record['exit']}, {record['seconds']} s)",
                  flush=True)
            if record["exit"] != 0 or record.get("result_missing"):
                print(record["output"].rstrip())

    outcomes = [row for record in records for row in record["outcomes"]]
    errors, summary = tier_support.verify_outcomes(table, outcomes, set(wanted))
    errors += [f"{record['module']}: process exited {record['exit']}" for record in records if record["exit"] != 0]
    errors += [f"{record['module']}: no result was recorded" for record in records if record.get("result_missing")]
    reasons = {}
    for row in outcomes:
        if row["outcome"] == "skip":
            module = row["id"].split(".", 1)[0]
            reasons.setdefault(table["modules"][module]["tier"], row["reason"])

    passed = sum(item["passed"] for item in summary.values())
    skipped = sum(item["skipped"] for item in summary.values())
    failed = len(outcomes) - passed - skipped
    lines = ["| Tier | Tests in table | Passed | Skipped | Note |", "|---|---:|---:|---:|---|"]
    print("Tier summary:")
    for name, item in summary.items():
        note = "required here" if name in wanted else f"SKIPPED: {reasons.get(name, 'no skip reason recorded')}"
        print(f"  {name}: {item['expected']} in table, {item['passed']} passed, {item['skipped']} skipped; {note}")
        lines.append(f"| {name} | {item['expected']} | {item['passed']} | {item['skipped']} | {note} |")
    state = "PASSED" if not errors else "FAILED"
    verdict = (f"Unit tests ({', '.join(wanted)}): {state}; {passed} passed, {skipped} skipped with a tier reason, "
               f"{failed} other outcomes, {sum(totals.values())} tests in the table.")
    for error in errors[:50]:
        print(f"ERROR: {error}", file=sys.stderr)
    print(verdict)
    write_step_summary([f"### Unit tests — Python {sys.version.split()[0]}, tiers: {', '.join(wanted)}", "",
                        *lines, "", verdict, *[f"- ERROR: {error}" for error in errors[:50]], ""])
    if args.json is not None:
        args.json.write_text(json.dumps({"passed": not errors, "python": sys.version.split()[0], "tiers": wanted,
                                         "summary": summary, "errors": errors,
                                         "modules": [{key: value for key, value in record.items() if key != "output"}
                                                     for record in records]},
                                        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
