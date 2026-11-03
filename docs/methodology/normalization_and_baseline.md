# Normalizasyon ve iki ek analiz için sabitlenen baseline

## Mevcut hesap politikası

| Senaryo | Sınıflandırmada kullanılan ölçek |
|---|---|
| `baseline` | `clip((raw−0.029)/0.473,0,1)`; kaydedilmiş canonical sınıflar. |
| `earthquake-heavy` | Kendi AOI içindeki gözlenen ham min/max değerleriyle `clip((raw−min)/(max−min),0,1)`. |
| `equal-weight` | Kendi AOI içindeki gözlenen ham min/max değerleriyle aynı dönüşüm. |

Her üçünde sınıf eşikleri `0.2/0.4/0.6/0.8`dir. Eşik değeri üst sınıfa girer.
Baseline sabitleri ve yuvarlama etkisi [mevcut yöntem §8'de](updated_mcda_methodology_note.md#8-normalization)
zaten açıklanmıştır. Alternatiflerin işlemi
[duyarlılık üreticisindeki `weighted_score`](../../scripts/python/generate_sensitivity_tables.py)
içindedir. Üretici baseline ham istatistiklerini de hesaplar; baseline sınıf
karşılaştırmasında kaydedilmiş canonical sınıf rasterını kullanır.

Bu uygulama korunmuştur. Alternatiflerde yüksek sınıf, **ilgili senaryonun
kendi göreli ölçeğinde** yüksek önceliktir. Sınıf farkları ağırlık değişimi
ile senaryoya göre yeniden ölçeklemenin **birleşik etkisini** içerir.
Ortak bir mutlak afet tehlikesi eşiği veya yalnız ağırlık katsayısının etkisi
olarak okunmamalıdır.

## Mevcut sonuçların teyidi

| Senaryo | Yüksek + çok yüksek alan (km²) | Baseline sınıf uyumu (%) |
|---|---:|---:|
| baseline | 545.92 | 100.00 |
| earthquake-heavy | 818.70 | 84.08 |
| equal-weight | 927.09 | 72.59 |

Üç senaryonun [mevcut özet CSV'sindeki](../../outputs/tables/mcda_sensitivity_scenario_summary.csv)
13'er sayısal alan bağımsız hesapla karşılaştırıldı; farkların tamamı `0`.
Canonical ham/normalize skor ve sınıflar da mevcut sabitlerle birebir eşleşti.
Yeni bir normalizasyon veya güncellenmiş sonuç tablosu üretilmedi.

Ölçek farkının etkisini ayıran yalnız tanısal bir hesapta, baseline'a kendi
gözlenen min/max'ı uygulanınca 1.393 hücrenin sınıfı değişir. Bu, iki
yaklaşımın tamamen aynı olmadığını gösterir; baseline'ı yeniden sınıflandırma
önerisi değildir. İki ek analiz mevcut politikayı kullanacaktır.

## Ağırlık pertürbasyonunda ölçek

[Ağırlık pertürbasyonu](../analysis/weight_perturbation.md) binlerce ağırlık
örneği kullandığı için ölçek seçimi sonucu belirler:

| Ölçek | Yüksek + çok yüksek tanımı | Kullanım |
|---|---|---|
| Sıralama tabanlı (ana) | Her örnekte en yüksek ham skorlu 54.592 hücre (baseline payı, %5,565); çok yüksek en yüksek 699 hücre. Sınır k'inci en büyük değer, eşitler dahil | P(yüksek+) rasterı, olasılık sınıfları, ilçe sıra kararlılığı |
| Baseline sabit ölçeği (ek) | `clip((raw−0.029)/0.473,0,1) ≥ 0.6` | Yalnız alan değişimi tabloları |
| Örneğin kendi min/max'ı | — | Kullanılmaz: tek uç hücreye bağlıdır; baseline ağırlığında bile 1.393 hücre farklı sınıf verir |

Sıralama tabanlı ölçüde yüksek+ alanı tanım gereği sabittir; ölçü, alanın
büyüklüğünü değil, hangi hücrelerin yüksek+ kaldığını (konum kararlılığını)
gösterir. Baseline ağırlıklarıyla iki ölçek de kanonik sınıfları birebir verir.
Ağırlığın neredeyse her yerde sıfır olan kriterlerden (taşkın, bina, nüfus)
ortalaması yüksek kriterlere kayması bütün ham skorları yükseltir; sabit
ölçekteki alan artışının büyük kısmı bu düzey kaymasıdır. Mevcut üç senaryonun
yukarıdaki politikası ve kayıtlı tabloları değişmez; sıralama tabanlı karşılıkları
ayrı köprü satırlarıdır.

## Girdi sürümü ve AOI izolasyonu

[`config/analysis_baseline_v1.json`](../../config/analysis_baseline_v1.json),
`canakkale-canonical-11criteria-v1` kimliğiyle **27 dosyanın** boyut/SHA-256
kaydını tutar: 11 skor, şablon, üç canonical sonuç, ağırlık config'i, ilçe
vektörü, iki mevcut hesap/politika scripti ve sekiz referans CSV.

Bu, processed-canonical seviyeden başlayan bir analiz sürümüdür; büyük
upstream ham paketlerin tamamından yeniden kurulum iddiası değildir.
README/rapor düzenlemesi veya yeni sonuç eklenmesi baseline'ı değiştirmez;
kayıtlı girdi/config/politika değişimi yeniden sürüm kararı gerektirir.

Salt okunur kontrol:

```bash
python3 scripts/python/analysis_baseline.py --check
```

Bu komut standart kütüphaneyle dosya bütünlüğünü ve kayıtlı sözleşmeyi
denetler. Manifest kendisini yeniden üretmez. Kaynak klonunda büyük veriler
yoksa eksik dosya bildirir ve doğrulanan/eksik dosyaları ayrı sayar; checksum
eşleşmesi bilimsel doğrulama değildir.

Kanonik veri içermeyen kamu kaynak sürümünde kapsam açıkça seçilir:

```bash
python3 scripts/python/analysis_baseline.py --check --scope public-source
```

Bu modda dağıtılmayan kayıtlar iki bağımsız yoldan belirlenir: manifestteki
`data/processed/` kayıtları ve
[kamu seçim listesinde](../../config/public_source_release_v1.json) bulunmayan
kayıtlar. İki küme eşit olmalıdır; bugün ikisi de aynı 16 dosyadır. Bu
dosyaların her biri kopyada bulunmamalıdır ve tek tek `SKIPPED` satırıyla
listelenir; kalan 11 kayıt checksum ile doğrulanır. Kanonik verinin bir kısmı
veya tamamı kopyada varsa kontrol başarısız olur ve tam kapsamı önerir.

Yeni analizler [ortak yükleyiciyi](../../scripts/python/analysis_baseline.py)
`load_frozen_inputs()` ile kullanır: önce snapshot, sonra sayısal baseline QA
kontrol edilir; kriterler yalnız **şablon AOI'sinin 981.033 hücresinden**
oluşan ayrı 1D kopyalar halinde döner. Üç senaryo tanımı aynı config'ten
alınır. Böylece arazi örtüsünün AOI dışındaki 5.272 hücresi korelasyona veya
senaryo ortaklığı hesabına girmez. Kaynak raster değiştirilmemiştir.

Yeni hesaplarda bu yükleyicinin kullanılması gerekir; manifest kontrolünü
atlayıp bütün dikdörtgen raster hücrelerini kullanmak aynı analiz sözleşmesi
değildir. Yeni coğrafi rasterlar tekrar 2D'ye yerleştirilirken AOI dışı NoData,
geçerli sıfır senaryo-ortaklığı değerinden ayrı tutulacaktır.
