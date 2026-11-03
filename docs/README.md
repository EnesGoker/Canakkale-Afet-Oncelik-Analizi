# Belge dizini

[README (Türkçe)](../README.md) · [README (English)](../README.en.md) · [English index](#english).
**(EN)** işaretli belgeler İngilizcedir; diğerleri Türkçedir.

## Buradan başlayın

| Belge | İçerik |
|---|---|
| [Yöntem özeti](method_summary.md) · [Method summary (EN)](method_summary.en.md) | Tek sayfalık özet: kriterler, ağırlıklar, sınıflar, senaryolar, pertürbasyon, varyantlar, QA, bilinen sınırlılıklar |
| [Kullanım](usage.md) · [Usage (EN)](usage.en.md) | QGIS projesini açma, analiz ortamı, tam QA, testler ve CI, haritaları yeniden dışa aktarma |
| [Güncel MCDA yöntem notu](methodology/updated_mcda_methodology_note.md) | Tam yöntem, ağırlık gerekçesi, sınıflar |

## Analizler ve sonuç tabloları

Tablolar QGIS veya Python kurmadan okunabilir.

| Analiz | Belge | Veri |
|---|---|---|
| Ağırlık duyarlılığı (üç senaryo) | [Senaryo özeti](../outputs/tables/mcda_sensitivity_scenario_summary.md) · [Yorum](../outputs/tables/mcda_sensitivity_interpretation.md) | [Tablolar](../outputs/tables/) |
| Üç senaryonun mekânsal ortaklığı | [Senaryo ortaklığı](analysis/scenario_agreement.md) | [Alan sayımları](../outputs/analysis/scenario_agreement_v1/agreement_count_summary.csv) · [Senaryo karşılaştırması](../outputs/analysis/scenario_agreement_v1/scenario_high_area_comparison.csv) |
| 11 kriterin korelasyonu | [Kriter korelasyonu](analysis/criterion_correlation.md) | [11 × 11 CSV](../outputs/tables/criterion_correlation_v1/criterion_pearson_correlation.csv) |
| Ağırlık pertürbasyonu (Dirichlet, tek tek) | [Ağırlık pertürbasyonu](analysis/weight_perturbation.md) | [CSV klasörü](../outputs/analysis/weight_perturbation_v1/) |
| Model varyantları (taşkın, vejetasyon, eşikler) | [MCDA varyantları](analysis/mcda_variants.md) | [CSV klasörü](../outputs/analysis/mcda_variants_v1/) |
| İlçe ve sınıf alanı özetleri | [Rapor tablo çıktıları](report_table_outputs.md) | [Tablolar](../outputs/tables/) |

## Yöntem

[Kriter dönüşümleri](methodology/criterion_transformations.md) ·
[Normalizasyon ve baseline](methodology/normalization_and_baseline.md) ·
[MCDA yöntem notları](methodology/mcda_methodology_notes.md) ·
[Bilimsel sınırlılıklar](methodology/scientific_limits.md) ·
[CRS politikası](methodology/crs_policy.md) ·
[Fay verisi](methodology/fault_data_methodology_note.md) ·
[Nüfus verisi](methodology/population_data_methodology_note.md) ·
[Vs30 verisi](methodology/vs30_data_methodology_note.md).

## Veri kaynakları ve haklar

[Kaynak envanteri](data_source_inventory.md) ·
[Veri hakları ve dağıtım](data_rights_and_distribution.md) ·
[Statik harita bildirimleri](static_map_attributions.md) ·
[Yayın dosya kapsamı](publication_file_scope.md) ·
[Yayın durumu](../PUBLICATION_STATUS.md) ·
[Lisans kapsamı](../LICENSE_SCOPE.md) (Türkçe ve İngilizce) ·
[Veri manifesti](data_manifest.md) ·
[Kanonik veri politikası](canonical_data_policy.md).

## Haritalar ve QGIS

[Harita listesi ve atıf](../outputs/maps/README.md) ·
[Harita ve atlas planı](map_atlas_plan.md) ·
[Harita sembolojisi QA](map_symbology_qa.md) ·
[Harita dışa aktarma QA](qa/map_export_qa.md) ·
[QGIS projesinin taşınabilirliği](qgis_project_portability.md) ·
[Canlı CARTO altlığı](carto_live_access.md) ·
[Ara VRT politikası](interim_vrt_policy.md) ·
[Atlas notları](../outputs/atlas/README.md).

## QA ve testler

[Kanonik QA koşucusu](canonical_qa_runner.md) ·
[Kanonik bütünlük kontrolleri](qa/canonical_integrity_checks.md) ·
[Çalışma ortamı uyumluluğu](qa/runtime_compatibility.md) ·
[Betik rehberi](script_kullanim_ve_guvenlik_rehberi.md) ·
[Taşınabilir betik standardı](portable_script_standard.md) ·
[Test katmanı tablosu](../config/test_tiers_v1.json) ·
[Kaynak katmanı QA kayıtları](qa/) (veri kümesi başına QA ve istatistikler).

## Yayın ve paketleme

[GitHub dağıtımı](github_distribution.md) ·
[Rapor üretim çıktıları](report_build_outputs.md) ·
[Rapor görsel taslağı](report_asset_outline_lock.md) ·
[Rapor tablo çıktıları](report_table_outputs.md).

## Depo yapısı

```text
config/          Ağırlıklar, model tanımları, test katmanları ve donmuş girdi sürümü
.github/         Sürekli entegrasyon: birim testler ve kamu kaynak kontrolleri
scripts/         Python ve Bash analiz, QA ve paketleme araçları
qgis/            QGIS projesi ve harita düzenleri
data/            Yerel analiz verisi; dağıtılmaz (yalnız boş klasörler)
docs/            Yöntem, veri kaynakları, kullanım ve QA belgeleri
outputs/         Özet tablolar, analiz CSV'leri, 14 harita PNG'si ve köken kayıtları
```

## English

[README (English)](../README.en.md) · [README (Türkçe)](../README.md).
Documents marked **(TR)** are in Turkish.

### Start here

| Document | Content |
|---|---|
| [Method summary](method_summary.en.md) · [Yöntem özeti (TR)](method_summary.md) | One-page summary: criteria, weights, classes, scenarios, perturbation, variants, QA, known limitations |
| [Usage](usage.en.md) · [Kullanım (TR)](usage.md) | Opening the QGIS project, analysis environment, full QA, tests and CI, re-exporting maps |
| [Updated MCDA methodology note](methodology/updated_mcda_methodology_note.md) (TR) | Full method, weight rationale, classes |

### Analyses and result tables

The tables can be read without installing QGIS or Python.

| Analysis | Document | Data |
|---|---|---|
| Weight sensitivity (three scenarios) | [Scenario summary](../outputs/tables/mcda_sensitivity_scenario_summary.md) · [Interpretation](../outputs/tables/mcda_sensitivity_interpretation.md) (TR) | [Tables](../outputs/tables/) |
| Spatial agreement of three scenarios | [Scenario agreement](analysis/scenario_agreement.md) (TR) | [Area counts](../outputs/analysis/scenario_agreement_v1/agreement_count_summary.csv) · [Scenario comparison](../outputs/analysis/scenario_agreement_v1/scenario_high_area_comparison.csv) |
| Correlation of 11 criteria | [Criterion correlation](analysis/criterion_correlation.md) (TR) | [11 × 11 CSV](../outputs/tables/criterion_correlation_v1/criterion_pearson_correlation.csv) |
| Weight perturbation (Dirichlet, one-at-a-time) | [Weight perturbation](analysis/weight_perturbation.md) (TR) | [CSV folder](../outputs/analysis/weight_perturbation_v1/) |
| Model variants (flood, vegetation, thresholds) | [MCDA variants](analysis/mcda_variants.md) (TR) | [CSV folder](../outputs/analysis/mcda_variants_v1/) |
| District and class-area summaries | [Report table outputs](report_table_outputs.md) (TR) | [Tables](../outputs/tables/) |

### Methodology (TR)

[Criterion transformations](methodology/criterion_transformations.md) ·
[Normalization and baseline](methodology/normalization_and_baseline.md) ·
[MCDA method notes](methodology/mcda_methodology_notes.md) ·
[Scientific limits](methodology/scientific_limits.md) ·
[CRS policy](methodology/crs_policy.md) ·
[Fault data](methodology/fault_data_methodology_note.md) ·
[Population data](methodology/population_data_methodology_note.md) ·
[Vs30 data](methodology/vs30_data_methodology_note.md).

### Data sources and rights (TR)

[Source inventory](data_source_inventory.md) ·
[Data rights and distribution](data_rights_and_distribution.md) ·
[Static map notices](static_map_attributions.md) ·
[Publication file scope](publication_file_scope.md) ·
[Publication status](../PUBLICATION_STATUS.md) ·
[License scope](../LICENSE_SCOPE.md#license-scope-english) (TR and English) ·
[Data manifest](data_manifest.md) ·
[Canonical data policy](canonical_data_policy.md).

### Maps and QGIS (TR)

[Map list and attribution](../outputs/maps/README.md) ·
[Map and atlas plan](map_atlas_plan.md) ·
[Map symbology QA](map_symbology_qa.md) ·
[Map export QA](qa/map_export_qa.md) ·
[QGIS project portability](qgis_project_portability.md) ·
[Live CARTO basemap](carto_live_access.md) ·
[Interim VRT policy](interim_vrt_policy.md) ·
[Atlas notes](../outputs/atlas/README.md).

### QA and tests (TR)

[Canonical QA runner](canonical_qa_runner.md) ·
[Canonical integrity checks](qa/canonical_integrity_checks.md) ·
[Runtime compatibility](qa/runtime_compatibility.md) ·
[Script guide](script_kullanim_ve_guvenlik_rehberi.md) ·
[Portable script standard](portable_script_standard.md) ·
[Test tier table](../config/test_tiers_v1.json) ·
[Source-layer QA records](qa/) (per-dataset QA and statistics).

### Publication and packaging (TR)

[GitHub distribution](github_distribution.md) ·
[Report build outputs](report_build_outputs.md) ·
[Report asset outline](report_asset_outline_lock.md) ·
[Report table outputs](report_table_outputs.md).

### Repository structure

```text
config/          Weights, model definitions, test tiers and the frozen input version
.github/         Continuous integration: unit tests and public-source checks
scripts/         Python and Bash analysis, QA and packaging tools
qgis/            QGIS project and map layouts
data/            Local analysis data; not distributed (empty folders only)
docs/            Method, data sources, usage and QA documentation
outputs/         Aggregate tables, analysis CSVs, the 14 map PNGs and provenance
```
