# HRL Tree Cover Density 2021 Raster Teknik QA

## Durum

KABUL EDİLDİ

## Raster Özellikleri

- Kaynak: `data/processed/landcover/canakkale_tree_cover_density_2021_32635.tif`
- CRS: `EPSG:32635` — **PASS**
- Raster boyutu: `15858 x 14228` pixels
- Pixel size X: `10.0`
- Pixel size Y: `10.0`
- Pixel size QA: **PASS**
- NoData değeri: `255` — **PASS**
- Extent: `386390.0000000000000000,4367450.0000000000000000 : 544970.0000000000000000,4509730.0000000000000000`

## Değer Bütünlüğü

- Minimum value: `0`
- Maximum value: `255`
- Unique value count: `98`
- Beklenmeyen değerler: `[]`
- Değer bütünlüğü QA: **PASS**

## Dağılım Özeti

- Toplam hücre: `225627624`
- NoData hücreleri: `127525793` / `56.5205%`
- Geçerli tree cover density hücreleri: `98101831`
- Mean tree cover density: `31.4682`

## Önemli Değer Sayıları

- `0`: `51756301`
- `1`: `841`
- `10`: `4499`
- `25`: `54895`
- `50`: `575534`
- `75`: `821141`
- `100`: `497`
- `254`: `0`
- `255`: `127525793`

## Yorum

- HRL Tree Cover Density 0-100 aralığında vegetation density input olarak ele alınır.
- `0` geçerli değerdir ve hiç ağaç örtüsü yok ya da çok düşük ağaç örtüsü anlamına gelir.
- `255` NoData olarak kullanılır.
- Nearest Neighbor resampling kullanılmıştır.
- Nihai raster Çanakkale AOI sınırına clip edilmiş ve EPSG:32635 sisteminde saklanmıştır.
- Bu katman vegetation density / wildfire susceptibility yorumu için destek girdisidir; tek başına nihai hazard çıktısı değildir.
