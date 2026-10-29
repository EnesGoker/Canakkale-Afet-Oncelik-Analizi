# Çanakkale harita atlası

**Kaynak sürümü kapsamı:** Bu belge tam yerel çalışmanın harita ürünlerini
ve kaynak kayıtlarını açıklar. Aşağıdaki PNG/PDF ve atlas yolları yerel
çıktılardır; mevcut kaynak ve analitik özet sürümünde bu görseller dağıtılmaz.
Manifest yalnız yerel ürünlerin üretim/bütünlük kanıtıdır; mevcut sürümün
içerik listesi değildir. [Kamu dosya kapsamı](../../docs/publication_file_scope.md).

Atlas PDF (`outputs/atlas/canakkale_afet_oncelik_harita_atlasi.pdf`), 13 A3 yatay sayfadan oluşur:
ilk sayfa birleşik MCDA öncelik sınıfı, 2–12 kriter haritaları, 13 ise üç
senaryoda yüksek öncelik ortaklığıdır. Sayfalar ilgili QGIS düzenlerinden
üretilmiş tekil PDF'lerin 01–13 sırasıyla birleştirilmesiyle oluşturulur.
Korelasyon figürü ayrı analiz çıktısıdır ve bu atlasın sayfa sayısına dahil değildir.

**Atlas için ortak taban haritası atfı:**
© [OpenStreetMap contributors](https://www.openstreetmap.org/copyright),
© [CARTO](https://www.carto.com/attribution/); CartoDB Positron.
Atlas başka yerde gösterildiğinde bu açıklama yanında korunmalıdır.
Ayrıntılı tematik kaynaklar, eğitim amaçlı kullanım ve dağıtım durumu
[haritaların ortak açıklamasında](../maps/README.md) verilmiştir.
Bu çalışma resmî tehlike/risk veya sınır ürünü değildir.

[Çıktı manifesti](../maps/map_export_manifest.json), atlasın 13 sayfalı,
tekil haritaların birer sayfalı olduğu üretim kontrolünü ve SHA-256 kayıtlarını
tutar. Sonraki QA bu baytları doğrular; PDF'yi yeniden çizmez.
