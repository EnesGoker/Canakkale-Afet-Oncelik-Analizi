# Bilimsel Sınırlılıklar

Bu proje kesin bir afet risk haritası değildir.

Çanakkale için afet duyarlılığı, maruziyet, kırılganlık proxy'leri ve mekânsal
öncelik alanlarını inceleyen GIS tabanlı çok kriterli bir ön değerlendirmedir.

Önemli sınırlar:

- Nehirlere yakınlık, taşkın riskiyle aynı şey değildir.
- Diri faylara yakınlık, deprem riskiyle aynı şey değildir.
- Eğim, heyelan riskiyle aynı şey değildir.
- MTA WMS üzerinde belirlenen `mta:YERHEYELAN` katmanı, indirilebilir/nicel
  GIS girdisi olarak kullanılamadığı için MCDA kriteri değildir.
- Ağaç örtüsü yoğunluğu, yangın riskiyle aynı şey değildir.
- Building footprint verisi maruziyeti temsil eder; yapısal kırılganlığı temsil etmez.
- PGA değerleri sismik tehlike / yer hareketi parametrelerini temsil eder; doğrudan bina hasarı anlamına gelmez.
- JRC/CEMS flood raster resmi yerel taşkın risk haritası değildir.
- Baseline MCDA ağırlıkları AHP, resmi uzman anketi veya gözlenmiş afet kaybı kalibrasyonu ile üretilmiş nihai karar ağırlıkları değildir.
- Üç senaryolu sensitivity/robustness kontrolü, ağırlık varsayımına duyarlılığı görünür kılar; kapsamlı Monte Carlo, AHP tutarlılık testi veya kurumsal ağırlık kararı yerine geçmez.
- Alternatif senaryolar kendi gözlenen min/max ölçeğini kullanır; sınıf farkları
  ağırlık değişimiyle yeniden ölçeklemenin birleşik etkisini içerir.
- Bazı kaynakların AOI içindeki NoData hücreleri mevcut skor reçetesinde 0'a
  karşılık gelir. Bu, o hücrelerde tehlike yokluğunun ölçülmesi anlamına gelmez.
- PGA/eğim ölçekleme parametrelerinin tarihsel seçme kuralı tam izlenemiyor;
  mevcut dosyalara sayısal eşdeğer reçete, geçmiş üretim niyetinden ayrı tutulur.
- Fay kaynağı AOI'ye kırpılmıştır; dış fay geometrisi bulunmadığı için çevre
  fayların iç alan üzerindeki etkisi tamponlu kaynakla doğrulanmamıştır.
- Çıktı tarihsel afet kayıpları, saha gözlemi veya resmi olay envanteriyle kalibre edilmiş doğrulanmış risk modeli değildir.
- Kaynak yılı veya extract tarihi proje metadata'sında kayıtlı olmayan upstream kaynaklarda yıl/sürüm belirsizliği ayrıca belirtilmelidir.
- Yeniden üretilebilirlik kapsamı, büyük upstream ham veri paketlerinden değil,
  processed-canonical analiz seviyesinden başlayan script, tablo ve rapor
  üretiminden tanımlanır.

Tüm kriterler proxy gösterge olarak kullanılır ve dikkatli yorumlanmalıdır.
