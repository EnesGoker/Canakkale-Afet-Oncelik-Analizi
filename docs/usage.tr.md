[English](usage.md) | [Türkçe](usage.tr.md)

# Kullanım: QGIS, analiz ortamı, QA ve testler

Bütün komutlar depo kökünden çalıştırılır. [README'ye dön](../README.tr.md) ·
[Belge dizini](README.md).

## Yalnız depodan ne çalışır

Kaynak deposu, `Code → Download ZIP`, otomatik `Source code (zip)` ve
`git clone`, işlenmiş kanonik analiz verilerini içermez; bu veriler için bir
indirme yolu yayımlanmamıştır ([yayın kapsamı](../PUBLICATION_STATUS.md)).
Veriler olmadan şunlar çalışır:

- birim testler ([Testler ve sürekli entegrasyon](#testler-ve-sürekli-entegrasyon));
- `python3 scripts/python/check_public_scope.py` (kamu kapsamı kontrolü);
- `python3 scripts/python/build_public_source_release.py --check` (seçilmiş kaynak dosyaları).

Analizler, tam QA ve QGIS katmanları tam kanonik veri klasörünü gerektirir.
Yeniden üretilebilirlik **işlenmiş kanonik analiz verilerinden** başlar;
hazırlık zincirinin büyük upstream ham verilerden yeniden kurulması proje
kapsamı dışındadır. Word (`.docx`) dosyası yetkili düzenlenebilir rapordur;
ayrı akademik DOCX üreticisi onun elle düzenlenmiş içeriğini yeniden üretmez.
[Canonical veri politikası](canonical_data_policy.md) ·
[Rapor üretim kapsamı](report_build_outputs.md).

## QGIS'te açma ve veri erişimi

**Tam verili kamu Release paketi yayımlanmamıştır.** QGIS dosyasını indirmek,
katmanlarıyla açılabilir projeyi indirmek anlamına gelmez.

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
[Taşınabilirlik](qgis_project_portability.md) ·
[İndirme ve paket rehberi](github_distribution.md).

Canlı CARTO çevre haritasını QGIS'te açmak için kendi anahtarınızı proje
dışında özel dosyada tutup başlatıcıyı kullanın:

```bash
python3 scripts/python/open_qgis_with_carto.py --key-file "$HOME/.config/canakkale-disaster-priority/carto_basemap.key"
```

[Canlı altlık kurulumu](carto_live_access.md). Hazır haritalar anahtar
istemez; projeye doğrudan çift tıklamak kişisel anahtarı yüklemez.

## Analiz ortamı ve temel QA

Python **3.10+**, Bash ve GDAL/OGR **3.7+**, analiz/QA araçlarının temel
ortamıdır. Gerçek QGIS okuması için **PyQGIS**, raster ve hesap kontrolleri
için **GDAL Python (`osgeo`) ve NumPy** gerekir.

Tam QA; ayrı **GDAL 3.12.3 / NumPy 2.4.4 (Accelerate)** analiz ortamı ve
**QGIS 3.44.15** proje okuyucusuyla doğrulandı. GDAL 3.13.3'ün varsayılan
yeniden örneklemesi kayıtlı eğim/taşkın reçetelerinden farklıdır; ana MCDA aynı kalır.
[Çalışma ortamı ve uyumluluk kapsamı](qa/runtime_compatibility.md).

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

[Ortam kurulumu ve sabit profiller](qa/runtime_compatibility.md).
Uyumlu GIS araçları zaten seçilmişse tam veri klasörünün kökünden temel QA:

```bash
bash scripts/bash/run_canonical_qa.sh --check
```

QA; 11 kriterin CRS/grid/AOI uyumunu ve skorlarını kontrol eder, baseline
ham/normalize skorunu ve sınıfları bellekte yeniden hesaplar. Sekiz
kaynak→skor eşdeğer reçetesini, 27 dosyalık sabit girdi sürümünü,
korelasyonu, senaryo ortaklığını, ağırlık pertürbasyonunu ve model
varyantlarını karşılaştırır. Rapor ve duyarlılık tabloları canonical veriden
geçici bir sandbox'ta yeniden üretilir ve `outputs/tables/` altındaki 7 ve 11
kayıtlı dosyayla bayt bayt karşılaştırılır; değişmiş, eksik veya fazla dosya
kontrolü düşürür. İki tablo manifestine yazılan üretim zamanı, kayıtlı
manifestin tek `Üretim zamanı (UTC)` satırından kopyalanır; bu değer
doğrulanmaz, yeniden üretilir: değiştirilmiş bir zaman değeri de kontrolden geçer.
QGIS kontrolü; 14 düzenin katman/stil kilitlerini, lejant bağlantılarını,
QGS/QGZ eşliğini ve 28 harita/atlas dosyasının checksum'ını denetler.
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
onayı değildir. [Dağıtım rehberi](github_distribution.md), nihai kamu
paketinin kapsamını ve kontrollerini açıklar.

[QA kapsamı](qa/canonical_integrity_checks.md) ·
[Script rehberi](script_kullanim_ve_guvenlik_rehberi.md).

</details>

## Testler ve sürekli entegrasyon

`scripts/python/` altındaki birim testleri küçük geçici fikstürler kurar;
hiçbiri canonical veriyi okumaz. [`config/test_tiers_v1.json`](../config/test_tiers_v1.json)
her test modülünü bir çalışma katmanına atar ve test sayısını kaydeder;
aşağıdaki sayıların tek kaynağıdır.

| Katman | Test | Modül | Gereksinim | CI'da |
|---|---:|---:|---|---|
| `stdlib` | 192 | 15 | Python 3.10+ standart kütüphanesi | Ubuntu 24.04 ve macOS arm64; Python 3.10, 3.12, 3.14 |
| `scientific` | 90 | 4 | `requirements.txt` ile NumPy, Matplotlib ve Pillow | Ubuntu 24.04 ve macOS arm64; Python 3.12, kilitli sürümler |
| `gdal` | 166 | 7 | GDAL Python (`osgeo`) ve `scientific` katmanı | Yalnız macOS arm64; kilitli ortam (GDAL 3.12.3, NumPy 2.4.4 Accelerate) |
| `qgis` | 17 | 1 | PyQGIS 3.44 | Çalıştırılmaz |
| **Toplam** | **465** | **27** | | |

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

- `Test tier table: PASSED; 27 modules, 465 tests (stdlib 192, scientific 90, gdal 166, qgis 17).`
- `Unit tests (stdlib): PASSED; 192 passed, 273 skipped with a tier reason, 0 other outcomes, 465 tests in the table.`
- `Public-source scope: PASSED`. Bu satırdan önce `analysis_baseline.py`
  için `11 verified, 16 skipped` (sürümün dağıtmadığı 16 sabit veri dosyası),
  `check_portability.py` için `30 layers skipped` (dağıtılmayan yerel QGIS
  katmanları) bildirilir. İki atlama listesi de
  [`config/public_scope_expected_v1.json`](../config/public_scope_expected_v1.json)
  ile kayıt kayıt aynı olmalıdır.

`python3 -m unittest discover -s scripts/python`, bilimsel paketleri olmayan
bir Python'da `OK (skipped=273)` ile biter; bazı testler sınadıkları
komutların mesajlarını yazdırır. `--scope public-source` olmadan
`analysis_baseline.py --check` ve `check_portability.py --check` kaynak
kopyada canonical veri bulunmadığı için 1 koduyla çıkar; bu beklenen
durumdur.

`requirements.txt` kurulduktan sonra `--tiers stdlib,scientific` kullanılır
(282 geçer, 183 atlanır). macOS arm64'te kilitli GDAL ortamı
`config/qa_runtime_macos_arm64/` dosyalarından proje dışında kurulup ilk üç
katman için kullanılabilir (448 geçer, 17 atlanır):

```bash
bash scripts/bash/setup_locked_gis_runtime.sh install "$HOME/.local/share/canakkale-qa/test-runtime"
bash scripts/bash/setup_locked_gis_runtime.sh run "$HOME/.local/share/canakkale-qa/test-runtime" python -B scripts/python/run_tests.py --tiers stdlib,scientific,gdal
```

[`.github/workflows/tests.yml`](../.github/workflows/tests.yml) her push ve
pull request'te çalışır:

- `stdlib` katmanı, katman tablosu kontrolü, `check_public_scope.py` ve
  `build_public_source_release.py --check`; Ubuntu 24.04 ve macOS arm64'te,
  Python 3.10, 3.12 ve 3.14 ile;
- `scientific` katmanı, Python 3.12 ve
  [`config/ci/scientific_constraints.txt`](../config/ci/scientific_constraints.txt)
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

[Yöntem özeti, bilinen sınırlılıklar](method_summary.md#10-known-limitations) (İngilizce) ·
[Yöntem ve bilimsel sınırlılıklar](methodology/scientific_limits.md).

## Taban haritası ve yeniden dışa aktarma

Tam canonical veri klasörüyle hazır harita/atlasları incelemek ve çevrimdışı
QA yapmak için erişim anahtarı veya internet gerekmez. QGIS'te web taban
haritasını yeniden yüklemek internet, CARTO altlığını yeniden çizmek ise kendi
erişim anahtarınızı gerektirir.

Dışa aktarma anahtarı `CARTO_BASEMAPS_API_KEY` üzerinden, canlı QGIS erişimi
yukarıdaki özel anahtar dosyası üzerinden alır. Kamu QGIS dosyaları anahtar
içermez. Yeniden dışa aktarma QGIS Python ortamı ve ayrı, boş çıktı klasörü kullanır.
[Harita üretim rehberi](map_atlas_plan.md) ·
[Özel dosyadan anahtar okuma ve üretim](qa/map_export_qa.md).
