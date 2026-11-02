"""Experiments added in the second revision (Reviewer 2, round 2).

  formulation : exact (nonlinear) enumeration vs. linearised BIP vs. LP relaxation
                with risk-aware rounding, compared in the NONLINEAR objective
                (a) on the decision states recorded in the 30 ATLAS test runs (n = 6)
                (b) on synthetic chain-structured service models with n = 8, 12, 16
  blast       : blast radius / availability assumptions (Eqs. (6) and (11)):
                exactness of max_j v_j for the chain topology, union bound vs.
                independent failures, and ATLAS re-run with the conservative
                whole-process blast radius
  anomaly     : value of the anomaly detector in two scenarios in which the
                anomaly matters (anomaly at peak load; anomaly that precedes a
                crash of the same module), full ATLAS vs. ATLAS without detector
  combined    : 2^4 factorial stress test (pod start-up x service demand x
                failures per run x network latency), ATLAS vs. static
                microservices and the HANSEL-like autoscaler

Output: results/round2.json
"""
import json, os, sys, time
from dataclasses import replace
from multiprocessing import Pool
import numpy as np
from scipy.optimize import linprog
sys.path.insert(0, os.path.dirname(__file__))
import run_cluster as rc
from atlas_sim.cluster import Sim, Params, summarise

OUT = rc.OUT
PATH = os.path.join(OUT, "round2.json")
T = json.load(open(os.path.join(OUT, "cluster.json")))["tuned"]
TEST = list(range(1, 31))


# --------------------------------------------------------------- generic model
def model(CM, lam, v, w, pc, P, ref):
    """Nonlinear model of Eqs. (3)-(6) and (11) for all configurations CM [K,n]."""
    tight = CM == 0; anyt = tight.any(1)
    Dm = (tight * (v * w)).sum(1)
    rho = np.where(anyt, lam * Dm / 1000.0 / P["Km"], 0.0)
    Lm = np.where(anyt, Dm / (1 - np.minimum(rho, 0.97)), 0.0)
    L = P["base"] + Lm + ((~tight) * (v * (w / (1 - P["tgt"]) + P["net"]))).sum(1)
    L = np.where(rho >= 0.98, 1e4, L)
    need = np.maximum(P["rmin"], np.ceil(lam * v * w / 1000.0 / (P["tgt"] * P["pod"])))
    reps = CM * need[None, :]
    C = np.where(anyt, P["Km"], 0.0) + (reps * (P["pod"] + P["sc"])).sum(1) + CM.sum(1) * P["fix"] \
        + lam * ((~tight) * v).sum(1) * P["netc"]
    phi = np.where(anyt, (tight * v).max(1), 0.0)
    d = np.where(tight, phi[:, None], v[None, :])
    rh = np.where(tight, rho[:, None], P["tgt"])
    p = pc[None, :] + P["prho"] / (1 + np.exp(-(rh - 0.9) * 20))
    risk = (p * d).sum(1)
    L0, C0, R0 = ref
    return dict(L=L, C=C, R=risk * lam, A=1 - risk, rho=rho, reps=reps, p=p, d=d,
                J0=P["alpha"] * L / L0 + P["beta"] * C / C0 + P["gamma"] * risk * lam / R0)


def feasible(M, P):
    return (M["rho"] <= P["rhomax"]) & (M["L"] <= P["Lmax"]) & (M["reps"] <= P["Rmax"]).all(1) & (M["A"] >= P["Amin"])


def configs(n):
    K = 2 ** n
    return ((np.arange(K)[:, None] >> np.arange(n)[None, :]) & 1).astype(int)


def repair(c, lam, v, w, pc, P, ref, cprev):
    """Phase 3 (Steps 19-23): verification against the nonlinear model + greedy flips."""
    c = c.copy()
    for _ in range(3 * len(c)):
        M = model(c[None, :], lam, v, w, pc, P, ref)
        if feasible(M, P)[0]:
            return c, True
        tightm = np.where(c == 0)[0]; loose = np.where(c == 1)[0]
        if (M["rho"][0] > P["rhomax"] or M["L"][0] > P["Lmax"]) and len(tightm):
            c[tightm[np.argmax((v * w)[tightm])]] = 1
        elif (M["reps"][0] > P["Rmax"]).any() and len(loose):
            c[loose[np.argmax(M["reps"][0][loose])]] = 0
        elif M["A"][0] < P["Amin"] and len(tightm):
            c[tightm[np.argmax((M["p"][0] * M["d"][0])[tightm])]] = 1
        else:
            break
    return np.ones_like(c), False


def solve_all(lam, v, w, pc, P, ref, cprev, CM=None):
    """Returns the configurations chosen by (E) exact nonlinear enumeration,
    (LB) exact solution of the linearised BIP and (LP) LP relaxation + risk-aware
    rounding, the latter two followed by Phase-3 verification/repair."""
    n = len(v)
    sw = lambda X: P["kappa"] * np.abs(X - cprev[None, :]).sum(1)
    # ---- (E) exact nonlinear
    if CM is not None:
        M = model(CM, lam, v, w, pc, P, ref); J = M["J0"] + sw(CM); ok = feasible(M, P)
        cE = CM[int(np.argmin(np.where(ok, J, np.inf)))] if ok.any() else np.ones(n, int)
    else:
        cE = None
    # ---- linearisation around c_prev (one-flip finite differences)
    up = np.repeat(cprev[None, :], n, 0); up[np.arange(n), np.arange(n)] = 1
    dn = np.repeat(cprev[None, :], n, 0); dn[np.arange(n), np.arange(n)] = 0
    Mu = model(up, lam, v, w, pc, P, ref); Md = model(dn, lam, v, w, pc, P, ref)
    M0 = model(cprev[None, :], lam, v, w, pc, P, ref)
    Lc = lambda key, M: np.where(M["rho"] >= 0.98, P["base"] + (M["C"] * 0) + 1e3, M[key]) if key == "L" else M[key]
    dJ = Mu["J0"] - Md["J0"]
    f = dJ + P["kappa"] * (1 - 2 * cprev)                    # linear objective coefficients
    dL = Lc("L", Mu) - Lc("L", Md); dA = Mu["A"] - Md["A"]
    rho_coef = -lam * v * w / 1000.0 / P["Km"]               # rho_m is exactly linear in c
    rho_0 = lam * (v * w).sum() / 1000.0 / P["Km"]
    L_0 = float(Lc("L", M0)[0]) - dL @ cprev; A_0 = float(M0["A"][0]) - dA @ cprev
    A_ub = np.vstack([rho_coef, dL, -dA]); b_ub = np.array([P["rhomax"] - rho_0, P["Lmax"] - L_0, A_0 - P["Amin"]])
    need = np.maximum(P["rmin"], np.ceil(lam * v * w / 1000.0 / (P["tgt"] * P["pod"])))
    ub = np.where(need > P["Rmax"], 0, 1)
    # ---- (LB) exact optimum of the linearised BIP (enumeration for n <= 16)
    if CM is not None:
        okl = np.all(CM @ A_ub.T <= b_ub + 1e-9, 1) & np.all(CM <= ub, 1)
        cLB = CM[int(np.argmin(np.where(okl, CM @ f, np.inf)))] if okl.any() else np.ones(n, int)
        cLB, okLB = repair(cLB, lam, v, w, pc, P, ref, cprev)
    else:
        cLB, okLB = None, None
    # ---- (LP) relaxation + risk-aware rounding (delta = 0.3) + repair
    res = linprog(f, A_ub=A_ub, b_ub=b_ub, bounds=list(zip(np.zeros(n), ub)), method="highs")
    x = res.x if res.status == 0 else np.full(n, 0.5)
    risk = (M0["p"][0] * M0["d"][0]); tau = 0.5 - 0.3 * risk / max(risk.max(), 1e-12)
    cLP = (x >= tau - 1e-9).astype(int)
    pre_ok = bool(feasible(model(cLP[None, :], lam, v, w, pc, P, ref), P)[0])
    cLP, okLP = repair(cLP, lam, v, w, pc, P, ref, cprev)
    return cE, cLB, okLB, cLP, okLP, pre_ok


def Jnl(c, lam, v, w, pc, P, ref, cprev):
    M = model(c[None, :], lam, v, w, pc, P, ref)
    return float(M["J0"][0] + P["kappa"] * np.abs(c - cprev).sum())


def sim_params():
    p = replace(Params(), **T["atlas"])
    P = dict(Km=p.mono_cores, base=p.base_ms, tgt=p.hpa_target, net=p.net_ms, rmin=p.min_rep, pod=p.pod_cores,
             sc=p.sidecar_cores, fix=p.svc_fixed_cores, netc=p.net_cost_core_s, prho=p.p_rho,
             alpha=p.alpha, beta=p.beta, gamma=p.gamma * p.gamma_scale, kappa=p.switch_pen,
             rhomax=p.rho_max, Lmax=p.sla_ms, Rmax=p.max_rep, Amin=p.a_min)
    return p, P


class RecSim(Sim):
    def bip(self, t, lam_star, a_score):
        p = self.p
        pc = np.full(self.n, p.p0)
        if self.anom_module >= 0:
            pc[self.anom_module] += p.p_a / (1 + np.exp(-(a_score - 0.7) * 20))
        self.states.append((float(lam_star), self.demand_est.copy(), pc, self.c.copy()))
        return super().bip(t, lam_star, a_score)


def record_states(seed):
    lam, fc, failure, anomaly = rc.window(seed, "test")
    p = replace(Params(), **T["atlas"])
    s = RecSim("atlas", lam, fc["lstm"], p=p, seed=seed, failure=failure, anomaly=anomaly, iforest=rc.ISO)
    s.states = []; s.run()
    return s.states


def summ_gap(g):
    g = np.asarray(g)
    return dict(median=float(np.median(g)), p95=float(np.percentile(g, 95)), max=float(g.max()),
                share_zero=float(np.mean(g <= 1e-9)))


def exp_formulation(R):
    p, P = sim_params()
    v, CM6 = p.visit, configs(6)
    L0 = None
    with Pool(2) as pool:
        ST = pool.map(record_states, TEST)
    # normalisation as in the simulator (all-tight at the nominal load)
    ref_M = model(np.zeros((1, 6), int), p.ref_lam, v, p.demand, np.full(6, 1e-3), P, (1, 1, 1))
    ref = (float(ref_M["L"][0]), float(ref_M["C"][0]), p.ref_lam * 1e-3)
    out = dict(E_LB=[], E_LP=[], same_LB=[], same_LP=[], preok_LP=[], ok_LB=[], ok_LP=[], hybrid=[], t_states=0)
    for run in ST:
        for k, (lam, w, pc, cprev) in enumerate(run):
            if k % 2:
                continue
            cE, cLB, okLB, cLP, okLP, pre = solve_all(lam, v, w, pc, P, ref, cprev, CM6)
            jE = Jnl(cE, lam, v, w, pc, P, ref, cprev)
            out["E_LB"].append(100 * (Jnl(cLB, lam, v, w, pc, P, ref, cprev) - jE) / abs(jE))
            out["E_LP"].append(100 * (Jnl(cLP, lam, v, w, pc, P, ref, cprev) - jE) / abs(jE))
            out["same_LB"].append(bool((cLB == cE).all())); out["same_LP"].append(bool((cLP == cE).all()))
            out["preok_LP"].append(pre); out["ok_LB"].append(okLB); out["ok_LP"].append(okLP)
            out["hybrid"].append(0 < cE.sum() < 6)
    hy = np.array(out["hybrid"])
    F = dict(n=6, states=len(out["E_LB"]), hybrid_share=float(hy.mean()),
             LB=dict(gap=summ_gap(out["E_LB"]), agree=float(np.mean(out["same_LB"])), feasible=float(np.mean(out["ok_LB"]))),
             LP=dict(gap=summ_gap(out["E_LP"]), agree=float(np.mean(out["same_LP"])), feasible=float(np.mean(out["ok_LP"])),
                     feasible_before_repair=float(np.mean(out["preok_LP"]))),
             LP_nontrivial=dict(gap=summ_gap(np.array(out["E_LP"])[~np.array(out["same_LP"]) | hy]),
                                agree_when_E_hybrid=float(np.mean(np.array(out["same_LP"])[hy])) if hy.any() else None))
    R["formulation_sim"] = F; print("sim", json.dumps(F)[:600], flush=True)
    # ---- (b) synthetic chain models, n = 8, 12, 16
    SY = {}
    for n in (8, 12, 16):
        g = np.random.default_rng(1000 + n); CM = configs(n)
        G = dict(E_LB=[], E_LP=[], same_LB=[], same_LP=[], ok_LP=[], preok=[], hyb=[])
        t_e, t_lp = [], []
        for inst in range(20):
            v = np.sort(np.r_[1.0, g.uniform(0.05, 1.0, n - 1)])[::-1]; v[1] = max(v[1], 0.8)
            w = g.uniform(0.3, 4.0, n)
            Pn = dict(P); Pn["Km"] = float(np.ceil((v * w).sum() * 3.0))     # monolith saturates at ~3000 RPS
            refm = model(np.zeros((1, n), int), 650.0, v, w, np.full(n, 1e-3), Pn, (1, 1, 1))
            refn = (float(refm["L"][0]), float(refm["C"][0]), 0.65)
            cprev = np.zeros(n, int)
            for s in range(15):
                lam = float(g.uniform(300, 4500))
                pc = np.full(n, 1e-4)
                if g.random() < 0.3:
                    pc[g.integers(n)] += 0.02 / (1 + np.exp(-(g.uniform(0.5, 1.0) - 0.7) * 20))
                t0 = time.perf_counter()
                cE, cLB, okLB, cLP, okLP, pre = solve_all(lam, v, w, pc, Pn, refn, cprev, CM)
                jE = Jnl(cE, lam, v, w, pc, Pn, refn, cprev)
                G["E_LB"].append(100 * (Jnl(cLB, lam, v, w, pc, Pn, refn, cprev) - jE) / abs(jE))
                G["E_LP"].append(100 * (Jnl(cLP, lam, v, w, pc, Pn, refn, cprev) - jE) / abs(jE))
                G["same_LB"].append(bool((cLB == cE).all())); G["same_LP"].append(bool((cLP == cE).all()))
                G["ok_LP"].append(okLP); G["preok"].append(pre); G["hyb"].append(0 < cE.sum() < n)
                cprev = cE
        SY[str(n)] = dict(states=len(G["E_LB"]), hybrid_share=float(np.mean(G["hyb"])),
                          LB=dict(gap=summ_gap(G["E_LB"]), agree=float(np.mean(G["same_LB"]))),
                          LP=dict(gap=summ_gap(G["E_LP"]), agree=float(np.mean(G["same_LP"])),
                                  feasible=float(np.mean(G["ok_LP"])), feasible_before_repair=float(np.mean(G["preok"]))))
        print("synthetic", n, json.dumps(SY[str(n)]), flush=True)
    R["formulation_synth"] = SY


# --------------------------------------------------------------- blast radius
def exp_blast(R):
    p, P = sim_params(); v = p.visit; n = 6; CM = configs(n)
    # (i) chain topology: depth classes q_k (request of depth k visits modules 1..k)
    vv = np.r_[v, 0.0]; q = vv[:-1] - vv[1:]
    exact_phi, maxv = [], []
    for c in CM:
        tight = np.where(c == 0)[0]
        if len(tight) == 0:
            continue
        exact_phi.append(float(q[[k for k in range(n) if (tight <= k).any()]].sum()))
        maxv.append(float(v[tight].max()))
    # (ii) union bound vs. independent failures on the recorded decision states
    with Pool(2) as pool:
        ST = pool.map(record_states, TEST[:10])
    ref_M = model(np.zeros((1, 6), int), p.ref_lam, v, p.demand, np.full(6, 1e-3), P, (1, 1, 1))
    ref = (float(ref_M["L"][0]), float(ref_M["C"][0]), p.ref_lam * 1e-3)
    rel, absd, anyflip = [], [], 0; cnt = 0
    for run in ST:
        for lam, w, pc, cprev in run[::4]:
            M = model(CM, lam, v, w, pc, P, ref)
            for kk in range(0, len(CM), 7):
                c = CM[kk]; pi = M["p"][kk]; tight = c == 0
                # request of depth k is affected by module i if i is decomposed and i <= k,
                # or if i is in-process and the request traverses the monolith
                aff = np.zeros((n, n))
                for k in range(n):
                    trav = (np.where(tight)[0] <= k).any()
                    for i in range(n):
                        aff[i, k] = (i <= k) if c[i] == 1 else trav
                Pk = 1 - np.prod(1 - pi[:, None] * aff, 0)
                exact = float((q * Pk).sum()); union = float((pi * M["d"][kk]).sum())
                absd.append(union - exact); rel.append((union - exact) / max(exact, 1e-12)); cnt += 1
    B = dict(chain_max_equals_exact=bool(np.allclose(exact_phi, maxv)),
             union_minus_independent=dict(max_abs=float(np.max(absd)), median_rel=float(np.median(rel)),
                                          max_rel=float(np.max(rel)), cases=cnt))
    # (iii) ATLAS with the conservative whole-process blast radius
    S = rc.pmap([("atlas", s, T["atlas"], dict(blast="process"), None, "test", 0) for s in TEST])
    B["process_blast"] = rc.summarise_runs(S)
    B["process_blast"]["mode_share"] = np.mean([s["mode_share"] for s in S], 0).tolist()
    S0 = rc.pmap([("atlas", s, T["atlas"], None, None, "test", 0) for s in TEST])
    B["max_blast"] = rc.summarise_runs(S0)
    B["max_blast"]["mode_share"] = np.mean([s["mode_share"] for s in S0], 0).tolist()
    B["test_p99"] = rc.compare(S, S0, "p99_ms"); B["test_sla"] = rc.compare(S, S0, "sla_viol_pct")
    B["test_cost"] = rc.compare(S, S0, "rel_cost")
    R["blast"] = B; print("blast", json.dumps(B)[:900], flush=True)


# --------------------------------------------------------------- anomaly detector
class AnomSim(Sim):
    def score(self, t, lam, d):
        inside = self.anomaly and self.anomaly["t0"] <= t < self.anomaly["t0"] + self.anomaly["dur"]
        if self.o.get("oracle"):
            # oracle detector: alert-level score attributed to the right module during the
            # anomaly; isolates the value of the isolation mechanism from detector quality
            a = super().score(t, lam, d)
            if inside:
                self.anom_module = self.anomaly["module"]; a = max(a, 0.8)
                self.first_alert = min(getattr(self, "first_alert", 1e9), t)
            return a
        a = super().score(t, lam, d)
        if self.anomaly and self.anomaly["t0"] <= t < self.anomaly["t0"] + self.anomaly["dur"] and a >= self.p.anomaly_alert:
            self.first_alert = min(getattr(self, "first_alert", 1e9), t)
        return a


def run_scen(args):
    scen, seed, opts = args
    lam, fc, failure, anomaly = rc.window(seed, "test")
    rng = np.random.default_rng(seed + 77)
    if scen == "main":
        pass
    elif scen == "peak":       # SLA-threatening anomaly: Inventory x6 starting shortly before the surge peak
        peak = failure["t"]
        anomaly = dict(t0=int(peak - rng.uniform(240, 360)), dur=480, module=3, factor=6.0)
    elif scen == "precursor":  # anomaly that precedes a crash of the same module (off-peak)
        t0 = int(rng.uniform(15, 25) * 60)
        anomaly = dict(t0=t0, dur=600, module=4, factor=6.0)
        failure = dict(t=float(t0 + rng.uniform(240, 360)), module=4, kind="exit")
    p = replace(Params(), **T["atlas"])
    s = AnomSim("atlas", lam, fc["lstm"], p=p, seed=seed, opts=opts, failure=failure, anomaly=anomaly, iforest=rc.ISO)
    out = s.run()
    ref = Sim("monolith", lam, fc["lstm"], p=p, seed=seed).run()
    S = summarise(out, ref_cost=float(np.mean(ref["cost"][300:])))
    fa = getattr(s, "first_alert", None)
    S["alert_lead_s"] = (failure["t"] - fa) if (fa is not None and failure is not None and fa < failure["t"]) else None
    S["alert"] = fa is not None
    S["recoveries"] = None
    return S


def exp_anomaly(R):
    AN = {}
    for scen in ("main", "peak", "precursor"):
        AN[scen] = {}
        runs = {}
        for name, opts in [("ATLAS (full)", None), ("- anomaly detector", dict(anomaly=False)),
                           ("oracle detector", dict(oracle=True))]:
            with Pool(2) as pool:
                S = pool.map(run_scen, [(scen, s, opts) for s in TEST])
            runs[name] = S
            AN[scen][name] = rc.summarise_runs(S)
            AN[scen][name]["alert_rate"] = float(np.mean([x["alert"] for x in S]))
            lead = [x["alert_lead_s"] for x in S if x["alert_lead_s"] is not None]
            AN[scen][name]["alert_lead_s"] = float(np.median(lead)) if lead else None
            print(scen, name, {k: round(v["mean"], 3) for k, v in AN[scen][name].items() if isinstance(v, dict)},
                  AN[scen][name]["alert_rate"], flush=True)
        AN[scen]["tests"] = {k: rc.compare(runs["ATLAS (full)"], runs["- anomaly detector"], k)
                             for k in ("p99_ms", "sla_viol_pct", "failed_pct", "rel_cost", "mttr_s")}
    R["anomaly"] = AN


# --------------------------------------------------------------- combined factors
def exp_combined(R):
    CO = {}; seeds = list(range(1, 11))
    for su in [(8.0, 30.0), (30.0, 60.0)]:
        for dm in (1.0, 1.3):
            for nf in (1, 3):
                for net in (4.0, 10.0):
                    key = f"startup={int(su[0])}-{int(su[1])}|demand={dm}|failures={nf}|net={int(net)}"
                    res = {}
                    for pol in ("atlas", "microservices", "hansel"):
                        pd = dict(T[pol]); pd.update(startup_s=su, demand=Params().demand * dm, net_ms=net)
                        pd["_nfail"] = nf
                        S = rc.pmap([(pol, s, pd, None, None, "test", 0) for s in seeds])
                        res[pol] = {k: rc.stat_block([s[k] for s in S]) for k in ["p99_ms", "sla_viol_pct", "failed_pct", "rel_cost"]}
                    CO[key] = res
                    print(key, {p_: (round(x["sla_viol_pct"]["mean"], 2), round(x["rel_cost"]["mean"], 2))
                                for p_, x in res.items()}, flush=True)
    R["combined"] = CO


# --------------------------------------------------------------- refined linearised method
def local_search(c, lam, v, w, pc, P, ref, cprev):
    """1-flip descent on the nonlinear objective over feasible configurations."""
    c = c.copy(); n = len(c)
    M = model(c[None, :], lam, v, w, pc, P, ref)
    best = Jnl(c, lam, v, w, pc, P, ref, cprev) if feasible(M, P)[0] else np.inf
    for _ in range(n):
        N = np.repeat(c[None, :], n, 0); N[np.arange(n), np.arange(n)] ^= 1
        MN = model(N, lam, v, w, pc, P, ref)
        J = MN["J0"] + P["kappa"] * np.abs(N - cprev[None, :]).sum(1)
        J = np.where(feasible(MN, P), J, np.inf); k = int(np.argmin(J))
        if J[k] < best - 1e-12:
            best = J[k]; c = N[k]
        else:
            break
    return c


def solve_refined(lam, v, w, pc, P, ref, cprev, iters=5):
    """Sequential linearisation (re-linearise around the candidate until it no
    longer changes) followed by 1-flip local search on the nonlinear model."""
    base = cprev.copy(); c = None
    for _ in range(iters):
        _, _, _, cand, ok, _ = _lp_only(lam, v, w, pc, P, ref, base, cprev)
        if c is not None and (cand == c).all():
            break
        c = cand; base = cand
    return local_search(c, lam, v, w, pc, P, ref, cprev)


def _lp_only(lam, v, w, pc, P, ref, base, cprev):
    """LP relaxation + rounding + repair of the problem linearised around `base`
    (switching cost still measured from the deployed configuration cprev)."""
    n = len(v)
    up = np.repeat(base[None, :], n, 0); up[np.arange(n), np.arange(n)] = 1
    dn = np.repeat(base[None, :], n, 0); dn[np.arange(n), np.arange(n)] = 0
    Mu = model(up, lam, v, w, pc, P, ref); Md = model(dn, lam, v, w, pc, P, ref)
    M0 = model(base[None, :], lam, v, w, pc, P, ref)
    capL = lambda M: np.where(M["rho"] >= 0.98, P["base"] + 1e3, M["L"])
    f = (Mu["J0"] - Md["J0"]) + P["kappa"] * (1 - 2 * cprev)
    dL = capL(Mu) - capL(Md); dA = Mu["A"] - Md["A"]
    rho_coef = -lam * v * w / 1000.0 / P["Km"]; rho_0 = lam * (v * w).sum() / 1000.0 / P["Km"]
    L_0 = float(capL(M0)[0]) - dL @ base; A_0 = float(M0["A"][0]) - dA @ base
    A_ub = np.vstack([rho_coef, dL, -dA]); b_ub = np.array([P["rhomax"] - rho_0, P["Lmax"] - L_0, A_0 - P["Amin"]])
    need = np.maximum(P["rmin"], np.ceil(lam * v * w / 1000.0 / (P["tgt"] * P["pod"])))
    ub = np.where(need > P["Rmax"], 0, 1)
    res = linprog(f, A_ub=A_ub, b_ub=b_ub, bounds=list(zip(np.zeros(n), ub)), method="highs")
    x = res.x if res.status == 0 else np.full(n, 0.5)
    risk = (M0["p"][0] * M0["d"][0]); tau = 0.5 - 0.3 * risk / max(risk.max(), 1e-12)
    c, ok = repair((x >= tau - 1e-9).astype(int), lam, v, w, pc, P, ref, cprev)
    return None, None, None, c, ok, None


def exp_formulation2(R):
    """Synthetic chain models n = 8, 12, 16 with (a) gradual load changes between
    five-second epochs (ramps of a flash sale) and (b) abrupt, independent load
    draws (worst case for a local linearisation); single-pass vs refined method."""
    p, P = sim_params(); SY = {}
    for regime in ("gradual", "abrupt"):
        SY[regime] = {}
        for n in (8, 12, 16):
            g = np.random.default_rng(2000 + n); CM = configs(n)
            G = {k: [] for k in ("gap1", "gap2", "agree1", "agree2", "ok1", "ok2", "hyb", "t1", "t2", "tE", "exok")}
            for inst in range(20):
                v = np.sort(np.r_[1.0, g.uniform(0.05, 1.0, n - 1)])[::-1]; v[1] = max(v[1], 0.8)
                w = g.uniform(0.3, 4.0, n)
                Pn = dict(P); Pn["Km"] = float(np.ceil((v * w).sum() * 3.0))
                refm = model(np.zeros((1, n), int), 650.0, v, w, np.full(n, 1e-3), Pn, (1, 1, 1))
                refn = (float(refm["L"][0]), float(refm["C"][0]), 0.65)
                cprev = np.zeros(n, int)
                if regime == "gradual":   # flash-sale ramp 300 -> 4500 -> 300 RPS, 5-s epochs
                    peak = g.uniform(3000, 4500)
                    lams = np.r_[np.linspace(300, peak, 36), np.linspace(peak, 300, 36)] * g.uniform(0.97, 1.03, 72)
                else:
                    lams = g.uniform(300, 4500, 15)
                for lam in lams:
                    lam = float(lam); pc = np.full(n, 1e-4)
                    if g.random() < 0.3:
                        pc[g.integers(n)] += 0.02 / (1 + np.exp(-(g.uniform(0.5, 1.0) - 0.7) * 20))
                    t0 = time.perf_counter()
                    M = model(CM, lam, v, w, pc, Pn, refn); J = M["J0"] + Pn["kappa"] * np.abs(CM - cprev).sum(1)
                    ok = feasible(M, Pn); cE = CM[int(np.argmin(np.where(ok, J, np.inf)))] if ok.any() else np.ones(n, int)
                    G["tE"].append(time.perf_counter() - t0)
                    jE = Jnl(cE, lam, v, w, pc, Pn, refn, cprev)
                    t0 = time.perf_counter(); _, _, _, c1, ok1, _ = _lp_only(lam, v, w, pc, Pn, refn, cprev, cprev)
                    G["t1"].append(time.perf_counter() - t0)
                    t0 = time.perf_counter(); c2 = solve_refined(lam, v, w, pc, Pn, refn, cprev)
                    G["t2"].append(time.perf_counter() - t0)
                    ok2 = bool(feasible(model(c2[None, :], lam, v, w, pc, Pn, refn), Pn)[0])
                    G["gap1"].append(100 * (Jnl(c1, lam, v, w, pc, Pn, refn, cprev) - jE) / abs(jE))
                    G["gap2"].append(100 * (Jnl(c2, lam, v, w, pc, Pn, refn, cprev) - jE) / abs(jE))
                    G["agree1"].append(bool((c1 == cE).all())); G["agree2"].append(bool((c2 == cE).all()))
                    G["ok1"].append(ok1); G["ok2"].append(ok2); G["hyb"].append(0 < cE.sum() < n)
                    G["exok"].append(bool(ok.any()))
                    cprev = cE
            SY[regime][str(n)] = dict(
                states=len(G["gap1"]), hybrid_share=float(np.mean(G["hyb"])),
                exact_feasible=float(np.mean(G["exok"])),
                single=dict(gap=summ_gap(G["gap1"]), agree=float(np.mean(G["agree1"])),
                            feasible=float(np.mean(np.array(G["ok1"])[np.array(G["exok"])])),
                            ms=1000 * float(np.median(G["t1"]))),
                refined=dict(gap=summ_gap(G["gap2"]), agree=float(np.mean(G["agree2"])),
                             feasible=float(np.mean(np.array(G["ok2"])[np.array(G["exok"])])),
                             ms=1000 * float(np.median(G["t2"]))),
                exact_ms=1000 * float(np.median(G["tE"])))
            print(regime, n, json.dumps(SY[regime][str(n)]), flush=True)
    R["formulation_synth2"] = SY


# --------------------------------------------------------------- where the detector fires (main scenario)
class CountSim(Sim):
    def score(self, t, lam, d):
        a = super().score(t, lam, d)
        inside = self.anomaly["t0"] <= t < self.anomaly["t0"] + self.anomaly["dur"]
        self.cnt.append((inside, lam > 1000, a >= self.p.anomaly_alert, a >= self.p.anomaly_emergency))
        return a


def alert_one(seed):
    lam, fc, failure, anomaly = rc.window(seed, "test")
    s = CountSim("atlas", lam, fc["lstm"], p=replace(Params(), **T["atlas"]), seed=seed, failure=failure,
                 anomaly=anomaly, iforest=rc.ISO)
    s.cnt = []; s.run()
    return s.cnt


def exp_alerts(R):
    with Pool(2) as pool:
        C = np.array([c for run in pool.map(alert_one, TEST) for c in run], bool)
    ins, surge, al, em = C.T
    R["alerts_main"] = dict(
        epochs=int(len(C)),
        alert_rate_in_anomaly=float(al[ins].mean()),
        alert_rate_surge=float(al[~ins & surge].mean()), emergency_rate_surge=float(em[~ins & surge].mean()),
        alert_rate_normal=float(al[~ins & ~surge].mean()),
        share_of_alerts_during_surge=float((al & surge & ~ins).sum() / max(al.sum(), 1)))
    print("alerts", R["alerts_main"], flush=True)


if __name__ == "__main__":
    which = sys.argv[1:] or ["formulation", "formulation2", "blast", "anomaly", "combined", "alerts"]
    R = json.load(open(PATH)) if os.path.exists(PATH) else {}
    for name, fn in [("formulation", exp_formulation), ("formulation2", exp_formulation2), ("blast", exp_blast),
                     ("anomaly", exp_anomaly), ("combined", exp_combined), ("alerts", exp_alerts)]:
        if name in which:
            t0 = time.time(); fn(R); print(name, f"{time.time()-t0:.0f}s", flush=True)
            json.dump(R, open(PATH, "w"), indent=1, default=float)
