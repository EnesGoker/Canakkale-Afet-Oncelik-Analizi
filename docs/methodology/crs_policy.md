# CRS Politikası

Ham veri, kendi özgün CRS bilgisinde korunur.

Tüm işlenmiş analiz katmanları şu sisteme standardize edilir:

`EPSG:32635 - WGS 84 / UTM Zone 35N`

Gerekçe:

Çanakkale UTM Zone 35N içinde yer alır. Mesafe, buffer, alan, yoğunluk ve
overlay hesapları coğrafi koordinatlar üzerinde doğrudan değil, projected CRS
üzerinde yapılmalıdır.
