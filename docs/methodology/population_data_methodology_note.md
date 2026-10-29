# Nüfus Maruziyeti Veri Metodoloji Notu

## 1. Amaç

Bu not, Çanakkale çok kriterli mekânsal öncelik analizi projesinde kullanılan
nüfus maruziyeti veri setinin hazırlanma ve doğrulama mantığını dokümante eder.

Bu katmanın amacı, Çanakkale çalışma alanı içinde tahmini yerleşik insan nüfusu
maruziyetini temsil etmektir.

Bu çıktı gerçek zamanlı nüfusu, resmi sayım sınırlarını, sosyal kırılganlığı,
afet riskini, beklenen can kaybını veya resmi karar destek zonlamasını temsil
etmez.

---

## 2. Kaynak Veri Seti

Bu metodoloji kapsamında kullanılan kaynak veri seti:

- WorldPop Turkey 2020 population count raster
- Dosya: `tur_ppp_2020_UNadj_constrained.tif`
- Format: GeoTIFF
- Kaynak CRS: EPSG:4326
- Model tipi: constrained population estimate
- Adjustment: UN-adjusted
- Yaklaşık özgün çözünürlük: 100 m

Constrained population ürünü, nüfus dağılımını unconstrained nüfus yüzeylerine
göre olası yerleşik/yapılı alanlara daha güçlü şekilde sınırladığı için tercih
edilmiştir.

UN-adjusted versiyon, ulusal nüfus toplamının ilgili United Nations nüfus
tahminiyle uyumlu olacak şekilde ayarlanması nedeniyle seçilmiştir.

---

## 3. İşleme Adımları

Nüfus rasterı aşağıdaki sırayla işlenmiştir:

1. Raw WorldPop GeoTIFF kaynak çalışma alanına alınmıştır.
2. Raster metadata bilgisi GDAL ile incelenmiştir.
3. Ana projenin 100 m analiz template'i kullanılmıştır.
4. Ana proje Çanakkale AOI sınırı kullanılmıştır.
5. Kaynak raster EPSG:4326 sisteminden EPSG:32635 sistemine reprojection işleminden geçirilmiştir.
6. Raster ana MCDA 100 m analiz gridine hizalanmıştır:
   - aynı extent
   - aynı pixel size
   - aynı raster boyutları
7. Kaynak değerler hücre başına tahmini nüfus sayısını temsil ettiği için sum resampling kullanılmıştır.
8. AOI dışı alanlara NoData değeri olarak `-9999` atanmıştır.
9. AOI içindeki nüfus değeri olmayan hücrelere `0` atanmıştır.
10. Log normalization ile 0-1 nüfus maruziyeti skoru üretilmiştir.

---

## 4. Ana Çıktılar

| Çıktı | Açıklama |
|---|---|
| `population_count_100m_32635.tif` | Proje gridine hizalanmış ara 100 m nüfus count rasterı |
| `population_count_aoi_100m_32635.tif` | AOI maskelenmiş 100 m tahmini nüfus count rasterı |
| `population_exposure_score_32635.tif` | 0-1 normalize nüfus maruziyeti score rasterı |

---

## 5. QA Özeti

AOI maskelenmiş population count rasterı şu özelliklere sahiptir:

| Özellik | Değer |
|---|---|
| Raster boyutu | 1586 x 1423 |
| Pixel size | 100 m |
| CRS | EPSG:32635 |
| Minimum count | 0.000 |
| Maximum count | 159.301 |
| Mean count | 0.544 |
| NoData değeri | -9999 |
| Valid percent | 43.47 |

Population exposure score rasterı şu özelliklere sahiptir:

| Özellik | Değer |
|---|---|
| Raster boyutu | 1586 x 1423 |
| Pixel size | 100 m |
| CRS | EPSG:32635 |
| Minimum score | 0.000 |
| Maximum score | 1.000 |
| Mean score | 0.017 |
| NoData değeri | -9999 |
| Valid percent | 43.47 |

Raster extent ve çözünürlüğü ana MCDA analiz template'iyle eşleşir.

---

## 6. Nüfus Maruziyeti Skor Formülü

Nüfus maruziyeti skoru, AOI maskelenmiş population count rasterından log
normalization kullanılarak hesaplanmıştır:

```text
population_exposure_score = log(1 + population_count) / log(1 + max_population_count)
```

Bu analizde:

```text
max_population_count = 159.301
```

Bu log-normalization yaklaşımı, nüfus dağılımı oldukça çarpık olduğu için
kullanılmıştır. Doğrudan linear normalization, az sayıdaki yoğun kentsel hücrenin
tüm skor aralığını baskılamasına ve küçük yerleşimlerin görünürlüğünün
azalmasına yol açabilirdi.

Yorum:

| Population count | Göreli yorum |
|---:|---|
| 0 | Hücrede tahmini yerleşik nüfus yok |
| Düşük pozitif değerler | Düşük tahmini nüfus maruziyeti |
| Daha yüksek değerler | Daha yüksek tahmini nüfus maruziyeti |
| Gözlenen maksimum değer | Çalışma alanındaki en yüksek göreli nüfus maruziyeti |

AOI dışı alanlara NoData değeri olarak `-9999` atanmıştır.

---

## 7. Yorumlama

Population exposure score, Çanakkale çalışma alanı içindeki göreli tahmini nüfus
yoğunlaşmasını temsil eder.

Daha yüksek değerler, seçilen WorldPop constrained population ürününe göre daha
yüksek tahmini yerleşik nüfusa sahip hücreleri gösterir.

Bu katman bir maruziyet kriteri olarak yorumlanmalıdır; tehlike, kırılganlık,
risk, hasar, can kaybı veya resmi nüfus sayımı ürünü değildir.

---

## 8. Sınırlılıklar

Önemli sınırlılıklar:

- Kaynak veri seti gridded population estimate ürünüdür; doğrudan resmi sayım sınır katmanı değildir.
- Çıktı gerçek zamanlı veya gündüz nüfusunu temsil etmez.
- Mevsimsel, turistik, öğrenci, çalışan ve geçici nüfus değişimi temsil edilmez.
- Yaş, gelir, engellilik, hareketlilik ve hane yapısı gibi sosyal kırılganlık değişkenleri temsil edilmez.
- Constrained model, settlement/built-up inputları eksikse bazı küçük veya informal yerleşimleri eksik temsil edebilir.
- Nüfus maruziyeti tek başına afet riskini temsil etmez.
- Çıktı uzman doğrulaması olmadan resmi risk, tehlike, acil durum planlama veya karar destek ürünü olarak kullanılmamalıdır.

---

## 9. Kullanılan Katmanlar ve Doğrulama

Bu metodoloji kapsamında kullanılan proje dosyaları:

- `data/processed/population/population_count_aoi_100m_32635.tif`
- `data/processed/analysis/population_exposure_score_32635.tif`
- `docs/methodology/population_data_methodology_note.md`
- `scripts/bash/population_processing_pipeline.sh`

Doğrulama scripti, raw WorldPop rasterını yeniden üretim girdisi olarak
beklemez; mevcut processed-canonical population katmanını ve türetilmiş score
rasterını doğrular.
