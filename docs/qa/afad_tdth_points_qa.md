# AFAD TDTH Noktaları Teknik QA

## Durum

KABUL EDİLDİ

## Katman Özellikleri

- Kaynak: `data/processed/earthquake/canakkale_afad_tdth_points_32635.gpkg`
- CRS: `EPSG:32635` — **PASS**
- Feature sayısı: `106` — **PASS**
- Extent: `393532.7706612540059723,4377910.2416767897084355 : 538495.8532775089843199,4499934.9636228298768401`

## Geometri QA

- Boş geometriler: `0`
- Geçersiz geometriler: `0` — **PASS**
- Point dışı geometriler: `0`

## Koordinat Kapsamı

- Longitude min: `25.75`
- Longitude max: `27.45`
- Latitude min: `39.55`
- Latitude max: `40.65`

## Metodolojik Sınır

- Bu katman, Çanakkale AOI sınırına clip edilmiş point-based AFAD TDTH parametre subset katmanıdır.
- Henüz raster surface değildir.
- `pga_10pct` birincil sismik tehlike-destek değişkeni olarak ele alınır.
- Katman bina düzeyi deprem risk ürünü değildir.
