#!/usr/bin/env bash
set -euo pipefail
: "${ATLAS_UPLOAD_KEYSTORE:?Private keystore path required}"
: "${ATLAS_UPLOAD_ALIAS:?Upload alias required}"
: "${ATLAS_UPLOAD_PASSWORD:?Upload password required}"
input=${1:?Unsigned AAB required}
output=${2:?Output AAB required}
mkdir -p "$(dirname "$output")"
cp "$input" "$output"
jarsigner -keystore "$ATLAS_UPLOAD_KEYSTORE" -storetype PKCS12 -storepass:env ATLAS_UPLOAD_PASSWORD -keypass:env ATLAS_UPLOAD_PASSWORD -sigalg SHA256withRSA -digestalg SHA-256 "$output" "$ATLAS_UPLOAD_ALIAS"
jarsigner -verify "$output"
