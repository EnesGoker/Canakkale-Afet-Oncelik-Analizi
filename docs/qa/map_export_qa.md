# Harita ve atlas dışa aktarma QA kaydı

**Kaynak sürümü kapsamı:** İlk kamu sürümü kod, yöntem belgeleri, QGIS
proje tanımı ve seçilmiş analitik özetleri içerir. Tam kanonik veriler ve
harita/rapor dosyaları dahil değildir. Bu belgedeki tam analiz, katman ve
çıktı kontrolleri ilgili yerel dosyalar ayrıca sağlandığında çalışır; kaynak
kopyasında eksik girdilerin bildirilmesi beklenir. [Dosya kapsamı](../publication_file_scope.md).

Güncelleme: 2026-10-29 · CRS: EPSG:32635 · analiz gridi: 100 m.

Harita seti, korunan ilk 12 PNG/PDF ile 13. QGIS düzeninden üretilen
senaryo ortaklığı haritasını kapsar. Atlas bu 13 PDF'yi aynı sırada
birleştirir. İlk 12 tekil ürünün baytları ve 13. sayfanın kayıtlı tasarımı,
renkleri ve metinleri korunmuştur.

Bu belge, 13 harita ve atlasın teslim sözleşmesini ve üretim QA kaydını tanımlar.
Güncel düzen ve stil kayıtları [map_layouts_v1.json](../../config/map_layouts_v1.json)
içindedir. Kayıtlı 27 dosyanın boyutları ve SHA-256 özetleri
[çıktı manifestinde](../../outputs/maps/map_export_manifest.json) tutulur. Veri dağıtım izinleri bu
teknik QA'nın kapsamından ayrıdır;
[veri hakları kaydı](../data_rights_and_distribution.md) geçerliliğini korur.

## Koruma ve bağlama kararı

- İlk 12 PNG ve tek sayfalık PDF referans ürünleri bayt düzeyinde korunur.
- İlk 12 QGIS düzeninin harita katman kümeleri, kendi manuel lejantlarındaki
  katman sırası esas alınarak sabitlenir. Kriterler,
  paletler, başlıklar ve sayfa geometrisi değiştirilmez.
- 13. sayfanın başlığı, alt başlığı, bilgi metni, çerçevesi,
  kapsam, ölçek, kuzey oku ve dört kutulu lejant korunur. Gömülü yerel kaynak
  yollarının göreli hâle getirilmesi tasarım değişikliği değildir.
- İlk 12 düzenin yeniden çizimleri karşılaştırma adayıdır; korunmuş nihai
  dosyaların üzerine otomatik yazılmaz. 13. harita QGIS düzeninden alınır.
- Atlas, korunmuş ilk 12 PDF ve 13. PDF'nin 01–13 sırasıyla birleşimidir.
  Korelasyon figürü coğrafi atlasın 14. sayfası değildir.

## Çıktı seti

Her kök için `outputs/maps/png/<kök>.png` ve
`outputs/maps/pdf/<kök>.pdf` teslim dosyaları kullanılır:

| No | Dosya kökü |
|---:|---|
| 01 | `01_cok_kriterli_oncelik_sinifi` |
| 02 | `02_fay_yakinlik_skoru` |
| 03 | `03_nufus_maruziyet_skoru` |
| 04 | `04_zemin_kosulu_skoru` |
| 05 | `05_deprem_pga_skoru` |
| 06 | `06_yapi_maruziyet_yogunluk_skoru` |
| 07 | `07_taskin_skoru` |
| 08 | `08_hidrografya_yakinlik_skoru` |
| 09 | `09_egim_skoru` |
| 10 | `10_arazi_ortusu_duyarlilik_skoru` |
| 11 | `11_agac_ortusu_skoru` |
| 12 | `12_yol_erisim_zorlugu_skoru` |
| 13 | `13_senaryo_ortakligi` |

Atlas yolu: `outputs/atlas/canakkale_afet_oncelik_harita_atlasi.pdf`.
13 PNG, 13 tek sayfalık PDF ve 13 sayfalık bir atlas olmak üzere 27
harita/atlas dosyası manifestle izlenir. `_layout` eki yalnız düzen
adlarında kullanılır. Dosya boyutları sabit bir yaklaşık MB değeriyle değil,
manifestteki gerçek bayt sayısı ve SHA-256 özetiyle doğrulanır.

## Salt okunur kontrol

Proje kökünden:

```bash
python3 scripts/python/check_map_layouts.py --check --json
python3 scripts/python/export_map_layouts.py --check --json
bash scripts/bash/run_canonical_qa.sh --check
```

İlk iki komut kaydedilmiş QGS/QGZ, sözleşme ve ürünleri denetler; çıktı
üretmez. Gerçek katman sağlayıcıları ana QA içindeki PyQGIS kontrolünde açılır.
Web altlığı bağlantısı salt okunur çevrim dışı QA'da sınanmaz. Dokuzuncu
zorunlu kontrol; düzen, stil ve kaydedilmiş 27 dosyanın bütünlüğünü kapsar.
Dosya veya manifest eksikliği başarısızlık (çıkış 1) üretir.

Yeni bir karşılaştırma adayı üretmek için QGIS'in Python ortamı kullanılır:

```bash
# CARTO_BASEMAPS_KEY_FILE, anahtarı tek satırda tutan özel yerel dosyayı gösterir.
IFS= read -r CARTO_BASEMAPS_API_KEY < "$CARTO_BASEMAPS_KEY_FILE"
export CARTO_BASEMAPS_API_KEY
"$QGIS_PYTHON_BIN" scripts/python/export_map_layouts.py \
  --generate --output-dir /tmp/canakkale-layout-review-01 \
  --allow-web-basemap
unset CARTO_BASEMAPS_API_KEY
```

Yalnız 13. sayfa için `--layouts 13` eklenir. Hedef yeni veya boş bir klasör
olmalıdır; mevcut nihai ürünlerin üzerine yazılmaz. `--allow-web-basemap`,
projede tanımlı CARTO altlığını çizmek için açık ağ iznidir; bu bayrak olmadan
web altlığı içeren düzen üretimi başarısız olur. QGIS projesi kaydedilmez.
CARTO altlığı kullanılan üretimde `CARTO_BASEMAPS_API_KEY` gerekir;
anahtar yalnız çalışma anında kullanılır. Salt okunur kontroller anahtar istemez. Gerçek anahtar
QGS/QGZ, Git, doküman, manifest veya komut çıktısına yazılmaz. Genel QGIS
projesi özgün anahtarsız CARTO URL'sini korur. Üretici anahtarı yalnız çizim
sırasında bağlantıya uygular ve projeyi kaydetmez. Dolayısıyla genel proje
XML'i ile canlı isteğin kimlik doğrulaması arasındaki fark bilinçlidir; harita
katmanlarının stilleri ve sayfa tasarımı değişmez. QGIS'te etkileşimli açılışta
kullanıcı kendi anahtarını yalnız yerel özel yapılandırmasında sağlamalıdır.

Anahtar eklenmesi tek başına görsel kabul kanıtı değildir: HTTP 200 veya
teknik dosya üretimi sonrasında harita içeriği mutlaka görsel olarak incelenir.

## Kontrol sınırları ve kabul ölçütleri

| Kontrol | Beklenen |
|---|---|
| QGS ve QGZ içindeki QGS | Birebir aynı XML baytları |
| Düzen sayısı ve adları | Sözleşmedeki 13 düzen |
| Katman kümesi | Her haritanın doğru sıralı kümesi; kilitli |
| Stiller | Tüm harita katmanları için kilitli ve sözleşmeyle aynı |
| Lejant | Kendi haritasına bağlı; doğru tematik katmanı içeriyor |
| Yerel dosya kaynakları | Göreli, proje kökü içinde, mevcut |
| 13. haritanın renk değerleri | EXACT; tam 0, 1, 2, 3 |
| 13. haritanın lejantı | Sürekli renk çubuğu kapalı; dört ayrı kutu |
| PNG | A3 yatay, 300 DPI; 4960 × 3507 px, manifestte kayıtlı |
| Tekil PDF | Bir sayfa, A3 yatay |
| Atlas | 13 sayfa, aynı sıra ve sayfa ölçüsü |
| Kaydedilmiş dosyalar | Tam 27 yol; boyut ve SHA-256 eşliği |

PDF sayfa sayıları ve sayfa ölçüleri üretim sırasında PDF okuyucuyla
kontrol edilir. Standart kütüphaneli `check_map_layouts.py`, PDF'yi yeniden
ayrıştırmaz; doğrulanmış dosyanın checksum'ını ve manifestteki sayfa kaydını
kontrol eder. PNG başlığı ve boyutları ayrıca okunur. Görsel kontrol; başlık,
lejant, içerik, kırpılma ve eski referansla uyumu kapsar.

## 2026-10-24 üretim ve kabul kaydı

| Kontrol | Sonuç |
|---|---|
| 13. düzen tasarımının kaynakla eşliği | Geçti; kaynak tasarım korunuyor |
| İlk 12 PNG/PDF'nin bayt eşliği | Korunan referanslarla aynı |
| Gerçek QGIS yerel katman okuması | 28 yerel katman geçerli |
| Düzen kontrolü ve dışa aktarma testleri | 46 test geçti: 27 düzen kontrolü + 19 dışa aktarma testi |
| QA başlatıcısı testleri | 10 test geçti |
| Anahtarla yeniden çizim | 13 PNG/PDF çifti; 151 HTTP isteği, 0 ağ hatası |
| Kaynak QGS | Üretim sırasında değiştirilmedi; anahtar kaydedilmedi |
| Kartografik gözden geçirme | Bağımsız incelemede 13 PNG/PDF kabul edildi; temiz özgün altlık bağlamı |
| Atlas | 13 sayfa A3; ilk 12 korunmuş PDF + 13. PDF; 13 sayfanın içerik akışı kaynak PDF'leriyle eşleşti |
| Tekil PDF'ler | 13 dosyanın her biri bir sayfa A3 |
| Nihai PNG'ler | 13 dosyanın tamamı 4960 × 3507 px |
| Düzen ve final dosya kontrolü | Geçti: 13 düzen, 27 kayıtlı dosya, 0 hata |
| Atlasın PDF'den görsel kontrolü | 13 sayfa Poppler ile çizildi; toplu görünüm temiz |
| Canonical QA | Çıkış 0; 9 bütünlük kontrolü ve canonical üreticilerin salt okunur kontrolleri geçti |
| Üretim anahtarının genel dosyalardan ayrılması | Genel dosyalar ve QGZ içeriğinde gerçek anahtar eşleşmesi 0 |

Bağımsız görsel kabul, doğrudan düzen/çıktı kontrolü ve ana canonical QA
geçti. Son QA koşusunda GDAL/PROJ veri yolları QGIS kurulum kaynaklarına
ayarlanmıştır. Kaydedilmiş 24 eski harita dosyası ile korunan 171 veri,
analiz ve rapor dosyasında değişiklik yoktur. Teknik dosya üretimi tek başına
görsel kabul sayılmamış; PNG/PDF adayları ve birleşik atlas ayrıca incelenmiştir.

Canonical QA'nın son bildirimi “zorunlu kontroller geçti; web tile bağlantısı
test edilmedi” şeklindedir. Bu çevrim dışı kontrolün kapsamıdır. Gerçek CARTO
erişimi, anahtarla yapılan ayrı üretim koşusunda 151 istek ve 0 ağ hatasıyla
denetlenmiştir. Anahtar genel projeye veya kaydedilmiş çıktılara yazılmamıştır.

CARTO'nun “API KEY REQUIRED” hata yazısını içeren çizimler görsel kontrolden
geçmez. Anahtarla üretim özgün CARTO bağlamını kullanır; hata yazıları
silinerek veya başka bir harita resmiyle kapatılarak düzeltilmez.

Atıf ve kullanım açıklamaları [harita notunda](../../outputs/maps/README.md)
ve [atlas notunda](../../outputs/atlas/README.md) ürünlerle birlikte tutulur.
Mevcut sayfa tasarımlarında bütün kaynakların ayrıntılı lisans metninin veya
ayrı bir yöntem uyarısının basılı olduğu iddia edilmez. Teknik dışa aktarma
başarısı, üçüncü taraf verilerin kamuya dağıtım izninin tamamlandığı anlamına gelmez.

## Kimlik alanları ve üretim kaydı

Manifest v1'de bütün QGS dosyası üretim hash'iyle birebir eşleşir. Manifest
v2, yalnız `qgis/@saveUser`, `qgis/@saveUserFull` ve
`qgis/projectMetadata/author` değerlerinin değiştiği kimlik temizliğini
yeniden çizimden ayırır. `project_qgs_sha256`, **özgün dışa aktarma kaynağının**
hash'i olarak kalır; güncel proje hash'i `metadata_revision` içinde tutulur.

Tanık oluşturulurken özgün QGS'nin üretim hash'i, üç değer dışındaki bütün
XML baytlarının eşitliği, QGS/QGZ eşliği ve QGZ'nin XML dışı üyeleri doğrulanır.
İzin verilen alan listesi kodda sabittir; başka metadata, layout, stil,
veri yolu, XML boşluğu veya sürüm değişikliği kabul edilmez. Tanık önceki
kişisel değerleri içermez. `render_performed: false`, yeni harita üretimi
yapılmadığını açıkça kaydeder. 27 PNG/PDF/atlas boyut/hash kontrolü sürer.

Bu kayıt bir kaynak/provenance beyanıdır; erişilemeyen eski XML'i yalnız
hash'ten yeniden oluşturmaz ve veri paylaşım izni sağlamaz.
