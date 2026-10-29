# OSM Waterways Gap-Fill Değerlendirme QA

## Durum

KABUL EDİLDİ

## Amaç

- HydroRIVERS AOI birincil river network / hydrography veri seti olarak ele alınır.
- OSM waterways yalnızca ikincil yerel gap-fill kaynağı olarak değerlendirilir.
- HydroRIVERS'a yakın OSM waterways, duplicate hydrography azaltmak için dışlanır.

## Girdiler

- HydroRIVERS AOI: `data/processed/hydrography/canakkale_hydrorivers_aoi_32635.gpkg`
- OSM waterways: `data/processed/osm/canakkale_osm_waterways_32635.gpkg`

## Kurallar

- Duplicate distance threshold: `100.0` m
- Korunan minimum OSM waterway length: `100.0` m

## Sonuçlar

- OSM total features: `733`
- OSM empty geometries: `0`
- OSM invalid geometries repaired: `0`
- Çok kısa olduğu için atlanan OSM: `200`
- OSM duplicates / already represented: `267`
- Yakın HydroRIVERS bbox adayı olmayan OSM: `169`
- Kabul edilen OSM gap-fill: `266`
- Gap-fill output: `data/processed/hydrography/canakkale_osm_waterways_gapfill_32635.gpkg`

## OSM Gap-Fill Class Dağılımı

- `stream`: `178`
- `drain`: `60`
- `canal`: `24`
- `river`: `4`

## Yorum

- Gap-fill waterways ayrı bir hazard criterion değildir.
- Kabul edilirse yalnızca yerel hidrografya tamlığı için HydroRIVERS katmanını tamamlar.
- River proximity proxy/context input olarak kalır ve flood-depth modelling yerine geçmez.
