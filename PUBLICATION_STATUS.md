# İlk yayın dosyası listesi

Güncelleme: **3 Kasım 2026 — kaynak sürümü `v0.2.0`.** İlk kaynak sürümü
`v0.1.0` 30 Ekim 2026'da yayımlandı.

Kaynak sürümünün içeriği: Python/Bash kodu, model tanımları, yöntem/QA
belgeleri, kaynak atıfları, QGIS proje şablonu ve seçilmiş indirgenmiş
analiz tabloları. Pozitif dosya listesi
[`config/public_source_release_v1.json`](config/public_source_release_v1.json)
içindedir. Kamu paketi bu listeden ayrı temiz klasöre hazırlanır; yerel
çalışma deposunun geçmişi taşınmaz.

Harita PDF'leri, atlas, Word/PDF rapor, canonical raster/vektör veriler ve tam
portable ZIP bu sürüme dahil değildir; harita görselleri yalnız PNG olarak sunulur. QGIS şablonu verileri içermez;
veriye bağlı analiz ve tam QA için canonical girdiler ayrıca gereklidir.
Tam yerel çalışma sürümünün teknik kontrolleri bu kapsamdan bağımsız
olarak korunur. [Somut dosya seçimi](docs/publication_file_scope.md).

Bir dosyanın yerel Git'te izlenmesi veya portable ZIP'e girmesi, kamu
paketine girdiği anlamına gelmez. Kamu harita görselleri `01`–`14` PNG
dosyalarıdır; her biri görünür ortak ve tema atıflarını taşır ve SHA-256
değeriyle paket seçiminde sabitlenir. Kaynak bildirimleri ve ilgili OSM erişim
düzeni [statik bildirimlerde](docs/static_map_attributions.md) açıklanır.

Tam QA; ayrı GDAL 3.12.3 / NumPy 2.4.4 (Accelerate) ortamı ve QGIS 3.44.15
okuyucusuyla geçmiştir. GDAL 3.13.3'ün varsayılan eğim/taşkın yeniden örneklemesi
eski reçetelerden farklıdır; ana MCDA aynı kalır. [Çalışma ortamı uyumluluğu](docs/qa/runtime_compatibility.md).

| Dosya / grup | İçerik rolü | Sürüm kapsamı / sonraki koşul |
|---|---|---|
| `scripts/`, `.github/workflows/`, `requirements.txt`, `.gitignore`, `.gitattributes` | Kaynak deposu | Özgün kod MIT; son kod ve temiz klasör kontrollerinden geçecek. |
| `README.md`, `README.tr.md`, `LICENSE`, `LICENSE_SCOPE.md`, bu liste, `docs/` | Kaynak deposu | İngilizce ve Türkçe README sürümleri karşılıklı dil bağlantılarıyla sunulur. Belgelerin seçilmiş kaynak sürümü lisans kapsamını ve kaynak bağlantılarını korur. Ham veri örnekleri dağıtılmaz; tam dosya listesi kaynak sürümü config dosyasındadır. |
| `config/` | Kaynak deposu | Mevcut model tanımları korunacak; ayrı açık veri lisansı verilmedi. |
| `qgis/*.qgs`, `qgis/*.qgz` | Kaynak deposu ve uygun veri paketi | Göreli yerel yollar korunur; yerel katmanları içermez. 14 düzen, 28 harita/atlas dosyası (14 PNG, 01–13 PDF'leri, atlas) ve statik çıktı üretimi teknik olarak doğrulanmıştır. Her düzen ortak ve temaya özgü kaynak bildirimlerini görünür bir etiket olarak taşır. Kamu proje dosyası erişim anahtarı içermez. |
| `outputs/report/canakkale_disaster_priority_public_report.docx` | Düzenlenebilir ana kamu raporu / yayın adayı | Microsoft Word biçimindeki rapor 13 coğrafi harita, bir korelasyon figürü ve 1–6, A1, B1 numaralı sekiz veri tablosunu içerir. Tam dosya ilk dar seçkiye dahil değildir; ilgili şekil/ekler [kapsam kaydında](docs/publication_file_scope.md) ayrılır. Kamu kişisel bilgi kapsamı ad, üniversite ve derstir; öğrenci numarası ve danışman bilgisi bu kapsamın dışındadır. Dosya sürümü ve kontroller `outputs/report/public_report_manifest.json` ile izlenir. |
| `outputs/report/*.pages` | Yalnız yerel arşiv / yedek | Kamu Git ve portable paket seçimine alınmaz. Düzenlenebilir ana kaynak Word'dür. |
| `outputs/report/canakkale_disaster_priority_public_report.pdf` | Kamu raporunun okuma kopyası / yayın adayı | PDF 18 sayfadır; tam raporun kaynak kapsamı ayrıca geçerlidir ve dosya ilk dar seçkiye dahil değildir. Güncel Word/PDF dosyalarının kaynak, checksum, sayısal kontrol ve teknik sınırlılık kaydı `outputs/report/public_report_manifest.json` içindedir; başka bir rapor sürümünün kontrol sonucu bu dosyalara otomatik uygulanmaz. |
| `outputs/maps/png/` | Kamu harita görselleri | `01`–`14` PNG dosyaları görünür ortak ve tema atıflarıyla yayımlanır; her haritanın kaynakları [statik bildirimlerde](docs/static_map_attributions.md). AFAD ve MTA verisinden türetilen görseller için yazılı izin alınmamıştır; JRC/CEMS, HydroRIVERS ve USGS Vs30 için açık kalan lisans/türev kapsamı da çözülmemiştir. Yayın bu bilinerek yapılmıştır ve hak sahibinin talebi halinde ilgili görsel kaldırılır. Harita PDF'leri (`outputs/maps/pdf/`) ve atlas bu sürüme dahil değildir. [Dosya kapsamı](docs/publication_file_scope.md). |
| `outputs/atlas/` | Tam atlas; ilk seçkinin dışında | 01–13 PDF'lerinden oluşan 13 sayfalık atlasın teknik QA kaydı korunur (`14` yalnız PNG'dir); içindeki ilgili şekiller için kaynak/yayın kapsamı ayrıdır. Teknik kabul bütün atlas için genel yayın izni değildir. |
| `outputs/tables/` ve diğer sayısal model çıktıları | Dosya bazında ayrı seçim | Seçilmiş alan/ilçe/duyarlılık/korelasyon özetleri kaynak sürümündedir. Klasör bütünü dahil edilmez; ana MCDA/senaryo TIFF dosyaları ve yan dosyaları bu kapsamın dışındadır. |
| `outputs/report/a11y_report.json` | İlgili akademik DOCX ile birlikte, gerekirse | Ayrı 12 haritalı akademik DOCX üreticisinin kontrol kaydıdır; kamu Word/PDF raporunun doğrulaması değildir. |
| `data/raw/`, `data/interim/` | Git dışında | Mevcut veriler korunur. İzinli küçük kaynaklar veya edinim talimatı, kaynağa göre seçilecek. |
| `data/processed/`, `data/reference/` | İlk kamu kapsamı dışında; yerel analiz | Ayrı veri paketi, kaynağa özgü koşullarla seçilir. Beş açık ailedeki 27 somut yol [dosya listesinde](docs/publication_file_scope.md) ayrılmıştır. Canonical analiz girdisi olmak yeniden dağıtım izni değildir. |
| `data/**/.gitkeep` | Kaynak deposu | Klasör yapısını temsil edebilir; veri içermez. |
| `outputs/temp/`, eski portable ZIP'ler, cache, kilit ve geçici dosyalar | Yalnız yerel çalışma | Kamu Git/ZIP seçimine alınmaz. Kamu dağıtımı yalnız son dosya seçimine göre oluşturulan paketle yapılır. |

## Veriler için ilk dağıtım kararı

Resmî bağlantılar ve kapsamın ayrıntısı:
[veri hakları ve dağıtım kaydı](docs/data_rights_and_distribution.md).

| Kaynak ailesi | Kamu veri paketi için ilk karar |
|---|---|
| HGM sınırları | Ticari olmayan kullanım/dağıtım ve HGM atfı; sınırların resmî olmadığının belirtilmesi. İlçe adlarındaki OSM katkısı ayrıca anılacak. |
| Copernicus DEM, ESA WorldCover, CLMS TCD, WorldPop | Kaynağa özgü lisans/bildirim ve değişiklik açıklamaları eklenerek paket adayı. Yerel sürümün bilinmeyen ayrıntıları tahmin edilmeyecek. |
| Microsoft binaları ve OSM katmanları | Microsoft lisans metni, OSM ODbL bildirimleri ve hibrit veritabanı kapsamı tamamlanacak. Tek lisans altında varsayılmayacak. |
| AFAD TDTH ve MTA tarihsel fay verisi | Yerel edinim tarihi/ayrı izin kaydı bilinmiyor. Kaynak ve sayısal türevler (workbook, nokta, IDW, fay GeoPackage, skor rasterları) dağıtılmaz. Bu verilerden türetilen statik harita görselleri (`01`, `02`, `05`, `13`, `14`) atıfla yayımlanır; yazılı izin alınmamıştır ve izin ileri sürülmez. Hak sahibinin talebi halinde ilgili görsel kaldırılır. |
| JRC/CEMS taşkın | Katalog/README ODbL ve copyright CC BY 4.0 kayıtları uyuşmuyor; yerel release bilinmiyor. Taşkın ve skor TIFF dosyaları dağıtılmaz. `07` görseli lisans adı yerine kaynak, telif ve DOI atfıyla yayımlanır; lisans uyuşmazlığı çözülmemiştir. |
| HydroRIVERS ve OSM hidrografya hibriti | HydroSHEDS özel lisansı standalone/türev dağıtımı ayırır; hibrit ve skor dağıtılmaz. `08` görseli HydroSHEDS Ek B bildirimi ve OSM atfıyla yayımlanır; lisansın türev dağıtım hükmünün statik görsele uygulanma kapsamı çözülmemiştir. Saf OSM gap-fill, ODbL koşullarıyla ayrı adaydır. |
| USGS Global Vs30 Mosaic | Yerel release/bölgesel bileşen kapsamı bilinmiyor; extract ve skor dağıtılmaz. Depodaki varsayılan CC0 bütün mozaiğin her bileşenine otomatik atanmaz. `04` görseli USGS ve Heath vd. (2020) atfıyla yayımlanır. |
| CARTO | Veri paketi olarak tile önbelleği dağıtılmaz. Statik harita atfı ile canlı hizmet erişimi ayrı kontrol edilir. |

Bu durumlar veri kullanımının ihlal olduğu yönünde bir hüküm değildir.
Eksik olan, bazı kaynakların bu kamu dağıtımı için yeterli koşul kaydıdır.
Yerel analiz girdileri silinmez veya lisans çalışması gerekçesiyle değiştirilmez.

## Paket kapsamı

`build_portable_release.py --check/--build`, teknik paketleme ve bütünlük
aracıdır. Yerelde üretilen tam veri paketinin kapsamı, yukarıdaki kamu
paylaşımı kararlarından ayrıdır; teknik paket üretimi veri paylaşım izni
vermez. Kamu paketi, kaynaklara özgü dağıtım koşullarıyla uyumlu dosyalardan
oluşmalıdır. Özgün kodun MIT lisanslı olması veri, harita veya rapor içeriğinin
tamamını MIT kapsamına almaz. Tam Word/PDF ve atlas korunur; dar kamu
seçimine alınmamak raporun tamamına genel bir yasak anlamına gelmez.
