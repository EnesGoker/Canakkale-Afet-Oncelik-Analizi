# Hybrid Hydrography İstatistikleri

## Durum

KABUL EDİLDİ

## Hybrid Çıktı

- Hybrid layer: `data/processed/hydrography/canakkale_hydrography_hybrid_hydrorivers_osm_32635.gpkg`
- HydroRIVERS features: `445`
- OSM gap-fill features: `266`
- Total hybrid features: `711`

## Hybrid Uzunluk Özeti

- Total hybrid length: `2139.3073` km
- Minimum length: `101.1448` m
- Maximum length: `25492.4529` m
- Mean length: `3008.871` m
- Median length: `1879.8595` m
- 95th percentile length: `9444.6656` m

## OSM Gap-Fill Uzunluk Özeti

- Total OSM gap-fill length: `218.1531` km
- Minimum gap-fill length: `101.1448` m
- Maximum gap-fill length: `10199.554` m
- Mean gap-fill length: `820.1244` m
- Median gap-fill length: `485.2533` m

## Metodolojik Not

- Hybrid layer, hydrography/proximity analysis içinde standalone HydroRIVERS ve standalone OSM waterways katmanlarının yerini alır.
- HydroRIVERS, OSM waterways ve hybrid hydrography aynı anda scoring içinde kullanılmamalıdır.
- JRC/CEMS flood depth ana flood hazard-support rasterı olarak kalır.
