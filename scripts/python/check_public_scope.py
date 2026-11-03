#!/usr/bin/env python3
"""Run the public-source scope checks and require the recorded skip lists.

In a copy of the public source edition, analysis_baseline.py and
check_portability.py are run with --scope public-source. Each must exit 0,
and what each lists as skipped must equal config/public_scope_expected_v1.json
exactly: the 16 frozen data files and 30 local QGIS layers the edition omits.
A missing, extra or renamed entry fails. In a copy with the canonical data the
tools themselves fail by design; use their full scope there.

Exit codes: 0 both checks passed with the expected lists; 1 otherwise. Uses
only the standard library and never writes files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
EXPECTED = Path("config/public_scope_expected_v1.json")
PORTABILITY_SKIP = "ATLANDI (kamu kaynak sürümünde dağıtılmaz): "


def run(root: Path, script: str, *extra: str) -> subprocess.CompletedProcess:
    command = [sys.executable, "-B", str(root / "scripts/python" / script), "--check",
               "--scope", "public-source", "--project-root", str(root), *extra]
    return subprocess.run(command, cwd=str(root), capture_output=True, text=True, encoding="utf-8", timeout=600)


def compare(label: str, found: list[str], expected: list[str]) -> list[str]:
    errors = [f"{label}: duplicate entry {name}" for name in sorted({n for n in found if found.count(n) > 1})]
    errors += [f"{label}: skipped but not expected: {name}" for name in sorted(set(found) - set(expected))]
    errors += [f"{label}: expected to be skipped but was not: {name}" for name in sorted(set(expected) - set(found))]
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    errors = []
    try:
        expected = json.loads((root / EXPECTED).read_text(encoding="utf-8"))
        if expected.get("format_version") != 1:
            raise ValueError("unsupported format_version")
        baseline_expected = expected["analysis_baseline"]
        layers_expected = expected["check_portability"]["skipped_layers"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"ERROR: {EXPECTED} could not be read: {error}", file=sys.stderr)
        return 1

    baseline = run(root, "analysis_baseline.py", "--json")
    try:
        report = json.loads(baseline.stdout)
    except ValueError:
        report = {}
    if baseline.returncode != 0 or report.get("passed") is not True:
        errors.append(f"analysis_baseline.py --scope public-source exited {baseline.returncode}: "
                      + "; ".join(report.get("errors") or [baseline.stderr.strip() or "no JSON result"]))
    skipped = report.get("skipped_files") or []
    errors += compare("analysis_baseline", skipped, baseline_expected["skipped_files"])
    if report.get("verified_files") != baseline_expected["verified_files"]:
        errors.append(f"analysis_baseline: {report.get('verified_files')} files verified, "
                      f"{baseline_expected['verified_files']} expected")
    print(f"analysis_baseline.py --scope public-source: exit {baseline.returncode}; "
          f"{report.get('verified_files')} verified, {len(skipped)} skipped "
          f"(expected {baseline_expected['verified_files']} and {len(baseline_expected['skipped_files'])})")

    portability = run(root, "check_portability.py")
    lines = portability.stdout.splitlines()
    layers = [line[len(PORTABILITY_SKIP):] for line in lines if line.startswith(PORTABILITY_SKIP)]
    if portability.returncode != 0:
        errors.append(f"check_portability.py --scope public-source exited {portability.returncode}: "
                      + portability.stderr.strip())
    errors += compare("check_portability", layers, layers_expected)
    print(f"check_portability.py --scope public-source: exit {portability.returncode}; "
          f"{len(layers)} layers skipped (expected {len(layers_expected)})")
    if lines and not lines[-1].startswith(PORTABILITY_SKIP):
        print(f"  {lines[-1]}")

    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"Public-source scope: {'PASSED' if not errors else 'FAILED'}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
