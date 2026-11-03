# On bir kriterin Pearson korelasyonu

**Kaynak sürümü kapsamı:** Aşağıdaki raster, harita PDF, atlas ve Word/PDF
yolları tam yerel çalışma çıktısıdır; bu dosyalar kaynak ve analitik özet
sürümünde dağıtılmaz. `outputs/maps/png/` altındaki harita PNG'leri kamu
kapsamındadır. Yerel üretim/kontrol komutları ilgili kanonik veri ve
çıktıların ayrıca bulunmasını gerektirir. [Kamu dosya kapsamı](../publication_file_scope.md).

**Analiz tarihi: 24 Ekim 2026.** Bu analiz, Çanakkale MCDA modelinde kullanılan
11 kriter skorunun AOI genelinde ne ölçüde birlikte değiştiğini gösterir.
Kaynaklar, ağırlık gerekçeleri ve
[kavramsal çift sayım tartışması](../methodology/updated_mcda_methodology_note.md#10-çift-sayım-ve-model-dengesi)
zaten belgelenmişti; burada bu tartışmaya sayısal karşılaştırma eklenmiştir.
Kriterler, ağırlıklar ve mevcut öncelik sonuçları değiştirilmemiştir.

## Veri ve yöntem

Girdi sürümü [27 dosyalık baseline kaydıyla](../../config/analysis_baseline_v1.json)
sabitlenmiştir. Dosya checksum'ları ve mevcut skor hesapları doğrulandıktan
sonra, 100 m analiz şablonunun `1` olduğu **981.033 hücrenin tamamı** alınır.
Her kriter aynı hücre sırasını ve aynı AOI'yi kullanır. Örnekleme, nüfusla
ağırlıklandırma veya çifte göre farklı hücre elemesi yapılmaz; her hücre eşit
ağırlıktadır. Arazi örtüsünün AOI dışındaki 5.272 hücresi analize girmez.

Kullanılan değerler, kaynak ölçümlerinin doğrudan ham değerleri yerine
[mevcut dönüşümlerden geçmiş kriter skorlarıdır](../methodology/criterion_transformations.md).
Bu skorlara MCDA ağırlıkları uygulanmaz ve final öncelik skoruyla korelasyon
hesaplanmaz. Her çift için float64 hassasiyetinde Pearson katsayısı hesaplanır:

```text
r(x,y) = Σ[(x−ortalama(x)) × (y−ortalama(y))]
         / √[Σ(x−ortalama(x))² × Σ(y−ortalama(y))²]
```

Pozitif katsayı aynı, negatif katsayı ters yöndeki doğrusal değişimi anlatır.
Sıfıra yakın katsayı istatistiksel bağımsızlık veya yerel ilişkinin yokluğu
anlamına gelmez. 11 kriter **55 farklı çift** oluşturur; matrisin köşegeni 1'dir.
Bütün vektörler sonlu ve sıfırdan büyük varyanslıdır. Bağımsız bir hesapta
kaydedilen matris ile `numpy.corrcoef` sonucunun en büyük mutlak farkı
**2,3 × 10⁻¹⁶** altında kalmıştır.

## Çıktılar ve skor dağılımları

- [11 × 11 korelasyon matrisi — CSV](../../outputs/tables/criterion_correlation_v1/criterion_pearson_correlation.csv)
- [Kriter dağılım istatistikleri — CSV](../../outputs/tables/criterion_correlation_v1/criterion_correlation_statistics.csv)
- [Girdi ve çıktı sürüm kaydı — JSON](../../outputs/tables/criterion_correlation_v1/criterion_correlation_manifest.json)
- Korelasyon figürü — PNG (`outputs/figures/criterion_correlation_v1/criterion_pearson_correlation.png`)
  ve PDF (`outputs/figures/criterion_correlation_v1/criterion_pearson_correlation.pdf`)

Aşağıdaki değerler aynı 981.033 hücreden hesaplanmıştır. Standart sapma,
tüm AOI vektörüne aittir (`ddof=0`); tabloda altı ondalığa yuvarlanmıştır.
Sıfır sütunu **mevcut skor rasterındaki** sıfırları sayar.

| Kriter | Ortalama | Standart sapma | Sıfır hücre | Sıfır % |
|---|---:|---:|---:|---:|
| PGA | 0.172916 | 0.142017 | 11.473 | 1.17 |
| Fay yakınlığı | 0.332655 | 0.369354 | 455.340 | 46.41 |
| VS30 zemin koşulu | 0.566380 | 0.170536 | 1.580 | 0.16 |
| Nüfus maruziyeti | 0.017320 | 0.093017 | 940.459 | 95.86 |
| Bina yoğunluğu | 0.004311 | 0.029531 | 899.181 | 91.66 |
| Taşkın | 0.004508 | 0.034016 | 948.171 | 96.65 |
| Hidrografya yakınlığı | 0.206958 | 0.313063 | 596.807 | 60.83 |
| Eğim | 0.243516 | 0.163034 | 1.635 | 0.17 |
| Arazi örtüsü | 0.488119 | 0.119734 | 0 | 0.00 |
| Ağaç örtüsü | 0.314691 | 0.312571 | 252.756 | 25.76 |
| Yol erişim zorluğu | 0.198808 | 0.220579 | 155.856 | 15.89 |

Toplam sıfır sayısı, kaynak NoData sayısı değildir.
[Kaynak→skor kontrolünde](../methodology/criterion_transformations.md#sayısal-sonuç-ve-kaynak-nodata-davranışı)
PGA'da 9.412, eğimde 538, taşkında 948.171 ve ağaç örtüsünde 7 hücrenin kaynak
NoData'dan sıfır skora dönüştüğü görülmüştür. Bu hücreler mevcut model
davranışını korumak için analizde tutulmuştur. Özellikle taşkındaki %96,65
sıfır, AOI'nin bu oranında ölçülmüş taşkın tehlikesi yokluğu olarak okunamaz.
Bu sayılarla toplam skor sıfırlarını birbirine eşitlemek diğer kriterlerde de
yanlış olur.

## Sonuçların yorumu

**Çevresel blokta belirgin eşdeğişim var.** En yüksek mutlak katsayı arazi
örtüsü–ağaç örtüsünde **r = 0.8152**. Eğim–arazi örtüsü **0.6058**, eğim–ağaç
örtüsü **0.5795**. Arazi örtüsü reçetesinde ağaç sınıfının 0.60, tarımın 0.30
ve yapılı alanın 0.20 alması, TCD/100 ile artan ağaç skoruyla aynı yönlü
değişimi anlaşılır kılar. Bu, mekânsal mekanizmanın tek başına kanıtı değildir;
puanlama tercihleri de ilişkinin parçasıdır.
[Çevresel/topoğrafik blok](../methodology/updated_mcda_methodology_note.md#104-çevresel-ve-topoğrafik-kriterler)
toplam 0.18, arazi ve ağaç çifti 0.10 ağırlıktadır. Bulgular bu bloğun ortak
bilgi taşıdığını görünür kılar; ağırlıklar otomatik değiştirilmez.

**Maruziyet göstergeleri birlikte değişiyor.** Nüfus–bina yoğunluğu
**r = 0.6046**. İnsan maruziyeti ve bina alanı birbirinin aynısı değildir;
[0.24 ağırlıklı maruziyet bloğunda](../methodology/updated_mcda_methodology_note.md#102-maruziyet-kriterleri)
birlikte değişmeleri sayısallaştırılmıştır. İki skorun sıfır oranları %95,86 ve
%91,66 olduğundan, tüm-AOI katsayısı yalnız yerleşim hücreleri arasındaki
ilişkinin aynı olduğu anlamına gelmez.

**En belirgin negatif ilişki zemin–eğim çiftinde.** Katsayı **−0.6561**;
zemin–arazi örtüsü **−0.4811**, zemin–ağaç örtüsü **−0.4702**. Zemin skoru
düşük VS30'da yükseldiğinden işaret yorumunda bu ters kodlama korunmalıdır.
Bu değerler kriterlerin fiziksel olarak birbirini iptal ettiğini göstermez.
USGS mosaic'in yerel bileşeni doğrulanmadan ilişki bütünüyle tek bir veri
üretim yöntemine de bağlanamaz.

**Aynı kavramsal grupta olmak aynı rasterı üretmiyor.** PGA–fay yakınlığı
**0.3385**, PGA–zemin **−0.0516**, fay yakınlığı–zemin **−0.1919**.
[Su ilişkili grupta](../methodology/updated_mcda_methodology_note.md#103-su-i̇lişkili-kriterler)
taşkın–hidrografya katsayısı **0.2094**. Taşkının sınırlı veri desteği ve
NoData→0 davranışı nedeniyle bu son değer, sahadaki taşkın–akarsu ilişkisinin
zayıf olduğuna kanıt olarak kullanılamaz.

Bu analiz skorların **doğrusal eşdeğişimini** tarif eder. Logaritmik dönüşüm,
kırpma, kategorik puanlama ve yeniden örnekleme sonucu etkiler; kaynak
değişkenleriyle aynı katsayıların çıkması beklenmez. Komşu raster hücreleri
bağımsız gözlemler sayılmadığından p-değeri veya bağımsız örneklem güven
aralığı raporlanmaz. Korelasyon, gerçekleşmiş afetlerle doğrulama, nedensellik
veya ağırlıkların optimumluğu kanıtı değildir. Mevcut çift sayım tartışmasına
ölçülebilir destek sağlar; tek bir eşikle kriter eleme kararı üretmez.
