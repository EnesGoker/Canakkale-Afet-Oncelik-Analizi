# OSM POI / Places / Transport Points QA

## Durum

KABUL EDİLDİ

## Nihai Katmanlar

### POIs

- Path: `data/processed/osm/canakkale_osm_pois_32635.gpkg`
- Kaynak layer: `gis_osm_pois_free`
- Feature sayısı: `1748`
- CRS: `EPSG:32635`

### Places

- Path: `data/processed/osm/canakkale_osm_places_32635.gpkg`
- Kaynak layer: `gis_osm_places_free`
- Feature sayısı: `843`
- CRS: `EPSG:32635`

### Transport Points

- Path: `data/processed/osm/canakkale_osm_transport_points_32635.gpkg`
- Kaynak layer: `gis_osm_transport_free`
- Feature sayısı: `43`
- CRS: `EPSG:32635`

## İşleme Özeti

1. Türkiye geneli OSM point katmanları raw Geofabrik GeoPackage içinden okunmuştur.
2. Performans için AOI bounding box filtering kullanılmıştır.
3. Aday geometriler EPSG:32635 sistemine dönüştürülmüştür.
4. Çanakkale AOI ile kesişen point feature'ları çıkarılmıştır.
5. Nihai çıktılar `data/processed/osm` altına yazılmıştır.

## QA Notları

- Çıktı CRS EPSG:32635 değerindedir.
- Çıktı geometry type point tabanlıdır.
- Teknik QA `docs/qa/osm_poi_places_transport_stats.md` içinde dokümante edilmiştir.

## Metodolojik Sınır

OSM POI, places ve transport point katmanları maruziyet/bağlam destek verisidir.
Tamlık düzeyi OpenStreetMap mapping quality değerine bağlıdır ve resmi envanter
olarak yorumlanmamalıdır.
