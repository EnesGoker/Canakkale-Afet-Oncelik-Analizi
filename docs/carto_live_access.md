# QGIS'te canlı CARTO Positron erişimi

**Kaynak sürümü kapsamı:** İlk kamu sürümü kod, yöntem belgeleri, QGIS
proje tanımı, seçilmiş analitik özetleri ve harita PNG görsellerini içerir.
Tam kanonik veriler, harita PDF/atlas ve rapor dosyaları dahil değildir. Bu belgedeki tam analiz, katman ve
çıktı kontrolleri ilgili yerel dosyalar ayrıca sağlandığında çalışır; kaynak
kopyasında eksik girdilerin bildirilmesi beklenir. [Dosya kapsamı](publication_file_scope.md).

Yerel analiz katmanları ve hazır harita/atlas dosyaları web hizmetinden
bağımsızdır. Canlı CARTO altlığı kişisel bir Basemaps anahtarı ister.
Anahtarsız döşemelerde `API KEY REQUIRED` yazısı görülebilir.
[CARTO anahtar ve kullanım açıklaması](https://www.carto.com/basemaps/apikey/).

## Açılış

Kendi anahtarınızı proje dışında bir metin dosyasında, tek satır olarak tutun.
Örnek konum `$HOME/.config/canakkale-disaster-priority/carto_basemap.key`;
macOS/Linux'ta dosya erişimini `chmod 600` ile sınırlandırabilirsiniz.
Anahtarı Git'e, QGIS katman URL'sine veya paylaşılacak komutlara yazmayın.

Tam veri klasörünün kökünden:

```bash
python3 scripts/python/open_qgis_with_carto.py --key-file "$HOME/.config/canakkale-disaster-priority/carto_basemap.key"
```

Önce yalnız yerel hazırlık kontrolü için aynı komuta `--check` eklenir.
Bu kontrol web isteği yapmaz; anahtarın servis tarafından kabul edildiğini
iddia etmez. Varsayılan proje `qgis/canakkale_disaster_priority.qgz` dosyasıdır.
Başka kopya için `--project`, QGIS çalıştırıcısı için `--qgis-bin` kullanılır.
Windows'ta `python3` yerine `py -3` seçilebilir. QGIS ve veriler ayrıca kurulmuş
olmalıdır; kaynak kodu kopyası canonical veri paketinin yerine geçmez.

## Anahtarın kapsamı

Başlatıcı, QGIS'in `--code` desteğiyle yalnız çalışma anında bir ağ isteği
hazırlayıcısı kurar. Anahtar, izin verilen CARTO `light_all` HTTPS döşeme
isteklerine eklenir; sağlayıcı URL'si, QGS/QGZ veya proje ayarları değişmez.
Diğer sunucu, HTTP, farklı port ve stil yollarına anahtar eklenmez. GUI
kimlik doğrulaması başlatılan proje ile sınırlıdır; başka projeye geçildiğinde
anahtar o projenin isteklerine eklenmez.
QGIS'in yerel ağ önbelleği kendi profilinde kalır; yayın paketine alınmaz.

QGIS bu başlatıcıyla yeniden açılmalıdır. Projeye doğrudan çift tıklamak
anahtarı kendiliğinden yüklemez. Kişisel anahtar Git/ZIP'in parçası değildir;
başka kullanıcı kendi anahtarıyla aynı komutu çalıştırır. Geçersiz/süresi dolmuş
anahtar veya ağ hatasında yerel katmanlar ve hazır çıktılar korunur.

Harita atfı `© OpenStreetMap contributors, © CARTO` olarak korunmalıdır.
Canlı erişimin çalışması, veri/harita dağıtım koşullarını değiştirmez.

## Doğrulama

29 Ekim 2026'da QGIS 3.44.15'te gerçek ağ isteği hazırlayıcısı doğrulandı:
QGIS yanıtı doğrudan kimliği doğrulanmış döşemeyle aynı, anahtarsız uyarı
döşemesinden farklıydı. QGIS yeniden açılışında çevre haritası görsel olarak
doğrulandı; proje URL'leri ve kaydedilmiş tasarım değişmedi.
[QGIS 3.44 ağ API'si](https://api.qgis.org/api/3.44/classQgsNetworkAccessManager.html).
