# ESA WorldCover 2021 Raster Teknik QA

## Durum

KABUL EDİLDİ

## Raster Özellikleri

- Kaynak: `data/processed/landcover/canakkale_worldcover_2021_32635.tif`
- CRS: `EPSG:32635` — **PASS**
- Raster boyutu: `15858 x 14228` pixels
- Pixel size X: `10.0`
- Pixel size Y: `10.0`
- Pixel size QA: **PASS**
- NoData değeri: `0`
- Extent: `386390.0000000000000000,4367450.0000000000000000 : 544970.0000000000000000,4509730.0000000000000000`

## Class Bütünlüğü

- Beklenmeyen class value: `[]`
- Class integrity QA: **PASS**

## Class Dağılımı

- Toplam hücre: `225627624`
- NoData hücreleri: `127524087` / `56.5197%`
- Geçerli landcover hücreleri: `98103537`

- `10` — Tree cover: `54619793` cells / `55.6757%`
- `20` — Shrubland: `2835290` cells / `2.8901%`
- `30` — Grassland: `18388670` cells / `18.7441%`
- `40` — Cropland: `19387576` cells / `19.7624%`
- `50` — Built-up: `1409467` cells / `1.4367%`
- `60` — Bare / sparse vegetation: `534477` cells / `0.5448%`
- `70` — Snow and ice: `0` cells / `0.0%`
- `80` — Permanent water bodies: `735889` cells / `0.7501%`
- `90` — Herbaceous wetland: `192375` cells / `0.1961%`
- `95` — Mangroves: `0` cells / `0.0%`
- `100` — Moss and lichen: `0` cells / `0.0%`

## Yorum

- ESA WorldCover categorical rasterdır.
- Class code değerlerini korumak için Nearest Neighbor resampling kullanılmıştır.
- Raster Çanakkale AOI sınırına clip edilmiş ve EPSG:32635 sisteminde saklanmıştır.
- Bu katman input katmanıdır; tek başına nihai hazard/risk çıktısı değildir.
