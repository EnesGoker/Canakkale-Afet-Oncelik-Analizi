# AFAD TDTH Excel Yapısı

Bu belge kaynak workbook'un şemasını ve kolon eşlemesini açıklar. Ham
koordinat/parametre satırları ve örnek hücre değerleri kaynak sürümüne dahil
edilmez. Workbook kamu veri seçkisinde değildir;
[dağıtım kapsamı](../publication_file_scope.md) geçerlidir.

## Workbook ve sayfalar

- Yerel kaynak yolu: `data/raw/earthquake/afad_tdth/afad_tdth_parametre_degerleri.xlsx`
- Sayfa sayısı: **2**.
- `TDTH PARAMETRE DEĞERLERİ`: 14.039 satır, 18 sütun; ilk üç satır başlık,
  4–14.039 arası 14.036 veri satırıdır.
- `Sayfa1`: bir satır/bir sütun; parametre tablosunun girdisi değildir.

## Kolon şeması

Koordinatlar EPSG:4326'da boylam/enlem sırasındadır. İvme alanları `g`,
PGV alanları `cm/sn` birimindedir. Aşılma olasılıkları 50 yıllık dönem içindir.

| Kaynak sütun | Anlam | Normalize alan |
|---|---|---|
| A | Boylam | `longitude` |
| B | Enlem | `latitude` |
| C | PGA, %2 | `pga_2pct_50yr_g` |
| D | PGA, %10 | `pga_10pct_50yr_g` |
| E | PGA, %50 | `pga_50pct_50yr_g` |
| F | PGA, %68 | `pga_68pct_50yr_g` |
| G | SS, 0,2 sn, %2 | `ss_2pct_50yr_g` |
| H | SS, 0,2 sn, %10 | `ss_10pct_50yr_g` |
| I | SS, 0,2 sn, %50 | `ss_50pct_50yr_g` |
| J | SS, 0,2 sn, %68 | `ss_68pct_50yr_g` |
| K | S1, 1,0 sn, %2 | `s1_2pct_50yr_g` |
| L | S1, 1,0 sn, %10 | `s1_10pct_50yr_g` |
| M | S1, 1,0 sn, %50 | `s1_50pct_50yr_g` |
| N | S1, 1,0 sn, %68 | `s1_68pct_50yr_g` |
| O | PGV, %68 | `pgv_68pct_50yr_cm_s` |
| P | PGV, %50 | `pgv_50pct_50yr_cm_s` |
| Q | PGV, %10 | `pgv_10pct_50yr_cm_s` |
| R | PGV, %2 | `pgv_2pct_50yr_cm_s` |

PGV sütunlarının olasılık sırası ivme sütunlarından farklıdır; eşleme
bu başlık sırasını korur. Analizin birincil destek değişkeni
`pga_10pct_50yr_g` alanıdır. Şema ve satır sayısı, kaynağın edinim tarihi
veya yeniden dağıtım izni yerine geçmez.

[Normalizasyon QA ve toplu istatistikler](afad_tdth_table_normalization.md) ·
[Kaynak dosya kontrolü](afad_tdth_source_check.md).
