# Rapor Varlıkları ve Akademik Rapor Yapısı

**Kaynak sürümü kapsamı:** Aşağıdaki harita, raster, atlas ve Word/PDF
yolları tam yerel çalışma çıktısıdır; bu dosyalar kaynak ve analitik özet
sürümünde dağıtılmaz. Yerel üretim/kontrol komutları ilgili kanonik veri ve
çıktıların ayrıca bulunmasını gerektirir. [Kamu dosya kapsamı](publication_file_scope.md).

Proje: Çanakkale çok kriterli afet öncelik alanları analizi

Varlık seti, 13 QGIS haritasının PNG/PDF çıktıları ile 13 sayfalık atlası
içerir. Kamu Word raporu 13 coğrafi haritayı ve ayrı korelasyon figürünü
toplam 14 şekil olarak sunar.

Bu doküman, kamu raporunun varlık setini ve bölüm/şekil sırasını kaydeder.
Düzenlenebilir ana kaynak
`outputs/report/canakkale_disaster_priority_public_report.docx`,
okuma kopyası ise
18 sayfalık PDF (`outputs/report/canakkale_disaster_priority_public_report.pdf`)
dosyasıdır. Pages dosyaları yerel arşivdir ve kamu dağıtımında yer almaz.
Akademik DOCX üreticisi ayrı bir 12 haritalı rapor üretir; hazır kamu Word
raporunu yeniden oluşturmaz.

## 1. Kapsam

Rapor; veri, harita, MCDA rasterı ve tablo üretimlerini yeniden çalıştırmak
yerine proje içindeki canonical varlıkları kullanır.

Rapor girdileri:

| Varlık grubu | Konum | Rapordaki rol |
|---|---|---|
| Tekil harita PNG'leri | `outputs/maps/png/` | Ana gövde figure yerleşimi |
| Tekil harita PDF'leri | `outputs/maps/pdf/` | Kaynak kalitesinde harita arşivi / opsiyonel ek |
| Birleşik harita atlası PDF | `outputs/atlas/canakkale_afet_oncelik_harita_atlasi.pdf` | Atlas referansı / opsiyonel ek |
| Rapor tabloları | `outputs/tables/` | Sonuç tabloları ve istatistik özetleri |
| Metodoloji dokümanları | `docs/methodology/` | Yöntem, CRS, sınırlılıklar ve kriter ağırlıkları |
| Kaynak envanteri | `docs/data_source_inventory.md` | Veri kaynağı anlatımı |
| Canonical veri politikası | `docs/canonical_data_policy.md` | Ham veri ve processed-canonical açıklaması |

Büyük upstream ham veri setleri rapor girdisi değildir.

## 2. Harita Varlıkları

Harita varlıkları rapor ve atlas kullanımı için aşağıdaki yapıdadır:

| Kontrol | Sonuç |
|---|---:|
| Tekil PDF haritalar | 13 |
| Tekil PNG haritalar | 13 |
| PDF/PNG dosya kökü eşleşmesi | 01–13 aynı kök; final manifestiyle denetlenir |
| Sayısal prefix sırası | 01–13 |
| PNG boyutları | 4960 × 3507 px; A3 yatay, 300 DPI |
| Tekil PDF sayfaları | Her biri 1 sayfa |
| PDF sayfa boyutu | A3 yatay; üretim sırasında doğrulanır |
| Birleşik atlas sayfaları | 13 |
| Birleşik atlas sayfa boyutu | A3 yatay |
| Görsel kontrol | 13 PNG/PDF bağımsız incelemeden geçti |

Atlas harita sırası (raporun şekil sırası aşağıda ayrıca belirtilir):

| Atlas no | Harita başlığı | PNG varlığı | PDF varlığı |
|---:|---|---|---|
| 1 | Çok Kriterli Afet Öncelik Sınıfı | `outputs/maps/png/01_cok_kriterli_oncelik_sinifi.png` | `outputs/maps/pdf/01_cok_kriterli_oncelik_sinifi.pdf` |
| 2 | Fay Yakınlık Skoru | `outputs/maps/png/02_fay_yakinlik_skoru.png` | `outputs/maps/pdf/02_fay_yakinlik_skoru.pdf` |
| 3 | Nüfus Maruziyet Skoru | `outputs/maps/png/03_nufus_maruziyet_skoru.png` | `outputs/maps/pdf/03_nufus_maruziyet_skoru.pdf` |
| 4 | Zemin Koşulu Skoru | `outputs/maps/png/04_zemin_kosulu_skoru.png` | `outputs/maps/pdf/04_zemin_kosulu_skoru.pdf` |
| 5 | Deprem PGA Skoru | `outputs/maps/png/05_deprem_pga_skoru.png` | `outputs/maps/pdf/05_deprem_pga_skoru.pdf` |
| 6 | Yapı Maruziyet Yoğunluk Skoru | `outputs/maps/png/06_yapi_maruziyet_yogunluk_skoru.png` | `outputs/maps/pdf/06_yapi_maruziyet_yogunluk_skoru.pdf` |
| 7 | Taşkın Skoru | `outputs/maps/png/07_taskin_skoru.png` | `outputs/maps/pdf/07_taskin_skoru.pdf` |
| 8 | Hidrografya Yakınlık Skoru | `outputs/maps/png/08_hidrografya_yakinlik_skoru.png` | `outputs/maps/pdf/08_hidrografya_yakinlik_skoru.pdf` |
| 9 | Eğim Skoru | `outputs/maps/png/09_egim_skoru.png` | `outputs/maps/pdf/09_egim_skoru.pdf` |
| 10 | Arazi Örtüsü Duyarlılık Skoru | `outputs/maps/png/10_arazi_ortusu_duyarlilik_skoru.png` | `outputs/maps/pdf/10_arazi_ortusu_duyarlilik_skoru.pdf` |
| 11 | Ağaç Örtüsü Skoru | `outputs/maps/png/11_agac_ortusu_skoru.png` | `outputs/maps/pdf/11_agac_ortusu_skoru.pdf` |
| 12 | Yol Erişim Zorluğu Skoru | `outputs/maps/png/12_yol_erisim_zorlugu_skoru.png` | `outputs/maps/pdf/12_yol_erisim_zorlugu_skoru.pdf` |
| 13 | Üç Senaryoda Yüksek Öncelik Ortaklığı | `outputs/maps/png/13_senaryo_ortakligi.png` | `outputs/maps/pdf/13_senaryo_ortakligi.pdf` |

13. harita, senaryo ortaklığını atlasın A3 yatay QGIS tasarımıyla sunar.
Düzen bağları/stilleri [map_layouts_v1.json](../config/map_layouts_v1.json),
ürün özeti [map_export_manifest.json](../outputs/maps/map_export_manifest.json),
doğrulama sonuçları [harita QA kaydında](qa/map_export_qa.md) tutulur.

Korelasyon matrisi coğrafi atlasın parçası değildir; raporda ayrı bir analiz
figürü olarak kullanılır:

- PNG: `outputs/figures/criterion_correlation_v1/criterion_pearson_correlation.png`
- PDF: `outputs/figures/criterion_correlation_v1/criterion_pearson_correlation.pdf`
- Yorum: [korelasyon analizi](analysis/criterion_correlation.md)

Kamu Word raporunda Şekil 1–12, atlasın 01–12 haritalarıdır. Şekil 13 korelasyon
matrisi, Şekil 14 ise atlasın 13. QGIS ortaklık haritasıdır. Böylece raporda
14 şekil, coğrafi atlas içinde 13 harita bulunur.

Bağımsız senaryo ortaklığı figürü ayrı bir analiz çıktısıdır. Rapor ve
coğrafi atlasta kullanılan harita, yukarıdaki QGIS düzeni çıktısıdır.
Rapor varlığı seçimi, kayıtlı kapsam ve görsel kontrol ölçütleriyle yapılır.
`CARTO_BASEMAPS_API_KEY` yalnız üretim ortamına sağlanır; rapor, kaynak QGIS
projesi ve Git deposunda yer almaz. Genel QGIS projesinin anahtarsız URL'yi
koruması ile nihai haritanın kimlik doğrulamalı üretilmesi bilinçli bir ayrımdır.
Anahtarın varlığı, teknik üretimin veya görsel kabulün otomatik olarak başarılı
olduğu anlamına gelmez.

Rapor yerleşim kuralı:

- Kamu Word raporunda şekiller için tanımlı PNG varlıkları kullanılır.
- Tekil PDF haritalar kaynak kalitesindeki exportlar olarak korunur.
- Birleşik atlas PDF, tamamlayıcı atlas ürünü olarak anılır.

## 3. Tablo Varlıkları

Rapor tabloları aşağıdaki CSV dosyalarından oluşur.

| Tablo | Dosya | Satır | Rapordaki kullanım |
|---|---|---:|---|
| MCDA class dağılımı | `outputs/tables/mcda_class_distribution.csv` | 5 | Ana sonuç özeti |
| İlçe x MCDA class alanı | `outputs/tables/mcda_class_area_by_district.csv` | 60 | İlçe düzeyi sonuç tablosu |
| Kriter raster istatistikleri | `outputs/tables/criterion_raster_statistics.csv` | 14 | Yöntem/istatistik eki veya kompakt yöntem tablosu |
| Kriter korelasyon matrisi | `outputs/tables/criterion_correlation_v1/criterion_pearson_correlation.csv` | 11 | 11 × 11 Pearson matrisi ve ayrı figürü |
| Korelasyon girdi istatistikleri | `outputs/tables/criterion_correlation_v1/criterion_correlation_statistics.csv` | 11 | Sıfır oranı ve değişkenlik bağlamı |
| Ortaklık sayısı il/ilçe özeti | `outputs/analysis/scenario_agreement_v1/agreement_count_summary.csv` | 52 | 0–3 senaryo sayısının alan dağılımı |
| Senaryo üyelik il/ilçe özeti | `outputs/analysis/scenario_agreement_v1/agreement_membership_summary.csv` | 104 | Hangi senaryoların ortak olduğunun ayrımı |
| Senaryo yüksek alanı karşılaştırması | `outputs/analysis/scenario_agreement_v1/scenario_high_area_comparison.csv` | 39 | Üç senaryonun il/ilçe yüksek öncelik alanları |


Senaryo ortaklığı tabloları birlikte 195 veri satırı içerir; il toplamı ile
12 ilçenin özetlerini kapsar. Sekiz baseline referans CSV'sinden ayrı analiz
çıktılarıdır.
Kaynak dosya sürümleri analiz manifestleriyle eşleştirilir.

Baseline tablo QA:

| Kontrol | Sonuç |
|---|---:|
| MCDA class satırları | 5 |
| İlçe-class satırları | 60 |
| İlçe sayısı | 12 |
| MCDA class değerleri | 1-5 |
| Kriter raster satırları | 11 |
| MCDA raster satırları | 3 |
| Geçerli MCDA class pikselleri | 981033 |
| Geçerli MCDA class alanı km2 | 9810.33 |
| District id değeri olmayan class pikselleri | 0 |

MCDA sınıf dağılımı:

| Class | Piksel | Alan km2 | Pay yüzde |
|---:|---:|---:|---:|
| 1 | 114283 | 1142.83 | 11.6493 |
| 2 | 483129 | 4831.29 | 49.2470 |
| 3 | 329029 | 3290.29 | 33.5390 |
| 4 | 53893 | 538.93 | 5.4935 |
| 5 | 699 | 6.99 | 0.0713 |

## 4. Metodoloji Kaynakları

Rapor metodolojisi, 11 kriterli MCDA modelini kullanır.

Operasyonel ağırlık kaynağı:

```text
config/mcda_weights.tsv
```

Baseline kriterler ve ağırlıklar:

| No | Kriter | Ağırlık |
|---:|---|---:|
| 1 | Earthquake PGA Score | 0.16 |
| 2 | Fault Proximity Score | 0.12 |
| 3 | Site Condition Score | 0.08 |
| 4 | Population Exposure Score | 0.14 |
| 5 | Building Exposure Density Score | 0.10 |
| 6 | Flood Score | 0.10 |
| 7 | Hydrography Proximity Score | 0.06 |
| 8 | Slope Score | 0.08 |
| 9 | Landcover Sensitivity Score | 0.06 |
| 10 | Tree Cover Score | 0.04 |
| 11 | Road Accessibility Difficulty Score | 0.06 |
| Toplam |  | 1.00 |

Yorum sınırı: Bu ağırlık seti AHP, resmi uzman anketi veya gözlenmiş afet kaybı
kalibrasyonu olarak sunulmamalıdır. Gerekçe ve blok dengesi için birincil kaynak
`docs/methodology/updated_mcda_methodology_note.md` dosyasındaki
"Ağırlıklandırma Stratejisi" bölümüdür.

Metodoloji kaynak dokümanları:

| Konu | Kaynak doküman |
|---|---|
| 11 kriterli MCDA modeli | `docs/methodology/updated_mcda_methodology_note.md` |
| Operasyonel ağırlık config'i | `config/mcda_weights.tsv` |
| CRS ve projected analysis politikası | `docs/methodology/crs_policy.md` |
| Bilimsel sınırlılıklar | `docs/methodology/scientific_limits.md` |
| Nüfus işleme notu | `docs/methodology/population_data_methodology_note.md` |
| VS30/site condition notu | `docs/methodology/vs30_data_methodology_note.md` |
| Fay yakınlığı notu | `docs/methodology/fault_data_methodology_note.md` |
| Kaynak envanteri | `docs/data_source_inventory.md` |
| Canonical veri politikası | `docs/canonical_data_policy.md` |

## 5. Rapor Yapısı

Kamu Word raporunun yapısı:

| Bölüm | İçerik | Birincil varlıklar |
|---|---|---|
| Başlık sayfası | Proje başlığı, yazar/ders bilgileri, tarih | Yok |
| Abstract / Öz | Amaç, veri seviyesi, yöntem, temel bulgular, sınırlılıklar | Sınıf dağılımı özeti |
| 1. Giriş | Çalışma motivasyonu ve rapor kapsamı | Bilimsel sınırlılıklar |
| 2. Çalışma Alanı, CRS ve Grid | Çanakkale AOI, EPSG:32635, 100 m grid | CRS politikası |
| 3. Veri ve Veri Yönetimi | Canonical girdiler, upstream kaynaklar, ham veri politikası | Kaynak envanteri, canonical politika |
| 4. Yöntem | 11 kriter, skor mantığı, ağırlıklar, WLC formülü, sınıflandırma | Metodoloji kaynakları |
| 5. Bulgular | MCDA class dağılımı ve ilçe düzeyi sonuçlar | Tablolar, Figure 1 |
| 6. Kriter Haritaları | 11 kriter haritası | Şekil 2–12 |
| 7. Ek Analizler | 7.1 Kriterler Arasındaki Pearson Korelasyonu; 7.2 Üç Senaryoda Yüksek Öncelik Alanlarının Mekânsal Ortaklığı | Şekil 13–14; Tablo 6 |
| 8. Tartışma ve Sınırlılıklar | Yorum sınırları, proxy niteliği, mevcut olmayan kriterler | Bilimsel sınırlılıklar |
| 9. Sonuç | Nihai özet ve uygun kullanım beyanı | Temel tablo/figure referansları |
| Kaynak Veri Setleri | Dataset-level kaynak listesi | Kaynak envanteri |
| Ek A / Ek B | İlçe sınıf alanları ve raster istatistikleri | Tablo A1 / B1; tamamlayıcı atlas referansı |

Rapordaki tablolar 1–6, A1 ve B1 olarak sıralanır. Tablo 6, il geneli ile
Yenice, Gelibolu ve Çan için ortak/değişen yüksek alanları ve her kapsamın
kendi raster AOI paylarını verir. Korelasyon
mekânsal bağımlı işlenmiş skorları betimler; ağırlık değiştirme talimatı veya
nedensellik testi değildir. Senaryo ortaklığı, alternatiflerin kendi min–max
normalizasyonunu da içerir. İlgili [analiz yorumu](analysis/scenario_agreement.md)
raporda bu yorum sınırıyla kullanılmalıdır.

## 6. Rapor Yazım Kuralları

Rapor şunları belirtmelidir:

- proje, analiz seviyesi olarak processed-canonical veriyi kullanır,
- büyük upstream ham dosyalar build girdisi değildir,
- kaynak bilgisi dataset/provider/year-or-version seviyesinde raporlanır,
- haritalar öncül MCDA mekânsal öncelik çıktılarıdır,
- sonuçlar resmi afet riski, tehlike, acil durum planlaması veya hukuki karar
  destek ürünü değildir,
- ilçe tablosu ölçülmüş parsel veya resmi idari istatistik değil, raster hücre
  alanı özetleri raporlar.

Kaynak envanterinde dosya adı, yerel metadata, QA dokümanı veya kaynak
veri seti adından desteklenemeyen veri yılları tahmin edilmemelidir. Bu durumda
"proje metadata'sında yıl/sürüm kaydı yok" düzeyinde açık sınırlılık
ifadesi kullanılmalıdır.

## 7. Rapor Üretim Kuralları

Ayrı akademik DOCX üreticisi aşağıdaki kuralları uygular. Bu tablo,
düzenlenebilir kamu Word raporunu yeniden üretme talimatı değildir:

| Öğe | Önerilen karar |
|---|---|
| Rapor dili | Ana metin Türkçe; dataset adları gerektiğinde resmi İngilizce adlarıyla korunur |
| Sınıf etiketleri | Anlatımda ve figure caption metinlerinde Türkçe etiket kullanılır; sayısal class değerleri açık tutulur |
| Figure yerleşimi | Tanımlı PNG harita dosyaları kullanılır |
| Tablo yerleşimi | Elle kopyalanmış tablo metni değil, tanımlı CSV dosyalarından render edilir |
| Kaynak listesi | `docs/data_source_inventory.md` kullanılır ve ham dosya varlığı iddiasından kaçınılır |

## 8. Rapor ve kaynak varlığı kontrolü

Harita/atlas kontrolü 13 QGIS düzeni ve 27 ürünü kapsar. Kamu Word raporu
korelasyon ve senaryo ortaklığı bölümlerini, Şekil 13–14'ü ve Tablo 6'yı
içerir. Raporun Word ve 18 sayfalık PDF sürümüne ait kontroller,
[rapor manifestinde](../outputs/report/public_report_manifest.json) kayıtlı
dosya hash'leri üzerinden izlenir. Başka bir rapor biçimine veya akademik
DOCX üreticisine ait kontrol sonucu bu dosyalara otomatik aktarılmaz.

- Atlas 01–13 sırasıyla 13 sayfa içerir; tekil PNG/PDF dosyaları
  manifestteki referans ürünlerdir.
- Korelasyon ayrı figür olarak raporda yer alır; iki kaynak CSV'siyle izlenir.
- Senaryo ortaklığı tabloları baseline CSV'lerinden ayrı tutulur.
- Harita/atlas dışa aktarma sonuçları [QA kaydı](qa/map_export_qa.md) ile doğrulanır.
- Rapordaki sekiz veri tablosunun sayısal değerleri kaynak tablolarla;
  gömülü şekiller tanımlı PNG varlıklarıyla karşılaştırılır. Kontrolün kapsamı
  ve sonucu, güncel Word/PDF dosyalarının sürüm kaydıyla birlikte değerlendirilir.
- Word düzenlenebilir ana kaynaktır. Ayrı akademik DOCX üreticisi korelasyon
  ve senaryo ortaklığı eklerini üretmez. Pages dosyaları yerel arşivdir.
- Atıf, rapor kapsamı ve veri paylaşım kararları
  [yayın durumu](../PUBLICATION_STATUS.md) ve [veri hakları kaydı](data_rights_and_distribution.md)
  ile uyumlu kalmalıdır. Kamuya açık raporda öğrenci numarası ve danışman adı yer almaz.
