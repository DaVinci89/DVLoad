[app]
title = DVLoad
package.name = dvload
package.domain = org.davinci
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,mp3,mp4,json,spec,html
version = 1.0.0
requirements = python3,kivy,flask,requests,yt-dlp,ffmpeg,android,pyjnius
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.1.0
fullscreen = 0
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 30
android.minapi = 21
android.ndk = 23b
android.sdk = 30
android.arch = arm64-v8a
android.allow_backup = True
android.add_src =
android.add_assets =
android.add_jar =
android.add_android_meta_data =
android.gradle_dependencies =
android.enable_androidx = True
android.enable_gradle = True
# Важливо: додаємо yt-dlp та ffmpeg як бінарники
# В іншому випадку потрібно включити рецепти в python-for-android
# Для простоти ставимо через `p4a` --bootstrap sdl2 --requirements ...
# Але в buildozer автоматично підхоплює yt-dlp та ffmpeg, якщо вони є в requirements.
# Також можна додати їх через `p4a.branch` тощо.