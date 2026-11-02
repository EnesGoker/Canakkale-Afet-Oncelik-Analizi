#!/usr/bin/env python3
"""Runtime tiers for the unit tests: one table, test-by-test skips, count checks.

config/test_tiers_v1.json is the only place that assigns a test module to a
tier and records how many tests it defines. A module whose tier needs packages
that are not importable here is skipped test by test, with the missing import
named. Availability is probed in a child process, so probing never imports
GDAL or QGIS into the test process. Runners compare what actually ran or was
skipped against the same table; a skip in a tier the runner requires is a
failure there, not a pass. --check compares the table with the test files on
disk and never runs a test.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
TABLE = ROOT / "config/test_tiers_v1.json"
SCRIPTS = Path(__file__).resolve().parent
MODULE_NAME = re.compile(r"test[a-z0-9_]*")
PROBE = ("import importlib, sys\n"
         "for name in sys.argv[1:]:\n"
         "    try:\n"
         "        importlib.import_module(name)\n"
         "    except Exception:\n"
         "        print(name)\n"
         "        raise SystemExit(3)\n")
_missing_cache: dict[tuple[str, ...], str | None] = {}


def _unique_keys(pairs):
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate key in the test tier table")
    return dict(pairs)


def load_table(path: Path = TABLE) -> dict:
    table = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_keys)
    if not isinstance(table, dict) or table.get("format_version") != 1:
        raise ValueError("Unsupported test tier table")
    tiers, modules = table.get("tiers"), table.get("modules")
    if not isinstance(tiers, dict) or not tiers or not isinstance(modules, dict) or not modules:
        raise ValueError("The test tier table needs non-empty tiers and modules")
    for name, tier in tiers.items():
        imports = tier.get("imports") if isinstance(tier, dict) else None
        if not isinstance(imports, list) or not all(isinstance(item, str) and item for item in imports):
            raise ValueError(f"Tier {name!r} needs a list of import names")
    for name, entry in modules.items():
        if (not MODULE_NAME.fullmatch(name) or not isinstance(entry, dict) or set(entry) != {"tier", "tests"}
                or entry["tier"] not in tiers or type(entry["tests"]) is not int or entry["tests"] < 1):
            raise ValueError(f"Invalid test tier table entry: {name}")
    return table


def tier_totals(table: dict) -> dict[str, int]:
    totals = {name: 0 for name in table["tiers"]}
    for entry in table["modules"].values():
        totals[entry["tier"]] += entry["tests"]
    return totals


def discover_modules(scripts_dir: Path = SCRIPTS) -> list[str]:
    """Module names that `unittest discover` loads with its default test*.py pattern."""
    return sorted(path.stem for path in Path(scripts_dir).glob("test*.py") if path.is_file())


def static_test_count(path: Path) -> int:
    """Count test methods the default loader collects, without importing the module."""
    tree = ast.parse(Path(path).read_bytes(), filename=str(path))
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

    def base_names(node):
        return [base.attr if isinstance(base, ast.Attribute) else getattr(base, "id", None) for base in node.bases]

    def is_test_case(node, seen=()):
        return any(name == "TestCase" or (name in classes and name not in seen
                   and is_test_case(classes[name], (*seen, name))) for name in base_names(node))

    def methods(node, seen=()):
        names = {item.name for item in node.body
                 if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test")}
        for name in base_names(node):
            if name in classes and name not in seen:
                names |= methods(classes[name], (*seen, name))
        return names

    return sum(len(methods(node)) for node in classes.values() if is_test_case(node))


def check_table(table: dict, scripts_dir: Path = SCRIPTS) -> list[str]:
    errors = []
    on_disk = set(discover_modules(scripts_dir))
    listed = set(table["modules"])
    errors += [f"Test module not in the tier table: {name}" for name in sorted(on_disk - listed)]
    errors += [f"Tier table lists a missing test module: {name}" for name in sorted(listed - on_disk)]
    for name in sorted(on_disk & listed):
        found, expected = static_test_count(Path(scripts_dir) / f"{name}.py"), table["modules"][name]["tests"]
        if found != expected:
            errors.append(f"{name}: {found} test methods on disk, {expected} in the tier table")
    return errors


def missing_import(imports: tuple[str, ...], python: str = sys.executable) -> str | None:
    """Return the first import a child Python cannot load, or None when all load."""
    key = (python, *imports)
    if key not in _missing_cache:
        missing = None
        if imports:
            try:
                process = subprocess.run([python, "-B", "-c", PROBE, *imports],
                                         capture_output=True, text=True, timeout=120)
                if process.returncode != 0:
                    missing = process.stdout.strip() or "the import probe"
            except (OSError, subprocess.TimeoutExpired):
                missing = "the import probe (it did not finish)"
        _missing_cache[key] = missing
    return _missing_cache[key]


@dataclass(frozen=True)
class Tier:
    module: str
    name: str
    missing: str | None

    @property
    def available(self) -> bool:
        return self.missing is None

    @property
    def reason(self) -> str:
        return (f"requires the '{self.name}' test tier; {self.missing} is not importable "
                "here (config/test_tiers_v1.json)")

    def skip_unless_available(self, cls):
        return unittest.skipUnless(self.available, self.reason)(cls)


def module_tier(module_file: str, table_path: Path = TABLE) -> Tier:
    name = Path(module_file).stem
    table = load_table(table_path)
    if name not in table["modules"]:
        raise LookupError(f"{name} is not registered in {Path(table_path).name}")
    tier = table["modules"][name]["tier"]
    return Tier(name, tier, missing_import(tuple(table["tiers"][tier]["imports"])))


def verify_outcomes(table: dict, outcomes: list[dict], available_tiers: set[str]) -> tuple[list[str], dict]:
    """Compare per-test outcomes with the table for an environment providing these tiers.

    Modules in an available tier must pass every test; modules in other tiers must
    skip every test with a reason naming their tier. Counts come from the table.
    """
    errors = [f"Unknown tier: {name}" for name in sorted(set(available_tiers) - set(table["tiers"]))]
    seen = {name: [] for name in table["modules"]}
    for row in outcomes:
        module = row["id"].split(".", 1)[0]
        if module not in seen:
            errors.append(f"Unexpected test outcome outside the tier table: {row['id']} ({row['outcome']})")
            continue
        seen[module].append(row)
    summary = {name: {"expected": 0, "passed": 0, "skipped": 0} for name in table["tiers"]}
    for module, rows in seen.items():
        tier, expected = table["modules"][module]["tier"], table["modules"][module]["tests"]
        summary[tier]["expected"] += expected
        if len(rows) != expected:
            errors.append(f"{module}: {len(rows)} test outcomes, {expected} in the tier table")
        wanted = "pass" if tier in available_tiers else "skip"
        for row in rows:
            if row["outcome"] in ("pass", "skip"):
                summary[tier]["passed" if row["outcome"] == "pass" else "skipped"] += 1
            if row["outcome"] != wanted:
                errors.append(f"{row['id']}: {row['outcome']}, expected {wanted} ({tier} tier)")
            elif wanted == "skip" and f"'{tier}' test tier" not in row.get("reason", ""):
                errors.append(f"{row['id']}: skip reason does not name the {tier} tier")
    return errors, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare the tier table with test files (default)")
    parser.add_argument("--table", type=Path, default=TABLE)
    parser.add_argument("--scripts-dir", type=Path, default=SCRIPTS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        table = load_table(args.table)
        errors = check_table(table, args.scripts_dir)
    except (OSError, ValueError, SyntaxError) as error:
        table, errors = None, [str(error)]
    totals = tier_totals(table) if table else {}
    result = {"passed": not errors, "errors": errors, "tier_tests": totals,
              "modules": len(table["modules"]) if table else 0, "tests": sum(totals.values())}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        state = "PASSED" if result["passed"] else "FAILED"
        detail = ", ".join(f"{name} {count}" for name, count in totals.items())
        print(f"Test tier table: {state}; {result['modules']} modules, {result['tests']} tests ({detail}).")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
