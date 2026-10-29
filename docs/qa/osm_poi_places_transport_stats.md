# OSM POI / Places / Transport Points Teknik QA

## Durum

KABUL EDİLDİ

## POIs

- Kaynak layer: `gis_osm_pois_free`
- Çıktı: `data/processed/osm/canakkale_osm_pois_32635.gpkg`
- CRS: `EPSG:32635` — **PASS**
- Feature sayısı: `1748`
- Extent: `387262.9943835560115986,4368107.4384707203134894 : 543775.9013982450123876,4509590.2039078902453184`

### Geometri QA

- Boş geometriler: `0`
- Geçersiz geometriler: `0`
- Point dışı geometriler: `0`
- AOI dışındaki feature'lar: `0`

### Class Dağılımı

- `pharmacy`: `197`
- `hotel`: `183`
- `restaurant`: `134`
- `drinking_water`: `121`
- `cafe`: `100`
- `supermarket`: `86`
- `convenience`: `79`
- `memorial`: `64`
- `tower`: `54`
- `hostel`: `51`
- `attraction`: `35`
- `camp_site`: `31`
- `atm`: `31`
- `tourist_info`: `29`
- `toilet`: `25`
- `fast_food`: `22`
- `bakery`: `21`
- `battlefield`: `20`
- `gift_shop`: `19`
- `beverages`: `18`
- `shelter`: `17`
- `bank`: `15`
- `clothes`: `15`
- `archaeological`: `14`
- `observation_tower`: `14`
- `pub`: `13`
- `post_office`: `13`
- `hairdresser`: `13`
- `butcher`: `13`
- `museum`: `12`

### Type Dağılımı

- Class/type field değerleri bulunmadı.

### Ad Tamlığı

- İsimsiz feature'lar: `398`
- İsimli feature'lar: `1350`

## Places

- Kaynak layer: `gis_osm_places_free`
- Çıktı: `data/processed/osm/canakkale_osm_places_32635.gpkg`
- CRS: `EPSG:32635` — **PASS**
- Feature sayısı: `843`
- Extent: `389842.5795989619800821,4370432.9804156497120857 : 543885.3966122990241274,4509681.1007400099188089`

### Geometri QA

- Boş geometriler: `0`
- Geçersiz geometriler: `0`
- Point dışı geometriler: `0`
- AOI dışındaki feature'lar: `0`

### Class Dağılımı

- `village`: `585`
- `locality`: `185`
- `suburb`: `32`
- `hamlet`: `21`
- `town`: `10`
- `farm`: `9`
- `city`: `1`

### Type Dağılımı

- Class/type field değerleri bulunmadı.

### Ad Tamlığı

- İsimsiz feature'lar: `2`
- İsimli feature'lar: `841`

## Transport Points

- Kaynak layer: `gis_osm_transport_free`
- Çıktı: `data/processed/osm/canakkale_osm_transport_points_32635.gpkg`
- CRS: `EPSG:32635` — **PASS**
- Feature sayısı: `43`
- Extent: `405949.4672756990185007,4392770.4307945501059294 : 519244.8138722960138693,4495347.1515023401007056`

### Geometri QA

- Boş geometriler: `0`
- Geçersiz geometriler: `0`
- Point dışı geometriler: `0`
- AOI dışındaki feature'lar: `0`

### Class Dağılımı

- `bus_stop`: `23`
- `taxi`: `10`
- `ferry_terminal`: `5`
- `bus_station`: `4`
- `helipad`: `1`

### Type Dağılımı

- Class/type field değerleri bulunmadı.

### Ad Tamlığı

- İsimsiz feature'lar: `18`
- İsimli feature'lar: `25`

## Yorum

- Bu point katmanları maruziyet / insan aktivitesi / yerleşim / ulaşım destek girdileri olarak kullanılır.
- Tek başlarına hazard, vulnerability veya nihai risk çıktısı değildir.
- Tamlık düzeyi OpenStreetMap mapping quality değerine bağlıdır.
- Kabul edilen tüm katmanlar EPSG:32635 sisteminde saklanmış ve Çanakkale AOI ile clip/intersect edilmiştir.
