# Flood RP100 Depth QA

## Durum

KABUL EDİLDİ

## Nihai Katman

Path:

`data/processed/flood/canakkale_flood_rp100_depth_32635.tif`

CRS:

`EPSG:32635 - WGS 84 / UTM Zone 35N`

Çözünürlük:

`90 m x 90 m`

NoData:

`-9999`

## Kaynak

JRC / CEMS flood depth raster: `Europe_RP100_filled_depth.tif`

## İşleme Özeti

1. Raw flood raster proje raw seceresine alınmıştır.
2. Raw raster Çanakkale AOI sınırına karşı görsel olarak kontrol edilmiştir.
3. Raster `canakkale_aoi_32635` sınırına clip edilmiştir.
4. Çıktı EPSG:4326 sisteminden EPSG:32635 sistemine reprojection işleminden geçirilmiştir.
5. `-9999` NoData olarak korunmuştur.
6. Çıktı resolution 90 m olarak ayarlanmıştır.

## QA Notları

- Çanakkale AOI görsel olarak kapsanmaktadır.
- NoData `-9999` olarak korunmuştur.
- `0` NoData olarak ele alınmaz.
- Teknik raster istatistikleri `docs/qa/flood_raster_stats.md` içinde dokümante edilmiştir.

## Metodolojik Sınır

Flood depth tehlike-destek input katmanıdır. Tek başına tam afet riski,
kırılganlık veya maruziyet çıktısı değildir.
