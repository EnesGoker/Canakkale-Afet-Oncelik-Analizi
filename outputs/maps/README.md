# QGIS haritaları ve ortak kaynak açıklaması

**Kaynak sürümü kapsamı:** Bu belge tam yerel çalışmanın harita ürünlerini
ve kaynak kayıtlarını açıklar. Aşağıdaki PNG/PDF ve atlas yolları yerel
çıktılardır; mevcut kaynak ve analitik özet sürümünde bu görseller dağıtılmaz.
Manifest yalnız yerel ürünlerin üretim/bütünlük kanıtıdır; mevcut sürümün
içerik listesi değildir. [Kamu dosya kapsamı](../../docs/publication_file_scope.md).

Tam yerel çalışmada bu klasörde 13 A3 yatay haritanın PNG (`outputs/maps/png/`) ve PDF (`outputs/maps/pdf/`) sürümleri bulunur.
01–12, öncelik sınıfı ve kriter haritalarıdır; 13, senaryo ortaklığı
haritasıdır. Çıktılar ilgili QGIS düzenleriyle ve checksum manifestiyle izlenir.
Aynı sıra 13 sayfalık atlasta (`outputs/atlas/canakkale_afet_oncelik_harita_atlasi.pdf`) kullanılır.

**13 haritanın tamamı için ortak taban haritası atfı:**
© [OpenStreetMap contributors](https://www.openstreetmap.org/copyright),
© [CARTO](https://www.carto.com/attribution/); CartoDB Positron.
Bu görünür açıklama, haritaların yanındaki ortak kaynak açıklamasıdır.
Bir harita tek başına başka yerde gösterilirse bu atıf yanında korunmalıdır.
PDF metadata'sı görünür atfın yerine kullanılmaz.

Tematik kaynaklar; AFAD TDTH (PGA), MTA (fay), USGS tabanlı VS30,
WorldPop (nüfus), Microsoft/OSM (yapı), JRC (taşkın), HydroRIVERS/OSM
(hidrografya), DEM (eğim), ESA WorldCover (arazi örtüsü), Copernicus HRL Tree Cover Density
(ağaç örtüsü) ve OSM (yol)
veri zincirlerinden türetilmiştir. Ürün/sürüm, veri şeceresi ve koşullar için
[kaynak envanteri](../../docs/data_source_inventory.md) ve
[veri hakları kaydı](../../docs/data_rights_and_distribution.md) esas alınır.
İdari sınırlar çalışma alanı referansıdır; HGM'nin resmî sınır ürünü olarak sunulmaz.

Haritalar eğitim amaçlı, 100 m gridde **göreli öncelik** ön değerlendirmesidir;
resmî tehlike/risk haritası değildir. 13. sayfada yüksek, her senaryonun 4. ve 5.
sınıfıdır. Değer 0 güvenli anlamına gelmez; değer 3 yalnız seçilmiş üç senaryoda
ortaklığı ifade eder. Ağırlık değişimi ve senaryoya özgü normalizasyon birlikte
karşılaştırılır. [Sonuçların yorumu](../../docs/analysis/scenario_agreement.md).

Bu teknik çıktıların hazırlanması, üçüncü taraf verilerin yeniden dağıtım
koşullarının tamamlandığı anlamına gelmez. [Yayın durumu](../../PUBLICATION_STATUS.md)
ve veri hakları kaydındaki açık konular kamu yayını öncesinde ele alınacaktır.

[Harita/stil sözleşmesi](../../config/map_layouts_v1.json),
[çıktı manifesti](map_export_manifest.json) ve [kontrol kaydı](../../docs/qa/map_export_qa.md)
teknik bütünlüğü izler. Tasarım değişikliği gerekiyorsa sözleşme ve çıktılar
birlikte gözden geçirilir; kayıtlı checksum tek başına görsel doğruluk kanıtı değildir.

CARTO anahtarı yalnız yeniden üretim sırasında özel ortam girdisi olarak kullanılır.
Genel QGIS projesi anahtar içermez; hazır çıktıların kontrolü internetsiz yapılır.
[Üretim ve kontrol kaydı](../../docs/qa/map_export_qa.md).
