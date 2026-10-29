# OSM Buildings Gap-Fill Değerlendirme QA

## Durum

KABUL EDİLDİ

## Amaç

- Microsoft Buildings birincil built-up exposure veri seti olarak ele alınır.
- OSM Buildings yalnızca ikincil gap-fill kaynağı olarak değerlendirilir.
- Microsoft buildings ile yeterli düzeyde overlap yapan OSM buildings çift sayımı önlemek için dışlanır.

## Girdiler

- Microsoft buildings: `data/processed/exposure/canakkale_microsoft_buildings_32635.gpkg`
- OSM buildings: `data/processed/osm/canakkale_osm_buildings_32635.gpkg`

## Kurallar

- Duplicate threshold: `intersection_area / osm_area >= 0.2`
- Korunan minimum OSM building alanı: `5.0` m²

## Sonuçlar

- OSM total features: `85535`
- OSM empty geometries: `0`
- OSM invalid geometries repaired: `0`
- Çok küçük olduğu için atlanan OSM: `32`
- Duplicate olarak dışlanan OSM: `75427`
- Yakın Microsoft bbox adayı olmayan OSM: `3797`
- Kabul edilen OSM gap-fill: `10076`
- Gap-fill output: `data/processed/exposure/canakkale_osm_buildings_gapfill_32635.gpkg`

## Yorum

- Gap-fill buildings ayrı bir exposure criterion değildir.
- Ana Microsoft buildings katmanına opsiyonel tamamlayıcıdır.
- Gap-fill sayı/alanı küçükse sadelik için Microsoft-only exposure tercih edilebilir.
- Gap-fill adayları mekânsal olarak anlamlıysa hybrid katman nihai built-up exposure katmanı olarak kullanılabilir.
