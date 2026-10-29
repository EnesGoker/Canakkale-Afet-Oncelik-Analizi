# DEM / Eğim Tutarlılık Kontrolleri

## Durum

Grid uyumluluğu: **PASS**  
Negatif elevation kontrolü: **PASS / küçük caveat**

## Grid Uyumluluğu

- DEM shape: `(4744, 5287)`
- Slope shape: `(4744, 5287)`
- Same shape: `True`
- Same geotransform: `True`
- Same projection: `True`

## DEM Elevation Dağılımı

- Geçerli DEM hücreleri: `10900362`
- Negatif elevation hücreleri: `661`
- Negatif elevation yüzdesi: `0.0061%`
- 0-10 m hücreleri: `419990` / `3.853%`
- 0-50 m hücreleri: `1603266` / `14.7084%`
- >=1000 m hücreleri: `65925` / `0.6048%`

## Slope Dağılımı

- Geçerli slope hücreleri: `10900362`
- Slope > 15° hücreleri: `2563881` / `23.5211%`
- Slope > 30° hücreleri: `87378` / `0.8016%`
- Slope > 45° hücreleri: `887` / `0.0081%`

## Yorum

- Raster overlay işlemleri için DEM ve slope rasterları aynı grid bilgisini paylaşmalıdır.
- Negatif elevation değerleri otomatik olarak hata kabul edilmez, ancak dokümante edilmelidir.
- Negatif elevation yüzdesi düşükse coastal / DEM artefact caveat olarak ele alınabilir.
- Negatif elevation yüzdesi yüksek olsaydı elevation class kullanımı öncesinde DEM ayrıca incelenmeliydi.
- Low-elevation veya coastal exposure analizlerinde negatif elevation değerleri 0'a clamp edilmeli veya ayrı caveat olarak ele alınmalıdır.
