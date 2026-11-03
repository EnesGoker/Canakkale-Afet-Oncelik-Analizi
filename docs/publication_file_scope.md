# İlk kamu paylaşım kapsamı

Tarih: **3 Kasım 2026** (`v0.2.1`). İlk kaynak sürümü (`v0.1.0`) özgün kod,
model tanımları, yöntem/QA belgeleri, QGIS proje şablonu ve dosya bazında
seçilmiş analitik özetleri kapsar. `v0.2.0` buna görünür atıflı `01`–`14`
harita PNG görsellerini ekler. **Harita PDF'leri, tam sayısal veri
kümesi, rapor/atlas ve yerel portable ZIP dağıtılmaz.**
Kaynak ayrıntıları [veri hakları kaydında](data_rights_and_distribution.md),
genel dosya rolleri [yayın listesinde](../PUBLICATION_STATUS.md) açıklanır.

Kaynak sürümünün tam pozitif dosya listesi
[`config/public_source_release_v1.json`](../config/public_source_release_v1.json)
içindedir. [`build_public_source_release.py`](../scripts/python/build_public_source_release.py)
yalnız bu listedeki dosyaları seçer; `.gitignore` veya Git geçmişi dosya
seçiminin yerine geçmez. Manifest, dosya baytlarını ve SHA-256 değerlerini
kaydeder. Veri gerektiren tam QA ile kaynak seçimi kontrolü ayrı kapsamlardır.

## Kaynak deposu

- `scripts/`: özgün Python/Bash kodu, MIT lisansı ve bağımlılık bildirimleri.
- `.github/workflows/tests.yml`: test katmanlarını ve kamu kapsamı kontrollerini koşan CI tanımı; veri veya anahtar içermez.
- `config/`, `README.md`, `README.en.md`, `docs/`, `LICENSE`, `LICENSE_SCOPE.md`, `PUBLICATION_STATUS.md`, kurulum/bağımlılık dosyaları: yöntem, kullanım, sonuç ve kaynak açıklamaları; [lisans kapsamı](../LICENSE_SCOPE.md) geçerlidir.
- `qgis/canakkale_disaster_priority.qgs` ve `.qgz`: göreli dosya referansları ve kayıtlı düzenler. Kaynak veriler ve kişisel servis anahtarı bu dosyalarla dağıtılmaz; veri olmadan tam proje görüntüsü beklenmez.
- `data/**/.gitkeep`: yalnız klasör iskeleti.
- `outputs/tables/` içindeki seçilmiş CSV/MD ve kaynak manifestleri: il/ilçe
  sınıf alanları, duyarlılık karşılaştırmaları, 11 kriterin Pearson matrisi
  ve dağılım özetleri. `outputs/analysis/scenario_agreement_v1/` içinden yalnız
  üç alan/üyelik/senaryo karşılaştırma CSV'si ve üretim manifesti seçilir.
  `outputs/analysis/weight_perturbation_v1/` içinden sekiz CSV (ağırlık
  örnekleri, OAT, senaryo köprüsü, Monte Carlo, κ, olasılık alanı, ilçe sırası,
  yakınsama) ve üretim manifesti seçilir.
  `outputs/analysis/mcda_variants_v1/` içinden altı CSV (varyant ağırlıkları,
  varyant özeti, ilçe alanları, sınıflandırma özeti ve dağılımı, taşkın kanıtı)
  ve üretim manifesti seçilir.
  Tekil koordinat/değer kayıtları veya raster hücreleri dağıtılmaz.
- Harita/rapor/figür JSON üretim kayıtları yalnız dosya adı, sürüm ve checksum
  kanıtıdır; kayıtta bir ürünün geçmesi ürün baytlarının dağıtıldığı anlamına gelmez.

QGZ şablonu stillerini gömülü taşır. Düz QGS, aynı proje XML'inin
incelenebilir eşidir; bağımsız tam veri teslimi olarak sunulmaz.
AFAD çalışma kitabının QA belgesi yalnız şema/sayfa/sütun eşlemesini açıklar;
ham koordinat ve parametre örnek satırları kaynak sürümünde yer almaz.

Kaynak sürümünde OSM veritabanı sunulmaz. OSM verisi içeren harita
görselleri `© OpenStreetMap contributors` atfını taşır; kodun ve görsellerin
yayımlanması, OSM türevi veritabanı için erişim koşullarının (ODbL 4.6)
tamamlandığı anlamına gelmez.

Bu kapsam, `outputs/` veya `data/` klasörlerinin bütünü için bir dahil etme
kuralı değildir. Rapor/sayısal dosya bağlantıları bulunması, dosyanın ilk
pakete dahil veya yeniden lisanslanmış olduğu anlamına gelmez.

## Kamu harita görselleri

Her kökün yalnız PNG dosyası kamu kapsamındadır: `outputs/maps/png/<kök>.png`.
Dosyalar [paket seçiminde](../config/public_source_release_v1.json) SHA-256
değeriyle sabitlenir; paketleyici sabitlenmemiş, metadata'sı uygun olmayan veya
veri uzantılı dosyayı reddeder. Her görsel ortak ve tema atfını görünür etiket
olarak taşır; tam kredi/değişiklik/sorumluluk metinleri
[statik harita bildirim dosyasındadır](static_map_attributions.md). **OSM türev
veritabanı/değişiklik erişimi** açık kalır.

| Dosya kökü | Temaya özgü bildirim / koşul | Yayın dayanağı |
|---|---|---|
| `01_cok_kriterli_oncelik_sinifi` | On bir kriterin bütün kaynakları ve MTA fay çizgisi. | Atıf; AFAD/MTA izni yok, JRC/HydroSHEDS/USGS kapsamı açık |
| `02_fay_yakinlik_skoru` | Tarihsel MTA diri fay verisi ve fay çizgisi. | Atıf; MTA izni yok |
| `03_nufus_maruziyet_skoru` | WorldPop / University of Southampton, Türkiye 2020 constrained UN-adjusted; WP00685 DOI, CC BY 4.0; kesme/yeniden örnekleme ve log-skor dönüşümü açıklaması. | Lisans koşulu |
| `04_zemin_kosulu_skoru` | USGS Global Vs30 Mosaic, Heath vd. (2020); yerel extract ve bölgesel bileşen kapsamı bilinmiyor. | Atıf; bileşen kapsamı açık |
| `05_deprem_pga_skoru` | AFAD TDTH parametreleri; IDW yüzeyi yazarın türetimi, resmî AFAD ürünü değil. | Atıf; AFAD izni yok |
| `06_yapi_maruziyet_yogunluk_skoru` | Microsoft GlobalML BuildingFootprints ve OSM gap-fill atfı; veri sunulursa CDLA Permissive 2.0 metni; OSM türev veritabanı/erişim düzeni. Microsoft sonuç hükmü OSM yükümlülüğünü kaldırmaz. | Lisans koşulu |
| `07_taskin_skoru` | JRC/CEMS RP100 taşkın derinliği, © European Union, DOI; resmî lisans kayıtları uyuşmuyor. | Atıf; lisans adı yazılmaz, uyuşmazlık açık |
| `08_hidrografya_yakinlik_skoru` | HydroRIVERS v1.0 (Lehner & Grill 2013), HydroSHEDS Ek B bildirimi ve OSM su yolları. | Atıf; türev dağıtım kapsamı açık |
| `09_egim_skoru` | Copernicus DEM GLO-30; değiştirilmiş veriye ilişkin lisans 6(b) ve sorumluluk 6(c) bildirimleri; eğim/100 m grid işlemi açıklaması. | Lisans koşulu |
| `10_arazi_ortusu_duyarlilik_skoru` | ESA WorldCover 2021 v200, CC BY 4.0; ürünün ESA/Copernicus Sentinel kaynak bildirimi ve skor dönüşümü. | Lisans koşulu |
| `11_agac_ortusu_skoru` | Copernicus Land Monitoring Service, HRL Tree Cover Density, Avrupa 10 m, 2021; kaynak ve kesme/projeksiyon/skor değişiklikleri; kurumsal destek izlenimi verilmemesi. | Lisans koşulu |
| `12_yol_erisim_zorlugu_skoru` | OSM yol ağı, ODbL ve değişiklikler; türev veritabanına veya değişiklik yöntemine erişim düzeni. | Lisans koşulu; ODbL 4.6 erişimi açık |
| `13_senaryo_ortakligi` | Üç senaryonun bütünleşik modelinden üretildi; `01` ile aynı kaynaklar (fay çizgisi yok). | Atıf; `01` ile aynı açık noktalar |
| `14_yuksek_oncelik_olasiligi` | Ağırlık pertürbasyonunun 2.000 örneğinden P(yüksek+) ve baseline yüksek+ sınırı; `01` ile aynı kaynaklar (fay çizgisi yok). | Atıf; `01` ile aynı açık noktalar |

Bütün harita görselleri için ortak uygulama:

1. HGM idari sınır kaynağı ve [ürün bağlantısı](https://www.harita.gov.tr/urun/turkiye-mulki-idare-sinirlari/232) korunur; sınırlar gösterim amaçlıdır. Görseller ticari olmayan portföy kapsamındadır; sınırlara MIT/CC0 verilmez.
2. İlçe adları ve taban harita dahil OSM katkıları için `© OpenStreetMap contributors` ve [OSM telif/lisans bağlantısı](https://www.openstreetmap.org/copyright) sağlanır. Basılı/PDF bağlamında URL okunabilir olmalıdır.
3. CARTO Positron kullanılan görsellerde `© CARTO` ve [atıf bağlantısı](https://www.carto.com/attribution/) görünür olur. [Statik belgeleme koşulu](https://www.carto.com/legal/basemap-terms/) karo önbelleğini dağıtma veya servis anahtarını paylaşma izni değildir.
4. Tema kaynağı, referans yıl ve yapılan değişiklikler dosyayla birlikte sunulan okunabilir açıklamada yer alır; bilinmeyen release/edinim tarihi eklenmez.
5. OSM türevi veritabanından üretilmiş eserlerde [ODbL 4.3–4.6](https://opendatacommons.org/licenses/odbl/1-0/) bildirim ve erişim düzeni açıklanır. Yalnız kaynakça eklemek bu kapsamın yerine geçmez; ilgili türev veritabanı veya bütün değişiklikleri sağlayan yöntem/ek içerik sunumu ayrı belirtilir.

Ürüne özgü tam kaynak/lisans bağlantıları için [veri hakları kaydı](data_rights_and_distribution.md) geçerlidir.

AFAD ve MTA verisinden türetilen görseller (`01`, `02`, `05`, `13`, `14`) için yazılı izin alınmamıştır; JRC/CEMS (`07`), HydroRIVERS (`08`) ve USGS Vs30 (`04`) için açık kalan lisans/türev kapsamı çözülmemiştir. Bu görseller bu bilinerek yayımlanmıştır; izin ileri sürülmez ve hak sahibinin talebi halinde ilgili görsel kaldırılır.

## Kamu kapsamının dışındaki dosyalar

| Dosya / grup | Kapsamın açık kalan kısmı |
|---|---|
| `outputs/maps/pdf/*.pdf` | `01`–`13` harita PNG'lerinin PDF eşleri; aynı içeriğin ikinci kopyası olarak yerel kalır. `14` yalnız PNG olarak üretilir. |
| `outputs/figures/scenario_agreement_v1/` | Bütünleşik modelden üretilmiş ayrı senaryo karşılaştırma figürü. |
| `outputs/report/canakkale_disaster_priority_public_report.docx` ve aynı adlı `.pdf` | Tam rapordaki ilgili şekil/eklerin kapsamı. Word ana kaynak, 18 sayfalık PDF okuma kopyasıdır. |
| `outputs/atlas/canakkale_afet_oncelik_harita_atlasi.pdf` | Aynı kaynak kapsamını taşıyan `01`–`13` haritalarının birleşimi. |

`config/map_layouts_v1.json` içinde MTA fay overlay’i yalnız `01` ve `02`
düzenlerindedir. `13` ve `14` bu çizgiyi taşımaz; fay skoru yalnız sayısal model
bağımlılığı olarak içindedir ve atfında anılır.

Tam rapor/atlasın farklı şekil ve ekleri farklı kaynak koşulları taşır;
raporun tümüne genel bir yasak sonucu çıkarılmaz. Özgün yöntem,
formül, yorum ve indirgenmiş korelasyon/alan/senaryo özetleri; doğrudan kaynak
nokta, çizgi veya değerlerinin yeniden sunumundan ayrılır. `outputs/tables/` ve
`outputs/figures/criterion_correlation_v1/` de topluca MIT/CC BY kapsamına
alınmaz; içerik ve kaynak bildirimleri üzerinden ayrı seçilir.

## İlk kamu veri paketine alınmayan 27 somut dosya yolu

Aşağıdaki 27 yol (yan dosyalar dahil) ilk kapsamın dışındadır. Bunlar bir
yasak/ihlal listesi değildir; mevcut yerel dosyaların uygulanabilir dağıtım
dayanağı tamamlanmadan kamuya aktarılmaması için somut seçim listesidir.

### AFAD TDTH — 9 yol

- `data/interim/earthquake/afad_tdth_parameters_4326.csv`
- `data/processed/analysis/earthquake_pga_score_32635.tif`
- `data/processed/analysis/earthquake_pga_score_32635.tif.aux.xml`
- `data/processed/earthquake/canakkale_afad_tdth_pga10_aoi_masked_32635.tif`
- `data/processed/earthquake/canakkale_afad_tdth_pga10_aoi_masked_32635.tif.aux.xml`
- `data/raw/earthquake/afad_tdth/afad_tdth_parametre_degerleri.xlsx`
- `data/reference/earthquake/canakkale_afad_tdth_pga10_32635.tif`
- `data/reference/earthquake/canakkale_afad_tdth_pga10_32635.tif.aux.xml`
- `data/reference/earthquake/canakkale_afad_tdth_points_32635.gpkg`

### MTA — 3 yol

- `data/processed/analysis/fault_proximity_score_32635.tif`
- `data/processed/analysis/fault_proximity_score_32635.tif.aux.xml`
- `data/processed/faults/canakkale_faults_final_32635.gpkg`

### JRC/CEMS — 4 yol

- `data/processed/analysis/flood_score_32635.tif`
- `data/processed/analysis/flood_score_32635.tif.aux.xml`
- `data/processed/flood/canakkale_flood_rp100_depth_32635.tif`
- `data/processed/flood/canakkale_flood_rp100_depth_32635.tif.aux.xml`

### HydroRIVERS / OSM hidrografya — 7 yol

- `data/processed/analysis/hydrography_proximity_score_32635.tif`
- `data/processed/analysis/hydrography_proximity_score_32635.tif.aux.xml`
- `data/processed/hydrography/canakkale_hydrography_hybrid_clean_32635.gpkg`
- `data/reference/hydrography/canakkale_hydrography_hybrid_hydrorivers_osm_32635.gpkg`
- `data/reference/hydrography/canakkale_hydrorivers_32635.gpkg`
- `data/reference/hydrography/canakkale_hydrorivers_aoi_32635.gpkg`
- `data/reference/hydrography/canakkale_osm_waterways_gapfill_32635.gpkg`

### USGS Vs30 — 4 yol

- `data/processed/analysis/site_condition_score_32635.tif`
- `data/processed/analysis/site_condition_score_32635.tif.aux.xml`
- `data/processed/vs30/vs30_aoi_100m_32635.tif`
- `data/processed/vs30/vs30_aoi_100m_32635.tif.aux.xml`

Saf `canakkale_osm_waterways_gapfill_32635.gpkg`, diğer HydroRIVERS/hibrit
dosyalarından farklı olarak ODbL ve atıf/erişim koşullarıyla **ayrı veri paketi
adayıdır**; bu ilk seçkiye otomatik dahil değildir.

## Diğer sayısal çıktılar ve portable paket

- `data/` içindeki diğer kaynak, işlenmiş ve referans veriler de ilk kaynak/görsel seçkisinde dağıtılmaz. Daha sonra kaynağa özgü lisans/bildirimlerle ayrı veri paketi oluşturulabilir.
- `data/processed/analysis/mcda_priority_{score,score_normalized,class}_32635.tif` ve yan dosyaları; `outputs/analysis/scenario_agreement_v1/*.tif`, `outputs/analysis/weight_perturbation_v1/*.tif` ve yan dosyaları kamu kapsamının dışındadır. Eski analiz arşivleri ve yeniden üretim ara dosyaları da bu seçkiye girmez.
- `outputs/tables/` içindeki CSV/MD özetleri, tam kaynak verisi veya rasterla aynı şey değildir. Dosya bazında uygun analitik özetler seçilebilir; klasör bütünü otomatik veri paketi sayılmaz.
- `outputs/report/*.pages`, geçici dosyalar, önbellek ve eski paketler kamu seçkisinde yer almaz.
- `build_portable_release.py --check/--build` yerel teknik paketleme/bütünlük aracıdır. Tam yerel ZIP bu kapsama göre seçilmiş kamu sürümü değildir; teknik testin geçmesi dosyalara yeniden dağıtım izni vermez.

Kaynak edinim tarihleri bilinmeyen alanlarda bilinmiyor olarak korunur.
AFAD/MTA için açık yayın dayanağı, JRC lisans seçimi, USGS bileşen kapsamı ve
HydroRIVERS/OSM hibrit düzeni çözülmeden bu sayısal dosyalar kamu kapsamına
genişletilmez; statik harita görsellerinin yayımlanması bu dosyalar için izin
oluşturmaz. Öğrenci/akademik kullanım tek başına genel yayın izni sayılmaz.
