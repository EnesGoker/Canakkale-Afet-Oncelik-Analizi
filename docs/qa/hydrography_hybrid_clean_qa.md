# Clean Hybrid Hydrography QA

## Durum

KABUL EDİLDİ

## Amaç

- HydroRIVERS AOI birincil doğal river network olarak korunur.
- OSM gap-fill yalnızca seçilmiş yerel hydrography class değerleri için kullanılır.
- OSM `drain` feature'ları temiz doğal hydrography katmanından dışlanır.

## Girdiler

- HydroRIVERS AOI: `data/processed/hydrography/canakkale_hydrorivers_aoi_32635.gpkg`
- OSM waterways gap-fill: `data/processed/hydrography/canakkale_osm_waterways_gapfill_32635.gpkg`

## Class Kuralı

- Dahil edilen OSM class değerleri: `canal, river, stream`
- Dışlanan OSM class değerleri: `drain`

## Sonuçlar

- Korunan HydroRIVERS features: `445`
- Korunan OSM clean gap-fill features: `206`
- Dışlanan OSM drain features: `60`
- Dışlanan OSM other features: `0`
- Clean hybrid total features: `651`
- Çıktı: `data/processed/hydrography/canakkale_hydrography_hybrid_clean_32635.gpkg`

## Geometri QA

- CRS: `EPSG:32635` — **PASS**
- Boş geometriler: `0`
- Geçersiz geometriler: `0` — **PASS**
- Line dışı geometriler: `0`

## Dahil Edilen OSM Class Dağılımı

- `stream`: `178`
- `canal`: `24`
- `river`: `4`

## Dışlanan OSM Class Dağılımı

- `drain`: `60`

## Yorum

- Bu clean hybrid layer doğal river/stream/canal proximity analysis için tercih edilir.
- OSM drain feature'ları clean nihai hydrography içinde değil, yalnızca önceki gap-fill QA katmanında korunur.
- JRC/CEMS flood depth ana flood hazard-support rasterı olarak kalır.
