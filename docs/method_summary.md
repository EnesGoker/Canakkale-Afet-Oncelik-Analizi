# Method summary

A one-page English summary of the analysis. The detailed method, QA and source
documents are in Turkish; links point to them. [README](../README.md) ·
[Documentation index](README.md).

## 1. Purpose and scope

The project ranks **relative priority** for disaster preparedness in
Çanakkale province by combining hazard susceptibility, exposure and
accessibility criteria. It is a student GIS portfolio and an educational
preliminary assessment, **not** an official disaster risk, damage prediction or
boundary product. No institution endorses it.

## 2. Study area and grid

| Item | Value |
|---|---|
| Area | Çanakkale province, 12 districts |
| CRS | EPSG:32635 (WGS 84 / UTM zone 35N) |
| Grid | 100 m; 1,586 × 1,423 cells; **981,033 cells** inside the area of interest (AOI) |
| AOI area | 9,810.33 km² (from the raster cell area) |

Every criterion is aligned to the same template raster; results are compared
only inside the AOI.

## 3. Criteria, sources and transformations

`x` is the source value after alignment to the 100 m template; `d` is a
distance in metres. Scores are clipped to 0–1.

| Criterion | Source | Native resolution | Score | Weight |
|---|---|---|---|---:|
| Earthquake PGA (10% exceedance in 50 years) | AFAD TDTH point parameters, IDW surface by the author | 1,000 m | `clip((x − 0.2977) / 0.4381)` | 0.16 |
| Fault proximity | MTA active fault map data (2013/2014) | vector | `max(1 − d / 10 000, 0)` | 0.12 |
| Site condition (Vs30) | USGS Global Vs30 Mosaic | 30″ (≈ 1 km) | `clip((900 − Vs30) / (900 − 180.042))` | 0.08 |
| Population exposure | WorldPop Türkiye 2020 | 100 m | `log1p(count) / log1p(159.301)` | 0.14 |
| Building density | Microsoft building footprints + OSM gap fill | vector | footprint share of the cell | 0.10 |
| Flood | JRC/CEMS RP100 flood depth | 90 m | `clip(x / 10.0526)`; source NoData → 0 | 0.10 |
| Hydrography proximity | HydroRIVERS + OSM waterways | vector | `clip(1 − d / 1 000)` | 0.06 |
| Slope | Copernicus DEM GLO-30 | 30 m | `clip(x / 40.2023)` (degrees) | 0.08 |
| Land-cover sensitivity | ESA WorldCover 2021 | 10 m | class score table (0.05–0.60), then 100 m average | 0.06 |
| Tree cover | Copernicus CLMS HRL Tree Cover Density 2021 | 10 m | 100 m average of `x / 100` | 0.04 |
| Road access difficulty | OpenStreetMap roads | vector | `clip(d / 2 000)` | 0.06 |

The PGA and slope divisors were estimated from the existing data so that the
recorded scores are reproduced; eight source-to-score recipes match the saved
rasters in all 981,033 cells (largest absolute difference below 3 × 10⁻⁸).
[Criterion transformations](methodology/criterion_transformations.md) ·
[Source inventory](data_source_inventory.md).

## 4. Weights and blocks

The baseline weights ([`config/mcda_weights.tsv`](../config/mcda_weights.tsv))
are reasoned expert choices balanced in five blocks: earthquake (PGA, fault
proximity, site condition) 0.36, exposure (population, buildings) 0.24, water
and flood (flood, hydrography) 0.16, environment and terrain (slope, land
cover, tree cover) 0.18, accessibility (roads) 0.06. No AHP, survey or
calibration was used.
[Weight rationale](methodology/updated_mcda_methodology_note.md#6-ağırlıklandırma-stratejisi).

## 5. Aggregation, normalization and classes

The raw score is the weighted linear sum of the 11 scores (Float32, recorded
order). The canonical normalized score is `clip((raw − 0.029) / 0.473)` and is
shown in five equal-interval classes (thresholds 0.2, 0.4, 0.6, 0.8):

| Class | Cells | Area (km²) | Share of AOI |
|---|---:|---:|---:|
| 1 Very low | 114,283 | 1,142.83 | 11.65% |
| 2 Low | 483,129 | 4,831.29 | 49.25% |
| 3 Medium | 329,029 | 3,290.29 | 33.54% |
| 4 High | 53,893 | 538.93 | 5.49% |
| 5 Very high | 699 | 6.99 | 0.07% |

"High-plus" means classes 4 and 5 (545.92 km²). The 27 frozen inputs and
outputs of this baseline are pinned by SHA-256 in
[`config/analysis_baseline_v1.json`](../config/analysis_baseline_v1.json).
[Normalization](methodology/normalization_and_baseline.md).

## 6. Scenario agreement

Two alternative weightings (`earthquake-heavy`, `equal-weight`) are compared
with the baseline. Each uses its own observed min/max scale, so class changes
combine the weight change and the rescaling. **415.05 km²** (4.23% of the AOI)
is high-plus in all three scenarios and **820.96 km²** in only one or two
(map 13). [Scenario agreement](analysis/scenario_agreement.md).

## 7. Weight perturbation

Weights are sampled around the baseline from a Dirichlet distribution
(concentration κ × baseline weights; κ = 100 main, 50 and 200 as summary rows;
2,000 samples per κ, fixed seed). The main measure is rank based: in each
sample the cells holding the baseline high-plus cell count (top 5.565%) are
high-plus, so the area is constant by definition and the measure is location
stability. P(high-plus) is the share of samples in which a cell is high-plus
(map 14); it measures weight uncertainty only and is **not a disaster
probability**.

- κ = 100: P ≥ 0.9 covers **215.75 km²**, 39.52% of the baseline high-plus
  area; P ≥ 0.5 covers 498.47 km² (91.3%). κ = 50: 126.19 km²; κ = 200:
  296.12 km² at P ≥ 0.9.
- The baseline top-five districts keep the same set in 94.25% of κ = 100
  samples and the same order in 36.65%.
- One-at-a-time ±10% / ±20% changes: the lowest high-plus Jaccard values are
  hydrography 0.867, fault 0.886, roads 0.896, PGA 0.900, slope 0.917.

[Weight perturbation](analysis/weight_perturbation.md).

## 8. Model variants

Variants change the weights or merge criteria and use the same rank-based
measure (Jaccard similarity of the high-plus set with the baseline):

| Variant | High-plus Jaccard |
|---|---:|
| Flood weight 0, redistributed in proportion | 0.958 (very-high class 0.515; fixed scale 0.391) |
| Land cover and tree cover averaged, block 0.0625 (main) | 0.850 |
| Averaged, block 0.10 | 0.935 |
| Tree cover removed, redistributed | 0.676 |
| Kept separate, block 0.0625 | 0.814 |

Quantile and natural-break thresholds on the baseline score show the effect
of the threshold choice: class 5 becomes 1,962.06 km² and 939.03 km². They are
not proposed replacements for the canonical classes.
[Model variants](analysis/mcda_variants.md).

## 9. QA and reproducibility

- Full QA recomputes the baseline score and classes, the eight recipes,
  correlation, scenario agreement, perturbation and variants, the report
  tables (byte for byte) and the 14 QGIS layouts with 28 map/atlas checksums.
  It needs the canonical data and a locked GDAL 3.12.3 / NumPy 2.4.4 runtime.
- 465 unit tests in 27 modules use synthetic fixtures; CI runs the stdlib,
  scientific and gdal tiers (gdal on macOS arm64 only); the 17 qgis tests
  run locally only.
- From the repository alone, only the unit tests and the package and scope
  checks run. [Usage](usage.md) · [QA scope](qa/canonical_integrity_checks.md).

## 10. Known limitations

1. **Flood:** score 0 in 96.65% of the AOI (948,171 cells); source NoData is
   counted as 0 and its meaning could not be verified in the primary source.
   The 0.10 weight acts on 3.35% of the area.
2. **Very-high class depends on flood cells:** 396 of 699 very-high cells
   (56.7%) and 4,902 of 54,592 high-plus cells (9.0%) have a flood score
   above 0.
3. **Flood weight 0:** the high-plus set is kept (Jaccard 0.958), but half of
   the very-high class changes (0.515).
4. **Double counting:** land cover and tree cover correlate at r = 0.8152
   and carry 0.10 of the weight together.
5. **Class 5 is narrow:** 699 cells (0.07%); the threshold choice decides it
   (quantile 1,962.06 km², natural breaks 939.03 km²).
6. **Weights:** expert judgement; no AHP/consistency ratio, survey or
   calibration.
7. **P(high-plus)** is not a disaster probability; κ sets the width of the
   uncertainty (P ≥ 0.9: 126.19 / 215.75 / 296.12 km² at κ = 50 / 100 / 200).
8. **District order:** the top-five set holds in 94.25% of samples, the
   order in 36.65% (κ = 100; κ = 50: 87.05%).
9. **Gelibolu** moves between analyses: 2nd in the baseline, in the top
   three in 69.9% of κ = 100 samples, 5th with quantile and natural-break
   classes, 4th with flood weight 0 on the fixed scale.
10. **Sensitive criteria** (±20%): hydrography, fault, roads, PGA, slope
    (lowest Jaccard 0.867–0.917).
11. **Scenario rescaling:** alternative scenarios use their own min/max; class
    changes are the combined effect of weights and rescaling.
12. **Coarse sources** resampled to 100 m: PGA IDW 1,000 m, Vs30 ≈ 1 km,
    flood 90 m (apparent precision).
13. **Mixed data dates:** faults 2013/2014, population 2020, land cover 2021;
    six sources have no recorded year or extract date.
14. **Estimated parameters:** two scale parameters (PGA, slope) were estimated
    afterwards; the original rationale of the eight land-cover class scores is
    not recorded.
15. **Boundary effects:** the fault source was clipped to the AOI;
    5,272 land-cover cells outside the AOI do not enter the analysis.
16. **No validation:** not calibrated against observed losses or events; no
    building vulnerability, so the result is priority and exposure, not risk.
17. **Not reproducible from the repository alone:** the processed canonical
    data are not distributed and no download route is published.
18. **Data rights:** no written permission from AFAD or MTA (maps 01, 02, 05,
    13, 14); the JRC/CEMS licence (ODbL or CC BY 4.0), the regional Vs30
    components and the HydroSHEDS terms for static images could not be
    verified; OSM derived-database access remains open. Attribution is not
    permission.
19. **Environment:** full QA needs GDAL 3.12.3 (3.13.3 resamples slope and
    flood differently); the gdal tier runs in CI on macOS arm64 only and the
    qgis tier not at all.
20. **Map production:** the Open Sans font is not installed (fallback font);
    CARTO tile seams change a few pixels on re-export (maps 01/02: 400 and
    1,085 pixels; map 14: 2,251 pixels).

Planned later: AHP pairwise weights, external validation with event data,
the flood dataset version, combining the variants with the perturbation, and
district ranks by area share.
[Scientific limits](methodology/scientific_limits.md).

## 11. Sources and rights

[Source inventory](data_source_inventory.md) ·
[Data rights and distribution](data_rights_and_distribution.md) ·
[Static map notices](static_map_attributions.md) ·
[File scope](publication_file_scope.md) ·
[License scope](../LICENSE_SCOPE.md#license-scope-english).
