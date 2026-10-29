# Sınır bulguları: fay kaynağı ve arazi örtüsü

İnceleme: **23–24 Ekim 2026**. Mevcut raster/vektörler değiştirilmedi.

## Fay yakınlığı: doğrulanan ve doğrulanamayan kapsam

132 veri dosyası, 21 GeoPackage'ın katmanları ve korunan portable ZIP
incelendi. Kullanılabilir tek fay kaynağı AOI'ye kırpılmış
`data/processed/faults/canakkale_faults_final_32635.gpkg` dosyasıdır.
ZIP'teki kopya da aynı hash'e sahiptir; AOI dışında devam eden ayrı ulusal
veya bağlam fay geometrisi bulunmadı.

207 obje, yaklaşık **476,893 km** toplam uzunluk taşır. Mevcut kaynak,
100 m rasterizasyon, GDAL GEO distance ve 10 km doğrusal yakınlık dönüşümüyle
yeniden hesaplandığında **981.033 AOI hücresinde fark 0** verir. Bu, mevcut
kaynakla hesap tutarlılığını doğrular.

AOI dışındaki bir fayın içerideki hücreye daha yakın olup olmadığı, yalnız
kırpılmış kaynakla sınanamaz. Kırpılmış veri bulunması tek başına skorun
yanlış olduğunu göstermez; dış geometrinin etkisiz olduğunu da kanıtlamaz.
Bu nedenle tamponlu sonuç ve gerçekten etkilenen alan hesaplanmış gibi
sunulmamıştır. AOI dışı fay geometrisi bulunmadığından tamponlu yeniden
hesaplama ve sınır etkisi karşılaştırması bu doğrulamanın kapsamı dışındadır.

Gelecekte sınamak için AOI dışında en az skorun 10 km etki mesafesini kapsayan
fay geometrisi gerekir. Raster kapsamı mevcut orijine 100 m katlarıyla
hizalanarak genişletilmeli; aynı rasterizasyon/mesafe yöntemiyle hesaplanan
sonuç yalnız orijinal AOI üzerinde karşılaştırılmalıdır. Sadece çizgiyi
AOI'ye kırpmak veya yeni grid orijini seçmek uygun karşılaştırma değildir.

## Arazi örtüsü: geçerli kenar hücrelerinin izolasyonu

10 m kategoriler önce Float32 skora çevrilip 100 m **average** ile yeniden
örneklendiğinde kayıtlı skorun **986.305 geçerli hücresi ve GDAL maskesi**
birebir yeniden elde edildi. Bunların **5.272'si şablon AOI'si dışındadır**.
Kategori bütünlüğü bozulması bulunmadı.

Bu fark, average'ın kısmen geçerli kaynak alanıyla kesişen hedef hücrelere
değer verebilmesiyle uyumludur. Şablonun AOI hücre seçimi ayrıca uygulanır;
“kaynak kategorilerinin tamamı yanlış” sonucu çıkarılmaz.

Seçilen yol, kaynak rasterı sessizce değiştirmek yerine **analiz girdisini
AOI içinde izole etmektir**. [Ortak baseline yükleyicisi](../../scripts/python/analysis_baseline.py)
yalnız template==1 hücrelerini ayrı kopyalara alır. AOI içinde arazi örtüsü
farkı `0`; dış hücre katkısı `0`; mevcut ham/normalize/sınıf sonucu farkı `0`.
Mevcut harita ve referans çıktılar bu nedenle yeniden üretilmemiştir.

QA, bilinen dış hücreleri görünür uyarı olarak tutar. İstisna yalnız bu
kriterde en fazla 5.272 hücre içindir; geçersiz değer, büyüyen taşma veya
başka kriter/nihai çıktıda taşma başarısız olur. Baseline dosya checksum'u
da değişmiş kaynağı ayrıca yakalar.

İki ek analizde AOI izolasyonu, bütün dikdörtgen rasterın veya yalnızca
`NoData olmayan` arazi örtüsü hücrelerinin seçilmesiyle değiştirilemez.
