# Python ve hostpython sürümünü Kivy 2.3.0 ile tam uyumlu 3.11.9 sürümüne çivile:
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0,pyjnius

# Sadece modern 64-bit Android mimarisini hedefle (süreyi yarıya indirir):
android.archs = arm64-v8a

# API seviyeleri:
android.api = 34
android.minapi = 24
android.ndk = 25b

# Logların kesilmemesi için hata ayıklama seviyesini 1 yap (hata olursa 2 yaparsın):
log_level = 1
