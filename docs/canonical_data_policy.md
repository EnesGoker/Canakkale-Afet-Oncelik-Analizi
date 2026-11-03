# Canonical Veri Politikası

**Kaynak sürümü kapsamı:** İlk kamu sürümü kod, yöntem belgeleri, QGIS
proje tanımı, seçilmiş analitik özetleri ve harita PNG görsellerini içerir.
Tam kanonik veriler, harita PDF/atlas ve rapor dosyaları dahil değildir. Bu belgedeki tam analiz, katman ve
çıktı kontrolleri ilgili yerel dosyalar ayrıca sağlandığında çalışır; kaynak
kopyasında eksik girdilerin bildirilmesi beklenir. [Dosya kapsamı](publication_file_scope.md).

Proje: Çanakkale çok kriterli afet öncelik alanları analizi

Bu politika, analiz ve raporlama için hangi veri katmanlarının geçerli girdi
kabul edildiğini tanımlar. Projenin veri tabanı, büyük upstream ham veri
paketlerine değil, mevcut processed/reference katmanlarına dayanır.

**Kapsam ayrımı:** Canonical olması, dosyanın analiz için geçerli girdi olduğu
anlamına gelir; kamuya yeniden dağıtım izni anlamına gelmez. Kaynak ve türev
verilerin paylaşımı [veri hakları kaydına](data_rights_and_distribution.md),
kamu dosya seçimi [yayın listesine](../PUBLICATION_STATUS.md) tabidir.

## 1. Amaç

Bu belgenin amacı:

- analiz veri tabanını tanımlamak,
- scriptlerin beklediği girdi seviyesini netleştirmek,
- raporda kaynak bilgisini doğru düzeyde sunmak,
- ham dosya varlığı iddiası oluşturmamak,
- grid, CRS ve katman kullanım kurallarını standartlaştırmaktır.

## 2. Canonical Veri Seviyesi

Analiz için canonical veri seviyesi aşağıdaki klasörlerdir:

| Seviye | Klasör | Kullanım |
|---|---|---|
| Analiz katmanları | `data/processed/` | MCDA kriterleri, nihai/hybrid vektörler, raster skorları, AOI ve ilçe sınırları |
| İzlenebilirlik katmanları | `data/reference/` | Gap-fill bileşenleri, pre-mask türevler ve kaynak seceresi için korunan referans katmanlar |
| Küçük raw kaynaklar | `data/raw/admin/`, `data/raw/earthquake/afad_tdth/` | İdari sınır ve AFAD TDTH gibi küçük kaynak kayıtları |

Rapor, tablo üretimi, MCDA kontrolü, QGIS proje kontrolü ve DOCX build süreci bu
veri seviyesini esas alır.

## 3. Yeniden Üretilebilirlik Kapsamı

Proje, analiz seviyesindeki yeniden üretilebilirliği hedefler. Scriptler,
`data/processed` ve `data/reference` canonical katmanlarından MCDA kontrolü,
sensitivity tabloları, rapor tabloları ve DOCX üretimini yeniden çalıştırabilir.

Büyük upstream ham veri paketlerinden tüm veri hazırlama zincirinin birebir
yeniden kurulması bu proje paketinin kapsamı dışındadır. Bu kaynaklar veri seti
adı, kurum ve yıl/sürüm düzeyinde izlenir; ancak scriptler bu büyük ham
dosyaların proje klasöründe bulunmasını zorunlu kılmaz.

## 4. Büyük Upstream Ham Veri Paketleri

Aşağıdaki büyük upstream ham veri paketleri build girdisi değildir:

- Microsoft Global ML Building Footprints ham paketleri
- Geofabrik / OpenStreetMap Türkiye ham GeoPackage dosyaları
- Copernicus DEM GLO-30 ham karoları
- ESA WorldCover ham karoları
- Copernicus / CLMS Tree Cover Density ham karoları
- JRC / CEMS flood ham raster dosyaları
- HydroRIVERS ulusal/kıtasal ham paketleri
- WorldPop ham nüfus rasterı
- USGS Global Vs30 Mosaic ham extract dosyası

Bu kaynaklar veri kaynağı olarak anılır; ancak scriptler ve rapor builder bu
paketlerin proje klasöründe bulunmasını beklemez. Kaynak bilgisi
`docs/data_source_inventory.md` içinde kurum/veri seti/yıl veya sürüm düzeyinde
tutulur.

## 5. Katman Kullanım Kuralı

Aynı temanın raw, standalone, gap-fill, reference ve nihai/hybrid versiyonları
aynı anda skor girdisi olarak kullanılmaz. Analizde nihai veya hybrid katman
tercih edilir; reference katmanlar izlenebilirlik ve açıklama için korunur.

| Tema | Analiz katmanı | Aynı anda skor girdisi yapılmayacak katmanlar |
|---|---|---|
| Bina maruziyeti | `data/processed/exposure/canakkale_buildings_hybrid_microsoft_osm_32635.gpkg` | Standalone Microsoft binaları, standalone OSM binaları, OSM gap-fill katmanı |
| Hidrografya | `data/processed/hydrography/canakkale_hydrography_hybrid_clean_32635.gpkg` | HydroRIVERS AOI-only, OSM waterways standalone, OSM waterways gap-fill, drain içeren full hybrid reference katmanı |
| Deprem PGA | `data/processed/earthquake/canakkale_afad_tdth_pga10_aoi_masked_32635.tif` | AFAD nokta katmanı ve pre-mask PGA rasterı |
| MCDA | `data/processed/analysis/mcda_priority_class_32635.tif` ve ilgili score rasterları | `data/processed/analysis/archive/` altındaki eski MCDA rasterları |

## 6. Script Davranış Sözleşmesi

Proje scriptleri şu kurallara uyar:

1. Proje kökünü script konumuna göre belirler.
2. Kişisel veya local absolute pathleri girdi olarak kullanmaz.
3. Büyük upstream ham veri paketlerini zorunlu input olarak beklemez.
4. Girdi katmanı olarak `data/processed` ve `data/reference` seviyesini kullanır.
5. Çıktı üretmeden önce dosya varlığı, CRS, grid ve satır sözleşmesini kontrol eder.
6. Yazma yapan modlar hedef çıktı dizinini açıkça belirtir.
7. `--check` modları proje dosyalarını değiştirmez; geçici dosyalar sistem temp
   dizininde oluşturulur.

Script ayrıntıları için:

```text
docs/script_kullanim_ve_guvenlik_rehberi.md
```

## 7. Raporlama Sözleşmesi

Rapor ve tablolar şu ilkelere göre yazılır:

- Büyük upstream ham veri paketlerinin proje klasöründe bulunduğu iddia edilmez.
- Veri kaynakları kurum/veri seti adı/yıl veya sürüm düzeyinde verilir.
- Analiz katmanları `data/processed` ve `data/reference` üzerinden tanımlanır.
- Her veri seti için temel metodolojik sınırlılık belirtilir.
- Sonuçlar resmi risk, tehlike, hasar, acil durum veya hukuki karar ürünü gibi
  sunulmaz.

## 8. Kalite Kontrol Kapıları

Canonical veri seviyesinden üretilen her tablo, skor veya rapor şu kontrollerle
uyumlu olmalıdır:

| Kontrol | Kabul kriteri |
|---|---|
| CRS | Mekânsal analiz katmanları EPSG:32635 olmalıdır |
| Raster grid | MCDA ve kriter skor rasterları 1586 x 1423 boyutunda, 100 m gridde ve aynı extentte olmalıdır |
| NoData | Sürekli skor rasterlarında AOI dışı değer `-9999`; class rasterında AOI dışı değer `0` sözleşmesi korunmalıdır |
| Katman seçimi | Nihai/hybrid katmanlar kullanılmalı; standalone ve gap-fill katmanlar çift sayıma yol açacak şekilde skor girdisi olmamalıdır |
| Kaynak metni | Rapor ham dosya varlığı iddiası içermemelidir |
| İzlenebilirlik | Kullanılan analiz katmanı `docs/data_source_inventory.md` içinde kaynak kurum/veri seti adıyla eşleşmelidir |

## 9. Politika Revizyon Koşulları

Bu politika aşağıdaki durumlarda ilgili dokümanlarla birlikte gözden geçirilir:

- yeni bir veri setinin analize eklenmesi,
- bir nihai/hybrid katmanın başka bir katmanla değiştirilmesi,
- MCDA kriter seti veya ağırlıklarının değişmesi,
- büyük upstream ham veri paketlerinin build girdisi haline getirilmesi,
- QGIS atlasında gösterilen ana analiz katmanlarının değişmesi.

Bir revizyonda birlikte kontrol edilecek belgeler:

- `docs/data_source_inventory.md`
- `docs/canonical_data_policy.md`
- `docs/data_manifest.md`
- ilgili metodoloji notu
- ilgili QA notu
