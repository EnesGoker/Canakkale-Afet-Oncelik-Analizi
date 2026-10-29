# HRL Tree Cover Density 2021 QA

## Durum

KABUL EDİLDİ

## Nihai Katman

Path:

`data/processed/landcover/canakkale_tree_cover_density_2021_32635.tif`

CRS:

`EPSG:32635 - WGS 84 / UTM Zone 35N`

Çözünürlük:

`10 m x 10 m`

NoData:

`255`

## Kaynak

Copernicus / CLMS HRL Tree Cover Density 2021 raster tile'ları.

## İşleme Özeti

1. Dokuz HRL Tree Cover Density tile proje raw seceresine alınmıştır.
2. Raw tile'lar Çanakkale AOI sınırına karşı görsel olarak kontrol edilmiştir.
3. EPSG:3035 sisteminde virtual raster mosaic oluşturulmuştur.
4. Mosaic `canakkale_aoi_32635` sınırına clip edilmiştir.
5. Çıktı EPSG:32635 sistemine reprojection işleminden geçirilmiştir.
6. Nearest Neighbor resampling kullanılmıştır.
7. `255` NoData olarak korunmuştur.
8. Değer bütünlüğü kontrol edilmiş; beklenmeyen değer kalmamıştır.

## QA Notları

- Çanakkale AOI kapsanmaktadır.
- Gökçeada ve Bozcaada dahildir.
- Değer aralığı geçerlidir: 0-100 ve 255 NoData.
- Önceki 254 NoData conversion sorunu `-srcnodata 255` kullanılarak düzeltilmiştir.
- Teknik value integrity `docs/qa/tree_cover_density_raster_stats.md` içinde dokümante edilmiştir.

## Metodolojik Sınır

Tree Cover Density vejetasyon yoğunluğu destek katmanıdır. Tek başına tehlike,
risk, kırılganlık veya maruziyet çıktısı değildir.
