# Statik harita kaynakları ve bildirimleri

Tarih: **3 Kasım 2026** (`v0.2.1`). Bu bildirim `outputs/maps/png/` altındaki 14 harita PNG
görseliyle birlikte sunulur. Kapsam [dosya seçiminde](publication_file_scope.md)
açıklanır; sayısal kaynak verileri, harita PDF'leri veya atlas için lisans değildir.

## Birlikte sunulacak dosyalar

Her kök için `outputs/maps/png/<kök>.png`:

- `01_cok_kriterli_oncelik_sinifi`
- `02_fay_yakinlik_skoru`
- `03_nufus_maruziyet_skoru`
- `04_zemin_kosulu_skoru`
- `05_deprem_pga_skoru`
- `06_yapi_maruziyet_yogunluk_skoru`
- `07_taskin_skoru`
- `08_hidrografya_yakinlik_skoru`
- `09_egim_skoru`
- `10_arazi_ortusu_duyarlilik_skoru`
- `11_agac_ortusu_skoru`
- `12_yol_erisim_zorlugu_skoru`
- `13_senaryo_ortakligi`
- `14_yuksek_oncelik_olasiligi`

Her görsel alt bandında ortak ve tema atfını taşır; etiket bu dosyanın bağlantısını
verir. Harita tek başına paylaşılırsa etiket kırpılmadan korunmalıdır. Aşağıdaki
metinler görseldeki kısa atfın tam halidir.

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
Görselde kaynak URL'leri okunabilir yazılır. Karo önbelleği ve kişisel servis
anahtarı görsellerle dağıtılmaz.

HGM kesin release/edinim tarihi, OSM extract tarihi ve CARTO arka planının
veri tarihi kayıtlı değildir. Aşağıdaki bilinen ürün yılları indirme tarihi değildir.
Ortak gösterim EPSG:32635 ve 100 m analiz grididir; kaynakların özgün çözünürlüğü farklıdır.

Her görselin alt bandındaki ortak satır:

> İdari sınırlar: HGM Türkiye Mülki İdare Sınırları (resmî nitelik taşımaz) · Taban harita: © OpenStreetMap contributors (openstreetmap.org/copyright), © CARTO (carto.com/attribution) · Tam kaynak ve lisans bildirimleri: github.com/EnesGoker/Canakkale-Afet-Oncelik-Analizi/blob/main/docs/static_map_attributions.md

## 01 — Çok kriterli öncelik sınıfı

On bir kriter skorunun ağırlıklı toplamından üretilen beş sınıf; MTA fay çizgisi
bindirmesi vardır. Kaynaklar: AFAD TDTH (§05), MTA (§02), USGS Vs30 (§04), WorldPop (§03),
Microsoft/OSM binalar (§06), JRC/CEMS (§07), HydroRIVERS/OSM (§08), Copernicus DEM (§09),
ESA WorldCover (§10), CLMS TCD (§11), OSM yollar (§12). Lisansların zorunlu kalıpları
(DEM 6(b) ve 6(c), ESA, CLMS) görseldeki etikette aynen yer alır; HydroSHEDS Ek B
bildiriminin tamamı §08'dedir. [Yöntem](methodology/updated_mcda_methodology_note.md).

Görseldeki etiket:

> Veri: AFAD TDTH parametreleri (PGA; IDW yüzeyi yazarın türetimi) · MTA Türkiye Diri Fay Haritası sayısal verisi (2013/2014) · USGS Global Vs30 Mosaic (Heath vd. 2020) · WorldPop Türkiye 2020 (doi:10.5258/SOTON/WP00685, CC BY 4.0) · Microsoft GlobalML Building Footprints (CDLA-Permissive-2.0) + OSM binalar · JRC/CEMS Avrupa ve Akdeniz RP100 taşkın derinliği, © European Union, 1995-2026, doi:10.2905/1D128B6C-A4EE-4858-9E34-6210707F3C81 · HydroRIVERS v1.0 (Lehner & Grill 2013, doi:10.1002/hyp.9740; HydroSHEDS © WWF, lisansla kullanıldı) + OSM su yolları · produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved · © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium · Generated using European Union's Copernicus Land Monitoring Service information · OSM yollar © OpenStreetMap contributors (ODbL).
>
> Skorlar, sınıflar ve harita yazarın türetimidir; kaynak kurumlar çalışmayı onaylamaz. AFAD ve MTA'dan yazılı izin alınmamıştır. The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30.

## 02 — Fay yakınlığı

Kaynak: MTA Türkiye Diri Fay Haritası sayısal verisi, 2013/2014 paketi; kesin sürüm
ve edinim kaydı **bilinmiyor**. Değişiklikler: AOI kesiti, EPSG:32635, fay çizgisine
mesafe ve 100 m yakınlık skoru. [Fay yöntem notu](methodology/fault_data_methodology_note.md).
MTA'dan yazılı yayın izni alınmamıştır; izin ileri sürülmez. 2026 yenilenmiş diri fay
ürününün koşulları bu eski pakete uygulanmaz.

Görseldeki etiket:

> Fay: MTA Türkiye Diri Fay Haritası sayısal verisi (2013/2014). Fay yakınlık skoru yazarın türetimidir; MTA çalışmayı onaylamaz ve MTA'dan yazılı izin alınmamıştır.

## 03 — Nüfus maruziyeti

Kaynak: WorldPop / University of Southampton; Türkiye **2020**, constrained,
UN-adjusted BSGM; Bondarenko ve diğerleri (2020), [WP00685](https://doi.org/10.5258/SOTON/WP00685).
Lisans: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Değişiklikler: EPSG:4326→32635, AOI kesiti ve 100 m hizalama; nüfus sayıları
sum yöntemiyle yeniden örneklendi, log normalizasyonuyla göreli skor üretildi.
[İşlem kaydı](methodology/population_data_methodology_note.md). Resmî nüfus sayımı değildir.

Görseldeki etiket:

> Nüfus: WorldPop / University of Southampton, Türkiye 2020 constrained UN-adjusted (Bondarenko vd. 2020, doi:10.5258/SOTON/WP00685), CC BY 4.0. Değişiklikler: EPSG:32635, AOI kesiti, 100 m toplam yeniden örnekleme ve log skoru (yazarın türetimi).

## 04 — Zemin koşulu

Kaynak: [USGS Vs30 Models and Data](https://earthquake.usgs.gov/data/vs30/), Global Vs30
Mosaic; Heath ve diğerleri (2020). Yerel extract'in yıl/release ve bölgesel bileşen
kapsamı **bilinmiyor**. USGS deposu aksi belirtilmeyen kapsam için CC0 bildirir; bu
bildirim bilinmeyen bileşenlere otomatik atanmaz, bu nedenle görselde lisans adı yazılmaz.
Değişiklikler: AOI kesiti, 100 m hizalama ve zemin skoru.
[VS30 yöntem notu](methodology/vs30_data_methodology_note.md).

Künye (USGS sayfasındaki haliyle; sayfa DOI vermez): Heath, D., Wald, D. J., Worden, C. B.,
Thompson, E. M., and Scmocyk, G. (2020). A Global Hybrid VS30 Map with a
Topographic-Slope-Based Default and Regional Map Insets, Earthquake Spectra, vol. 36, 3:
pp. 1570-1584.

Görseldeki etiket:

> Vs30: USGS Global Vs30 Mosaic (Heath vd. 2020; earthquake.usgs.gov/data/vs30). Değişiklikler: AOI kesiti, 100 m hizalama ve zemin koşulu skoru (yazarın türetimi).

## 05 — Deprem PGA

Kaynak: AFAD Türkiye Deprem Tehlike Haritası (TDTH) parametre değerleri. Projedeki IDW
yüzeyi ve skor yazarın türetimidir; resmî AFAD raster ürünü değildir. AFAD'dan yazılı
yayın izni alınmamıştır; izin ileri sürülmez. Ham parametre ve nokta verisi dağıtılmaz.
[AFAD QA](qa/afad_tdth_source_check.md), [dönüşüm](methodology/criterion_transformations.md).

Görseldeki etiket:

> PGA: AFAD Türkiye Deprem Tehlike Haritası (TDTH) parametreleri. IDW yüzeyi ve skor yazarın türetimidir, resmî AFAD ürünü değildir; AFAD'dan yazılı izin alınmamıştır.

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

Görseldeki etiket:

> Yapı: Microsoft GlobalML Building Footprints (CDLA-Permissive-2.0) + OSM bina gap-fill © OpenStreetMap contributors (ODbL). Değişiklikler: hibrit bina alanının 100 m hücre alanına oranı (yazarın türetimi).

## 07 — Taşkın

Kaynak: JRC/CEMS European and Mediterranean RP100 flood depth,
doi:[10.2905/1D128B6C-A4EE-4858-9E34-6210707F3C81](https://doi.org/10.2905/1D128B6C-A4EE-4858-9E34-6210707F3C81);
© European Union, 1995-2026. Resmî README ODbL 1.0, aynı dizinin copyright dosyası
CC BY 4.0 belirtir; uyuşmazlık çözülmediği için görselde lisans adı yazılmaz, kaynak,
telif ve DOI yazılır. Değişiklikler: AOI kesiti, 100 m hizalama ve taşkın skoru.
[Flood QA](qa/flood_qa.md).

Görseldeki etiket:

> Taşkın: JRC/CEMS Avrupa ve Akdeniz RP100 taşkın derinliği, © European Union, 1995-2026, doi:10.2905/1D128B6C-A4EE-4858-9E34-6210707F3C81. Değişiklikler: AOI kesiti ve 100 m taşkın skoru (yazarın türetimi).

## 08 — Hidrografya yakınlığı

Kaynak: HydroRIVERS v1.0 (Lehner ve Grill 2013,
[10.1002/hyp.9740](https://doi.org/10.1002/hyp.9740)), [www.hydrosheds.org](https://www.hydrosheds.org),
ve OSM su yolları gap-fill (© OpenStreetMap contributors, [ODbL](https://opendatacommons.org/licenses/odbl/1-0/)).
Değişiklikler: AOI kesiti, OSM ile hibrit ağ, mesafe ve 100 m yakınlık skoru.
[HydroRIVERS QA](qa/hydrorivers_qa.md), [hibrit QA](qa/hydrography_hybrid_clean_qa.md).
HydroSHEDS lisansının türev dağıtım hükmünün statik görsele uygulanma kapsamı çözülmemiştir.

HydroSHEDS lisansı Ek B zorunlu bildirimi (aynen; ürün adı yerine bu görsel):

> This product (08_hidrografya_yakinlik_skoru map image) incorporates data from the HydroSHEDS version 1 database
> which is © World Wildlife Fund, Inc. (2006-2022) and has been used herein under license. WWF has not evaluated the
> data as altered and incorporated within 08_hidrografya_yakinlik_skoru map image, and therefore gives no warranty
> regarding its accuracy, completeness, currency or suitability for any particular purpose. Portions of the HydroSHEDS v1
> database incorporate data which are the intellectual property rights of © USGS (2006-2008), NASA (2000-2005), ESRI
> (1992-1998), CIAT (2004-2006), UNEP-WCMC (1993), WWF (2004), Commonwealth of Australia (2007), and Her
> Royal Majesty and the British Crown and are used under license. The HydroSHEDS v1 database and more information
> are available at https://www.hydrosheds.org.

Aynı bildirim `01`, `13` ve `14` görselleri için de geçerlidir.

Görseldeki etiket:

> Hidrografya: HydroRIVERS v1.0 (Lehner & Grill 2013, doi:10.1002/hyp.9740), www.hydrosheds.org; HydroSHEDS v1 © World Wildlife Fund, Inc. (2006-2022), lisansla kullanıldı · OSM su yolları © OpenStreetMap contributors (ODbL). Yakınlık skoru yazarın türetimidir; WWF değiştirilmiş veriyi değerlendirmemiştir.

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
Madde 6(b) bildirimi (lisansın 2. sayfasından aynen):
**"produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH
2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved"**.
Madde 6(c) bildirimi (aynen): **"The organisations in charge of the Copernicus programme by law or by
delegation do not incur any liability for any use of the Copernicus WorldDEM-30"** — Türkçesi:
Copernicus programından kanunen veya yetki devriyle sorumlu kuruluşlar, Copernicus WorldDEM-30'un
herhangi bir kullanımından doğan sorumluluk üstlenmez. Kurumsal destek ileri sürülmez; sonraki dağıtımda
madde 6 kapsamındaki bildirim/yükümlülükler korunur.

Görseldeki etiket:

> Eğim: produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved. The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30. Değişiklikler: mozaik, EPSG:32635, AOI kesiti, eğim ve 100 m skor (yazarın türetimi).

## 10 — Arazi örtüsü duyarlılığı

Kaynak: [ESA WorldCover 2021 v200](https://esa-worldcover.org/en/data-access),
Zanaga ve diğerleri (2022), [ürün DOI'si](https://doi.org/10.5281/zenodo.7254221);
lisans [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
**© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data
(2021) processed by ESA WorldCover consortium.**
Değişiklikler: iki 10 m karo mozaiği, AOI kesiti/projeksiyonda nearest-neighbour;
sınıf→skor dönüşümü ardından average ile 100 m. [Kaynak QA](qa/landcover_qa.md),
[dönüşüm tablosu](methodology/criterion_transformations.md).

Görseldeki etiket:

> Arazi örtüsü: © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium (Zanaga vd. 2022, doi:10.5281/zenodo.7254221, CC BY 4.0). Değişiklikler: sınıf→skor dönüşümü ve 100 m ortalama (yazarın türetimi).

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

Görseldeki etiket:

> Ağaç örtüsü: Generated using European Union's Copernicus Land Monitoring Service information (HRL Tree Cover Density 2021, 10 m). Değişiklikler: EPSG:32635, AOI kesiti, 100 m ortalama ve yüzde/100 skor (yazarın türetimi); AB veya CLMS çalışmayı onaylamaz.

## 12 — Yol erişim zorluğu

Kaynak: OpenStreetMap contributors / [Geofabrik Türkiye](https://download.geofabrik.de/europe/turkey.html),
`gis_osm_roads_free`; extract tarihi **bilinmiyor**; [ODbL](https://opendatacommons.org/licenses/odbl/1-0/).
Değişiklikler: AOI bbox filtresi, EPSG:32635 ve kesme; merkez rasterizasyonu,
metre cinsinden yol mesafesi ve 2 km'de 1'e ulaşan göreli zorluk skoru.
[Yol QA](qa/osm_roads_qa.md), [dönüşüm](methodology/criterion_transformations.md).
Resmî yol envanteri veya yol ağı üzerinde gerçek seyahat süresi değildir.

Görseldeki etiket:

> Yollar: © OpenStreetMap contributors (Geofabrik Türkiye, gis_osm_roads_free), ODbL. Değişiklikler: AOI kesiti, rasterizasyon, yol mesafesi ve 2 km'de 1'e ulaşan zorluk skoru (yazarın türetimi).

## 13 — Senaryo ortaklığı

Üç ağırlık senaryosunda yüksek öncelik (4. ve 5. sınıf) sayısı (0–3). Kaynaklar `01`
ile aynıdır; fay çizgisi bindirmesi yoktur, fay skoru modelin içindedir.
[Sonuçların yorumu](analysis/scenario_agreement.md).

Görseldeki etiket:

> Veri: AFAD TDTH parametreleri (PGA; IDW yüzeyi yazarın türetimi) · MTA Türkiye Diri Fay Haritası sayısal verisi (2013/2014) · USGS Global Vs30 Mosaic (Heath vd. 2020) · WorldPop Türkiye 2020 (doi:10.5258/SOTON/WP00685, CC BY 4.0) · Microsoft GlobalML Building Footprints (CDLA-Permissive-2.0) + OSM binalar · JRC/CEMS Avrupa ve Akdeniz RP100 taşkın derinliği, © European Union, 1995-2026, doi:10.2905/1D128B6C-A4EE-4858-9E34-6210707F3C81 · HydroRIVERS v1.0 (Lehner & Grill 2013, doi:10.1002/hyp.9740; HydroSHEDS © WWF, lisansla kullanıldı) + OSM su yolları · produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved · © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium · Generated using European Union's Copernicus Land Monitoring Service information · OSM yollar © OpenStreetMap contributors (ODbL).
>
> Skorlar, sınıflar ve harita yazarın türetimidir; kaynak kurumlar çalışmayı onaylamaz. AFAD ve MTA'dan yazılı izin alınmamıştır. The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30.

## 14 — Yüksek öncelikte kalma oranı

P(yüksek+): hücrenin 2.000 Dirichlet ağırlık örneğinde (κ = 100) sıralama tabanlı
yüksek+ (4.–5.) sınıfta kalma oranı; koyu gri çizgi baseline yüksek+ sınırıdır.
Afet olasılığı değildir. Kaynaklar `01` ile aynıdır; fay çizgisi bindirmesi yoktur,
fay skoru modelin içindedir. [Sonuçların yorumu](analysis/weight_perturbation.md).

Görseldeki etiket `13` ile aynıdır.

## Açık kalan koşullar ve yayın dayanağı

1. **OSM türev veritabanı/değişiklik erişimi:** [ODbL 4.3–4.6](https://opendatacommons.org/licenses/odbl/1-0/) ve [OSMF üretilmiş eser rehberi](https://osmfoundation.org/wiki/Licence/Community_Guidelines/Produced_Work_-_Guideline) kapsamında ilgili türev veritabanı veya bütün değişiklikler/yöntem ve ek içerikler için somut erişim düzeni sağlanmalıdır. Mevcut [dönüşüm kontrolü](../scripts/python/check_criterion_transformations.py) processed girdilerden skora gidişi, [QA belgeleri](qa/osm_roads_qa.md) bazı upstream adımlarını açıklar; ham OSM→kesit/hibrit zincirinin tamamının yürütülebilir ve mevcut extract'i yeniden kurabilir olduğu iddia edilmez. Bu nedenle kodun bulunması 4.6'nın tek başına tamamlandığı anlamına gelmez.
2. **İzin ve lisans kapsamı:** AFAD ve MTA verisinden türetilen görseller (`01`, `02`, `05`, `13`, `14`) yazılı izin olmadan yayımlanmıştır; JRC/CEMS (`07`), HydroSHEDS (`08`) ve USGS Vs30 (`04`) için açık kalan lisans/türev kapsamı çözülmemiştir. Yayın bu bilinerek yapılmıştır; izin ileri sürülmez ve hak sahibinin talebi halinde ilgili görsel kaldırılır.

Kurumların bu çalışmayı onayladığı veya sonuçların resmî olduğu ileri sürülmez.
