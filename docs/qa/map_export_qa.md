# Harita ve atlas dışa aktarma QA kaydı

**Kaynak sürümü kapsamı:** İlk kamu sürümü kod, yöntem belgeleri, QGIS
proje tanımı, seçilmiş analitik özetleri ve harita PNG görsellerini içerir.
Tam kanonik veriler, harita PDF/atlas ve rapor dosyaları dahil değildir. Bu belgedeki tam analiz, katman ve
çıktı kontrolleri ilgili yerel dosyalar ayrıca sağlandığında çalışır; kaynak
kopyasında eksik girdilerin bildirilmesi beklenir. [Dosya kapsamı](../publication_file_scope.md).

Güncelleme: 2026-11-03 · CRS: EPSG:32635 · analiz gridi: 100 m.

Harita seti, korunan ilk 12 PNG/PDF ile 13. QGIS düzeninden üretilen
senaryo ortaklığı haritasını ve yalnız PNG olarak üretilen 14. yüksek
öncelikte kalma oranı haritasını kapsar. Atlas 01–13 PDF'lerini aynı sırada
birleştirir. İlk 12 tekil ürünün baytları ve 13. sayfanın kayıtlı tasarımı,
renkleri ve metinleri korunmuştur.

Bu belge, 14 harita ve atlasın teslim sözleşmesini ve üretim QA kaydını tanımlar.
Güncel düzen ve stil kayıtları [map_layouts_v1.json](../../config/map_layouts_v1.json)
içindedir. Kayıtlı 28 dosyanın boyutları ve SHA-256 özetleri
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
  Korelasyon figürü coğrafi atlasın sayfası değildir.
- 14. düzenin sözleşme kaydı `pdf_export: false` taşır; harita yalnız PNG
  olarak üretilir ve atlasa girmez.

## Çıktı seti

Her kök için `outputs/maps/png/<kök>.png` ve
`outputs/maps/pdf/<kök>.pdf` teslim dosyaları kullanılır (14 için yalnız PNG):

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
| 14 | `14_yuksek_oncelik_olasiligi` |

Atlas yolu: `outputs/atlas/canakkale_afet_oncelik_harita_atlasi.pdf`.
14 PNG, 01–13 için 13 tek sayfalık PDF ve 13 sayfalık bir atlas olmak üzere 28
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
zorunlu kontrol; düzen, stil ve kaydedilmiş 28 dosyanın bütünlüğünü kapsar.
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

Seçili düzenler için `--layouts` eklenir (ör. `--layouts 14` veya `--layouts 01,02`); 14. düzende PDF üretilmez. Hedef yeni veya boş bir klasör
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
| Düzen sayısı ve adları | Sözleşmedeki 14 düzen |
| Katman kümesi | Her haritanın doğru sıralı kümesi; kilitli |
| Stiller | Tüm harita katmanları için kilitli ve sözleşmeyle aynı |
| Lejant | Kendi haritasına bağlı; doğru tematik katmanı içeriyor |
| Yerel dosya kaynakları | Göreli, proje kökü içinde, mevcut |
| 13. haritanın renk değerleri | EXACT; tam 0, 1, 2, 3 |
| 13. haritanın lejantı | Sürekli renk çubuğu kapalı; dört ayrı kutu |
| 14. haritanın renk değerleri | DISCRETE; sayım sınırları 0, 499, 999, 1499, 1799, 2000 (P = sayım / 2.000); 0 saydam |
| 14. haritanın lejantı | Sürekli renk çubuğu kapalı; altı ayrı kutu ve baseline yüksek+ sınır çizgisi |
| PNG | A3 yatay, 300 DPI; 4960 × 3507 px, manifestte kayıtlı |
| Tekil PDF | 01–13 için bir sayfa, A3 yatay; 14 için PDF yok |
| Atlas | 13 sayfa, aynı sıra ve sayfa ölçüsü |
| Kaydedilmiş dosyalar | Tam 28 yol; boyut ve SHA-256 eşliği |

PDF sayfa sayıları ve sayfa ölçüleri üretim sırasında PDF okuyucuyla
kontrol edilir. Standart kütüphaneli `check_map_layouts.py`, PDF'yi yeniden
ayrıştırmaz; doğrulanmış dosyanın checksum'ını ve manifestteki sayfa kaydını
kontrol eder. PNG başlığı ve boyutları ayrıca okunur. Görsel kontrol; başlık,
lejant, içerik, kırpılma ve eski referansla uyumu kapsar.

## 2026-11-03 üretim ve kabul kaydı (v0.2.1, atıf bandında yeni depo adresi)

| Kontrol | Sonuç |
|---|---|
| Düzen değişikliği | 14 düzenin `atif_kaynak_bildirimi` etiketinde yalnız depo adresi değişti (`github.com/EnesGoker/Canakkale-Afet-Oncelik-Analizi/blob/main/docs/static_map_attributions.md`); etiketin konumu, boyutu ve yazı tipi, diğer öğeler, katmanlar ve stiller aynı. Metin [statik harita bildirimleri](../static_map_attributions.md) ile aynı |
| Üretim | `export_map_layouts.py --generate --allow-web-basemap`, QGIS 3.44.15; tek koşu (01–14), 151 HTTP isteği, 0 ağ hatası; kaynak QGS değişmedi |
| Nihai PNG'ler | 14 dosya, 4960 × 3507 px, 300 DPI; PNG parçaları IHDR, pHYs, IDAT, IEND; yan dosya yok |
| Önceki üretimle fark | 02–14'te değişen bütün pikseller atıf bandında (11.966–11.973 piksel). 01'de ek olarak bant dışında 41 piksel (kanal farkı ≤ 9) altlık karo dikiş çizgilerinde; tematik ve vektör katmanlarda fark yok |
| Tekil PDF'ler ve atlas | 13 PDF; atlas aynı 13 PDF sayfasından yeniden birleştirildi, sayfa içerikleri kaynaklarla aynı |
| Görsel kabul | 14. harita yazar tarafından tam incelendi; 01 ve rastgele seçilen 04 önceki dışa aktarımla karşılaştırıldı; atıf bandında yeni adres, taşma yok |
| Düzen ve final dosya kontrolü | Geçti: 14 düzen, 28 kayıtlı dosya |

QGIS, dışa aktarımdan sonra coğrafi konum yazmak için PNG'yi GDAL ile güncelleme kipinde açmayı dener; PNG sürücüsü bunu
desteklemediği için terminalde düzen başına bir `ERROR 6` satırı görülür. PNG değişmez ve yan dosya yazılmaz.

## 2026-11-03 üretim ve kabul kaydı (v0.2, 14. harita)

| Kontrol | Sonuç |
|---|---|
| Düzen değişikliği | 14. düzen 13. düzenin sayfa tasarımından eklendi: P(yüksek+) sayım rasterı (`outputs/analysis/weight_perturbation_v1/high_plus_probability_count_32635.tif`) ve baseline yüksek+ sınır çizgisi (0,15 mm, #4d4d4d). Sınır katmanı türev harita katmanıdır (`outputs/maps/layers/baseline_high_plus_boundary_32635.geojson`; üretici [`build_high_plus_boundary.py`](../../scripts/python/build_high_plus_boundary.py): donmuş sınıf rasterında 4–5 ∩ AOI, 4 komşuluk, 2.022 poligon, 54.592 hücre = 545,92 km², SHA-256 `841d9fa3…`; `--check` kayıtlı dosyayı bayt bayt yeniden üretir); proje `data/interim`'e başvurmaz ([Interim VRT politikası](../interim_vrt_policy.md)). 01–13 düzenlerinin XML'i değişmedi |
| Üretim | `export_map_layouts.py --generate --allow-web-basemap`, QGIS 3.44.15; tek koşu (01–14), 151 HTTP isteği, 0 ağ hatası; kaynak QGS değişmedi |
| Nihai PNG'ler | 14 dosya, 4960 × 3507 px, 300 DPI |
| 01–13 yeniden üretimi | 03–13 PNG'leri 2026-11-02 üretimiyle bayt bayt aynı. 01 ve 02'de 400 ve 1.085 piksel (%0,002 ve %0,006) farklı; hepsi altlık karo dikiş çizgilerinde ve beyaza yakın tonlarda, tematik ve vektör katmanlarda fark yok |
| 14'ün yeniden üretimi | Sınır katmanının yolu değişmeden önceki ilk 14 üretimine göre 2.251 piksel (%0,013) farklı; 2.244'ü karo dikiş çizgilerinin 3 px yakınında, düşük doygunluklu gri tonlarda (mor sınıf piksellerinde fark yok); 13 piksel sınır/idari çizgilerin dikişi kestiği yerlerde, kanal farkı ≤ 4 |
| Tekil PDF'ler | 13 PDF; önceki üretimden yalnız oluşturma tarihi ve XMP belge kimliğiyle ayrılır |
| Atlas | 13 sayfa; aynı PDF sayfalarından yeniden birleştirme önceki atlasla bayt bayt aynı |
| Görsel kabul | 14. harita yazar tarafından tam incelendi; 01–13 örneklemeyle: 01 ve rastgele seçilen 06 önceki dışa aktarımla karşılaştırıldı (13 de görüldü); sorun bulunmadı |
| Düzen ve final dosya kontrolü | Geçti: 14 düzen, 28 kayıtlı dosya |

Aynı projeden ve sözleşmeden yapılan iki dışa aktarım, CARTO karo dikişlerinde
birkaç yüz ile birkaç bin piksel farklı olabilir (01, 02 ve 14 yukarıda); bu nedenle PNG pinleri ve
manifest SHA-256 değerleri yalnız kaydedilen dışa aktarıma aittir.

## 2026-11-02 üretim ve kabul kaydı (v0.2, görünür atıflı haritalar)

| Kontrol | Sonuç |
|---|---|
| Düzen değişikliği | 13 düzene alt bant atıf etiketi eklendi; lejantta görünen katman ve grup adları Türkçe yazımla düzeltildi. Katman kimlikleri, veri kaynakları ve kilitli stiller değişmedi |
| Üretim | `export_map_layouts.py --generate --allow-web-basemap`, QGIS 3.44.15; iki koşu (01; 02–13), aynı QGS ve sözleşme; her koşuda 151 HTTP isteği, 0 ağ hatası; kaynak QGS değişmedi |
| PNG metadata | Dışa aktarım metadata kapalı; PNG'lerde metin parçası yok (izinli tek değer `Author = Enes Göker`); yalnız IHDR, pHYs, IDAT, IEND |
| Nihai PNG'ler | 13 dosya, 4960 × 3507 px, 300 DPI |
| Altlık çizimi | 13 haritanın çerçevesinde altlık piksel düzeyinde denetlendi: beyaz piksel payı < %0,01, boş karo bloğu 0 |
| Tekil PDF'ler | Aynı iki koşunun 13 PDF'i; her biri bir sayfa A3 |
| Atlas | 13 sayfa A3, 01–13 sözleşme sırası, ek sayfa yok; her sayfanın içerik akışı kaynak PDF ile bayt bayt aynı |
| Görsel kabul | 13 PNG yazar tarafından incelendi |
| Düzen ve final dosya kontrolü | Geçti: 13 düzen, 27 kayıtlı dosya |

Aynı karo kümesi 13 düzenin hepsinde kullanılır (harita çerçevesi ve kapsamı aynıdır); istek sayısı koşu başına kaydedilir, düzen başına değil.

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

Manifest v1'de bütün QGS dosyası üretim hash'iyle birebir eşleşir; v0.2
çıktıları (2026-11-02) bu biçimdedir ve 27 kayıt aynı QGS hash'ine bağlıdır; 2026-11-03'ten beri 28 kayıt
(14 PNG, 13 PDF, atlas) güncel QGS hash'ine bağlıdır. Manifest
v2, yalnız `qgis/@saveUser`, `qgis/@saveUserFull` ve
`qgis/projectMetadata/author` değerlerinin değiştiği kimlik temizliğini
yeniden çizimden ayırır. `project_qgs_sha256`, **özgün dışa aktarma kaynağının**
hash'i olarak kalır; güncel proje hash'i `metadata_revision` içinde tutulur.

Tanık oluşturulurken özgün QGS'nin üretim hash'i, üç değer dışındaki bütün
XML baytlarının eşitliği, QGS/QGZ eşliği ve QGZ'nin XML dışı üyeleri doğrulanır.
İzin verilen alan listesi kodda sabittir; başka metadata, layout, stil,
veri yolu, XML boşluğu veya sürüm değişikliği kabul edilmez. Tanık önceki
kişisel değerleri içermez. `render_performed: false`, yeni harita üretimi
yapılmadığını açıkça kaydeder. Kayıtlı bütün PNG/PDF/atlas dosyalarının boyut/hash kontrolü sürer.

Bu kayıt bir kaynak/provenance beyanıdır; erişilemeyen eski XML'i yalnız
hash'ten yeniden oluşturmaz ve veri paylaşım izni sağlamaz.
