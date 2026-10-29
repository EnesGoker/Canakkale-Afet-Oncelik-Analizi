# Veri hakları ve kamuya dağıtım kapsamı

Kontrol tarihi: **29 Ekim 2026**.

Bu belge, üçüncü taraf kaynakların kaynak deposu, statik görsel ve sayısal
veri paketi için dağıtım koşullarını ayırır. Ürün kimlikleri ve analizdeki
roller [veri kaynak envanterinde](data_source_inventory.md), teknik paket
yapısı [dağıtım rehberinde](github_distribution.md) açıklanır.

Belirsiz bir paylaşım koşulu, mevcut çalışmanın hukuka aykırı olduğu veya
analitik açıdan kusurlu olduğu sonucunu vermez. Dağıtım kapsamı, kaynak
koşullarına ve sunulan dosyanın niteliğine göre belirlenir. Somut dosya seçimi [ilk kamu paylaşım kapsamındadır](publication_file_scope.md):
geçerli ilk sürüm kaynak deposu ve dosya bazında seçilmiş analitik
özetlerdir. Altı haritalık seçki, aşağıdaki koşullar tamamlandığında ayrı
bir sonraki adaydır; haritalar ve tam sayısal veri paketi mevcut kaynak
sürümüne dahil değildir.

Depodaki özgün kod için MIT kapsamı [LICENSE_SCOPE.md](../LICENSE_SCOPE.md)
belgesinde ayrılır. **MIT, üçüncü taraf verilerini veya bunlardan üretilmiş
bütün çıktıları kendiliğinden kapsamaz.** Kaynak atfı ile yeniden dağıtım izni
de farklı konulardır.

## Durumların anlamı

- **Koşullu:** Resmî kaynakta paylaşımı destekleyen koşullar bulundu. Atıf,
  lisans metni, değişiklik bildirimi veya kullanım kapsamı uygulanmalıdır.
- **Çözümlenmemiş:** Yerel sürüme uygulanacak koşul veya türev kapsamı henüz
  doğrulanamadı; bu bir kesin yasak ya da ihlal hükmü değildir.
- **Karma veri:** Birleştirilmiş dosyada birden fazla kaynağın koşulları
  değerlendirilir. Kaynaklardan birinin lisansı diğerinin yerine geçmez.

**2026'da erişilen güncel bir koşul sayfası, eski bir yerel dosyanın aynı
koşulla edinildiğinin kanıtı değildir.** Kesin indirme tarihi, kaynak paket
kimliği veya lisans kaydı bulunmayan yerlerde bu sınır özellikle korunur.

| No | Kaynak ailesi | Kamu dağıtımı için mevcut durum |
|---:|---|---|
| 1 | HGM idari sınırlar | Koşullu; ticari olmayan kullanım ve dağıtım, atıf |
| 2 | AFAD TDTH | Çözümlenmemiş; workbook edinimi ve türev paylaşım kapsamı |
| 3 | MTA diri fay | Çözümlenmemiş; tarihsel sayısal paket koşulları |
| 4 | Copernicus DEM GLO-30 | Koşullu; ürüne özel kaynak ve sorumluluk bildirimleri |
| 5 | JRC/CEMS RP100 taşkın | Çözümlenmemiş; resmî lisans metinleri çelişkili, yerel sürüm eksik |
| 6 | WorldPop Türkiye 2020 | Koşullu; CC BY 4.0 ve değişiklik bildirimi |
| 7 | USGS Global Vs30 Mosaic | Çözümlenmemiş; extract sürümü ve bölgesel bileşen kapsamı |
| 8 | Microsoft bina izleri | Koşullu; CDLA Permissive 2.0, OSM hibriti ayrıca incelenecek |
| 9 | OpenStreetMap / Geofabrik | Koşullu; ODbL, atıf ve türev veritabanı değerlendirmesi |
| 10 | HydroRIVERS v1.0 | Çözümlenmemiş; standalone/türev ayrımı ve OSM hibriti |
| 11 | ESA WorldCover 2021 v200 | Koşullu; CC BY 4.0 ve ürün atfı |
| 12 | CLMS ağaç örtüsü 2021 | Koşullu; CLMS kaynak ve değişiklik bildirimi |
| 13 | CARTO Positron | Statik harita için koşullu; canlı servis erişimi ayrıca incelenecek |

## 1. HGM — Türkiye Mülki İdare Sınırları

**Ürün ve resmî koşullar:** [HGM ürün 232](https://www.harita.gov.tr/urun/turkiye-mulki-idare-sinirlari/232).

**Yerel kanıt:** AOI ve ilçe geometrileri HGM kaynaklıdır. Ham il/ilçe XML
başlığında `il_ilce_2018` görülür; metadata tarihleri kesin ürün sürümü veya
indirme tarihi kabul edilmez. İlçe adlarında OSM destekli manuel aktarım da
kaynak envanterinde kayıtlıdır.

- **Ham veri:** Ürün sayfası, ticari faaliyetler dışında kullanım ve dağıtıma
  HGM atfıyla izin verir. Bu koşul sınırsız ticari yeniden kullanım lisansı
  değildir; telif HGM'de kalır.
- **İşlenmiş/türev veri:** AOI ve ilçe dosyalarında HGM kökeni, ticari olmayan
  kapsam ve resmî sınır niteliği taşımadığı bilgisi korunmalıdır. MIT/CC0 gibi
  genel bir veri lisansı verilmez.
- **Harita/rapor:** Ticari olmayan öğrenci portföyü kapsamında HGM atfı ve
  sınırların gösterim amaçlı olduğu açıklamasıyla değerlendirilebilir.

**Uygulama:** HGM ürün bağlantısını ve işlenmiş geometri açıklamasını ekle;
ilçe adları için OSM atfını da koru. Son kamu paketinin kullanım kapsamını bu
koşula göre belirle.

## 2. AFAD — Türkiye Deprem Tehlike Haritası parametreleri

**Ürün:** [AFAD TDTH açıklaması](https://www.afad.gov.tr/turkiye-deprem-tehlike-haritasi).
**Koşul:** [İnteraktif uygulamanın yasal uyarısı](https://tdth.afad.gov.tr/TDTH/loginControl.xhtml).

**Yerel kanıt:** PGA nokta tablosu, nokta katmanı ve IDW yüzeyinin kaynak
ailesi TDTH'dir. Yerel workbook'un kesin edinim URL'si/sürümü kayıtlı değildir;
Office metadata tarihi veri sürümü olarak kullanılmaz. Edinim tarihi ve ayrı
izin kaydı bilinmiyor; bu alanlar tahmin edilmez.

- **Ham veri:** Uygulama uyarısı, kapsamındaki veri/belgelerin çoğaltılması,
  dağıtılması ve yayımlanması için atıf yanında yazılı izin şartı içerir. Yerel
  workbook'un doğrudan mevzuat ekinden mi uygulamadan mı geldiği ve varsa
  ayrı kullanım izni kaydı korunmamıştır.
- **İşlenmiş/türev veri:** Projedeki IDW yüzeyi resmî AFAD raster ürünü
  değildir. Nokta, IDW ve skor dosyalarının kamuya dağıtımı için uygulanabilir
  açık türev izni bu araştırmada doğrulanmamıştır.
- **Harita/rapor:** Öğrencinin kendi haritası AFAD posterinin kopyasıyla aynı
  şey değildir; fakat bu ayrım tek başına açık yayın izni oluşturmaz. Yerel
  veri kaynağına uygulanacak kapsam ayrıca belirlenmelidir.

**Dağıtım kararı:** Workbook, CSV, nokta, IDW ve skor dosyaları ilk kamu
paketinde yer almaz. `05_deprem_pga_skoru` haritası için de genel yayın izni
ileri sürülmez. AFAD atfı, özgün IDW açıklaması ve yöntem belgeleri korunur;
bu ayrım çalışmanın bütün metnine veya sonuçlarına otomatik yasak getirmez.

## 3. MTA — tarihsel Türkiye Diri Fay Haritası sayısal verisi

**Tarihsel ürün bağlantısı:** [Sayısal diri fay haritası](https://www.mta.gov.tr/v3.0/bilgi-merkezi/turkiye-diri-fay-haritasi-sayisal).
**İlgili resmî koşullar:** [Yerbilimleri portalı yasal uyarısı](https://yerbilimleri.mta.gov.tr/yasal-uyari.aspx),
[ayrı 2026 ürünü](https://www.mta.gov.tr/v3.0/hizmetler/yenilenmis-diri-fay-haritalari).

**Yerel kanıt:** Envanter ve yöntem notu kaynağı 2013/2014 paketi olarak
kaydeder. İşlenmiş GeoPackage içinde kesin sürüm/lisans kaydı bulunmamış;
ham paket bu çalışma girdileri arasında korunmamıştır.

- **Ham veri:** Portal uyarısı atıf ve yazılı yayın/dağıtım izni koşulları
  içerir. Bunun tarihsel indirilebilir pakete uygulanma kapsamını doğrulayan
  eksiksiz edinim kaydı yoktur.
- **İşlenmiş/türev veri:** Tarihsel fay kesiti ve mesafe skorunun açık kamu
  dağıtımına ilişkin koşul henüz belirlenmemiştir. Güncel 2026 ürünü farklı
  bir sürümdür; onun kısıtları eski pakete geriye dönük varsayılmaz.
- **Harita/rapor:** Portal görselleri ile tarihsel veriden öğrencinin ürettiği
  harita ayrılır. İkincisinin kapsamı tarihsel paket koşulu veya uygun izinle
  netleştirilmelidir; bütün türevler otomatik yasak sayılmaz.

**Dağıtım kararı:** Fay GeoPackage ve yakınlık skoru ilk kamu paketinde
yer almaz. `01` ve `02` QGIS düzenlerinde gerçek fay çizgisi de bulunduğundan
bu görseller için genel yayın izni ileri sürülmez. 2013/2014 kaynak kaydı
korunur; eski veriye 2026 bibliyografisi veya lisansı aktarılmaz.

## 4. Copernicus DEM — GLO-30

**Ürün:** [Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM).
**Koşul:** [WorldDEM-30 lisansı](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf).

**Yerel kanıt:** DEM ve eğim QA belgeleri GLO-30 ailesini kaydeder; kesin
release ve ham karo kimlikleri korunmamıştır. 30 m ürün koşulu, ayrı EEA-10
ürününe uygulanmaz.

- **Ham veri:** Lisans; çoğaltma, dağıtma ve kamuya iletim hakları verir.
  Madde 6'daki bildirimler ve sonraki kullanıcılara aktarılacak yükümlülükler
  uygulanmalıdır.
- **İşlenmiş/türev veri:** Uyarlama ve birleştirmeye izin verilir. Kesilmiş
  DEM, eğim ve ilgili türevler için değiştirilmiş veri bildirimi gerekir.
- **Harita/rapor:** İlgili kaynak bildirimleriyle kullanılabilir; kurumlarca
  resmen desteklenmiş çalışma izlenimi verilmez.

**Uygulama:** Genel bir “Copernicus” etiketi yerine resmî lisansın **6(b)**
değiştirilmiş veri bildirimini ve **6(c)** sorumluluk bildirimini esas al;
**6(e)** sonraki kullanıcı yükümlülüklerini veri paketi bildirimlerine taşı.
Uzun zorunlu metinler burada yeniden yazılmamıştır; lisansa bağlantı verilmiştir.

## 5. JRC/CEMS — Avrupa ve Akdeniz RP100 taşkın derinliği

**Ürün:** [JRC veri kataloğu](https://data.jrc.ec.europa.eu/dataset/1d128b6c-a4ee-4858-9e34-6210707f3c81).
**Koşul kaynakları:** [Resmî README](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard/README.txt),
[aynı dizinin copyright bildirimi](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard/copyright.txt).

**Yerel kanıt:** [Flood QA](qa/flood_qa.md), kaynak adını
`Europe_RP100_filled_depth.tif` olarak korur. Kesin release/yıl yoktur; bu ad,
güncel v3.1.1 dosyasıyla birebir sürüm eşleşmesini kanıtlamaz.

- **Ham veri:** Güncel katalog ve README A02, **ODbL 1.0** belirtirken
  README'nin bağladığı copyright dosyası **CC BY 4.0** belirtir. İki lisans da
  yeniden kullanımı düzenler; çelişki giderilmeden tek lisans kesinleştirilmez.
- **İşlenmiş/türev veri:** CC BY yorumunda atıf/değişiklik bildirimi; ODbL
  yorumunda ayrıca türev veritabanı yükümlülükleri gündeme gelebilir. Skorun
  bütün haklarının proje sahibinde olduğu varsayılmaz.
- **Harita/rapor:** Kaynak ve değişiklikler belirtilir; ODbL kapsamı geçerliyse
  harita ile arkasındaki türev veritabanının yükümlülükleri ayrı ele alınır.

**Dağıtım kararı:** İşlenmiş taşkın ve skor TIFF dosyaları ilk kamu
paketinde yer almaz. Resmî metinler kendiliğinden çift lisans seçeneği sayılmaz;
`07_taskin_skoru` görseli de bu lisans/türev kapsamı açıklanmadan onaylı
yayın sayılmaz. Kaynak DOI'si korunur:
[10.2905/1D128B6C-A4EE-4858-9E34-6210707F3C81](https://doi.org/10.2905/1D128B6C-A4EE-4858-9E34-6210707F3C81).

## 6. WorldPop — Türkiye 2020 constrained UN-adjusted

**Ürün:** [Resmî Türkiye dosya dizini](https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/2020/BSGM/TUR/).
**Koşul ve kaynakça:** [WorldPop WP00685 koleksiyonu](https://hub.worldpop.org/doi/10.5258/SOTON/WP00685),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

**Yerel kanıt:** [Nüfus yöntem notunda](methodology/population_data_methodology_note.md)
adı verilen `tur_ppp_2020_UNadj_constrained.tif`, resmî dizinde mevcuttur.
Ürün Türkiye 2020 BSGM constrained/UN-adjusted ailesidir; ayrı Türkiye 2021
WOPR/COD-PS ürünüyle değiştirilmez. Kaynak dosya checksum/indirme tarihi yoktur.

- **Ham veri:** CC BY 4.0 kapsamında atıf ve lisans bilgisiyle paylaşılabilir.
- **İşlenmiş/türev veri:** Kesme, yeniden örnekleme ve log-skor dönüşümlerini
  belirterek paylaşılabilir; kaynak ve lisans bilgisi korunur.
- **Harita/rapor:** WorldPop / University of Southampton, 2020 ürün tanımı ve
  ilgili DOI ile kaynak gösterilir.

**Uygulama:** Dosya adını ve WP00685 DOI'sini veri bildirimine ekle;
değişiklikleri kaydet. Kaynakça için Bondarenko ve diğerleri (2020) koleksiyon
kaydını kullan.

## 7. USGS — Global Vs30 Mosaic

**Ürün:** [USGS Vs30 Models and Data](https://earthquake.usgs.gov/data/vs30/).
**Koşul kanıtları:** [İlgili USGS deposu lisansı](https://github.com/usgs/earthquake-global_vs30/blob/master/LICENSE.md),
[bölgesel kaynakları açıklayan README](https://github.com/usgs/earthquake-global_vs30/blob/master/README.md),
[USGS veri lisanslama ilkeleri](https://www.usgs.gov/data-management/data-licensing).

**Yerel kanıt:** [VS30 yöntem notu](methodology/vs30_data_methodology_note.md),
Map Viewer/Extraction Tool üzerinden `vs30_mosaic` katmanının 30 arc-second
extract'ini kaydeder. Kesin yıl/release bilinmez.

- **Ham veri:** İlgili resmî depo, aksi belirtilmeyen kapsam için dünya
  çapında CC0 bildirir. Depo farklı kurumlardan bölgesel haritalar da içerir;
  bu bilgi tek başına bilinmeyen extract'in her bileşenini kesinleştirmez.
- **İşlenmiş/türev veri:** Yerel kesit ve zemin skoru için kaynak sürümü ile
  ilgili bölgesel bileşen kapsamı doğrulanarak lisans kararı verilir.
- **Harita/rapor:** USGS Global Vs30 Mosaic ve Heath ve diğerleri (2020)
  kaynağı belirtilir; sürümü bilinmeyen extract'e yeni bir release'in lisansı
  veya tarihi atanmaz.

**Dağıtım kararı:** Yerel VS30 ve zemin skoru TIFF dosyaları ilk kamu
paketinde yer almaz; `04_zemin_kosulu_skoru` görseli koşullu inceleme adayıdır.
Genel USGS kamu malı/CC0 yaklaşımı bütün üçüncü taraf bileşenlere otomatik
genişletilmez. Bilinmeyen yıl/release bilinmiyor olarak kalır.

## 8. Microsoft — GlobalML BuildingFootprints

**Ürün:** [Resmî Microsoft deposu](https://github.com/microsoft/GlobalMLBuildingFootprints).
**Koşullar:** [Veri lisans bildirimi](https://github.com/microsoft/GlobalMLBuildingFootprints/blob/main/LICENSE),
[CDLA Permissive 2.0](https://cdla.dev/permissive-2-0/).

**Yerel kanıt:** Bina katmanının Microsoft birincil kaynak ve OSM gap-fill
bileşimi olduğu envanterde yazılıdır. Ham quadkey/release/edinim tarihi yoktur;
güncel depo tarihi yerel veri tarihi olarak kullanılmaz.

- **Ham veri:** Microsoft verisi kullanılabilir, değiştirilebilir ve
  paylaşılabilir; paylaşılan veriyle CDLA Permissive 2.0 metni sağlanmalıdır.
- **İşlenmiş/türev veri:** Değiştirilmiş veri için de anlaşma metni verilir.
  Lisansın hesaplama sonuçları için ek kısıt getirmemesi, hibritteki OSM
  yükümlülüklerini kaldırmaz.
- **Harita/rapor:** Microsoft kaynak bilgisi korunur; OSM katkısı bulunan
  çıktılarda OSM atfı ayrıca uygulanır.

**Paket koşulu:** Lisans metni veri paketi bildirimlerinde sağlanmalıdır.
Hibrit GeoPackage'ın tamamı yalnız CDLA lisanslı sayılmaz; OSM ile birleşimin
lisans kapsamı ayrıca belirlenmelidir.

## 9. OpenStreetMap / Geofabrik

**Ürün:** [Geofabrik indirme ve lisans açıklaması](https://www.geofabrik.de/data/download.html).
**Koşullar:** [OSM telif/lisans sayfası](https://www.openstreetmap.org/copyright),
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/),
[OSMF atıf rehberi](https://osmfoundation.org/wiki/Attribution_Guidelines),
[üretilmiş eser rehberi](https://osmfoundation.org/wiki/Licence/Community_Guidelines/Produced_Work_-_Guideline).

**Yerel kanıt:** Yol, yerleşim, POI, ulaşım ve arazi kullanımı katmanları;
bina/akarsu gap-fill bileşenleri ve ilçe adı aktarımı belgelenmiştir. Extract
tarihi korunmamıştır.

- **Ham veri:** OSM/Geofabrik verileri ODbL ve kaynak atfıyla yeniden
  dağıtılabilir; lisans bildirimi birlikte verilmelidir.
- **İşlenmiş/türev veri:** Kesilmiş/filtrelenmiş vektörler veritabanıdır.
  ODbL türev veritabanı, paylaşım ve erişim yükümlülükleri değerlendirilir.
  Microsoft bina ve HydroRIVERS akarsu hibritleri ayrı incelenir; ODbL bütün
  bağımsız verilere veya proje koduna otomatik yayılmaz.
- **Harita/rapor:** Görüntü olarak sunulan haritalar genellikle üretilmiş
  eserdir; haritanın lisansı ile arkasındaki türev veritabanı farklıdır.
  Türev veritabanına erişim sağlama yükümlülüğü devam edebilir. Sayısal analiz
  rasterı yalnız TIFF olduğu için otomatik üretilmiş eser sayılmaz.

**Uygulama:** `© OpenStreetMap contributors` atfı ve
[OSM telif sayfası](https://www.openstreetmap.org/copyright) bağlantısını
ekle; basılı/PDF bağlamında URL okunabilir olsun. Veri alt kümelerinde ODbL
adı/bağlantısı ve gerekliyse türev veriye erişim düzeni sağla.

## 10. HydroRIVERS — v1.0 / v10

**Ürün:** [HydroRIVERS](https://www.hydrosheds.org/products/hydrorivers).
**Koşullar:** [HydroRIVERS v1.0 teknik belgesi, bölüm 4](https://data.hydrosheds.org/file/technical-documentation/HydroRIVERS_TechDoc_v10.pdf),
[bağlı HydroSHEDS lisansı, Ek A](https://data.hydrosheds.org/file/technical-documentation/HydroSHEDS_TechDoc_v1_4.pdf).

**Yerel kanıt:** Envanter v10 kaydını; referans dosyaları ise bağlam ve AOI
kesitlerini korur. Temiz hibrit, OSM waterways katkısı içerir. Ürünün koşulu
ayrı HydroATLAS/CC BY ürünlerinden alınmaz.

- **Ham veri:** Bağlı özel lisansın **2.1.2** bölümü, lisanslı materyalin
  standalone ürün olarak dağıtımını sınırlar. Kaynak/bağlam/AOI dosyaları
  otomatik serbest dağıtım adayı kabul edilmez.
- **İşlenmiş/türev veri:** Aynı bölüm, türev çalışmaya dahil dağıtımı en az
  aynı koruyuculukta son kullanıcı koşullarına bağlar. Kesilmiş veri, OSM
  hibriti ve skorlarda bu kapsam ayrıca değerlendirilmelidir. OSM'nin ODbL
  koşullarıyla uyum henüz kesinleştirilmemiştir.
- **Harita/rapor:** Atıf ve türev kullanım koşulları birlikte ele alınır.
  “Eğitimde ücretsiz kullanım” açıklaması bütün türev dağıtımlarına sınırsız
  izin anlamına gelmez.

**Uygulama:** HydroSHEDS lisansının **Ek B** kaynak ve garanti bildirimi
gerekliliklerini esas al; Lehner ve Grill (2013),
[10.1002/hyp.9740](https://doi.org/10.1002/hyp.9740) kaynağını belirt.
HydroRIVERS context/AOI ve birleştirilmiş hidrografya/skor dosyaları ilk
kamu paketinde yer almaz. Ayrı saf OSM gap-fill dosyası, ODbL koşullarıyla
ayrı bir veri adayıdır; ilk görsel/kod kapsamına otomatik eklenmez.
`08_hidrografya_yakinlik_skoru` için statik eser atfı ile ODbL 4.6 kapsamındaki
türev veritabanı veya değişiklik yöntemine erişim düzeni birlikte ele alınır.

## 11. ESA — WorldCover 2021 v200

**Ürün ve atıf:** [ESA WorldCover veri erişimi](https://esa-worldcover.org/en/data-access).
**Koşul:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

**Yerel kanıt:** [Arazi örtüsü QA](qa/landcover_qa.md), 2021 v200
`N39E024` ve `N39E027` karo adlarını kaydeder; ürün/sürüm eşleşmesi açıktır.

- **Ham veri:** Atıf ve lisans bilgisiyle paylaşılabilir.
- **İşlenmiş/türev veri:** Kesme, yeniden projeksiyon ve skor dönüşümleri
  belirtilerek paylaşılabilir; kaynak atfı korunur.
- **Harita/rapor:** Ürünün haritalar için istediği ESA/Copernicus kaynağı
  ve 2021 referans yılı belirtilir.

**Uygulama:** Harita kaynağında şu ürün bildirimini kullan:
“© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data
(2021) processed by ESA WorldCover consortium”. Kaynakça için Zanaga ve
diğerleri (2022), [2021 v200 DOI](https://doi.org/10.5281/zenodo.7254221)
kaydını ekle; yerel işlemleri ayrıca belirt.

## 12. CLMS — HRL Tree Cover Density, Avrupa 10 m, 2021

**Ürün ailesi:** [CLMS Avrupa yıllık ağaç örtüsü 10 m](https://land.copernicus.eu/en/products/high-resolution-layer-forests-and-tree-cover/tree-cover-density-2018-present-raster-10-m-europe-yearly).
**Koşul:** [CLMS veri politikası](https://land.copernicus.eu/en/data-policy).

**Yerel kanıt:** [Ağaç örtüsü QA](qa/tree_cover_density_qa.md), dokuz
2021 HRL karosu, EPSG:3035 mozaiği, 10 m çözünürlük ve 0–100 değerlerini
kaydeder. Kesin karo kimlikleri/release yoktur; güncel Avrupa ürün sayfası
aile referansıdır. Yeni global/pantropikal ürünle karıştırılmaz.

- **Ham veri:** CLMS politikasına göre kaynak belirtilerek kamuya dağıtım
  mümkündür.
- **İşlenmiş/türev veri:** Uyarlamalar açıkça belirtilir; AB tarafından resmî
  destek izlenimi verilmez.
- **Harita/rapor:** CLMS kaynak bilgisi, 2021 referans yılı ve uygun ürün
  bağlantısı kullanılır; güncel release yerel sürüm olarak iddia edilmez.

**Uygulama:** CLMS bilgisinden üretildiğini belirt; kesme, projeksiyon ve skor
işlemlerini kaydet. Güncel Avrupa ürün ailesinin
[DOI bağlantısı](https://doi.org/10.2909/e677441e-fb94-431c-b4f9-304f10e4dfd8)
kesin yerel release kanıtı olarak sunulmadan kullanılabilir.

## 13. CARTO — Positron taban harita

**Ürün:** [CARTO Basemaps](https://www.carto.com/basemaps/).
**Koşullar:** [Basemap hizmet koşulları](https://www.carto.com/legal/basemap-terms/),
[atıf talimatı](https://www.carto.com/attribution/).

**Yerel kanıt:** QGIS projesinde anahtarsız eski `light_all` XYZ adresi
tanımlıdır. Servise bağlantı ile sunucudan gelen harita karolarını yeniden
dağıtmak farklıdır. Güncel koşullar eski dışa aktarımın tarihini/koşulunu
kanıtlamaz.

- **Ham veri/karolar:** Güncel hizmet koşulları **9(c)**, toplu içerik alma,
  karo/veri olarak yeniden dağıtma ve sunucu tarafında önbellekleme gibi
  kullanımları sınırlar. Kamu paketine indirilen XYZ karo arşivi eklenmez.
- **Canlı kullanım:** Güncel hizmet erişimi anahtar ve kullanım koşullarına
  tabidir. Kişisel API anahtarı depoya konmaz; mevcut anahtarsız adresin
  başka bilgisayarlarda çalışacağı varsayılmaz.
- **Harita/rapor:** **9(d)**, açıklama/belgeleme amaçlı statik görselleri
  okunabilir **13. bölüm** atıflarıyla kabul eder. Bu kullanım, karo verisinin
  açık lisansla dağıtımı anlamına gelmez.

**Uygulama:** Harita veya uygun açıklamasında `© OpenStreetMap contributors,
© CARTO` kredisini görünür tut; OSM ve CARTO bağlantılarını sağla. Yeni dışa
aktarımlarda uygun canlı erişim veya yerel bağlam katmanı seçimini ayrıca
doğrula.

## Somut kamu kapsamı

[İlk kamu paylaşım kapsamı](publication_file_scope.md), kaynak ve görselleri
somut dosya adlarıyla ayırır. Kod/config/Markdown ve veri referanslı QGIS
projesi; koşulları tamamlanan `03`, `06`, `09`, `10`, `11`, `12` statik
haritalarıyla sunulabilir. Bu seçki bütün kaynak verilerine açık lisans vermez.

AFAD, MTA, JRC/CEMS, HydroRIVERS/OSM hibriti ve USGS Vs30 ailesindeki 27
somut sayısal dosya yolu ilk paketin dışındadır; OSM-only dosyanın ayrı koşullu
adaylığı listede belirtilir. Ana MCDA/senaryo rasterları ile tam yerel veri
ZIP'i de bu ilk kamu kapsamına dahil değildir.

Tam Word/PDF raporu ve atlası korunur. İçerdikleri `01`, `02`, `04`, `05`,
`07`, `08`, `13` haritaları ve ilgili veri ekleri için kaynak kapsamı ayrı
değerlendirilir; teknik QA bütün belgeye genel yayın izni sağlamaz. Özgün
anlatım ve indirgenmiş analitik özetler, kaynak verisinin kopyasıyla otomatik
aynı sayılmaz; raporun tamamına genel bir yasak sonucu çıkarılmaz.
