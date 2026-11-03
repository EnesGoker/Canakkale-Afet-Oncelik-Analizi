[Türkçe](method_summary.md) | [English](method_summary.en.md)

# Yöntem özeti

Analizin tek sayfalık Türkçe özeti. Ayrıntılı yöntem, QA ve kaynak belgelerine
bağlantı verilir. [README](../README.md) · [Belge dizini](README.md).

## 1. Amaç ve kapsam

Proje, Çanakkale ilinde afet hazırlığı için **göreli önceliği** tehlike
duyarlılığı, maruziyet ve erişim kriterlerini birleştirerek sıralar. Bir öğrenci
CBS portföyü ve eğitim amaçlı bir ön değerlendirmedir; resmî afet riski, hasar
tahmini veya sınır ürünü **değildir**. Hiçbir kurum tarafından onaylanmamıştır.

## 2. Çalışma alanı ve grid

| Öğe | Değer |
|---|---|
| Alan | Çanakkale ili, 12 ilçe |
| CRS | EPSG:32635 (WGS 84 / UTM 35N) |
| Grid | 100 m; 1.586 × 1.423 hücre; çalışma alanında (AOI) **981.033 hücre** |
| AOI alanı | 9.810,33 km² (raster hücre alanından) |

Her kriter aynı şablon rastere hizalanır; sonuçlar yalnız AOI içinde
karşılaştırılır.

## 3. Kriterler, kaynaklar ve dönüşümler

`x`, 100 m şablona hizalandıktan sonraki kaynak değeridir; `d`, metre cinsinden
mesafedir. Skorlar 0–1 aralığına kırpılır.

| Kriter | Kaynak | Özgün çözünürlük | Skor | Ağırlık |
|---|---|---|---|---:|
| Deprem PGA (50 yılda %10 aşılma) | AFAD TDTH nokta parametreleri, yazarın IDW yüzeyi | 1.000 m | `clip((x − 0.2977) / 0.4381)` | 0,16 |
| Fay yakınlığı | MTA diri fay haritası verisi (2013/2014) | vektör | `max(1 − d / 10 000, 0)` | 0,12 |
| Zemin koşulu (Vs30) | USGS Global Vs30 Mosaic | 30″ (≈ 1 km) | `clip((900 − Vs30) / (900 − 180.042))` | 0,08 |
| Nüfus maruziyeti | WorldPop Türkiye 2020 | 100 m | `log1p(count) / log1p(159.301)` | 0,14 |
| Bina yoğunluğu | Microsoft bina izleri + OSM boşluk doldurma | vektör | hücrede bina izi oranı | 0,10 |
| Taşkın | JRC/CEMS RP100 taşkın derinliği | 90 m | `clip(x / 10.0526)`; kaynak NoData → 0 | 0,10 |
| Hidrografya yakınlığı | HydroRIVERS + OSM su yolları | vektör | `clip(1 − d / 1 000)` | 0,06 |
| Eğim | Copernicus DEM GLO-30 | 30 m | `clip(x / 40.2023)` (derece) | 0,08 |
| Arazi örtüsü duyarlılığı | ESA WorldCover 2021 | 10 m | sınıf skor tablosu (0,05–0,60), sonra 100 m ortalama | 0,06 |
| Ağaç örtüsü | Copernicus CLMS HRL Tree Cover Density 2021 | 10 m | `x / 100`'ün 100 m ortalaması | 0,04 |
| Yol erişim zorluğu | OpenStreetMap yolları | vektör | `clip(d / 2 000)` | 0,06 |

PGA ve eğim bölenleri, kayıtlı skorları yeniden üretecek şekilde mevcut veriden
kestirildi; sekiz kaynak→skor reçetesi kayıtlı rasterlarla 981.033 hücrenin
hepsinde eşleşir (en büyük mutlak fark 3 × 10⁻⁸'in altında).
[Kriter dönüşümleri](methodology/criterion_transformations.md) ·
[Kaynak envanteri](data_source_inventory.md).

## 4. Ağırlıklar ve bloklar

Baseline ağırlıklar ([`config/mcda_weights.tsv`](../config/mcda_weights.tsv))
beş blokta dengelenmiş gerekçeli uzman seçimleridir: deprem (PGA, fay yakınlığı,
zemin koşulu) 0,36; maruziyet (nüfus, bina) 0,24; su ve taşkın (taşkın,
hidrografya) 0,16; çevre ve arazi (eğim, arazi örtüsü, ağaç örtüsü) 0,18;
erişim (yol) 0,06. AHP, anket veya kalibrasyon kullanılmadı.
[Ağırlık gerekçesi](methodology/updated_mcda_methodology_note.md#6-ağırlıklandırma-stratejisi).

## 5. Birleştirme, normalizasyon ve sınıflar

Ham skor, 11 skorun ağırlıklı doğrusal toplamıdır (Float32, kayıtlı sıra).
Kanonik normalize skor `clip((raw − 0.029) / 0.473)`'tür ve beş eşit aralıklı
sınıfta gösterilir (eşikler 0,2, 0,4, 0,6, 0,8):

| Sınıf | Hücre | Alan (km²) | AOI payı |
|---|---:|---:|---:|
| 1 Çok düşük | 114.283 | 1.142,83 | %11,65 |
| 2 Düşük | 483.129 | 4.831,29 | %49,25 |
| 3 Orta | 329.029 | 3.290,29 | %33,54 |
| 4 Yüksek | 53.893 | 538,93 | %5,49 |
| 5 Çok yüksek | 699 | 6,99 | %0,07 |

"Yüksek+", 4. ve 5. sınıflardır (545,92 km²). Bu baseline'ın 27 donmuş girdi ve
çıktısı [`config/analysis_baseline_v1.json`](../config/analysis_baseline_v1.json)
içinde SHA-256 ile sabitlenir.
[Normalizasyon](methodology/normalization_and_baseline.md).

## 6. Senaryo ortaklığı

İki alternatif ağırlıklandırma (`earthquake-heavy`, `equal-weight`) baseline ile
karşılaştırılır. Her biri kendi gözlenen min/max ölçeğini kullanır; bu yüzden
sınıf değişiklikleri ağırlık değişikliğini ve yeniden ölçeklemeyi birlikte
içerir. **415,05 km²** (AOI'nin %4,23'ü) üç senaryonun hepsinde, **820,96 km²**
yalnız bir veya ikisinde yüksek+'dır (harita 13).
[Senaryo ortaklığı](analysis/scenario_agreement.md).

## 7. Ağırlık pertürbasyonu

Ağırlıklar baseline çevresinde Dirichlet dağılımından örneklenir (yoğunlaşma
κ × baseline ağırlıkları; ana κ = 100, özet satırları κ = 50 ve 200; her κ için
2.000 örnek, sabit tohum). Ana ölçü sıra tabanlıdır: her örnekte baseline
yüksek+ hücre sayısını tutan hücreler (en üst %5,565) yüksek+ sayılır; alan
tanım gereği sabittir ve ölçü konum kararlılığıdır. P(yüksek+), bir hücrenin
yüksek+ olduğu örneklerin oranıdır (harita 14); yalnız ağırlık belirsizliğini
ölçer ve **afet olasılığı değildir**.

- κ = 100: P ≥ 0,9 **215,75 km²**'yi, baseline yüksek+ alanının %39,52'sini
  kapsar; P ≥ 0,5 498,47 km²'yi (%91,3). P ≥ 0,9'da κ = 50: 126,19 km²;
  κ = 200: 296,12 km².
- Baseline'ın ilk beş ilçesi κ = 100 örneklerinin %94,25'inde aynı kümeyi,
  %36,65'inde aynı sırayı korur.
- Tek tek ±%10 / ±%20 değişiklikler: en düşük yüksek+ Jaccard değerleri
  hidrografya 0,867, fay 0,886, yol 0,896, PGA 0,900, eğim 0,917.

[Ağırlık pertürbasyonu](analysis/weight_perturbation.md).

## 8. Model varyantları

Varyantlar ağırlıkları değiştirir veya kriterleri birleştirir ve aynı sıra
tabanlı ölçüyü kullanır (yüksek+ kümesinin baseline ile Jaccard benzerliği):

| Varyant | Yüksek+ Jaccard |
|---|---:|
| Taşkın ağırlığı 0, oransal dağıtım | 0,958 (çok yüksek sınıf 0,515; sabit ölçek 0,391) |
| Arazi örtüsü ve ağaç örtüsü ortalaması, blok 0,0625 (ana) | 0,850 |
| Ortalama, blok 0,10 | 0,935 |
| Ağaç örtüsü çıkarıldı, oransal dağıtım | 0,676 |
| Ayrı tutuldu, blok 0,0625 | 0,814 |

Baseline skorunda kantil ve doğal kırılma eşikleri eşik seçiminin etkisini
gösterir: 5. sınıf 1.962,06 km² ve 939,03 km² olur. Kanonik sınıfların yerine
önerilmezler.
[Model varyantları](analysis/mcda_variants.md).

## 9. QA ve yeniden üretilebilirlik

- Tam QA baseline skoru ve sınıflarını, sekiz reçeteyi, korelasyonu, senaryo
  ortaklığını, pertürbasyonu ve varyantları, rapor tablolarını (bayt bayt) ve
  28 harita/atlas checksum'uyla 14 QGIS düzenini yeniden hesaplar. Kanonik veri
  ve kilitli bir GDAL 3.12.3 / NumPy 2.4.4 ortamı gerektirir.
- 27 modüldeki 465 birim test sentetik fikstür kullanır; CI stdlib, scientific
  ve gdal katmanlarını koşar (gdal yalnız macOS arm64'te); 17 qgis testi yalnız
  yerelde koşar.
- Yalnız depodan birim testler ile paket ve kapsam kontrolleri çalışır.
  [Kullanım](usage.md) · [QA kapsamı](qa/canonical_integrity_checks.md).

## 10. Bilinen sınırlılıklar

1. **Taşkın:** AOI'nin %96,65'inde (948.171 hücre) skor 0; kaynak NoData 0
   sayıldı ve anlamı birincil kaynakta doğrulanamadı. 0,10 ağırlık alanın
   %3,35'inde etkilidir.
2. **Çok yüksek sınıf taşkın hücrelerine bağlı:** 699 çok yüksek hücrenin 396'sında
   (%56,7) ve 54.592 yüksek+ hücrenin 4.902'sinde (%9,0) taşkın skoru 0'dan
   büyüktür.
3. **Taşkın ağırlığı 0:** yüksek+ kümesi korunur (Jaccard 0,958), ama çok yüksek
   sınıfın yarısı değişir (0,515).
4. **Çift sayım:** arazi örtüsü ve ağaç örtüsü r = 0,8152 ile ilişkilidir ve
   ağırlığın 0,10'unu birlikte taşır.
5. **5. sınıf dar:** 699 hücre (%0,07); onu eşik seçimi belirler (kantil
   1.962,06 km², doğal kırılma 939,03 km²).
6. **Ağırlıklar:** uzman yargısı; AHP/tutarlılık oranı, anket veya kalibrasyon
   yok.
7. **P(yüksek+)** afet olasılığı değildir; belirsizliğin genişliğini κ belirler
   (P ≥ 0,9: κ = 50 / 100 / 200'de 126,19 / 215,75 / 296,12 km²).
8. **İlçe sırası:** ilk beş küme örneklerin %94,25'inde, sıra %36,65'inde korunur
   (κ = 100; κ = 50: %87,05).
9. **Gelibolu** analizler arasında yer değiştirir: baseline'da 2., κ = 100
   örneklerinin %69,9'unda ilk üçte, kantil ve doğal kırılma sınıflarında 5.,
   sabit ölçekte taşkın ağırlığı 0 ile 4.
10. **Duyarlı kriterler** (±%20): hidrografya, fay, yol, PGA, eğim (en düşük
    Jaccard 0,867–0,917).
11. **Senaryo yeniden ölçeklemesi:** alternatif senaryolar kendi min/max'ını
    kullanır; sınıf değişiklikleri ağırlıkların ve yeniden ölçeklemenin
    birleşik etkisidir.
12. **Kaba kaynaklar** 100 m'ye yeniden örneklendi: PGA IDW 1.000 m, Vs30
    ≈ 1 km, taşkın 90 m (görünür hassasiyet).
13. **Karışık veri tarihleri:** faylar 2013/2014, nüfus 2020, arazi örtüsü 2021;
    altı kaynağın kayıtlı yılı veya indirme tarihi yok.
14. **Kestirilmiş parametreler:** iki ölçek parametresi (PGA, eğim) sonradan
    kestirildi; sekiz arazi örtüsü sınıf skorunun özgün gerekçesi kayıtlı değil.
15. **Sınır etkileri:** fay kaynağı AOI'ye kırpıldı; AOI dışındaki 5.272 arazi
    örtüsü hücresi analize girmez.
16. **Doğrulama yok:** gözlenmiş kayıp veya olaylarla kalibre edilmedi; bina
    kırılganlığı yok, bu yüzden sonuç risk değil öncelik ve maruziyettir.
17. **Yalnız depodan yeniden üretilemez:** işlenmiş kanonik veriler dağıtılmıyor
    ve bir indirme yolu yayımlanmadı.
18. **Veri hakları:** AFAD ve MTA'dan yazılı izin yok (harita 01, 02, 05, 13,
    14); JRC/CEMS lisansı (ODbL veya CC BY 4.0), bölgesel Vs30 bileşenleri ve
    statik görseller için HydroSHEDS koşulları doğrulanamadı; OSM türev
    veritabanı erişimi açık kalır. Atıf izin değildir.
19. **Ortam:** tam QA GDAL 3.12.3 gerektirir (3.13.3 eğim ve taşkını farklı
    yeniden örnekler); gdal katmanı CI'da yalnız macOS arm64'te, qgis katmanı
    hiç koşmaz.
20. **Harita üretimi:** Open Sans yazı tipi kurulu değil (yedek yazı tipi);
    CARTO karo dikişleri yeniden dışa aktarımda birkaç pikseli değiştirir
    (harita 01/02: 400 ve 1.085 piksel; harita 14: 2.251 piksel).

Sonraya planlananlar: AHP ikili ağırlıklar, olay verisiyle dış doğrulama, taşkın
veri kümesi sürümü, varyantların pertürbasyonla birleştirilmesi ve alan oranına
göre ilçe sıraları.
[Bilimsel sınırlılıklar](methodology/scientific_limits.md).

## 11. Kaynaklar ve haklar

[Kaynak envanteri](data_source_inventory.md) ·
[Veri hakları ve dağıtım](data_rights_and_distribution.md) ·
[Statik harita bildirimleri](static_map_attributions.md) ·
[Dosya kapsamı](publication_file_scope.md) ·
[Lisans kapsamı](../LICENSE_SCOPE.md).
