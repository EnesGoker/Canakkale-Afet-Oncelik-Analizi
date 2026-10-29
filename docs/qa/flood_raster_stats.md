# Flood RP100 Depth Raster Teknik QA

## Durum

KABUL EDİLDİ

## Raster Özellikleri

- Kaynak: `data/processed/flood/canakkale_flood_rp100_depth_32635.tif`
- CRS: `EPSG:32635` — **PASS**
- Raster boyutu: `1763 x 1582` pixels
- Pixel size X: `90.0`
- Pixel size Y: `90.0`
- Pixel size QA: **PASS**
- NoData değeri: `-9999.0` — **PASS**
- Extent: `386370.0000000000000000,4367430.0000000000000000 : 545040.0000000000000000,4509810.0000000000000000`

## Değer Bütünlüğü

- Geçerli hücreler: `40589`
- NoData hücreleri: `2748477` / `98.5447%`
- Negatif geçerli hücreler: `0` — **PASS**
- Minimum geçerli depth: `0.10000000149011612`
- Maximum geçerli depth: `15.041999816894531`
- Mean geçerli depth: `1.3586`
- Standard deviation: `1.453`

## Flood Depth Dağılımı

- `0 m` hücreleri: `0` / `0.0%`
- `> 0 m` hücreleri: `40589` / `100.0%`
- `> 0.1 m` hücreleri: `40589` / `100.0%`
- `> 0.5 m` hücreleri: `31488` / `77.5777%`
- `> 1 m` hücreleri: `16912` / `41.6665%`
- `> 2 m` hücreleri: `6904` / `17.0095%`
- `> 5 m` hücreleri: `1461` / `3.5995%`
- `> 10 m` hücreleri: `180` / `0.4435%`

## Yorum

- Bu raster RP100 flood depth input değerlerini temsil eder.
- `0` NoData olarak kullanılmaz.
- `-9999` NoData olarak korunmuştur.
- Raster Çanakkale AOI sınırına clip edilmiş ve EPSG:32635 sisteminde saklanmıştır.
- Bu katman flood hazard-supporting input niteliğindedir; tek başına nihai risk/kırılganlık/maruziyet çıktısı değildir.
