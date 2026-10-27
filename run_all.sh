#!/bin/bash
# Reproduces every experiment of the manuscript (about 2-3 h on 2 CPU cores).
set -e
cd "$(dirname "$0")"
[ -f results/forecast.json ] || python3 -u run_forecast.py
python3 -u run_ood.py
python3 -u val_preds.py
python3 -u run_anomaly.py
python3 -u run_recovery_mc.py
python3 -u run_bip_timing.py
(cd prototype && python3 -u proto_run.py bench switch recovery)
python3 -u run_cluster.py tune main forecast ablation load sensitivity
python3 -u run_vehicle.py
python3 -u export_datasets.py
python3 -u make_figures.py
