# HydroRIVERS AOI-Clip Teknik QA

## Durum

KABUL EDİLDİ

## Katman Özellikleri

- Context source: `data/processed/hydrography/canakkale_hydrorivers_32635.gpkg`
- AOI-clipped output: `data/processed/hydrography/canakkale_hydrorivers_aoi_32635.gpkg`
- CRS: `EPSG:32635` — **PASS**
- Feature sayısı: `445` — **PASS**
- Extent: `391162.7862472319975495,4372246.7426231503486633 : 544504.1893502889433876,4506843.1022419100627303`

## İşleme Özeti

- Context source features: `478`
- AOI ile kesişen feature'lar: `445`
- Nihai kabul edilen AOI river reaches: `445`
- Atlanan boş geometriler: `0`
- AOI dışında atlananlar: `33`
- Atlanan line dışı geometriler: `0`
- Clip sonrası geçersiz olup atlananlar: `0`

## Geometri QA

- Boş geometriler: `0`
- Geçersiz geometriler: `0` — **PASS**
- Line dışı geometriler: `0`
- AOI dışındaki feature'lar: `0` — **PASS**

## Metodolojik Not

- 5 km HydroRIVERS context katmanı teknik kaynak katmanı olarak korunur.
- Bu AOI-clipped katman temiz harita gösterimi ve Çanakkale analizi için kullanılır.
- Nehir yakınlığı taşkın riskiyle aynı şey değildir.
- JRC/CEMS flood depth ana flood hazard-support rasterı olarak kalır.
