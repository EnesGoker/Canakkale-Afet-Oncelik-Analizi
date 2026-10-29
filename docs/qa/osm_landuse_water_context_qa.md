# OSM Landuse / Water Context QA

## Durum

KABUL EDİLDİ

## Nihai Katmanlar

### Landuse

- Path: `data/processed/osm/canakkale_osm_landuse_32635.gpkg`
- Kaynak layer: `gis_osm_landuse_a_free`
- Feature sayısı: `5643`
- Geometry: `polygon`
- CRS: `EPSG:32635`

### Water Areas

- Path: `data/processed/osm/canakkale_osm_water_areas_32635.gpkg`
- Kaynak layer: `gis_osm_water_a_free`
- Feature sayısı: `244`
- Geometry: `polygon`
- CRS: `EPSG:32635`

### Waterways

- Path: `data/processed/osm/canakkale_osm_waterways_32635.gpkg`
- Kaynak layer: `gis_osm_waterways_free`
- Feature sayısı: `733`
- Geometry: `line`
- CRS: `EPSG:32635`

## İşleme Özeti

1. Türkiye geneli OSM context katmanları raw Geofabrik GeoPackage içinden okunmuştur.
2. Performans için AOI bounding box filtering kullanılmıştır.
3. Aday geometriler EPSG:32635 sistemine dönüştürülmüştür.
4. Çanakkale AOI ile kesişen feature'lar AOI geometrisiyle clip edilmiştir.
5. Nihai çıktılar `data/processed/osm` altına yazılmıştır.

## QA Notları

- Çıktı CRS EPSG:32635 değerindedir.
- Landuse ve water areas polygon tabanlıdır.
- Waterways line tabanlıdır.
