# Microsoft Buildings Teknik QA

## Durum

KABUL EDİLDİ

## Katman Özellikleri

- Raw source: `data/raw/buildings/microsoft/canakkale_microsoft_buildings_bbox_test.gpkg`
- Çıktı: `data/processed/exposure/canakkale_microsoft_buildings_32635.gpkg`
- CRS: `EPSG:32635` — **PASS**
- Feature sayısı: `295989` — **PASS**
- Extent: `397734.5152698879828677,4367658.0705820498988032 : 544808.4515554730314761,4508941.4477087603881955`

## İşleme Özeti

- Raw feature count: `668337`
- AOI ile kesişen adaylar: `295989`
- Nihai kabul edilen buildings: `295989`
- Atlanan boş geometriler: `0`
- AOI dışında atlananlar: `372348`
- Atlanan polygon dışı geometriler: `0`
- Clip sonrası geçersiz olup atlananlar: `0`

## Geometri QA

- Boş geometriler: `0`
- Geçersiz geometriler: `0` — **PASS**
- Polygon dışı geometriler: `0`
- AOI dışındaki feature'lar: `0` — **PASS**

## Metodolojik Not

- Microsoft Global ML Building Footprints ana built-up exposure veri seti olarak kullanılır.
- Çift sayımı önlemek için OSM buildings MCDA exposure scoring içinde devre dışı bırakılmalı veya yalnızca gap-fill bileşeni olarak ele alınmalıdır.
- Bu katman detected building footprintleri temsil eder; nüfus, yapısal kırılganlık veya bina düzeyi afet riskini temsil etmez.
