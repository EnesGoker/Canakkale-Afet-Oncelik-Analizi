# AFAD TDTH Tablo Normalizasyon QA

## Durum

NORMALIZE EDİLDİ

## Girdi

- Raw Excel: `data/raw/earthquake/afad_tdth/afad_tdth_parametre_degerleri.xlsx`
- Sheet: `TDTH PARAMETRE DEĞERLERİ`
- Header satırları: `1-3`
- Data başlangıç satırı: `4`

## Çıktı

- CSV: `data/interim/earthquake/afad_tdth_parameters_4326.csv`
- Çıktı satır sayısı: `14036`
- Hatalı/atlanmış satır sayısı: `0`

## Koordinat QA

- Longitude min: `24.55`
- Longitude max: `45.95`
- Latitude min: `34.25`
- Latitude max: `42.95`
- Unique longitude count: `215`
- Unique latitude count: `88`
- Longitude step candidates: `[0.1]`
- Latitude step candidates: `[0.1]`

## 50 Yılda %10 Aşılma Olasılığı PGA QA

- Min PGA %10: `0.060820686`
- Max PGA %10: `0.8106634`
- Mean PGA %10: `0.2763521255786544`

## Kolon Eşlemesi

- `longitude`
- `latitude`
- `pga_2pct_50yr_g`
- `pga_10pct_50yr_g`
- `pga_50pct_50yr_g`
- `pga_68pct_50yr_g`
- `ss_2pct_50yr_g`
- `ss_10pct_50yr_g`
- `ss_50pct_50yr_g`
- `ss_68pct_50yr_g`
- `s1_2pct_50yr_g`
- `s1_10pct_50yr_g`
- `s1_50pct_50yr_g`
- `s1_68pct_50yr_g`
- `pgv_68pct_50yr_cm_s`
- `pgv_50pct_50yr_cm_s`
- `pgv_10pct_50yr_cm_s`
- `pgv_2pct_50yr_cm_s`

## Yorum

- AFAD TDTH Excel tablosu temiz bir koordinat CSV dosyasına normalize edilmiştir.
- Koordinatlar EPSG:4326 sisteminde longitude/latitude olarak ele alınır.
- `pga_10pct_50yr_g` birincil sismik tehlike-destek kolonudur.
- Bu CSV interim tabular dataset niteliğindedir; henüz processed GIS katmanı değildir.
