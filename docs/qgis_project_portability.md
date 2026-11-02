# QGIS proje taşınabilirliği

**Kaynak sürümü kapsamı:** İlk kamu sürümü kod, yöntem belgeleri, QGIS
proje tanımı ve seçilmiş analitik özetleri içerir. Tam kanonik veriler ve
harita/rapor dosyaları dahil değildir. Bu belgedeki tam analiz, katman ve
çıktı kontrolleri ilgili yerel dosyalar ayrıca sağlandığında çalışır; kaynak
kopyasında eksik girdilerin bildirilmesi beklenir. [Dosya kapsamı](publication_file_scope.md).

Güncelleme: 2026-10-24.

QGIS projesi, 13 harita düzeninin katman ve stil bağlantılarını içerir.
28 yerel katman QGIS'te geçerli bulunmuştur. 13 tekil PNG/PDF harita ve
13 sayfalık atlas, 27 dosya manifestiyle izlenir.
Canlı CARTO altlığının anahtarı yalnız çalışma ortamından sağlanır.

Güncel açılabilir proje `qgis/canakkale_disaster_priority.qgz` dosyasıdır.
Yanındaki `canakkale_disaster_priority.qgs`, aynı projenin açık XML kopyasıdır;
QGZ içindeki QGS ile bayt düzeyinde eşleşmesi zorunludur. QGZ'nin proje dışı
üyeleri, stil veritabanı ve varsa ekler korunur. Harita düzenlerinin tek
sözleşmesi [map_layouts_v1.json](../config/map_layouts_v1.json) dosyasıdır.

## Göreli yol kapsamı

Yerel veri kaynakları QGIS proje klasörüne göre çözülür:

```text
../data/processed/analysis/mcda_priority_class_32635.tif
../data/processed/admin/canakkale_districts_32635.gpkg|layername=canakkale_districts_32635
../outputs/analysis/scenario_agreement_v1/scenario_agreement_count_32635.tif
```

Politika; `projectlayers/datasource`, katman ağacı, lejant ağacı ve haritaların
gömülü `LayerSet` / `LayerStyles` kaynaklarını birlikte kapsar. Dosyalar proje
kökünün içinde bulunmalıdır. Yol taşınabilirliği, harita kapsamını, stilleri
ve sayfa tasarımını değiştirmeden sağlanır. Yerleşik QGIS kuzey oku gibi
`arrows/NorthArrow_04.svg` kaynakları QGIS'in kurulumundan çözülür.

QGS ve QGZ/ek arşivleri senkron tutulur. Dosyaları
elle adlandırarak farklı sürümde bir QGS ve QGZ çiftini yan yana bırakmak uygun
değildir. QGIS'te düzenleme sonrasında hem proje çifti hem de kaydedilmiş
haritaların sürüm ilişkisi yeniden kontrol edilmelidir.

Harici CARTO XYZ kaynağı yerel dosya yolu değildir. URL'nin varlığı, döşeme
sunucusunun ulaşılabilir olduğu veya canlı kullanım koşullarının onaylandığı
anlamına gelmez. Ana QA web bağlantısını çevrim dışı atlar; harita üretiminde
ağ kullanımı ayrıca `--allow-web-basemap` ile seçilir. HTTP 200 yanıtı tek
başına kullanılabilir harita döşemesi veya görsel kabul kanıtı sayılmaz.

Genel QGIS projesi özgün anahtarsız CARTO URL'sini korur. Dışa aktarmada
`CARTO_BASEMAPS_API_KEY`, canlı QGIS açılışında ise özel anahtar dosyasını
okuyan `open_qgis_with_carto.py` başlatıcısı kullanılabilir. Canlı erişimde
ağ isteği hazırlayıcısı anahtarı yalnız izinli CARTO döşeme isteklerine ekler;
katman URL'leri ve QGS/QGZ değişmez. Başka kullanıcı kendi anahtarını sağlar.
[Canlı erişim kurulumu](carto_live_access.md) ve
[dışa aktarma komutu](qa/map_export_qa.md) bu iki yolu açıklar.
Salt okunur temel QA anahtar istemez; web görünümü ayrıca doğrulanır.

## Salt okunur kontroller

```bash
python3 scripts/python/check_map_layouts.py --check --json
python3 scripts/python/check_portability.py --check
bash scripts/bash/run_canonical_qa.sh --check
```

Düzen kontrolü QGS/QGZ eşliğini, tam 13 düzeni, kilitli katman/stilleri,
lejant bağlantılarını, yerel dosyaları ve 27 harita/atlas dosyasının manifestini
denetler. Katman sağlayıcısının dosya içeriğini gerçekten açması ana QA'daki
PyQGIS kontrolünün işidir; yolun mevcut olması tek başına yeterli sayılmaz.
Bu sürümde 28 yerel katman geçerli bulunmuştur; bir web altlığı tanımlıdır.

Kamu kaynak sürümünün kopyasında bu 28 yerel katman bulunmaz; orada tam kapsam
eksik katmanları hata olarak listeler. Kaynak kopyası açık kapsamla denetlenir:

```bash
python3 scripts/python/check_portability.py --check --scope public-source
```

Bu modda dağıtılmayan katmanlar iki bağımsız yoldan belirlenir: kamu seçim
listesinde bulunmayan katmanlar ve kamu paketleme politikasının hiç seçemeyeceği
katmanlar. İki küme eşit olmalı; her katman kopyada bulunmamalı ve tek tek
`ATLANDI` satırıyla listelenir. Göreli yol, mutlak yol ve proje dışına çıkış
kontrolleri aynen uygulanır. Bu katmanlardan biri kopyada varsa kontrol
başarısız olur ve tam kapsamı önerir.
Ana QA'nın 9. zorunlu kontrolü, düzen ve kayıtlı ürün bütünlüğünü denetler; eksik
veya değişmiş final dosyası başarısızlık (çıkış 1) üretir.
Kontrol sonuçları [harita QA kaydında](qa/map_export_qa.md) tutulur.

2026-10-24 kontrolünde düzen/ürün denetimi 13 düzen ve 27 dosyayı hatasız
doğrulamış; ana canonical QA çıkış 0 ile tamamlanmıştır. Genel dosyalar ve
QGZ'nin gömülü içeriğinde üretim anahtarı eşleşmesi 0'dır. Bu doğrulamalar
canlı web altlığının gelecekte her kullanıcı için otomatik açılacağı iddiası
değildir; canlı kullanım kullanıcının kendi anahtarını gerektirir.

## Veri paketi ve GitHub kapsamı

Göreli yolun geçerli olması, verinin Git deposunda bulunacağı anlamına gelmez.
`.gitignore` büyük ve üçüncü taraf veri dosyalarını depo dışında tutar.
`qgis/`, `data/` ve `outputs/` klasörleri aynı kök altında korunmalıdır.

12 haritalı portable ZIP önceki sürümün referans arşividir; güncel
13 haritalı sürümün GitHub dağıtım paketiyle aynı değildir. Kamuya dağıtılacak
paket, [veri hakları kaydı](data_rights_and_distribution.md) ve
[yayın durumu](../PUBLICATION_STATUS.md) tamamlandığında ayrıca hazırlanır.
Yeni bir portable pakette manifest varsa:

```bash
python3 scripts/python/check_portability.py --check --verify-manifest
```

Paket üretimi ve mevcut yayın kapsamı için [dağıtım rehberine](github_distribution.md)
bakılır; teknik taşınabilirlik veri dağıtım izninin yerine geçmez.

## Proje kimlik alanları ve kayıtlı haritalar

Kamu proje yazar alanı Enes Göker'dir; otomatik kaydeden hesap alanları boştur.
Yalnız bu üç değerin temizlenmesi katman/stil/sayfa tasarımını değiştirmez.
Dışa aktarma manifesti v2, haritaların özgün üretim QGS hash'ini korur ve
güncel QGS/QGZ için dar bir metadata değişimi tanığı ekler. Sabit üç alan
dışındaki bütün XML baytları ve QGZ yardımcı üyeleri doğrulanır. Diğer
proje değişiklikleri bu istisna kapsamında kabul edilmez.
[Doğrulama kapsamı](qa/map_export_qa.md#kimlik-alanları-ve-üretim-kaydı).
