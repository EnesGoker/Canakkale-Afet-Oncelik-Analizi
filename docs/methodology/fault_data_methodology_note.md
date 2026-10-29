# Çanakkale Fay Hattı Veri Metodoloji Notu

## 1. Amaç

Bu doküman, Çanakkale fay yakınlığı analizinde kullanılan diri fay hattı veri
setinin hazırlanma ve doğrulama mantığını açıklar.

Amaç, Çanakkale çok kriterli afet öncelik analizi projesinde kullanılan teknik
olarak temiz fay hattı katmanını dokümante etmektir.

---

## 2. Kaynak Veri Seti

Kaynak veri seti, Türkiye Diri Fay Haritası veri paketiyle dağıtılan MTA diri
fay hattı veri setidir.

Büyük raw source dosyaları build girdisi olarak beklenmez; kaynak veri seti
düzeyinde upstream materyal olarak izlenir.

Raw source CRS WGS84 geographic coordinate system bilgisindedir. İşlenmiş proje
CRS değeri `EPSG:32635 - WGS 84 / UTM Zone 35N` olarak kullanılır.

---

## 3. İşleme Adımları

Fay verisi aşağıdaki sırayla işlenmiştir:

1. Raw MTA shapefile GeoPackage formatına dönüştürülmüştür.
2. GeoPackage uyumluluğu için geometri tipi MultiLineString'e yükseltilmiştir.
3. Veri seti WGS84 sisteminden EPSG:32635 sistemine reprojection işleminden geçirilmiştir.
4. Ulusal diri fay katmanı Çanakkale AOI sınırıyla clip edilmiştir.
5. Projected geometri kullanılarak `length_m` alanı hesaplanmıştır.
6. 10 metreden kısa çok küçük clipped sliver geometriler kaldırılmıştır.
7. Temizlenmiş fay hatları ana MCDA projesinde kullanılan aynı 100 m grid üzerine rasterize edilmiştir.
8. Fay mesafe rasterı üretilmiştir.
9. 10 km mesafe eşiği kullanılarak 0-1 fay yakınlığı score rasterı üretilmiştir.

Tam işleme dizisi şu scriptte dokümante edilmiştir:

- `scripts/bash/fault_processing_pipeline.sh`

Bu script, raw kaynak paketini zorunlu girdi olarak beklemek yerine
processed-canonical fay katmanını ve türetilmiş yakınlık skorunu doğrular.

---

## 4. Ana Çıktılar

| Çıktı | Açıklama |
|---|---|
| `data/processed/faults/canakkale_faults_final_32635.gpkg` | Temizlenmiş Çanakkale diri fay hattı katmanı |
| `data/processed/analysis/fault_proximity_score_32635.tif` | 0-1 normalize fay yakınlığı score rasterı |

---

## 5. QA Özeti

Nihai temizlenmiş fay katmanı şu özelliklere sahiptir:

| Özellik | Değer |
|---|---|
| Geometri | MultiLineString |
| CRS | EPSG:32635 |
| Feature sayısı | 207 |
| Toplam uzunluk | 476.89 km |
| Minimum segment uzunluğu | 11.15 m |
| Maksimum segment uzunluğu | 12,678.85 m |

Nihai fault proximity score rasterı şu özelliklere sahiptir:

| Özellik | Değer |
|---|---|
| Raster boyutu | 1586 x 1423 |
| Pixel size | 100 m |
| CRS | EPSG:32635 |
| Minimum score | 0.000 |
| Maximum score | 1.000 |
| Mean score | 0.333 |
| NoData değeri | -9999 |
| Valid percent | 43.47 |

Raster extent ve çözünürlüğü ana MCDA analiz template'iyle eşleşir.

---

## 6. Fay Yakınlığı Skor Formülü

Fault proximity score, faya uzaklık rasterından aşağıdaki formülle
hesaplanmıştır:

```text
fault_proximity_score = max(1 - distance_to_fault_m / 10000, 0)
```

Yorum:

| Faya uzaklık | Skor |
|---:|---:|
| 0 m | 1.00 |
| 5,000 m | 0.50 |
| 10,000 m veya daha fazla | 0.00 |

AOI dışı alanlara NoData değeri olarak `-9999` atanmıştır.

---

## 7. Yorumlama

Fault proximity score, haritalanmış diri fay hatlarına göreli mekânsal
yakınlığı temsil eder.

Daha yüksek değerler diri fay izlerine daha yakın alanları gösterir. Bu skor
deterministik deprem riski, beklenen hasar, yer sarsıntısı şiddeti veya resmi
tehlike zonlaması anlamına gelmez.

Skor yalnızca daha geniş bir çok kriterli analiz çerçevesi içinde destekleyici
geospatial kriter olarak yorumlanmalıdır.

---

## 8. Sınırlılıklar

Önemli sınırlılıklar:

- Kaynak diri fay veri seti haritalanmış fay izlerine ve ilgili kaynak dokümantasyonuna dayanır.
- Fay yakınlığı tek başına deprem tehlikesini temsil etmez.
- Yerel zemin koşulları, VS30, havza etkileri, sıvılaşma duyarlılığı, bina kırılganlığı ve nüfus maruziyeti bu kriter tarafından temsil edilmez.
- Bazı kaynak özniteliklerinde null değerler bulunur.
- Bazı kaynak metin alanlarında küçük Türkçe karakter encoding sorunları vardır.
- 10 km eşiği göreli yakınlık skorlama için metodolojik tasarım seçimidir; resmi tehlike mesafesi değildir.
- Çıktı uzman doğrulaması olmadan resmi risk, tehlike veya karar destek ürünü olarak kullanılmamalıdır.

---

## 9. Kullanılan Katmanlar ve Doğrulama

Bu metodoloji kapsamında kullanılan proje dosyaları:

- `data/processed/faults/canakkale_faults_final_32635.gpkg`
- `data/processed/analysis/fault_proximity_score_32635.tif`
- `docs/methodology/fault_data_methodology_note.md`
- `scripts/bash/fault_processing_pipeline.sh`

Doğrulama scripti, raw MTA shapefile paketini yeniden üretim girdisi olarak
beklemez; mevcut processed-canonical fay katmanını ve türetilmiş fault proximity
score rasterını doğrular.

## 10. AOI dışındaki faylar için doğrulama sınırı

23–24 Ekim 2026 incelemesinde yerel veri paketi ve korunan ZIP içinde AOI
dışına devam eden ayrı fay geometrisi bulunmadı. Mevcut kaynakla aynı grid ve
yöntem yeniden hesaplandığında skor farkı 0'dır. Bu, dışarıdaki fayların
içerideki yakınlık skoruna etkisini ölçmez.

Tamponlu karşılaştırma ve gerçek etkilenen alan, dış kaynak olmadan
hesaplanmış gibi sunulmaz. Koşul, uygulanamayan adımlar ve ileride gerekli
hizalı kapsam [sınır bulguları kaydında](../qa/stage3_boundary_findings.md#fay-yakınlığı-doğrulanan-ve-doğrulanamayan-kapsam)
açıklanır. Kırpma tek başına mevcut skorun yanlış olduğunu kanıtlamaz.
