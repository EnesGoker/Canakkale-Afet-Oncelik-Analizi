# ESA WorldCover 2021 / Arazi Örtüsü QA

## Durum

KABUL EDİLDİ

## Nihai Katman

Path:

`data/processed/landcover/canakkale_worldcover_2021_32635.tif`

CRS:

`EPSG:32635 - WGS 84 / UTM Zone 35N`

Çözünürlük:

`10 m x 10 m`

## Kaynak

ESA WorldCover 2021, 10 m categorical land cover raster.

Raw tile kayıtları:

- `data/raw/landcover/esa_worldcover_2021/ESA_WorldCover_10m_2021_v200_N39E024_Map.tif`
- `data/raw/landcover/esa_worldcover_2021/ESA_WorldCover_10m_2021_v200_N39E027_Map.tif`

## İşleme Özeti

1. İki ESA WorldCover tile proje raw data seceresine alınmıştır.
2. Raw tile'lar Çanakkale AOI sınırına karşı görsel olarak kontrol edilmiştir.
3. Virtual raster mosaic oluşturulmuştur.
4. Mosaic `canakkale_aoi_32635` sınırına clip edilmiştir.
5. Çıktı `EPSG:32635` sisteminde saklanmıştır.
6. Categorical class değerlerini korumak için Nearest Neighbor resampling kullanılmıştır.

## QA Notları

- Çanakkale AOI kapsanmaktadır.
- Gökçeada ve Bozcaada dahildir.
- Clip sonrasında görünür AOI taşması gözlenmemiştir.
- Class value integrity `docs/qa/landcover_raster_stats.md` içinde dokümante edilmiştir.

## Metodolojik Sınır

Landcover bağlamsal ve duyarlılık-destek input katmanıdır. Tek başına tehlike,
risk, kırılganlık veya maruziyet çıktısı değildir.

## Teknik QA Eki

Ek raster QA kayıtları üretilmiştir:

- `docs/qa/landcover_raster_stats.md`

Özet:

- Nihai landcover rasterı `EPSG:32635` sistemindedir.
- Pixel size `10 m x 10 m` değerindedir.
- Beklenmeyen class value bulunmamıştır.
- ESA WorldCover categorical raster olduğu için Nearest Neighbor resampling kullanılmıştır.
- NoData değeri `0`dır.
- NoData hücreleri clip sonrasında Çanakkale AOI dışındaki dikdörtgen raster extent alanını temsil eder.
- Yüksek NoData yüzdesi beklenen bir durumdur ve AOI coverage hatası göstermez.
