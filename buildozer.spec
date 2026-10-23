[app]

# Uygulama bilgileri (title, package.name, package.domain ve version zorunludur)
title = Lugat
package.name = lugat
package.domain = org.kelime
source.dir = .
source.include_exts = py
source.exclude_dirs = tests, bin, .github, .buildozer
version = 1.0.0

# Kivy 2.3.0 + pyjnius (sözlük adresini Android'de tarayıcıda açmak için)
requirements = python3,kivy==2.3.0,pyjnius

orientation = portrait
fullscreen = 0

# Uygulama internete kendisi bağlanmaz, adresi tarayıcıya devreder
android.permissions =

# Kivy 2.3.0 ile birlikte denenmiş sürüm kombinasyonu (python-for-android v2024.01.21 + NDK 25b)
p4a.branch = v2024.01.21
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
