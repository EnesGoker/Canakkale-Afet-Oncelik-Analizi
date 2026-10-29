# OSM Buildings QA

## Durum

KABUL EDİLDİ

## Nihai Katman

Path:

`data/processed/osm/canakkale_osm_buildings_32635.gpkg`

CRS:

`EPSG:32635 - WGS 84 / UTM Zone 35N`

Feature sayısı:

`85535`

## Kaynak

Geofabrik OSM Turkey GeoPackage, source layer:

`gis_osm_buildings_a_free`

## İşleme Özeti

1. Türkiye geneli OSM buildings katmanı raw Geofabrik GeoPackage içinden okunmuştur.
2. Performans için AOI bounding box filtering kullanılmıştır.
3. Aday geometriler EPSG:32635 sistemine dönüştürülmüştür.
4. Çanakkale AOI ile kesişen buildings geometrileri AOI geometrisiyle clip edilmiştir.
5. Nihai çıktı `data/processed/osm` altına yazılmıştır.

## QA Notları

- Çıktı CRS EPSG:32635 değerindedir.
- Çıktı geometry type polygon tabanlıdır.
- Katman Çanakkale AOI sınırına clip edilmiştir.
- Teknik QA `docs/qa/osm_buildings_stats.md` içinde dokümante edilmiştir.

## Metodolojik Sınır

OSM buildings maruziyet / built-environment destek verisidir. Tamlık düzeyi
OpenStreetMap mapping quality değerine bağlıdır ve resmi bina envanteri olarak
yorumlanmamalıdır.
