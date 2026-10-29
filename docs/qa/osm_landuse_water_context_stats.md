# OSM Landuse / Water Context Teknik QA

## Durum

KABUL EDİLDİ

## Landuse

- Kaynak layer: `gis_osm_landuse_a_free`
- Çıktı: `data/processed/osm/canakkale_osm_landuse_32635.gpkg`
- Expected geometry: `polygon`
- CRS: `EPSG:32635` — **PASS**
- Feature sayısı: `5643`
- Extent: `386392.7056060530012473,4367462.8720032097771764 : 544962.3790084109641612,4509726.2724630497395992`

### Geometri QA

- Boş geometriler: `0`
- Geçersiz geometriler: `0`
- Yanlış geometri tipi: `0`
- Zero area feature'lar: `0`
- AOI dışındaki feature'lar: `0`

### Ölçü Özeti

- Toplam alan: `3617.7091` km²
- Minimum alan: `14.7028` m²
- Maximum alan: `140806892.6312` m²

### Class Dağılımı

- `forest`: `1524`
- `farmland`: `1306`
- `residential`: `988`
- `orchard`: `532`
- `scrub`: `374`
- `grass`: `280`
- `park`: `140`
- `cemetery`: `119`
- `industrial`: `89`
- `quarry`: `69`
- `farmyard`: `54`
- `vineyard`: `34`
- `commercial`: `30`
- `military`: `29`
- `allotments`: `22`
- `landfill`: `20`
- `heath`: `18`
- `meadow`: `11`
- `retail`: `4`

### Type Dağılımı

- Class/type field değerleri bulunmadı.

### Ad Tamlığı

- İsimsiz feature'lar: `5303`
- İsimli feature'lar: `340`

## Water Areas

- Kaynak layer: `gis_osm_water_a_free`
- Çıktı: `data/processed/osm/canakkale_osm_water_areas_32635.gpkg`
- Expected geometry: `polygon`
- CRS: `EPSG:32635` — **PASS**
- Feature sayısı: `244`
- Extent: `389860.4484189769718796,4372609.3754373798146844 : 543948.3073735659709200,4504591.5691994102671742`

### Geometri QA

- Boş geometriler: `0`
- Geçersiz geometriler: `0`
- Yanlış geometri tipi: `0`
- Zero area feature'lar: `0`
- AOI dışındaki feature'lar: `0`

### Ölçü Özeti

- Toplam alan: `72.2585` km²
- Minimum alan: `9.6821` m²
- Maximum alan: `10285669.4375` m²

### Class Dağılımı

- `water`: `153`
- `reservoir`: `61`
- `riverbank`: `19`
- `wetland_tidalflat`: `4`
- `wetland_marsh`: `3`
- `wetland`: `2`
- `wetland_saltmarsh`: `2`

### Type Dağılımı

- Class/type field değerleri bulunmadı.

### Ad Tamlığı

- İsimsiz feature'lar: `180`
- İsimli feature'lar: `64`

## Waterways

- Kaynak layer: `gis_osm_waterways_free`
- Çıktı: `data/processed/osm/canakkale_osm_waterways_32635.gpkg`
- Expected geometry: `line`
- CRS: `EPSG:32635` — **PASS**
- Feature sayısı: `733`
- Extent: `395335.7207136480137706,4372252.3235597796738148 : 541480.2763695219764486,4508280.6628853296861053`

### Geometri QA

- Boş geometriler: `0`
- Geçersiz geometriler: `0`
- Yanlış geometri tipi: `0`
- Zero length feature'lar: `0`
- AOI dışındaki feature'lar: `0`

### Ölçü Özeti

- Toplam uzunluk: `1432.0306` km
- Minimum uzunluk: `3.3127` m
- Maximum uzunluk: `24060.4124` m

### Class Dağılımı

- `stream`: `509`
- `drain`: `110`
- `river`: `62`
- `canal`: `52`

### Type Dağılımı

- Class/type field değerleri bulunmadı.

### Ad Tamlığı

- İsimsiz feature'lar: `573`
- İsimli feature'lar: `160`

## Yorum

- Landuse, water areas ve waterways bağlamsal destek girdileridir.
- Duyarlılık, maruziyet ve spatial-priority yorumlarını desteklerler.
- Tek başlarına hazard, vulnerability, exposure veya nihai risk çıktısı değildirler.
- Tamlık düzeyi OpenStreetMap mapping quality değerine bağlıdır.
- Kabul edilen tüm katmanlar EPSG:32635 sisteminde saklanmış ve Çanakkale AOI ile clip/intersect edilmiştir.
