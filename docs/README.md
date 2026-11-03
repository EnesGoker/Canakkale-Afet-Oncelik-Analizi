# Documentation index

[README (English)](../README.md) · [README (Türkçe)](../README.tr.md).
Documents marked **(TR)** are in Turkish.

## Start here

| Document | Content |
|---|---|
| [Method summary](method_summary.md) | One-page English summary: criteria, weights, classes, scenarios, perturbation, variants, QA, known limitations |
| [Usage](usage.md) · [Kullanım (TR)](usage.tr.md) | Opening the QGIS project, analysis environment, full QA, tests and CI, re-exporting maps |
| [Updated MCDA methodology note](methodology/updated_mcda_methodology_note.md) (TR) | Full method, weight rationale, classes |

## Analyses and result tables

The tables can be read without installing QGIS or Python.

| Analysis | Document | Data |
|---|---|---|
| Weight sensitivity (three scenarios) | [Scenario summary](../outputs/tables/mcda_sensitivity_scenario_summary.md) · [Interpretation](../outputs/tables/mcda_sensitivity_interpretation.md) (TR) | [Tables](../outputs/tables/) |
| Spatial agreement of three scenarios | [Scenario agreement](analysis/scenario_agreement.md) (TR) | [Area counts](../outputs/analysis/scenario_agreement_v1/agreement_count_summary.csv) · [Scenario comparison](../outputs/analysis/scenario_agreement_v1/scenario_high_area_comparison.csv) |
| Correlation of 11 criteria | [Criterion correlation](analysis/criterion_correlation.md) (TR) | [11 × 11 CSV](../outputs/tables/criterion_correlation_v1/criterion_pearson_correlation.csv) |
| Weight perturbation (Dirichlet, one-at-a-time) | [Weight perturbation](analysis/weight_perturbation.md) (TR) | [CSV folder](../outputs/analysis/weight_perturbation_v1/) |
| Model variants (flood, vegetation, thresholds) | [MCDA variants](analysis/mcda_variants.md) (TR) | [CSV folder](../outputs/analysis/mcda_variants_v1/) |
| District and class-area summaries | [Report table outputs](report_table_outputs.md) (TR) | [Tables](../outputs/tables/) |

## Methodology (TR)

[Criterion transformations](methodology/criterion_transformations.md) ·
[Normalization and baseline](methodology/normalization_and_baseline.md) ·
[MCDA method notes](methodology/mcda_methodology_notes.md) ·
[Scientific limits](methodology/scientific_limits.md) ·
[CRS policy](methodology/crs_policy.md) ·
[Fault data](methodology/fault_data_methodology_note.md) ·
[Population data](methodology/population_data_methodology_note.md) ·
[Vs30 data](methodology/vs30_data_methodology_note.md).

## Data sources and rights (TR)

[Source inventory](data_source_inventory.md) ·
[Data rights and distribution](data_rights_and_distribution.md) ·
[Static map notices](static_map_attributions.md) ·
[Publication file scope](publication_file_scope.md) ·
[Publication status](../PUBLICATION_STATUS.md) ·
[License scope](../LICENSE_SCOPE.md) (TR and English) ·
[Data manifest](data_manifest.md) ·
[Canonical data policy](canonical_data_policy.md).

## Maps and QGIS (TR)

[Map list and attribution](../outputs/maps/README.md) ·
[Map and atlas plan](map_atlas_plan.md) ·
[Map symbology QA](map_symbology_qa.md) ·
[Map export QA](qa/map_export_qa.md) ·
[QGIS project portability](qgis_project_portability.md) ·
[Live CARTO basemap](carto_live_access.md) ·
[Interim VRT policy](interim_vrt_policy.md) ·
[Atlas notes](../outputs/atlas/README.md).

## QA and tests (TR)

[Canonical QA runner](canonical_qa_runner.md) ·
[Canonical integrity checks](qa/canonical_integrity_checks.md) ·
[Runtime compatibility](qa/runtime_compatibility.md) ·
[Script guide](script_kullanim_ve_guvenlik_rehberi.md) ·
[Portable script standard](portable_script_standard.md) ·
[Test tier table](../config/test_tiers_v1.json) ·
[Source-layer QA records](qa/) (per-dataset QA and statistics).

## Publication and packaging (TR)

[GitHub distribution](github_distribution.md) ·
[Report build outputs](report_build_outputs.md) ·
[Report asset outline](report_asset_outline_lock.md) ·
[Report table outputs](report_table_outputs.md).

## Repository structure

```text
config/          Weights, model definitions, test tiers and the frozen input version
.github/         Continuous integration: unit tests and public-source checks
scripts/         Python and Bash analysis, QA and packaging tools
qgis/            QGIS project and map layouts
data/            Local analysis data; not distributed (empty folders only)
docs/            Method, data sources, usage and QA documentation
outputs/         Aggregate tables, analysis CSVs, the 14 map PNGs and provenance
```
