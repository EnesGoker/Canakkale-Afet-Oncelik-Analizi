# Çanakkale harita atlası planı ve düzen sözleşmesi

**Kaynak sürümü kapsamı:** Aşağıdaki raster, harita PDF, atlas ve Word/PDF
yolları tam yerel çalışma çıktısıdır; bu dosyalar kaynak ve analitik özet
sürümünde dağıtılmaz. `outputs/maps/png/` altındaki harita PNG'leri kamu
kapsamındadır. Yerel üretim/kontrol komutları ilgili kanonik veri ve
çıktıların ayrıca bulunmasını gerektirir. [Kamu dosya kapsamı](publication_file_scope.md).

Güncelleme: 2026-11-03.

Atlas, 13 QGIS düzeninin tekil PDF çıktılarından birleştirilir. Düzenlerin
metinleri, renkleri, harita kapsamları ve sayfa öğeleri üretim sözleşmesinin
parçasıdır. Dışa aktarma sırasında CARTO anahtarı yalnız çalışma ortamında
kullanılır; genel QGIS projesinde veya Git'te tutulmaz.

Atlas; nihai öncelik sınıfı, 11 kriter haritası ve üç senaryonun yüksek
öncelik ortaklığını gösteren sayfa olmak üzere 13 coğrafi haritadan
oluşur. 14. QGIS düzeni (yüksek öncelikte kalma oranı) yalnız PNG olarak
üretilir; sözleşmede `pdf_export: false` taşır ve atlasa girmez. Korelasyon figürü (`outputs/figures/criterion_correlation_v1/criterion_pearson_correlation.png`)
ayrı bir analiz görselidir. Güncel teknik bağlama kaydı
[map_layouts_v1.json](../config/map_layouts_v1.json), çıktı kontrolü
[harita QA belgesidir](qa/map_export_qa.md).

## Düzen sözleşmesi

`13_senaryo_ortakligi_layout` sayfası, atlasla aynı A3 yatay tasarımı kullanır.
Başlık ve alt başlık, sağ bilgi metni,
harita kapsamı ve kutusu, lejantın dört rengi, ölçek ve kuzey oku korunur.
Kaynak yollarını taşınabilir hâle getirmek veya harita/stil kilitlerini
sabitlemek için sayfa öğeleri taşınmaz ya da yeniden tasarlanmaz.

Kaydedilmiş PNG/PDF ürünleri, checksum manifestiyle izlenen referans
çıktılardır. Her düzenin katmanları ve stilleri, kendi lejantı ve tematik
içeriğiyle eşleşecek şekilde kilitlidir. Yeniden üretim ayrı bir çıktı
klasöründe yapılır. Atlasın sayfa sırası ve içerik akışları, 01–13 numaralı
giriş PDF'leriyle karşılaştırılır.

## Çıktı sırası

Dosya köklerinin PNG'leri `outputs/maps/png/`, PDF'leri `outputs/maps/pdf/`
klasöründedir. Düzen adı köke `_layout` eklenerek elde edilir.

| No | Başlık | Ana raster | Dosya kökü |
|---:|---|---|---|
| 01 | Çok Kriterli Öncelik Sınıfı | `mcda_priority_class_32635.tif` | `01_cok_kriterli_oncelik_sinifi` |
| 02 | Fay Yakınlık Skoru | `fault_proximity_score_32635.tif` | `02_fay_yakinlik_skoru` |
| 03 | Nüfus Maruziyet Skoru | `population_exposure_score_32635.tif` | `03_nufus_maruziyet_skoru` |
| 04 | Zemin Koşulu Skoru | `site_condition_score_32635.tif` | `04_zemin_kosulu_skoru` |
| 05 | Deprem PGA Skoru | `earthquake_pga_score_32635.tif` | `05_deprem_pga_skoru` |
| 06 | Yapı Maruziyeti Yoğunluk Skoru | `building_exposure_density_score_32635.tif` | `06_yapi_maruziyet_yogunluk_skoru` |
| 07 | Taşkın Skoru | `flood_score_32635.tif` | `07_taskin_skoru` |
| 08 | Hidrografya Yakınlık Skoru | `hydrography_proximity_score_32635.tif` | `08_hidrografya_yakinlik_skoru` |
| 09 | Eğim Skoru | `slope_score_32635.tif` | `09_egim_skoru` |
| 10 | Arazi Örtüsü Duyarlılık Skoru | `landcover_sensitivity_score_32635.tif` | `10_arazi_ortusu_duyarlilik_skoru` |
| 11 | Ağaç Örtüsü Skoru | `tree_cover_score_32635.tif` | `11_agac_ortusu_skoru` |
| 12 | Yol Erişim Zorluğu Skoru | `road_accessibility_difficulty_score_32635.tif` | `12_yol_erisim_zorlugu_skoru` |
| 13 | Üç Senaryoda Yüksek Öncelik Ortaklığı | `scenario_agreement_count_32635.tif` | `13_senaryo_ortakligi` |
| 14 | Yüksek Öncelikte Kalma Oranı (yalnız PNG) | `high_plus_probability_count_32635.tif` | `14_yuksek_oncelik_olasiligi` |

İlk 12 raster `data/processed/analysis/`, 13. raster
`outputs/analysis/scenario_agreement_v1/`, 14. raster
`outputs/analysis/weight_perturbation_v1/` içindedir. Atlasın adı
`outputs/atlas/canakkale_afet_oncelik_harita_atlasi.pdf` olarak korunur.

## Haritaya özel referanslar

İl ve ilçe sınırları ile %50 opak CARTO Positron altlığı tüm sayfalarda
kullanılır. Sınırlar üstte, ilgili referans vektörleri ve tek tematik raster
ortada, altlık en alttadır. Sayfalara göre ek referanslar şöyledir:

| Sayfa | Ek referans katmanları |
|---|---|
| 01–02 | Diri fay hatları |
| 03 | Yerleşim noktaları |
| 04–05 | Yok |
| 06 | Yol ağı ve yerleşim noktaları |
| 07–08 | Hidrografya ağı |
| 09–11 | Yok |
| 12 | Yol ağı |
| 13 | Yok |
| 14 | Baseline yüksek+ sınırı (tematik rasterın üstünde) |

Bu seçimler proje ana ekranındaki aç/kapa durumundan bağımsızdır. Lejantlar
kendi haritalarına bağlanır; katman kümesi ve stilleri her sayfa için kilitlidir.
Fiili paletler [semboloji kaydında](map_symbology_qa.md) açıklanır.

2026-10-24 kontrolünde 13 PNG/PDF bağımsız görsel incelemeden, birleşik atlasın
13 sayfası PDF okuma ve görsel çizim kontrolünden geçmiştir. Düzen/çıktı
kontrolü 13 düzen ve 27 dosyayı doğrular; ana canonical QA çıkış 0 ile geçmiştir.
Ayrıntılı kapsam ve üretim kanıtı [QA kaydındadır](qa/map_export_qa.md).
2026-11-02 (v0.2) üretiminde 13 harita alt bant atıf etiketiyle yeniden dışa
aktarılmış, atlas bu 13 PDF'ten aynı sıra ve sayfa içerik akışı eşliğiyle yeniden
birleştirilmiştir; düzen/çıktı kontrolü yine 13 düzen ve 27 dosyayı doğrular.
2026-11-03'te 14. düzen eklenmiş, 01–13 aynı projeden yeniden dışa aktarılmış ve
atlas aynı sayfalarla değişmeden yeniden birleştirilmiştir; düzen/çıktı kontrolü
14 düzen ve 28 dosyayı (14 PNG, 13 PDF, atlas) doğrular.

## Ortak sayfa ve yorum bilgileri

A3 yatay sayfa; başlık, alt başlık, ana harita, lejant, ölçek çubuğu, kuzey
oku, EPSG:32635 ve 100 m grid bilgisi ile hazırlayan bilgisini taşır.
Kaynak/kriter referansı bilgi kutularında yer alır. Ayrıntılı atıflar ve
kullanım sınırları [harita notu](../outputs/maps/README.md),
[atlas notu](../outputs/atlas/README.md) ve
[veri hakları kaydı](data_rights_and_distribution.md) ile birlikte okunur.
Bu notların tümünün mevcut sayfa tasarımında basılı olduğu ileri sürülmez.

13. haritanın değerleri 0–3 tam sayılı senaryo sayılarıdır. Yüksek öncelik,
her senaryonun 4. veya 5. sınıfına girmektir. Baseline sabit normalizasyonu,
alternatiflerin kendi AOI min–max normalizasyonu kullanıldığı için harita
ortak mutlak tehlike eşiği ya da yalnız ağırlık değişiminin etkisi değildir.
[Analiz yorumu](analysis/scenario_agreement.md) bu sınırı ve alan sonuçlarını açıklar.

14. haritanın değeri P(yüksek+) = sayım / 2.000'dir: hücrenin 2.000 ağırlık
örneğinde sıralama tabanlı yüksek+ sınıfta kalma oranı. Afet olasılığı değildir;
sınıflar ve yorum [ağırlık pertürbasyonu analizindedir](analysis/weight_perturbation.md).

## Dışa aktarma ve doğrulama

PNG üretimi 300 DPI, arka plan opak, sayfa A3 yataydır. Tekil PDF'ler birer
sayfadır (14 için PDF yok); atlas 01–13 sırasıyla 13 sayfadır. Dosya adları küçük ASCII harf,
alt çizgi ve iki haneli sıra numarası kullanır. `_layout` eki çıktı adına girmez.

```bash
python3 scripts/python/export_map_layouts.py --check --json
```

Kaydedilmiş ürünler [28 dosya manifestiyle](../outputs/maps/map_export_manifest.json)
eşleştirilir. HTTP 200 yanıtı veren altlık görseli de hatalı içerik
taşıyabilir; teknik üretim sonrasında görsel inceleme ayrıca gereklidir.

Yeniden üretim `--generate --output-dir <yeni-veya-boş-klasör>` ile açıkça
başlatılır; seçili düzenler için `--layouts` (ör. `--layouts 14`), CARTO döşemelerini çizmek için
`--allow-web-basemap` ve `CARTO_BASEMAPS_API_KEY` gerekir. Anahtar ortam
değişkeniyle yalnız çalışma anında sağlanır; salt okunur kontrol anahtar istemez;
özel anahtar dosyasından okuma örneği [QA belgesindedir](qa/map_export_qa.md).
Genel QGIS dosyası özgün anahtarsız URL'yi korur; kendi QGIS oturumunda canlı
altlık isteyen kullanıcı anahtarını yalnız özel yerel yapılandırmasına ekler.
QGIS Python ortamı kullanılır. Komut kaynak
projeyi kaydetmez ve nihai ürünlerin üzerine yazmaz. Tam örnekler ve
kontrol kayıtları [QA belgesinde](qa/map_export_qa.md) yer alır.

## Mevcut PDF'lerden atlası yeniden birleştirme

Bu adım haritaları yeniden çizmez; mevcut 13 tek sayfalık PDF'yi sözleşmedeki
sırayla birleştirir (`pdf_export: false` olan 14. düzen atlanır). CARTO anahtarı veya ağ erişimi gerekmez. `pypdf` isteğe
bağlı birleştirme bağımlılığıdır; temel QA gereksinimlerinin parçası değildir.
Gerekirse seçtiğiniz Python ortamına `python3 -m pip install pypdf` ile kurulur.

Proje kökünden aşağıdaki örnek ayrı bir doğrulama dosyası oluşturur. Kayıtlı
atlasın üzerine yazmaz; hedef dosya varsa `xb` açılışı işlemi durdurur.

```bash
python3 - <<'PY'
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader, PdfWriter

records = [r for r in json.loads(Path("config/map_layouts_v1.json").read_text())["layouts"]
           if r.get("pdf_export", True)]
assert len(records) == 13
writer = PdfWriter()
source_hashes = []
for record in records:
    reader = PdfReader(Path("outputs/maps/pdf") / (record["output_stem"] + ".pdf"))
    assert len(reader.pages) == 1
    source_hashes.append(hashlib.sha256(reader.pages[0].get_contents().get_data()).digest())
    writer.append(reader)
assert len(writer.pages) == 13
writer.add_metadata({
    "/Title": "Çanakkale Afet Öncelik Harita Atlası",
    "/Author": "Enes Göker",
    "/Subject": "Eğitim amaçlı MCDA | © OpenStreetMap contributors © CARTO | Kaynaklar: outputs/atlas/README.md",
})
target = Path("outputs/temp/atlas_review/atlas.pdf")
target.parent.mkdir(parents=True, exist_ok=True)
with target.open("xb") as stream:
    writer.write(stream)
writer.close()
merged = PdfReader(target)
assert len(merged.pages) == 13
assert [hashlib.sha256(p.get_contents().get_data()).digest() for p in merged.pages] == source_hashes
print("13 sayfa; kaynak sırası ve sayfa içerik akışları eşleşti.")
PY
```

PDF birleştiricinin sürümü veya metadata, atlasın dosya baytlarını değiştirebilir.
Burada yeniden üretim güvencesi; sayfa sayısı, sırası ve her sayfanın kaynak
PDF ile içerik akışı eşliğidir. Farklı üretimlerde aynı atlas dosyası hash'i
oluşacağı iddia edilmez. Atıf ve dağıtım kapsamı için
[atlas notu](../outputs/atlas/README.md) ürünle birlikte korunur.
