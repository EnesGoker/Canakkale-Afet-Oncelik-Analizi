# Portable Script Standardı

Proje: Çanakkale çok kriterli afet öncelik alanları analizi

Bu doküman, proje scriptleri için yürütme standardını tanımlar. Amaç,
scriptlerin farklı klasörler, makineler ve kullanıcılar arasında taşınabilir
kalmasını sağlamaktır.

## 1. Proje Kökü

Scriptler proje kökünü kendi konumlarından çözmelidir. Kullanıcıya özel
mutlak proje pathine bağlı olmamalıdır.

Canonical örüntü:

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/project_env.sh"
project_cd_root
```

## 2. Proje Dosya Pathleri

Proje veri pathleri project-relative olmalıdır.

İzin verilen örnekler:

```text
data/processed/analysis/...
data/processed/faults/...
data/reference/...
outputs/...
docs/...
```

Scriptlerde izin verilmeyenler:

```text
kullanıcı home dizini pathleri
yerel volume pathleri
eski sandbox pathleri
eski ham veri pathleri
```

## 3. Araç Bulma

GDAL/QGIS komut satırı araçları yerel bir uygulama pathine hard-code
edilmemelidir. Scriptler araçları `scripts/bash/lib/project_env.sh`
üzerinden çözmelidir.

Çözüm sırası:

1. `GDALINFO` veya `GDAL_CALC` gibi açık araç değişkeni.
2. `GDAL_BIN` dizini.
3. `QGIS_BIN` dizini.
4. `PATH`.

Desteklenen araç değişkenleri:

```text
GDALINFO
GDAL_CALC
GDAL_TRANSLATE
GDAL_RASTERIZE
GDAL_PROXIMITY
OGRINFO
OGR2OGR
GDAL_BIN
QGIS_BIN
```

`PROJ_LIB`, `PROJ_DATA` ve `GDAL_DATA` opsiyonel runtime ortam
değişkenleridir. Yerel GDAL/QGIS kurulumu açık projection veya GDAL data
pathleri gerektirdiğinde sağlanabilirler; ancak scriptler bu pathleri
hard-code etmemelidir.

## 4. Güvenlik

Validation scriptleri için varsayılan operasyonel mod `--check`tir.

`--check` scriptleri sistem temp dizini altında geçici dosyalar oluşturabilir,
ancak proje verisi oluşturamaz, üzerine yazamaz, taşıyamaz veya silemez.

Mutating modlar açık, dokümante edilmiş ve varsayılan dışı olmalıdır.

## 5. Bash Standardı

`scripts/bash` altındaki bash scriptleri şunu source eder:

```text
scripts/bash/lib/project_env.sh
```

Bu helper şunları sağlar:

- script konumundan proje kökü çözümü,
- proje köküne `cd`,
- gerekli dosya kontrolleri,
- runtime araç bulma,
- opsiyonel PROJ ortam aktarımı.

Proje seviyesindeki read-only QA entry point:

```text
scripts/bash/run_canonical_qa.sh --check
```

Proje seviyesindeki rapor tablo entry point:

```text
scripts/bash/generate_report_tables.sh --check
scripts/bash/generate_report_tables.sh --generate
```

`--check` proje verisi açısından read-only çalışır. `--generate`,
`outputs/tables/` altında CSV/Markdown rapor tabloları yazar.

Proje seviyesindeki DOCX rapor build entry point:

```text
scripts/bash/build_academic_report.sh --check
scripts/bash/build_academic_report.sh --build
```

`--check`, input/tool doğrulaması için DOCX'i geçici dizinde build eder.
`--build`, A4 akademik DOCX'i `outputs/report/` altında yazar.

QGIS proje datasource taşınabilirliği ayrı dokümante edilir; çünkü bash script
mantığından farklı olarak `.qgz` proje dosyasının düzenlenmesini gerektirir.
Bkz.:

```text
docs/qgis_project_portability.md
```
