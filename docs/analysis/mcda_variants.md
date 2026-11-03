# MCDA varyantları: taşkın ağırlığı, vejetasyon çift sayımı ve eşik seçimi

**Kaynak sürümü kapsamı:** Altı CSV ve üretim manifesti kamu kapsamındadır;
raster üretilmez. Yerel kontrol/üretim komutları kanonik verinin ve yerel
HydroRIVERS/taşkın derinliği dosyalarının ayrıca bulunmasını gerektirir.
[Kamu dosya kapsamı](../publication_file_scope.md).

**Analiz tarihi: 3 Kasım 2026.** Bu analiz, kanonik modelin üç bilinen
zayıflığını tek tek sınar: taşkın skorunun AOI'nin çoğunda sıfır olması, arazi
örtüsü ile ağaç örtüsünün aynı bilgiyi iki kez taşıması ve "çok yüksek"
sınıfın çok dar olması. Kriter skorları, baseline ağırlıkları, kanonik sınıflar
ve mevcut tablolar değiştirilmemiştir. Varyantlar doğrulanmış alternatif
modeller değildir; her biri tek bir modelleme seçiminin etkisini gösterir.

## Yöntem

Girdi ve ölçüler [ağırlık pertürbasyonu](weight_perturbation.md) ile aynıdır:
981.033 AOI hücresi, ortak motor ve baseline ham skorunun bit düzeyinde
yeniden üretimi.

- **Sıralama tabanlı (ana):** her varyantta en yüksek ham skorlu 54.592 hücre
  yüksek+, en yüksek 699 hücre çok yüksek sayılır. Alan tanım gereği sabittir;
  karşılaştırma konumu ölçer (Jaccard, baseline yüksek+ korunumu, çok yüksek
  Jaccard, ilçe Spearman ρ, ilk 5 ilçe).
- **Baseline sabit ölçeği (ek):** `clip((raw−0.029)/0.473,0,1)` ve
  0,2/0,4/0,6/0,8 eşikleri. Alan değişimi düzey kaymasını da içerir.

Ayarlar [`config/mcda_variants_v1.json`](../../config/mcda_variants_v1.json),
ağırlıklar [`variant_weights.csv`](../../outputs/analysis/mcda_variants_v1/variant_weights.csv)
içindedir. Çıkarılan ağırlık kalan kriterlere oranlarıyla dağıtılır.

## Taşkın

**Kaynak NoData'sının anlamı doğrulanamadı.** Taşkın skoru 981.033 hücrenin
yalnız 32.862'sinde (%3,35) sıfırdan büyüktür; kalan hücrelerde kaynak NoData'sı
0'a dönüşür ([kriter dönüşümleri](../methodology/criterion_transformations.md#sayısal-sonuç-ve-kaynak-nodata-davranışı)).
NoData'nın "taşkın yok" mu "modellenmemiş alan" mı olduğu birincil kaynaklardan
belirlenemedi:

- JRC/CEMS ürününün [README](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard/README.txt)
  ve [CHANGELOG](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard/CHANGELOG.txt)
  dosyaları NoData'yı tanımlamaz; README yalnız kara alanlarının kapsandığını
  belirtir.
- v2 yöntem makalesi ([Dottori vd. 2022](https://doi.org/10.5194/essd-14-1549-2022))
  yukarı havza alanı 500 km²'den büyük nehirleri modeller ve modellenen ağı
  ayrı bir harita olarak verir. Güncel v3 dizininde böyle bir ağ veya kapsama
  maskesi yoktur; README eşik belirtmez. Makaleye göre haritalar yerel taşkın
  koruma yapılarını hesaba katmaz.
- Yerel dosyanın sürümü bilinmiyor ([veri hakları §5](../data_rights_and_distribution.md#5-jrccems--avrupa-ve-akdeniz-rp100-taşkın-derinliği)).
  Yerel derinlik rasterında geçerli en küçük değer 0,1 m'dir, 0 m hücre yoktur:
  değer yalnız su basan hücrelerde bulunur; kuru ama modellenmiş hücre ile
  modellenmemiş hücre ikisi de NoData'dır.
- Taşkın hücreleri, HydroRIVERS'ta yukarı havzası ≥ 500 km² olan kollardan
  medyan 1,4 km, en çok 43,9 km uzaktadır (≥ 150 km² için 0,5 / 25,8 km).
  500 km² eşiği yerel dosyaya uymaz; havza alanıyla kapsama yeniden kurulamaz.

Kanıtlar [`flood_coverage_evidence.csv`](../../outputs/analysis/mcda_variants_v1/flood_coverage_evidence.csv)
içindedir.

**Sınıf 5'in taşkına bağımlılığı.** Baseline yüksek+ hücrelerinin %9,0'ında,
**çok yüksek sınıfın 699 hücresinin 396'sında (%56,7)** taşkın skoru sıfırdan
büyüktür. En dar sınıf büyük ölçüde taşkın hücrelerinden oluşur.

**Neden kapsama maskesi yok.** "NoData = modellenmemiş" ucu, taşkın ağırlığının
yalnız kapsanan hücrelerde çalıştığı ve diğer hücrelerde kalan ağırlıkların
yeniden ölçeklendiği bir maskeyle kurulabilirdi. Elde kapsama katmanı olmadığı
için böyle bir maske ancak sonuçtan, yani taşkın > 0 hücrelerinden türetilebilir.
Bu durumda modellenmiş ama kuru hücreler kapsam dışında kalır ve 1/0,9
ölçeklemesiyle yükselir; sığ taşkınlı hücreler ise kapsam içinde kalıp düşük
taşkın skoruyla cezalanır. Bu maske bir kapsama ölçütü değildir; bu yüzden
tabloya alınmamıştır. Tabloda yalnız taşkın ağırlığının bütün AOI'de sıfırlandığı
senaryo vardır.

| Ölçü | Yüksek+ (km²) | Korunum | Jaccard | Çok yüksek Jaccard | İlçe ρ | Çok yüksek (km²) | İlk 5 |
|---|---:|---:|---:|---:|---:|---:|---|
| Sıralama tabanlı | 545,93 | 0,978 | 0,958 | **0,515** | 1,000 | 6,99 | baseline ile aynı sıra |
| Sabit ölçek | 1.388,98 | 0,996 | 0,391 | 0,095 | 0,956 | 64,34 | Yenice, Çan, Biga, Gelibolu, Ayvacık |

Taşkın ağırlığı 0'a indirilip oranlarla dağıtıldığında (diğer ağırlıklar
1/0,9 ile büyür) baseline yüksek+ hücrelerinin %97,8'i yerinde kalır
(Jaccard 0,958), ama çok yüksek sınıfın yaklaşık yarısı değişir. Sabit ölçekteki alan artışı düzey kaymasıdır: taşkın, AOI'nin
çoğunda sıfır olan bir kriterdir ve ağırlığı ortalaması yüksek kriterlere geçer.

## Vejetasyon çift sayımı

Arazi örtüsü (0,06) ve ağaç örtüsü (0,04) skorlarının Pearson r'si 0,8152'dir
([korelasyon analizi](criterion_correlation.md)). Dört varyant iki etkiyi,
birleştirmeyi ve blok ağırlığının düşürülmesini, birbirinden ayırır:

- **Ortalama, blok 0,0625 (ana):** iki skorun ortalaması tek vejetasyon
  kriteri olur. Blok bir kez, en büyük üyesinin ağırlığıyla sayılır: kalan
  0,04 bütün kriterlere oranla dağıtılır, blok `0,06 / (1 − 0,04) = 0,06 / 0,96
  = 0,0625` olur. Birleştirme ve ağırlık düşürme birliktedir.
- **Ortalama, blok 0,10 (ek):** yalnız birleştirme; diğer ağırlıklar aynıdır.
  Bu, iki skora 0,05/0,05 vermekle eşdeğerdir.
- **İki kriter ayrı, blok 0,0625 (ek):** yalnız ağırlık düşürme. İki skor ayrı
  kalır; blok ana varyanttaki gibi 0,0625'e iner ve baseline oranıyla
  (0,6 : 0,4) bölünür: arazi örtüsü 0,0375, ağaç örtüsü 0,025. Diğer
  ağırlıklar ana varyanttaki gibi 1/0,96 ile büyür.
- **Ağaç örtüsü çıkarıldı (ek):** ağırlık düşürme ve bilgi kaybı; arazi örtüsü
  `0,06 / 0,96 = 0,0625` olur, ağaç örtüsü bilgisi modelden çıkar.

| Varyant | Ölçü | Yüksek+ (km²) | Korunum | Jaccard | Çok yüksek Jaccard | İlçe ρ | Çok yüksek (km²) |
|---|---|---:|---:|---:|---:|---:|---:|
| **Ortalama, blok 0,0625** | Sıralama tabanlı | 545,92 | 0,919 | **0,850** | 0,726 | 0,989 | 6,99 |
| | Sabit ölçek | 397,19 | 0,716 | 0,708 | 0,685 | 0,989 | 7,72 |
| Ortalama, blok 0,10 | Sıralama tabanlı | 545,92 | 0,966 | 0,935 | 0,859 | 1,000 | 6,99 |
| | Sabit ölçek | 545,38 | 0,966 | 0,935 | 0,847 | 1,000 | 6,31 |
| İki kriter ayrı, blok 0,0625 | Sıralama tabanlı | 545,92 | 0,897 | 0,814 | 0,703 | 0,989 | 6,99 |
| | Sabit ölçek | 400,46 | 0,713 | 0,699 | 0,648 | 0,989 | 8,35 |
| Ağaç örtüsü çıkarıldı | Sıralama tabanlı | 545,92 | 0,807 | 0,676 | 0,647 | 0,984 | 6,99 |
| | Sabit ölçek | 426,69 | 0,689 | 0,631 | 0,437 | 0,989 | 12,76 |

İlk beş ilçe ve sırası bütün vejetasyon varyantlarında baseline ile aynıdır.
Yüksek+ alanı (km², sıralama tabanlı):

| İlçe | Baseline | Ortalama, 0,0625 | Ortalama, 0,10 | Ayrı, 0,0625 | Ağaç çıkarıldı |
|---|---:|---:|---:|---:|---:|
| Yenice | 200,68 | 190,42 | 203,10 | 188,95 | 181,63 |
| Gelibolu | 105,06 | 117,31 | 101,76 | 119,28 | 126,73 |
| Çan | 88,68 | 86,94 | 89,63 | 86,49 | 86,14 |
| Biga | 85,06 | 83,39 | 86,30 | 82,59 | 78,76 |
| Ayvacık | 38,69 | 40,63 | 37,14 | 41,72 | 46,56 |

**İki skorun ölçeği farklıdır.** Arazi örtüsü sınıf tablosundan gelir ve
0,05–0,60 aralığındadır (ortalama 0,488, standart sapma 0,120; sıfır yok).
Ağaç örtüsü 0–1 ölçeklidir (en çok 0,964; ortalama 0,315, standart sapma 0,313;
hücrelerin %25,8'i sıfır). Bu yüzden ortalama eşit ağırlıklı görünse de
mekânsal değişkenliğinin yaklaşık **%74**'ü ağaç örtüsünden gelir: ortalamanın
ağaç örtüsüyle korelasyonu 0,986, arazi örtüsüyle 0,900'dür. Ortalamada arazi
örtüsü düzeyi yükseltir, ağaç örtüsü konumu belirler. Baseline'da da bloğun
değişkenliğine en büyük katkı ağaç örtüsündendir (0,04 × 0,313 > 0,06 × 0,120).

Sıralama tabanlı Jaccard'a göre ayrıştırma:

| Varyant | Birleştirme | Blok ağırlığı | Ağaç bilgisi | Jaccard |
|---|---|---:|---|---:|
| Ortalama, blok 0,10 | var | 0,10 | korunur | 0,935 |
| İki kriter ayrı, blok 0,0625 | yok | 0,0625 | korunur | 0,814 |
| Ortalama, blok 0,0625 (ana) | var | 0,0625 | korunur | 0,850 |
| Ağaç örtüsü çıkarıldı | — | 0,0625 | atılır | 0,676 |

Konum değişiminin büyük kısmı ağırlık düşürmeden gelir: yalnız ağırlık
düşürme Jaccard'ı 0,814'e, yalnız birleştirme 0,935'e indirir. İkisi birlikte
(0,850) yalnız ağırlık düşürmeden daha az değişiklik verir. Ortalamada iki
skor bloğu eşit paylaşır (0,03125 / 0,03125); ayrı varyantta ağaç örtüsü
0,025'te kalır (baseline 0,04). Ağaç örtüsü bloğun konumunu belirlediği için
ortalamadaki daha büyük ağaç payı sonucu kısmen baseline'a geri yaklaştırır. Ağaç örtüsünü tamamen
çıkarmak, aynı blok ağırlığında iki bilginin birini atar ve en büyük farkı
verir (0,676); bu fark ağırlık düşürmenin üstüne bilgi kaybından gelir.

## Eşik seçiminin etkisi

Kanonik sınıflar sabit ölçekte eşit aralıklıdır ve değişmemiştir. Aşağıdaki
iki yöntem **eşik seçiminin etkisini göstermek için** yalnız baseline skoruna
uygulanmıştır; eşit aralığa alternatif öneri değildir. Skorlar aynıdır;
değişen yalnız "yüksek" ve "çok yüksek" sınırlarının nerede çizildiğidir.

- **Kantil:** 2.–5. sınıf sınırı, sıralı skorların `⌈q·n/5⌉` konumundaki
  gözlenmiş değerdir (q = 1…4); sınırda eşitler üst sınıfa girer.
- **Doğal kırılma (Fisher-Jenks):** skor `⌊1000·z⌋` ile 0,001 genişlikli
  kutulara ayrılır; dolu kutular hücre sayılarıyla ağırlıklandırılır ve beş
  sınıflı bölüntü dinamik programlamayla kesin olarak bulunur. Örnekleme
  yoktur; sınır, kutunun alt kenarıdır. Varyans uyum iyiliği (GVF) 0,941.

| Yöntem | Sınırlar (2/3/4/5) | Sınıf payları % (1/2/3/4/5) | Yüksek+ (km²) | Çok yüksek (km²) | Eşit aralıkla aynı sınıf | Yüksek+ Jaccard | İlk 5 |
|---|---|---|---:|---:|---:|---:|---|
| Eşit aralık (kanonik) | 0,2 / 0,4 / 0,6 / 0,8 | 11,65 / 49,25 / 33,54 / 5,49 / 0,07 | 545,92 | 6,99 | %100 | 1 | Yenice, Gelibolu, Çan, Biga, Ayvacık |
| Kantil | 0,233 / 0,305 / 0,395 / 0,502 | 20 / 20 / 20 / 20 / 20 | 3.924,13 | 1.962,06 | %31,72 | 0,139 | Yenice, Biga, Çan, Ayvacık, Gelibolu |
| Doğal kırılma | 0,238 / 0,339 / 0,448 / 0,564 | 21,31 / 26,92 / 21,75 / 20,45 / 9,57 | 2.945,68 | 939,03 | %47,71 | 0,185 | Yenice, Biga, Çan, Ayvacık, Gelibolu |

Skor dağılımı sağa çarpık olduğu için iki yöntem de yüksek+ sınırını 0,6'dan
0,40–0,45'e çeker. Yüksek+ alanı 5–7 katına çıkar; kantilde il alanının %40'ı
yüksek+ olur. Çok yüksek sınıfın darlığı (%0,07) bir eşik sonucudur: aynı skorla
çok yüksek alan 6,99 km² ile 1.962 km² arasında değişebilir. İki yöntemde de
Gelibolu beşinci sıraya iner; Gelibolu'nun yüksek+ alanı en yüksek skorlarda
yoğunlaşır, eşik düşünce geniş ilçeler öne geçer. İl ve ilçe sınıf dağılımları
[`classification_distribution.csv`](../../outputs/analysis/mcda_variants_v1/classification_distribution.csv)
içindedir.

## Çıktılar ve yorumun sınırı

`outputs/analysis/mcda_variants_v1/` altında:
[`variant_weights.csv`](../../outputs/analysis/mcda_variants_v1/variant_weights.csv),
[`variant_summary.csv`](../../outputs/analysis/mcda_variants_v1/variant_summary.csv),
[`variant_district_areas.csv`](../../outputs/analysis/mcda_variants_v1/variant_district_areas.csv),
[`classification_summary.csv`](../../outputs/analysis/mcda_variants_v1/classification_summary.csv),
[`classification_distribution.csv`](../../outputs/analysis/mcda_variants_v1/classification_distribution.csv),
[`flood_coverage_evidence.csv`](../../outputs/analysis/mcda_variants_v1/flood_coverage_evidence.csv)
ve [üretim manifesti](../../outputs/analysis/mcda_variants_v1/mcda_variants_manifest.json).

Kontrol ve üretim: [QA sözleşmesi](../qa/canonical_integrity_checks.md#mcda-varyantları-kontrolü).

Varyantlar baseline'ı değiştirmez ve birbirine göre "daha doğru" model
sıralaması vermez. Taşkın NoData'sının anlamı çözülmeden taşkın bloğunun
doğru ağırlığı bilinemez; vejetasyon varyantları ağırlık seçimini, eşik
yöntemleri sınıf sınırını değiştirir. Dış doğrulama bulunmadığı için hangi
seçimin gerçeğe daha yakın olduğu bu analizle belirlenemez
([sınırlılıklar](../methodology/scientific_limits.md)).
