# MCDA Sensitivity / Robustness Manifesti

Üretim zamanı (UTC): `2026-06-06T13:58:43+00:00`

Girdi seviyesi: canonical `data/processed` skor rasterları ve `config/mcda_weights.tsv`.

Kalıcı senaryo rasterı üretilmez; senaryo skorları geçici array hesaplarıdır.

## Dosyalar

- `outputs/tables/mcda_sensitivity_scenario_summary.csv`
- `outputs/tables/mcda_sensitivity_scenario_summary.md`
- `outputs/tables/mcda_sensitivity_interpretation.csv`
- `outputs/tables/mcda_sensitivity_interpretation.md`
- `outputs/tables/mcda_sensitivity_class_distribution.csv`
- `outputs/tables/mcda_sensitivity_class_distribution.md`
- `outputs/tables/mcda_sensitivity_top_districts.csv`
- `outputs/tables/mcda_sensitivity_top_districts.md`
- `outputs/tables/mcda_sensitivity_class_transition.csv`
- `outputs/tables/mcda_sensitivity_class_transition.md`
- `outputs/tables/mcda_sensitivity_manifest.md`

## QA Özeti

- Senaryo sayısı: `3`
- Yorum satırları: `3`
- Class dağılım satırları: `15`
- Top district satırları: `15`
- Class transition satırları: `75`

## Kısa Okuma

- `baseline`: canonical MCDA sınıf rasterı referans senaryodur.
- `earthquake-heavy`: yüksek+çok yüksek alan payı baseline'a göre +2.78 yüzde puan değişti; class agreement `84.08%`.
- `equal-weight`: yüksek+çok yüksek alan payı baseline'a göre +3.89 yüzde puan değişti; class agreement `72.59%`.
