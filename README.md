[English](README.md) | [Türkçe](README.tr.md)

# Çanakkale Multi-Criteria Disaster Susceptibility and Spatial Priority Analysis

A GIS project that combines disaster susceptibility, population and building
exposure, and accessibility conditions in Çanakkale province through
**multi-criteria decision analysis (MCDA) with 11 criteria**. It identifies
relative priority areas on a **shared 100 m grid** and compares results across
12 districts and three weighting scenarios.

**Project author: Enes Göker.** Developed for a Geographic Information Systems
course, the project is presented as a student portfolio with QGIS maps,
Python/Bash analysis tools, calculation checks, and methodology documentation.

**Public source edition:** analysis and QA code, model definitions, methodology,
aggregate result tables, and a QGIS project template. Canonical datasets, map
images, the atlas, and the Word/PDF report are retained in the full local
working version and are not included in this edition.
[Files and distribution scope](docs/publication_file_scope.md).

This educational preliminary assessment is not an official disaster risk,
damage prediction, or boundary product.

## Key findings

- **415.05 km²** has high or very high priority in all three scenarios,
  representing **4.23% of the analysis area of interest (AOI)**.
- **820.96 km²** has high priority in only one or two scenarios;
  membership of the high-priority classes changes with the selected scenario.
- The Pearson correlation between the land-cover and tree-cover
  **criterion scores** is **r = 0.8152**, providing a numerical basis for
  discussing information shared by the two indicators.

For the first two findings, “high” includes **classes 4 and 5**.
The scenario comparison captures the combined effects of changing weights
and scenario-specific normalization. These figures are not disaster
probabilities or model accuracy rates.
[Scenario agreement](docs/analysis/scenario_agreement.md) ·
[Correlation interpretation](docs/analysis/criterion_correlation.md).

## Explore the project

The tables and methodology below can be reviewed without installing QGIS
or Python. Detailed documentation is in Turkish; the
[Turkish README](README.tr.md) is also available.

| Content | Link |
|---|---|
| District and class-area summaries | [Tables](outputs/tables/) |
| Weight sensitivity | [Scenario summary](outputs/tables/mcda_sensitivity_scenario_summary.md) · [Interpretation](outputs/tables/mcda_sensitivity_interpretation.md) |
| Correlation of 11 criteria | [Method and interpretation](docs/analysis/criterion_correlation.md) · [11 × 11 CSV](outputs/tables/criterion_correlation_v1/criterion_pearson_correlation.csv) |
| Spatial agreement across three scenarios | [Method and interpretation](docs/analysis/scenario_agreement.md) · [Area counts](outputs/analysis/scenario_agreement_v1/agreement_count_summary.csv) · [Scenario comparison](outputs/analysis/scenario_agreement_v1/scenario_high_area_comparison.csv) |
| QGIS project template | [QGZ](qgis/canakkale_disaster_priority.qgz) — canonical analysis data must be supplied separately |
| Data sources and distribution | [Source inventory](docs/data_source_inventory.md) · [File scope](docs/publication_file_scope.md) |

The full local working version contains 13 geographic maps, one correlation
figure, a 13-page atlas, the reviewed Word report, and its 18-page PDF. They are
not downloadable assets of this source edition. Future static-map sharing
uses the [source notices and attribution requirements](docs/static_map_attributions.md).

The source package can be checked using the Python standard library:

```bash
python3 scripts/python/build_public_source_release.py --check
```

This validates the selected source files and does not run the GIS analysis.
The data-dependent commands below require the complete canonical data folder.
[Tests and continuous integration](#tests-and-continuous-integration) lists
what runs without the data.

## My contribution

- I brought together GIS layers from institutions and open data sources
  and prepared them for analysis.
- I built the MCDA model combining 11 criteria on a shared 100 m grid and
  documented the score transformations, weight rationale, and methodological
  limitations.
- I prepared the QGIS layers and map layouts and presented the results
  through district tables, a map atlas, and the course report.

## Technical skills developed

- **Data alignment:** I learned to use a shared CRS, grid, and AOI when
  comparing layers with different resolutions and coordinate systems, and
  to distinguish NoData from a zero score when interpreting results.
- **Model interpretation:** I examined how weights and normalization affect
  priority classes through scenario comparisons and learned to assess
  information shared by criteria using correlation.
- **Portable QGIS projects:** I combined relative paths with layer/style
  management to address opening the project in another folder and keeping
  map layouts consistent.
- **Calculation checks:** I learned to detect invalid inputs using test
  cases with missing files, incorrect CRS/grids, NaN, and out-of-range scores,
  and to compare score and class calculations against saved outputs.
- **Traceability and sharing:** I learned to track input/output versions
  using manifests and SHA-256, and to document source attribution, code
  licensing, and data sharing conditions separately.

## How the analysis works

1. Processed criterion layers are brought together in a shared CRS, grid,
   and study area.
2. Each criterion is converted into an analysis score using documented
   transformations.
3. Scores are combined linearly using the recorded weights; the normalized
   priority score is displayed in five relative classes.
4. The `baseline`, `earthquake-heavy`, and `equal-weight` scenarios are compared.
5. Pearson correlation describes how criterion scores vary together;
   spatial agreement analysis shows which high-priority areas are shared
   across scenarios and which change.
6. QA compares calculations against existing outputs; district summaries,
   maps, and the report make the results available for review.

| Component | Description |
|---|---|
| Study area | Çanakkale province and 12 districts |
| CRS | EPSG:32635 — WGS 84 / UTM Zone 35N |
| Grid | 100 m; raster of 1,586 × 1,423 cells; 981,033 cells within the AOI |
| Analysis AOI area | 9,810.33 km², calculated from raster cell area |
| Criteria | PGA, fault proximity, VS30, population, building density, flooding, hydrography, slope, land cover, tree cover, road access |
| Main model | Weighted linear combination; five relative priority classes |
| Tools | QGIS, GDAL/OGR, Python, Bash |

**Methodology resources:**
[Weights](config/mcda_weights.tsv) ·
[Method and weight rationale](docs/methodology/updated_mcda_methodology_note.md) ·
[Criterion transformations](docs/methodology/criterion_transformations.md) ·
[Normalization and input version](docs/methodology/normalization_and_baseline.md) ·
[Data sources](docs/data_source_inventory.md) ·
[Sensitivity interpretation](outputs/tables/mcda_sensitivity_interpretation.md).

Reproducibility starts from the **processed canonical analysis data**.
Rebuilding the entire preparation chain from large upstream raw datasets
is outside the scope of this project. The Word (`.docx`) file is the authoritative editable report.
The separate academic DOCX generator does not reproduce its manually edited content.
[Canonical data policy](docs/canonical_data_policy.md) ·
[Report generation scope](docs/report_build_outputs.md).

## Repository structure

```text
config/          Weights, model definitions, and frozen input version
.github/         Continuous integration: unit tests and public-source checks
scripts/         Python and Bash analysis, QA, and packaging tools
qgis/            QGIS project and map layouts
data/            Local analysis data; large datasets are excluded from Git
docs/            Methodology, data sources, setup, and QA documentation
outputs/         Selected aggregate tables and provenance; full visuals stay local
```

## Open in QGIS and access the data

**A public Release package containing the full data has not been published yet.**
The source repository, `Code → Download ZIP`, automatic `Source code (zip)`,
and `git clone` do not include the large analysis datasets. Downloading the
QGIS file alone does not provide the full project with all its layers.
[Publication scope and pending data distribution decisions](PUBLICATION_STATUS.md).

For users who already have the full canonical data folder, or once the
distribution conditions have been resolved and
`canakkale-disaster-priority-portable.zip` has been published:

1. Extract the full ZIP completely into a folder.
2. Keep the `qgis/`, `data/`, and `outputs/` folders together inside
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
[Portability](docs/qgis_project_portability.md) ·
[Download and packaging guide](docs/github_distribution.md).

To display the live CARTO basemap in QGIS, keep your own key in a private
file outside the project and use the launcher:

```bash
python3 scripts/python/open_qgis_with_carto.py --key-file "$HOME/.config/canakkale-disaster-priority/carto_basemap.key"
```

[Live basemap setup](docs/carto_live_access.md). Saved maps/PDFs need no key;
opening the project by double-clicking does not load your private key.

## Analysis environment and basic QA

Python **3.10+**, Bash, and GDAL/OGR **3.7+** form the basic environment for
the analysis and QA tools. Reading the QGIS project requires **PyQGIS**;
raster and calculation checks require **GDAL Python (`osgeo`) and NumPy**.

Full QA was verified with a separate **GDAL 3.12.3 / NumPy 2.4.4 (Accelerate)**
analysis environment and the **QGIS 3.44.15** project reader. GDAL 3.13.3's
default resampling differs from the saved slope/flood recipes; the main MCDA remains unchanged.
[Runtime compatibility and scope](docs/qa/runtime_compatibility.md).

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

[Environment setup and frozen profiles](docs/qa/runtime_compatibility.md).
If compatible GIS tools are already selected, run basic QA from the full data root:

```bash
bash scripts/bash/run_canonical_qa.sh --check
```

QA checks CRS/grid/AOI consistency and scores for all 11 criteria, then
recalculates the baseline raw and normalized scores and classes in memory.
It verifies eight source-to-score equivalent recipes, the frozen 27-file
input version, correlation, and scenario agreement. The report and
sensitivity tables are regenerated from the canonical data in a temporary
sandbox and compared byte for byte with the 7 and 11 recorded files in
`outputs/tables/`; a changed, missing, or extra file fails the check. The
generation time written into the two table manifests is copied from the
single `Üretim zamanı (UTC)` line of the recorded manifest, so that value is
reproduced, not verified: a changed time value still passes.
QGIS checks cover the layer/style locks and legend
links in 13 layouts, QGS/QGZ equivalence, and checksums for 27 map/atlas files.
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
`build_academic_report.sh --build`. Pages archives and the separately generated academic DOCX are excluded
from public distribution.

Technical checks and generation of a local full-data package:

```bash
python3 scripts/python/build_portable_release.py --check
python3 scripts/python/build_portable_release.py --build
```

The ZIP and SHA-256 file are generated under `outputs/temp/releases/`,
which is excluded from Git. Generating a technical package does not publish
it or approve data distribution. The [distribution guide](docs/github_distribution.md)
explains the scope and checks for the final public package.

[QA scope](docs/qa/canonical_integrity_checks.md) ·
[Script guide](docs/script_kullanim_ve_guvenlik_rehberi.md).

</details>

## Tests and continuous integration

The unit tests in `scripts/python/` build small temporary fixtures; none of
them reads the canonical data. [`config/test_tiers_v1.json`](config/test_tiers_v1.json)
assigns each test module to one runtime tier and records its number of
tests; it is the only source of the counts below.

| Tier | Tests | Modules | Requires | In CI |
|---|---:|---:|---|---|
| `stdlib` | 143 | 12 | Python 3.10+ standard library | Ubuntu 24.04 and macOS arm64; Python 3.10, 3.12, 3.14 |
| `scientific` | 54 | 3 | NumPy, Matplotlib, and Pillow from `requirements.txt` | Ubuntu 24.04 and macOS arm64; Python 3.12, locked versions |
| `gdal` | 111 | 4 | GDAL Python (`osgeo`) and the `scientific` tier | macOS arm64 only; locked runtime (GDAL 3.12.3, NumPy 2.4.4 Accelerate) |
| `qgis` | 17 | 1 | PyQGIS 3.44 | Not run |
| **Total** | **325** | **20** | | |

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

- `Test tier table: PASSED; 20 modules, 325 tests (stdlib 143, scientific 54, gdal 111, qgis 17).`
- `Unit tests (stdlib): PASSED; 143 passed, 182 skipped with a tier reason, 0 other outcomes, 325 tests in the table.`
- `Public-source scope: PASSED`. Before this line, it reports
  `11 verified, 16 skipped` for `analysis_baseline.py` (the 16 frozen data
  files the edition omits) and `28 layers skipped` for `check_portability.py`
  (the omitted local QGIS layers). Both skip lists must equal
  [`config/public_scope_expected_v1.json`](config/public_scope_expected_v1.json)
  entry for entry.

`python3 -m unittest discover -s scripts/python` ends with
`OK (skipped=182)` on a Python without the scientific packages; some tests
print the messages of the commands they exercise. Without
`--scope public-source`, `analysis_baseline.py --check` and
`check_portability.py --check` exit with code 1 in a source copy because the
canonical data are missing; this is expected.

After installing `requirements.txt`, use `--tiers stdlib,scientific`
(197 passed, 128 skipped). On macOS arm64, the locked GDAL runtime can be
built outside the project from the files in `config/qa_runtime_macos_arm64/`
and used for the first three tiers (308 passed, 17 skipped):

```bash
bash scripts/bash/setup_locked_gis_runtime.sh install "$HOME/.local/share/canakkale-qa/test-runtime"
bash scripts/bash/setup_locked_gis_runtime.sh run "$HOME/.local/share/canakkale-qa/test-runtime" python -B scripts/python/run_tests.py --tiers stdlib,scientific,gdal
```

[`.github/workflows/tests.yml`](.github/workflows/tests.yml) runs on every
push and pull request:

- the `stdlib` tier, the tier table check, `check_public_scope.py`, and
  `build_public_source_release.py --check` on Ubuntu 24.04 and macOS arm64
  with Python 3.10, 3.12, and 3.14;
- the `scientific` tier on Python 3.12 with the versions in
  [`config/ci/scientific_constraints.txt`](config/ci/scientific_constraints.txt),
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

[Methodological and scientific limitations](docs/methodology/scientific_limits.md).

## Basemap and re-exporting

With the full canonical data folder, viewing saved maps/atlas and running
offline QA requires neither an access key nor an internet connection. Reloading the web basemap in
QGIS requires internet access, and rendering the CARTO basemap requires
your own access key.

Exports read the key from `CARTO_BASEMAPS_API_KEY`; live QGIS access uses
the private key file described above. Public QGIS files contain no key.
Re-exporting uses the QGIS Python environment and a separate, empty output folder.
[Map generation guide](docs/map_atlas_plan.md) ·
[Reading a key from a private file and generating outputs](docs/qa/map_export_qa.md).

## License and sources

The original `scripts/` software is [MIT-licensed](LICENSE).
A [separate license scope](LICENSE_SCOPE.md) applies to the report,
documentation, maps, model definitions, and data; they are not all MIT-licensed.
Data attribution is not the same as permission to redistribute.

[Source inventory](docs/data_source_inventory.md) ·
[Data rights and distribution record](docs/data_rights_and_distribution.md) ·
[Publication file list](PUBLICATION_STATUS.md) ·
[Map attribution](outputs/maps/README.md) ·
[Atlas notes](outputs/atlas/README.md).
