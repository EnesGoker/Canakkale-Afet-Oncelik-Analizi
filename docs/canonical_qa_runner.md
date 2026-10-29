# Canonical QA Runner

Bu belge, tam yerel kanonik veri ve çıktı setini salt okunur denetleyen
`run_canonical_qa.sh` girişini açıklar. Kaynak ve analitik özet sürümü bu
veri/harita/rapor setini içermez; yalnız kaynak kopyasını indirmek tam QA'yı
çalıştırmaya yetmez. [Kamu dosya kapsamı](publication_file_scope.md).

## Kullanım

Uyumlu GIS araçları seçilmiş ve tam kanonik dosyalar sağlanmış kökte:

```bash
bash scripts/bash/run_canonical_qa.sh --check
```

macOS arm64'te sabit GIS ortamı kurulduktan sonra tek giriş:

```bash
python3 scripts/python/run_compatible_qa.py --gdal-prefix "$GIS_QA_PREFIX" --numpy-overlay "$GIS_QA_NUMPY"
```

Ortam değişkenleri ve kurulum [uyumluluk rehberinde](qa/runtime_compatibility.md),
tek tek sayısal ve PyQGIS kontrolleri
[bütünlük sözleşmesinde](qa/canonical_integrity_checks.md) açıklanır.
`requirements.txt` tek başına GDAL veya QGIS kurmaz.

Varsayılan ve tek operasyonel mod `--check`'tir. Runner kalıcı analiz verisi
üretmez veya değiştirip silmez. Geçici hesap/QA dosyaları sistem geçici
dizinindedir. Python sözdizimi kontrolü bytecode üretmez; raster kontrolleri
PAM yan dosyası yazımını kapatır. ZIP'teki executable izinlerinden bağımsız
olarak Bash girişi kullanılabilir.

## Kontroller

| Kontrol grubu | Kapsam |
|---|---|
| Ortam ve sözdizimi | Gerekli shell araçları, Python/Bash kaynaklarının ayrıştırılması |
| Yol ve VRT denetimi | Kişisel mutlak yol örüntüleri, yerel VRT politikası ve QGIS kaynak yolları |
| Gerçek QGIS okuması | `QgsProject.read()`, kayıtlı katmanların geçerliliği; web altlığı ayrı atlanır |
| Hesap bütünlüğü | 11 kriterin CRS/grid/AOI/aralıkları; baseline ham, normalize ve sınıf sonuçları |
| Dönüşümler ve baseline | Sekiz kaynak→skor reçetesi ve sabit 27 girdinin checksum'ları |
| Tablolar ve ek analizler | Rapor/duyarlılık tabloları, korelasyon ve senaryo ortaklığı karşılaştırmaları |
| Harita düzenleri ve ürünler | 13 düzen, stil/lejant kilitleri, QGS/QGZ eşliği ve 27 harita/atlas dosyası |

Gerçek PyQGIS okuması zorunlu bütünlük kontrolüdür; yalnız algoritma
listelemek proje okuması olarak kabul edilmez. GDAL Python, NumPy veya
PyQGIS eksikliği başarılı kontrol sayılmaz. Web/XYZ erişimi çevrimdışı
QA'da sınanmaz; CARTO görünümü ve görsel kabul ayrıca ele alınır.

## Doğrulanmış tam yerel sürüm

29 Ekim 2026'da ayrı GDAL **3.12.3**, NumPy **2.4.4 / Accelerate** ve native
QGIS **3.44.15** okuyucusuyla tam canonical QA geçmiştir. 28 yerel katman,
13 düzen/27 harita ürünü, 981.033 AOI hücresi ve baseline hesapları bu
kapsamdadır. 272 proje regresyon testi geçmiştir. Bu sonuçlar, verileri ve
ürünleri içermeyen kaynak sürümünde tam QA'nın çalıştığı anlamına gelmez.

Arazi örtüsünün AOI dışındaki 5.272 geçerli hücresi belgelenmiş, sınırlı
uyarıdır; diğer girdiler veya sonuçlar için maske muafiyeti oluşturmaz.
GDAL 3.13.3'ün varsayılan eğim/taşkın yeniden örneklemesi eski reçetelerden
farklıdır; uyumlu profil yerine toleranslar değiştirilmez.

## Çıkış kodları ve üretim

- **0:** Bütün zorunlu kontroller geçti.
- **1:** Girdi/çıktı veya hesap kontrolü başarısız.
- **2:** GIS bağımlılıkları nedeniyle bütünlük kontrolü tamamlanamadı.

Eksik kanonik dosyalar veya harita ürünleri kaynak kopyasında beklenen eksik
girdilerdir; test kapsamından sessizce çıkarılmaz. QA, gerçek afetlerle
bilimsel doğrulama veya veri paylaşım izni sağlamaz.

Tablo üretimi açıkça ayrı çağrılır:

```bash
bash scripts/bash/generate_report_tables.sh --generate
```

Bu komut da kanonik raster ve ilçe verilerini gerektirir. Rapor/görsel üretim
araçlarının davranışı [script rehberinde](script_kullanim_ve_guvenlik_rehberi.md)
açıklanır.
