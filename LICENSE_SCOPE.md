# Lisans kapsamı

[English](#license-scope-english) | Türkçe

## Özgün yazılım

[MIT lisansı](LICENSE), Enes Göker'in bu projedeki `scripts/` altında bulunan
özgün Python ve Bash yazılımına uygulanır. Yazılımın kopyalarında lisans ve
telif bildirimi korunmalıdır. Bağımlılıkların kendi lisansları geçerlidir.

## Rapor, belgeler, haritalar ve veriler

MIT, deponun bütün içeriğine verilmiş bir veri veya rapor lisansı değildir.
GitHub'ın depo sayfasında gösterdiği "MIT License" etiketi yalnız `LICENSE`
dosyasından okunur ve yalnız `scripts/` için geçerlidir.

| İçerik | Kapsam |
|---|---|
| `scripts/` içindeki özgün yazılım | MIT |
| README, yöntem/QA belgeleri, rapor metni ve özgün kartografik düzen | MIT kapsamında değildir; ayrıca açık içerik lisansı verilmemiştir. Özgün kısımlarda telif Enes Göker'e aittir. |
| `outputs/maps/png/` içindeki 14 harita PNG'si | MIT kapsamında değildir; yeni bir lisans verilmemiştir. Yazarın kartografik katkısı (düzen, semboloji, sınıflama, metin) Enes Göker'e aittir. Görsellerdeki üçüncü taraf içerik (veri katmanları ve CARTO/OpenStreetMap altlığı) kendi koşullarına tabidir; her görselin alt bandındaki atıf ve [statik harita bildirimleri](docs/static_map_attributions.md) geçerlidir. |
| `outputs/tables/` ve `outputs/analysis/` içindeki türev tablolar (CSV, Markdown, JSON manifestler) | MIT kapsamında değildir; yeni bir lisans verilmemiştir. Yazarın sayısal katkısı (hesap, birleştirme, sınıflama) Enes Göker'e aittir. Tabloların türetildiği kaynak verilerin koşulları geçerlidir. |
| `config/` içindeki model tanımları | Ayrı bir açık veri lisansı verilmemiştir. |
| `data/` içindeki kaynak ve türetilmiş veriler | Sağlayıcıların veri koşulları; kaynak ve işlem türüne göre ayrı değerlendirilir. |
| Harita, atlas, tablo ve rapordaki üçüncü taraf içerikler | İlgili veri, görsel ve hizmet koşulları geçerlidir; yalnız yazılım lisansıyla yeniden lisanslanmaz. |
| QGIS, GDAL, Python ve diğer bağımlılıklar | İlgili projelerin kendi lisansları; bu depo onların lisansını değiştirmez. |

Veri atfı, veri kümesini yeniden dağıtma izniyle aynı şey değildir. Ham veri,
işlenmiş veri ve basılı/statik harita için koşullar farklı olabilir.
[Veri hakları kaydı](docs/data_rights_and_distribution.md) ve
[ilk yayın dosyası listesi](PUBLICATION_STATUS.md) bu ayrımı tutar.

Kamu raporu için kişisel bilgi temizliği, raporun içerdiği bütün üçüncü taraf
haritaların paylaşım koşullarının tamamlandığı anlamına gelmez. Proje eğitim
amaçlıdır; kurumların projeyi onayladığı veya sonuçların resmî olduğu ileri
sürülmez.

Lisans kararı: 23 Ekim 2026. MIT metni: [Open Source Initiative](https://opensource.org/license/mit).

## License scope (English)

The [MIT License](LICENSE) applies only to Enes Göker's original Python and
Bash software under `scripts/`. Copies of the software must keep the licence and
copyright notice. Dependencies keep their own licences. The "MIT License" label
that GitHub shows for the repository is read from the `LICENSE` file and covers
`scripts/` only.

| Content | Scope |
|---|---|
| Original software in `scripts/` | MIT |
| READMEs, method/QA documents, report text and the original cartographic layout | Not under MIT; no open content licence is granted. Copyright in the original parts belongs to Enes Göker. |
| The 14 map PNGs in `outputs/maps/png/` | Not under MIT; no new licence is granted. The author's cartographic contribution (layout, symbology, classification, text) belongs to Enes Göker. Third-party content in the images (data layers and the CARTO/OpenStreetMap basemap) stays under its own terms; the attribution band of each image and the [static map notices](docs/static_map_attributions.md) apply. |
| Derived tables in `outputs/tables/` and `outputs/analysis/` (CSV, Markdown, JSON manifests) | Not under MIT; no new licence is granted. The author's numerical contribution (calculation, aggregation, classification) belongs to Enes Göker. The terms of the source data the tables are derived from apply. |
| Model definitions in `config/` | No separate open data licence is granted. |
| Source and derived data in `data/` | The providers' data terms, assessed per source and processing type. |
| Third-party content in maps, atlas, tables and report | The relevant data, image and service terms apply; it is not relicensed by the software licence. |
| QGIS, GDAL, Python and other dependencies | Their own projects' licences; this repository does not change them. |

Attributing a dataset is not the same as permission to redistribute it. Raw
data, processed data and printed/static maps can have different terms. The
[data rights record](docs/data_rights_and_distribution.md) and the
[publication file list](PUBLICATION_STATUS.md) (both in Turkish) keep this
distinction. The project is for education; no institution endorses it and the
results are not official.

Licence decision: 23 October 2026. MIT text: [Open Source Initiative](https://opensource.org/license/mit).
