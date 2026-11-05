[app]
title = ATLAS Go
package.name = mobility
package.domain = org.atlas
source.dir = .
source.include_exts = py,png,kv,ttf,json
source.exclude_dirs = tests,docs,releases,scripts,.venv,local-data
version = 1.0.0
requirements = python3,kivy==2.3.1
orientation = portrait
fullscreen = 0
icon.filename = assets/icon.png
presplash.filename = assets/presplash.png
presplash.color = #F6F7F2
android.api = 36
android.minapi = 26
android.ndk = 28c
android.ndk_api = 26
android.archs = arm64-v8a, x86_64
android.accept_sdk_license = True
android.allow_backup = False
android.release_artifact = aab
android.debug_artifact = apk
android.permissions =
p4a.branch = develop
p4a.commit = 1c9a4b4f817847bd8505d972d1a0e6f965929a88
[buildozer]
log_level = 2
warn_on_root = 0
