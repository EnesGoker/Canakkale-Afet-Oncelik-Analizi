# OSM Roads Teknik QA

## Durum

KABUL EDİLDİ

## Katman Özellikleri

- Kaynak: `data/processed/osm/canakkale_osm_roads_32635.gpkg`
- CRS: `EPSG:32635` — **PASS**
- Feature sayısı: `34442` — **PASS**
- Extent: `386665.6107095350162126,4367545.1018329402431846 : 544629.1222119369776919,4509717.4736243002116680`

## Geometri QA

- Boş geometriler: `0`
- Geçersiz geometriler: `0` — **PASS**
- Line dışı geometriler: `0`
- AOI dışındaki feature'lar: `0` — **PASS**

## Uzunluk Özeti

- Toplam road length: `17644.855` km
- Minimum feature length: `0.082` m
- Maximum feature length: `17666.666` m

## Road Class Dağılımı

- `residential`: `15781`
- `track`: `7633`
- `tertiary`: `3256`
- `service`: `2369`
- `unclassified`: `1334`
- `living_street`: `826`
- `path`: `584`
- `footway`: `567`
- `secondary`: `561`
- `trunk`: `547`
- `trunk_link`: `275`
- `primary`: `124`
- `motorway_link`: `98`
- `motorway`: `86`
- `tertiary_link`: `74`
- `pedestrian`: `66`
- `secondary_link`: `65`
- `steps`: `53`
- `primary_link`: `39`
- `track_grade3`: `29`
- `track_grade4`: `28`
- `track_grade2`: `23`
- `track_grade1`: `15`
- `cycleway`: `4`
- `track_grade5`: `3`
- `bridleway`: `2`

## Ad Tamlığı

- İsimsiz road feature'ları: `31040`
- İsimli road feature'ları: `3402`

## Yorum

- OSM roads maruziyet/erişilebilirlik/destekleyici altyapı girdisi olarak kullanılır.
- Bu katman tek başına hazard, vulnerability veya risk çıktısı değildir.
- Katman Çanakkale AOI sınırına clip edilmiş ve EPSG:32635 sisteminde saklanmıştır.
