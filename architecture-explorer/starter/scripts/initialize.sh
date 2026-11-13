#!/bin/sh
set -eu
"${PYTHON:-python}" -m packages.db
if [ ! -f "${ATLAS_DATA:-.data}/models/active-models.json" ]; then
  "${PYTHON:-python}" -m ml.train
fi
