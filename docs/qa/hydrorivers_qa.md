# HydroRIVERS Teknik QA

## Durum

KABUL EDİLDİ

## Katman Özellikleri

- Raw source: `data/raw/hydrography/hydrorivers/HydroRIVERS_v10_eu_shp/HydroRIVERS_v10_eu.shp`
- Çıktı: `data/processed/hydrography/canakkale_hydrorivers_32635.gpkg`
- CRS: `EPSG:32635` — **PASS**
- Feature sayısı: `478` — **PASS**
- Context buffer: `5000` m
- Extent: `391162.7862472319975495,4372246.7426231503486633 : 549660.6883294190047309,4513730.1743225501850247`

## İşleme Özeti

- Raw feature count: `938544`
- AOI context ile kesişen adaylar: `478`
- Nihai kabul edilen river reaches: `478`
- AOI ile kesişen river reaches: `445`
- Yalnızca context içinde kalan river reaches: `33`
- Atlanan boş geometriler: `0`
- Context dışında atlananlar: `938066`
- Atlanan line dışı geometriler: `0`
- Clip sonrası geçersiz olup atlananlar: `0`

## Geometri QA

- Boş geometriler: `0`
- Geçersiz geometriler: `0` — **PASS**
- Line dışı geometriler: `0`
- 5 km AOI context dışındaki feature'lar: `0` — **PASS**

## Metodolojik Not

- HydroRIVERS ana river network / hydrography veri seti olarak kullanılır.
- İdari sınırlarda yapay nehir kesilmesini azaltmak için 5 km AOI context buffer korunmuştur.
- Nehir yakınlığı taşkın riskiyle aynı şey değildir.
- JRC/CEMS flood depth ana flood hazard-support rasterı olarak kalır.
- OSM waterways devre dışı bırakılmalı, arşivlenmeli veya yalnızca ikincil yerel gap-fill/reference source olarak değerlendirilmelidir.
