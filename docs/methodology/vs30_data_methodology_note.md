# VS30 / Zemin Koşulu Veri Metodoloji Notu

## 1. Amaç

Bu not, Çanakkale çok kriterli mekânsal öncelik analizi projesinde kullanılan
VS30 tabanlı site condition proxy veri setinin hazırlanma ve doğrulama mantığını
dokümante eder.

Bu veri setinin amacı, Çanakkale çalışma alanı içinde geniş ölçekli yüzeye yakın
zemin koşulu farklılıklarını temsil etmektir.

Bu çıktı yerel mikrobölgeleme haritası, resmi zemin sınıflaması, sıvılaşma
duyarlılığı haritası, deterministik yer hareketi modeli, deprem tehlike haritası
veya resmi karar destek zonlaması değildir.

---

## 2. Kaynak Veri Seti

Bu metodoloji kapsamında kullanılan kaynak veri seti:

- USGS Global Vs30 Mosaic
- Extract dosyası: `vs30_mosaic_canakkale_extract.tif`
- Format: GeoTIFF
- Kaynak CRS: EPSG:4326
- Kaynak çözünürlük: 30 arc-seconds, yaklaşık 1 km
- Birim: metre/saniye
- Değişken: VS30, üst 30 metredeki zaman ortalamalı shear-wave velocity

Veri seti USGS Global Vs30 Mosaic Map Viewer ve VS30 Data Extraction Tool
kullanılarak elde edilmiştir.

Extraction için yalnızca `vs30_mosaic` katmanı seçilmiştir.

Extract edilen alan Çanakkale ve çevresindeki buffer alanını kapsar. Veri seti
daha sonra ana proje AOI sınırına hizalanmış ve maskelenmiştir.

---

## 3. Bilimsel Anlam

VS30, zeminin üst 30 metresindeki ortalama shear-wave velocity değerini temsil
eder.

Genel olarak daha düşük VS30 değerleri, deprem sarsıntısı sırasında daha güçlü
yer hareketi büyütmesiyle ilişkili olabilecek daha yumuşak yüzeye yakın zemin
koşullarına işaret eder.

Daha yüksek VS30 değerleri genellikle daha rijit veya kaya benzeri zemin
koşullarını gösterir.

Bu projede VS30 yalnızca geniş ölçekli site-condition proxy olarak kullanılır.

---

## 4. İşleme Adımları

VS30 rasterı aşağıdaki sırayla işlenmiştir:

1. Çanakkale alanı VS30 raster extract'i USGS Global Vs30 Mosaic Map Viewer üzerinden indirilmiştir.
2. Extract edilen GeoTIFF kaynak çalışma alanına alınmıştır.
3. Raw raster metadata bilgisi GDAL ile incelenmiştir.
4. Ana projenin 100 m analiz template'i kullanılmıştır.
5. Ana proje Çanakkale AOI sınırı kullanılmıştır.
6. Kaynak raster EPSG:4326 sisteminden EPSG:32635 sistemine reprojection işleminden geçirilmiştir.
7. Raster ana MCDA 100 m analiz gridine hizalanmıştır:
   - aynı extent
   - aynı pixel size
   - aynı raster boyutları
8. VS30 sürekli numeric surface olduğu için bilinear resampling kullanılmıştır.
9. AOI dışı alanlara NoData değeri olarak `-9999` atanmıştır.
10. Inverse min-max normalization kullanılarak 0-1 site condition score üretilmiştir.

---

## 5. Ana Çıktılar

| Çıktı | Açıklama |
|---|---|
| `vs30_100m_32635.tif` | Proje gridine hizalanmış ara VS30 rasterı |
| `vs30_aoi_100m_32635.tif` | Metre/saniye biriminde AOI maskelenmiş VS30 rasterı |
| `site_condition_score_32635.tif` | 0-1 normalize site condition proxy skoru |

---

## 6. QA Özeti

Raw extract VS30 rasterı şu özelliklere sahiptir:

| Özellik | Değer |
|---|---|
| Raster boyutu | 314 x 197 |
| Kaynak CRS | EPSG:4326 |
| Pixel size | 0.008333333 degrees |
| Data type | Int32 |
| Minimum VS30 | 88 m/s |
| Maximum VS30 | 937 m/s |
| Mean VS30 | 529.329 m/s |
| NoData değeri | 0 |

AOI maskelenmiş VS30 rasterı şu özelliklere sahiptir:

| Özellik | Değer |
|---|---|
| Raster boyutu | 1586 x 1423 |
| Pixel size | 100 m |
| CRS | EPSG:32635 |
| Minimum VS30 | 180.042 m/s |
| Maximum VS30 | 900.000 m/s |
| Mean VS30 | 492.230 m/s |
| NoData değeri | -9999 |
| Valid percent | 43.47 |

Site condition score rasterı şu özelliklere sahiptir:

| Özellik | Değer |
|---|---|
| Raster boyutu | 1586 x 1423 |
| Pixel size | 100 m |
| CRS | EPSG:32635 |
| Minimum score | 0.000 |
| Maximum score | 1.000 |
| Mean score | 0.566 |
| NoData değeri | -9999 |
| Valid percent | 43.47 |

Raster extent ve çözünürlüğü ana MCDA analiz template'iyle eşleşir.

---

## 7. Site Condition Skor Formülü

Site condition score, AOI maskelenmiş VS30 rasterından inverse min-max
normalization kullanılarak hesaplanmıştır:

```text
site_condition_score = (max_vs30 - vs30) / (max_vs30 - min_vs30)
```

Bu analizde:

```text
min_vs30 = 180.042
max_vs30 = 900.000
```

Skor 0-1 aralığına kırpılmıştır.

Yorum:

| VS30 koşulu | Skor yorumu |
|---|---|
| Daha düşük VS30 | Daha yüksek site condition score |
| Daha yüksek VS30 | Daha düşük site condition score |
| 1'e yakın skor | Daha yumuşak zemin proxy'si |
| 0'a yakın skor | Daha rijit zemin proxy'si |

AOI dışı alanlara NoData değeri olarak `-9999` atanmıştır.

---

## 8. Yorumlama

Site condition score, USGS Global Vs30 Mosaic tabanlı göreli yüzeye yakın zemin
koşulu farklılıklarını temsil eder.

Daha yüksek skor değerleri daha düşük VS30 alanlarını, dolayısıyla potansiyel
olarak daha yumuşak zemin koşullarını gösterir.

Daha düşük skor değerleri daha yüksek VS30 alanlarını, dolayısıyla potansiyel
olarak daha rijit zemin koşullarını gösterir.

Bu katman yalnızca geniş ölçekli site-condition ve olası ground-motion
amplification proxy'si olarak yorumlanmalıdır.

Resmi yerel zemin sınıfı, sıvılaşma duyarlılığı, heyelan duyarlılığı,
mikrobölgeleme, deprem tehlikesi veya deprem riski katmanı olarak
yorumlanmamalıdır.

---

## 9. Sınırlılıklar

Önemli sınırlılıklar:

- Kaynak veri seti global ölçekte ve yaklaşık niteliktedir.
- Kaynak çözünürlük yaklaşık 30 arc-seconds, yani yaklaşık 1 km'dir.
- Çıktı proje 100 m gridine hizalanmış olsa da gerçek bilgi detayı özgün kaynak çözünürlüğüyle sınırlıdır.
- Veri seti yerel jeoteknik ölçümler, sondaj verileri, mikrotremor çalışmaları veya resmi mikrobölgeleme ürünlerinin yerine geçmez.
- Bilinear resampling daha düzgün 100 m hizalanmış raster üretir; fakat gerçek yeni 100 m zemin bilgisi oluşturmaz.
- VS30 tek başına deprem tehlikesi veya deprem riskini temsil etmez.
- Sıvılaşma duyarlılığı, havza etkileri, yeraltı suyu derinliği, yerel jeoloji, bina kırılganlığı ve nüfus maruziyeti bu kriter tarafından doğrudan temsil edilmez.
- Çıktı uzman doğrulaması olmadan resmi risk, tehlike, acil durum planlama veya karar destek ürünü olarak kullanılmamalıdır.

---

## 10. Kullanılan Katmanlar ve Doğrulama

Bu metodoloji kapsamında kullanılan proje dosyaları:

- `data/processed/vs30/vs30_aoi_100m_32635.tif`
- `data/processed/analysis/site_condition_score_32635.tif`
- `docs/methodology/vs30_data_methodology_note.md`
- `scripts/bash/vs30_processing_pipeline.sh`

Doğrulama scripti, raw USGS VS30 extract dosyasını yeniden üretim girdisi olarak
beklemez; mevcut processed-canonical VS30 katmanını ve türetilmiş site condition
score rasterını doğrular.
