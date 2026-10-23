# Lugat: Android APK derlemesi

## Dosyalar
- `main.py`: uygulama kodu (Kivy). Buildozer giriş noktasını `main.py` olarak arar, bu yüzden dosya adı değiştirilmemeli.
- `buildozer.spec`: Android derleme ayarları (paket adı, Android sürümleri, bağımlılıklar).
- `.github/workflows/apk.yml`: APK'yı GitHub sunucularında derler. Kendi bilgisayarında Linux/WSL gerekmez.

## GitHub'da derleme (önerilen)
1. Bu klasörü bir GitHub deposuna yükle (`main` dalı).
2. Depo sayfasında **Actions → Android APK → Run workflow** düğmesine bas.
3. 40–70 dakika sürer (ilk çalıştırmada Android SDK indirilir, sonraki çalıştırmalarda önbellekten hızlanır).
4. Bitince çalıştırma sayfasının altındaki **lugat-apk** dosyasını indir, içinden `.apk` çıkar.
5. APK'yı telefona kopyalayıp kur (Ayarlar'dan "bilinmeyen kaynaklardan kuruluma izin ver" seçilmeli).

## Yerelde derleme (Linux)
    pip install buildozer cython==0.29.36
    buildozer -v android debug
    # çıktı: bin/lugat-1.0.0-arm64-v8a_armeabi-v7a-debug.apk

## Bilinen sınırlar
- Osmanlıca özel harfler (â, î, û, ʿ, ʾ) telefonda varsayılan yazı tipinde eksik görünebilir. Tasarımı değiştirmemek için yazı tipi eklenmedi.
- Geri tuşu uygulamayı kapatır; ayrı bir geri tuşu davranışı tanımlı değil.
- Sözlük adresleri tarayıcıda açılır; uygulama içinde gösterilmez.
