# Veri Kaynak Envanteri

Proje: Çanakkale çok kriterli afet öncelik alanları analizi

Bu envanter, analizde kullanılan veri setlerinin kaynak bilgisini kurum/veri
seti adı düzeyinde kayda geçirir. Büyük upstream ham veri paketleri build
girdisi değildir; bu doküman mevcut `data/processed` ve `data/reference`
katmanlarının kaynak seceresini tanımlar.

Resmî ürün ve kullanım koşulu bağlantıları, ham/türev/harita ayrımı ve yerel
sürümün kanıt sınırları [veri hakları ve dağıtım kaydındadır](data_rights_and_distribution.md).
Envanterde bir kaynağın anılması, ona ait dosyaların tamamının kamuya
dağıtılabileceği anlamına gelmez. İlk dosya seçimi
[yayın durumu](../PUBLICATION_STATUS.md) belgesinde tutulur.

## Analiz Kaynakları

| No | Tema | Kaynak kurum / veri seti | Yıl / sürüm | Projedeki katman | Analizdeki rol | Temel sınırlılık |
|---:|---|---|---|---|---|---|
| 1 | İdari sınır / AOI | HGM idari sınır verileri; ilçe adları için OSM Geofabrik adminareas destekli manuel ad aktarımı | HGM kaynak metadata'sında 2021/2023 işlem tarihleri görülür; OSM extract yılı proje metadata'sında kayıtlı değil | `data/processed/aoi/canakkale_aoi_32635.gpkg`; `data/processed/admin/canakkale_districts_32635.gpkg` | Ana çalışma sınırı ve ilçe özet birimi | İdari referans katmanıdır; afet tehlikesi veya risk katmanı değildir. |
| 2 | DEM / eğim | Copernicus DEM GLO-30 | GLO-30; kaynak yıl/sürüm proje metadata'sında kayıtlı değil | `data/processed/dem/canakkale_dem_32635.tif`; `data/processed/dem/canakkale_slope_degrees_32635.tif` | Yükseklik ve eğim destek girdisi | DEM ve eğim tek başına heyelan, risk veya kırılganlık göstergesi değildir. |
| 3 | Taşkın | JRC / CEMS RP100 flood depth raster | RP100; kaynak yıl/sürüm proje metadata'sında kayıtlı değil | `data/processed/flood/canakkale_flood_rp100_depth_32635.tif`; `data/processed/analysis/flood_score_32635.tif` | Taşkın duyarlılık / tehlike destek girdisi | Resmi yerel taşkın risk haritası veya hidrodinamik model değildir. |
| 4 | Deprem yer hareketi | AFAD TDTH parametre değerleri | AFAD TDTH; kaynak workbook yılında proje metadata kaydı yok | `data/processed/earthquake/canakkale_afad_tdth_pga10_aoi_masked_32635.tif`; `data/processed/analysis/earthquake_pga_score_32635.tif` | PGA tabanlı sismik tehlike destek yüzeyi | AFAD tarafından yayımlanmış resmi raster ürün değildir; AFAD nokta parametrelerinden türetilmiş IDW destek yüzeyidir. |
| 5 | Diri fay / fay yakınlığı | MTA Türkiye Diri Fay Haritası veri paketi | 2013/2014 kaynak paketi olarak dokümante edilmiştir | `data/processed/faults/canakkale_faults_final_32635.gpkg`; `data/processed/analysis/fault_proximity_score_32635.tif` | Diri fay yakınlık skoru | Fay yakınlığı deterministik deprem riski, hasar beklentisi veya resmi tehlike zonu değildir. |
| 6 | Nüfus maruziyeti | WorldPop Turkey 2020 constrained UN-adjusted population raster | 2020 | `data/processed/population/population_count_aoi_100m_32635.tif`; `data/processed/analysis/population_exposure_score_32635.tif` | Tahmini yerleşik nüfus maruziyeti | Gerçek zamanlı, gündüz/gece, turistik, öğrenci veya mevsimsel nüfusu temsil etmez. |
| 7 | Zemin koşulu / VS30 | USGS Global Vs30 Mosaic | Kaynak yıl/sürüm proje metadata'sında kayıtlı değil | `data/processed/vs30/vs30_aoi_100m_32635.tif`; `data/processed/analysis/site_condition_score_32635.tif` | VS30 tabanlı zemin koşulu proxy skoru | Global ölçekli yaklaşık proxy veridir; yerel mikrobölgeleme veya jeoteknik etüt yerine geçmez. |
| 8 | Yapılı çevre / bina maruziyeti | Microsoft Global ML Building Footprints; OSM buildings gap-fill | Microsoft/OSM kaynak yılı veya Geofabrik extract tarihi proje metadata'sında kayıtlı değil | `data/processed/exposure/canakkale_buildings_hybrid_microsoft_osm_32635.gpkg`; `data/processed/analysis/building_exposure_density_score_32635.tif` | Bina footprint yoğunluğu ve yapılı çevre maruziyet proxy'si | Bina yaşı, yapı kalitesi, kat adedi, kullanıcı sayısı veya yapısal kırılganlık içermez. |
| 9 | Hidrografya | HydroRIVERS; OSM waterways gap-fill | HydroRIVERS v10; OSM extract tarihi proje metadata'sında kayıtlı değil | `data/processed/hydrography/canakkale_hydrography_hybrid_clean_32635.gpkg`; `data/processed/analysis/hydrography_proximity_score_32635.tif` | Nehir/akarsu/canal ağı ve yakınlık skoru | Hidrografya yakınlığı taşkın riski ile aynı şey değildir; hidrodinamik model yerine geçmez. |
| 10 | Arazi örtüsü | ESA WorldCover 2021 | 2021 | `data/processed/landcover/canakkale_worldcover_2021_32635.tif`; `data/processed/analysis/landcover_sensitivity_score_32635.tif` | Arazi örtüsü duyarlılık destek girdisi | Kategorik arazi örtüsü verisidir; tek başına tehlike veya risk üretmez. |
| 11 | Ağaç örtüsü | Copernicus / CLMS HRL Tree Cover Density | 2021 | `data/processed/landcover/canakkale_tree_cover_density_2021_32635.tif`; `data/processed/analysis/tree_cover_score_32635.tif` | Ağaç/vejetasyon yoğunluğu destek girdisi | Ağaç örtüsü yangın riski, yakıt nemi, rüzgâr veya yangın davranışı modeli değildir. |
| 12 | Yol erişimi | OpenStreetMap / Geofabrik Turkey OSM road network | Geofabrik Turkey OSM extract tarihi proje metadata'sında kayıtlı değil | `data/processed/osm/canakkale_osm_roads_32635.gpkg`; `data/processed/analysis/road_accessibility_difficulty_score_32635.tif` | Yol erişim zorluğu / operasyonel erişilebilirlik proxy'si | OSM kapsamlılığı bölgesel olarak değişebilir; resmi yol envanteri değildir. |

## Referans ve Destek Katmanları

| Katman grubu | Kaynak kurum / veri seti | Projedeki dosya | Kullanım notu |
|---|---|---|---|
| AFAD TDTH noktaları | AFAD TDTH parametre değerleri | `data/reference/earthquake/canakkale_afad_tdth_points_32635.gpkg` | PGA rasterinin türetilmesinde kullanılan nokta kaynak katmanıdır. |
| AFAD TDTH pre-mask raster | AFAD TDTH parametrelerinden türetilmiş IDW yüzey | `data/reference/earthquake/canakkale_afad_tdth_pga10_32635.tif` | AOI maskelenmiş raster öncesi izlenebilirlik katmanıdır. |
| OSM bina gap-fill | OpenStreetMap / Geofabrik Turkey OSM buildings | `data/reference/exposure/canakkale_osm_buildings_gapfill_32635.gpkg` | Microsoft binalarını tamamlamak için kullanılan ikincil gap-fill bileşenidir. |
| HydroRIVERS context | HydroRIVERS | `data/reference/hydrography/canakkale_hydrorivers_32635.gpkg` | AOI + 5 km bağlam için tutulan hidrografya izlenebilirlik katmanıdır. |
| HydroRIVERS AOI | HydroRIVERS | `data/reference/hydrography/canakkale_hydrorivers_aoi_32635.gpkg` | OSM gap-fill öncesi AOI hidrografya kaynağıdır. |
| OSM waterways gap-fill | OpenStreetMap / Geofabrik Turkey OSM waterways | `data/reference/hydrography/canakkale_osm_waterways_gapfill_32635.gpkg` | Temiz hibrit hidrografya katmanına ikincil yerel tamamlayıcı olarak kullanılmıştır. |
| OSM yerleşim/POI/ulaşım/arazi kullanım | OpenStreetMap / Geofabrik Turkey OSM GeoPackage | `data/processed/osm/canakkale_osm_places_32635.gpkg`; `data/processed/osm/canakkale_osm_pois_32635.gpkg`; `data/processed/osm/canakkale_osm_transport_points_32635.gpkg`; `data/processed/osm/canakkale_osm_landuse_32635.gpkg` | Harita bağlamı, yerleşim ve destek analizleri için referans katmanlardır. |

## Veri Yönetimi Notu

Büyük upstream ham veri paketleri build girdisi değildir. Analiz için kabul
edilen canonical seviye `data/processed` ve `data/reference` katmanlarıdır.
Kaynak kurum ve veri seti adı düzeyinde kaynak bilgisi verilir; büyük ham dosya
varlığı iddia edilmez.

## Yıl / Sürüm Kayıt İlkesi

Bu envanterde yıl veya sürüm bilgisi yalnızca dosya adı, yerel metadata, QA
dokümanı veya kaynak veri seti adından desteklenebildiğinde yazılır. Kaynak yılı
proje metadata'sında korunmuyorsa değer tahmin edilmez; bu durum ilgili satırda
açıkça belirtilir.

## Raporlama İçin Kaynak Seviyesi

Bu proje için kaynakça ve veri açıklaması aşağıdaki ayrıntı seviyesinde tutulur:

- kaynak kurum veya platform adı,
- veri seti adı,
- bilinen yıl veya sürüm,
- projedeki analiz / referans katmanı,
- analizdeki rol,
- temel metodolojik sınırlılık.
