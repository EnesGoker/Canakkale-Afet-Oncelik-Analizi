# Canonical QA: gerçek proje okuma ve hesap bütünlüğü

**Kaynak sürümü kapsamı:** İlk kamu sürümü kod, yöntem belgeleri, QGIS
proje tanımı ve seçilmiş analitik özetleri içerir. Tam kanonik veriler ve
harita/rapor dosyaları dahil değildir. Bu belgedeki tam analiz, katman ve
çıktı kontrolleri ilgili yerel dosyalar ayrıca sağlandığında çalışır; kaynak
kopyasında eksik girdilerin bildirilmesi beklenir. [Dosya kapsamı](../publication_file_scope.md).

## Kullanım ve ortam

Proje kökünde tek QA girişini çalıştırın:

```bash
bash scripts/bash/run_canonical_qa.sh --check
```

Bu giriş script/yol/VRT ve sayısal/QGIS kontrollerini çalıştırır.
GDAL/OGR komutları için mevcut `GDAL_BIN`,
`QGIS_BIN` veya araç değişkenleri kullanılır. Başlatıcı ve tablo scriptlerinin
Python'u `PYTHON_BIN` ile seçilir.

`run_integrity_checks.py`, NumPy/GDAL ve PyQGIS modüllerini gerçekten içe
aktarabilen Python ortamlarını arar. `GDAL_PYTHON_BIN` ve `QGIS_PYTHON_BIN`
açık seçimlerdir; verilmemişse `QGIS_BIN` altındaki Python, `PYTHON_BIN`,
başlatıcının Python'u ve PATH'teki `python3` değerlendirilir. Açık seçilmiş
bir ortam için sessizce başka Python'a geçilmez. macOS paketinde modül ve
PROJ/GDAL kaynak yolları paket konumundan türetilir. `requirements.txt`, GDAL
ve QGIS'in ikili Python bağlarını kurmaz.

Tam QA; GDAL 3.12.3 ve NumPy 2.4.4 (Accelerate) analiz ortamı ile ayrı
QGIS 3.44.15 okuyucusu birlikte seçilerek doğrulanmıştır. macOS için
`run_compatible_qa.py`, ortamları ve geçici CLI köprülerini ayırır; kontrol
algoritmalarını veya toleranslarını değiştirmez. GDAL 3.13.3'ün varsayılan
eğim/taşkın yeniden örneklemesi eski reçetelerden farklıdır; ana MCDA aynı kalır.
[Ortam uyumluluğu ve doğrulama kapsamı](runtime_compatibility.md).

Yalnız bütünlük kontrolleri veya yapılandırılmış sonuç için:

```bash
python3 scripts/python/run_integrity_checks.py --check
python3 scripts/python/run_integrity_checks.py --check --json
```

`--json` stdout'a yazar; proje içinde rapor dosyası oluşturmaz. Tekil
`check_mcda_integrity.py` ve `check_qgis_runtime.py` de `--check`, `--json`,
`--project-root` kabul eder. Tekil kontroller doğrudan uygun GIS Python'uyla
çalıştırılmalıdır. QGIS kontrolünde `--project-file` ile kök içindeki başka
bir QGS/QGZ seçilebilir.

## Gerçek QGIS kontrolü

- QGZ/QGS içeriği ve tanımlı katman kimlikleri okunur.
- Yeni, geçici profille **`QgsProject.read()` gerçekten çağrılır**; algoritma
  listelenmesi proje açıldı kanıtı olarak kullanılmaz.
- Yüklenen katmanlar XML listesiyle eşleştirilir. Yerel dosyaların kök içinde
  kaldığı ve QGIS sağlayıcısının `isValid()` sonucu denetlenir. Dosyanın
  var olması, GeoPackage içindeki istenen tablonun varlığı yerine geçmez.
- Ağ kapalıdır, harita çizilmez. Web/XYZ katmanları yerel katmanlardan ayrı
  **ATLANDI: bağlantı sınanmadı** olarak raporlanır. Sağlayıcının tanımlı
  olması, internetten döşeme indirilebildiği şeklinde yorumlanmaz.
- Kaynak URL'leri/anahtarlar sonuç kaydına yazılmaz. Çevrimdışı yerel
  sağlayıcı kontrolü sıradan yerel dosyalarla sınırlıdır; uzak/sanal dosya
  sistemi URI'leri bu kontrol kapsamına alınmaz.

Bu kontrol layout içeriğinin doğru haritayı gösterdiğini, okunabilirliğini
veya basemap'in gelecekte erişilebilirliğini doğrulamaz. Harita içeriği ve
görsel kontrollerin kapsamı [harita dışa aktarma QA kaydında](map_export_qa.md)
açıklanır.

## Raster ve MCDA kontrolü

1. Config'teki `baseline` satırlarında 11 ayrı kriter, canonical sıra,
   göreli kaynak yolları, sonlu `[0,1]` ağırlıklar ve toplam `1` denetlenir.
   Değişmiş config'in eski çıktılarla kullanılması hesap karşılaştırmasında
   yakalanır.
2. AOI yalnız `analysis_template_100m_32635.tif == 1` ile belirlenir. Şablon
   `0/1` olmalı; NoData `0` ve GDAL geçerlilik maskesi AOI ile uyuşmalıdır.
   Kayıtlı sonuç sınıflarından AOI çıkarılmaz.
3. Her kriter ve üç sonuçta tek bant, semantik **EPSG:32635**, kuzeye yönlü
   100 m piksel, şablon boyutu/geotransformu ve NoData metadata'sı doğrulanır.
   Sürekli skorlar Float32, sınıf/şablon tam sayı olmalıdır; sınıfta Byte ve
   Int16 farkı tek başına bozukluk sayılmaz.
4. AOI içinde NoData, GDAL maske boşluğu, NaN, sonsuz değer ve skor aralığı
   denetlenir. Skor toleransı **mutlak `1e-6`**; sınıflar `1–5` tam sayıdır.
5. Ağırlıklı toplam üretim sırasıyla **Float32** olarak bellekte hesaplanır.
   Normalizasyon üretim scriptindeki korunmuş **`0.029` / `0.473`**
   sabitleriyle ve `0–1` kırpmasıyla yapılır. Sınıf eşikleri **`0.2`, `0.4`,
   `0.6`, `0.8`**; eşik değeri üst sınıfa girer. Politika değişikliği sessizce
   yeni ölçüt kabul edilmez; inceleme gerektirir.
6. Üç kayıtlı sonuç dosyası zorunludur. Ham/normalize skor farkı en çok
   `1e-6`, sınıf eşleşmesi tam olmalıdır. AOI dışı sürekli çıktılar `-9999`,
   sınıf çıktısı `0` olmalı; GDAL maskeleri de bunu yansıtmalıdır.

Bu, mevcut skorların ve baseline birleşiminin teknik tutarlılık kontrolüdür.
Kriter dönüşümlerinin bilimsel doğruluğunu veya gerçek afet riskini
doğrulamaz. Duyarlılık üreticisinin senaryo bazlı gözlenen min/max
normalizasyonu, canonical baseline ölçütü yerine kullanılmaz.

## Açık arazi örtüsü sınır bulgusu

Mevcut arazi örtüsü skorunda şablon AOI'si dışında **5.272 geçerli hücre**
bulunur. Diğer 10 kriter ve üç nihai çıktı doğru dış maskeleme taşır.
Bu girdi, adı açıkça belirtilen tek **uyarı istisnasıdır**; genel bir maske
muafiyeti değildir. Taşma hücrelerinin sonlu ve skor aralığında olması,
maskenin değerlerle uyuşması ve sayının **5.272'yi aşmaması** zorunludur.
Yeni/büyüyen taşma veya başka kriter/nihai çıktıda taşma başarısız olur.

İstisna, AOI dışındaki hücreleri sonuca dahil etmez; bağımsız şablon AOI'si
korunur. Uyarı görünür kalır; “bütün girdilerin dış maskesi temiz” sonucu
verilmez. Kaynak raster korunur; taşmanın kaynağı ve AOI izolasyonunun
sonuçlara etkisi [sınır bulgularında](stage3_boundary_findings.md#arazi-örtüsü-geçerli-kenar-hücrelerinin-izolasyonu)
açıklanır.

## Başarı, başarısızlık ve eksik kontrol

| Çıkış | Anlam |
|---:|---|
| `0` | Bütün zorunlu yerel/QGIS/hesap kontrolleri geçti; kayıtlı uyarı ayrıca görünür. |
| `1` | Bozuk/eksik girdi, hesap uyuşmazlığı, yanlış açık runtime ayarı veya çalıştırma hatası. |
| `2` | Gerekli GIS Python/modül/kaynak ortamı kullanılamadığı için zorunlu kontrol tamamlanamadı; tam başarı değildir. |

Web bağlantısının çevrimdışı atlanması beklenen kapsam sınırıdır; zorunlu
yerel proje kontrolünün atlanmasıyla aynı şey değildir. Alt süreç çökmesi,
zaman aşımı veya geçersiz sonuç JSON'u başarı olarak kabul edilmez.

## Geçici bozuk girdi testleri

Testler gerçek proje verilerini kullanarak bozmaz; küçük geçici projeler ve
rasterlar oluşturur, bitince temizler. Uygun runtime ile:

```bash
python3 scripts/python/test_integrity_runner.py
"$GDAL_PYTHON_BIN" scripts/python/test_mcda_integrity.py
"$QGIS_PYTHON_BIN" scripts/python/test_qgis_runtime.py
"$GDAL_PYTHON_BIN" scripts/python/test_criterion_transformations.py
"$GDAL_PYTHON_BIN" scripts/python/test_analysis_baseline.py
```

GIS Python değişkenleri, bu örnekleri doğrudan çalıştırmadan önce uygun Python'a
ayarlanmalıdır. PROJ/GDAL kaynakları da o ortamda kullanılabilir olmalıdır;
özellikle paket Python'unun doğrudan kullanımında gerekebilir. Eksik GIS
bağımlılığı test takımının başarılı sayılarak atlanmasına yol açmaz.

Kapsam: eksik/yanlış yol, yanlış CRS/grid, geçersiz şablon/maske, NoData,
NaN/Inf/aralık dışı değer, değişmiş ağırlık, bozuk ham/normalize/sınıf hücresi,
AOI dışı taşma; QGIS'te eksik/bozuk proje veya veri, olmayan GPKG tablosu,
eksik PyQGIS; başlatıcıda hata/atlama ayrımı ve tutarsız alt süreç sonucu.

## Kaynak→skor eşdeğerliği ve sabitlenmiş analiz girdileri

QA girişi kaynak→skor eşdeğerliğini ve sabitlenmiş girdileri iki modülle denetler:

- `check_criterion_transformations.py`: Sekiz eski kriterin kaynak dosyasından
  bugünkü skorla eşdeğer reçetesini GDAL belleğinde hesaplar. Tarihsel kayıt,
  sayısal eşdeğerlik ve PGA/eğim parametre kökenindeki belirsizlik
  [ayrı belgede](../methodology/criterion_transformations.md) açıklanır. Bu
  kontrol bütün upstream ham hazırlama zincirinin yeniden üretimi değildir.
- `analysis_baseline.py`: İki ek analiz için seçilmiş 27 dosyanın checksum ve
  senaryo sözleşmesini doğrular. NumPy/GDAL kullanan ortak yükleyici yalnız
  template AOI içindeki 1D değerleri döndürür. Böylece arazi örtüsünün 5.272
  dış hücresi analize girmez; kaynak raster korunur.

Normalizasyon politikası ve snapshot yenilemenin kapsamı
[baseline notunda](../methodology/normalization_and_baseline.md) yer alır.

## Kriter korelasyonu ve figür kontrolü

QA girişi korelasyon sonuçlarını iki zorunlu çıktı kontrolüyle denetler:

- `generate_correlation_analysis.py --check`: Sabitlenmiş 27 dosyayı ve mevcut
  MCDA bütünlüğünü doğruladıktan sonra, aynı 981.033 AOI hücresinden 11 kriterin
  Pearson matrisini ve dağılım istatistiklerini yeniden hesaplar. Kayıtlı iki
  CSV'nin sırasını, bütün katsayı/istatistiklerini ve JSON manifestini karşılaştırır.
  Matris sonlu, simetrik, köşegeni 1 ve `[-1,1]` sınırında olmalıdır; mutlak
  tolerans `1e-12`dir. Eksik/sabit veya sayısal olarak ayırt edilemeyecek kadar
  sabit kriter reddedilir; NaN doldurma, örnekleme, çift bazında hücre eleme
  veya hatalı matrisi kırparak düzeltme yapılmaz.
- `plot_criterion_correlation.py --check`: Kaynak üç analiz dosyasını ve
  PNG/PDF'nin checksum'larını figür manifestiyle doğrular. AOI, kriter sırası
  ve baseline kimliği de eşleşmelidir. Bu kontrol **Matplotlib yüklemez**;
  PNG/PDF'nin görsel okunabilirliği ayrıca incelenmiştir. Checksum, görsel
  yorumun veya yöntem doğruluğunun otomatik kanıtı sayılmaz.

Kontrol, eksik veya değiştirilmiş çıktıda `1`, gerekli modül yoksa `2` döner.
QA eksik dosyayı yeniden üretmez. Yalnız ilgili kontroller için, uygun
Python ortamları önceden seçildikten sonra:

```bash
"$GDAL_PYTHON_BIN" scripts/python/generate_correlation_analysis.py --check --json
"$PLOT_PYTHON_BIN" scripts/python/plot_criterion_correlation.py --check --json
"$GDAL_PYTHON_BIN" scripts/python/test_correlation_analysis.py
"$PLOT_PYTHON_BIN" scripts/python/test_plot_criterion_correlation.py
```

`PLOT_PYTHON_BIN`, NumPy ve üretim/test için Matplotlib bulunan Python'u
gösterir; QGIS Python'u bunları sağlıyorsa aynı yorumlayıcı seçilebilir.
Bu değişken yalnız komut örneklerinin kısaltmasıdır; QA başlatıcısı önceki
GIS Python çözümlemesini kullanır. Yeni figür üretimi dışında Matplotlib
gerekmez.

## Korelasyon çıktılarını yeniden üretme

`--generate`, açıkça belirtilmiş **yeni veya boş** hedef ister ve mevcut
dosyaların üzerine yazmaz. Eski çıktıları koruyarak denemek için:

```bash
mkdir -p outputs/figures
"$GDAL_PYTHON_BIN" scripts/python/generate_correlation_analysis.py --generate --output-dir outputs/tables/criterion_correlation_recheck
"$PLOT_PYTHON_BIN" scripts/python/plot_criterion_correlation.py --generate --source-dir outputs/tables/criterion_correlation_recheck --output-dir outputs/figures/criterion_correlation_recheck
"$GDAL_PYTHON_BIN" scripts/python/generate_correlation_analysis.py --check --output-dir outputs/tables/criterion_correlation_recheck
"$PLOT_PYTHON_BIN" scripts/python/plot_criterion_correlation.py --check --source-dir outputs/tables/criterion_correlation_recheck --output-dir outputs/figures/criterion_correlation_recheck
```

Bu hedefler de varsa başka yeni bir ad seçilir. Varsayılan QA, sürümü
sabitlenmiş `criterion_correlation_v1` dizinlerini kontrol etmeye devam eder.
Sayısal sonuçlar ve yorum: [kriter korelasyonu](../analysis/criterion_correlation.md).

## Senaryo ortaklığı ve harita kontrolü

QA girişi senaryo ortaklığı sonuçlarını ve haritasını aşağıdaki zorunlu
kontrollerle denetler:

- `generate_scenario_agreement.py --check`, sabit baseline yükleyicisini
  kullanır; baseline sınıflarını korur, alternatifleri eski duyarlılık
  üreticisinin Float32 toplam/normalizasyon/sınıf fonksiyonlarıyla hesaplar.
  Mevcut altı CSV'nin **173 satırındaki bütün alanlar** karşılaştırılır;
  sekiz referans CSV'nin checksum'u ayrıca sabit girdi kontrolüne dahildir.
- Üç senaryoda sınıf `4` veya `5` üyeliği sayılır. Sayım `0–3`; üyelik kodu
  `baseline × 1 + deprem × 2 + eşit × 4` ile `0–7`dir. İki GeoTIFF Byte,
  EPSG:32635 ve template ile aynı 100 m griddedir. **AOI dışı NoData 255**;
  AOI içi sıfır geçerli veridir. Yeniden hesaplanan bütün hücreler, grid,
  CRS, NoData ve GDAL geçerlilik maskesi kayıtlı rasterlarla karşılaştırılır.
- İlçe ataması kaynak FID sırasıyla GDAL merkez rasterizasyonudur;
  `ALL_TOUCHED` kullanılmaz. Her AOI hücresinin tam bir ilçe tarafından
  kapsanması, 12 ilçenin her birinin boş olmaması ve ilçe toplamlarının il
  toplamını vermesi gerekir. Yüzdelerin paydası aynı kapsamdaki **AOI hücre
  alanı**dır; vektör poligon alanı değildir.
- Yeni tablolar **52 sayım, 104 üyelik ve 39 senaryo karşılaştırma satırı**
  içerir. Sayılar tam eşleşir; CSV kayan nokta değerleri mutlak `1e-10`
  toleransla karşılaştırılır. Boş yüksek küme paydasında Jaccard/korunma/
  örtüşme oranları boş bırakılır. Üretim manifesti kaynak/politika ve beş
  dosyanın checksum'larını içerir; metadata değişimi de başarısız olur.
- `plot_scenario_agreement.py --check`, analiz paketinin beş dosyasını,
  baseline manifesti ve haritanın template/idari referanslarını doğrular.
  Üyelik–sayım eşitliği, sıfır–NoData ayrımı ve PNG/PDF kaynak/dosya
  checksum'ları kontrol edilir. Bu mod **Matplotlib yüklemez**. Görsel
  okunabilirlik ayrıca incelenir; QGIS layout/atlas kontrolü aşağıda ayrıca açıklanır.

Yalnız ilgili kontroller/testler için uygun GIS Python'u seçilerek:

```bash
"$GDAL_PYTHON_BIN" scripts/python/generate_scenario_agreement.py --check --json
"$GDAL_PYTHON_BIN" scripts/python/plot_scenario_agreement.py --check --json
"$GDAL_PYTHON_BIN" scripts/python/test_scenario_agreement.py
"$GDAL_PYTHON_BIN" scripts/python/test_plot_scenario_agreement.py
```

Sayısal motor ve harita kontrolü NumPy/GDAL/OGR ister. Harita üretimi ve
gerçek render testi için aynı ortamda Matplotlib ve Pillow da bulunmalıdır.
Diğer kontrollerdeki gibi çıkış `0` başarı, `1` bozuk/eksik dosya veya hesap
hatası, `2` eksik bağımlılıktır. Eksik dosya kontrolde otomatik üretilmez.

Eski çıktıları koruyarak yeni/boş hedeflerde yeniden üretim:

```bash
mkdir -p outputs/analysis outputs/figures
"$GDAL_PYTHON_BIN" scripts/python/generate_scenario_agreement.py --generate --output-dir outputs/analysis/scenario_agreement_recheck
"$GDAL_PYTHON_BIN" scripts/python/plot_scenario_agreement.py --generate --source-dir outputs/analysis/scenario_agreement_recheck --output-dir outputs/figures/scenario_agreement_recheck
"$GDAL_PYTHON_BIN" scripts/python/generate_scenario_agreement.py --check --output-dir outputs/analysis/scenario_agreement_recheck
"$GDAL_PYTHON_BIN" scripts/python/plot_scenario_agreement.py --check --source-dir outputs/analysis/scenario_agreement_recheck --output-dir outputs/figures/scenario_agreement_recheck
```

Hedefler zaten doluysa başka yeni bir ad seçilir; üzerine yazılmaz.
Varsayılan QA `scenario_agreement_v1` paketini ve haritasını denetler.
[Sayısal sonuçlar ve coğrafi yorum](../analysis/scenario_agreement.md),
senaryoların kendi göreli ölçeklerini ve seçilmiş üç ayarın kapsamını açıklar.

## QGIS düzenleri ve harita/atlas bütünlüğü

Ana QA'nın dokuzuncu kontrolü `check_map_layouts.py` ile 13 QGIS düzenini,
katman/stil kilitlerini, lejant bağlantılarını, göreli kaynakları ve QGS/QGZ
XML eşliğini doğrular. Tam düzen ve stil hashleri `config/map_layouts_v1.json`
içindedir. 13 PNG, 13 tek sayfalık PDF ve 13 sayfalık atlasın boyut ve SHA-256
kayıtları `outputs/maps/map_export_manifest.json` üzerinden denetlenir.
Standart Python yeterlidir; bu kontrol ağa bağlanmaz veya PDF'yi yeniden çizmez.
PDF sayfa sayıları/ölçüleri üretim sırasında PDF okuyucuyla doğrulanmıştır.

```bash
python3 scripts/python/check_map_layouts.py --check --json
python3 scripts/python/export_map_layouts.py --check --json
python3 -m unittest discover -s scripts/python -p 'test_*map_layouts.py'
```

Üretim ayrı `--generate` moduyla, QGIS Python ortamında yeni/boş klasöre yapılır.
Canlı CARTO altlığı için açık ağ bayrağı ve çalışma anında
`CARTO_BASEMAPS_API_KEY` gerekir; anahtar kamu QGIS projesine veya çıktı kaydına
yazılmaz. [Üretim ve görsel kabul kaydı](map_export_qa.md) komutları ve sınırları
ayrıntılandırır. HTTP başarısı tek başına görsel kabul sayılmaz.

## Salt okuma güvencesi

GDAL veri kaynakları salt okunur açılır, PAM/bytecode yazımı kapatılır.
Hesaplar bellekte; QGIS profili ve test dosyaları sistem geçici dizinindedir.
`--execute`, `--generate`, proje kaydetme veya harita dışa aktarma yapılmaz.
Gerçek proje üzerinde yapılan kontrol koşusunda dosya checksum'ları çalışma
öncesi ve sonrasında karşılaştırılarak salt okuma davranışı doğrulanmıştır.
