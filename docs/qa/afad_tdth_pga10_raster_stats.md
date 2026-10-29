# AFAD TDTH PGA %10 Manual IDW Raster Teknik QA

## Durum

KABUL EDİLDİ

## Raster Özellikleri

- Kaynak: `data/processed/earthquake/canakkale_afad_tdth_pga10_32635.tif`
- Yöntem: `Manual IDW`
- Input field: `pga_10pct`
- Distance coefficient / power: `2.0`
- Raster boyutu: `159 x 143` pixel
- Pixel size X: `1000.0`
- Pixel size Y: `1000.0`
- Pixel size QA: **PASS**
- NoData değeri: `-9999.0`
- Extent: `386000.0,4367000.0 : 545000.0,4510000.0`

## Girdi Nokta Değer QA

- Girdi nokta sayısı: `106`
- Girdi PGA min: `0.28964725`
- Girdi PGA max: `0.7597009`
- Girdi PGA mean: `0.3780405633018869`

## Raster Değer Bütünlüğü

- Toplam hücre: `22737`
- Geçerli hücre: `9822`
- NoData hücreleri: `12915`
- Minimum PGA: `0.29068878293037415`
- Maximum PGA: `0.7565720081329346`
- Mean PGA: `0.37453457713127136`
- Standard deviation: `0.06239595636725426`
- Negatif geçerli hücre: `0`
- 1.5g üzerindeki değerler: `0`

## Yorum

- Bu raster AFAD TDTH nokta parametrelerinden kontrollü manual IDW interpolation ile üretilmiştir.
- Input field `pga_10pct`, 50 yılda %10 aşılma olasılığı için PGA değerini temsil eder.
- Yanıltıcı yüksek çözünürlük hassasiyeti üretmemek için çıktı çözünürlüğü 1000 m seçilmiştir.
- Bu türetilmiş bir sismik tehlike-destek yüzeyidir; resmi AFAD raster ürünü değildir ve bina düzeyi deprem risk haritası olarak yorumlanmamalıdır.
