# Kriter kaynakları, skor dönüşümleri ve mevcut açıklamalar

İnceleme: **23–24 Ekim 2026**. Analiz değerleri ve ağırlıklar değiştirilmedi.

## Mevcut yöntem açıklamalarına erişim

Kaynaklar, ağırlık gerekçeleri ve ana model zaten belgelenmiştir. Bu belge,
onları tekrar yazmak yerine kaynak→skor adımlarını mevcut dosyalarla eşleştirir.

| Konu | Mevcut açıklama |
|---|---|
| Kaynak kurum, ürün, yıl/sürüm ve rol | [Veri envanteri](../data_source_inventory.md#analiz-kaynakları) |
| 11 kriterin tek tek ağırlık gerekçesi | [Güncel yöntem §6.3](updated_mcda_methodology_note.md#63-kriter-düzeyi-gerekçe) |
| Blok dengesi ve çift sayım | [Güncel yöntem §6.4](updated_mcda_methodology_note.md#64-blok-düzeyi-denge), [§10](updated_mcda_methodology_note.md#10-çift-sayım-ve-model-dengesi) |
| Ağırlıklı toplam, final normalizasyon ve sınıflar | [§7](updated_mcda_methodology_note.md#7-weighted-overlay-formülü), [§8](updated_mcda_methodology_note.md#8-normalization), [§9](updated_mcda_methodology_note.md#9-öncelik-sınıflandırması) |
| Duyarlılık senaryoları | [§6.5](updated_mcda_methodology_note.md#65-sınırlı-ağırlık-duyarlılığı-kontrolü), [ölçekleme açıklaması](normalization_and_baseline.md) |
| Yorum sınırları | [Bilimsel sınırlılıklar](scientific_limits.md) |

Üç kanıt türü ayrılır: **kayıtlı açıklama/kod**, **kurtarılan işlem kaydı**,
**mevcut dosyalara sayısal olarak eşdeğer reçete**. Eşdeğerlik, yazarın
geçmişte kullandığı her komutu veya parametre seçme gerekçesini kanıtlamaz.

## On bir kriterin eşleştirmesi

`x`: ilgili kaynak 100 m şablona hizalandıktan sonraki değer; `d`: GDAL
rasterizasyonundan üretilen metre cinsinden mesafe. Bütün sonuçlar yalnız
`analysis_template_100m_32635.tif == 1` alanında karşılaştırılmıştır.

| Kriter / ağırlık | Mevcut kaynak ve gerekçe | Skor / yürütülebilir kontrol |
|---|---|---|
| PGA / 0.16 | [PGA QA](../qa/afad_tdth_pga10_aoi_masked_qa.md), [IDW notu](../qa/afad_tdth_pga10_raster_stats.md); kaynak `processed/earthquake/` | Bilinear; `clip((x−0.29773420095947556)/0.438076138475815,0,1)`. İki sabit mevcut veriden kestirilmiş eşdeğer parametredir. [Yeni kontrol](../../scripts/python/check_criterion_transformations.py). |
| Fay yakınlığı / 0.12 | [Fay notu §3](fault_data_methodology_note.md#3-i̇şleme-adımları), [§6](fault_data_methodology_note.md#6-fay-yakınlığı-skor-formülü) | `max(1−d/10000,0)`; [mevcut fay kontrolü](../../scripts/bash/fault_processing_pipeline.sh). |
| VS30 zemin / 0.08 | [VS30 notu §4](vs30_data_methodology_note.md#4-i̇şleme-adımları), [§7](vs30_data_methodology_note.md#7-site-condition-skor-formülü) | `clip((900−VS30)/(900−180.042),0,1)`; [mevcut VS30 kontrolü](../../scripts/bash/vs30_processing_pipeline.sh). |
| Nüfus / 0.14 | [Nüfus notu §3](population_data_methodology_note.md#3-i̇şleme-adımları), [§6](population_data_methodology_note.md#6-nüfus-maruziyeti-skor-formülü) | `log1p(max(count,0))/log1p(159.301)`; [mevcut nüfus kontrolü](../../scripts/bash/population_processing_pipeline.sh). |
| Bina yoğunluğu / 0.10 | [Hibrit kaynak](../qa/buildings_hybrid_stats.md); `building_density_final_grid_100m_32635.gpkg` alanları | `clip(building_area_m2/grid_area_m2,0,1)` ve kayıtlı skor alanının merkez rasterizasyonu; yeni kontrol. |
| Taşkın / 0.10 | [Taşkın QA](../qa/flood_qa.md), [istatistikler](../qa/flood_raster_stats.md); kaynak `processed/flood/` | Bilinear; `clip(x/10.0526208878,0,1)`. Bölen işlem kaydında var; üst kırpma güncel dosyalarla eşdeğer reçeteye aittir. |
| Hidrografya / 0.06 | [Temiz hibrit kuralları](../qa/hydrography_hybrid_clean_qa.md); kaynak `processed/hydrography/` | Merkez rasterizasyonu → GEO proximity → `clip(1−d/1000,0,1)`; yeni kontrol. |
| Eğim / 0.08 | [DEM/eğim QA](../qa/dem_qa.md), [kontroller](../qa/dem_sanity_checks.md); derece cinsinden kaynak `processed/dem/` | Bilinear; `clip(x/40.20227432106767,0,1)`. Bölen mevcut veriden kestirilmiş eşdeğer parametredir. |
| Arazi örtüsü / 0.06 | [WorldCover kaynak hazırlığı](../qa/landcover_qa.md); kategorik kaynak `processed/landcover/` | Önce aşağıdaki 10 m sınıf→skor tablosu, sonra **AVERAGE** ile 100 m; yeni kontrol. |
| Ağaç örtüsü / 0.04 | [TCD QA](../qa/tree_cover_density_qa.md); 0–100 kaynak `processed/landcover/` | **AVERAGE** ile 100 m, `x/100`; yeni kontrol. |
| Yol erişimi / 0.06 | [OSM yol QA](../qa/osm_roads_qa.md); kaynak `processed/osm/` | Merkez rasterizasyonu → GEO proximity → `clip(d/2000,0,1)`; yeni kontrol. |

Her skorun dosya adı, kriter kimliğinin `_32635.tif` eklenmiş halidir ve
`data/processed/analysis/` altındadır. Tek yetkili ağırlık kaynağı
`config/mcda_weights.tsv` olarak korunur. Buradaki eşdeğer parametreler yeni
ağırlık, yeni fiziksel tehlike eşiği veya yeni model önerisi değildir.

## Arazi örtüsü tablosu ve işlem sırası

| WorldCover kodu | Kaynak sınıfı | Geri doğrulanan skor |
|---:|---|---:|
| 10 | Ağaç örtüsü | 0.60 |
| 20 | Çalılık | 0.50 |
| 30 | Çayır/otsu örtü | 0.40 |
| 40 | Tarım | 0.30 |
| 50 | Yapılı alan | 0.20 |
| 60 | Çıplak/seyrek örtü | 0.20 |
| 80 | Kalıcı su | 0.05 |
| 90 | Otsu sulak alan | 0.50 |

Bu tablo mevcut rasterlardan geri doğrulanmıştır; her sınıfın özgün puan
seçme gerekçesinin ayrıca bulunduğu iddia edilmez. Kaynak `0`, NoData'dır.
Yerel veride görülmeyen `70/95/100` sınıflarına puan uydurulmaz; yeni kontrol
tanınmayan sınıf geldiğinde durur.

Kategorik kaynağın hazırlanmasındaki **nearest-neighbour**, sınıf kimliğini
korur. 10 m sınıflar skora çevrildikten sonraki **average**, sürekli 100 m
skoru üretir. Bunlar farklı iki aşamadır. Sınıf kodlarını doğrudan ortalamak
veya 100 m'de baskın sınıfa puan vermek mevcut sonucu üretmez.

## Sayısal sonuç ve kaynak NoData davranışı

Yeni denetimde sekiz reçete **981.033 AOI hücresinin tamamında** karşılaştırıldı.
PGA/eğim/taşkında en büyük mutlak fark `3e-8` altında; diğer beşinde fark
tam `0`. Kullanılan kabul toleransı mutlak `1e-6`dır. Parametreler her koşuda
yeniden uydurulmaz; değişmiş kaynak/skor uyuşmazlığı böylece yakalanır.

Bina oranı **986.286 öznitelik satırında** da eşleşir. 23 satırda ham oran
1'i aştığından kırpma etkilidir; bu veri, bina kırılganlığı ölçümü değildir.
Mesafe reçeteleri GDAL'ın varsayılan rasterizasyonuyla eşleşir;
`ALL_TOUCHED` açılması aynı sonucu vermez.

Güncel eşdeğer reçetelerde kaynak NoData'nın AOI içinde sıfır skora
dönüştüğü hücreler:

| Kaynak | Hücre |
|---|---:|
| PGA | 9.412 |
| Eğim | 538 |
| Taşkın | 948.171 |
| Ağaç örtüsü | 7 |

Bu, mevcut modelin kaynak kapsamı/NoData davranışıdır. Sıfır skor, bu
hücrelerde tehlikenin yokluğunun ölçüldüğü anlamına gelmez. Özellikle taşkın
katmanı, bütün AOI'de yerel bir taşkın modelinin varlığı gibi yorumlanmaz.

## Kurtarılan işlem kayıtları ve açık kalan ayrıntı

[Temizlenmiş seçki](processing_history_excerpt.json), ilgili yerel QGIS
işlem geçmişinden 13 kaydın yalnız algoritma, parametre ve dosya taban
adlarını içerir. Kişisel dizinler, kimlik bilgileri ve diğer uygulama
kayıtları kamu belgesine alınmamıştır. Tarihler kaynakta saat dilimsizdir.

- 73–74: taşkın bilinear 100 m ve `where(A < 0, 0, A / 10.0526208878)`.
- 75–76: PGA ve eğimin bilinear 100 m hizalanması.
- 77–78: ağaç örtüsü ve 10 m arazi örtüsü skorunun average ile 100 m'ye geçişi.
- 79–82: bina gridi/kesişim/alan/toplulaştırma adımları.

Taşkının tarihsel ifadesi üst kırpma içermez. Güncel kaynak yeniden
hizalandığında eşdeğer reçetedeki üst kırpma 82 AOI hücresinde etkilidir.
Korunmamış ara dosyaların byte düzeyinde özdeşliği ileri sürülmez.

En dar açık sayısal köken bilgisi, PGA alt/aralık referansları ile eğim
böleninin geçmişte **hangi seçim kuralıyla** alındığıdır. Bunların kaynak
min/max veya belirli bir yüzdelik olduğu doğrulanmadı. Verilen uzun
katsayılar sayısal eşdeğerliği korur; fiziksel doğruluk hassasiyeti göstermez.
Mesafe eşikleri ve sınıf skorlarının tarihsel seçme gerekçesi de yalnız
sayısal eşleşmeden çıkarılamaz. Mevcut kaynak, ağırlık gerekçesi ve genel
yöntem açıklamaları bu dar köken sınırından ayrı değerlendirilir.
