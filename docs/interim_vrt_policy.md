# Interim VRT Politikası

Proje: Çanakkale çok kriterli afet öncelik alanları analizi

Bu doküman, `data/interim` altındaki VRT dosyalarının kullanım politikasını
kaydeder.

## 1. Kullanım Kuralı

`data/interim` altındaki VRT dosyaları tarihsel/interim build artefact
kayıtlarıdır. Yalnızca teknik izlenebilirlik için korunurlar.

Analiz pipeline'ı için canonical input değildirler.

Analiz girdileri şu belgelerde dokümante edilen processed/reference
katmanlarıdır:

```text
docs/canonical_data_policy.md
docs/data_source_inventory.md
```

## 2. Tanınan VRT Kayıtları

Aşağıdaki VRT kayıtları canonical input değildir. Dosya mevcutsa XML ve path
standardı doğrulanır; dosya mevcut değilse processed-canonical karşılıklar esas
alınır.

| VRT | Kayıt türü | Canonical karşılık |
|---|---|---|
| `data/interim/dem/canakkale_dem_mosaic_4326.vrt` | Tarihsel/interim | `data/processed/dem/canakkale_dem_32635.tif` ve `data/processed/dem/canakkale_slope_degrees_32635.tif` |
| `data/interim/landcover/canakkale_worldcover_2021_mosaic_4326.vrt` | Tarihsel/interim | `data/processed/landcover/canakkale_worldcover_2021_32635.tif` |
| `data/interim/landcover/canakkale_tree_cover_density_2021_mosaic_3035.vrt` | Tarihsel/interim | `data/processed/landcover/canakkale_tree_cover_density_2021_32635.tif` |

## 3. Path Standardı

VRT `SourceFilename` girdileri yerel mutlak path kullanmamalıdır.

Korunan VRT'ler şu tür relative pathler kullanır:

```text
../../raw/dem/...
../../raw/landcover/...
```

Bu pathler, bir interim mosaic yeniden üretimi gerektiğinde upstream ham kaynak
dosyalarının nerede bulunması gerekeceğini tarif eder.

## 4. Pipeline Kuralı

Scriptler, QGIS katmanları, atlas çıktıları, rapor tabloları ve MCDA
analizi bu VRT dosyalarına bağımlı olmamalıdır.

Raw upstream veri setleri mevcut değilse bu bir proje hatası değildir.
Processed-canonical çıktılar analiz veri tabanı olmaya devam eder.

## 5. Doğrulama

Temizlik sonrası:

| Kontrol | Sonuç |
|---|---:|
| `data/interim` içinde kişisel/yerel mutlak path eşleşmesi | 0 |
| VRT XML doğrulaması | Mevcut VRT dosyaları için uygulanır |
| QGIS projesinin VRT dosya referansı | 0 |
| Scriptlerin VRT dosya referansı | 0 |
