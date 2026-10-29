# GIS çalışma ortamı ve sayısal uyumluluk

**Kaynak sürümü kapsamı:** İlk kamu sürümü kod, yöntem belgeleri, QGIS
proje tanımı ve seçilmiş analitik özetleri içerir. Tam kanonik veriler ve
harita/rapor dosyaları dahil değildir. Bu belgedeki tam analiz, katman ve
çıktı kontrolleri ilgili yerel dosyalar ayrıca sağlandığında çalışır; kaynak
kopyasında eksik girdilerin bildirilmesi beklenir. [Dosya kapsamı](../publication_file_scope.md).

Hazır Word/PDF ve haritaları incelemek GIS Python ortamı istemez.
Tam QA, kaynak→skor dönüşümlerini ve kayıtlı analizleri yeniden hesaplar.

## Doğrulanmış profiller

| Ortam | Tam QA / kapsam |
|---|---|
| QGIS 3.44.10, GDAL 3.12.3, NumPy 2.4.4 | Önceki tam doğrulama geçti. |
| QGIS 3.44.15, kendi GDAL 3.13.3 / NumPy 2.5.2 ortamı | Ana MCDA, korelasyon, senaryo ortaklığı ve QGIS okuması geçer; eğim/taşkın kaynak→skor eşdeğerliği farklıdır. |
| Ayrı GDAL 3.12.3, NumPy 2.4.4 **Accelerate**; QGIS 3.44.15 okuyucusu | **Tam canonical QA geçti.** 8/8 dönüşüm, 28 yerel katman, 13 düzen/27 ürün; ana MCDA 0 farklı hücre. |

Son profil macOS arm64, Python 3.12.16 ve macOS 14+ NumPy wheel'iyle
sınanmıştır. Başka işletim sistemi/BLAS kurulumları bu profille doğrulanmış
sayılmaz. Kod ve kayıtlı rasterlar değiştirilmemiştir.

## macOS arm64 kurulumu

QGIS ayrı uygulama olarak kurulu kalır. Bir Conda/Micromamba kurulumu gerekir.
Yeni/boş ortam ve overlay hedefleri seçin; ortamı proje dışında tutun.

```bash
export GIS_QA_PREFIX="$HOME/.local/share/canakkale-qa/env"
export GIS_QA_NUMPY="$HOME/.local/share/canakkale-qa/numpy-accelerate"
micromamba create --yes --prefix "$GIS_QA_PREFIX" --file config/qa_runtime_macos_arm64/conda-explicit.txt
"$GIS_QA_PREFIX/bin/python" -m pip install --no-deps --only-binary=:all: --require-hashes --target "$GIS_QA_NUMPY" -r config/qa_runtime_macos_arm64/numpy-accelerate.requirements.txt
```

Conda da aynı explicit paket listesini kullanabilir. Listede çekirdek
ortamın 77 sabit paket URL'si bulunur. NumPy wheel URL/SHA-256'sı
[numpy_accelerate.lock.json](../../config/qa_runtime_macos_arm64/numpy_accelerate.lock.json),
paket SHA-256'ları
[package_sha256.json](../../config/qa_runtime_macos_arm64/package_sha256.json)
içindedir. NumPy overlay, Conda'nın yönettiği paketi değiştirmez.

Tam veri kökünde:

```bash
python3 scripts/python/run_compatible_qa.py --gdal-prefix "$GIS_QA_PREFIX" --numpy-overlay "$GIS_QA_NUMPY"
```

`--qgis-app` farklı QGIS.app konumu; `--project-root` taşınmış proje kökü
seçer. Başlatıcı bağımlılık kurmaz. Geçici CLI köprüleri, boşluklu ortam
yollarındaki shebang sorununu ve QGIS/GDAL PROJ verilerinin karışmasını önler;
iş bitince temizlenir. Analizler izole GDAL/NumPy, proje okuması QGIS'in kendi
Python/PROJ/GDAL kaynaklarını kullanır. Asıl QA'nın çıkış kodu korunur.

Matplotlib/Pillow yalnız görsel üretimi ve ilgili regresyon testlerinde
gerekir. Bu testler için 117 paketli
[conda-full-explicit.txt](../../config/qa_runtime_macos_arm64/conda-full-explicit.txt)
aynı yöntemle seçilebilir; NumPy overlay yine kullanılır. Temel QA hazır
figürleri yeniden çizmez. Ortam taşınır bir veri dosyası değildir; başka
kurulum yolunda bu profilden yeniden oluşturulmalıdır.

## GDAL yeniden örnekleme farkı

GDAL 3.13, warper'ın `XSCALE/YSCALE` hesabını ve bilinear/cubic çekirdek
seçimini değiştirdi. GDAL 3.13.3 varsayılanıyla kaynak→skor karşılaştırması:

- Eğim: 398.513 AOI hücresi `1e-6` toleransını aşar; en büyük skor farkı
  yaklaşık `5.38e-5`.
- Taşkın: 28.067 hücre toleransı aşar; en büyük skor farkı yaklaşık `0.14415`.

Eğimde eski kaynak penceresinin sınırda kırpılmasından türeyen ölçek, yeni
çözünürlük oranından farklıdır. Taşkında 90 m→100 m bilinear çekirdek seçimi
farklıdır. Eski GDAL 3.12.3 ortamında sekiz reçetenin tamamı 981.033 AOI
hücresinde mevcut toleransa uyar. GDAL 3.13 desteği ayrı uyumluluk işidir;
kontroller atlanmaz, tolerans artırılmaz veya baseline rasterlar değiştirilmez.

Kaynaklar: [GDAL değişiklik kaydı](https://github.com/OSGeo/gdal/blob/v3.13.3/NEWS.md),
[eski çekirdek](https://github.com/OSGeo/gdal/blob/v3.12.3/alg/gdalwarpkernel.cpp),
[yeni çekirdek](https://github.com/OSGeo/gdal/blob/v3.13.3/alg/gdalwarpkernel.cpp),
[eski kaynak pencere hesabı](https://github.com/OSGeo/gdal/blob/v3.12.3/alg/gdalwarpoperation.cpp),
[warp API](https://gdal.org/en/stable/api/gdalwarp_cpp.html).

## NumPy/BLAS ve korelasyon

Conda-forge NumPy 2.4.4/OpenBLAS ile tek simetrik Pearson çiftinde yaklaşık
`1.0383e-12` fark gözlendi; mevcut `1e-12` karşılaştırma sınırını aştı.
Aynı NumPy sürümünün resmî PyPI macOS arm64/Accelerate wheel'iyle kayıtlı
matris birebir eşleşti: maksimum fark **0**, farklı eleman **0**.
Bu yüzden sabit profil sürüm numarası yanında BLAS backend'ini de kaydeder.
CSV'ler ve tolerans değiştirilmemiştir. [NumPy wheel kaynağı](https://pypi.org/pypi/numpy/2.4.4/json).
