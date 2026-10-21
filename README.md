# Kelime

Lügatte arama + Arapça kök/türev bulma. PC ve mobil (Flet).

## Çalıştırma
    pip install -r requirements.txt
    flet run

## Test (arayüzsüz çekirdek)
    python -m unittest

## Kendi köklerini ekle
`data/kokler.csv` ile aynı başlıkları kullanarak (kok,kok_ar,kelime,anlam) kullanıcı klasöründe
`benim_kokler.csv` oluştur; uygulama her açılışta ikisini birlikte yükler.

## Paketleme
    flet build apk        # Android
    flet build windows    # Windows
(Ayrıntı: Flet belgeleri)
