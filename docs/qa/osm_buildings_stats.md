# OSM Buildings Teknik QA

## Durum

KABUL EDİLDİ

## Katman Özellikleri

- Kaynak: `data/processed/osm/canakkale_osm_buildings_32635.gpkg`
- CRS: `EPSG:32635` — **PASS**
- Feature sayısı: `85535` — **PASS**
- Extent: `386753.7634433539933525,4367663.4022095398977399 : 543082.0445093410089612,4506344.8640794102102518`

## Geometri QA

- Boş geometriler: `0`
- Geçersiz geometriler: `0` — **PASS**
- Polygon dışı geometriler: `0`
- Zero-area geometriler: `0`
- AOI dışındaki feature'lar: `0` — **PASS**

## Alan Özeti

- Toplam building footprint alanı: `14.6127` km²
- Minimum feature alanı: `0.0049` m²
- Maximum feature alanı: `70894.8224` m²
- `< 10 m²` buildings: `188` / `0.2198%`
- `< 25 m²` buildings: `2451` / `2.8655%`
- `> 100 m²` buildings: `45342` / `53.0099%`
- `> 500 m²` buildings: `2857` / `3.3402%`
- `> 1000 m²` buildings: `1006` / `1.1761%`

## Building Class Dağılımı

- `building`: `85535`

## Building Type Dağılımı

- `NULL`: `82030`
- `house`: `1364`
- `apartments`: `529`
- `mosque`: `444`
- `industrial`: `396`
- `school`: `166`
- `roof`: `90`
- `ruins`: `84`
- `greenhouse`: `61`
- `university`: `46`
- `residential`: `38`
- `hotel`: `35`
- `commercial`: `32`
- `dam`: `28`
- `barn`: `27`
- `dormitory`: `20`
- `storage_tank`: `16`
- `service`: `15`
- `hospital`: `13`
- `public`: `11`
- `shed`: `9`
- `kindergarten`: `9`
- `bunker`: `9`
- `cowshed`: `8`
- `farm`: `5`
- `sports_centre`: `5`
- `hangar`: `4`
- `civic`: `4`
- `garage`: `3`
- `warehouse`: `3`

## Ad Tamlığı

- İsimsiz building feature'ları: `84790`
- İsimli building feature'ları: `745`

## Yorum

- OSM buildings maruziyet / built-environment support verisi olarak kullanılır.
- Building completeness OpenStreetMap mapping quality değerine bağlıdır.
- Katman Çanakkale AOI sınırına clip edilmiş ve EPSG:32635 sisteminde saklanmıştır.
- Bu katman tek başına hazard, vulnerability veya nihai risk çıktısı değildir.
