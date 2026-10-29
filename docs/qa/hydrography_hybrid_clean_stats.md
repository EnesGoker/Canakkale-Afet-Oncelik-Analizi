# Clean Hybrid Hydrography İstatistikleri

## Durum

KABUL EDİLDİ

## Çıktı

- Clean hybrid layer: `data/processed/hydrography/canakkale_hydrography_hybrid_clean_32635.gpkg`
- HydroRIVERS features: `445`
- OSM clean gap-fill features: `206`
- Total features: `651`

## Clean Hybrid Uzunluk Özeti

- Total clean hybrid length: `2117.2784` km
- Minimum length: `101.1448` m
- Maximum length: `25492.4529` m
- Mean length: `3252.3477` m
- Median length: `2219.9516` m
- 95th percentile length: `9642.0456` m

## OSM Clean Gap-Fill Uzunluk Özeti

- Total OSM clean gap-fill length: `196.1242` km
- Minimum OSM clean length: `101.1448` m
- Maximum OSM clean length: `10199.554` m

## Dışlanan Drain Uzunluk Özeti

- Total excluded drain/other length: `22.0289` km
- Excluded feature count: `60`

## Metodolojik Not

- Nihai hydrography katmanı olarak bu clean hybrid layer kullanılmalıdır.
- HydroRIVERS AOI, OSM waterways, OSM gap-fill ve clean hybrid scoring içinde eşzamanlı kullanılmamalıdır.
- Drainage feature'ları hydrography katmanını doğal river/stream/canal temsiline daha yakın tutmak için dışlanmıştır.
