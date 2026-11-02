# Rapor Tablo Çıktıları

**Kaynak sürümü kapsamı:** Aşağıdaki harita, raster, atlas ve Word/PDF
yolları tam yerel çalışma çıktısıdır; bu dosyalar kaynak ve analitik özet
sürümünde dağıtılmaz. Yerel üretim/kontrol komutları ilgili kanonik veri ve
çıktıların ayrıca bulunmasını gerektirir. [Kamu dosya kapsamı](publication_file_scope.md).

Proje: Çanakkale çok kriterli afet öncelik alanları analizi

Bu doküman, canonical rapor tablosu üretimini açıklar.

## 1. Script

Giriş noktası:

```text
scripts/bash/generate_report_tables.sh
```

Modlar:

```text
--check
--generate
```

`--check`, tabloları geçici bir sandbox'ta göreli `outputs/tables` hedefiyle
yeniden üretir; üretici satır sayılarını, ilçe kapsamını, sınıf toplamlarını ve
ortak raster grid varsayımlarını doğrular. Ardından
[`check_table_reproduction.py`](../scripts/python/check_table_reproduction.py)
üretilen yedi dosyayı `outputs/tables/` altındaki kayıtlı dosyalarla bayt bayt
karşılaştırır. Manifestteki üretim zamanı, kayıtlı manifestin tek
`Üretim zamanı (UTC)` satırından okunur; satır yoksa, birden fazlaysa veya
biçimi bozuksa kontrol başarısız olur. Bu satırın değeri başka bir kayıtla
doğrulanmaz. Eksik veya fazla dosya da başarısızlıktır; proje dosyalarına
yazılmaz.

`--generate`, rapora hazır çıktıları şu konuma yazar:

```text
outputs/tables/
```

Bash entry point, proje kökünü kendi konumundan çözer ve GDAL/OGR araçlarını
portable script standardı üzerinden runtime'da bulur.

## 2. Canonical Girdiler

Tablo generator yalnızca canonical proje katmanlarını kullanır:

| Girdi | Path |
|---|---|
| MCDA class raster | `data/processed/analysis/mcda_priority_class_32635.tif` |
| İlçe vektörü | `data/processed/admin/canakkale_districts_32635.gpkg` |
| Kriter ve MCDA rasterları | `data/processed/analysis/*_32635.tif` |

Büyük upstream ham dosyalar gerekli değildir.

## 3. Üretilen Dosyalar

| Çıktı | Amaç |
|---|---|
| `outputs/tables/mcda_class_distribution.csv` | MCDA sınıf piksel sayıları, alan ve il geneli payı |
| `outputs/tables/mcda_class_distribution.md` | Rapor metni için Markdown versiyonu |
| `outputs/tables/mcda_class_area_by_district.csv` | 12 ilçe x 5 MCDA sınıf alan tablosu |
| `outputs/tables/mcda_class_area_by_district.md` | Rapor metni için Markdown versiyonu |
| `outputs/tables/criterion_raster_statistics.csv` | Min, max, mean, standard deviation, NoData ve valid-percent istatistikleri |
| `outputs/tables/criterion_raster_statistics.md` | Rapor metni için Markdown versiyonu |
| `outputs/tables/report_tables_manifest.md` | Çıktı manifesti ve QA özeti |

Alan değerleri canonical 100 m grid üzerinden hesaplanır; bu nedenle bir geçerli
piksel 0.01 km2'ye eşittir.

## 4. QA Sözleşmesi

Generator, aşağıdaki koşullardan herhangi biri sağlanmazsa başarısız olur:

| Kontrol | Kabul kriteri |
|---|---|
| MCDA sınıf dağılımı | Sınıf 1-5 için tam 5 satır |
| İlçe-sınıf tablosu | Tam 60 satır: 12 ilçe x 5 sınıf |
| İlçe kapsamı | Tüm geçerli MCDA class piksellerinin district id değeri olmalı |
| Sınıf toplamları | İlçe sınıf toplamları global sınıf toplamlarına eşit olmalı |
| Raster istatistikleri | 11 kriter rasterı ve 3 MCDA rasterı |
| Ortak grid | Tüm istatistik rasterları MCDA class raster grid ile eşleşmeli |

Ortak grid sözleşmesi:

```text
EPSG:32635
100 m
1586 x 1423
same extent as the MCDA class raster
```

## 5. Üretim Özeti

Üretilen çıktılar şu kontrollerden geçer:

| Öğe | Sonuç |
|---|---:|
| MCDA sınıf satırları | 5 |
| İlçe-sınıf satırları | 60 |
| Raster istatistik satırları | 14 |
| Geçerli MCDA class pikselleri | 981033 |
| Geçerli MCDA class alanı km2 | 9810.33 |
| District id değeri olmayan class pikselleri | 0 |

MCDA sınıf dağılımı:

| Sınıf | Piksel | Alan km2 | Pay yüzde |
|---|---:|---:|---:|
| 1 | 114283 | 1142.83 | 11.6493 |
| 2 | 483129 | 4831.29 | 49.2470 |
| 3 | 329029 | 3290.29 | 33.5390 |
| 4 | 53893 | 538.93 | 5.4935 |
| 5 | 699 | 6.99 | 0.0713 |

## 6. Kapsam

Tablo üretimi yalnızca tablosal rapor girdileri üretir. MCDA rasterlarını
yeniden build etmez, QGIS projelerini düzenlemez, ham kaynak veri çekmez ve
nihai DOCX raporunu üretmez.

## 7. Sensitivity / Robustness Tabloları

Küçük ağırlık duyarlılığı kontrolü için ayrı bir güvenli tablo generator
eklenmiştir:

```text
scripts/bash/generate_sensitivity_tables.sh
```

Modlar:

```text
--check
--generate
```

`--check`, rapor tablolarıyla aynı yöntemle on bir dosyayı yeniden üretir ve
`outputs/tables/` altındaki kayıtlı dosyalarla bayt bayt karşılaştırır.

Bu script `config/mcda_weights.tsv` içindeki üç senaryoyu kullanır:

| Senaryo | Rol |
|---|---|
| `baseline` | Canonical MCDA class rasterı için referans senaryo |
| `earthquake-heavy` | Deprem ilişkili kriterlerin etkisini artıran robustness senaryosu |
| `equal-weight` | Tüm kriterleri eşit kabul eden robustness senaryosu |

Kalıcı senaryo rasterı üretilmez. Alternatif senaryo skorları geçici array
hesaplarıyla oluşturulur ve yalnızca tablo çıktısı yazılır.

Üretilen dosyalar:

| Çıktı | Amaç |
|---|---|
| `outputs/tables/mcda_sensitivity_scenario_summary.csv` | Senaryo özeti, yüksek+çok yüksek alan değişimi ve baseline agreement ölçüleri |
| `outputs/tables/mcda_sensitivity_scenario_summary.md` | Markdown versiyonu |
| `outputs/tables/mcda_sensitivity_interpretation.csv` | Senaryo sonuçlarından otomatik üretilen kısa rapor yorumları |
| `outputs/tables/mcda_sensitivity_interpretation.md` | Markdown versiyonu |
| `outputs/tables/mcda_sensitivity_class_distribution.csv` | Senaryo x MCDA sınıf dağılımı |
| `outputs/tables/mcda_sensitivity_class_distribution.md` | Markdown versiyonu |
| `outputs/tables/mcda_sensitivity_top_districts.csv` | Her senaryoda yüksek+çok yüksek alana göre ilk beş ilçe |
| `outputs/tables/mcda_sensitivity_top_districts.md` | Markdown versiyonu |
| `outputs/tables/mcda_sensitivity_class_transition.csv` | Baseline class değerlerinden senaryo class değerlerine geçiş matrisi |
| `outputs/tables/mcda_sensitivity_class_transition.md` | Markdown versiyonu |
| `outputs/tables/mcda_sensitivity_manifest.md` | Çıktı manifesti, QA özeti ve kısa okuma |

Sensitivity QA sözleşmesi:

| Öğe | Sonuç |
|---|---:|
| Senaryo sayısı | 3 |
| Kısa yorum satırları | 3 |
| Class dağılım satırları | 15 |
| Top district satırları | 15 |
| Class transition satırları | 75 |

Senaryo özeti:

| Senaryo | Yüksek+çok yüksek alan km2 | Baseline'a göre değişim km2 | Class agreement |
|---|---:|---:|---:|
| `baseline` | 545.92 | 0.00 | 100.00% |
| `earthquake-heavy` | 818.70 | 272.78 | 84.08% |
| `equal-weight` | 927.09 | 381.17 | 72.59% |

## 8. Kriter Korelasyonu

Mevcut sekiz referans CSV korunur. Ek analiz, ayrı
`outputs/tables/criterion_correlation_v1/` dizininde üç dosya üretir:

| Çıktı | Amaç |
|---|---|
| [criterion_pearson_correlation.csv](../outputs/tables/criterion_correlation_v1/criterion_pearson_correlation.csv) | Canonical sırayla 11 × 11 Pearson matrisi; katsayılar 17 anlamlı basamakla saklanır. |
| [criterion_correlation_statistics.csv](../outputs/tables/criterion_correlation_v1/criterion_correlation_statistics.csv) | 11 kriter için AOI/sonlu/NoData/sıfır sayıları, sıfır payı, min/max/ortalama ve popülasyon standart sapması. |
| [criterion_correlation_manifest.json](../outputs/tables/criterion_correlation_v1/criterion_correlation_manifest.json) | Baseline ve kaynak hash'leri, sayısal politika, yazılım sürümleri ve iki CSV'nin checksum'u. |

Bu tablolar, eski `criterion_raster_statistics.csv` ile aynı kapsam değildir:
korelasyon dağılımları yalnız ortak template AOI'sindeki 981.033 hücreyi içerir.
AOI dışındaki geçerli arazi örtüsü hücreleri buraya alınmaz. Sıfır skorlar
korunur; NoData'nın geçmişte sıfıra çevrilmesi yeni eksik veri yokluğu gibi
yorumlanmaz. [Yöntem/yorum](analysis/criterion_correlation.md) ve
[yeniden üretim](qa/canonical_integrity_checks.md#korelasyon-çıktılarını-yeniden-üretme)
ayrı açıklanır. Türkçe PNG/PDF figürü `outputs/figures/criterion_correlation_v1/`
altındadır; mevcut 13 coğrafi haritanın sayısını değiştirmez. Kamu Word
raporunda bu ayrı figür Şekil 13, QGIS ortaklık haritası Şekil 14'tür.

## 9. Senaryo Mekânsal Ortaklığı

Eski sekiz CSV ve iki korelasyon CSV'si korunur. Yeni mekânsal analiz,
rasterlarıyla birlikte `outputs/analysis/scenario_agreement_v1/` altında
tek sürümlü paket olarak tutulur:

| Çıktı | İçerik |
|---|---|
| [agreement_count_summary.csv](../outputs/analysis/scenario_agreement_v1/agreement_count_summary.csv) | İl geneli ve 12 ilçe × 4 ortaklık sayısı = 52 satır. |
| [agreement_membership_summary.csv](../outputs/analysis/scenario_agreement_v1/agreement_membership_summary.csv) | Aynı 13 kapsam × 8 senaryo üyelik kombinasyonu = 104 satır. |
| [scenario_high_area_comparison.csv](../outputs/analysis/scenario_agreement_v1/scenario_high_area_comparison.csv) | Aynı 13 kapsam × 3 senaryo = 39 satır; yüksek alan, baseline ile korunan/eklenen/çıkan/birleşim, Jaccard ve ayrı örtüşme payları. |
| [scenario_agreement_manifest.json](../outputs/analysis/scenario_agreement_v1/scenario_agreement_manifest.json) | Baseline/politika, ilçe atama yöntemi, altı eski CSV karşılaştırması ve beş çıktı checksum'u. |

İki GeoTIFF aynı pakettedir: `scenario_agreement_count_32635.tif` (`0–3`)
ve `scenario_agreement_membership_32635.tif` (`0–7`). AOI dışı NoData `255`;
geçerli sıfırdan ayrıdır. CSV hücre sayıları tam sayı, alanlar hücre sayısı
× 0,01 km²dir. Yeni ilçe payları kendi grid AOI alanına bölünür; eski
vektör poligon paylarıyla aynı isim veya payda kullanılmaz. Boş paydada
Jaccard/korunma/örtüşme yüzdesi boş bırakılır.

[Sonuç ve yorum](analysis/scenario_agreement.md) ile
[kontrol/yeniden üretim](qa/canonical_integrity_checks.md#senaryo-ortaklığı-ve-harita-kontrolü)
ayrı belgelenmiştir. PNG/PDF haritası `outputs/figures/scenario_agreement_v1/`
altındadır; mevcut QGIS/atlas düzenlemesi bu tablo üreticisinin işi değildir.

Kamu Word raporunun Tablo 6'sı, sayım özetinden il geneli ile Yenice,
Gelibolu ve Çan'ın ortak/değişen yüksek alanlarını ve kendi AOI paylarını
sunar. Sekiz veri tablosu 1–6, A1 ve B1 olarak sıralanır. Sekiz referans CSV,
rapor tablolarının ayrı hesaplama girdileridir.

Düzenlenebilir ana rapor
`outputs/report/canakkale_disaster_priority_public_report.docx`,
okuma kopyası ise 18 sayfalık PDF (`outputs/report/canakkale_disaster_priority_public_report.pdf`)
dosyasıdır. Rapora aktarılan sayısal alanların kaynak karşılaştırmaları,
[rapor manifestindeki](../outputs/report/public_report_manifest.json) güncel
Word/PDF sürümüyle birlikte izlenir; başka bir rapor biçiminin kontrol
sonuçları yeni dosya sürümüne aktarılmaz.
