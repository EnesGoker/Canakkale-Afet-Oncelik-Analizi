# Üç senaryoda yüksek öncelik alanlarının mekânsal ortaklığı

**Kaynak sürümü kapsamı:** Aşağıdaki raster, harita PDF, atlas ve Word/PDF
yolları tam yerel çalışma çıktısıdır; bu dosyalar kaynak ve analitik özet
sürümünde dağıtılmaz. `outputs/maps/png/` altındaki harita PNG'leri kamu
kapsamındadır. Yerel üretim/kontrol komutları ilgili kanonik veri ve
çıktıların ayrıca bulunmasını gerektirir. [Kamu dosya kapsamı](../publication_file_scope.md).

**Analiz tarihi: 24 Ekim 2026.** Bu analiz, baseline, deprem ağırlıklı ve eşit ağırlıklı senaryolarda
**yüksek + çok yüksek** sınıfa giren hücrelerin nerede ortak kaldığını inceler.
Önceki duyarlılık analizine mekânsal üyelik ve ilçe karşılaştırması ekler.
[Kaynaklar, ağırlık gerekçeleri ve duyarlılık yaklaşımı](../methodology/updated_mcda_methodology_note.md)
önceden belgelenmiştir; yeni sonuçlar bunları tamamlar. Kriterler, ağırlıklar,
kanonik sınıflar ve eski sekiz referans CSV değiştirilmemiştir.

## Girdi, ölçek ve sınıf tanımı

[27 dosyalık sabit baseline kaydı](../../config/analysis_baseline_v1.json)
ve sayısal QA doğrulandıktan sonra, aynı 100 m şablonun `1` olduğu
**981.033 hücrenin tamamı** kullanılır. Her hücre 0,01 km²; toplam analiz
AOI alanı **9.810,33 km²**dir. Arazi örtüsündeki AOI dışı 5.272 hücre alınmaz.
Bütün senaryolar aynı hücrelerde karşılaştırılır.

Baseline, saklanan ve doğrulanmış kanonik sınıf rasterıdır. Alternatifler
11 kriterin kayıtlı sırada Float32 ağırlıklı toplamıyla yeniden hesaplanır.
Baseline normalizasyonu sabit `clip((raw−0.029)/0.473,0,1)` iken alternatifler
kendi AOI ham minimum ve maksimumlarıyla ölçeklenir. Üçünde de sınıf eşikleri
`0.2 / 0.4 / 0.6 / 0.8`; eşik üst sınıfa dahildir. **Sınıf ≥ 4**, ilgili
senaryoda yüksek + çok yüksek üyeliğidir.

[Korunan normalizasyon politikası](../methodology/normalization_and_baseline.md)
nedeniyle değişim, **ağırlıkların ve senaryoya özgü yeniden ölçeklemenin
birleşik etkisidir**. Harita saf ağırlık etkisini veya senaryolar arasında
ortak bir mutlak afet tehlikesi eşiğini ölçmez. Üç senaryo aynı kaynakları ve skor dönüşümlerini paylaşır; yüksek alanın
artması fiziksel tehlikenin arttığı anlamına gelmez.

## İl genelinde ortak ve değişen alanlar

Her hücrenin yüksek çıktığı senaryo sayısı 0–3 arasında tutulur. Yalnız bir
veya iki senaryoda yüksek çıkan **820,96 km²**, seçili senaryolar arasında
yüksek üyeliği değişen alanları gösterir. Üçünde ortak alan
**415,05 km²**dir: il AOI'sinin **%4,23**ü ve baseline yüksek alanının
**%76,03**ü. Paydalar farklıdır.

| Yüksek çıkan senaryo sayısı | Hücre | Alan (km²) | AOI (%) |
|---|---:|---:|---:|
| 0 | 857.432 | 8.574,32 | 87,40 |
| 1 | 59.536 | 595,36 | 6,07 |
| 2 | 22.560 | 225,60 | 2,30 |
| 3 | 41.505 | 415,05 | 4,23 |

Sayı haritası hangi senaryoların yüksek olduğunu tek başına belirtmez.
Bunun için ikinci raster ve ayrı tabloda sekiz kombinasyon saklanır:
`kod = B + 2D + 4E`; B baseline, D deprem ağırlıklı, E eşit ağırlıklı
senaryodur. Gösterge yüksekse 1, değilse 0'dır.

| Kod | Yüksek çıkan senaryolar | Hücre | Alan (km²) |
|---|---|---:|---:|
| 0 | Hiçbiri | 857.432 | 8.574,32 |
| 1 | Yalnız B | 188 | 1,88 |
| 2 | Yalnız D | 20.287 | 202,87 |
| 3 | B + D | 10.417 | 104,17 |
| 4 | Yalnız E | 39.061 | 390,61 |
| 5 | B + E | 2.482 | 24,82 |
| 6 | D + E | 9.661 | 96,61 |
| 7 | B + D + E | 41.505 | 415,05 |

AOI içindeki **0, bu üç senaryoda yüksek eşiğinin altında kalmak** demektir;
güvenli, afetsiz veya verisi eksiksiz alan demek değildir. AOI dışındaki
NoData ayrı tutulur. Aynı şekilde üçünde yüksek olmak, gerçekleşmiş olaylarla
doğrulama veya tüm olası ağırlıklarda değişmezlik iddiası taşımaz.

## Baseline'a göre korunan, eklenen ve çıkan alan

Baseline yüksek alanı **545,92 km²**; deprem ağırlıklı senaryoda **818,70 km²**,
eşit ağırlıkta **927,09 km²**dir. Korunan, iki yüksek kümenin kesişimidir;
eklenen alternatifte yüksek olup baseline'da yüksek olmayan, çıkan bunun
tersi olan hücrelerdir.

| Alternatif | Korunan km² | Eklenen km² | Çıkan km² | Birleşim km² | Jaccard % | Baseline korunma % |
|---|---:|---:|---:|---:|---:|---:|
| Deprem ağırlıklı | 519,22 | 299,48 | 26,70 | 845,40 | 61,42 | 95,11 |
| Eşit ağırlıklı | 439,87 | 487,22 | 106,05 | 1.033,14 | 42,58 | 80,57 |

**Jaccard = kesişim / birleşim**; **baseline korunma = kesişim / baseline
yüksek alanı**. Alternatifin kendi yüksek alanının baseline ile örtüşme
oranı ise **kesişim / alternatif yüksek alanı**dır: sırasıyla %63,42 ve
%47,45. Yüksek baseline korunması, yeni alanlar eklenirken aynı büyüklükte
Jaccard üretmez. Hiç yüksek hücresi olmayan iki kümenin birleşimi boşsa
Jaccard tanımsızdır; boş baseline için korunma oranı da tanımsızdır.
CSV'de tanımsız oranlar boş bırakılır.

## İlçelere göre dağılım

İlçe kimlikleri aynı GPKG'deki `fid=1..12` değerlerinden, şablon gridine
hücre merkezine göre rasterleştirilir. Her AOI hücresi tam bir ilçeye atanır;
ilçe sayımları il toplamını aynen verir. Aşağıdaki yüzdelerin paydası **ilgili
ilçedeki analiz AOI hücre alanıdır**. Eski tablolardaki vektör poligon alanına
bölünen oranlarla aynı ölçü değildir. Kaynak ilçe poligonlarının toplamı
9.810,3724 km² iken AOI grid alanı 9.810,33 km²dir; sınırın raster üzerinde
temsili nedeniyle bu küçük fark korunur.

| İlçe | Üçünde yüksek km² | İlçe AOI % | Bir veya ikisinde yüksek km² | İlçe AOI % |
|---|---:|---:|---:|---:|
| Bozcaada | 0,00 | 0,00 | 0,00 | 0,00 |
| Ayvacık | 27,52 | 3,13 | 78,20 | 8,88 |
| Ezine | 0,42 | 0,06 | 4,76 | 0,66 |
| Çanakkale Merkez | 0,00 | 0,00 | 11,54 | 1,14 |
| Lapseki | 0,00 | 0,00 | 10,59 | 1,29 |
| Biga | 72,89 | 5,57 | 99,68 | 7,61 |
| Yenice | 175,31 | 12,70 | 304,02 | 22,02 |
| Bayramiç | 22,34 | 1,86 | 53,45 | 4,44 |
| Gökçeada | 0,00 | 0,00 | 0,02 | 0,01 |
| Gelibolu | 42,27 | 5,14 | 132,90 | 16,16 |
| Eceabat | 0,00 | 0,00 | 0,24 | 0,06 |
| Çan | 74,30 | 8,22 | 125,56 | 13,89 |

**Yenice**, ortak yüksek alanın hem büyüklüğünde hem ilçe AOI payında öne
çıkar: 175,31 km² ve %12,70. 304,02 km²'nin yalnız bir veya iki senaryoda yüksek olması,
ortak alan ile senaryoya bağlı alanların aynı ilçede birlikte bulunduğunu
gösterir.

**Gelibolu**, il genelindeki artışın her ilçeye aynı yönde yansımadığını
gösterir: yüksek alan baseline'da 105,06 km², deprem ağırlıklı senaryoda
173,41 km², eşit ağırlıkta 44,12 km²dir. Ortak alan 42,27 km²; yalnız bir
veya iki senaryoda yüksek alan 132,90 km²dir. Yerel üyelikler farklı yönlerde değişir.

**Çan** için ortak yüksek alan 74,30 km² (%8,22), değişen yüksek üyeliği
125,56 km² (%13,89) kaplar. Biga'nın ortak alanı 72,89 km² ile yakın olsa
da ilçe AOI payı %5,57'dir. İlçe büyüklüğü farklı olduğundan mutlak alan ve
ilçe içi pay birlikte okunmalıdır. Karşılaştırma fiziksel nedenleri tek başına açıklamaz.

## Çıktılar ve yorumun sınırı

- Ortaklık haritası — PNG (`outputs/figures/scenario_agreement_v1/scenario_high_agreement.png`)
  ve PDF (`outputs/figures/scenario_agreement_v1/scenario_high_agreement.pdf`).
- 0–3 sayım rasterı (`outputs/analysis/scenario_agreement_v1/scenario_agreement_count_32635.tif`)
  ve 0–7 üyelik rasterı (`outputs/analysis/scenario_agreement_v1/scenario_agreement_membership_32635.tif`).
- [Sayım özeti](../../outputs/analysis/scenario_agreement_v1/agreement_count_summary.csv),
  [sekiz kombinasyon](../../outputs/analysis/scenario_agreement_v1/agreement_membership_summary.csv)
  ve [il/ilçe karşılaştırmaları](../../outputs/analysis/scenario_agreement_v1/scenario_high_area_comparison.csv).
- [Girdi, politika ve çıktı kaydı](../../outputs/analysis/scenario_agreement_v1/scenario_agreement_manifest.json).

Bu analiz yalnız seçilmiş üç senaryoya ve işlenmiş kanonik girdilere aittir.
Korelasyon, kaynak NoData'nın sıfıra dönüştürülmesi, skor tarifleri ve sınır
koşulları gibi [mevcut sınırlılıklar](../methodology/scientific_limits.md)
geçerliliğini korur. Yüksek üyelik değişimi, beş sınıfın bütün geçişlerini
veya skor farklarının büyüklüğünü kapsamaz; eski sınıf geçiş tabloları ayrıca
korunmuştur. Sonuç doğruluk yüzdesi, afet olasılığı veya belirsizlik olasılığı
değildir. Ayrı analiz haritası korunur. QGIS düzeninden üretilen
13. harita PNG (`outputs/maps/png/13_senaryo_ortakligi.png`) ve
PDF (`outputs/maps/pdf/13_senaryo_ortakligi.pdf`),
13 sayfalık atlasa (`outputs/atlas/canakkale_afet_oncelik_harita_atlasi.pdf`)
eklenmiştir. Kaynak atıfları ve kullanım açıklamaları
[haritaların ortak notunda](../../outputs/maps/README.md) bulunur.
