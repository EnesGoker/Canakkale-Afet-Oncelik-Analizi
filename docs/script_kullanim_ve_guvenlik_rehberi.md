# Script Kullanım ve Güvenlik Rehberi

**Kaynak sürümü kapsamı:** İlk kamu sürümü kod, yöntem belgeleri, QGIS
proje tanımı ve seçilmiş analitik özetleri içerir. Tam kanonik veriler ve
harita/rapor dosyaları dahil değildir. Bu belgedeki tam analiz, katman ve
çıktı kontrolleri ilgili yerel dosyalar ayrıca sağlandığında çalışır; kaynak
kopyasında eksik girdilerin bildirilmesi beklenir. [Dosya kapsamı](publication_file_scope.md).

Proje: Çanakkale çok kriterli afet öncelik alanları analizi

Bu rehber, proje içindeki Bash ve Python scriptlerinin amacını, çalışma modlarını,
girdi/çıktı sözleşmesini ve yazma davranışını açıklar. Scriptler canonical veri
seviyesini esas alır: analiz girdileri `data/processed`, `data/reference`,
korunan küçük raw kaynaklar ve rapora hazır `outputs` varlıklarıdır.

İlgili politika belgeleri:

- `docs/canonical_data_policy.md`
- `docs/data_source_inventory.md`
- `docs/portable_script_standard.md`
- `docs/canonical_qa_runner.md`
- `docs/report_table_outputs.md`
- `docs/report_build_outputs.md`

## 1. Çalıştırma Sınıfları

| Sınıf | Anlam | Yazma davranışı |
|---|---|---|
| Read-only audit | Proje durumunu okur ve terminale özet yazar | Proje dosyası yazmaz |
| Read-only QA | Girdi, grid, CRS, path ve tablo sözleşmelerini doğrular | Geçici dosyaları sistem temp dizininde oluşturabilir |
| Output generator | Rapor tablosu veya DOCX gibi türetilmiş çıktı üretir | Yalnızca belirtilen `outputs/` alt dizinine yazar |
| Controlled rebuild | Canonical analiz çıktısını yeniden üretir | Hedef analiz çıktılarını kontrollü biçimde değiştirir |
| Shared helper | Diğer scriptler tarafından source/import edilir | Tek başına çıktı üretmez |

## 2. Bash Scriptleri

| Script | Sınıf | Modlar | Girdiler | Çıktı / yazma davranışı |
|---|---|---|---|---|
| `scripts/bash/audit_project_tree.sh` | Read-only audit | Yok | Proje klasör yapısı | Terminale proje ağacı, QGIS dosyaları, processed dosyalar, temp/lock dosyaları ve boyut özeti yazar |
| `scripts/bash/run_canonical_qa.sh` | Read-only QA | `--check` | Scriptler, QGIS projesi, `data/interim` VRT kayıtları, canonical analiz katmanları | Proje dosyası yazmaz; geçici QA dosyaları sistem temp dizinindedir |
| `scripts/bash/generate_report_tables.sh` | Output generator | `--check`, `--generate` | MCDA class rasterı, ilçe vektörü, kriter rasterları | `--check` temp dizine yazar; `--generate` `outputs/tables/` altında rapor tabloları üretir |
| `scripts/bash/generate_sensitivity_tables.sh` | Output generator | `--check`, `--generate` | `config/mcda_weights.tsv`, canonical kriter rasterları, ilçe vektörü | `--check` temp dizine yazar; `--generate` `outputs/tables/` altında sensitivity tabloları üretir |
| `scripts/bash/build_academic_report.sh` | Output generator | `--check`, `--build` | Harita PNG'leri, rapor tabloları, metodoloji/kaynak dokümanları | `--check` temp dizine DOCX üretir; `--build` `outputs/report/` altında DOCX rapor üretir |
| `scripts/bash/mcda_pipeline_commands.sh` | Controlled rebuild | `--check`, `--execute` | `config/mcda_weights.tsv`, 11 canonical kriter rasterı, analysis template | `--check` okuma/doğrulama yapar; `--execute` MCDA score, normalized score ve class rasterlarını üretir |
| `scripts/bash/population_processing_pipeline.sh` | Read-only QA | `--check` | Canonical population count ve population exposure score rasterları | Skor formülünü temp dizinde geçici diff rasterı ile kontrol eder |
| `scripts/bash/vs30_processing_pipeline.sh` | Read-only QA | `--check` | Canonical VS30 AOI rasterı ve site condition score rasterı | Skor formülünü temp dizinde geçici diff rasterı ile kontrol eder |
| `scripts/bash/fault_processing_pipeline.sh` | Read-only QA | `--check` | Canonical fault vector ve fault proximity score rasterı | Fault vector/proximity akışını temp dizinde yeniden hesaplayarak kontrol eder |
| `scripts/bash/lib/project_env.sh` | Shared helper | Yok | Bash runtime environment | Proje kökü, tool çözümleme ve GDAL/QGIS environment yardımcılarını sağlar |

## 3. Python Modülleri

| Modül | Bash entry point | Amaç | Çıktı |
|---|---|---|---|
| `scripts/python/generate_report_tables.py` | `scripts/bash/generate_report_tables.sh` | MCDA sınıf dağılımı, ilçe bazlı sınıf alanı ve raster istatistik tablolarını hesaplar | CSV ve Markdown tablolar |
| `scripts/python/generate_sensitivity_tables.py` | `scripts/bash/generate_sensitivity_tables.sh` | Baseline, earthquake-heavy ve equal-weight ağırlık senaryoları için tablo bazlı robustness çıktıları hesaplar | CSV ve Markdown sensitivity tabloları |
| `scripts/python/build_academic_report.py` | `scripts/bash/build_academic_report.sh` | Rapor varlıklarından A4 DOCX akademik raporu üretir | DOCX rapor |
| `scripts/python/generate_correlation_analysis.py` | Doğrudan; kontrolü canonical QA'ya bağlı | Sabit AOI'deki 11 skorun Pearson matrisi ve dağılım istatistikleri | `--check` salt okur; `--generate --output-dir` yeni/boş hedefe iki CSV ve JSON manifest yazar |
| `scripts/python/plot_criterion_correlation.py` | Doğrudan; kontrolü canonical QA'ya bağlı | Kayıtlı matrisi Türkçe figüre dönüştürür ve figür checksum'larını doğrular | `--check` salt okur; `--generate --output-dir` yeni/boş hedefe PNG, PDF ve JSON manifest yazar |
| `scripts/python/generate_scenario_agreement.py` | Doğrudan; kontrolü canonical QA'ya bağlı | Üç senaryonun yüksek sınıf ortaklığı, sekiz üyelik kombinasyonu ve il/ilçe özetleri | `--check` yeniden hesapla karşılaştırır; `--generate --output-dir` yeni/boş hedefe iki GeoTIFF, üç CSV ve JSON manifest yazar |
| `scripts/python/plot_scenario_agreement.py` | Doğrudan; kontrolü canonical QA'ya bağlı | Sayım rasterından Türkçe coğrafi harita; kaynak ve dosya checksum kontrolü | `--check` Matplotlib yüklemeden salt okur; `--generate --output-dir` yeni/boş hedefe PNG/PDF/JSON yazar |

Python modülleri doğrudan çağrılabilir; ancak normal kullanımda Bash entry point
tercih edilir. Bash wrapper'lar proje kökünü, tool pathlerini ve gerekli environment
değişkenlerini tek noktadan yönetir.

Korelasyon modülleri doğrudan çağrılır. Varsayılan kaynak/hedefler
`outputs/tables/criterion_correlation_v1/` ve
`outputs/figures/criterion_correlation_v1/`dir. Kontrol, kaydedilmiş çıktıların
bulunmasını ister; üretim açık hedef seçimi gerektirir ve eski dosyaları
değiştirmez. Ortam ve yeniden üretim örnekleri
[QA sözleşmesinde](qa/canonical_integrity_checks.md#korelasyon-çıktılarını-yeniden-üretme).

Senaryo ortaklığı paketi `outputs/analysis/scenario_agreement_v1/`;
haritası `outputs/figures/scenario_agreement_v1/` altındadır. Raster ve tablolar,
aynı manifestle birlikte altı dosyalık bir paket olarak üretilir; eski
`outputs/tables/` dosyalarına veya canonical rasterlara yazılmaz.
[Kontrol/üretim sözleşmesi](qa/canonical_integrity_checks.md#senaryo-ortaklığı-ve-harita-kontrolü)
bu yeni modüllerin komutlarını ve NoData ayrımını açıklar.

## 4. Önerilen Kullanım Komutları

Genel proje kontrolü:

```bash
scripts/bash/run_canonical_qa.sh --check
```

Rapor tablolarını doğrulama:

```bash
scripts/bash/generate_report_tables.sh --check
scripts/bash/generate_sensitivity_tables.sh --check
```

Rapor tablolarını üretme:

```bash
scripts/bash/generate_report_tables.sh --generate
scripts/bash/generate_sensitivity_tables.sh --generate
```

DOCX raporu doğrulama ve üretme:

```bash
scripts/bash/build_academic_report.sh --check
scripts/bash/build_academic_report.sh --build
```

MCDA rasterlarını kontrol etme:

```bash
scripts/bash/mcda_pipeline_commands.sh --check
```

MCDA rasterlarını yeniden üretme:

```bash
scripts/bash/mcda_pipeline_commands.sh --execute
```

## 5. Yazma Davranışı

| Mod | Yazma kapsamı |
|---|---|
| `--check` | Proje dosyalarını değiştirmez; gerekiyorsa sistem temp dizinine geçici dosya yazar |
| `--generate` | Tablo üreticileri CSV/Markdown; ek analiz modülleri açıkça seçilen yeni/boş hedefe CSV/JSON, GeoTIFF veya PNG/PDF/JSON üretir |
| `--build` | `outputs/report/` altında DOCX rapor üretir |
| `--execute` | `data/processed/analysis/` altında MCDA raster çıktılarını üretir |

`mcda_pipeline_commands.sh --execute`, hedef MCDA çıktılarını üretmeden önce mevcut
MCDA output dosyalarını `data/processed/analysis/archive/` altında zaman damgalı
bir klasöre taşır. Bu mod yalnızca MCDA rasterlarının yeniden üretilmesi
gerektiğinde kullanılmalıdır.

## 6. Runtime ve Tool Çözümleme

Bash scriptleri proje kökünü `scripts/bash/lib/project_env.sh` üzerinden script
konumuna göre belirler. Yerel proje pathi hard-code edilmez.

GDAL, OGR ve QGIS komut satırı araçları şu sırayla çözülebilir:

1. Doğrudan araç environment variable değerleri: `GDALINFO`, `GDAL_CALC`,
   `GDAL_TRANSLATE`, `GDAL_RASTERIZE`, `GDAL_PROXIMITY`, `OGRINFO`, `OGR2OGR`,
   `QGIS_PROCESS`
2. `GDAL_BIN`
3. `QGIS_BIN`
4. `PATH`

Python seçimi için `PYTHON_BIN` kullanılabilir. DOCX raporu için Python runtime
içinde `python-docx` ve `Pillow`, tablo üretimi için `numpy` bulunmalıdır.

Canonical QA'nın gerçek proje ve hesap kontrolleri ayrı GIS Python ortamı
kullanabilir: `QGIS_PYTHON_BIN` PyQGIS'i, `GDAL_PYTHON_BIN` GDAL Python ve
NumPy'ı sağlayan yorumlayıcıyı açıkça seçer. Bu değişkenler yoksa `QGIS_BIN`
altındaki `python`/`python3`, `PYTHON_BIN` ve mevcut Python adayları sınanır.
macOS QGIS paketinin kaynak yolları seçilen paketten türetilir; kişisel proje
yolu koda yazılmaz. Açıkça hatalı bir yorumlayıcı ayarı başka ortama sessizce
geçilerek gizlenmez.

QA çıkışı `0`: zorunlu kontroller geçti; `1`: doğrulama/çalıştırma hatası;
`2`: bağımlılık yokluğundan tamamlanamayan zorunlu kontrol. Web katmanının
çevrimdışı bağlantı kontrolü bu zorunlu yerel kontrollerden ayrı gösterilir.
[Ayrıntılı QA sözleşmesi](qa/canonical_integrity_checks.md), maskeleri,
sayısal toleransları ve geçici bozuk girdi testlerini açıklar.

## 7. Veri Girdi Sözleşmesi

Scriptler büyük upstream ham veri paketlerini build girdisi olarak beklemez:

- Microsoft Global ML Building Footprints ham paketleri
- Geofabrik / OSM ham GeoPackage dosyaları
- Copernicus DEM GLO-30 ham karoları
- ESA WorldCover ham karoları
- Tree Cover Density ham karoları
- JRC/CEMS flood ham raster dosyaları
- HydroRIVERS ulusal/kıtasal ham paketleri
- WorldPop ham nüfus rasterı
- USGS Global VS30 Mosaic ham extract dosyası
- MTA raw shapefile paketi

Analiz ve rapor üretimi mevcut canonical katmanlara dayanır. Kaynak veri bilgisi
dataset, kurum ve bilinen yıl/sürüm düzeyinde `docs/data_source_inventory.md`
içinde tutulur.

## 8. Güvenli Kullanım Sırası

Rapor üretimi için önerilen güvenli sıra:

1. `scripts/bash/run_canonical_qa.sh --check`
2. `scripts/bash/generate_report_tables.sh --check`
3. `scripts/bash/generate_sensitivity_tables.sh --check`
4. `scripts/bash/generate_report_tables.sh --generate`
5. `scripts/bash/generate_sensitivity_tables.sh --generate`
6. `scripts/bash/build_academic_report.sh --check`
7. `scripts/bash/build_academic_report.sh --build`

MCDA rasterları yalnızca model ağırlığı, kriter rasterı veya analysis template
değiştiğinde yeniden üretilmelidir. Normal rapor üretimi için MCDA `--execute`
modu gerekli değildir.
