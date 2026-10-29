# Statik harita kaynakları ve bildirimleri

Tarih: **29 Ekim 2026**. Bu bildirim yalnız aşağıdaki altı haritanın PNG/PDF
seçkisiyle birlikte sunulur. Kapsam [dosya seçiminde](publication_file_scope.md)
açıklanır; sayısal kaynak verileri veya bütün rapor/atlas için lisans değildir.

## Birlikte sunulacak dosyalar

Her kök için `outputs/maps/png/<kök>.png` ve `outputs/maps/pdf/<kök>.pdf`:

- `03_nufus_maruziyet_skoru`
- `06_yapi_maruziyet_yogunluk_skoru`
- `09_egim_skoru`
- `10_arazi_ortusu_duyarlilik_skoru`
- `11_agac_ortusu_skoru`
- `12_yol_erisim_zorlugu_skoru`

Bu Markdown dosyasının bağlantısı seçki açıklamasında görünür olmalıdır.
Harita tek başına paylaşılırsa ilgili kaynak kredileri de onunla taşınmalıdır.
**Yan bildirim, PNG/PDF üzerindeki veya yanında bulunması gereken okunabilir
atıfların eksikliğini kendiliğinden düzeltmez.** Son kabul koşulları aşağıdadır.

## Ortak kredi

İdari sınırlar: Harita Genel Müdürlüğü (HGM), [Türkiye Mülki İdare Sınırları](https://www.harita.gov.tr/urun/turkiye-mulki-idare-sinirlari/232).
Sınırlar ve bunlardan türetilen gösterimler resmî nitelik taşımaz; ticari olmayan
öğrenci portföyü kapsamında kullanılır. HGM telifi korunur; sınırlara MIT/CC0 verilmez.
İlçe adlarında OSM/Geofabrik adminareas destekli manuel aktarım bulunmaktadır.

Taban harita ve OSM katkıları: **© OpenStreetMap contributors, © CARTO**.
[OSM telif/lisansı](https://www.openstreetmap.org/copyright),
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/),
[CARTO atıf rehberi](https://www.carto.com/attribution/) ve
[statik belgeleme koşulları](https://www.carto.com/legal/basemap-terms/) geçerlidir.
Basılı/PDF bağlamında kaynak URL'leri okunabilir olmalıdır. Karo önbelleği ve
kişisel servis anahtarı bu statik seçkiyle dağıtılmaz.

HGM kesin release/edinim tarihi, OSM extract tarihi ve CARTO arka planının
veri tarihi kayıtlı değildir. Aşağıdaki bilinen ürün yılları indirme tarihi değildir.
Ortak gösterim EPSG:32635 ve 100 m analiz grididir; kaynakların özgün çözünürlüğü farklıdır.

## 03 — Nüfus maruziyeti

Kaynak: WorldPop / University of Southampton; Türkiye **2020**, constrained,
UN-adjusted BSGM; Bondarenko ve diğerleri (2020), [WP00685](https://doi.org/10.5258/SOTON/WP00685).
Lisans: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Değişiklikler: EPSG:4326→32635, AOI kesiti ve 100 m hizalama; nüfus sayıları
sum yöntemiyle yeniden örneklendi, log normalizasyonuyla göreli skor üretildi.
[İşlem kaydı](methodology/population_data_methodology_note.md). Resmî nüfus sayımı değildir.

## 06 — Yapı maruziyeti yoğunluğu

Kaynak: [Microsoft GlobalML BuildingFootprints](https://github.com/microsoft/GlobalMLBuildingFootprints)
ve OSM bina gap-fill. Kaynak yıl/release ve OSM extract tarihi **bilinmiyor**.
Microsoft koşulu: [CDLA Permissive 2.0](https://cdla.dev/permissive-2-0/);
OSM bileşeni: [ODbL](https://opendatacommons.org/licenses/odbl/1-0/).
Değişiklikler: AOI kesiti/projeksiyon; örtüşme ve küçük alan filtresiyle OSM
gap-fill; hibrit bina alanının 100 m hücre alanına oranı ve 0–1 kırpma.
[Gap-fill kuralları](qa/osm_buildings_gapfill_qa.md), [yoğunluk dönüşümü](methodology/criterion_transformations.md).
CDLA'nın hesaplama sonuçları için ek kısıt getirmemesi OSM koşullarını kaldırmaz.
Veri dosyası ayrıca dağıtılırsa CDLA anlaşma metni de veriyle sağlanmalıdır.

## 09 — Eğim

Kaynak: [Copernicus DEM GLO-30](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM).
Kaynak yıl/release **bilinmiyor**. Altı karo mozaiklenmiş, EPSG:32635'e
alınmış ve AOI'ye kesilmiştir; derece eğiminden bilinear 100 m hizalama ve
normalize skor üretilmiştir. [DEM QA](qa/dem_qa.md), [dönüşüm](methodology/criterion_transformations.md).
Lisans: [WorldDEM-30, madde 6(b)–6(e), sayfa 2](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf#page=2).
Bu ürün değiştirilmiş Copernicus WorldDEM-30 verisinden üretilmiştir.
Kaynak telifleri DLR e.V. (2010–2014) ve Airbus Defence and Space GmbH
(2014–2018); veri Avrupa Birliği ve ESA tarafından COPERNICUS altında sağlanır.
Bu telif aralıkları yerel veri yılı/edinim tarihi yerine geçmez.
Madde 6(b)'nin zorunlu özgün kaynak kalıbı resmî lisansın sayfa 2'sindedir;
bu Türkçe açıklama o kalıbın aynen uygulandığına ilişkin bir kabul değildir.
Madde 6(c) sorumluluk bildirimi: **Copernicus programından kanunen veya yetki
devriyle sorumlu kuruluşlar, Copernicus WorldDEM-30'un herhangi bir kullanımından
doğan sorumluluk üstlenmez.** Kurumsal destek ileri sürülmez; sonraki dağıtımda
madde 6 kapsamındaki bildirim/yükümlülükler korunur.

## 10 — Arazi örtüsü duyarlılığı

Kaynak: [ESA WorldCover 2021 v200](https://esa-worldcover.org/en/data-access),
Zanaga ve diğerleri (2022), [ürün DOI'si](https://doi.org/10.5281/zenodo.7254221);
lisans [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
**© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data
(2021) processed by ESA WorldCover consortium.**
Değişiklikler: iki 10 m karo mozaiği, AOI kesiti/projeksiyonda nearest-neighbour;
sınıf→skor dönüşümü ardından average ile 100 m. [Kaynak QA](qa/landcover_qa.md),
[dönüşüm tablosu](methodology/criterion_transformations.md).

## 11 — Ağaç örtüsü

Kaynak: Copernicus Land Monitoring Service (CLMS), Avrupa HRL Tree Cover Density,
**2021**, 10 m; kesin karo/release kimliği bilinmiyor. [Ürün ailesi](https://land.copernicus.eu/en/products/high-resolution-layer-forests-and-tree-cover/tree-cover-density-2018-present-raster-10-m-europe-yearly),
[veri politikası](https://land.copernicus.eu/en/data-policy).
**Generated using European Union's Copernicus Land Monitoring Service information.**
Değişiklikler: dokuz karo mozaiği, EPSG:3035→32635, AOI kesiti ve nearest-neighbour;
255 NoData korunmuş, average ile 100 m ve yüzde/100 skor dönüşümü uygulanmıştır.
[Kaynak QA](qa/tree_cover_density_qa.md), [dönüşüm](methodology/criterion_transformations.md).
Avrupa Birliği veya CLMS'nin projeyi onayladığı ileri sürülmez; yeni ürün DOI'si
kesin yerel release olarak sunulmaz.

## 12 — Yol erişim zorluğu

Kaynak: OpenStreetMap contributors / [Geofabrik Türkiye](https://download.geofabrik.de/europe/turkey.html),
`gis_osm_roads_free`; extract tarihi **bilinmiyor**; [ODbL](https://opendatacommons.org/licenses/odbl/1-0/).
Değişiklikler: AOI bbox filtresi, EPSG:32635 ve kesme; merkez rasterizasyonu,
metre cinsinden yol mesafesi ve 2 km'de 1'e ulaşan göreli zorluk skoru.
[Yol QA](qa/osm_roads_qa.md), [dönüşüm](methodology/criterion_transformations.md).
Resmî yol envanteri veya yol ağı üzerinde gerçek seyahat süresi değildir.

## Son kabul için açık kalan iki koşul

1. **Görünür kaynak bildirimleri:** Altı PNG/PDF ve paylaşıldıkları bağlamda ortak/tema kredileri okunabilir olmalıdır; 09 için özgün 6(b) kalıbı ve 6(c) sorumluluk bildirimi uygulanır. Bu MD'nin varlığı görseldeki uygulamayı doğrulamaz.
2. **OSM türev veritabanı/değişiklik erişimi:** [ODbL 4.3–4.6](https://opendatacommons.org/licenses/odbl/1-0/) ve [OSMF üretilmiş eser rehberi](https://osmfoundation.org/wiki/Licence/Community_Guidelines/Produced_Work_-_Guideline) kapsamında ilgili türev veritabanı veya bütün değişiklikler/yöntem ve ek içerikler için somut erişim düzeni sağlanmalıdır. Mevcut [dönüşüm kontrolü](../scripts/python/check_criterion_transformations.py) processed girdilerden skora gidişi, [QA belgeleri](qa/osm_roads_qa.md) bazı upstream adımlarını açıklar; ham OSM→kesit/hibrit zincirinin tamamının yürütülebilir ve mevcut extract'i yeniden kurabilir olduğu iddia edilmez. Bu nedenle kodun bulunması 4.6'nın tek başına tamamlandığı anlamına gelmez.

Bu iki koşul kapanmadan altı görselin son kamu dağıtımı tamamlanmış sayılmaz.
Bu bildirim AFAD/MTA/diğer kaynaklar içeren 01/02/04/05/07/08/13 haritalarına
ve tam rapor/atlasa yayın garantisi vermez; onların kapsamı ayrı kalır.
