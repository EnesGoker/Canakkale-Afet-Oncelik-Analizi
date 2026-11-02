[English](README.md) | [Türkçe](README.tr.md)

# Çanakkale Çok Kriterli Afet Duyarlılığı ve Mekânsal Öncelik Analizi

Çanakkale ili için afet duyarlılığı, nüfus ve yapı maruziyeti ile erişim
koşullarını **11 kriterli çok kriterli karar analizi (MCDA)** ile birleştiren
bir CBS projesi. **100 m ortak gridde** göreli öncelik alanları üretir;
12 ilçe için sonuçları ve üç ağırlık senaryosunu karşılaştırır.

**Proje sahibi: Enes Göker.** Coğrafi Bilgi Sistemleri dersi kapsamında
hazırlanan çalışma; QGIS haritaları, Python/Bash analiz araçları, hesaplama
kontrolleri ve yöntem belgeleriyle bir öğrenci portföyü olarak sunulur.

**Kamu kaynak sürümü:** analiz ve QA kodu, model tanımları, yöntem belgeleri,
özet sonuç tabloları ve QGIS proje şablonu. Canonical veriler, harita
görselleri, atlas ve Word/PDF raporu tam yerel çalışma sürümünde korunur;
bu sürüme dahil değildir.
[Dosyalar ve paylaşım kapsamı](docs/publication_file_scope.md).

Bu eğitim amaçlı ön değerlendirme, resmî afet riski, hasar tahmini veya sınır
ürünü değildir.

## Öne çıkan bulgular

- **415,05 km²**, üç senaryoda da yüksek veya çok yüksek önceliklidir.
  Bu, analiz çalışma alanının (AOI) **%4,23'üdür**.
- **820,96 km²**, yalnız bir veya iki senaryoda yüksek önceliklidir;
  bu alanların yüksek sınıfa üyeliği seçilen senaryoya göre değişir.
- Arazi örtüsü ve ağaç örtüsü **kriter skorları** arasındaki Pearson
  korelasyonu **r = 0,8152**'dir; iki göstergenin ortak bilgi taşıdığını
  tartışmak için sayısal bir bulgudur.

İlk iki bulguda “yüksek”, **4. ve 5. sınıfları** birlikte ifade eder.
Senaryoların karşılaştırılması ağırlık değişimiyle senaryoya özgü
normalizasyonun birleşik etkisini içerir. Bu sayılar afet olasılığı veya
model doğruluk oranı değildir.
[Senaryo ortaklığı](docs/analysis/scenario_agreement.md) ·
[Korelasyon yorumu](docs/analysis/criterion_correlation.md).

## Projeyi inceleyin

Aşağıdaki tablo ve yöntem belgelerini incelemek için QGIS veya Python
kurulumu gerekmez. Ayrıntılı belgeler Türkçedir; bu README'nin
[İngilizce sürümü](README.md) de bulunur.

| İçerik | Bağlantı |
|---|---|
| İlçe ve sınıf alanı özetleri | [Tablolar](outputs/tables/) |
| Ağırlık duyarlılığı | [Senaryo özeti](outputs/tables/mcda_sensitivity_scenario_summary.md) · [Yorum](outputs/tables/mcda_sensitivity_interpretation.md) |
| 11 kriterin korelasyonu | [Yöntem ve yorum](docs/analysis/criterion_correlation.md) · [11 × 11 CSV](outputs/tables/criterion_correlation_v1/criterion_pearson_correlation.csv) |
| Üç senaryonun mekânsal ortaklığı | [Yöntem ve yorum](docs/analysis/scenario_agreement.md) · [Alan sayıları](outputs/analysis/scenario_agreement_v1/agreement_count_summary.csv) · [Senaryo karşılaştırması](outputs/analysis/scenario_agreement_v1/scenario_high_area_comparison.csv) |
| QGIS proje şablonu | [QGZ](qgis/canakkale_disaster_priority.qgz) — canonical analiz verileri ayrıca sağlanmalıdır |
| Veri kaynakları ve paylaşım | [Kaynak envanteri](docs/data_source_inventory.md) · [Dosya kapsamı](docs/publication_file_scope.md) |

Tam yerel çalışma sürümünde 13 coğrafi harita, bir korelasyon figürü,
13 sayfalık atlas, incelenmiş Word raporu ve onun 18 sayfalık PDF kopyası bulunur. Bu
kaynak sürümünde indirilebilir dosya olarak sunulmazlar. Daha sonraki statik
harita paylaşımı için [kaynak bildirimleri ve atıf koşulları](docs/static_map_attributions.md) geçerlidir.

Kaynak paketi Python standart kütüphanesiyle kontrol edilebilir:

```bash
python3 scripts/python/build_public_source_release.py --check
```

Bu komut seçilmiş kaynak dosyalarını doğrular; CBS analizini çalıştırmaz.
Aşağıdaki veriye bağımlı komutlar tam canonical veri klasörünü gerektirir.
Veri olmadan çalışanlar [Testler ve sürekli entegrasyon](#testler-ve-sürekli-entegrasyon)
bölümündedir.

## Kişisel katkım

- Farklı kurumlardan ve açık veri kaynaklarından gelen CBS katmanlarını
  bir araya getirip analiz için hazırladım.
- On bir kriteri ortak 100 m gridde birleştiren MCDA modelini kurdum;
  skor dönüşümlerini, ağırlıkların gerekçelerini ve yöntemin sınırlılıklarını
  belgeledim.
- QGIS katmanlarını ve harita düzenlerini hazırladım; sonuçları ilçe
  tabloları, harita atlası ve ders raporuyla sundum.

## Teknik kazanımlar

- **Veri uyumu:** Farklı çözünürlük ve koordinat sistemlerindeki katmanları
  karşılaştırırken ortak CRS, grid ve AOI kullanmayı; NoData ile sıfır skoru
  sonuç yorumunda ayırmayı öğrendim.
- **Model yorumu:** Ağırlık ve normalizasyon tercihlerinin öncelik sınıflarına
  etkisini senaryo karşılaştırmalarıyla inceledim. Korelasyonla ortak bilgi
  taşıyan kriterleri değerlendirmeyi öğrendim.
- **Taşınabilir QGIS projesi:** Göreli yolları ve katman/stil yönetimini
  birlikte kullanarak projenin farklı bir klasörde açılmasını ve harita
  düzenlerinin tutarlılığını ele aldım.
- **Hesap kontrolü:** Eksik dosya, yanlış CRS/grid, NaN ve aralık dışı skor
  örnekleriyle test yaparak hatalı girdileri yakalamayı; skor ve sınıf
  hesaplarını kayıtlı çıktılarla karşılaştırmayı öğrendim.
- **İzlenebilirlik ve paylaşım:** Girdi/çıktı sürümlerini manifest ve SHA-256
  ile takip etmeyi, kaynak atfını, kod lisansını ve veri paylaşım koşullarını
  ayrı belgelemeyi öğrendim.

## Analiz nasıl çalışır?

1. İşlenmiş kriter katmanları ortak CRS, grid ve çalışma alanında birleştirilir.
2. Her kriter, belgelenmiş dönüşümlerle analiz skoruna çevrilir.
3. Skorlar, kayıtlı ağırlıklarla doğrusal olarak birleştirilir; normalize
   öncelik skoru beş göreli sınıfta gösterilir.
4. `baseline`, `earthquake-heavy` ve `equal-weight` senaryoları karşılaştırılır.
5. Pearson korelasyonu, kriter skorlarının birlikte değişimini;
   mekânsal ortaklık analizi, yüksek alanların senaryolar arasındaki
   ortaklığını ve değişimini gösterir.
6. QA, hesapları mevcut çıktılarla karşılaştırır; ilçe özetleri, haritalar
   ve rapor sonuçların incelenmesini sağlar.

| Bileşen | İçerik |
|---|---|
| Çalışma alanı | Çanakkale ili ve 12 ilçe |
| CRS | EPSG:32635 — WGS 84 / UTM Zone 35N |
| Grid | 100 m; 1586 × 1423 hücrelik raster; AOI içinde 981.033 hücre |
| Analiz AOI alanı | 9.810,33 km²; raster hücre alanından hesaplanır |
| Kriterler | PGA, fay yakınlığı, VS30, nüfus, yapı yoğunluğu, taşkın, hidrografya, eğim, arazi örtüsü, ağaç örtüsü, yol erişimi |
| Ana model | Ağırlıklı doğrusal birleşim; beş göreli öncelik sınıfı |
| Araçlar | QGIS, GDAL/OGR, Python, Bash |

**Yöntem kaynakları:**
[Ağırlıklar](config/mcda_weights.tsv) ·
[Yöntem ve ağırlık gerekçeleri](docs/methodology/updated_mcda_methodology_note.md) ·
[Kriter dönüşümleri](docs/methodology/criterion_transformations.md) ·
[Normalizasyon ve girdi sürümü](docs/methodology/normalization_and_baseline.md) ·
[Veri kaynakları](docs/data_source_inventory.md) ·
[Duyarlılık yorumu](outputs/tables/mcda_sensitivity_interpretation.md).

Yeniden üretilebilirlik, **işlenmiş kanonik analiz verilerinden** başlar.
Büyük kaynak ham veri paketlerinden bütün hazırlama zincirini yeniden kurma
kapsamı dışındadır. Kamu raporunun düzenlenebilir ana kaynağı Word (`.docx`) dosyasıdır.
Ayrı akademik DOCX üreticisi bu raporun elle düzenlenmiş içeriğini yeniden üretmez.
[Kanonik veri politikası](docs/canonical_data_policy.md) ·
[Rapor üretim kapsamı](docs/report_build_outputs.md).

## Klasör yapısı

```text
config/          Ağırlıklar, model ve sabit girdi sürümü
.github/         Sürekli entegrasyon: birim testleri ve kamu kapsamı kontrolleri
scripts/         Python ve Bash analiz, QA ve paketleme araçları
qgis/            QGIS projesi ve harita düzenleri
data/            Yerel analiz verileri; büyük veriler Git dışında
docs/            Yöntem, veri kaynakları, kurulum ve QA belgeleri
outputs/         Seçilmiş özet tablolar ve üretim kayıtları; tam görseller yerelde
```

## QGIS'te açma ve veri erişimi

**Tam verili kamu Release paketi henüz yayımlanmamıştır.**
Kaynak deposu, `Code → Download ZIP`, otomatik `Source code (zip)` ve
`git clone`, büyük analiz verilerini içermez. QGIS dosyasını indirmek,
katmanlarıyla açılabilir tam projeyi indirmek anlamına gelmez.
[Yayın kapsamı ve açık veri paylaşımı kararları](PUBLICATION_STATUS.md).

Tam kanonik veri klasörüne sahip olanlar için, veya paylaşım koşulları
tamamlanıp `canakkale-disaster-priority-portable.zip` yayımlandığında:

1. Tam ZIP'i bir klasöre tamamen çıkarın.
2. `canakkale-disaster-priority/` içinde `qgis/`, `data/` ve `outputs/`
   klasörlerini birlikte tutun.
3. QGIS ile `qgis/canakkale_disaster_priority.qgz` dosyasını açın.

QGIS **3.44.10**, projenin kayıt ve uyumluluk referansıdır. Diğer sürümlerdeki
görünüm ayrıca kontrol edilmelidir. Katman yolları `../data/processed/...`
biçiminde görelidir; QGIS dosyasını tek başına taşımayın.
QGIS'te açmak için Python sanal ortamı gerekmez.

Tam veri klasörünün kökünden, Python 3.10+ ile dosya ve yol kontrolü:

```bash
python3 scripts/python/check_portability.py --check
```

Manifest içeren tam portable pakette ayrıca:

```bash
python3 scripts/python/check_portability.py --check --verify-manifest
```

Bu araç ek Python paketi veya QGIS gerektirmez. Windows'ta `python3` yerine
`py -3` kullanılır. Eksik verili kaynak kopyada kontrolün eksik dosyaları
bildirmesi beklenir; bu, tam veri paketinin yerine geçmez.
[Taşınabilirlik](docs/qgis_project_portability.md) ·
[İndirme ve paket rehberi](docs/github_distribution.md).

Canlı CARTO çevre haritasını QGIS'te açmak için kendi anahtarınızı proje
dışında özel dosyada tutup başlatıcıyı kullanın:

```bash
python3 scripts/python/open_qgis_with_carto.py --key-file "$HOME/.config/canakkale-disaster-priority/carto_basemap.key"
```

[Canlı altlık kurulumu](docs/carto_live_access.md). Hazır harita/PDF dosyaları
anahtar istemez; projeye doğrudan çift tıklamak kişisel anahtarı yüklemez.

## Analiz ortamı ve temel QA

Python **3.10+**, Bash ve GDAL/OGR **3.7+**, analiz/QA araçlarının temel
ortamıdır. Gerçek QGIS okuması için **PyQGIS**, raster ve hesap kontrolleri
için **GDAL Python (`osgeo`) ve NumPy** gerekir.

Tam QA; ayrı **GDAL 3.12.3 / NumPy 2.4.4 (Accelerate)** analiz ortamı ve
**QGIS 3.44.15** proje okuyucusuyla doğrulandı. GDAL 3.13.3'ün varsayılan
yeniden örneklemesi eski eğim/taşkın reçeteleriyle farklıdır; ana MCDA aynı kalır.
[Çalışma ortamı ve uyumluluk kapsamı](docs/qa/runtime_compatibility.md).

Python bağımlılıklarını kurmak için:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

`requirements.txt`, GDAL veya QGIS'i kurmaz; bunlar uyumlu GIS kurulumundan
sağlanır. Matplotlib yalnız analiz figürü/haritası üretiminde gerekir;
hazır figürlerin bütünlük kontrolünde gerekmez. Windows'ta Bash scriptleri
için ayrıca uygun bir Bash ortamı ve buradan erişilebilen GIS araçları gerekir.

macOS arm64'te kayıtlı ortam kurulduktan sonra tek giriş:

```bash
python3 scripts/python/run_compatible_qa.py --gdal-prefix "$GIS_QA_PREFIX" --numpy-overlay "$GIS_QA_NUMPY"
```

[Ortam kurulumu ve sabit profiller](docs/qa/runtime_compatibility.md).
Uyumlu GIS araçları zaten seçilmişse tam veri klasörünün kökünden temel QA:

```bash
bash scripts/bash/run_canonical_qa.sh --check
```

QA; 11 kriterin CRS/grid/AOI uyumunu ve skorlarını kontrol eder, baseline
ham/normalize skorunu ve sınıfları bellekte yeniden hesaplar. Sekiz
kaynak→skor eşdeğer reçetesini, 27 dosyalık sabit girdi sürümünü,
korelasyonu ve senaryo ortaklığını karşılaştırır. Rapor ve duyarlılık
tabloları canonical veriden geçici bir sandbox'ta yeniden üretilir ve
`outputs/tables/` altındaki 7 ve 11 kayıtlı dosyayla bayt bayt
karşılaştırılır; değişmiş, eksik veya fazla dosya kontrolü düşürür. İki tablo
manifestine yazılan üretim zamanı, kayıtlı manifestin tek
`Üretim zamanı (UTC)` satırından kopyalanır; bu değer doğrulanmaz, yeniden
üretilir: değiştirilmiş bir zaman değeri de kontrolden geçer.
QGIS kontrolü; 13 düzenin katman/stil kilitlerini, lejant bağlantılarını,
QGS/QGZ eşliğini ve 27 harita/atlas dosyasının checksum'ını denetler.
Bunlar teknik tutarlılık kontrolleridir; gözlenmiş afetlerle doğrulama değildir.

Çıkış kodları: **0** zorunlu kontroller geçti; **1** kontrol başarısız;
**2** eksik bağımlılık nedeniyle kontrol tamamlanamadı. Canlı taban haritası
erişimi çevrimdışı QA kapsamında denenmez. Kayıtlı arazi örtüsü sınır
bulgusu uyarı olarak gösterilir.

<details>
<summary>GIS araçları, ek kontrol komutları ve üretim kapsamı</summary>

GDAL komutları `PATH`, `GDAL_BIN`, `QGIS_BIN` veya araçlara özgü ortam
değişkenleri üzerinden sağlanır. `gdal_calc.py` ve `gdal_proximity.py` için
uyumlu Python bağımlılıkları gerekir. QA ayrıca `unzip`, `xmllint`, `perl`
ve standart shell araçlarını kullanır.

QA, GIS Python bağımlılıklarını `QGIS_BIN` içindeki Python'da veya uygun
ortamda arar. Gerekirse `QGIS_PYTHON_BIN` ve `GDAL_PYTHON_BIN` ile ayrı
yorumlayıcılar seçilir. `PYTHON_BIN`, tablo/rapor araçları ile QA başlatıcısı
için kullanılır.

Tablo kontrolü tek başına da çalıştırılabilir; ana QA bunu zaten içerir:

```bash
bash scripts/bash/generate_report_tables.sh --check
```

Ayrı DOCX üreticisinin kontrolü aşağıdadır. Bu komut geçici DOCX üretir;
son kamu Word/PDF raporunu doğrulamaz:

```bash
bash scripts/bash/build_academic_report.sh --check
```

DOCX, `build_academic_report.sh --build` ile üretilebilen ayrı bir hedeftir.
Pages arşivleri ve ayrı üretilen akademik DOCX, kamu dağıtımına alınmaz.

Yerel tam veri paketinin teknik kontrolü ve üretimi:

```bash
python3 scripts/python/build_portable_release.py --check
python3 scripts/python/build_portable_release.py --build
```

ZIP ve SHA-256 dosyası `outputs/temp/releases/` altında üretilir; bu klasör
Git dışında tutulur. Teknik paket üretimi kamuya yükleme veya veri paylaşımı
onayı değildir. [Dağıtım rehberi](docs/github_distribution.md), nihai kamu
paketinin kapsamını ve kontrollerini açıklar.

[QA kapsamı](docs/qa/canonical_integrity_checks.md) ·
[Script rehberi](docs/script_kullanim_ve_guvenlik_rehberi.md).

</details>

## Testler ve sürekli entegrasyon

`scripts/python/` altındaki birim testleri küçük geçici fikstürler kurar;
hiçbiri canonical veriyi okumaz. [`config/test_tiers_v1.json`](config/test_tiers_v1.json)
her test modülünü bir çalışma katmanına atar ve test sayısını kaydeder;
aşağıdaki sayıların tek kaynağıdır.

| Katman | Test | Modül | Gereksinim | CI'da |
|---|---:|---:|---|---|
| `stdlib` | 143 | 12 | Python 3.10+ standart kütüphanesi | Ubuntu 24.04 ve macOS arm64; Python 3.10, 3.12, 3.14 |
| `scientific` | 54 | 3 | `requirements.txt` ile NumPy, Matplotlib ve Pillow | Ubuntu 24.04 ve macOS arm64; Python 3.12, kilitli sürümler |
| `gdal` | 111 | 4 | GDAL Python (`osgeo`) ve `scientific` katmanı | Yalnız macOS arm64; kilitli ortam (GDAL 3.12.3, NumPy 2.4.4 Accelerate) |
| `qgis` | 17 | 1 | PyQGIS 3.44 | Çalıştırılmaz |
| **Toplam** | **325** | **20** | | |

Bir katmanın içe aktarımları yoksa testleri tek tek, katmanı adlandıran bir
gerekçeyle atlanır. Atlama hiçbir zaman geçti sayılmaz: `run_tests.py` her
modülü ayrı süreçte koşar ve geçen/atlanan sayıları tabloyla karşılaştırır.
Adı verilen bir katman içe aktarılamıyorsa ya da adı verilmeyen bir katman
içe aktarılabiliyorsa test koşmaz ve 2 koduyla çıkar.

Yeni bir klonda veya kaynak ZIP'inde Python standart kütüphanesi şunlara yeter:

```bash
python3 scripts/python/tier_support.py --check
python3 scripts/python/run_tests.py --tiers stdlib
python3 scripts/python/check_public_scope.py
```

Her biri 0 koduyla çıkar ve şu satırla biter:

- `Test tier table: PASSED; 20 modules, 325 tests (stdlib 143, scientific 54, gdal 111, qgis 17).`
- `Unit tests (stdlib): PASSED; 143 passed, 182 skipped with a tier reason, 0 other outcomes, 325 tests in the table.`
- `Public-source scope: PASSED`. Bu satırdan önce `analysis_baseline.py`
  için `11 verified, 16 skipped` (sürümün dağıtmadığı 16 sabit veri dosyası),
  `check_portability.py` için `28 layers skipped` (dağıtılmayan yerel QGIS
  katmanları) bildirilir. İki atlama listesi de
  [`config/public_scope_expected_v1.json`](config/public_scope_expected_v1.json)
  ile kayıt kayıt aynı olmalıdır.

`python3 -m unittest discover -s scripts/python`, bilimsel paketleri olmayan
bir Python'da `OK (skipped=182)` ile biter; bazı testler sınadıkları
komutların mesajlarını yazdırır. `--scope public-source` olmadan
`analysis_baseline.py --check` ve `check_portability.py --check` kaynak
kopyada canonical veri bulunmadığı için 1 koduyla çıkar; bu beklenen
durumdur.

`requirements.txt` kurulduktan sonra `--tiers stdlib,scientific` kullanılır
(197 geçer, 128 atlanır). macOS arm64'te kilitli GDAL ortamı
`config/qa_runtime_macos_arm64/` dosyalarından proje dışında kurulup ilk üç
katman için kullanılabilir (308 geçer, 17 atlanır):

```bash
bash scripts/bash/setup_locked_gis_runtime.sh install "$HOME/.local/share/canakkale-qa/test-runtime"
bash scripts/bash/setup_locked_gis_runtime.sh run "$HOME/.local/share/canakkale-qa/test-runtime" python -B scripts/python/run_tests.py --tiers stdlib,scientific,gdal
```

[`.github/workflows/tests.yml`](.github/workflows/tests.yml) her push ve
pull request'te çalışır:

- `stdlib` katmanı, katman tablosu kontrolü, `check_public_scope.py` ve
  `build_public_source_release.py --check`; Ubuntu 24.04 ve macOS arm64'te,
  Python 3.10, 3.12 ve 3.14 ile;
- `scientific` katmanı, Python 3.12 ve
  [`config/ci/scientific_constraints.txt`](config/ci/scientific_constraints.txt)
  sürümleriyle; ayrıca Python 3.14'te `requirements.txt`'nin izin verdiği en
  yeni sürümlerle bir canary işi; canary başarısız olsa da iş akışı düşmez;
- `gdal` katmanı, macOS arm64'te yukarıdaki kilitli ortamda; ortam önbelleği
  kilit dosyalarının hash'iyle anahtarlanır.

CI, 17 `qgis` testini (barındırılan hiçbir runner PyQGIS 3.44 sağlamaz),
Linux'ta `gdal` katmanını (bunun için kilit dosyası yok) ve canonical veri
isteyen hiçbir QA komutunu **çalıştırmaz**: `run_canonical_qa.sh`,
`run_compatible_qa.py`, tam kapsamlı `analysis_baseline.py` ve
`check_portability.py`, tablo `--check` komutları. Başarılı bir CI koşusu bu
kontrolleri kapsamaz.

## Sonuçları yorumlarken

- Ağırlıklar gerekçelendirilmiş eğitim amaçlı tercihlerdir; AHP, resmî uzman
  anketi veya gözlenmiş kayıplarla kalibrasyon sonucu değildir.
- Alternatif senaryolar kendi gözlenen min/max ölçeğini kullanır. Sınıf
  değişimleri ağırlıklar ile yeniden ölçeklemenin birleşik etkisidir.
- Kaynak NoData'nın sıfır skora dönüştüğü hücreler bulunur. Sıfır skor veya
  üç senaryoda da yüksek sınıfa girmemek, ölçülmüş tehlike yokluğu anlamına gelmez.
- Korelasyon, dönüştürülmüş kriter skorlarını karşılaştırır; nedensellik,
  ağırlıkların optimumluğu veya model doğruluğu kanıtı değildir.
- Dış fay kaynağı ve bazı tarihsel dönüşüm parametreleri için izlenebilirlik
  sınırları vardır. Yerel veri sürümü bilinmeyen kaynaklarda bu belirsizlik
  ayrıca kaydedilir.

[Yöntem ve bilimsel sınırlılıklar](docs/methodology/scientific_limits.md).

## Taban haritası ve yeniden dışa aktarma

Tam canonical veri klasörüyle hazır harita/atlasları incelemek ve çevrimdışı
QA yapmak için erişim anahtarı veya internet gerekmez. QGIS'te web taban haritasını yeniden yüklemek internet,
CARTO altlığını yeniden çizmek ise kendi erişim anahtarınızı gerektirir.

Dışa aktarma anahtarı `CARTO_BASEMAPS_API_KEY` üzerinden, canlı QGIS erişimi
yukarıdaki özel anahtar dosyası üzerinden alır. Kamu QGIS dosyaları anahtar
içermez. Yeniden dışa aktarma QGIS Python ortamı ve ayrı, boş çıktı klasörü kullanır.
[Harita üretim rehberi](docs/map_atlas_plan.md) ·
[Özel dosyadan anahtar okuma ve üretim](docs/qa/map_export_qa.md).

## Lisans ve kaynaklar

Özgün `scripts/` yazılımı [MIT lisanslıdır](LICENSE).
Rapor, belgeler, haritalar, model tanımları ve veriler için
[ayrı lisans kapsamı](LICENSE_SCOPE.md) geçerlidir; tamamı MIT değildir.
Veri atfı, yeniden dağıtım izniyle aynı şey değildir.

[Kaynak envanteri](docs/data_source_inventory.md) ·
[Veri hakları ve dağıtım kaydı](docs/data_rights_and_distribution.md) ·
[Yayın dosyası listesi](PUBLICATION_STATUS.md) ·
[Harita atıfları](outputs/maps/README.md) ·
[Atlas açıklaması](outputs/atlas/README.md).
