# Harita Sembolojisi QA Notu

Proje: Çanakkale çok kriterli afet öncelik alanları analizi  
QGIS projesi: `qgis/canakkale_disaster_priority.qgz`  
CRS: EPSG:32635  
Grid çözünürlüğü: 100 m

Güncelleme: 2026-11-03

Bu kayıt, korunan ilk 12 haritanın stillerini ve
13. ve 14. QGIS düzenlerini kapsar. Yerel QGIS çıktısı ve 13 sayfalık atlas bu tasarımla
izlenir; 14. harita yalnız PNG'dir. Canlı CARTO altlığı için anahtar yalnız üretim sırasında uygulanır;
genel QGS/QGZ dosyası özgün anahtarsız URL'yi korur.

---

## 1. Amaç

Bu doküman, QGIS harita atlasında fiilen kullanılan stil kararlarını kaydeder.
Stil açıklamaları PNG/PDF, manuel lejant ve proje stilleriyle eşleştirilmiştir;
paletler ve 13. sayfanın tasarımı korunur. Makinece
denetlenen düzen/stil kayıtları [sözleşmede](../config/map_layouts_v1.json),
teslim doğrulaması [harita QA kaydında](qa/map_export_qa.md) yer alır.

Semboloji standardizasyonunun amacı, tüm harita çıktılarının görsel olarak
tutarlı, okunabilir ve metodolojik açıdan dikkatli kalmasını sağlamaktır.

Haritalar resmi tehlike haritaları değildir. Seçilmiş proxy kriterlere ve
ağırlıklı MCDA mantığına dayalı öncül mekânsal öncelik ve duyarlılık tarzı
çıktılardır.

---

## 2. Bilimsel ve Kartografik Uyarı

Harita ürünleri şu şekilde yorumlanmalıdır:

- öncül mekânsal öncelik haritaları
- duyarlılık tarzı proxy çıktıları
- karşılaştırmalı MCDA tabanlı değerlendirme katmanları
- seçilmiş kriterlerin kartografik özetleri

Şu şekilde yorumlanmamalıdır:

- resmi tehlike haritaları
- deterministik afet risk haritaları
- acil durum müdahale planları
- hukuken bağlayıcı planlama belgeleri
- saha doğrulamalı kırılganlık değerlendirmeleri

Semboloji, zayıf veya seyrek veri sinyallerini abartmak için değil,
okunabilirliği artırmak için kullanılır.

---

## 3. Katman Grubu Yönetişimi

QGIS layer panel aşağıdaki grup yapısını kullanır:

| Sıra | Grup adı | Amaç |
|---|---|---|
| 00 | `00_TEMEL_IDARI` | İl ve ilçe sınır katmanları |
| 01 | `01_REFERANS_KATMANLAR` | Opsiyonel bağlamsal referans katmanları |
| 02 | `02_KRITER_SKORLARI` | Normalize MCDA kriter skor rasterları |
| 03 | `03_ANALIZ_CIKTILARI` | Nihai MCDA score ve class çıktıları |
| 04 | `04_GRID_VE_SABLONLAR` | Analiz gridi ve layout/template yardımcı katmanları |
| 99 | `99_ARSIV_PASIF` | Arşivlenmiş veya pasif katmanlar |
| Base | `CartoDB Positron` | Basemap katmanı |

Ana QGIS ekranındaki görünürlük son kayıt sırasında seçilmiş katmana göre
farklılaşabilir. Atlasın içeriği bu genel aç/kapa durumundan bağımsızdır:
her haritanın katman kümesi ve stilleri kilitlidir, lejantı kendi haritasına
bağlıdır. Böylece başka bir kriter ana ekranda açıldığında hazırlanmış 14
QGIS düzeni birden o kritere dönüşmez. Atlas bu düzen sırasıyla 01–13 coğrafi sayfalarını içerir.

Tüm QGIS düzenlerinde il/ilçe sınırları ve CARTO altlığı tanımlıdır.
Altlığın tanımlı olması veya HTTP 200 yanıtı alması görsel kabul değildir;
teknik üretim sonrasında içerik ayrıca incelenir.
CARTO altlığı kullanılan üretimde `CARTO_BASEMAPS_API_KEY` gerekir;
salt okunur kontroller anahtar istemez;
anahtar palet/stil değişikliği değildir ve genel QGS/QGZ'ye kaydedilmez.
Genel projede özgün anahtarsız URL korunur. Özel yerel QGIS oturumunda canlı
altlık için kullanıcının kendi anahtarı gerekir; [üretim örneği](qa/map_export_qa.md)
anahtarı özel dosyadan, çıktıya basmadan okumayı gösterir. Tematik rasterın
üstündeki ek referanslar şöyledir:

| Sayfa | Ek referans |
|---|---|
| 01–02 | Diri fay hatları |
| 03 | Yerleşim noktaları |
| 04–05 | Yok |
| 06 | Yol ağı ve yerleşim noktaları |
| 07–08 | Hidrografya ağı |
| 09–11 | Yok |
| 12 | Yol ağı |
| 13 | Yok |
| 14 | Baseline yüksek+ sınırı |

Diğer kaynak/grid/POI katmanları sırf projede mevcut diye haritaya eklenmez.

---

## 4. QGIS Panelinde Gösterilmeyen Kaynak Raster Katmanları

Aşağıdaki kaynak raster katmanları QGIS layer panelinde varsayılan referans
katmanı olarak gösterilmez:

- Nüfus Sayısı 100m
- VS30 100m

Gerekçe:

Bu katmanlar kaynak/input raster katmanlarıdır; nihai harita referans katmanı
değildir. İşlenmiş analiz karşılıkları zaten kriter skor katmanlarıyla temsil
edilmektedir:

| Kaynak raster | İşlenmiş kriter katmanı |
|---|---|
| Nüfus Sayısı 100m | Nüfus Maruziyet Skoru |
| VS30 100m | Zemin Koşulu Skoru |

Kaynak raster dosyaları izlenebilirlik için proje veri klasörlerinde kalmalıdır,
ancak QGIS layer panelinde görünür referans katmanı olarak tutulmaz. Bu tercih,
layer panelini diğer kaynak raster veri setlerine uygulanan yaklaşımla tutarlı
tutar.

---

## 5. Opaklık ve Referans Katman Kuralları

Referans katmanlar rolüne, geometri tipine ve görsel yoğunluğuna göre opaklık
kullanır.

| Katman tipi | Standart opaklık mantığı |
|---|---|
| Ana il sınırı | 100% |
| Destekleyici ilçe sınırı | 70-80% |
| Kritik tematik çizgi referansı | 70-90% |
| Yoğun çizgi ağı | 50-60% |
| Nokta referans katmanı | 70-80% |
| Poligon referans katmanı | 30-50% |
| Basemap | 50% |

Amaç, ana analiz katmanının okunabilirliğini korurken mekânsal bağlam
sağlamaktır.

---

## 6. Basemap ve İdari Katman Stili

### CartoDB Positron

| Özellik | Değer |
|---|---|
| Rol | Basemap |
| Varsayılan görünürlük | Görünür |
| Opaklık | 50% |
| Kullanım | Konum bağlamı için arka plan haritası |

---

### Çanakkale İl Sınırı

| Özellik | Değer |
|---|---|
| Rol | Ana proje sınırı |
| Varsayılan görünürlük | Görünür |
| Dolgu | Şeffaf |
| Stroke rengi | Siyah |
| Stroke genişliği | 0.70 mm |
| Opaklık | 100% |

---

### Çanakkale İlçeleri

| Özellik | Değer |
|---|---|
| Rol | İlçe bağlam sınırı |
| Varsayılan görünürlük | Görünür |
| Dolgu | Şeffaf |
| Stroke rengi | Koyu gri |
| Stroke genişliği | 0.30 mm |
| Opaklık | 80% |

---

## 7. Referans Katman Stili ve Kullanım Kararları

### Yol Ağı

| Özellik | Değer |
|---|---|
| Geometri | Line |
| Rol | Opsiyonel yol ağı referansı |
| Varsayılan görünürlük | Gizli |
| Dolgu/çizgi rengi | #6B6B6B |
| Stroke genişliği | 0.18 mm |
| Opaklık | 55% |
| Kullanım | Opsiyonel destek haritası veya yol erişimi bağlamı |
| Ana atlas haritaları | 06 ve 12. sayfalarda görünür |

Gerekçe:

Yol ağı yalnız mevcut 06 ve 12. sayfalarda bağlamsal referans olarak korunur;
tüm kriter haritalarına genellenmez.

---

### Yerleşim Noktaları

| Özellik | Değer |
|---|---|
| Geometri | Point |
| Rol | Yerleşim bağlam referansı |
| Varsayılan görünürlük | Gizli |
| Dolgu rengi | #E76F51 |
| Stroke rengi | #FFFFFF |
| Sembol boyutu | 1.5 mm |
| Stroke genişliği | 0.15 mm |
| Opaklık | 75% |
| Kullanım | Opsiyonel yerleşim/nüfus bağlam haritaları |
| Ana atlas haritaları | 03 ve 06. sayfalarda görünür |

---

### Ulaşım Noktaları

| Özellik | Değer |
|---|---|
| Geometri | Point |
| Rol | Ulaşım bağlam referansı |
| Varsayılan görünürlük | Gizli |
| Dolgu rengi | #2A9D8F |
| Stroke rengi | #FFFFFF |
| Sembol boyutu | 1.7 mm |
| Stroke genişliği | 0.15 mm |
| Opaklık | 75% |
| Kullanım | Opsiyonel ulaşım/erişilebilirlik destek haritaları |
| Ana atlas haritaları | Varsayılan olarak gizli |

---

### İlgi Noktaları POI

| Özellik | Değer |
|---|---|
| Geometri | Point |
| Rol | Genel POI bağlamı |
| Varsayılan görünürlük | Gizli |
| Dolgu rengi | #8E44AD |
| Stroke rengi | #FFFFFF |
| Sembol boyutu | 1.4 mm |
| Stroke genişliği | 0.12 mm |
| Opaklık | 70% |
| Kullanım | Opsiyonel destek/bağlam haritaları |
| Ana atlas haritaları | Varsayılan olarak gizli |

---

### Diri Fay Hatları

| Özellik | Değer |
|---|---|
| Geometri | Line |
| Rol | Kritik tematik sismik referans |
| Varsayılan görünürlük | Gizli |
| Çizgi rengi | #6A3D9A |
| Stroke genişliği | 0.45 mm |
| Opaklık | 90% |
| Kullanım | 01 nihai öncelik ve 02 fay yakınlığı sayfaları |

Gerekçe:

Fay hatları, yüksek risk algısı veren kırmızı/turuncu raster sınıflarıyla görsel
karışıklık yaratmamak için kırmızı yerine mor renkte stillendirilmiştir.

---

### Hidrografya Ağı

| Özellik | Değer |
|---|---|
| Geometri | Line |
| Rol | Hidrografya referansı |
| Varsayılan görünürlük | Gizli |
| Çizgi rengi | #2C7FB8 |
| Stroke genişliği | 0.30 mm |
| Opaklık | 70% |
| Kullanım | Taşkın skoru haritası ve opsiyonel hidrografya bağlam haritaları |

Gerekçe:

Hidrografya ağı mevcut 07 taşkın ve 08 hidrografya yakınlığı sayfalarında
bağlamsal referans olarak kullanılır. Bu karar manuel lejant ve eski
harita çıktılarıyla uyumludur; başka bir skor rasterı eklenmez.

---

### Arazi Kullanımı

| Özellik | Değer |
|---|---|
| Geometri | Polygon |
| Rol | Arazi kullanımı source/reference bağlamı |
| Varsayılan görünürlük | Gizli |
| Dolgu rengi | #B56576 |
| Stroke rengi | #FFFFFF |
| Stroke genişliği | 0.10 mm |
| Opaklık | 40% |
| Kullanım | Opsiyonel arazi kullanımı/source destek haritası |
| Ana atlas haritaları | Varsayılan olarak gizli |

Gerekçe:

İşlenmiş analiz karşılığı `Arazi Örtüsü Duyarlılık Skoru` ile temsil edilir.
Raw/reference arazi kullanımı katmanı ana kriter haritalarında gösterilmemelidir.

---

### Yapı Veri Seti

| Özellik | Değer |
|---|---|
| Geometri | Polygon |
| Rol | Microsoft building footprint source/reference katmanı |
| Varsayılan görünürlük | Gizli |
| Dolgu rengi | #4D908E |
| Stroke rengi | #4D908E |
| Stroke genişliği | 0.08 mm |
| Opaklık | 45% |
| Kullanım | Opsiyonel bina verisi kapsam destek haritası |
| Ana atlas haritaları | Varsayılan olarak gizli |

Gerekçe:

İşlenmiş analiz karşılığı `Yapı Maruziyeti Yoğunluk Skoru` ile temsil edilir.
Raw building footprintler düzenli atlas haritaları için fazla yoğundur.

---

## 8. Genel Kriter Raster Stili Standardı

Aksi belirtilmedikçe tüm normalize kriter skor rasterları şunları kullanır:

| Ayar | Değer |
|---|---|
| Render tipi | Singleband pseudocolor |
| Minimum | 0 |
| Maximum | 1 |
| Interpolation | Discrete |
| Mode | Equal interval |
| Sınıf sayısı | 5 |
| Etiketler | Çok Düşük, Düşük, Orta, Yüksek, Çok Yüksek |
| NoData | Gizli / şeffaf |

Tüm kriter haritalarında beş sınıf korunur; bu tercih nihai MCDA
sınıflandırmasıyla tutarlılık sağlar.

Bazı seyrek kriterler görsel olarak sınırlı görünebilir. Bu durum input veri
dağılımının özelliği olarak kabul edilir ve sembolojiyle abartılmamalıdır.

---

## 9. Nihai MCDA Öncelik Sınıfı

| Sınıf | Etiket | Renk |
|---|---|---|
| 1 | Çok Düşük | #1A9850 |
| 2 | Düşük | #91CF60 |
| 3 | Orta | #FFFFBF |
| 4 | Yüksek | #FC8D59 |
| 5 | Çok Yüksek | #D73027 |

Kullanım:

- Ana nihai atlas haritası
- Nihai öncelik sınıfı çıktısı
- Resmi afet riski olarak değil, göreli mekânsal öncelik olarak yorumlanmalıdır

---

## 10. Kriter Renk Paletleri

### Fay Yakınlık Skoru

| Sınıf | Etiket | Renk |
|---|---|---|
| 1 | Çok Düşük | #FFF7BC |
| 2 | Düşük | #FEE391 |
| 3 | Orta | #FEC44F |
| 4 | Yüksek | #FE9929 |
| 5 | Çok Yüksek | #CC4C02 |

Referans kararı:

- `Diri Fay Hatları` gösterilebilir.
- Fay hatları, yüksek skorlu raster renkleriyle karışmaması için mor renktedir.

---

### Nüfus Maruziyet Skoru

| Sınıf | Etiket | Renk |
|---|---|---|
| 1 | Çok Düşük | #F7FCF0 |
| 2 | Düşük | #C7E9B4 |
| 3 | Orta | #7FCDBB |
| 4 | Yüksek | #41B6C4 |
| 5 | Çok Yüksek | #253494 |

Referans kararı:

- `Yerleşim Noktaları` mevcut 03. haritada görünür.
- Aynı referans 06 yapı maruziyeti sayfasında da bulunur.

---

### Zemin Koşulu Skoru

| Sınıf | Etiket | Renk |
|---|---|---|
| 1 | Çok Düşük | #FFFFD4 |
| 2 | Düşük | #FED98E |
| 3 | Orta | #FE9929 |
| 4 | Yüksek | #D95F0E |
| 5 | Çok Yüksek | #993404 |

Yorum notu:

- Daha yüksek skor, daha elverişsiz site-condition proxy değerini temsil eder.
- Yerel jeoteknik etüdün yerine geçmez.

---

### Deprem PGA Skoru

| Sınıf | Etiket | Renk |
|---|---|---|
| 1 | Çok Düşük | #FFFFCC |
| 2 | Düşük | #FFFBC1 |
| 3 | Orta | #FFD076 |
| 4 | Yüksek | #F4592B |
| 5 | Çok Yüksek | #BD0026 |

Referans kararı:

- `Diri Fay Hatları` varsayılan olarak gösterilmez.
- PGA ve fay yakınlığı ayrı kriterler olarak ele alınır.

---

### Yapı Maruziyeti Yoğunluk Skoru

| Sınıf | Etiket | Renk |
|---|---|---|
| 1 | Çok Düşük | #F2F0F7 |
| 2 | Düşük | #CBC9E2 |
| 3 | Orta | #9E9AC8 |
| 4 | Yüksek | #6A51A3 |
| 5 | Çok Yüksek | #3F007D |

Referans kararı:

- Raw `Yapı Veri Seti` ana haritaya eklenmez.
- Mevcut 06. sayfada `Yol Ağı` ve `Yerleşim Noktaları` görünür.
- Raster, işlenmiş building exposure density değerini temsil eder.

---

### Taşkın Skoru

| Sınıf | Etiket | Renk |
|---|---|---|
| 1 | Çok Düşük | #EFF3FF |
| 2 | Düşük | #BDD7E7 |
| 3 | Orta | #6BAED6 |
| 4 | Yüksek | #3182BD |
| 5 | Çok Yüksek | #08519C |

Referans kararı:

- `Hidrografya Ağı` açık mavi referans katmanı olarak gösterilebilir.
- `Hidrografya Yakınlık Skoru`, `Taşkın Skoru` ile birlikte gösterilmez.

---

### Hidrografya Yakınlık Skoru

| Sınıf | Etiket | Renk |
|---|---|---|
| 1 | Çok Düşük | #F7FBFF |
| 2 | Düşük | #C6DBEF |
| 3 | Orta | #6BAED6 |
| 4 | Yüksek | #2171B5 |
| 5 | Çok Yüksek | #08519C |

Referans kararı:

- `Hidrografya Ağı` mevcut 08. sayfada görünür; eski manuel lejant ve
  harita çıktısındaki tercih korunur.

---

### Eğim Skoru

| Sınıf | Etiket | Renk |
|---|---|---|
| 1 | Çok Düşük | #FFFFE5 |
| 2 | Düşük | #FFF7BC |
| 3 | Orta | #D9F0A3 |
| 4 | Yüksek | #78C679 |
| 5 | Çok Yüksek | #238443 |

---

### Arazi Örtüsü Duyarlılık Skoru

| Sınıf | Etiket | Renk |
|---|---|---|
| 1 | Çok Düşük | #F7FCB9 |
| 2 | Düşük | #ADDD8E |
| 3 | Orta | #78C679 |
| 4 | Yüksek | #41AB5D |
| 5 | Çok Yüksek | #006837 |

Not:

- Atlas genelinde tutarlılık için beş sınıf korunur.
- Bazı sınıflar görsel olarak geniş alan kaplayabilir; çünkü land-cover
  sensitivity mekânsal olarak yaygındır.

---

### Ağaç Örtüsü Skoru

| Sınıf | Etiket | Renk |
|---|---|---|
| 1 | Çok Düşük | #F7FCF5 |
| 2 | Düşük | #C7E9C0 |
| 3 | Orta | #74C476 |
| 4 | Yüksek | #238B45 |
| 5 | Çok Yüksek | #00441B |

---

### Yol Erişim Zorluğu Skoru

| Sınıf | Etiket | Renk |
|---|---|---|
| 1 | Çok Düşük | #F7F7F7 |
| 2 | Düşük | #D9D9D9 |
| 3 | Orta | #BDBDBD |
| 4 | Yüksek | #737373 |
| 5 | Çok Yüksek | #252525 |

Referans kararı:

- `Yol Ağı` mevcut 12. sayfada bağlamsal referans olarak görünür.
- Tematik raster yol erişim zorluğu skorudur; yol ağı ayrı bir skor değildir.

---

## 11. Senaryo ortaklığı ve layout kuralları

13. sayfanın rasterı kriter skoru değil, yüksek/çok yüksek sınıfa giren
senaryo sayısıdır. EXACT eşleştirmede kullanılan renkler ve etiketler:

| Değer | Renk | Açıklama |
|---:|---|---|
| 0 | #E2E5E9 | Hiçbir senaryoda yüksek değil |
| 1 | #F8D36A | Yalnız 1 senaryoda yüksek |
| 2 | #E98747 | Yalnız 2 senaryoda yüksek |
| 3 | #542788 | Üç senaryoda da yüksek |

Değerler tam 0, 1, 2, 3 olmalıdır; yuvarlama sonucu böyle görünen kesirli
sınıf eşikleri kabul edilmez. Sürekli lejant kapalıdır; dört ayrı renk kutusu
kullanılır. Görsel yeniden örnekleme en yakın komşudur. Kilitli stil bu
ayarları da içerir.

14. sayfanın rasterı, 2.000 ağırlık örneğinde sıralama tabanlı yüksek+ sınıfta
kalma sayısıdır (P(yüksek+) = sayım / 2.000; κ = 100). DISCRETE eşleştirme
ColorBrewer Purples dizisinin altı sınıflı sürümünü, en açık tonu atlayarak kullanır:

| Sayım üst sınırı | P(yüksek+) | Renk | Not |
|---:|---|---|---|
| 0 | P = 0 | #ffffff | Saydam; altlık görünür |
| 499 | 0 < P < 0,25 | #dadaeb | |
| 999 | 0,25 ≤ P < 0,50 | #bcbddc | |
| 1499 | 0,50 ≤ P < 0,75 | #9e9ac8 | |
| 1799 | 0,75 ≤ P < 0,90 | #756bb1 | |
| 2000 | P ≥ 0,90 | #54278f | |

Tek renk tonlu sıralı palette açıklık tekdüze azalır. Sürekli lejant kapalıdır;
altı ayrı kutu kullanılır. Baseline yüksek+ (4.–5. sınıf) sınırı 0,15 mm
#4d4d4d çizgiyle rasterın üstündedir; lejantta ayrı satırdır. Lejant notu
değerin afet olasılığı olmadığını belirtir.

Kriter rasterlarının kayıtlı beş sınıfı ve renkleri korunur. Bazı stillerde
son eşik `inf` olarak kaydedilmiştir; bu, son renk aralığının üst sınırıdır.
Raster veride Inf bulunduğu anlamına gelmez; veri sonluluğu ve 0–1 aralığı
sayısal QA ile ayrıca kontrol edilir.


Nihai harita layoutları için:

- Lejantta yalnızca ana harita katmanı ve gerekli referans katmanları
  görünmelidir.
- Gizli destek katmanları lejantta görünmemelidir.
- Lejant başlığı sade ve haritaya özgü olmalıdır.
- Referans katmanları yalnızca yorumu doğrudan desteklediğinde eklenmelidir.
- İşlenmiş score katmanı zaten ana haritaysa kaynak/input katmanları
  gösterilmemelidir.

Gerekli layout öğeleri:

- harita başlığı
- alt başlık
- lejant
- ölçek çubuğu
- kuzey oku
- CRS notu
- grid çözünürlüğü notu
- bilgi kutusunda mevcut kriter/kaynak referansı

Ayrıntılı atıflar ve yöntem sınırları [harita notu](../outputs/maps/README.md),
[atlas notu](../outputs/atlas/README.md) ve [veri hakları kaydında](data_rights_and_distribution.md)
tutulur. Bunların tümünün mevcut sayfalarda basılı olduğu iddia edilmez;
13. sayfanın kayıtlı tasarımında ek atıf metin kutuları bulunmaz.

Önerilen export ayarları:

| Export | Ayar |
|---|---|
| PNG | 300 DPI |
| PDF | Vector/raster mixed export kabul edilebilir |
| Arka plan | Şeffaf değil |
| Adlandırma | Harita atlası planındaki tutarlı dosya adları kullanılır |

---

## 12. QA Özeti

2026-10-24 tesliminde 13 PNG/PDF ve 13 sayfalık atlas görsel kontrolden
geçmiştir. Düzen/stil ve kayıtlı dosya kontrolü 13 düzen, 27 çıktı ve 0 hata
raporlamış; ana canonical QA çıkış 0 ile tamamlanmıştır. Teknik üretim
başarısı ayrıca görsel incelemeyle desteklenmiştir.

2026-11-02 (v0.2) güncellemesinde düzenlere alt bant atıf etiketi eklenmiş,
lejantta görünen katman ve grup adları Türkçe yazımla düzeltilmiştir (ör.
"Çanakkale İl Sınırı", "Diri Fay Hatları", "Analiz Çıktıları"). Stiller ve
paletler değişmemiştir; düzen/çıktı kontrolü 13 düzen ve 27 dosyayı doğrular.

2026-11-03'te 14. düzen (yüksek öncelikte kalma oranı) eklenmiştir; 01–13'ün
stilleri ve paletleri değişmemiştir. Düzen/çıktı kontrolü 14 düzen ve 28
dosyayı doğrular.

Tamamlananlar:

- ana idari sınır stili
- basemap opaklık standardizasyonu
- referans katman yönetişimi
- referans vektör stili
- kriter raster sembolojisi
- nihai MCDA class sembolojisi
- her atlas sayfasına özel katman/stil kilidi ve lejant bağlantısı
- kaynak raster panel temizliği

Kartografik kararlar:

- tüm normalize kriter haritaları için beş sınıf korunur
- seyrek kriterler yapay olarak abartılmaz
- source rasterlar varsayılan referans katmanı olarak tutulmaz
- yoğun raw veri setleri varsayılan olarak gizlidir
- referans katmanları yalnızca yorumu desteklediğinde kullanılır
- atlas sayfaları ana ekran görünürlüğünden bağımsız açılır

---

## 13. Semboloji Kalite Özeti

Semboloji ve layer panel standardı aşağıdaki kalite ilkelerine dayanır:

- ana idari sınır ve basemap stili tutarlı kullanılır
- referans katmanları yalnızca harita yorumunu doğrudan desteklediğinde görünür olur
- normalize kriter rasterları beş sınıflı ortak okuma dili kullanır
- nihai MCDA class haritası ayrı sınıf paletiyle sunulur
- kaynak rasterlar ve yoğun raw veri setleri varsayılan harita görünümünü bastırmaz
- 13. QGIS düzeni kayıtlı sayfa tasarımını ve tam sayılı renk sınıflarını korur
- 14. QGIS düzeni aynı sayfa tasarımını DISCRETE altı sınıflı tek ton paletle kullanır
- nihai 13. PNG/PDF ve atlas güncellemesi teknik kontrolle birlikte görsel kabul kapsamındadır
