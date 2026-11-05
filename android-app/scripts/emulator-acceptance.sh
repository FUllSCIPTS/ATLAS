#!/usr/bin/env bash
set -euo pipefail
mkdir -p test-output/android
adb install -r release/atlas-go-demo.apk
adb shell am start -n org.atlas.mobility/org.kivy.android.PythonActivity --ez atlas_acceptance true
for attempt in $(seq 1 60); do
  if adb shell run-as org.atlas.mobility cat files/test-output/result.json > test-output/android/result.json 2>/dev/null; then break; fi
  sleep 2
done
adb shell run-as org.atlas.mobility tar -C files/test-output -cf - . > test-output/android-screenshots.tar
tar -xf test-output/android-screenshots.tar -C test-output/android
python scripts/verify-acceptance.py test-output/android
adb logcat -d -b crash > test-output/crash-log.txt
if grep -q 'FATAL EXCEPTION' test-output/crash-log.txt; then exit 1; fi
