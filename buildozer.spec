[app]

# (zorunlu) Uygulama bilgileri
title = Lugat
package.name = lugat
package.domain = org.kelime
source.dir = .
source.include_exts = py
source.exclude_dirs = tests, bin, .github, .buildozer
version = 1.0.0

# Kivy 2.3.0 + pyjnius: Android'de sözlük adresini tarayıcıda açmak için (Intent)
requirements = python3,kivy==2.3.0,pyjnius

orientation = portrait
fullscreen = 0

# Android izinleri: uygulama internete kendisi bağlanmaz, adresi tarayıcıya devreder
android.permissions =

android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True

# Derleme günlüğü
log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
