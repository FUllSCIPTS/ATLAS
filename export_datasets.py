"""Write the dataset files described in the manuscript (Section "Data
Composition and Storage Format").  The full 525,600-row trace is produced with
--full; by default a 7-day excerpt is written to keep the package small.
"""
import csv, json, os, sys
from dataclasses import asdict
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from atlas_sim.traffic import ecommerce_trace, telemetry, SERVICES
from atlas_sim.cluster import Params

D = os.path.join(os.path.dirname(__file__), "data"); os.makedirs(D, exist_ok=True)
full = "--full" in sys.argv
r, mask, events = ecommerce_trace(365, seed=2026)
X = telemetry(r, np.random.default_rng(7))
ev_start = {s for s, _, _ in events}
n = len(r) if full else 7 * 1440
# include one complete flash-sale day in the excerpt
s0 = sorted(ev_start)[0]; lo = (s0 // 1440) * 1440
rows = list(range(0, n)) + ([] if full else list(range(lo, lo + 1440)))
with open(os.path.join(D, "traffic_trace.csv" if full else "traffic_trace_excerpt.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["minute", "rps", "cpu_pct", "mem_pct", "latency_ms", "error_rate", "queue_depth",
                "net_MBps", "disk_ms", "anomaly", "failure_class", "coupling_mode"])
    for t in rows:
        x = X[t]
        w.writerow([t, f"{x[0]:.1f}", f"{x[1]:.1f}", f"{x[2]:.1f}", f"{x[3]:.2f}", f"{x[4]:.4f}",
                    f"{x[5]:.1f}", f"{x[6]:.2f}", f"{x[7]:.2f}", 0, 0, ""])
# anomaly dataset (seed 0 of run_anomaly.py)
import importlib.util
spec = importlib.util.spec_from_file_location("ra", os.path.join(os.path.dirname(__file__), "run_anomaly.py"))
src = open(spec.origin).read().split("res = {")[0]
ns = {"__file__": spec.origin}; exec(src, ns)
Xa, ya = ns["dataset"](0)
names = ["normal", "cpu_exhaustion", "memory_queue_exhaustion", "downstream_failure", "request_flood", "network_disk_delay"]
with open(os.path.join(D, "anomaly_data.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["rps", "cpu_pct", "mem_pct", "latency_ms", "error_rate", "queue_depth", "net_MBps", "disk_ms", "label", "category"])
    for x, y in zip(Xa, ya):
        w.writerow([f"{v:.4f}" for v in x] + [int(y > 0), names[y]])
# failure schedule of the 30 test runs (same windows as run_cluster.py)
sys.argv = [sys.argv[0]]
import run_cluster as rc
with open(os.path.join(D, "failure_schedule.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["run_id", "failure_time_s", "service", "failure_class", "kind", "anomaly_t0_s", "anomaly_service", "anomaly_factor", "anomaly_duration_s"])
    for s in range(1, 31):
        _, _, fl, an = rc.window(s)
        w.writerow([s, f"{fl['t']:.1f}", SERVICES[fl["module"]], "C1", fl["kind"], an["t0"], SERVICES[an["module"]], an["factor"], an["dur"]])
cfg = {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in asdict(Params()).items()}
cfg["services"] = SERVICES
cfg["traffic"] = dict(days=365, seed=2026, base=600, daily_amp=350, weekly_amp=120, noise_sd=60,
                      flash_sales=48, flash_amp=[4000, 8000], flash_dur_min=[20, 90], min_separation_h=48)
cfg["lstm"] = dict(layers=2, hidden=128, dropout=0.2, optimiser="Adam", lr=1e-3, loss="MSE (log-rate, standardised)",
                   batch=64, windows_per_epoch=8192, max_epochs=100, patience=10, lookback_min=60, horizons_min=[5, 15, 60])
cfg["isolation_forest"] = dict(trees=100, max_samples=256, contamination=0.05)
cfg["random_seeds"] = dict(test_runs=list(range(1, 31)), tuning_runs=list(range(101, 111)))
json.dump(cfg, open(os.path.join(D, "simulation_config.json"), "w"), indent=1)
print("written to", D)
