"""Regenerate all data-driven figures of the manuscript from results/*.json."""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); RS = os.path.join(HERE, "results")
FIG = os.environ.get("ATLAS_FIG_DIR", os.path.join(HERE, "figures")); os.makedirs(FIG, exist_ok=True)
sys.path.insert(0, HERE)
plt.rcParams.update({"font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "legend.frameon": False,
                     "pdf.fonttype": 42, "font.family": "DejaVu Sans"})
POL = ["monolith", "microservices", "hansel", "phybrid", "xscale", "atlas"]
NAME = {"monolith": "Static Monolith", "microservices": "Static Microservices", "hansel": "HANSEL-like",
        "phybrid": "Predictive-Hybrid", "xscale": "XScale-like", "atlas": "ATLAS"}
COL = {"monolith": "#7f7f7f", "microservices": "#4C78A8", "hansel": "#9ecae9", "phybrid": "#72B7B2",
       "xscale": "#B279A2", "atlas": "#E45756"}
MODECOL = ["#4C78A8", "#F58518", "#E45756"]
J = lambda n: json.load(open(os.path.join(RS, n)))
save = lambda f, n: (f.savefig(os.path.join(FIG, n), bbox_inches="tight"), plt.close(f))


def fig_trace():
    C = J("cluster.json"); tr = C["main_traces"]["atlas"]
    import run_cluster as rc
    lam_s, fc, fail, an = rc.window(1)
    t = np.arange(len(tr["lam"])) * 10 / 60.0
    f, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 3.6), sharex=True, gridspec_kw=dict(height_ratios=[3, 1]))
    a1.plot(t, tr["lam"], lw=0.6, color="#4C78A8", label="Measured request rate (1-s arrivals)")
    a1.plot(np.arange(len(tr["fc"])) + 5, tr["fc"], lw=1.3, color="#E45756", ls="--", label="LSTM forecast (5 min ahead, out-of-sample)")
    a1.axvline(fail["t"] / 60, color="k", lw=0.8, ls=":"); a1.text(fail["t"] / 60 + 1, max(tr["lam"]) * 0.92, "Payment crash", fontsize=7)
    a1.axvspan(an["t0"] / 60, (an["t0"] + an["dur"]) / 60, color="#F58518", alpha=0.15, lw=0)
    a1.text(an["t0"] / 60 + 0.5, max(tr["lam"]) * 0.75, "Inventory\nanomaly", fontsize=7)
    a1.set_ylabel("Requests/s"); a1.legend(loc="upper left", fontsize=7)
    m = np.array(tr["mode"])
    for k, nm in enumerate(["Tight", "Hybrid", "Loose"]):
        a2.fill_between(t, 0, 1, where=m == k, color=MODECOL[k], step="post", lw=0, label=nm)
    a2.set_yticks([]); a2.set_xlabel("Time (min)"); a2.set_ylabel("Mode"); a2.legend(ncol=3, loc="upper right", fontsize=7)
    a2.grid(False)
    save(f, "fig_lstm_simulation.pdf")


def fig_anomaly():
    Z = np.load(os.path.join(RS, "anomaly_scatter.npz")); X, y, a, thr = Z["X"], Z["y"], Z["a"], float(Z["thr"])
    f, ax = plt.subplots(figsize=(5.2, 3.4))
    pred = a >= thr
    ax.scatter(X[~pred, 1], X[~pred, 3], s=4, color="#4C78A8", alpha=0.35, label="Classified normal")
    ax.scatter(X[pred, 1], X[pred, 3], s=14, marker="x", color="#E45756", lw=0.8, label="Classified anomalous")
    ax.set_yscale("log"); ax.set_xlabel("CPU utilisation (%)"); ax.set_ylabel("Response latency (ms, log)")
    ax.legend(loc="upper left")
    save(f, "fig_anomaly_detection.pdf")


def fig_main():
    C = J("cluster.json")["main"]
    mets = [("p99_ms", "p99 latency (ms)"), ("sla_viol_pct", "SLA violations (%)"), ("failed_pct", "Failed requests (%)"), ("rel_cost", "Relative cost (×)")]
    f, axs = plt.subplots(1, 4, figsize=(7.4, 2.4))
    for ax, (k, lab) in zip(axs, mets):
        m = [C[p][k]["mean"] for p in POL]; lo = [C[p][k]["mean"] - C[p][k]["ci95"][0] for p in POL]
        ax.bar(range(6), m, yerr=lo, color=[COL[p] for p in POL], capsize=2, error_kw=dict(lw=0.7))
        ax.set_xticks(range(6)); ax.set_xticklabels(["Mono", "Micro", "HANSEL", "P-Hyb", "XScale", "ATLAS"], rotation=60, fontsize=7)
        ax.set_title(lab, fontsize=8); ax.grid(axis="x", visible=False)
        if k in ("p99_ms", "sla_viol_pct", "failed_pct"):
            ax.set_yscale("log")
            for i, v in enumerate(m):
                if v <= 0:
                    ax.text(i, ax.get_ylim()[0] * 1.5, "0", ha="center", fontsize=7, color=COL[POL[i]])
    f.tight_layout(); save(f, "fig_latency_comparison.pdf")


def fig_load():
    L = J("cluster.json")["load_sweep"]; xs = sorted(L, key=float); x = [float(v) for v in xs]
    for key, fn, lab in [("p99_ms", "atlas_latency_comparison.pdf", "p99 latency of completed requests (ms)")]:
        f, ax = plt.subplots(figsize=(5.6, 3.0))
        for p in POL:
            m = [L[s][p][key]["mean"] for s in xs]; e = [L[s][p][key]["mean"] - L[s][p][key]["ci95"][0] for s in xs]
            ax.errorbar(x, m, yerr=e, marker="o", ms=3, lw=1.6 if p == "atlas" else 1, color=COL[p], label=NAME[p], capsize=2)
        ax.axhline(200, color="k", ls="--", lw=0.7); ax.set_yscale("log")
        ax.set_xlabel("Offered load (× test traffic; peak ≈ 4.5–8.5 kRPS at 1×)"); ax.set_ylabel(lab); ax.legend(fontsize=6.5, ncol=2)
        save(f, fn)
    f, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.8))
    for p in POL:
        a1.plot(x, [L[s][p]["sla_viol_pct"]["mean"] for s in xs], marker="o", ms=3, color=COL[p], lw=1.6 if p == "atlas" else 1, label=NAME[p])
        a2.plot(x, [L[s][p]["rel_cost"]["mean"] for s in xs], marker="o", ms=3, color=COL[p], lw=1.6 if p == "atlas" else 1)
    a1.set_yscale("log"); a1.set_ylabel("SLA violations (%)"); a2.set_ylabel("Relative cost (×)")
    for a in (a1, a2):
        a.set_xlabel("Offered load (× test traffic)")
    a1.legend(fontsize=6.5); f.tight_layout(); save(f, "atlas_sla_comparison.pdf")


def fig_sens():
    S = J("cluster.json")["sensitivity"]; sw = list(S)
    f, axs = plt.subplots(4, 4, figsize=(7.4, 5.6))
    for j, name in enumerate(sw):
        r0 = (j // 4) * 2; c = j % 4
        keys = list(S[name]); xl = [k for k in keys]
        for p in ("microservices", "hansel", "atlas"):
            if p not in S[name][keys[0]]:
                continue
            for rr, met in ((0, "sla_viol_pct"), (1, "rel_cost")):
                ax = axs[r0 + rr, c]
                m = [S[name][k][p][met]["mean"] for k in keys]; e = [S[name][k][p][met]["mean"] - S[name][k][p][met]["ci95"][0] for k in keys]
                ax.errorbar(range(len(keys)), m, yerr=e, marker="o", ms=3, color=COL[p], lw=1.4 if p == "atlas" else 0.9, capsize=2, label=NAME[p])
        for rr, met in ((0, "SLA viol. (%)"), (1, "Rel. cost (×)")):
            ax = axs[r0 + rr, c]; ax.set_xticks(range(len(keys)))
            LBL = {"weights (alpha,beta,gamma)": {"(1, 1, 1)": "1,1,.01", "(2, 1, 1)": "2,1,.01", "(1, 2, 1)": "1,2,.01", "(1, 1, 5)": "1,1,.05"},
                   "forecast MAPE (%)": {"0.0": "LSTM", "0.1": "10", "0.2": "20", "0.4": "40"}}
            lab = [LBL.get(name, {}).get(k, k.replace("(", "").replace(")", "").replace(", ", "–").replace(".0", "")) for k in xl]
            ax.set_xticklabels(lab, fontsize=6, rotation=30)
            if c == 0: ax.set_ylabel(met, fontsize=7)
            if rr == 0: ax.set_title(name.replace("(alpha,beta,gamma)", "(α,β,γ)").replace("forecast MAPE (%)", "forecast error (MAPE %)"), fontsize=7.5)
    axs[0, 0].legend(fontsize=6)
    f.tight_layout(); save(f, "fig_sensitivity.pdf")


def fig_vehicle():
    V = J("vehicle.json"); Z = np.load(os.path.join(RS, "vehicle_preds.npz"))
    tr = V["atlas"]["trace"]; h = np.arange(1440) / 60
    f, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 3.4), sharex=True, gridspec_kw=dict(height_ratios=[3, 1]))
    a1.plot(h, np.array(tr["lam"]) / 1000, color="#4C78A8", lw=0.8, label="Event rate")
    a1.plot(h + 8 / 60, np.array(tr["fc"]) / 1000, color="#E45756", ls="--", lw=1.1, label="LSTM forecast (8 min ahead, out-of-sample)")
    a1.set_ylabel("kEvents/s"); a1.legend(fontsize=7)
    m = np.array(tr["mode"])
    for k, nm in enumerate(["Tight", "Hybrid", "Loose"]):
        a2.fill_between(h, 0, 1, where=m == k, color=MODECOL[k], step="post", lw=0, label=nm)
    a2.set_yticks([]); a2.set_xlabel("Hour of day"); a2.legend(ncol=3, fontsize=7, loc="upper right"); a2.grid(False)
    save(f, "fig_vehicle_traffic_prediction.pdf")
    f, ax = plt.subplots(figsize=(7.2, 2.8))
    for p in ("monolith", "microservices", "atlas"):
        ax.plot(h, V[p]["trace"]["lat"], color=COL[p], lw=1.3 if p == "atlas" else 0.9, label=NAME[p])
    ax.axhline(100, color="k", ls="--", lw=0.7); ax.set_yscale("log"); ax.set_ylabel("Mean latency (ms)"); ax.set_xlabel("Hour of day")
    ax.legend(fontsize=7); save(f, "fig_vehicle_latency_comparison.pdf")
    f, ax = plt.subplots(figsize=(7.2, 2.6))
    for p in ("monolith", "microservices", "atlas"):
        ref = V[p]["trace"]["ref_cost"]
        ax.plot(h, np.array(V[p]["trace"]["cost"]) / ref, color=COL[p], lw=1.3 if p == "atlas" else 0.9, label=NAME[p])
    ax.set_ylabel("Allocated cores / monolith"); ax.set_xlabel("Hour of day"); ax.legend(fontsize=7)
    save(f, "fig_vehicle_cost_comparison.pdf")


if __name__ == "__main__":
    which = sys.argv[1:] or ["trace", "anomaly", "main", "load", "sens", "vehicle"]
    for w in which:
        globals()["fig_" + w](); print("figure", w)
