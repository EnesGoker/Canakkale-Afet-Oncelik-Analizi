# 11 Kriterli MCDA Metodoloji ve Ağırlıklandırma Notu

## 1. Amaç

Bu not, Çanakkale mekânsal öncelik analizi projesinde kullanılan 11 kriterli
multi-criteria decision analysis (MCDA) modelini açıklar.

Model; tehlike, maruziyet, zemin koşulu, çevresel bağlam ve erişilebilirlik
boyutlarını birlikte temsil eden normalize raster kriterlerinden oluşur.
Metodolojik olarak özellikle aşağıdaki üç kriter, deprem ve maruziyet yorumunu
güçlendiren temel bileşenlerdir:

- Fay yakınlığı skoru
- Nüfus maruziyeti skoru
- VS30 tabanlı zemin koşulu skoru

11 kriterli MCDA modelinin amacı, tehlike ilişkili, maruziyet ilişkili,
çevresel ve erişilebilirlik ilişkili kriterleri birleştirerek Çanakkale çalışma
alanı içinde göreli mekânsal öncelik alanlarını belirlemektir.

Bu çıktı öncül bir mekânsal öncelik analizidir. Resmi afet risk haritası,
tehlike haritası, kırılganlık haritası, acil durum planlama ürünü veya hukuken
bağlayıcı karar destek ürünü değildir.

---

## 2. Proje CRS, Grid ve Analiz Çözünürlüğü

Tüm nihai MCDA kriterleri aynı analiz gridine hizalanmıştır:

| Özellik | Değer |
|---|---|
| CRS | EPSG:32635 - WGS 84 / UTM Zone 35N |
| Pixel size | 100 m x 100 m |
| Raster boyutu | 1586 x 1423 |
| Geçerli analiz alanı | Çanakkale AOI |
| Sürekli rasterlarda AOI dışı değer | -9999 NoData |
| Class raster NoData değeri | 0 |

100 m grid, ders ve portfolyo ölçeğindeki mekânsal analiz için dengeli bir
çözünürlük olarak seçilmiştir. Yerel mekânsal değişimi gösterecek kadar
ayrıntılıdır ve hesaplama açısından yönetilebilir kalır.

---

## 3. Girdi Kriterleri

MCDA modeli aşağıdaki 11 input kriterini kullanır:

| No | Kriter | Dosya | Yorum |
|---:|---|---|---|
| 1 | Earthquake PGA Score | `earthquake_pga_score_32635.tif` | Daha yüksek değerler daha yüksek deprem yer hareketi proxy'sini gösterir |
| 2 | Fault Proximity Score | `fault_proximity_score_32635.tif` | Daha yüksek değerler diri fay hatlarına daha yakınlığı gösterir |
| 3 | Site Condition Score | `site_condition_score_32635.tif` | Daha yüksek değerler düşük VS30 / daha yumuşak zemin proxy'sini gösterir |
| 4 | Population Exposure Score | `population_exposure_score_32635.tif` | Daha yüksek değerler daha yüksek tahmini nüfus maruziyetini gösterir |
| 5 | Building Exposure Density Score | `building_exposure_density_score_32635.tif` | Daha yüksek değerler daha yüksek yapı maruziyeti yoğunluğunu gösterir |
| 6 | Flood Score | `flood_score_32635.tif` | Daha yüksek değerler taşkın ilişkili mekânsal öncelik proxy'sinin daha güçlü olduğunu gösterir |
| 7 | Hydrography Proximity Score | `hydrography_proximity_score_32635.tif` | Daha yüksek değerler nehir/hidrografya yakınlığı etkisinin daha güçlü olduğunu gösterir |
| 8 | Slope Score | `slope_score_32635.tif` | Daha yüksek değerler topoğrafik eğim etkisinin daha güçlü olduğunu gösterir |
| 9 | Landcover Sensitivity Score | `landcover_sensitivity_score_32635.tif` | Daha yüksek değerler arazi örtüsü ilişkili duyarlılığın daha yüksek olduğunu gösterir |
| 10 | Tree Cover Score | `tree_cover_score_32635.tif` | Daha yüksek değerler ağaç örtüsü ilişkili çevresel etkinin daha güçlü olduğunu gösterir |
| 11 | Road Accessibility Difficulty Score | `road_accessibility_difficulty_score_32635.tif` | Daha yüksek değerler yol erişilebilirliğinin daha zor olduğunu gösterir |

Tüm input kriterleri nihai weighted overlay adımı öncesinde 0-1 score rasterı
olarak temsil edilmiştir.

Bu, her kriterin mutlaka hem 0 hem 1 uç değerini aldığı anlamına gelmez.
Kaynak→skor adımlarının mevcut açıklama/kod bağlantıları, kurtarılan işlem
kayıtları ve sayısal eşdeğer reçeteleri
[kriter dönüşüm eşleştirmesinde](criterion_transformations.md) ayrı tutulur.

---

## 4. Özel Kriter Notları

### 4.1 Fault Proximity Score

Fay yakınlığı skoru, işlenmiş MTA diri fay veri setinden türetilmiştir:

- `data/processed/faults/canakkale_faults_final_32635.gpkg`
- `data/processed/analysis/fault_proximity_score_32635.tif`

Bu kriter, haritalanmış diri fay hatlarına göreli yakınlığı temsil eder. Deprem
kaynağına yakınlık proxy'si olarak kullanılır.

Önemli sınırlılık:

Bu kriter deterministik deprem kırılma olasılığını, resmi sismik tehlikeyi veya
konuma özgü fay yer değiştirme riskini temsil etmez.

### 4.2 Population Exposure Score

Nüfus maruziyeti skoru, WorldPop constrained 2020 population rasterından
türetilmiştir:

- `data/processed/population/population_count_aoi_100m_32635.tif`
- `data/processed/analysis/population_exposure_score_32635.tif`

Gridded nüfus dağılımı oldukça çarpık olduğu için population score log-normalize
edilmiştir. Bu yaklaşım, az sayıdaki yoğun hücrenin tüm skor aralığını
baskılamasını önler.

Önemli sınırlılık:

Bu kriter tahmini yerleşik nüfus maruziyetini temsil eder. Gerçek zamanlı,
gündüz, mevsimsel, turistik, öğrenci, çalışan veya geçici nüfusu temsil etmez.

### 4.3 Site Condition Score

Site condition score, USGS Global Vs30 Mosaic verisinden türetilmiştir:

- `data/processed/vs30/vs30_aoi_100m_32635.tif`
- `data/processed/analysis/site_condition_score_32635.tif`

Skor, VS30 değerlerinin inverse normalization işlemiyle hesaplanmıştır. Daha
düşük VS30 değerleri daha yumuşak zemin proxy'sini ve dolayısıyla daha yüksek
site condition score değerini gösterir.

Önemli sınırlılık:

Bu kriter global VS30 tabanlı bir proxy'dir. Yerel mikrobölgeleme haritası,
resmi zemin sınıfı haritası, sıvılaşma haritası veya yerel jeoteknik etüt ürünü
değildir.

---

## 5. Kapsam Dışı Bırakılan Aday Katmanlar

Aşağıdaki aday veri setleri, 11 kriterli MCDA modelinde ağırlıklı skor katmanı
olarak kullanılmaz.

### 5.1 Heyelan Veri Seti

Heyelan ilişkili bir MTA WMS katmanı belirlenmiştir:

- `mta:YERHEYELAN`

WFS erişimi kapalıdır ve serbestçe indirilebilir, nicel analiz için uygun GIS
vektör/raster veri seti proje veri tabanında yer almaz.

Model kullanımı:

Heyelan veri seti MCDA score katmanı olarak kullanılmaz.

Gerekçe:

WMS görselleştirme katmanı, PDF harita veya ekran görüntüsünden türetilmiş raster
nicel MCDA inputu olarak güvenilir kabul edilmez.

Metodolojik yorum:

Bu dışlama, heyelan tehlikesinin önemsiz olduğu anlamına gelmez. Yalnızca bu
çalışma kapsamında WMS görselleştirme katmanından güvenilir, nicel ve yeniden
üretilebilir MCDA girdisi üretilmediği anlamına gelir. Resmi heyelan envanteri
vektör/raster veri seti indirilebilir biçimde sağlandığında ayrı bir kriter
olarak modele eklenebilir.

### 5.2 Jeoloji / Litoloji Veri Seti

1:500,000 ölçekli jeoloji/litoloji veri seti incelenmiştir.

Model kullanımı:

Jeoloji/litoloji veri seti ağırlıklı MCDA kriteri olarak kullanılmaz.

Gerekçe:

Bağlamsal referans olarak potansiyel yarar taşısa da ölçek ve yorum ayrıntısı,
100 m raster tabanlı ağırlıklı öncelik modeline doğrudan kriter olarak eklemek
için yeterli değildir.

### 5.3 Bina Yaşı, Bina Değeri ve Ekonomik Değer

Bina yaşı, yapısal kalite ve ekonomik değer değerli kırılganlık/maruziyet
göstergeleri olabilir.

Model kullanımı:

Bina yaşı, yapısal kalite ve ekonomik değer katmanları ağırlıklı MCDA kriteri
olarak kullanılmaz.

Gerekçe:

Bu proje kapsamı içinde güvenilir, açık, mekânsal olarak ayrıntılı bina düzeyi
veri setleri mevcut değildir.

---

## 6. Ağırlıklandırma Stratejisi

MCDA modeli weighted linear combination yaklaşımını kullanır.

Operasyonel ağırlık kaynağı:

```text
config/mcda_weights.tsv
```

Bu dosyadaki `baseline` senaryosu, canonical MCDA rasterlarının ve rapor
tablolarının ana ağırlık setidir. `earthquake-heavy` ve `equal-weight`
senaryoları nihai model değil, yalnızca küçük ölçekli robustness/sensitivity
kontrolleri için ayrılmış alternatif senaryolardır.

### 6.1 Yorum Sınırı

Bu ağırlık seti AHP, ikili karşılaştırma matrisi, resmi uzman anketi veya
gözlenmiş afet kaybı kalibrasyonu ile üretilmiş nihai karar ağırlığı değildir.
Bu nedenle ağırlıklar mutlak risk katsayısı, resmi planlama eşiği veya kurumsal
öncelik kararı gibi yorumlanmamalıdır.

Bu çalışmada ağırlıklar, processed-canonical veri katmanlarıyla üretilebilir
keşifsel bir MCDA öncelik indeksi kurmak için kullanılmıştır. Karar mantığı üç
ilkeye dayanır:

- tehlike ve maruziyet göstergelerine model içinde daha yüksek açıklayıcı rol
  vermek,
- aynı afet boyutunu kısmen tekrar eden proxy katmanlarda çift sayım etkisini
  sınırlamak,
- çevresel, topoğrafik ve erişilebilirlik göstergelerini destekleyici rol
  düzeyinde tutarak tek bir kriter grubunun modeli tamamen domine etmesini
  önlemek.

Bu çerçeve, çalışmanın amacını doğrulanmış afet risk tahmini değil, göreli ve
tekrar üretilebilir mekânsal önceliklendirme olarak sınırlar.

### 6.2 Baseline Ağırlık Seti

Nihai baseline ağırlıklar:

| Blok | Kriter | Ağırlık |
|---|---|---:|
| Deprem tehlikesi | Earthquake PGA Score | 0.16 |
| Deprem kaynak yakınlığı | Fault Proximity Score | 0.12 |
| Zemin koşulu | Site Condition Score | 0.08 |
| İnsan maruziyeti | Population Exposure Score | 0.14 |
| Fiziksel maruziyet | Building Exposure Density Score | 0.10 |
| Taşkın / su ilişkili öncelik | Flood Score | 0.10 |
| Hidrografya yakınlığı | Hydrography Proximity Score | 0.06 |
| Topoğrafya | Slope Score | 0.08 |
| Arazi örtüsü | Landcover Sensitivity Score | 0.06 |
| Vejetasyon / ağaç örtüsü | Tree Cover Score | 0.04 |
| Erişilebilirlik | Road Accessibility Difficulty Score | 0.06 |
| Toplam |  | 1.00 |

Ağırlıklandırma stratejisi, tek bir kriter grubuna aşırı baskınlık vermemek
üzere tasarlanmıştır.

Deprem ilişkili kriterler Çanakkale için önemlidir; ancak model maruziyet,
taşkın ilişkili, çevresel ve erişilebilirlik ilişkili boyutları da içerir.

### 6.3 Kriter Düzeyi Gerekçe

| Kriter | Ağırlık | Gerekçe |
|---|---:|---|
| Earthquake PGA Score | 0.16 | AFAD TDTH parametrelerinden türetilen PGA yüzeyi, deprem yer hareketi için modeldeki en doğrudan sismik tehlike proxy'sidir; bu nedenle tekil kriterler içinde en yüksek ağırlıklardan birini alır. |
| Fault Proximity Score | 0.12 | Diri fay yakınlığı deprem kaynak bağlamını güçlendirir, ancak tek başına deterministik risk veya hasar göstergesi olmadığı için PGA'dan düşük tutulur. |
| Site Condition Score | 0.08 | VS30 tabanlı zemin koşulu yer hareketi etkisini destekleyen önemli bir proxy'dir; global ölçekli veri olduğu ve yerel mikrobölgeleme yerine geçmediği için orta düzey ağırlık alır. |
| Population Exposure Score | 0.14 | İnsan maruziyeti, afet önceliklendirmede doğrudan etkilenebilir nüfusu temsil eden ana göstergedir; fakat dinamik nüfusu içermediği için deprem PGA'nın altında kalır. |
| Building Exposure Density Score | 0.10 | Yapılı çevre maruziyetini temsil eder; bina yaşı, taşıyıcı sistem ve yapısal kırılganlık içermediği için nüfus maruziyetinden daha düşük ağırlık alır. |
| Flood Score | 0.10 | Taşkın derinliği tabanlı destek yüzeyi, su ilişkili tehlike boyutunu doğrudan temsil eden ana girdidir; resmi yerel hidrodinamik risk modeli olmadığı için kontrollü tutulur. |
| Hydrography Proximity Score | 0.06 | Hidrografya yakınlığı taşkın ve su ilişkili bağlamı destekler, ancak flood score ile kavramsal örtüşme riski bulunduğu için daha düşük ağırlıklandırılır. |
| Slope Score | 0.08 | Eğim, topoğrafik duyarlılık ve erişim koşulları için destekleyici bir göstergedir; doğrudan heyelan veya risk modeli olmadığı için orta-düşük düzeyde tutulur. |
| Landcover Sensitivity Score | 0.06 | Arazi örtüsü, çevresel duyarlılık ve yüzey koşulları için bağlamsal destek sağlar; afet tehlikesini tek başına temsil etmediği için düşük-orta ağırlık alır. |
| Tree Cover Score | 0.04 | Ağaç örtüsü, yangın/ekolojik duyarlılık yorumunu destekleyen tamamlayıcı göstergedir; tehlike türüne göre anlamı değişebildiği için en düşük ağırlık grubundadır. |
| Road Accessibility Difficulty Score | 0.06 | Yol erişim zorluğu operasyonel müdahale açısından önemlidir, ancak tehlike veya maruziyet göstergesi değil destekleyici erişilebilirlik proxy'sidir. |

### 6.4 Blok Düzeyi Denge

Baseline modelde blok düzeyi ağırlık dağılımı şöyledir:

| Blok | Dahil edilen kriterler | Toplam ağırlık | Yorum |
|---|---|---:|---|
| Deprem ilişkili blok | Earthquake PGA, Fault Proximity, Site Condition | 0.36 | Çanakkale'nin sismik bağlamı nedeniyle en güçlü bloktur; fakat modelin tamamını deprem haritasına dönüştürmez. |
| Maruziyet bloğu | Population Exposure, Building Exposure Density | 0.24 | İnsan ve yapılı çevre maruziyetini birlikte temsil eder; kırılganlık verisi olmadığı için mutlak risk yerine exposure proxy olarak yorumlanır. |
| Su / taşkın ilişkili blok | Flood, Hydrography Proximity | 0.16 | Taşkın destek yüzeyi ana girdidir; hidrografya yakınlığı çift sayım riskini azaltmak için daha düşük tutulur. |
| Çevresel / topoğrafik blok | Slope, Landcover Sensitivity, Tree Cover | 0.18 | Topoğrafya ve arazi örtüsü bağlamını modele ekler; doğrudan tehlike modeli olmayan proxy'ler destekleyici düzeyde kalır. |
| Erişilebilirlik bloğu | Road Accessibility Difficulty | 0.06 | Müdahale ve erişim zorluğunu temsil eder; operasyonel bağlam sağlar ama tehlike/maruziyet bloklarını gölgelememelidir. |

Bu dağılım, baseline sonucu tek bir afet türüne veya tek bir maruziyet
göstergesine indirgemeden, farklı kriter grupları arasında kontrollü bir denge
kurmayı amaçlar.

### 6.5 Sınırlı Ağırlık Duyarlılığı Kontrolü

Ağırlık varsayımının sonuç üzerindeki etkisini görünür kılmak için üç senaryolu
sensitivity/robustness kontrolü kullanılır:

| Senaryo | Rol | Yüksek+çok yüksek alan km² | Baseline class agreement |
|---|---|---:|---:|
| `baseline` | Canonical sonuç | 545.92 | 100.00% |
| `earthquake-heavy` | Deprem ilişkili kriterleri öne çıkaran robustness senaryosu | 818.70 | 84.08% |
| `equal-weight` | Tüm kriterleri eşit kabul eden robustness senaryosu | 927.09 | 72.59% |

Bu kontrol, kapsamlı AHP, Monte Carlo ağırlık örneklemesi veya uzman paneli
değildir. Amaç, baseline sonucunun ağırlık varsayımına ne ölçüde duyarlı
olduğunu raporlanabilir tablolara indirmektir. Deprem ağırlıklı senaryoda ana
yüksek öncelik çekirdeği büyük ölçüde korunur; eşit ağırlıklı senaryo ise daha
geniş yüksek öncelik alanı üretir ve modelin ağırlık varsayımına belirgin
duyarlılık gösterdiğini ortaya koyar.

**Ölçekleme ayrımı:** Baseline sınıfları mevcut canonical rasterdan alınır;
alternatifler kendi AOI içi gözlenen ham min/max değerleriyle normalize
edilir. Dolayısıyla sınıf farkları ağırlık değişimiyle yeniden ölçeklemenin
birleşik etkisini içerir. Alternatiflerde “yüksek” kendi senaryosunun göreli
ölçeğindedir; ortak mutlak tehlike eşiği değildir. Mevcut üç senaryonun
kayıtlı özetleri bağımsız hesapla teyit edilmiştir. Ayrıntı:
[normalizasyon ve baseline](normalization_and_baseline.md).

[Mekânsal ortaklık analizi](../analysis/scenario_agreement.md), aynı üç
senaryonun yüksek/çok yüksek hücrelerini konumlarıyla karşılaştırır.
415,05 km² üçünde de, 820,96 km² yalnız bir veya iki senaryoda yüksek kalır.
İl ve ilçe tabloları, baseline'a göre korunan/eklenen/çıkan alanları da verir.
Bu ek analiz, mevcut senaryo tanımlarını ve sonuçlarını değiştirmez.

[Ağırlık pertürbasyonu](../analysis/weight_perturbation.md), baseline
ağırlıklarının çevresinde iki ek deneme yapar: her kriter için tek tek ±%10 /
±%20 değişim (OAT) ve Dirichlet(κ·w) örneklemesi (κ = 100 ana; κ = 50 ve 200
özet; κ başına 2.000 örnek, sabit tohum). Ana ölçü sıralama tabanlıdır: her
örnekte baseline'ın yüksek + çok yüksek hücre sayısı (54.592) en yüksek ham
skordan seçilir. Bu ölçüde yüksek+ alanı **tanım gereği sabittir**
(545,92 km²); sonuç alanın büyüklüğünü değil, **konumunun kararlılığını**
ölçer. κ = 100'de örneklerin en az %90'ında yüksek+ kalan dayanıklı çekirdek
215,75 km²'dir (baseline yüksek+'nın %39,52'si); kalan yaklaşık %60 ağırlığa
duyarlıdır. Baseline sabit ölçeğiyle (`0.029/0.473`) alan değişimi yalnız ek
tabloda verilir. Üç mevcut senaryo da sıralama tabanlı ölçüyle köprü satırı
olarak hesaplanmıştır; yukarıdaki tablo ve eski CSV'ler değişmez.

[MCDA varyantları](../analysis/mcda_variants.md) üç modelleme seçimini tek tek
sınar: taşkın ağırlığının sıfırlanması (kaynak NoData'sının anlamı
doğrulanamadığı için kapsama maskesi kurulmaz), arazi örtüsü ile ağaç
örtüsünün ortalama tek kriterde birleştirilmesi (blok ağırlığı 0,06/0,96 =
0,0625; ek satırlar yalnız birleştirme, yalnız blok ağırlığını düşürme ve ağaç
örtüsünü çıkarma) ve
eşik seçiminin etkisi (kantil ve doğal kırılma, yalnız baseline skorunda).
Sıralama tabanlı ölçüde Jaccard sırasıyla 0,958, 0,850 (0,935 / 0,814 / 0,676);
kanonik eşit aralıklı sınıflar değişmez.

Tablosal çıktı dosyaları:

```text
outputs/tables/mcda_sensitivity_scenario_summary.csv
outputs/tables/mcda_sensitivity_interpretation.csv
outputs/tables/mcda_sensitivity_class_distribution.csv
outputs/tables/mcda_sensitivity_top_districts.csv
outputs/tables/mcda_sensitivity_class_transition.csv
```

---

## 7. Weighted Overlay Formülü

Raw MCDA score aşağıdaki şekilde hesaplanır:

Formül:

```text
mcda_priority_score =
  0.16 * earthquake_pga_score
+ 0.12 * fault_proximity_score
+ 0.08 * site_condition_score
+ 0.14 * population_exposure_score
+ 0.10 * building_exposure_density_score
+ 0.10 * flood_score
+ 0.06 * hydrography_proximity_score
+ 0.08 * slope_score
+ 0.06 * landcover_sensitivity_score
+ 0.04 * tree_cover_score
+ 0.06 * road_accessibility_difficulty_score
```

Çıktı dosyası:

```text
data/processed/analysis/mcda_priority_score_32635.tif
```

Raw weighted score istatistikleri:

| Özellik | Değer |
|---|---:|
| Minimum | 0.029285 |
| Maximum | 0.501820 |
| Mean | 0.201904 |
| Standard deviation | 0.066713 |
| NoData | -9999 |
| Valid percent | 43.47 |

---

## 8. Normalization

Raw MCDA score, min-max normalization kullanılarak 0-1 aralığına normalize
edilmiştir.

Formül:

```text
normalized_score = (raw_score - min_raw_score) / (max_raw_score - min_raw_score)
```

Bu analizde:

```text
min_raw_score = 0.029
max_raw_score = 0.502
```

Çıktı dosyası:

```text
data/processed/analysis/mcda_priority_score_normalized_32635.tif
```

Normalize score istatistikleri:

| Özellik | Değer |
|---|---:|
| Minimum | 0.000603 |
| Maximum | 0.999620 |
| Mean | 0.365548 |
| Standard deviation | 0.141042 |
| NoData | -9999 |
| Valid percent | 43.47 |

Tam 0 ve 1 değerlerinden küçük sapmalar, floating point precision ve işleme
komutunda kullanılan yuvarlanmış min-max değerlerinden kaynaklanır.

Bu bölüm canonical baseline içindir. Alternatif senaryoların gözlenen
min/max uygulaması ve karşılaştırma yorumu
[ayrı açıklamada](normalization_and_baseline.md#mevcut-hesap-politikası) yer alır.

---

## 9. Öncelik Sınıflandırması

Normalize MCDA score beş öncelik sınıfına ayrılmıştır:

| Sınıf | Aralık | Etiket |
|---:|---|---|
| 1 | 0.00 - 0.20 | Çok Düşük Öncelik |
| 2 | 0.20 - 0.40 | Düşük Öncelik |
| 3 | 0.40 - 0.60 | Orta Öncelik |
| 4 | 0.60 - 0.80 | Yüksek Öncelik |
| 5 | 0.80 - 1.00 | Çok Yüksek Öncelik |

Çıktı dosyası:

```text
data/processed/analysis/mcda_priority_class_32635.tif
```

Class raster şu değerleri kullanır:

| Değer | Anlam |
|---:|---|
| 0 | NoData / AOI dışı |
| 1 | Çok Düşük Öncelik |
| 2 | Düşük Öncelik |
| 3 | Orta Öncelik |
| 4 | Yüksek Öncelik |
| 5 | Çok Yüksek Öncelik |

Class dağılımı:

| Sınıf | Hücre sayısı | Yüzde |
|---:|---:|---:|
| 1 | 114,283 | 11.65% |
| 2 | 483,129 | 49.25% |
| 3 | 329,029 | 33.54% |
| 4 | 53,893 | 5.49% |
| 5 | 699 | 0.07% |

Çok yüksek öncelik sınıfı seçici tutulur. Eşit alanlı sınıflar zorlamak yerine
en güçlü birleşik skor alanlarını temsil eder.

---

## 10. Çift Sayım ve Model Dengesi

Bu bölümdeki mevcut kavramsal gerekçeler, sonradan eklenen
[11 kriterin Pearson analizinde](../analysis/criterion_correlation.md)
aynı AOI üzerindeki sayısal eşdeğişimle birlikte değerlendirilir.
Korelasyon analizi ağırlık veya kriter değiştirmemiştir.

Bazı kriterler kavramsal olarak ilişkilidir. Ağırlıklandırma stratejisi, bu
örtüşmeleri tekil ağırlıkları sınırlayarak ele alır.

### 10.1 Deprem İlişkili Kriterler

Deprem ilişkili grup şunları içerir:

- Earthquake PGA Score
- Fault Proximity Score
- Site Condition Score

Bu kriterler farklı boyutları temsil eder:

- bölgesel yer hareketi proxy'si
- diri fay hatlarına yakınlık
- yerel/global zemin koşulu proxy'si

Deprem ilişkili blok ağırlığı:

```text
0.16 + 0.12 + 0.08 = 0.36
```

Bu değer, deprem ilişkili kriterlere güçlü etki verir; ancak tüm modeli yalnızca
deprem haritasına dönüştürmez.

### 10.2 Maruziyet Kriterleri

Maruziyet grubu şunları içerir:

- Population Exposure Score
- Building Exposure Density Score

Maruziyet blok ağırlığı:

```text
0.14 + 0.10 = 0.24
```

Bu ayrım, insan maruziyetini fiziksel/yapılı çevre maruziyetinden ayırır.

### 10.3 Su İlişkili Kriterler

Su ilişkili grup şunları içerir:

- Flood Score
- Hydrography Proximity Score

Su ilişkili blok ağırlığı:

```text
0.10 + 0.06 = 0.16
```

Hidrografya yakınlığı, taşkın skoru ile çift sayım riskini azaltmak için daha
düşük ağırlık alır.

### 10.4 Çevresel ve Topoğrafik Kriterler

Çevresel/topoğrafik grup şunları içerir:

- Slope Score
- Landcover Sensitivity Score
- Tree Cover Score

Birleşik ağırlık:

```text
0.08 + 0.06 + 0.04 = 0.18
```

Ağaç örtüsü düşük ağırlık alır; çünkü afet önceliği açısından anlamı tehlike
türüne göre değişebilir.

### 10.5 Erişilebilirlik Kriteri

Road accessibility difficulty, destekleyici öncelik kriteri olarak şu ağırlıkla
korunmuştur:

```text
0.06
```

Bu kriter, erişimi zor alanların operasyonel açıdan daha zorlayıcı olabileceği
yorumunu destekler.

---

## 11. MCDA Çıktı Dosyaları

MCDA modeli aşağıdaki raster çıktıları üretir:

| Çıktı | Açıklama |
|---|---|
| `mcda_priority_score_32635.tif` | Raw weighted MCDA score |
| `mcda_priority_score_normalized_32635.tif` | Min-max normalized MCDA score |
| `mcda_priority_class_32635.tif` | Beş sınıflı öncelik haritası |

Bu dosyalar şu konumdadır:

```text
data/processed/analysis/
```

---

## 12. Yorumlama

MCDA sonucu, Çanakkale çalışma alanı içindeki göreli mekânsal
önceliği temsil eder.

Daha yüksek değerler, seçilmiş birden fazla kriterin birleşerek daha yüksek
öncül öncelik skorları ürettiği alanları gösterir.

Sonuç şu şekilde yorumlanmalıdır:

- öncül mekânsal öncelik analizi
- çok kriterli tarama ürünü
- portfolyo/ders düzeyi GIS analizi
- karar destek tarzında keşifsel çıktı

Sonuç şu şekilde yorumlanmamalıdır:

- resmi afet risk haritası
- resmi tehlike haritası
- deterministik deprem/taşkın/heyelan modeli
- saha verisiyle doğrulanmış kırılganlık değerlendirmesi
- acil durum müdahale planı
- hukuki veya operasyonel planlama ürünü

---

## 13. Temel Sınırlılıklar

Önemli sınırlılıklar:

- Model seçilen input kriterlerine ve ağırlıklara bağlıdır.
- Farklı ağırlıklandırma stratejileri farklı sonuçlar üretebilir.
- Bazı kriterler doğrudan ölçüm değil proxy niteliğindedir.
- Population data tahmindir ve dinamik nüfusu temsil etmez.
- VS30 data global ölçektedir ve yerel jeoteknik çalışmaların yerine geçmez.
- Fault proximity proxy'dir ve tam bir sismik tehlike modeli değildir.
- Building exposure density bina yaşı, yapısal kalite veya kullanım yoğunluğunu temsil etmez.
- Flood ve hydrography kriterleri kavramsal olarak ilişkili olabilir.
- Tree cover yorumu tehlike türüne göre değişebilir.
- Çıktı gözlenmiş afet kayıpları veya uzman değerlendirmeli yerel risk verisiyle doğrulanmamıştır.

---

## 14. Yardımcı Metodoloji Kaynakları

Bu metodoloji notu aşağıdaki proje dosyalarıyla birlikte okunur:

| Kaynak | Rol |
|---|---|
| `config/mcda_weights.tsv` | Baseline ve robustness senaryoları için ağırlık kaynağı |
| `docs/methodology/scientific_limits.md` | Bilimsel sınırlılıklar ve yorum sınırları |
| `docs/report_table_outputs.md` | MCDA sınıf dağılımı, ilçe alanları ve sensitivity tabloları |
| `scripts/bash/mcda_pipeline_commands.sh` | MCDA raster üretim ve doğrulama komutları |
| `scripts/bash/generate_sensitivity_tables.sh` | Üç senaryolu sensitivity/robustness tablo üretimi |
| [Kriter dönüşüm eşleştirmesi](criterion_transformations.md) | 11 kriter için mevcut bölüm/kod bağlantıları ve sayısal kaynak→skor reçeteleri |
| [Normalizasyon ve baseline](normalization_and_baseline.md) | Senaryo ölçeklerinin yorumu ve iki ek analizin dondurulmuş girdileri |
| [Sınır bulguları](../qa/stage3_boundary_findings.md) | Fay çevre verisinin sınırı ve arazi örtüsünün AOI izolasyonu |
