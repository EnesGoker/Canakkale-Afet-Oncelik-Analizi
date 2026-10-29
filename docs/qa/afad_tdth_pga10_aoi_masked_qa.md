# AFAD TDTH PGA %10 AOI Maskelenmiş Raster QA

## Durum

KABUL EDİLDİ

## Amaç

- Özgün AFAD TDTH PGA10 rasterı analitik kaynak raster olarak korunur.
- Bu AOI maskelenmiş raster, temiz harita gösterimi ve yalnızca Çanakkale analizi için kullanılır.
- Mask işlemi Çanakkale AOI dışındaki görsel raster bloklarını kaldırır.

## Girdiler

- Girdi raster: `data/processed/earthquake/canakkale_afad_tdth_pga10_32635.tif`
- AOI mask: `data/processed/aoi/canakkale_aoi_32635.gpkg`

## Çıktı

- Çıktı raster: `data/processed/earthquake/canakkale_afad_tdth_pga10_aoi_masked_32635.tif`
- CRS: `EPSG:32635` — **PASS**
- Raster boyutu: `159 x 143` pixel
- Pixel size X: `1000.0`
- Pixel size Y: `1000.0`
- NoData değeri: `-9999.0`

## Değer Bütünlüğü

- Toplam hücre: `22737`
- Geçerli hücre: `9822`
- NoData hücreleri: `12915`
- Minimum PGA: `0.29068878293037415`
- Maximum PGA: `0.7565720081329346`
- Mean PGA: `0.3745345827537213`
- Standard deviation: `0.06239595742772233`
- Negatif geçerli hücre: `0` — **PASS**
- 1.5g üzerindeki değerler: `0` — **PASS**

## Metodolojik Not

- Bu yeni bir tehlike modeli değildir; türetilmiş AFAD TDTH PGA10 rasterının AOI maskelenmiş gösterim/analiz versiyonudur.
- PGA değerleri 50 yılda %10 aşılma olasılığını temsil eder.
- Katman sismik tehlike-destek yüzeyidir; bina düzeyi deprem risk ürünü değildir.
- Özgün kaynak raster ve AFAD TDTH nokta katmanı izlenebilirlik için korunur.
