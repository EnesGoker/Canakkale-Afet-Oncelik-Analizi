# Ağırlık pertürbasyonu: yüksek öncelik alanlarının konum kararlılığı

**Kaynak sürümü kapsamı:** Sayım rasterı (`outputs/analysis/weight_perturbation_v1/high_plus_probability_count_32635.tif`)
tam yerel çalışma çıktısıdır ve kaynak sürümünde dağıtılmaz. Sekiz CSV ve
üretim manifesti kamu kapsamındadır. Yerel kontrol/üretim komutları kanonik
verinin ayrıca bulunmasını gerektirir. [Kamu dosya kapsamı](../publication_file_scope.md).

**Analiz tarihi: 3 Kasım 2026.** Baseline ağırlıkları uzman yargısıyla
belirlenmiştir ([ağırlık gerekçeleri](../methodology/updated_mcda_methodology_note.md#6-ağırlıklandırma-stratejisi)).
Bu analiz, ağırlıklar baseline çevresinde değiştiğinde yüksek + çok yüksek
öncelik alanlarının **nerede** kaldığını inceler. Kriter skorları, baseline
ağırlıkları, kanonik sınıflar ve mevcut üç senaryonun tabloları değiştirilmemiştir.

## Ana bulgu: dayanıklı çekirdek

κ = 100 Dirichlet örneklerinin en az %90'ında yüksek+ kalan **dayanıklı çekirdek
215,75 km²**'dir; bu, baseline yüksek + çok yüksek alanının (545,92 km²)
**%39,52**'sidir. Kalan yaklaşık **%60**'ı ağırlığa duyarlıdır: bu hücreler
örneklerin bir kısmında yüksek+ kümesinden çıkar
([P(yüksek+) sınıfları](#dirichlet-sonuçları)). Yüksek öncelik alanlarının
çekirdeği ağırlık belirsizliğine dayanıklı, çevresi ise ağırlık seçimine
bağlıdır.

## Yöntem

**Girdi.** [27 dosyalık sabit baseline kaydı](../../config/analysis_baseline_v1.json)
ve sayısal QA doğrulandıktan sonra şablon AOI'sinin **981.033 hücresi**
kullanılır (hücre 0,01 km²). Ağırlıklı ham skor, kanonik ifadenin sırasıyla
Float32 olarak hesaplanır; baseline ağırlıklarıyla kayıtlı ham skor rasterı
**bit düzeyinde** yeniden üretilir ve bu her kontrolde sınanır.

**İki ölçü.** Ağırlık değişince bütün ham skorlar birlikte yükselip
alçalabilir. Taşkın, bina ve nüfus skorları AOI'nin %92–97'sinde sıfırdır;
ağırlık bunlardan ortalaması yüksek kriterlere kaydığında skorların genel
düzeyi yükselir. Bu düzey kayması konum bilgisi taşımaz. Bu yüzden:

- **Ana ölçü — sıralama tabanlı.** Her örnekte en yüksek ham skorlu
  **54.592 hücre** (baseline'daki yüksek + çok yüksek sayısı, AOI'nin
  %5,565'i) yüksek+ sayılır; çok yüksek, en yüksek 699 hücredir. Sınır,
  k'inci en büyük değerdir ve eşit değerler dahil edilir (eşitlik nedeniyle
  bir örnekte en çok 2 hücre fazla seçilmiştir). **Bu ölçüde yüksek+ alanı
  tanım gereği sabittir (545,92 km²).** P(yüksek+) bu yüzden alanın
  büyüklüğünü değil, hücrenin yüksek+ kümesinde kalma sıklığını, yani
  **konum kararlılığını** ölçer.
- **Ek ölçü — baseline sabit ölçeği.** `clip((raw−0.029)/0.473,0,1) ≥ 0.6`.
  Alanın ne kadar değiştiğini gösterir; düzey kayması ile konum değişimini
  birlikte içerdiği için yalnız tablolarda verilir.

Örneğin kendi min/max'ıyla ölçekleme kullanılmaz: sonuç tek bir uç hücreye
bağlıdır ve baseline ağırlığında bile 1.393 hücre farklı sınıf verir
([ölçek notu](../methodology/normalization_and_baseline.md#ağırlık-pertürbasyonunda-ölçek)).
Baseline ağırlıklarıyla iki ölçü de kanonik sınıfları birebir verir.

**OAT.** Her kriterin ağırlığı tek tek ±%10 ve ±%20 değiştirilir:
`w_i' = w_i(1+δ)`; diğer ağırlıklar `(1 − w_i')/(1 − w_i)` ile orantılı
ölçeklenir ve toplam 1 kalır (11 × 4 = 44 adım).

**Dirichlet örneklemesi.** Ağırlık vektörü `Dirichlet(κ · w_baseline)`
dağılımından çekilir. Ortalama baseline ağırlıklarıdır; κ büyüdükçe dağılım
daralır. Ağırlık i'nin değişim katsayısı `√((1−w)/(w(κ+1)))`dir:

| κ | Rol | Ağırlıkların değişim katsayısı |
|---:|---|---|
| 50 | Özet satırı | 0,32 (PGA) – 0,69 (ağaç) |
| **100** | **Ana** | **0,23 – 0,49** |
| 200 | Özet satırı | 0,16 – 0,35 |

κ = 100'de büyük ağırlıkların tipik sapması ±%23–25'tir; deprem ağırlıklı
senaryonun baseline'dan sapmalarıyla (−%33 … +%38) aynı mertebededir.
Her κ için **2.000 örnek** çekilir; tohum `20261103`, akış
`numpy.random.default_rng([tohum, κ])`. NumPy dağılım akışlarının sürümler
arasında aynı kalacağını garanti etmediği için örneklenen ağırlıklar
[`weight_samples.csv`](../../outputs/analysis/weight_perturbation_v1/weight_samples.csv)
olarak saklanır. Bütün sonuçlar bu tablodan yeniden hesaplanabilir.
Ayarlar: [`config/weight_perturbation_v1.json`](../../config/weight_perturbation_v1.json).

**Yakınsama.** κ = 100'de 4.000 örnek çekilir; ilk 2.000'i ana örneklerdir.
Ölçüt: 0 < P < 1 hücrelerinde `%99 |P_2000 − P_4000| ≤ 0,02` ve P ≥ 0,5
alanında göreli değişim ≤ %1. Sonuç **0,0128** ve **%0,06** (498,47 →
498,15 km²); ölçüt karşılanır. N = 1.000'de %99 fark 0,0242'dir.
P_2000 ve P_4000 bağımsız değildir: ilk 2.000 örnek 4.000'in önekidir
(iç içe örnekler), bu yüzden fark tek başına örnekleme hatasının tam ölçüsü
değildir. Bir hücrenin P tahmininin Monte Carlo standart hatası
`√(P(1−P)/N)`dir; N = 2.000'de en çok **0,0112** (P = 0,5), yani P ≈ 0,5
çevresinde %95 aralığı yaklaşık **±0,022**'dir. Sınıf sınırlarına
(0,25 / 0,50 / 0,75 / 0,90) bu kadar yakın hücreler başka bir tohumla komşu
sınıfa geçebilir; sınıf alanları bu düzeyde belirsizdir.

## OAT sonuçları

±%20 adımları; sıralama tabanlı ölçünün dört adımdaki en düşük Jaccard
değerine göre, en duyarlıdan en aza:

| Kriter | Jaccard (en düşük) | Baseline yüksek+ korunumu (en düşük) | Sabit ölçekte alan farkı −%20 / +%20 (km²) |
|---|---:|---:|---|
| Hidrografya yakınlığı | 0,867 | 0,929 | −9,80 / +16,91 |
| Fay yakınlığı | 0,886 | 0,940 | −202,65 / +309,86 |
| Yol erişim zorluğu | 0,896 | 0,945 | −6,79 / +6,21 |
| Deprem PGA | 0,900 | 0,948 | +36,62 / −32,95 |
| Eğim | 0,917 | 0,957 | −8,37 / +10,51 |
| Zemin koşulu | 0,928 | 0,963 | −65,12 / +74,65 |
| Ağaç örtüsü | 0,929 | 0,963 | −33,65 / +37,51 |
| Nüfus maruziyeti | 0,930 | 0,964 | +187,39 / −146,63 |
| Arazi örtüsü | 0,970 | 0,985 | −53,44 / +59,12 |
| Yapı yoğunluğu | 0,989 | 0,995 | +132,77 / −116,44 |
| Taşkın | 0,990 | 0,995 | +133,55 / −116,73 |

- Yüksek+ hücrelerin **konumu** en çok hidrografya, fay, yol ve PGA
  ağırlığına bağlıdır; ±%20 değişimde bu hücrelerin %5–7'si yer değiştirir.
- **Alan** en çok fay ve nüfus ağırlığına bağlıdır (sabit ölçek). Taşkın,
  yapı ve nüfusun büyük alan etkisi düzey kaymasıdır: taşkın ağırlığı %20
  azalınca sabit ölçekte alan 133,55 km² büyür, sıralama tabanlı ölçüde ise
  konum neredeyse aynı kalır (Jaccard 0,990).
- Taşkın (0,990) ve yapı yoğunluğunun (0,989) yüksek Jaccard değeri bu
  kriterlerin **önemsiz** olduğunu göstermez; nedeni **seyrekliktir**. Taşkın
  skoru AOI hücrelerinin %96,65'inde, yapı yoğunluğu %91,66'sında sıfırdır
  ([kriter istatistikleri](../../outputs/tables/criterion_correlation_v1/criterion_correlation_statistics.csv)).
  Ağırlık değişimi yalnız skoru sıfırdan büyük az sayıdaki hücreyi etkiler.
  Taşkın skorundaki sıfırların bir kısmı kaynak NoData'sından gelir; bunun
  anlamı doğrulanamamıştır; taşkın ağırlığının sıfırlandığı senaryo ve
  çok yüksek sınıfın taşkına bağımlılığı [MCDA varyantlarında](mcda_variants.md#taşkın)
  verilir ([sınırlılıklar](../methodology/scientific_limits.md)).
- Baseline'ın ilk beş ilçesi (Yenice, Gelibolu, Çan, Biga, Ayvacık) sıralama
  tabanlı ölçüde 44 adımın 42'sinde aynı sırada kalır; değişen ikisi PGA −%20
  ve yol −%20'dir. Beş ilçenin kümesi 44 adımın hepsinde aynıdır. İlçe
  alanlarının Spearman ρ'su her adımda ≥ 0,968'dir.

## Dirichlet sonuçları

**Konum kararlılığı** (sıralama tabanlı; medyan, parantezde %5–%95):

| κ | Baseline yüksek+ korunumu | Jaccard | İlçe ρ | P ≥ 0,5 alanı (km²) | P ≥ 0,9 alanı (km²) | P > 0 alanı (km²) |
|---:|---|---|---|---:|---:|---:|
| 50 | 0,720 (0,574–0,840) | 0,562 (0,403–0,725) | 0,961 (0,893–0,989) | 455,57 | 126,19 | 2.689,15 |
| **100** | **0,796 (0,672–0,888)** | **0,661 (0,506–0,799)** | **0,975 (0,928–0,993)** | **498,47** | **215,75** | **2.022,72** |
| 200 | 0,854 (0,756–0,919) | 0,744 (0,607–0,851) | 0,982 (0,937–0,993) | 521,86 | 296,12 | 1.501,49 |

**Alan duyarlılığı** (sabit ölçek; yüksek+ alanı km²):

| κ | %5 | Medyan | %95 | En az – en çok | Beklenen alan |
|---:|---:|---:|---:|---|---:|
| 50 | 88,30 | 616,17 | 2.399,57 | 11,73 – 4.029,61 | 840,99 |
| 100 | 145,22 | 590,85 | 1.804,29 | 19,08 – 2.939,81 | 732,09 |
| 200 | 204,40 | 565,61 | 1.399,53 | 47,76 – 2.171,98 | 645,42 |

Sabit ölçekte alan 10 kattan fazla oynar; bu oynamanın büyük kısmı düzey
kaymasıdır. Konum ölçüsünde ise baseline yüksek+ hücrelerinin medyan olarak
%80'i (κ = 100) korunur.

**P(yüksek+) sınıfları** (κ = 100, 2.000 örnek; il geneli):

| P(yüksek+) | Alan (km²) | AOI payı | Baseline yüksek+ içindeki payı |
|---|---:|---:|---:|
| P = 0 | 7.787,61 | %79,38 | %0 |
| 0 < P < 0,25 | 1.313,60 | %13,39 | %0 |
| 0,25 ≤ P < 0,50 | 210,65 | %2,15 | %8,69 |
| 0,50 ≤ P < 0,75 | 167,53 | %1,71 | %30,69 |
| 0,75 ≤ P < 0,90 | 115,19 | %1,17 | %21,10 |
| P ≥ 0,90 | 215,75 | %2,20 | %39,52 |

P ≥ 0,90 sınıfı yukarıdaki dayanıklı çekirdektir (baseline yüksek+'nın
%39,52'si); baseline yüksek+ alanının %91,3'ü P ≥ 0,5'tir ve hepsi
P ≥ 0,25'tir. Baseline dışındaki hiçbir hücrenin P ≥ 0,5'e ulaşmaması bir
bulgu değil, **baseline merkezli örneklemenin beklenen özelliğidir**: örnek
ağırlıklarının ortalaması baseline ağırlıklarıdır ve sıralama tabanlı ölçü
her örnekte baseline ile aynı sayıda hücre seçer. Bu yüzden yeni bir alanın
örneklerin çoğunda seçilmesi beklenmez. Bu sınıflar
[14. haritanın](../../outputs/maps/png/14_yuksek_oncelik_olasiligi.png)
lejantıdır; raster sayımı `P = sayı / 2.000` olarak verir. Haritadaki koyu gri
çizgi baseline yüksek+ sınırıdır.

**İlçe sırası** (yüksek+ alanına göre azalan; κ = 100, sıralama tabanlı).
Sıra, mevcut [ilk beş ilçe tablosu](../../outputs/tables/mcda_sensitivity_top_districts.csv)
gibi **mutlak yüksek+ alanına (km²)** göredir; o tablo da alana göre azalan,
eşitlikte ilçe adına göre sıralanır. Mutlak alan büyük ilçeyi öne çıkarır:
Biga (1.309 km²) baseline'da Çan'dan (904 km²) yalnız 3,6 km² az yüksek+
alana sahiptir, ama ilçe alanına oranla Çan %9,81, Biga %6,50'dir.
Bu veride baseline'ın ilk altı ilçesinin sırası iki ölçüde aynıdır.

| İlçe | Baseline sırası | Medyan sıra | İlk 1 | İlk 3 | İlk 5 | Yüksek+ alanı medyan (%5–%95), km² |
|---|---:|---:|---:|---:|---:|---|
| Yenice | 1 | 1 | %94,5 | %100 | %100 | 196,57 (160,90–232,79) |
| Gelibolu | 2 | 2 | %5,6 | %69,9 | %97,6 | 100,34 (46,21–168,19) |
| Çan | 3 | 3 | %0 | %76,5 | %100 | 88,62 (70,11–105,56) |
| Biga | 4 | 3 | %0 | %53,6 | %100 | 83,19 (67,56–100,78) |
| Ayvacık | 5 | 5 | %0 | %0 | %96,7 | 41,45 (28,98–54,49) |
| Bayramiç | 6 | 6 | %0 | %0 | %5,7 | 26,57 (15,57–38,99) |

Baseline'ın ilk beş ilçesi κ = 100 örneklerinin **%94,25**'inde aynı küme
olarak kalır (aynı sırayla %36,65). κ = 50'de %87,05, κ = 200'de %99,00.
Yenice'nin birinciliği kararlıdır; Gelibolu, Çan ve Biga arasındaki sıra
ağırlığa duyarlıdır. Kalan altı ilçenin medyan alanı en çok 1,25 km²'dir.
İlçe sırası, eşit alanlarda en iyi sırayı paylaştıran yarışma sıralamasıdır;
tam tablo [`district_rank_stability.csv`](../../outputs/analysis/weight_perturbation_v1/district_rank_stability.csv).

## Mevcut senaryolarla köprü

Üç mevcut senaryo sıralama tabanlı ölçüyle de hesaplanmıştır. "Yayımlanmış v1"
satırı mevcut duyarlılık tablolarının politikasıdır (baseline sabit ölçek,
alternatifler kendi min/max'ı) ve değişmemiştir.

| Senaryo | Ölçü | Yüksek+ (km²) | Baseline yüksek+ korunumu | Jaccard | İlçe ρ | İlk 5 ilçe |
|---|---|---:|---:|---:|---:|---|
| Deprem ağırlıklı | Yayımlanmış v1 | 818,70 | 0,951 | 0,614 | 0,960 | baseline ile aynı sıra |
| Deprem ağırlıklı | Sıralama tabanlı | 545,92 | 0,813 | 0,685 | 0,960 | baseline ile aynı sıra |
| Deprem ağırlıklı | Sabit ölçek | 1.353,76 | 0,993 | 0,400 | 0,964 | aynı küme, farklı sıra |
| Eşit ağırlık | Yayımlanmış v1 | 927,09 | 0,806 | 0,426 | 0,886 | Gelibolu yerine Bayramiç |
| Eşit ağırlık | Sıralama tabanlı | 545,92 | 0,687 | 0,523 | 0,888 | Gelibolu yerine Bayramiç |
| Eşit ağırlık | Sabit ölçek | 1.342,89 | 0,871 | 0,336 | 0,861 | Gelibolu yerine Bayramiç |

Aynı alanda karşılaştırıldığında deprem ağırlıklı senaryo baseline yüksek+
hücrelerinin %81'ini, eşit ağırlık %69'unu korur. İki değer de κ = 100
dağılımının içindedir (korunum %5'lik değeri 0,672); eşit ağırlık bu
dağılımın alt kuyruğuna yakındır.

## Çıktılar ve yorumun sınırı

`outputs/analysis/weight_perturbation_v1/` altında:

- `high_plus_probability_count_32635.tif` — κ = 100, sıralama tabanlı ölçü:
  hücrenin yüksek+ olduğu örnek sayısı (UInt16, 0–2.000; AOI dışı NoData
  65535; AOI içi 0 geçerli değerdir). Kaynak sürümünde dağıtılmaz.
- [`weight_samples.csv`](../../outputs/analysis/weight_perturbation_v1/weight_samples.csv),
  [`oat_summary.csv`](../../outputs/analysis/weight_perturbation_v1/oat_summary.csv),
  [`scenario_bridge.csv`](../../outputs/analysis/weight_perturbation_v1/scenario_bridge.csv),
  [`monte_carlo_summary.csv`](../../outputs/analysis/weight_perturbation_v1/monte_carlo_summary.csv),
  [`kappa_summary.csv`](../../outputs/analysis/weight_perturbation_v1/kappa_summary.csv),
  [`probability_area_summary.csv`](../../outputs/analysis/weight_perturbation_v1/probability_area_summary.csv),
  [`district_rank_stability.csv`](../../outputs/analysis/weight_perturbation_v1/district_rank_stability.csv),
  [`convergence.csv`](../../outputs/analysis/weight_perturbation_v1/convergence.csv)
  ve [üretim manifesti](../../outputs/analysis/weight_perturbation_v1/weight_perturbation_manifest.json).

Kontrol ve üretim: [QA sözleşmesi](../qa/canonical_integrity_checks.md#ağırlık-pertürbasyonu-kontrolü).

Pertürbasyon yalnız ağırlık belirsizliğini, tek bir uzman ağırlık setinin
çevresinde ve sabit kriter skorlarıyla inceler. P(yüksek+) bir afet olasılığı,
doğruluk yüzdesi veya bağımsız doğrulama değildir. κ seçimi belirsizliğin
genişliğini belirler; bu yüzden üç κ birlikte verilir. Skor dönüşümleri,
kaynak NoData'nın sıfıra dönüşmesi ve çift sayım gibi
[mevcut sınırlılıklar](../methodology/scientific_limits.md) örneklemeyle
giderilmez.
