# Çanakkale Afet Öncelik Projesi Veri Manifesti

**Kaynak sürümü kapsamı:** İlk kamu sürümü kod, yöntem belgeleri, QGIS
proje tanımı ve seçilmiş analitik özetleri içerir. Tam kanonik veriler ve
harita/rapor dosyaları dahil değildir. Bu belgedeki tam analiz, katman ve
çıktı kontrolleri ilgili yerel dosyalar ayrıca sağlandığında çalışır; kaynak
kopyasında eksik girdilerin bildirilmesi beklenir. [Dosya kapsamı](publication_file_scope.md).

Proje: Çanakkale çok kriterli afet öncelik alanları analizi

Bu manifest, proje klasöründeki analiz, referans, QGIS, rapor ve harita
varlıklarını listeler. Veri tabanı processed-canonical seviyeye dayanır:
`data/processed` analiz katmanlarını, `data/reference` izlenebilirlik katmanlarını
içerir.

## 1. Proje CRS ve Kapsam

| Özellik | Değer |
|---|---|
| CRS | EPSG:32635 - WGS 84 / UTM Zone 35N |
| Raster grid | 100 m, 1586 x 1423 |
| Çalışma alanı | Çanakkale AOI |
| Analiz niteliği | Keşifsel MCDA tabanlı mekânsal öncelik analizi |

Bu çalışma resmi afet risk haritası, deterministik tehlike modeli, mühendislik
düzeyinde hasar tahmini veya bina düzeyi kayıp modeli değildir. Katmanlar
duyarlılık, maruziyet ve mekânsal öncelik destek girdileri olarak kullanılır.

## 2. Analiz Katmanları

### 2.1 Temel ve İdari Katmanlar

| Katman | Path | Rol |
|---|---|---|
| Çanakkale AOI | `data/processed/aoi/canakkale_aoi_32635.gpkg` | Ana analiz sınırı |
| Çanakkale ilçeleri | `data/processed/admin/canakkale_districts_32635.gpkg` | İlçe sınırı ve özet birimi |

### 2.2 Topoğrafya

| Katman | Path | Rol |
|---|---|---|
| DEM | `data/processed/dem/canakkale_dem_32635.tif` | Yükseklik destek rasterı |
| Slope | `data/processed/dem/canakkale_slope_degrees_32635.tif` | Eğim destek rasterı |

### 2.3 Taşkın

| Katman | Path | Rol |
|---|---|---|
| JRC/CEMS RP100 flood depth | `data/processed/flood/canakkale_flood_rp100_depth_32635.tif` | Taşkın derinliği destek rasterı |
| Flood score | `data/processed/analysis/flood_score_32635.tif` | MCDA taşkın kriter skoru |

### 2.4 Deprem

| Katman | Path | Rol |
|---|---|---|
| AFAD TDTH PGA10 AOI-masked raster | `data/processed/earthquake/canakkale_afad_tdth_pga10_aoi_masked_32635.tif` | PGA tabanlı sismik tehlike destek yüzeyi |
| Earthquake PGA score | `data/processed/analysis/earthquake_pga_score_32635.tif` | MCDA deprem PGA kriter skoru |
| Fault vector | `data/processed/faults/canakkale_faults_final_32635.gpkg` | Diri fay referans geometrisi |
| Fault proximity score | `data/processed/analysis/fault_proximity_score_32635.tif` | MCDA fay yakınlık kriter skoru |

AFAD TDTH PGA rasterı, nokta parametre değerlerinden türetilmiş IDW destek
yüzeyidir; AFAD tarafından yayımlanmış resmi raster ürün olarak yorumlanmaz.

### 2.5 Maruziyet

| Katman | Path | Rol |
|---|---|---|
| Population count | `data/processed/population/population_count_aoi_100m_32635.tif` | WorldPop tabanlı tahmini yerleşik nüfus |
| Population exposure score | `data/processed/analysis/population_exposure_score_32635.tif` | MCDA nüfus maruziyet kriter skoru |
| Hybrid Microsoft + OSM buildings | `data/processed/exposure/canakkale_buildings_hybrid_microsoft_osm_32635.gpkg` | Yapılı çevre maruziyet proxy'si |
| Building exposure density score | `data/processed/analysis/building_exposure_density_score_32635.tif` | MCDA yapı maruziyeti kriter skoru |

Hybrid bina katmanı nüfus, kullanım, yapı kalitesi veya bina düzeyi afet riskini
temsil etmez.

### 2.6 Zemin ve Arazi Örtüsü

| Katman | Path | Rol |
|---|---|---|
| VS30 AOI raster | `data/processed/vs30/vs30_aoi_100m_32635.tif` | USGS VS30 tabanlı zemin proxy katmanı |
| Site condition score | `data/processed/analysis/site_condition_score_32635.tif` | MCDA zemin koşulu kriter skoru |
| ESA WorldCover | `data/processed/landcover/canakkale_worldcover_2021_32635.tif` | Arazi örtüsü destek rasterı |
| Landcover sensitivity score | `data/processed/analysis/landcover_sensitivity_score_32635.tif` | MCDA arazi örtüsü kriter skoru |
| Tree cover density | `data/processed/landcover/canakkale_tree_cover_density_2021_32635.tif` | Ağaç/vejetasyon destek rasterı |
| Tree cover score | `data/processed/analysis/tree_cover_score_32635.tif` | MCDA ağaç örtüsü kriter skoru |

### 2.7 Hidrografya ve Yol Erişimi

| Katman | Path | Rol |
|---|---|---|
| Clean hybrid HydroRIVERS + OSM waterways | `data/processed/hydrography/canakkale_hydrography_hybrid_clean_32635.gpkg` | Doğal nehir/akarsu/canal ağı |
| Hydrography proximity score | `data/processed/analysis/hydrography_proximity_score_32635.tif` | MCDA hidrografya yakınlık kriter skoru |
| OSM roads | `data/processed/osm/canakkale_osm_roads_32635.gpkg` | Yol ağı referansı |
| Road accessibility difficulty score | `data/processed/analysis/road_accessibility_difficulty_score_32635.tif` | MCDA yol erişim zorluğu kriter skoru |

Nehir yakınlığı hidrodinamik taşkın modellemesinin yerine geçmez.

### 2.8 OSM Referans Katmanları

| Katman | Path | Rol |
|---|---|---|
| OSM transport points | `data/processed/osm/canakkale_osm_transport_points_32635.gpkg` | Ulaşım referansı |
| OSM places | `data/processed/osm/canakkale_osm_places_32635.gpkg` | Yerleşim referansı |
| OSM POIs | `data/processed/osm/canakkale_osm_pois_32635.gpkg` | Hizmet/POI referansı |
| OSM landuse | `data/processed/osm/canakkale_osm_landuse_32635.gpkg` | Arazi kullanımı bağlam katmanı |

## 3. MCDA Analiz Çıktıları

| Katman | Path | Rol |
|---|---|---|
| Analysis template | `data/processed/analysis/analysis_template_100m_32635.tif` | Ortak 100 m analiz gridi |
| MCDA raw score | `data/processed/analysis/mcda_priority_score_32635.tif` | Ağırlıklı ham MCDA skoru |
| MCDA normalized score | `data/processed/analysis/mcda_priority_score_normalized_32635.tif` | 0-1 normalize MCDA skoru |
| MCDA priority class | `data/processed/analysis/mcda_priority_class_32635.tif` | 1-5 sınıflı öncelik rasterı |

## 4. Referans Katmanları

Bu katmanlar izlenebilirlik, kaynak seceresi ve gap-fill açıklaması için kullanılır;
ana MCDA skor girdisi olarak çift sayım yaratacak şekilde kullanılmaz.

| Katman | Path | Rol |
|---|---|---|
| AFAD TDTH source points | `data/reference/earthquake/canakkale_afad_tdth_points_32635.gpkg` | PGA rasterı için nokta kaynak katmanı |
| AFAD TDTH PGA10 pre-mask raster | `data/reference/earthquake/canakkale_afad_tdth_pga10_32635.tif` | AOI maskelenmiş raster öncesi türetilmiş PGA yüzeyi |
| OSM building gap-fill | `data/reference/exposure/canakkale_osm_buildings_gapfill_32635.gpkg` | Hybrid building dataset içindeki ikincil gap-fill bileşeni |
| HydroRIVERS context layer | `data/reference/hydrography/canakkale_hydrorivers_32635.gpkg` | AOI + 5 km hidrografya bağlam katmanı |
| HydroRIVERS AOI layer | `data/reference/hydrography/canakkale_hydrorivers_aoi_32635.gpkg` | OSM gap-fill öncesi AOI HydroRIVERS kaynağı |
| OSM waterways gap-fill | `data/reference/hydrography/canakkale_osm_waterways_gapfill_32635.gpkg` | Temiz hibrit hidrografyaya ikincil yerel tamamlayıcı |
| Full hybrid hydrography with drain | `data/reference/hydrography/canakkale_hydrography_hybrid_hydrorivers_osm_32635.gpkg` | Drain içeren karşılaştırma/reference katmanı |

## 5. Build Girdisi Olmayan Upstream Paketler

Büyük upstream ham veri paketleri build girdisi değildir. Kaynak adı raporda
anılır; scriptler bu paketlerin proje klasöründe bulunmasını beklemez.

| Veri grubu | Kaynak / örnek |
|---|---|
| Raw OSM | Geofabrik Turkey raw OSM GeoPackage |
| Raw flood | JRC/CEMS flood raster |
| Raw DEM | Copernicus DEM GLO-30 tiles |
| Raw landcover | ESA WorldCover tiles |
| Raw tree cover | Copernicus / CLMS Tree Cover Density tiles |
| Raw hydrography | HydroRIVERS package |
| Raw population | WorldPop raster |
| Raw buildings | Microsoft Global ML Building Footprints package |
| Raw VS30 | USGS Global VS30 Mosaic extract |

## 6. QGIS, Harita ve Rapor Varlıkları

| Varlık | Path | Rol |
|---|---|---|
| QGIS projesi | `qgis/canakkale_disaster_priority.qgz` | Harita düzeni, katman organizasyonu ve atlas üretimi |
| Harita PNG çıktıları | `outputs/maps/png/` | Kamu raporu ve görsel sunum için 13 harita |
| Harita PDF çıktıları | `outputs/maps/pdf/` | Tekil kaynak kalitesinde harita exportları |
| Birleşik atlas PDF | `outputs/atlas/canakkale_afet_oncelik_harita_atlasi.pdf` | 13 sayfalık harita atlası |
| Rapor tabloları | `outputs/tables/` | MCDA sınıf, ilçe, raster istatistik ve sensitivity tabloları |
| Kamu Word raporu | `outputs/report/canakkale_disaster_priority_public_report.docx` | Düzenlenebilir ana rapor; 13 harita, bir korelasyon figürü, sekiz veri tablosu |
| Kamu PDF raporu | `outputs/report/canakkale_disaster_priority_public_report.pdf` | 18 sayfalık okuma kopyası; dosya sürümü ve kontrol kapsamı `public_report_manifest.json` içinde |
| DOCX üretim hedefi | `outputs/report/canakkale_disaster_priority_academic_report.docx` | `build_academic_report.sh --build` ile ayrıca üretilebilir; kamu Word raporundaki elle yapılmış düzenlemeleri devralmaz |

## 7. Katman Kullanım Politikası

| Tema | Kullanılacak ana katman | Aynı anda skor girdisi yapılmayacak katmanlar |
|---|---|---|
| Bina maruziyeti | `canakkale_buildings_hybrid_microsoft_osm_32635` | Standalone Microsoft buildings, standalone OSM buildings, OSM building gap-fill |
| Hidrografya | `canakkale_hydrography_hybrid_clean_32635` | HydroRIVERS context, HydroRIVERS AOI-only, OSM waterways standalone, OSM waterways gap-fill, drain içeren full hybrid hydrography |
| Deprem PGA | `canakkale_afad_tdth_pga10_aoi_masked_32635` | AFAD source points ve pre-mask rasterı |
| MCDA | `mcda_priority_class_32635.tif` ve ilgili score rasterları | `data/processed/analysis/archive/` altındaki eski rasterlar |

## 8. Kaynak Seviyesi

Kaynakça ve veri açıklaması şu ayrıntı düzeyinde tutulur:

- kaynak kurum veya platform adı,
- veri seti adı,
- bilinen yıl veya sürüm,
- projedeki analiz/reference katmanı,
- analizdeki rol,
- temel metodolojik sınırlılık.

Ayrıntılı kaynak tablosu:

```text
docs/data_source_inventory.md
```
