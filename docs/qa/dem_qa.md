# DEM ve Eğim QA

## Durum

KABUL EDİLDİ

## Nihai Katmanlar

### DEM

Path:

`data/processed/dem/canakkale_dem_32635.tif`

CRS:

`EPSG:32635 - WGS 84 / UTM Zone 35N`

Kaynak:

`Copernicus DEM GLO-30`

### Eğim

Path:

`data/processed/dem/canakkale_slope_degrees_32635.tif`

CRS:

`EPSG:32635 - WGS 84 / UTM Zone 35N`

Birim:

`degrees`

## Kaynak Veri

DEM seceresinde kullanılan raw DEM tile grubu:

`data/raw/dem/copernicus_glo30`

Tile sayısı:

`6`

## Interim Veri

Intermediate mosaic kayıtları şu klasör altında tutulur:

`data/interim/dem`

Dosyalar:

- `canakkale_dem_mosaic_4326.vrt`
- `canakkale_dem_mosaic_32635.tif`

## İşleme Özeti

1. Altı Copernicus DEM GLO-30 raster tile proje raw data seceresine alınmıştır.
2. Tile'lar QGIS içinde Çanakkale AOI sınırına karşı görsel olarak kontrol edilmiştir.
3. Altı raw DEM tile üzerinden virtual raster mosaic oluşturulmuştur.
4. DEM mosaic EPSG:32635 sistemine reprojection işleminden geçirilmiştir.
5. EPSG:32635 DEM mosaic `canakkale_aoi_32635` ile clip edilmiştir.
6. Nihai clip edilmiş DEM üzerinden slope rasterı üretilmiştir.
7. Slope çıktısı percent değil, degrees biriminde üretilmiştir.

## QA Notları

- Nihai DEM tüm Çanakkale AOI alanını kapsar.
- Gökçeada ve Bozcaada dahildir.
- Gelibolu ve Eceabat dahildir.
- Clip sonrasında raster görsel olarak AOI dışına taşmaz.
- Slope rasterı beklenen arazi değişimini gösterir.
- Nihai DEM ve slope katmanları `data/processed/dem` altında bulunur.

## Metodolojik Sınır

DEM ve slope arazi morfolojisi girdileridir. Tek başlarına tehlike, risk,
kırılganlık veya maruziyet temsil etmezler.

Duyarlılık ve mekânsal öncelik analizi için destek girdisi olarak
kullanılırlar.

## Teknik QA Eki

İlk DEM/Slope işleme adımından sonra ek raster QA kayıtları üretilmiştir:

- `docs/qa/dem_raster_stats.md`
- `docs/qa/dem_sanity_checks.md`

Özet:

- DEM ve slope rasterları aynı grid, projection, extent ve pixel size bilgisini paylaşır.
- İki raster da `EPSG:32635` sistemindedir.
- Pixel size `30 m x 30 m` değerindedir.
- Slope değerleri degrees birimindedir.
- Negatif DEM hücreleri yalnızca çok küçük bir caveat olarak mevcuttur: geçerli DEM hücrelerinin `0.0061%` değeri.
- Base DEM bu QA kapsamında değiştirilmez.
- Daha sonra low-elevation veya coastal exposure analizi türetilirse negatif elevation değerleri türetilmiş katmanda açık şekilde ele alınmalıdır.
