[English](usage.md) | [Türkçe](usage.tr.md)

# Usage: QGIS, analysis environment, QA and tests

Run every command from the repository root. [Back to the README](../README.md) ·
[Documentation index](README.md).

## What runs from the repository alone

The source repository, `Code → Download ZIP`, the automatic `Source code (zip)`
and `git clone` do not contain the processed canonical analysis data, and no
download route for them is published
([publication scope](../PUBLICATION_STATUS.md)). Without them, these run:

- the unit tests ([Tests and continuous integration](#tests-and-continuous-integration));
- `python3 scripts/python/check_public_scope.py` (public-scope check);
- `python3 scripts/python/build_public_source_release.py --check` (selected source files).

The analyses, the full QA and the QGIS layers need the complete canonical data
folder. Reproducibility starts from the **processed canonical analysis data**;
rebuilding the preparation chain from large upstream raw datasets is outside
the scope of this project. The Word (`.docx`) file is the authoritative
editable report; the separate academic DOCX generator does not reproduce its
manually edited content.
[Canonical data policy](canonical_data_policy.md) ·
[Report generation scope](report_build_outputs.md).

## Open in QGIS and access the data

**A public Release package containing the full data has not been published.**
Downloading the QGIS file alone does not provide the project with its layers.

For users who already have the full canonical data folder, or once the
distribution conditions have been resolved and
`canakkale-disaster-priority-portable.zip` has been published:

1. Extract the full ZIP completely into a folder.
2. Keep the `qgis/`, `data/` and `outputs/` folders together inside
   `canakkale-disaster-priority/`.
3. Open `qgis/canakkale_disaster_priority.qgz` in QGIS.

QGIS **3.44.10** is the version used to save the project and the reference
for compatibility. Appearance in other versions needs separate checking.
Layer paths are relative, such as `../data/processed/...`; do not move the
QGIS file on its own. Opening the project in QGIS does not require a Python
virtual environment.

From the root of the full data folder, check files and paths with Python 3.10+:

```bash
python3 scripts/python/check_portability.py --check
```

For a full portable package that includes a manifest, also run:

```bash
python3 scripts/python/check_portability.py --check --verify-manifest
```

This tool requires no additional Python packages or QGIS. On Windows, use
`py -3` instead of `python3`. Reporting missing files is expected when checking
a source copy without the data; the source copy does not replace the full
data package.
[Portability](qgis_project_portability.md) ·
[Download and packaging guide](github_distribution.md).

To display the live CARTO basemap in QGIS, keep your own key in a private
file outside the project and use the launcher:

```bash
python3 scripts/python/open_qgis_with_carto.py --key-file "$HOME/.config/canakkale-disaster-priority/carto_basemap.key"
```

[Live basemap setup](carto_live_access.md). Saved maps need no key;
opening the project by double-clicking does not load your private key.

## Analysis environment and basic QA

Python **3.10+**, Bash, and GDAL/OGR **3.7+** form the basic environment for
the analysis and QA tools. Reading the QGIS project requires **PyQGIS**;
raster and calculation checks require **GDAL Python (`osgeo`) and NumPy**.

Full QA was verified with a separate **GDAL 3.12.3 / NumPy 2.4.4 (Accelerate)**
analysis environment and the **QGIS 3.44.15** project reader. GDAL 3.13.3's
default resampling differs from the recorded slope/flood recipes; the main MCDA remains unchanged.
[Runtime compatibility and scope](qa/runtime_compatibility.md).

Install the Python dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

`requirements.txt` does not install GDAL or QGIS; they must come from a
compatible GIS installation. Matplotlib is needed only to generate analysis
figures or maps, not to check the integrity of existing figures. On Windows,
Bash scripts also require a suitable Bash environment with access to the
GIS tools.

On macOS arm64, after creating the recorded environment, use this entry point:

```bash
python3 scripts/python/run_compatible_qa.py --gdal-prefix "$GIS_QA_PREFIX" --numpy-overlay "$GIS_QA_NUMPY"
```

[Environment setup and frozen profiles](qa/runtime_compatibility.md).
If compatible GIS tools are already selected, run basic QA from the full data root:

```bash
bash scripts/bash/run_canonical_qa.sh --check
```

QA checks CRS/grid/AOI consistency and scores for all 11 criteria, then
recalculates the baseline raw and normalized scores and classes in memory.
It verifies eight source-to-score equivalent recipes, the frozen 27-file
input version, correlation, scenario agreement, the weight perturbation and
the model variants. The report and sensitivity tables are regenerated from
the canonical data in a temporary sandbox and compared byte for byte with the
7 and 11 recorded files in `outputs/tables/`; a changed, missing, or extra file
fails the check. The generation time written into the two table manifests is
copied from the single `Üretim zamanı (UTC)` line of the recorded manifest, so
that value is reproduced, not verified: a changed time value still passes.
QGIS checks cover the layer/style locks and legend links in 14 layouts,
QGS/QGZ equivalence, and checksums for 28 map/atlas files.
These are technical consistency checks, not validation against observed disasters.

Exit codes: **0** means all required checks passed; **1** means a check
failed; **2** means a check could not be completed because of a missing
dependency. Live basemap access is not tested by offline QA. The recorded
land-cover boundary issue is reported as a warning.

<details>
<summary>GIS tools, additional checks, and generation scope</summary>

GDAL commands are resolved through `PATH`, `GDAL_BIN`, `QGIS_BIN`, or
tool-specific environment variables. `gdal_calc.py` and `gdal_proximity.py`
require compatible Python dependencies. QA also uses `unzip`, `xmllint`,
`perl`, and standard shell utilities.

QA looks for GIS Python dependencies in the Python interpreter under
`QGIS_BIN` or another suitable environment. If needed, select separate
interpreters with `QGIS_PYTHON_BIN` and `GDAL_PYTHON_BIN`. `PYTHON_BIN` is used
by the table/report tools and the QA launcher.

The table check can also be run separately; the main QA already includes it:

```bash
bash scripts/bash/generate_report_tables.sh --check
```

The following checks the separate DOCX generator. It creates a temporary
DOCX file and does not validate the final public Word/PDF report:

```bash
bash scripts/bash/build_academic_report.sh --check
```

DOCX is a separate output target that can be generated with
`build_academic_report.sh --build`. Pages archives and the separately generated
academic DOCX are excluded from public distribution.

Technical checks and generation of a local full-data package:

```bash
python3 scripts/python/build_portable_release.py --check
python3 scripts/python/build_portable_release.py --build
```

The ZIP and SHA-256 file are generated under `outputs/temp/releases/`,
which is excluded from Git. Generating a technical package does not publish
it or approve data distribution. The [distribution guide](github_distribution.md)
explains the scope and checks for the final public package.

[QA scope](qa/canonical_integrity_checks.md) ·
[Script guide](script_kullanim_ve_guvenlik_rehberi.md).

</details>

## Tests and continuous integration

The unit tests in `scripts/python/` build small temporary fixtures; none of
them reads the canonical data. [`config/test_tiers_v1.json`](../config/test_tiers_v1.json)
assigns each test module to one runtime tier and records its number of
tests; it is the only source of the counts below.

| Tier | Tests | Modules | Requires | In CI |
|---|---:|---:|---|---|
| `stdlib` | 192 | 15 | Python 3.10+ standard library | Ubuntu 24.04 and macOS arm64; Python 3.10, 3.12, 3.14 |
| `scientific` | 90 | 4 | NumPy, Matplotlib, and Pillow from `requirements.txt` | Ubuntu 24.04 and macOS arm64; Python 3.12, locked versions |
| `gdal` | 166 | 7 | GDAL Python (`osgeo`) and the `scientific` tier | macOS arm64 only; locked runtime (GDAL 3.12.3, NumPy 2.4.4 Accelerate) |
| `qgis` | 17 | 1 | PyQGIS 3.44 | Not run |
| **Total** | **465** | **27** | | |

When a tier's imports are missing, its tests are skipped one by one with a
reason that names the tier. A skip is never counted as a pass:
`run_tests.py` runs each module in its own process and compares the passed
and skipped counts with the table. If a named tier cannot be imported, or a
tier that was not named can be, it runs no tests and exits with code 2.

In a fresh clone or source ZIP, the Python standard library is enough for:

```bash
python3 scripts/python/tier_support.py --check
python3 scripts/python/run_tests.py --tiers stdlib
python3 scripts/python/check_public_scope.py
```

Each exits with code 0 and ends with:

- `Test tier table: PASSED; 27 modules, 465 tests (stdlib 192, scientific 90, gdal 166, qgis 17).`
- `Unit tests (stdlib): PASSED; 192 passed, 273 skipped with a tier reason, 0 other outcomes, 465 tests in the table.`
- `Public-source scope: PASSED`. Before this line, it reports
  `11 verified, 16 skipped` for `analysis_baseline.py` (the 16 frozen data
  files the edition omits) and `30 layers skipped` for `check_portability.py`
  (the omitted local QGIS layers). Both skip lists must equal
  [`config/public_scope_expected_v1.json`](../config/public_scope_expected_v1.json)
  entry for entry.

`python3 -m unittest discover -s scripts/python` ends with
`OK (skipped=273)` on a Python without the scientific packages; some tests
print the messages of the commands they exercise. Without
`--scope public-source`, `analysis_baseline.py --check` and
`check_portability.py --check` exit with code 1 in a source copy because the
canonical data are missing; this is expected.

After installing `requirements.txt`, use `--tiers stdlib,scientific`
(282 passed, 183 skipped). On macOS arm64, the locked GDAL runtime can be
built outside the project from the files in `config/qa_runtime_macos_arm64/`
and used for the first three tiers (448 passed, 17 skipped):

```bash
bash scripts/bash/setup_locked_gis_runtime.sh install "$HOME/.local/share/canakkale-qa/test-runtime"
bash scripts/bash/setup_locked_gis_runtime.sh run "$HOME/.local/share/canakkale-qa/test-runtime" python -B scripts/python/run_tests.py --tiers stdlib,scientific,gdal
```

[`.github/workflows/tests.yml`](../.github/workflows/tests.yml) runs on every
push and pull request:

- the `stdlib` tier, the tier table check, `check_public_scope.py`, and
  `build_public_source_release.py --check` on Ubuntu 24.04 and macOS arm64
  with Python 3.10, 3.12, and 3.14;
- the `scientific` tier on Python 3.12 with the versions in
  [`config/ci/scientific_constraints.txt`](../config/ci/scientific_constraints.txt),
  and a canary job on Python 3.14 with the newest versions
  `requirements.txt` allows; the canary may fail without failing the workflow;
- the `gdal` tier on macOS arm64 in the locked runtime above, cached by the
  hash of its lock files.

CI does **not** run the 17 `qgis` tests (no hosted runner provides
PyQGIS 3.44), the `gdal` tier on Linux (no lock file exists for it), or any
QA command that needs the canonical data: `run_canonical_qa.sh`,
`run_compatible_qa.py`, the full-scope `analysis_baseline.py` and
`check_portability.py`, and the table `--check` commands. A passing CI run
does not cover these checks.

## Interpreting the results

- The weights are reasoned educational choices, not the result of AHP,
  a formal expert survey, or calibration against observed losses.
- Alternative scenarios use their own observed min/max scale. Class changes
  reflect the combined effects of weights and rescaling.
- Some cells have source NoData converted to a zero score. A zero score or
  being below the high-priority classes in all three scenarios does not
  establish a measured absence of hazard.
- Correlation compares transformed criterion scores; it does not establish
  causality, optimal weights, or model accuracy.
- Traceability is limited for the external fault source and some historical
  transformation parameters. Uncertainty is recorded separately where the
  local dataset version is unknown.

[Method summary, known limitations](method_summary.md#10-known-limitations) ·
[Methodological and scientific limitations](methodology/scientific_limits.md) (Turkish).

## Basemap and re-exporting

With the full canonical data folder, viewing saved maps/atlas and running
offline QA requires neither an access key nor an internet connection.
Reloading the web basemap in QGIS requires internet access, and rendering the
CARTO basemap requires your own access key.

Exports read the key from `CARTO_BASEMAPS_API_KEY`; live QGIS access uses
the private key file described above. Public QGIS files contain no key.
Re-exporting uses the QGIS Python environment and a separate, empty output folder.
[Map generation guide](map_atlas_plan.md) ·
[Reading a key from a private file and generating outputs](qa/map_export_qa.md).
