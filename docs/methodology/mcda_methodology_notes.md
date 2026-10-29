# MCDA Metodoloji Notları — Önceki 8 Kriterli Sürüm

Bu doküman, projenin önceki 8 kriterli MCDA metodoloji notunu arşiv metodoloji
kaydı olarak korur. Ana rapor ve 11 kriterli analiz için birincil metodoloji
kaynağı `docs/methodology/updated_mcda_methodology_note.md` dosyasıdır.

## 1. Çalışma Amacı ve Kapsam

Bu çalışma, Çanakkale ili için seçilen açık ve işlenmiş coğrafi veri
katmanlarına dayalı olarak 100 m çözünürlüklü çok kriterli mekânsal öncelik
analizi üretmeyi amaçlamıştır.

Çalışma kesin afet riski, resmi tehlike haritası veya hasar tahmini üretmez.
Üretilen haritalar, seçilen kriterler ve ağırlıklar doğrultusunda göreli
mekânsal öncelik alanlarını gösteren ön değerlendirme niteliğinde çıktılardır.

Analiz kapsamında tüm raster kriterler ortak bir 100 m analiz şablonuna
hizalanmış, EPSG:32635 koordinat referans sisteminde işlenmiş ve AOI dışı
alanlar NoData olarak tanımlanmıştır.

---

## 2. Kullanılan Kriterler ve Ağırlıklar

Bu arşiv modelde nihai MCDA skorunun hesaplanmasında sekiz kriter kullanılır.
Tüm kriterler 0-1 aralığında skor rasterı olarak hazırlanmıştır.

| Kriter | Ağırlık | Gerekçe |
|---|---:|---|
| Taşkın Skoru | 0.18 | Taşkın derinliği verisine dayalı doğrudan tehlike göstergesidir. |
| Deprem PGA Skoru | 0.18 | AFAD PGA yüzeyine dayalı sismik tehlike göstergesidir. |
| Yapı Maruziyeti Yoğunluk Skoru | 0.18 | 100 m hücrelerdeki yapı footprint yoğunluğunu temsil eder ve maruziyet proxy'si olarak kullanılmıştır. |
| Eğim Skoru | 0.12 | Topografik kırılganlık, erişim zorluğu ve arazi stabilitesiyle ilişkili destekleyici kriterdir. |
| Ağaç Örtüsü Skoru | 0.10 | Vejetasyon yoğunluğunu temsil eder ve yangın/ekolojik duyarlılık için destekleyici göstergedir. |
| Arazi Örtüsü Duyarlılık Skoru | 0.10 | ESA WorldCover sınıflarına atanan duyarlılık skorlarına dayalıdır. |
| Hidrografya Yakınlık Skoru | 0.08 | Akarsu ve hidrografya ağına yakınlığı temsil eder; hidrolojik etkiyi destekleyici kriter olarak kullanılmıştır. |
| Yol Erişim Zorluğu Skoru | 0.06 | Yol ağına uzaklığı temsil eder ve müdahale/erişim zorluğu için destekleyici kriterdir. |

Ağırlıkların toplamı 1.00'dir.

Bu ağırlık seti uzman-yargısal ön değerlendirme yaklaşımıyla belirlenmiştir.
Ağırlıklar resmi kurum kararı, saha çalışması veya AHP tutarlılık analizi ile
doğrulanmış nihai ağırlıklar olarak değerlendirilmemelidir.

---

## 3. Nihai MCDA Formülü

Nihai ham MCDA öncelik skoru aşağıdaki ağırlıklı toplam formülü ile
hesaplanmıştır:

```text
MCDA =
  Taşkın Skoru * 0.18
+ Deprem PGA Skoru * 0.18
+ Yapı Maruziyeti Yoğunluk Skoru * 0.18
+ Eğim Skoru * 0.12
+ Ağaç Örtüsü Skoru * 0.10
+ Arazi Örtüsü Duyarlılık Skoru * 0.10
+ Hidrografya Yakınlık Skoru * 0.08
+ Yol Erişim Zorluğu Skoru * 0.06
```

---

## 4. Sınıflandırma Yöntemi

Normalize edilmiş MCDA öncelik skoru, 5 eşit aralıklı sınıfa ayrılmıştır.

| Sınıf kodu | Aralık | Etiket |
|---:|---:|---|
| 1 | 0.00 - 0.20 | Çok düşük |
| 2 | 0.20 - 0.40 | Düşük |
| 3 | 0.40 - 0.60 | Orta |
| 4 | 0.60 - 0.80 | Yüksek |
| 5 | 0.80 - 1.00 | Çok yüksek |

Equal interval sınıflandırma yöntemi, sınıf eşiklerinin şeffaf, tekrar
üretilebilir ve kolay yorumlanabilir olması nedeniyle tercih edilmiştir.

Quantile, natural breaks veya standard deviation gibi alternatif sınıflandırma
yöntemleri bu arşiv modelin kapsamı dışındadır.

---

## 5. Sınırlılıklar

Bu çalışmanın bazı önemli sınırlılıkları vardır:

- Sosyal kırılganlık verileri modele dahil edilmemiştir.
- Nüfus yoğunluğu doğrudan kullanılmamıştır; bunun yerine yapı footprint yoğunluğu maruziyet proxy'si olarak kullanılmıştır.
- Bina yaşı, kat sayısı, taşıyıcı sistem, yapı kalitesi veya hasar geçmişi gibi detaylı bina kırılganlık verileri kullanılmamıştır.
- Deprem kriteri PGA yüzeyine dayanmaktadır; zemin sınıfı, fay hattına uzaklık veya yerel jeolojik koşullar bu arşiv modele dahil edilmemiştir.
- Taşkın kriteri, kullanılan taşkın derinlik verisinin model varsayımlarına bağlıdır.
- Kriter ağırlıkları uzman-yargısal yaklaşımla belirlenmiştir; AHP veya resmi uzman görüşü ile doğrulanmamıştır.
- Nihai sınıflandırma equal interval yöntemiyle yapılmıştır; farklı sınıflandırma yöntemleri farklı mekânsal desenler üretebilir.

Bu sınırlılıklar nedeniyle çalışma, kesin afet riski veya resmi karar destek
ürünü olarak değil, ön değerlendirme ve mekânsal önceliklendirme çalışması
olarak yorumlanmalıdır.

---

## 6. Üretilen Ana Çıktılar

| Çıktı | Açıklama |
|---|---|
| `mcda_priority_score_32635.tif` | Ham ağırlıklı MCDA öncelik skoru |
| `mcda_priority_score_normalized_32635.tif` | 0-1 aralığına normalize edilmiş öncelik skoru |
| `mcda_priority_class_32635.tif` | 1-5 sınıflı nihai öncelik haritası |
| `scripts/bash/mcda_pipeline_commands.sh` | MCDA raster üretim komutlarını belgeleyen script |

---

## 7. Yorumlama Notu

Haritadaki yüksek değerler, seçilen kriterler ve ağırlıklar doğrultusunda
göreli olarak daha yüksek mekânsal öncelik gösteren alanları temsil eder. Bu
alanlar kesin afet tehlikesi veya kesin zarar beklentisi anlamına gelmez.
Sonuçlar; veri kalitesi, seçilen kriterler, ağırlıklar ve sınıflandırma yöntemi
ile birlikte değerlendirilmelidir.
