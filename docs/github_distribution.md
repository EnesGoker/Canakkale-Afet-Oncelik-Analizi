# GitHub Yayınlama ve İndirme Rehberi

**Kaynak sürümü kapsamı:** Aşağıdaki raster, harita PDF, atlas ve Word/PDF
yolları tam yerel çalışma çıktısıdır; bu dosyalar kaynak ve analitik özet
sürümünde dağıtılmaz. `outputs/maps/png/` altındaki harita PNG'leri kamu
kapsamındadır. Yerel üretim/kontrol komutları ilgili kanonik veri ve
çıktıların ayrıca bulunmasını gerektirir. [Kamu dosya kapsamı](publication_file_scope.md).

**Geçerli kamu sürümü:** Kaynak kodu, yöntem belgeleri, QGIS proje tanımı,
seçilmiş analitik özetler ve görünür atıflı harita PNG'leri sunulur. Tam veri,
harita PDF'leri, atlas ve Word/PDF raporu dağıtılmaz. Tam yerel paket için aşağıda ayrıca koşullu teknik
akış açıklanır. Güncel kararlar
[ilk yayın dosyası listesinde](../PUBLICATION_STATUS.md), kaynakların resmî
koşulları [veri hakları kaydında](data_rights_and_distribution.md) tutulur.
Mevcut yerel ZIP'in teknik olarak çalışması, paylaşım koşullarının tamamlandığı
anlamına gelmez.

## Dağıtım sözleşmesi

Kaynak sürümü ile tam yerel teknik paketin kapsamı ayrıdır:

| Teslim | İçerik | Kullanım |
|---|---|---|
| Git deposu / Source code ZIP | Son yayın listesinde seçilmiş README, kod, config, belgeler, QGIS proje tanımı ve izin koşulları tamamlanan kamu çıktıları | Portfolyo incelemesi ve kaynak kodu |
| `canakkale-disaster-priority-portable.zip` — yalnız tam yerel teknik paket | Depo içeriği + canonical processed/reference verileri + korunan küçük idari/AFAD kaynakları + bütünlük manifesti | Katmanlarıyla QGIS'te açma, analiz ve tablo QA |

`.gitignore`, `data/processed/`, `data/reference/`, `data/raw/` ve
`data/interim/` veri dosyalarını Git dışında tutar. Klasör yer tutucuları
saklanabilir. Release üreticisi canonical verileri açıkça pakete alır; Git
ignore kurallarını veri seçimi için kullanmaz.

GitHub normal Git depolarında 100 MiB üzerindeki dosyaları engeller.
Bu projedeki bazı GeoPackage ve GeoTIFF dosyaları sınırı aşar. Paylaşım koşulları tamamlanan tam paket ileride
GitHub Release varlığı olarak dağıtılabilir; her varlık 2 GiB altında olmalıdır.
Üretici bu sınırı kontrol eder. Bu, teknik dosya sınırıdır; verilerin dağıtım
koşulları ayrıca sağlanmalıdır.
Kaynaklar: [GitHub dosya sınırları](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github),
[GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

## Kaynak sürümünü indiren kişi için

GitHub'da `Code → Download ZIP`, `git clone` veya sürümün otomatik
`Source code` arşiviyle kaynak ve analitik özet dosyaları edinilir. CSV ve
Markdown sonuçları GIS kurulumu olmadan okunabilir. QGIS proje dosyası
katman/stil/düzen tanımıdır; eksik yerel veri katmanlarını içermez.

Bu kaynak sürümü için tam katmanlı portable ZIP bulunmaz. Harita/rapor
dosyalarına ait belge içi yollar, tam yerel çalışmanın çıktı konumlarıdır.
Tam analiz veya canonical QA için kayıtlı kanonik girdiler ve beklenen
çıktılar ayrıca sağlanmalıdır. [Somut kapsam](publication_file_scope.md).

## Kaynak paketinin bütünlüğü ve yeniden üretimi

Sürüm varlıkları `canakkale-disaster-priority-source.zip` ve aynı adlı
`.sha256` dosyasıdır. İndirilen klasörde:

```bash
shasum -a 256 -c canakkale-disaster-priority-source.zip.sha256
```

Kaynak kökünde Python 3.10+ ile dosya seçimi kontrol edilir:

```bash
python3 scripts/python/build_public_source_release.py --check
```

Yeni bir kaynak paketi üretmek için proje dışında boş bir çıktı yolu verin:

```bash
python3 scripts/python/build_public_source_release.py --build --output-dir ../public-source-build
```

Üretici yalnız pozitif config listesindeki dosyaları kopyalar; veri/görsel
ikili dosyalarını ve Git geçmişini taşımaz. Çıktıda temiz kaynak klasörü,
ZIP, SHA-256 ve dosya başına checksum içeren `public_source_manifest.json`
bulunur. Var olan dolu çıktı klasörünün üzerine yazılmaz. ZIP sıralaması,
zamanları ve dosya izinleri sabittir; aynı girdiler aynı ortamda aynı ZIP'i üretir.

## Tam yerel paketin bütünlüğünü kontrol etme

Bu bölüm yalnız paylaşım koşulları ayrıca tamamlanmış bir tam portable
paket edinildiğinde veya yerelde oluşturulduğunda uygulanır. Dosya adı
`canakkale-disaster-priority-portable.zip` ve yanındaki `.sha256` kaydıdır.
ZIP tamamen çıkarılır; `canakkale-disaster-priority/` kökündeki `qgis/`,
`data/`, `outputs/` birlikte korunur. Proje
`qgis/canakkale_disaster_priority.qgz` ile açılır.

ZIP'in bütünlüğü, indirildiği klasörde macOS/Linux için şu komutla kontrol edilir:

```bash
shasum -a 256 -c canakkale-disaster-priority-portable.zip.sha256
```

Çıkarılan proje kökünde Python 3.10+ ile:

```bash
python3 scripts/python/check_portability.py --check --verify-manifest
```

Windows'ta `py -3 scripts/python/check_portability.py --check --verify-manifest`
kullanılabilir. `portable_manifest.json`, paketteki payload dosyalarının boyut
ve SHA-256 değerlerini içerir; manifest kendisinin hash'ini içermez.

Kontrol, eksik/veri yerine LFS pointer bulunan katmanları ve proje dışına çıkan
kaynak yollarını reddeder. SHA-256 kontrolü manifestte listelenen eksik veya
değiştirilmiş dosyaları bildirir. Manifestte yer almayan ek dosyaları denetlemez;
ZIP'in bütünü yanındaki `.sha256` dosyasıyla kontrol edilir. Dosya doğrulaması
bilimsel doğrulama yerine geçmez.

## Paket üretimi

Tam veri klasörlerinin bulunduğu proje kökünde:

```bash
python3 scripts/python/build_portable_release.py --check
python3 scripts/python/build_portable_release.py --build
```

`--check` paket planını ve QGIS yerel dosya kaynaklarını doğrular; dosya yazmaz.
`--build` ZIP, dahili manifest ve ZIP için `.sha256` dosyası üretir.
Varsayılan çıktı dizini `outputs/temp/releases/` olur ve Git'e dahil edilmez.
Üretici mevcut aynı adlı paketin üzerine yazmayı reddeder; yeni üretim için
başka bir çıktı dizini kullanılabilir:

```bash
python3 scripts/python/build_portable_release.py --build --output-dir outputs/temp/releases-v1
```

Pakete `data/interim/` VRT'leri, işletim sistemi artıkları, Python cache,
veritabanı kilitleri, geçici çıktılar, özel çalışma notları ve özel rapor
kopyaları alınmaz. MIT metni, lisans kapsamı ve yayın durumu
pakete eklenir. Canonical kaynak katmanları
ve harita/veri içerikleri dönüştürülmeden korunur.

Bu üretici yerel tam analiz paketi içindir. AFAD/MTA/JRC/HydroRIVERS gibi
açık kalan dağıtım kayıtları çözülmeden bu ZIP kamuya yüklenmez. Kaynakları
paketten çıkarıp aynı anda “bütün katmanlarıyla eksiksiz açılır” sözü
verilmez; edinim talimatı veya farklı kamu paketinin kapsamı ayrıca
kesinleştirilecektir.

## Temiz kaynak deposu ve sürüm

Kamu deposu, [dosya kapsamındaki](publication_file_scope.md) kaynaklar ve
seçilmiş analitik özetlerden hazırlanır. Özel çalışma Git geçmişi veya tam
teknik portable ZIP bu sürüme aktarılmaz. Yalnız temiz kamu klasöründe
oluşturulan geçmiş yayımlanır; `.gitignore` geçmişteki özel dosyaları silmez.

Depo ve sürüm açıklaması; kanonik verilerin, harita PDF/atlas ve raporun bu
sürümde bulunmadığını açıkça belirtmelidir. Kaynak kodu arşivini tam veri
paketi veya katmanlarıyla eksiksiz QGIS projesi olarak sunmayın. Kod lisansı,
model/belge ve üçüncü taraf kaynak kapsamı ayrı korunur.

Gönderimden sonra yayımlanan kaynak commit'i yeniden indirilip dosya
seçimi, bütünlük, yerel Markdown bağlantıları ve QGS satır sonları kontrol
edilir. Kaynak kopyasında tam canonical QA'nın eksik girdiler nedeniyle
çalışmaması, kaynak arşivinin bozukluğu olarak yorumlanmaz.

Tam veri/görsel sürümü ileride ayrıca oluşturulursa kaynak koşulları,
görünür atıflar ve gerekli erişim düzeni yeniden değerlendirilir; yerel tam
ZIP'in teknik testi bu koşulların yerine geçmez.

## Rapor ve lisans kapsamı

Düzenlenebilir kamu raporunun ana kaynağı
`outputs/report/canakkale_disaster_priority_public_report.docx`
dosyasıdır. 18 sayfalık PDF (`outputs/report/canakkale_disaster_priority_public_report.pdf`)
raporun okuma kopyasıdır. Pages dosyaları yalnız yerel arşivde tutulur; kamu
Git ve portable paket seçimine alınmaz.

Akademik DOCX üreticisi ayrı bir 12 haritalı hedef oluşturur; hazır kamu Word
raporunu yeniden üretmez. `a11y_report.json`, içinde adı yazan akademik DOCX
üreticisinin kontrol kaydıdır; kamu Word/PDF raporunun doğrulaması değildir.
Kamu raporunun kaynak, checksum ve sürüme özgü kontrolleri
[rapor manifestinde](../outputs/report/public_report_manifest.json) tutulur.

Özgün `scripts/` yazılımı [MIT](../LICENSE) kapsamındadır. Rapor, belgeler,
veri ve haritalar bu lisansa otomatik dahil değildir; bkz.
[lisans kapsamı](../LICENSE_SCOPE.md). Kaynak envanteri atıf seceresini,
veri hakları kaydı paylaşım koşullarını sağlar. Kamu Word/PDF raporunun
gömülü haritaları da son yayın kontrolüne tabidir.
