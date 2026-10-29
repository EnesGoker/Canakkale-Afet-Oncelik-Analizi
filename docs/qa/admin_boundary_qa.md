# İdari Sınır QA

## Durum

KABUL EDİLDİ

## Nihai Katmanlar

### İlçe Katmanı

Path:

`data/processed/admin/canakkale_districts_32635.gpkg`

Layer name:

`canakkale_districts_32635`

CRS:

`EPSG:32635 - WGS 84 / UTM Zone 35N`

Feature sayısı:

`12`

### AOI Katmanı

Path:

`data/processed/aoi/canakkale_aoi_32635.gpkg`

CRS:

`EPSG:32635 - WGS 84 / UTM Zone 35N`

## İlçe Adları

- Ayvacık
- Bayramiç
- Biga
- Bozcaada
- Çan
- Çanakkale Merkez
- Eceabat
- Ezine
- Gelibolu
- Gökçeada
- Lapseki
- Yenice

## Yöntem Özeti

Nihai ilçe katmanı HGM tabanlı idari sınır geometrisi kullanılarak
oluşturulmuştur.

İşleme özeti:

1. HGM il ve ilçe sınır verileri yüklenmiştir.
2. Raw HGM CRS, custom Lambert Conformal Conic CRS olarak ele alınmıştır.
3. İdari katmanlar EPSG:32635 sistemine reprojection işleminden geçirilmiştir.
4. Çanakkale AOI oluşturulmuştur.
5. HGM ilçe sınır çizgileri Çanakkale AOI sınırına clip edilmiştir.
6. AOI sınır çizgileri ve clip edilmiş ilçe çizgileri polygonization network oluşturmak için kullanılmıştır.
7. Network polygonize edilmiştir.
8. Polygonize edilmiş ilçe parçaları Çanakkale AOI sınırına clip edilmiştir.
9. İlçe adları, görsel QA sonrasında OSM Geofabrik adminareas katmanından manuel olarak aktarılmıştır.

## Kaynak Rolleri

Geometri kaynağı:

`HGM AOI + HGM district boundary polygonize`

Ad kaynağı:

`OSM Geofabrik adminareas manual label transfer`

## QA Notları

- Nihai ilçe katmanı 12 ilçe feature'ı içerir.
- Tüm ilçe adları doldurulmuştur.
- Gökçeada ve Bozcaada dahildir.
- Nihai processed admin klasörü yalnızca kabul edilen ilçe katmanını içerir.
- Intermediate admin processing katmanları nihai proje paketiyle dağıtılmaz.

## Metodolojik Sınır

Bu idari sınır katmanı mekânsal referans katmanıdır. Tek başına tehlike, risk,
duyarlılık, kırılganlık veya maruziyet çıktısı değildir.
