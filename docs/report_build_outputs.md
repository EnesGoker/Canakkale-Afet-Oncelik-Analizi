# Akademik Rapor DOCX Üretim Sözleşmesi

**Kaynak sürümü kapsamı:** Aşağıdaki harita, raster, atlas ve Word/PDF
yolları tam yerel çalışma çıktısıdır; bu dosyalar kaynak ve analitik özet
sürümünde dağıtılmaz. Yerel üretim/kontrol komutları ilgili kanonik veri ve
çıktıların ayrıca bulunmasını gerektirir. [Kamu dosya kapsamı](publication_file_scope.md).

Proje: Çanakkale çok kriterli afet öncelik alanları analizi

Kamu raporunun düzenlenebilir ana kaynağı
`outputs/report/canakkale_disaster_priority_public_report.docx`
dosyasıdır. 18 sayfalık PDF (`outputs/report/canakkale_disaster_priority_public_report.pdf`),
raporun okuma kopyasıdır. Aşağıdaki script sözleşmesi ayrı akademik DOCX
üreticisini tanımlar; hazır kamu Word raporunu yeniden üretmez.

## 1. Script

Giriş noktası:

```text
scripts/bash/build_academic_report.sh
```

Modlar:

```text
--check
--build
```

`--check`, raporu sistem geçici dizininde üretir ve girdi/tooling doğrulaması
yapar.

`--build`, DOCX raporunu şu konuma yazar:

```text
outputs/report/canakkale_disaster_priority_academic_report.docx
```

Bash entry point, proje kökünü kendi konumundan çözer ve Python builder'ı
çalıştırır. Python runtime içinde `python-docx` ve `Pillow` bulunmalıdır.

## 2. DOCX Girdileri

DOCX builder yalnızca tanımlı rapor varlıklarını kullanır:

| Girdi grubu | Konum |
|---|---|
| Rapor varlık sözleşmesi | `docs/report_asset_outline_lock.md` |
| Kaynak envanteri | `docs/data_source_inventory.md` |
| Canonical veri politikası | `docs/canonical_data_policy.md` |
| Metodoloji notları | `docs/methodology/` |
| Harita PNG'leri | `outputs/maps/png/` |
| Rapor tabloları | `outputs/tables/` |

Büyük upstream ham veri setleri DOCX build girdisi değildir.

## 3. DOCX Çıktı Hedefi

| Özellik | Değer |
|---|---|
| DOCX hedef path | `outputs/report/canakkale_disaster_priority_academic_report.docx` |
| Sayfa düzeni | A4 dikey |
| Ana gövde haritaları | 12 |
| Ana tablolar | MCDA sınıf dağılımı, veri kaynakları, ağırlıklar, yüksek öncelikli ilçe özeti |
| Ek tablolar | İlçe sınıf alanları, raster istatistikleri |

## 4. Görsel QA

DOCX üretiminden sonra görsel QA için sayfa PNG'lerine render edilir.

QA kabul ölçütleri:

| Kontrol | Kabul ölçütü |
|---|---|
| DOCX açılabilirlik | Headless LibreOffice veya eşdeğer render aracıyla açılabilir |
| Sayfa render çıktıları | Her sayfa PNG olarak render edilir |
| Kapak sayfası | Başlık ve ana metadata okunabilir |
| Ana veri/yöntem tabloları | Tablolar kırpılmadan görünür |
| Haritalar | 12 haritanın tamamı görünür ve kırpılmamış olur |
| Ek tablolar | İlçe ve raster istatistik tabloları okunabilir olur |
| Yerleşim | Belirgin üst üste binme veya kırpılmış metin bulunmaz |
| Erişilebilirlik | High/medium/low bulgu üretilmez |

## 5. Kapsam

DOCX üretim sözleşmesi, `build_academic_report.sh` çıktısını ve yalnız bu
çıktı için gereken QA kapsamını tanımlar. Üretilen
`canakkale_disaster_priority_academic_report.docx`, hazır kamu Word raporundan
ayrı bir hedeftir; kamu dağıtımına otomatik alınmaz.

`a11y_report.json`, içinde adı verilen akademik DOCX için bir kontrol kaydıdır.
Kamu Word/PDF raporunun veya mevcut olmayan render çıktılarının doğrulaması
olarak kullanılamaz. Büyük upstream ham veri setleri bu üreticinin girdisi
değildir.

Pages dosyaları yalnız yerel arşivdir; kamu Git ve portable paket seçimine
alınmaz. Düzenlenebilir kamu kaynağı Word'dür. Raporun güncel dosya hash'leri,
kapsamı ve sürüme özgü kontrol sonuçları
[rapor manifestinde](../outputs/report/public_report_manifest.json) izlenir.

## 6. Kamu Word raporu ile ayrım

Kamu Word raporu 1–9 ana bölümleri; 7. Ek Analizler içindeki 7.1 korelasyon
ve 7.2 senaryo ortaklığı alt bölümlerini içerir. Şekil 1–14 toplam
13 coğrafi harita ve bir korelasyon figürüdür; sekiz veri tablosu
1–6, A1 ve B1 olarak sıralanır. Okuma PDF'si 18 sayfadır.

Yukarıdaki 12 haritalı üretim ve QA kapsamı yalnız akademik DOCX üreticisi için
geçerlidir. Kamu Word ve PDF dosyalarının sayısal, kaynak varlığı, gizlilik ve
görünüm kontrolleri kendi dosya sürümleri üzerinden ayrı değerlendirilir.
