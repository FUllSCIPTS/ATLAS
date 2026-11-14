// ATLAS Architecture Explorer — Machine learning & optimisation view.
// Loaded after security.js (reuses secEsc, secCode, secTable, secLink, secSection, secCheck, umlChip, umlSection,
// umlTopicsSection, umlInspector) and before explorer.js. Every lab runs in the browser: the coupling BIP is a
// line-by-line replica of Sim.eval_all and Sim.bip in atlas_sim/cluster.py (main branch, atlas_sim.zip).
// ATLAS Go 1.3–1.4 labs: the digital twin and its Guardian are ports of android-app/atlas_go/twin.py; the
// LSTM runs the weights of atlas_go/lstm_weights.py (ml-live.js, loaded before this file) and replays a recorded
// run of atlas_go/loop.py; the actor-critic and MAPPO labs are ports of ml_lab/machine_learning/ml22 and ml23.

const mlIcons = {
  sliders: '<path d="M4 6h10m4 0h2M4 12h4m4 0h8M4 18h12m4 0h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
  tree: '<path d="M12 3v6m0 0-5 5m5-5 5 5M7 14v4m10-4v4"/><circle cx="12" cy="3" r="1.5"/><circle cx="7" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/>',
  dice: '<rect x="4" y="4" width="16" height="16" rx="3"/><circle cx="9" cy="9" r="1.2"/><circle cx="15" cy="15" r="1.2"/><circle cx="15" cy="9" r="1.2"/><circle cx="9" cy="15" r="1.2"/>',
  scale: '<path d="M12 4v16M5 20h14M6 8h12M6 8l-3 6a3 3 0 0 0 6 0Zm12 0-3 6a3 3 0 0 0 6 0Z"/>',
  bars: '<path d="M5 20V10m7 10V4m7 16v-7"/>',
  twin: '<rect x="3" y="7" width="11" height="11" rx="2"/><rect x="10" y="3" width="11" height="11" rx="2" stroke-dasharray="2.5 2"/>',
  actorcritic: '<rect x="3" y="4" width="8" height="7" rx="2"/><rect x="13" y="13" width="8" height="7" rx="2"/><path d="M7 11v5h6M17 13V8h-6"/>',
  agents: '<circle cx="7" cy="8" r="3"/><circle cx="17" cy="8" r="3"/><path d="M2 20c0-3 2.2-5 5-5s5 2 5 5c0-3 2.2-5 5-5s5 2 5 5M12 4v3"/>',
  loop: '<path d="M20 12a8 8 0 1 1-2.3-5.7M20 4v4h-4"/><path d="m8 14 2.5-3 2 2 3.5-4"/>',
};

const ML_MAIN = "https://github.com/FUllSCIPTS/ATLAS/blob/main/";
const ML_GUIDE = ML_MAIN + "docs/MACHINE_LEARNING_OPTIMISATION.md";
const ML_LAB = ML_MAIN + "ml_lab/ml_optimisation_lab.py";

const mlStatus = {
  paper: { label: "Paper", tone: "paper", text: "Evaluated in the article; research code on main" },
  impl: { label: "App / starter", tone: "impl", text: "Runs in ATLAS Go or the server starter; trained on synthetic data" },
  teach: { label: "Teaching extension", tone: "teach", text: "Not in the ATLAS code" },
};

const mlTopics = [
  { id: "overview", title: "ML & optimisation map", icon: "brain", status: null },
  { id: "optimizer", title: "Coupling BIP", icon: "sliders", status: "paper" },
  { id: "solvers", title: "Solvers", icon: "bars", status: "paper" },
  { id: "forecasting", title: "Forecasting", icon: "trend", status: "paper" },
  { id: "anomaly", title: "Isolation Forest", icon: "tree", status: "paper" },
  { id: "rl", title: "Reinforcement learning", icon: "dice", status: "impl" },
  { id: "twin", title: "Digital twin", icon: "twin", status: "impl" },
  { id: "actorcritic", title: "Actor & critic", icon: "actorcritic", status: "teach" },
  { id: "marl", title: "Two agents, one critic", icon: "agents", status: "teach" },
  { id: "loop", title: "LSTM + RL loop", icon: "loop", status: "impl" },
  { id: "evaluation", title: "Tuning & evaluation", icon: "scale", status: "paper" },
  { id: "gaps", title: "Gaps & exercises", icon: "bug", status: null },
];
const mlTopicById = Object.fromEntries(mlTopics.map((t) => [t.id, t]));

function mlChip(status) {
  if (!status) return "";
  const s = mlStatus[status];
  return `<span class="sec-chip ${s.tone}" title="${s.text}">${s.label}</span>`;
}

// Seeded PRNG so every lab is reproducible (mulberry32 + Box-Muller).
function mlRng(seed) {
  let a = seed >>> 0;
  const uniform = () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  const normal = () => { const u = Math.max(uniform(), 1e-12), v = uniform(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
  return { uniform, normal, range: (lo, hi) => lo + (hi - lo) * uniform(), int: (n) => Math.floor(uniform() * n) };
}

const ml = {
  topic: "overview",
  busy: "",
  bip: { lam: 2500, a: 0, anom: 4, hybrid: true, now: [0, 0, 0, 0, 0, 0] },
  enum: [],
  fc: null, fcOpts: { gd: 0.01, adam: 0.003 },
  forest: null, forestTrees: 35, forestSubtle: false,
  rl: null,
  twin: { ratio: 1.8, rollouts: 200, seed: 1, free: 3, price: 1.3, stab: null, drill: null, retest: null },
  ac: null, marl: null, marlSeed: 1,
  loop: { hour: 47, tag: "none", shock: 1, parity: null },
};

function mlButton(action, label, { primary = false, iconName = "", disabled = false } = {}) {
  return `<button type="button" class="sec-btn${primary ? " primary" : ""}" data-ml-action="${action}" data-keep="ml-${action}"${disabled || ml.busy ? " disabled" : ""}>${iconName ? icon(iconName, 15) : ""}${label}</button>`;
}

function mlSelect(name, label, options, value) {
  return `<label class="sec-field compact"><span>${label}</span><select data-ml-select="${name}" data-keep="ml-sel-${name}">${options.map(([v, l]) => `<option value="${v}"${String(v) === String(value) ? " selected" : ""}>${l}</option>`).join("")}</select></label>`;
}

function mlRange(name, label, min, max, step, value, shown) {
  return `<label class="sec-field ml-range"><span>${label} <b id="ml-out-${name}">${shown}</b></span><input type="range" data-ml-range="${name}" data-keep="ml-rg-${name}" min="${min}" max="${max}" step="${step}" value="${value}"></label>`;
}

// Small SVG line chart. series: [{ points: [[x, y]], cls }]; options: logX, logY, labels.
function mlChart(series, { logX = false, logY = false, xLabel = "", yLabel = "", height = 170, hlines = [], vline = null } = {}) {
  const W = 560, H = height, P = { l: 46, r: 12, t: 10, b: 30 };
  const all = series.flatMap((s) => s.points).concat(hlines.map((h) => [null, h.y]));
  const fx = (x) => (logX ? Math.log10(x) : x), fy = (y) => (logY ? Math.log10(y) : y);
  const xs = series.flatMap((s) => s.points.map((p) => fx(p[0]))), ys = all.map((p) => fy(p[1]));
  let [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  if (y1 - y0 < 1e-9) { y0 -= 1; y1 += 1; }
  const pad = (y1 - y0) * 0.06; y0 -= pad; y1 += pad;
  const sx = (x) => P.l + ((fx(x) - x0) / (x1 - x0 || 1)) * (W - P.l - P.r);
  const sy = (y) => H - P.b - ((fy(y) - y0) / (y1 - y0)) * (H - P.t - P.b);
  const fmt = (v) => (Number.isInteger(v) && Math.abs(v) < 1000 ? String(v) : Math.abs(v) >= 1000 ? (v / 1000).toFixed(v >= 10000 ? 0 : 1) + "k" : Math.abs(v) >= 10 ? v.toFixed(0) : Math.abs(v) >= 1 ? v.toFixed(1) : v.toPrecision(3));
  const ticksY = [0, 0.25, 0.5, 0.75, 1].map((f) => y0 + pad + f * (y1 - y0 - 2 * pad)).map((v) => (logY ? 10 ** v : v));
  const ticksX = logX ? [...new Set(series.flatMap((s) => s.points.map((p) => p[0])))].filter((v) => Math.abs(Math.log10(v) % 1) < 1e-9 || v === 1) : [0, 0.25, 0.5, 0.75, 1].map((f) => x0 + f * (x1 - x0));
  return `<svg class="ml-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${secEsc(yLabel)} against ${secEsc(xLabel)}">
    ${ticksY.map((v) => `<line class="grid" x1="${P.l}" x2="${W - P.r}" y1="${sy(v)}" y2="${sy(v)}"/><text class="tick" x="${P.l - 6}" y="${sy(v) + 3}" text-anchor="end">${fmt(v)}</text>`).join("")}
    ${ticksX.map((v) => `<text class="tick" x="${sx(v)}" y="${H - P.b + 13}" text-anchor="middle">${fmt(v)}</text>`).join("")}
    <text class="axis" x="${(W + P.l) / 2}" y="${H - 3}" text-anchor="middle">${xLabel}</text>
    <text class="axis" x="10" y="${(H - P.b) / 2}" transform="rotate(-90 10 ${(H - P.b) / 2})" text-anchor="middle">${yLabel}</text>
    ${hlines.map((h) => `<line class="ref ${h.cls}" x1="${P.l}" x2="${W - P.r}" y1="${sy(h.y)}" y2="${sy(h.y)}"/><text class="ref-label ${h.cls}" x="${W - P.r - 2}" y="${sy(h.y) - 4}" text-anchor="end">${h.label}</text>`).join("")}
    ${vline != null ? `<line class="ref now" x1="${sx(vline)}" x2="${sx(vline)}" y1="${P.t}" y2="${H - P.b}"/>` : ""}
    ${series.map((s) => `<polyline class="line ${s.cls}" points="${s.points.map((p) => `${sx(p[0]).toFixed(1)},${sy(p[1]).toFixed(1)}`).join(" ")}"/>`).join("")}
  </svg>`;
}

function mlLegend(items) {
  return `<p class="ml-legend">${items.map(([cls, text]) => `<span><i class="ml-swatch ${cls}"></i>${text}</span>`).join("")}</p>`;
}

// ================================================================== overview
const mlMap = [
  ["optimizer", "sliders", "Coupling BIP", "paper", "Every 5 s: which modules stay in the monolith and which become services — min latency + cost + risk + switching", "atlas_sim/cluster.py → Sim.bip"],
  ["solvers", "bars", "Solving it at scale", "paper", "Enumeration, LP relaxation + risk-aware rounding + repair, branch-and-bound", "run_bip_timing.py · run_round2.py"],
  ["forecasting", "trend", "LSTM traffic forecast", "paper", "Adam, gradient clipping, early stopping; the optimiser plans for max(load, forecast)", "atlas_sim/forecast.py"],
  ["anomaly", "tree", "Isolation Forest", "paper", "Unsupervised; the score raises a module's crash risk inside the BIP", "run_anomaly.py · Sim.score"],
  ["rl", "dice", "REINFORCE dispatch", "impl", "Softmax policy over four drivers; beats nearest-driver by a minute per ride", "atlas_go/intelligence.py"],
  ["rl", "activity", "Q-learning courier", "impl", "When to send the courier so they arrive as the food is ready", "training/rl_sim.py"],
  ["twin", "twin", "Digital twin + 3 agents", "impl", "ATLAS Go 1.3 Layer 2: mirror, foresee 30 min, rehearse dispatch and prices; a Guardian falls back to Layer 1", "atlas_go/twin.py"],
  ["actorcritic", "actorcritic", "Actor & critic networks", "teach", "A2C: a critic V(s) turns rewards into advantages; reaches v1.4's level in a quarter of the rides", "ml22_actor_critic.py"],
  ["marl", "agents", "Two agents, one critic", "teach", "MAPPO vs IPPO: dispatch and pricing agents trained with a shared, centralised critic", "ml23_mappo_shared_critic.py"],
  ["loop", "loop", "LSTM → RL live loop", "impl", "ATLAS Go 1.4 Layer 1: forecast, act, record, retrain nightly, keep only validated challengers", "atlas_go/loop.py"],
  ["evaluation", "scale", "Tuning & statistics", "paper", "Grid search on validation seeds; Wilcoxon, Holm, bootstrap CIs on 30 test runs", "run_cluster.py"],
];

function mlOverview() {
  return `<div class="sec-intro"><p>The ATLAS paper is about an <strong>optimisation algorithm</strong>: every five seconds a <strong>binary integer program</strong> decides which modules run together in one process (tight) and which run as separate services (loose). Learned models feed it — a <strong>forecast</strong> of the load and an <strong>anomaly score</strong> — and the ATLAS Go app adds <strong>reinforcement learning</strong> for dispatch and couriers. ATLAS Go 1.3–1.4 adds two layers: a <strong>digital twin</strong> with dispatch, pricing and Guardian agents (Layer 2), and a <strong>closed LSTM → RL loop</strong> that retrains and validates itself on the phone (Layer 1). The labs also teach <strong>actor and critic networks</strong> and <strong>multi-agent RL with a shared critic</strong>. Each card opens a live lab.</p>
    <div class="sec-legend">${Object.keys(mlStatus).map((k) => `<span>${mlChip(k)}<small>${mlStatus[k].text}</small></span>`).join("")}</div></div>
    <div class="sec-grid">${mlMap.map(([topic, ic, title, status, text, where]) => `<button type="button" class="sec-card" data-ml-topic="${topic}" data-keep="ml-card-${title}"><span class="sec-card-top">${icon(ic, 18)}${mlChip(status)}</span><strong>${title}</strong><span>${text}</span><code>${where}</code></button>`).join("")}</div>
    ${secSection("PIPELINE", "One ATLAS decision, every 5 seconds (Sim.run)", `<ol class="sec-flow">${[
      ["Forecast", "λ* = max(load, LSTM 5-min forecast)", "Plan for the load that is coming"],
      ["Score", "Isolation Forest on telemetry", "Blame the module whose demand deviates most"],
      ["Optimise", "Sim.bip over 2⁶ = 64 configurations", "min J subject to utilisation, SLA, replicas, availability"],
      ["Override", "score ≥ 0.9 → all loose; ≥ 0.7 → isolate blamed module", "Safety rules around the optimiser"],
      ["Hysteresis", "merge back only after 300 s", "Stop the optimiser oscillating"],
      ["Apply", "dual-run while pods start (8–30 s)", "40 ms state hand-over, measured in the prototype"],
    ].map(([t, c, s], i) => `<li><span class="sec-flow-n">${i + 1}</span><strong>${t}</strong><code>${c}</code><small>${s}</small></li>`).join("")}</ol>`)}
    ${secSection("INVENTORY", "Every model and optimiser in ATLAS", secTable(["Component", "Technique", "Problem type", "Where", "Data"], [
      ["Coupling decision", "BIP: enumeration · LP + rounding · branch-and-bound", "Combinatorial optimisation", "atlas_sim/cluster.py, run_bip_timing.py, run_round2.py", "Paper simulator"],
      ["Policy tuning", "Grid search on validation seeds", "Hyperparameter optimisation", "run_cluster.py → tune", "Paper simulator"],
      ["Traffic forecast", "LSTM / Bi-LSTM; Ridge-AR, naive baselines", "Time-series regression", "atlas_sim/forecast.py", "One-year synthetic trace"],
      ["Anomaly detector", "Isolation Forest", "Unsupervised outliers", "run_anomaly.py, starter/ml/discrete.py", "Synthetic telemetry"],
      ["Acceptance", "Logistic regression · Beta(9,1) posterior", "Classification · Bayesian estimate", "starter/ml/discrete.py · intelligence.acceptance", "Synthetic · on-device history"],
      ["Ride dispatch", "REINFORCE, softmax over 4 drivers", "Policy-gradient RL", "intelligence.py, training/rl_sim.py", "Synthetic rides"],
      ["Courier timing", "Tabular Q-learning, ε-greedy", "Value-based RL", "training/rl_sim.py → train_food", "Synthetic kitchens"],
      ["Driver supply", "Tabular agent, hindsight updates", "Online learning", "training/city_sim.py → run_rl", "Two simulated years"],
      ["Starter policy", "Action values + approval gate", "Contextual bandit", "starter/ml/rl.py", "Recorded or synthetic trips"],
      ["Digital twin (1.3)", "Mirror + 30-min foresight + Monte Carlo rehearsal (200 rollouts)", "Simulation-based planning", "atlas_go/twin.py → mirror, foresee, rehearse", "Layer 1's outlook and pools"],
      ["Agents 1–2 (1.3)", "Rehearse top-3 drivers; three price/move plans per area", "Planning on a learned policy", "twin.agent1, agent2, driver_hint", "Simulated Cork"],
      ["Agent 3 · Guardian (1.3)", "Hard limits, time budget, fallback, 500-rollout re-test", "Runtime shield (safe RL)", "twin.check_dispatch, check_price, retest_pricing", "—"],
      ["Live LSTM (1.4)", "24 h → 16 hidden → 6 h, pure Python on the phone", "Time-series regression", "atlas_go/loop.py, training/export_lstm.py", "Supply agent's experience log"],
      ["Forecast-aware supply (1.4)", "Q over (calendar, LSTM level), hindsight updates every hour", "Value-based RL, online", "Loop.choose, Loop.step", "The loop's own log"],
      ["Nightly retraining (1.4)", "LSTM head SGD + agent challenger; champion / challenger", "Online learning with validation", "Loop.daily_update", "Last 24 h / 7 days held out"],
      ["Actor-critic (lab)", "Actor network + critic network, advantage r − V(s)", "Policy-gradient RL", "ml_lab … ml22_actor_critic.py", "Synthetic rides"],
      ["MAPPO vs IPPO (lab)", "Two PPO actors, shared centralised critic vs own critics", "Multi-agent RL", "ml_lab … ml23_mappo_shared_critic.py", "Three-zone twin"],
    ]))}
    ${secSection("ATLAS GO 1.4", "Two learning layers in the app", `<ol class="sec-flow">${[
      ["Layer 1 forecasts", "Loop.forecast (LSTM, every hour)", "Demand ÷ ordinary for the next 1–6 h"],
      ["Layer 1 acts", "Loop.choose · intelligence.choose", "Extra drivers; dispatch by policy v1.4 (live surge feature)"],
      ["Layer 1 learns", "Loop.step · Loop.daily_update", "Outcomes logged; nightly champion / challenger"],
      ["Layer 2 mirrors", "twin.mirror · foresee", "The city now and in 30 minutes"],
      ["Layer 2 rehearses", "twin.agent1 · agent2", "Best of Layer 1's top 3; capped surge and moves"],
      ["Layer 2 guards", "twin.check_dispatch · check_price", "Anything out of bounds → Layer 1's answer"],
    ].map(([t, c, s], i) => `<li><span class="sec-flow-n">${i + 1}</span><strong>${t}</strong><code>${c}</code><small>${s}</small></li>`).join("")}</ol>`)}`;
}

// ================================================================== coupling BIP (replica of atlas_sim/cluster.py)
const ML_SERVICES = ["Gateway", "Catalogue", "Cart", "Inventory", "Payment", "Order"];
const ML_P = { // Params() with the tuned switch_pen / rho_max (results/cluster.json → tuned.atlas)
  visit: [1.00, 1.00, 0.45, 0.35, 0.18, 0.15], demand: [0.5, 2.0, 1.5, 1.5, 4.0, 3.0],
  mono_cores: 16, pod_cores: 1, sidecar_cores: 0.1, svc_fixed_cores: 1, min_rep: 2, max_rep: 40, base_ms: 10, net_ms: 4,
  sla_ms: 200, hpa_target: 0.7, net_cost_core_s: 2e-5, alpha: 1, beta: 1, gamma: 1, switch_pen: 0.02, rho_max: 0.85,
  ref_lam: 650, p0: 1e-4, p_a: 0.02, p_rho: 1e-3, a_min: 0.99, gamma_scale: 0.01, anomaly_alert: 0.7, anomaly_emergency: 0.9,
};

// Sim.eval_all for one configuration c (0 = tight, 1 = loose).
function mlEvalConfig(c, lam, pCrash) {
  const p = ML_P, v = p.visit, d = p.demand, n = v.length;
  const tight = c.map((x) => x === 0), anyT = tight.some(Boolean);
  let Dm = 0; for (let i = 0; i < n; i++) if (tight[i]) Dm += v[i] * d[i];
  const rho = anyT ? (lam * Dm) / 1000 / p.mono_cores : 0;
  let L = p.base_ms + (anyT ? Dm / (1 - Math.min(rho, 0.97)) : 0);
  for (let i = 0; i < n; i++) if (!tight[i]) L += v[i] * (d[i] / (1 - p.hpa_target) + p.net_ms);
  if (rho >= 0.98) L = 1e4;
  const reps = v.map((vi, i) => c[i] * Math.max(p.min_rep, Math.ceil((lam * vi * d[i]) / 1000 / (p.hpa_target * p.pod_cores))));
  let looseVisits = 0; for (let i = 0; i < n; i++) if (!tight[i]) looseVisits += v[i];
  const C = (anyT ? p.mono_cores : 0) + reps.reduce((s, r) => s + r * (p.pod_cores + p.sidecar_cores), 0) + c.reduce((s, x) => s + x, 0) * p.svc_fixed_cores + lam * looseVisits * p.net_cost_core_s;
  const phi = anyT ? Math.max(...v.filter((_, i) => tight[i])) : 0;
  let risk = 0;
  for (let i = 0; i < n; i++) {
    const host = tight[i] ? rho : p.hpa_target;
    const P = pCrash[i] + p.p_rho / (1 + Math.exp(-(host - 0.9) * 20));
    risk += P * (tight[i] ? phi : v[i]);
  }
  return { L, C, R: risk * lam, A: 1 - risk, rho, reps };
}

// Sim.bip: enumerate every configuration, objective J, constraints, first minimum (same order as numpy argmin).
function mlBipSolve(lam, a, anomModule, now, hybrid = true) {
  const p = ML_P, n = 6;
  const L0 = mlEvalConfig([0, 0, 0, 0, 0, 0], p.ref_lam, Array(n).fill(1e-3)), R0 = p.ref_lam * 1e-3;
  const pCrash = Array(n).fill(p.p0);
  if (anomModule >= 0) pCrash[anomModule] += p.p_a / (1 + Math.exp(-(a - 0.7) * 20));
  const rows = [];
  for (let k = 0; k < 2 ** n; k++) {
    const c = Array.from({ length: n }, (_, i) => (k >> i) & 1);
    const s = c.reduce((x, y) => x + y, 0);
    if (!hybrid && s !== 0 && s !== n) continue;
    const m = mlEvalConfig(c, lam, pCrash);
    const sw = c.reduce((x, ci, i) => x + Math.abs(ci - now[i]), 0);
    const parts = { lat: (p.alpha * m.L) / L0.L, cost: (p.beta * m.C) / L0.C, risk: (p.gamma * p.gamma_scale * m.R) / R0, sw: p.switch_pen * sw };
    const J = parts.lat + parts.cost + parts.risk + parts.sw;
    const why = m.rho > p.rho_max ? "monolith ρ > 0.85" : m.L > p.sla_ms ? "latency > SLA" : m.reps.some((r) => r > p.max_rep) ? "replicas > 40" : m.A < p.a_min ? "availability < 0.99" : "";
    rows.push({ k, c, ...m, parts, J, ok: !why, why });
  }
  let best = null;
  for (const r of rows) if (r.ok && (!best || r.J < best.J)) best = r;
  return { rows, best, choice: best ? best.c : Array(n).fill(1), feasible: rows.filter((r) => r.ok).length };
}

function mlAfterOverrides(choice, a, anomModule) {
  if (a >= ML_P.anomaly_emergency) return { c: Array(6).fill(1), note: "Emergency: anomaly score ≥ 0.9, every module goes loose" };
  if (a >= ML_P.anomaly_alert && anomModule >= 0 && !choice[anomModule]) { const c = choice.slice(); c[anomModule] = 1; return { c, note: `Alert: score ≥ 0.7, ${ML_SERVICES[anomModule]} forced out` }; }
  return { c: choice, note: "" };
}

const mlShape = (c) => { const s = c.reduce((x, y) => x + y, 0); return s === 0 ? "Monolith (all tight)" : s === c.length ? "Microservices (all loose)" : "Hybrid"; };

function mlConfigChips(c, now = null) {
  return `<div class="ml-modules">${ML_SERVICES.map((name, i) => `<span class="ml-module ${c[i] ? "loose" : "tight"}${now && now[i] !== c[i] ? " moved" : ""}"><b>${c[i] ? "service" : "monolith"}</b>${name}</span>`).join("")}</div>`;
}

function mlOptimizer() {
  const b = ml.bip;
  const res = mlBipSolve(b.lam, b.a, b.anom, b.now, b.hybrid);
  const fin = mlAfterOverrides(res.choice, b.a, b.anom);
  const best = res.best;
  const top = res.rows.filter((r) => r.ok).sort((x, y) => x.J - y.J).slice(0, 6);
  const extremes = [res.rows.find((r) => r.k === 0), res.rows.find((r) => r.k === 63)].filter(Boolean);
  const fmtRow = (r) => [`<code>${r.c.join("")}</code>${r === best ? " ← chosen" : ""}`, mlShape(r.c), r.rho.toFixed(2), r.L >= 1e4 ? "∞" : r.L.toFixed(1), r.C.toFixed(1), r.A.toFixed(5), r.J > 100 ? r.J.toFixed(0) : r.J.toFixed(3), r.ok ? `<span class="sec-yes">${icon("check", 13)}</span>` : `<span class="cr-bad">${r.why}</span>`];
  // sweep: decision against load with the current deployment and anomaly settings
  const loads = Array.from({ length: 50 }, (_, i) => 200 * (i + 1));
  const sweep = loads.map((lam) => mlAfterOverrides(mlBipSolve(lam, b.a, b.anom, b.now, b.hybrid).choice, b.a, b.anom).c);
  const cell = 520 / loads.length;
  const heat = `<svg class="ml-heat" viewBox="0 0 640 ${6 * 22 + 30}" role="img" aria-label="Which modules are loose at each load">
    ${ML_SERVICES.map((name, i) => `<text class="tick" x="110" y="${i * 22 + 15}" text-anchor="end">${name}</text>${sweep.map((c, j) => `<rect x="${116 + j * cell}" y="${i * 22 + 2}" width="${cell - 1}" height="19" class="${c[i] ? "loose" : "tight"}"><title>${loads[j]} req/s: ${name} ${c[i] ? "service" : "in monolith"}</title></rect>`).join("")}`).join("")}
    ${[1000, 2500, 5000, 7500, 10000].map((l) => `<text class="tick" x="${116 + (l / 200 - 0.5) * cell}" y="${6 * 22 + 16}" text-anchor="middle">${l >= 1000 ? l / 1000 + "k" : l}</text>`).join("")}
    <line class="ref now" x1="${116 + (b.lam / 200 - 0.5) * cell}" x2="${116 + (b.lam / 200 - 0.5) * cell}" y1="0" y2="${6 * 22}"/>
    <text class="axis" x="${116 + 260}" y="${6 * 22 + 29}" text-anchor="middle">offered load λ* (req/s)</text></svg>`;
  return `<div class="sec-intro"><p>The decision is a vector <strong>c ∈ {0,1}⁶</strong>: 0 keeps a module inside the monolith process, 1 runs it as an autoscaled service. <code>Sim.eval_all</code> predicts latency, cost, crash risk and availability of all 64 configurations, and <code>Sim.bip</code> picks the cheapest feasible one. This lab is a line-by-line replica of that code with the tuned parameters; the command-line lab runs the original.</p></div>
    ${secSection("OBJECTIVE", "What the optimiser minimises", `${secCode(`minimise   J(c) = α·L(c)/L₀ + β·C(c)/C₀ + γ·γs·R(c)/R₀ + κ·Σ|cᵢ − cᵢ(now)|
subject to  ρ_monolith ≤ ${ML_P.rho_max}      latency L ≤ ${ML_P.sla_ms} ms      replicas ≤ ${ML_P.max_rep} per service      availability ≥ ${ML_P.a_min}
            c ∈ {0,1}⁶   (α = β = γ = 1, γs = ${ML_P.gamma_scale}, κ = switch_pen = ${ML_P.switch_pen}; L₀, C₀, R₀ = monolith at ${ML_P.ref_lam} req/s)`)}
      ${secTable(["Term", "Model in Sim.eval_all", "Pushes towards"], [
        ["Latency L", "10 ms + monolith queue D/(1 − ρ) + service time and a network hop per loose module", "Extracting hot modules when the monolith saturates"],
        ["Cost C", "16 monolith cores + replicas × 1.1 cores + 1 core per service + network cost", "Keeping modules together"],
        ["Risk R", "crash probability × blast radius: a monolith crash fails the biggest tight module's traffic", "Isolating risky modules"],
        ["Switching", "κ per module moved", "Staying put unless it pays"],
      ])}`)}
    ${secSection("LIVE", "Run the optimiser", `<div class="sec-row">${mlRange("lam", "Load λ* (req/s)", 100, 10000, 100, b.lam, b.lam.toLocaleString())}${mlRange("a", "Anomaly score a", 0, 1, 0.05, b.a, b.a.toFixed(2))}${mlSelect("anom", "Anomalous module", ML_SERVICES.map((s, i) => [i, s]), b.anom)}</div>
      <div class="sec-actions">${mlButton("hybrid", b.hybrid ? "Hybrid allowed (ablation: off)" : "Hybrid disabled (turn on)", { iconName: "layers" })}${mlButton("deploy", "Deploy this choice (sets c now)", { iconName: "check" })}${mlButton("reset", "Reset to monolith", { iconName: "reset" })}</div>
      <p class="sec-label">Currently deployed (c now): <code>${b.now.join("")}</code> — moving a module costs κ = ${ML_P.switch_pen}. This lab shows the optimiser alone; in <code>Sim.run</code>, hysteresis would hold a merge back for 300 s.</p>
      ${mlConfigChips(fin.c, b.now)}
      <ul class="sec-checks">${secCheck(true, `${mlShape(fin.c)} — <code>${fin.c.join("")}</code>`, `${res.feasible} of ${res.rows.length} configurations feasible${fin.note ? " · " + fin.note : ""}`)}</ul>
      ${best ? `<div class="ml-terms">${[["latency", best.parts.lat], ["cost", best.parts.cost], ["risk", best.parts.risk], ["switching", best.parts.sw]].map(([k, v]) => `<span class="ml-term ${k}" style="flex-grow:${Math.max(v, 0.02).toFixed(3)}"><b>${k}</b>${v.toFixed(3)}</span>`).join("")}</div><p class="sec-note">${icon("sliders", 14)} J = ${best.J.toFixed(3)} for the chosen configuration: ρ<sub>m</sub> ${best.rho.toFixed(2)}, latency ${best.L.toFixed(1)} ms, ${best.C.toFixed(1)} cores, availability ${best.A.toFixed(5)}.</p>` : `<ul class="sec-checks">${secCheck(false, "No configuration is feasible", "Sim.bip falls back to all-loose")}</ul>`}
      <p class="sec-label">Best feasible configurations, plus the two classic choices</p>
      ${secTable(["c (G C Ca I P O)", "Shape", "ρ mono", "L ms", "Cores", "Avail.", "J", "Feasible"], [...top, ...extremes.filter((r) => !top.includes(r))].map(fmtRow), "ml-table")}`)}
    ${secSection("SWEEP", "The decision across load (same anomaly and deployment settings)", `${heat}${mlLegend([["tight", "inside the monolith"], ["loose", "separate service"]])}<p class="sec-text">Light load: one process is cheapest. As load rises, modules leave the monolith so it stays below ρ<sub>max</sub>; which ones is the latency–cost–blast-radius trade-off. Raise the anomaly score above 0.7 and the blamed module leaves early. Turn hybrid off and the optimiser can only jump from monolith to full microservices — the ablation that raised p99 latency from 90 to 127 ms.</p>`)}`;
}

// ================================================================== solvers
const ML_TIMING = [ // results/bip_timing.json (median of 30 instances)
  [6, 0.163, 8.985, 2.279, 3.674], [10, 0.305, 7.902, 2.304, 0], [16, 11.939, 8.788, 2.794, 0], [25, null, 6.899, 2.345, 0],
  [50, null, 7.781, 2.921, 0], [100, null, 12.323, 3.418, 0], [200, null, 59.946, 4.222, 0.121], [500, null, 401.235, 6.378, 0.234],
];

// Random linear instance shaped like run_bip_timing.instance(); enumerate all 2^n binary vectors.
function mlEnumerateTiming(n, seed = n) {
  const g = mlRng(seed), u = (lo, hi) => g.range(lo, hi);
  const lm = [], ln = [], kp = [], kn = [], pr = [], dd = [], r = [];
  for (let i = 0; i < n; i++) { lm.push(u(0.01, 0.5)); ln.push(u(2, 15)); kp.push(u(0.5, 3)); kn.push(u(0.05, 0.5)); pr.push(u(1e-4, 0.05)); dd.push(1 + g.int(Math.max(2, Math.floor(n / 3)) - 1)); r.push(1 + g.int(5)); }
  const f = lm.map((_, i) => (ln[i] - lm[i]) + (kp[i] + kn[i]) - 50 * pr[i] * dd[i]);
  const A = [ln.map((x, i) => x - lm[i]), kp.map((x, i) => x + kn[i]), r, pr.map((x, i) => -x * dd[i])];
  const ub = [0.6 * A[0].reduce((s, x) => s + x, 0), 0.6 * A[1].reduce((s, x) => s + x, 0), 0.6 * A[2].reduce((s, x) => s + x, 0), 0.3 * A[3].reduce((s, x) => s + x, 0)];
  const t0 = performance.now();
  let best = Infinity, bestK = -1;
  for (let k = 0; k < 2 ** n; k++) {
    let J = 0, a0 = 0, a1 = 0, a2 = 0, a3 = 0;
    for (let i = 0; i < n; i++) if ((k >> i) & 1) { J += f[i]; a0 += A[0][i]; a1 += A[1][i]; a2 += A[2][i]; a3 += A[3][i]; }
    if (a0 <= ub[0] && a1 <= ub[1] && a2 <= ub[2] && a3 <= ub[3] && J < best) { best = J; bestK = k; }
  }
  return { n, ms: performance.now() - t0, configs: 2 ** n, best, chosen: bestK >= 0 ? bestK.toString(2).split("").filter((x) => x === "1").length : 0 };
}

function mlSolvers() {
  const chart = mlChart([
    { points: ML_TIMING.filter((r) => r[1] != null).map((r) => [r[0], r[1]]), cls: "s1" },
    { points: ML_TIMING.map((r) => [r[0], r[2]]), cls: "s2" },
    { points: ML_TIMING.map((r) => [r[0], r[3]]), cls: "s3" },
  ], { logX: true, logY: true, xLabel: "modules n", yLabel: "solve time (ms)" });
  return `<div class="sec-intro"><p>Six modules give 64 candidates, so <code>Sim.bip</code> simply enumerates them (0.27 ms per decision in the 30 test runs). Real systems have more modules. The paper therefore <strong>linearises</strong> the model around the current deployment, solves the <strong>LP relaxation</strong> (0 ≤ cᵢ ≤ 1), rounds with a <strong>risk-aware threshold</strong>, then <strong>verifies and repairs</strong> on the exact model — and checks the result against exact solvers.</p></div>
    ${secSection("METHODS", "Three ways to solve the coupling BIP", secTable(["Method", "Phase", "Idea", "Where"], [
      ["Exhaustive enumeration", "2a", "Evaluate all 2ⁿ configurations on the nonlinear model; exact", "<code>Sim.bip</code>, <code>run_round2.solve_all</code>"],
      ["Linearise + LP relaxation", "2b", "One-flip finite differences around c(now) give linear coefficients; solve min fᵀx, Ax ≤ b, 0 ≤ x ≤ 1 with HiGHS", "<code>run_round2.solve_all</code>, <code>run_bip_timing.lp_round</code>"],
      ["Risk-aware rounding", "2b", "cᵢ = 1 if xᵢ ≥ τᵢ, τᵢ = 0.5 − 0.3·riskᵢ / max risk: risky modules are extracted more readily", "<code>lp_round</code>"],
      ["Verify + greedy repair", "3 (Steps 19–23)", "Check the rounded c on the nonlinear model; flip the module behind each violated constraint until feasible", "<code>run_round2.repair</code>"],
      ["Branch-and-bound", "reference", "Exact mixed-integer solver (HiGHS via scipy.optimize.milp)", "<code>run_bip_timing.py</code>"],
      ["Sequential linearisation + local search", "revision", "Re-linearise until stable, then 1-flip descent on the exact objective", "<code>solve_refined</code>, <code>local_search</code>"],
    ]))}
    ${secSection("MEASURED", "Solve time as the number of modules grows (results/bip_timing.json)", `${chart}${mlLegend([["s1", "enumeration"], ["s2", "branch-and-bound (HiGHS)"], ["s3", "LP + rounding + repair"]])}
      ${secTable(["n", "Enumeration", "Branch-and-bound", "LP + rounding", "LP gap (median)"], ML_TIMING.map((r) => [r[0], r[1] == null ? "—" : r[1].toFixed(2) + " ms", r[2].toFixed(1) + " ms", r[3].toFixed(1) + " ms", r[4].toFixed(2) + " %"]))}
      <p class="sec-note">${icon("check", 14)} On 32 400 decision states recorded in the 30 test runs, the linearised BIP and the LP method pick the same configuration as the exact nonlinear optimum in 96.5 % and 96.4 % of states, and are always feasible after repair (results/round2.json).</p>`)}
    ${secSection("LIVE", "Feel the exponential: enumerate 2ⁿ configurations in your browser", `<p class="sec-text">Random instances shaped like <code>run_bip_timing.instance</code>: four linear constraints (latency, cost, replicas, availability). Each extra module doubles the work.</p>
      <div class="sec-actions">${[6, 10, 14, 18, 20].map((n) => mlButton(`enum-${n}`, `n = ${n}`, { iconName: "play" })).join("")}${ml.enum.length ? mlButton("enum-clear", "Clear", { iconName: "reset" }) : ""}</div>
      ${ml.busy === "enum" ? `<p class="sec-note">Enumerating…</p>` : ""}
      ${ml.enum.length ? secTable(["n", "Configurations", "Time in your browser", "Modules extracted in the optimum"], ml.enum.map((e) => [e.n, e.configs.toLocaleString(), e.ms.toFixed(1) + " ms", e.chosen])) + `<p class="sec-note">${icon("trend", 14)} At n = 50 enumeration would need 2⁵⁰ ≈ 10¹⁵ evaluations; branch-and-bound needs 7.8 ms and the LP method 2.9 ms.</p>` : ""}`)}`;
}

// ================================================================== forecasting
// Paper traffic model (atlas_sim/traffic.py → ecommerce_trace): daily + weekly sine, noise, flash sales.
function mlTrace(days, seed = 2026) {
  const g = mlRng(seed), n = days * 1440, r = new Float64Array(n);
  for (let t = 0; t < n; t++) {
    const h = (t / 60) % 24, w = (t / 1440) % 7;
    r[t] = 600 + 350 * Math.sin((2 * Math.PI * h) / 24 - (2 * Math.PI * 9) / 24) + 120 * Math.sin((2 * Math.PI * w) / 7 - (2 * Math.PI * 3) / 7) + g.normal() * 60;
  }
  for (let e = 0; e < Math.floor(days / 3); e++) {
    const s = 1440 + g.int(n - 1640), A = g.range(4000, 8000), D = Math.floor(g.range(20, 90)), mu = s + D / 3, sig = Math.max(D / 6, 2);
    for (let t = s; t <= Math.min(s + D, n - 1); t++) r[t] += A * Math.exp(-((t - mu) ** 2) / (2 * sig * sig));
  }
  for (let t = 0; t < n; t++) r[t] = Math.max(r[t], 0);
  return r;
}

// Fit a 5-minute-ahead AR(lags) forecaster by mini-batch gradient descent or Adam with early stopping.
function mlTrainForecaster(optimiser, lr, { lags = 30, days = 21, maxEpochs = 120, patience = 10 } = {}) {
  const r = mlTrace(days), n = r.length, H = 5;
  const y = Array.from(r, (x) => Math.log1p(x));
  const trEnd = 14 * 1440, vaEnd = 17 * 1440;
  let mu = 0, sd = 0; for (let i = 0; i < trEnd; i++) mu += y[i]; mu /= trEnd; for (let i = 0; i < trEnd; i++) sd += (y[i] - mu) ** 2; sd = Math.sqrt(sd / trEnd);
  const z = y.map((x) => (x - mu) / sd);
  const idx = []; for (let t = 1440; t < n - H; t++) idx.push(t);
  const tr = idx.filter((t) => t < trEnd), va = idx.filter((t) => t >= trEnd && t < vaEnd), te = idx.filter((t) => t >= vaEnd);
  const predict = (w, t) => { let s = w[lags]; for (let k = 0; k < lags; k++) s += w[k] * z[t - k]; return s; };
  const mse = (w, set) => set.reduce((s, t) => s + (predict(w, t) - z[t + H]) ** 2, 0) / set.length;
  let w = new Float64Array(lags + 1), m1 = new Float64Array(lags + 1), m2 = new Float64Array(lags + 1);
  const g = mlRng(0), curve = [];
  let best = Infinity, bestW = w.slice(), bad = 0, step = 0;
  const t0 = performance.now();
  for (let ep = 1; ep <= maxEpochs; ep++) {
    const order = tr.slice(); for (let i = order.length - 1; i > 0; i--) { const j = g.int(i + 1); [order[i], order[j]] = [order[j], order[i]]; }
    for (let b = 0; b < order.length; b += 256) {
      const batch = order.slice(b, b + 256), grad = new Float64Array(lags + 1);
      for (const t of batch) { const e = (2 * (predict(w, t) - z[t + H])) / batch.length; for (let k = 0; k < lags; k++) grad[k] += e * z[t - k]; grad[lags] += e; }
      step++;
      for (let k = 0; k <= lags; k++) {
        if (optimiser === "adam") { m1[k] = 0.9 * m1[k] + 0.1 * grad[k]; m2[k] = 0.999 * m2[k] + 0.001 * grad[k] ** 2; w[k] -= (lr * (m1[k] / (1 - 0.9 ** step))) / (Math.sqrt(m2[k] / (1 - 0.999 ** step)) + 1e-8); }
        else w[k] -= lr * grad[k];
      }
    }
    const v = mse(w, va); curve.push([ep, v]);
    if (!Number.isFinite(v)) break;
    if (v < best - 1e-5) { best = v; bestW = w.slice(); bad = 0; } else if (++bad >= patience) break;
  }
  const back = (x) => Math.expm1(x * sd + mu);
  const diverged = !(best < 10);
  const mae = (fn) => te.reduce((s, t) => s + Math.abs(fn(t) - r[t + H]), 0) / te.length;
  const day = te.slice(-1440).filter((_, i) => i % 5 === 0);
  return {
    optimiser, lr, curve, best, diverged, epochs: curve.length, ms: performance.now() - t0,
    mae: mae((t) => back(predict(bestW, t))), persistence: mae((t) => r[t]), seasonal: mae((t) => r[t + H - 1440]),
    day: day.map((t) => [(t - day[0]) / 60, r[t + H], back(predict(bestW, t))]),
  };
}

function mlForecasting() {
  const fc = ml.fc;
  return `<div class="sec-intro"><p>ATLAS plans for λ* = max(load, forecast), so pods start before a flash sale arrives. The paper's forecaster is an <strong>LSTM</strong> trained by <strong>optimisation</strong>: minimise mean-squared error with <strong>Adam</strong>, clip gradients, stop early when the validation loss stops improving, keep the best weights.</p></div>
    ${secSection("PAPER", "Forecasting results, 5 minutes ahead (results/forecast.json)", secTable(["Model", "MAE (req/s)", "RMSE", "MAPE"], [
      ["<strong>LSTM</strong> (2 × 128, Adam lr 1e-3, clip 1.0, patience 10)", "<strong>51.7</strong>", "98.7", "14.8 %"], ["Bi-LSTM", "53.5", "104.5", "14.8 %"],
      ["Ridge-AR (60 lags + yesterday + calendar)", "57.5", "151.4", "15.1 %"], ["Persistence", "72.2", "120.2", "19.2 %"], ["Seasonal naive", "111.8", "313.3", "35.1 %"],
    ]) + `<p class="sec-note">${icon("activity", 14)} During flash sales the LSTM's MAE rises to 745 req/s (48 in normal traffic): forecasts help, but the optimiser also reacts to the measured load.</p>`)}
    ${secSection("LIVE", "Training is optimisation: gradient descent vs Adam", `<p class="sec-text">21 days of the paper's traffic model (daily and weekly cycles, noise, flash sales). Model: linear AR(30) on log-load, 5 minutes ahead. Train on days 1–14, early-stop on days 15–17, test on days 18–21. Mini-batches of 256.</p>
      <div class="sec-row">${mlSelect("gd", "Gradient descent learning rate", [[0.001, "0.001"], [0.01, "0.01"], [0.05, "0.05 (too high)"]], ml.fcOpts.gd)}${mlSelect("adam", "Adam learning rate", [[0.0003, "0.0003"], [0.003, "0.003"], [0.03, "0.03"]], ml.fcOpts.adam)}</div>
      <div class="sec-actions">${mlButton("fc-train", fc ? "Train again" : "Train both", { primary: true, iconName: "play" })}</div>
      ${ml.busy === "fc" ? `<p class="sec-note">Training…</p>` : ""}
      ${fc ? `${mlChart([{ points: fc.gd.curve.filter((p) => p[1] < 5), cls: "s1" }, { points: fc.adam.curve.filter((p) => p[1] < 5), cls: "s3" }].filter((x) => x.points.length), { xLabel: "epoch", yLabel: "validation MSE", logY: true })}${mlLegend([["s1", `gradient descent, lr ${fc.gd.lr}`], ["s3", `Adam, lr ${fc.adam.lr}`]])}
        ${secTable(["Model", "Epochs (early stop)", "Best val. MSE", "Test MAE (req/s)", "Time"], [
          ...[["gradient descent", fc.gd], ["Adam", fc.adam]].map(([name, r]) => [`AR(30), ${name}, lr ${r.lr}`, r.epochs, r.diverged ? `<span class="cr-bad">diverged</span>` : r.best.toFixed(4), r.diverged ? "—" : r.mae.toFixed(1), r.ms.toFixed(0) + " ms"]),
          ["Persistence (last value)", "—", "—", fc.adam.persistence.toFixed(1), "—"], ["Seasonal naive (yesterday)", "—", "—", fc.adam.seasonal.toFixed(1), "—"],
        ])}
        ${mlChart([{ points: fc.adam.day.map((p) => [p[0], p[1]]), cls: "s0" }, { points: fc.adam.day.map((p) => [p[0], p[2]]), cls: "s3" }].filter(() => !fc.adam.diverged), { xLabel: "hour of the last test day", yLabel: "req/s", height: 150 })}${mlLegend([["s0", "actual load"], ["s3", "Adam AR(30) forecast, 5 min ahead"]])}
        <p class="sec-note">${icon("trend", 14)} Plain gradient descent uses one step size for every weight: at lr 0.05 it diverges. Adam scales each weight's step by running gradient statistics, so lr 0.0003 to 0.03 all converge. On this convex model both reach about the same optimum; on the non-convex LSTM that robustness is why the paper uses Adam.</p>` : ""}`)}
    ${secSection("IN ATLAS", "Three forecasters in the repository", secTable(["Where", "Model", "Optimiser", "Data"], [
      ["atlas_sim/forecast.py (paper)", "LSTMForecaster, 2 × 128, dropout 0.2; Bi-LSTM", "Adam 1e-3, batch 64, clip 1.0, early stopping", "One-year trace, 70/15/15 % by time"],
      ["starter/ml/forecast.py", "DemandLSTM, 1 × 12 units, 12-step window", "Adam 0.015, 75 full-batch epochs", "Synthetic daily cycle"],
      ["android-app/training/city_sim.py", "LSTM in numpy", "Hand-written Adam (LSTM.step)", "Two simulated years of Cork demand"],
      ["android-app/training/export_lstm.py → atlas_go/lstm_weights.py (1.4)", "Compact LSTM, 24 h → 16 hidden → 6 h, run in pure Python on the phone", "Adam offline; nightly SGD on the output layer on the phone, validated", "The supply agent's experience log + 30 calendar inputs"],
    ]) + `<p class="sec-note">${icon("loop", 14)}<span class="ml-t">ATLAS Go 1.4 runs its LSTM live and retrains it as outcomes arrive — run it, and replay the Jazz weekend, in the <button type="button" class="sec-inline-link" data-ml-topic="loop" data-keep="ml-xlink-loop">LSTM + RL loop</button> tab.</span></p>`)}`;
}

// ================================================================== isolation forest
function mlDrivers(subtle = false, seed = 11) { // starter/ml/discrete.py: normal drivers and odd ones (distance km, speed km/h)
  const g = mlRng(seed), normal = [], odd = [];
  for (let i = 0; i < 800; i++) normal.push([g.range(0.1, 12), Math.max(0, 28 + 9 * g.normal())]);
  for (let i = 0; i < 100; i++) odd.push(subtle ? [g.range(9, 16), g.range(45, 62)] : [g.range(17, 35), g.range(115, 200)]);
  return { train: normal.slice(0, 640), test: normal.slice(640), odd };
}

const mlC = (n) => (n <= 1 ? 0 : n === 2 ? 1 : 2 * (Math.log(n - 1) + 0.5772156649) - (2 * (n - 1)) / n);

function mlTree(points, depth, maxDepth, g) {
  if (depth >= maxDepth || points.length <= 1) return { size: points.length };
  const f = g.int(2), vals = points.map((p) => p[f]), lo = Math.min(...vals), hi = Math.max(...vals);
  if (hi === lo) return { size: points.length };
  const split = g.range(lo, hi);
  return { f, split, left: mlTree(points.filter((p) => p[f] < split), depth + 1, maxDepth, g), right: mlTree(points.filter((p) => p[f] >= split), depth + 1, maxDepth, g) };
}

function mlPath(node, x, depth = 0) { return node.size !== undefined ? depth + mlC(node.size) : mlPath(x[node.f] < node.split ? node.left : node.right, x, depth + 1); }

// Grow an Isolation Forest (sub-sample 256, depth limit log2 256 = 8) and score every point.
function mlForestGrow(nTrees, subtle = false) {
  const data = mlDrivers(subtle), g = mlRng(7), psi = Math.min(256, data.train.length), maxDepth = Math.ceil(Math.log2(psi));
  const trees = [];
  for (let t = 0; t < nTrees; t++) {
    const sample = []; for (let i = 0; i < psi; i++) sample.push(data.train[g.int(data.train.length)]);
    trees.push(mlTree(sample, 0, maxDepth, g));
  }
  const score = (x) => 2 ** (-(trees.reduce((s, tr) => s + mlPath(tr, x), 0) / trees.length) / mlC(psi));
  const trainScores = data.train.map(score).sort((a, b) => a - b);
  const threshold = trainScores[Math.floor(0.97 * trainScores.length)]; // contamination 0.03, as discrete.py
  const pts = [...data.test.map((x) => ({ x, y: 0, s: score(x) })), ...data.odd.map((x) => ({ x, y: 1, s: score(x) }))];
  const pos = pts.filter((p) => p.y), neg = pts.filter((p) => !p.y);
  let wins = 0; for (const a of pos) for (const b of neg) wins += a.s > b.s ? 1 : a.s === b.s ? 0.5 : 0;
  const flagged = pts.filter((p) => p.s > threshold);
  const depthOf = (x) => trees.reduce((s, tr) => s + mlPath(tr, x), 0) / trees.length;
  return { nTrees, subtle, threshold, pts, auc: wins / (pos.length * neg.length), precision: flagged.filter((p) => p.y).length / Math.max(flagged.length, 1), recall: flagged.filter((p) => p.y).length / pos.length, fpr: flagged.filter((p) => !p.y).length / neg.length, depthNormal: depthOf([5, 28]), depthOdd: depthOf(subtle ? [12, 55] : [25, 160]) };
}

function mlAnomaly() {
  const F = ml.forest;
  const scatter = F ? (() => {
    const W = 560, H = 230, P = { l: 46, r: 12, t: 10, b: 30 }, sx = (v) => P.l + (v / 36) * (W - P.l - P.r), sy = (v) => H - P.b - (v / 210) * (H - P.t - P.b);
    return `<svg class="ml-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Driver telemetry coloured by anomaly score">
      ${[0, 50, 100, 150, 200].map((v) => `<line class="grid" x1="${P.l}" x2="${W - P.r}" y1="${sy(v)}" y2="${sy(v)}"/><text class="tick" x="${P.l - 6}" y="${sy(v) + 3}" text-anchor="end">${v}</text>`).join("")}
      ${[0, 10, 20, 30].map((v) => `<text class="tick" x="${sx(v)}" y="${H - P.b + 13}" text-anchor="middle">${v}</text>`).join("")}
      <text class="axis" x="${(W + P.l) / 2}" y="${H - 3}" text-anchor="middle">distance to pickup (km)</text><text class="axis" x="10" y="${(H - P.b) / 2}" transform="rotate(-90 10 ${(H - P.b) / 2})" text-anchor="middle">speed (km/h)</text>
      ${F.pts.map((p) => `<circle cx="${sx(p.x[0]).toFixed(1)}" cy="${sy(p.x[1]).toFixed(1)}" r="${p.y ? 3.4 : 2.6}" class="${p.s > F.threshold ? "flag" : "ok"}${p.y ? " odd" : ""}" style="opacity:${(0.35 + 0.65 * Math.min(1, Math.max(0, (p.s - 0.35) / 0.4))).toFixed(2)}"><title>${p.x[0].toFixed(1)} km, ${p.x[1].toFixed(0)} km/h: score ${p.s.toFixed(3)}</title></circle>`).join("")}
    </svg>`;
  })() : "";
  return `<div class="sec-intro"><p>An Isolation Forest grows random trees: pick a feature at random, split at a random value, repeat until each point is alone. <strong>Unusual points are isolated after few splits</strong>, so a short average path length E[h(x)] gives a high score s(x) = 2<sup>−E[h(x)]/c(n)</sup>. It needs <strong>no labels</strong> — useful when nobody has labelled the incidents.</p></div>
    ${secSection("IN ATLAS", "Where the Isolation Forest runs", secTable(["Where", "Data", "Settings", "Used for"], [
      ["run_anomaly.py (paper)", "8 telemetry fields; 5 injected fault types", "100 trees, 256 samples, contamination 0.05", "ROC-AUC 0.9999, F1 0.975 over 10 seeds"],
      ["Sim.score (paper)", "Telemetry synthesised from simulator state", "Normalised to 0–1; alert 0.7, emergency 0.9", "Raises the blamed module's crash risk in the BIP"],
      ["FastIForest (paper)", "—", "Re-implements score_samples for one row", "≈ 50× faster inside the 1-s simulation loop"],
      ["starter/ml/discrete.py", "Driver distance and speed", "35 trees, contamination 0.03", "anomaly_flag per driver in /internal/v1/score"],
    ]))}
    ${secSection("LIVE", "Grow a forest on the starter's driver data", `<p class="sec-text">640 normal drivers for training (no labels). Evaluation: 160 normal drivers and 100 odd ones — either implausible (17–35 km away at 115–200 km/h, as in <code>discrete.py</code>) or subtle (9–16 km at 45–62 km/h, just outside normal). Threshold: the 97th percentile of training scores (contamination 0.03).</p>
      <div class="sec-row">${mlSelect("trees", "Trees", [[1, "1"], [5, "5"], [35, "35 (starter)"], [100, "100 (paper)"]], ml.forestTrees)}${mlSelect("subtle", "Odd drivers", [[0, "Implausible (starter)"], [1, "Subtle"]], ml.forestSubtle ? 1 : 0)}</div>
      <div class="sec-actions">${mlButton("forest", F ? "Grow again" : "Grow the forest", { primary: true, iconName: "tree" })}</div>
      ${F ? `${scatter}${mlLegend([["ok", "score below threshold"], ["flag", "flagged as anomalous"], ["odd", "larger dots: injected implausible drivers"]])}
        ${secTable(["Trees", "ROC-AUC", "Precision", "Recall", "False-positive rate", "Avg. path: normal (5 km, 28 km/h)", `Avg. path: odd (${F.subtle ? "12 km, 55" : "25 km, 160"} km/h)`], [[F.nTrees, F.auc.toFixed(4), F.precision.toFixed(3), F.recall.toFixed(3), F.fpr.toFixed(3), F.depthNormal.toFixed(2), F.depthOdd.toFixed(2)]])}
        <p class="sec-note">${icon("tree", 14)} The odd driver is isolated in about ${F.depthOdd.toFixed(1)} splits against ${F.depthNormal.toFixed(1)} for a normal one. Implausible drivers are so far from normal that even one tree separates them; for subtle ones, compare 1 tree with 35 or 100 — averaging many random trees is what makes the score reliable. Contamination only sets the threshold: about 3 % of normal drivers are flagged by design.</p>` : ""}`)}`;
}

// ================================================================== reinforcement learning (port of atlas_go/intelligence.py)
const ML_APPROVED = [7.304, 5.769, 7.87, 0.852]; // learned.RIDE_WEIGHTS, policy v1.4
const ML_COURIER = { "-2": 0, "-1": 0, 0: 0, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 9, 10: 9, 11: 10, 12: 11, 13: 12, 14: 13, 15: 14, 16: 15, 17: 16, 18: 15 }; // learned.COURIER_DELAY
const ML_POOL = [["Ava", "Mardyke", 2, 0.81, 0.85, true], ["Morgan", "Western Road", 3, 0.94, 0.1, false], ["Niamh", "City Centre", 6, 0.88, 0.3, false], ["Ciarán", "Douglas", 8, 0.97, 0.05, false]];

const mlFeatures = (c) => [-c.eta / 5, c.accept, -(c.surge * (c.last ? 1 : 0)), -c.surge];
const mlScore = (c, w) => mlFeatures(c).reduce((s, f, i) => s + f * w[i], 0);
function mlExpectedCost(c) { // intelligence.expected_cost
  const pLate = Math.max(0, Math.min(1, (c.eta + 1.5 + 5 - 8) / 3));
  const pickup = c.accept * c.eta + (1 - c.accept) * (c.eta + 1.5 + 3.5);
  const cancel = 0.45 * (c.accept * (c.eta > 8 ? 1 : 0) + (1 - c.accept) * pLate);
  return pickup + 10 * cancel + c.surge * (c.last ? 1 : 0) * 10;
}
const mlCandidates = (g) => Array.from({ length: 4 }, () => ({ eta: g.range(1, 9), accept: g.range(0.35, 0.98), surge: g.uniform() ** 1.5, last: g.uniform() < 0.45 }));
function mlSoftmax(scores) { const top = Math.max(...scores), ex = scores.map((s) => Math.exp(s - top)), z = ex.reduce((a, b) => a + b, 0); return ex.map((e) => e / z); }

function mlRlNew() {
  const tg = mlRng(1007), test = Array.from({ length: 300 }, () => mlCandidates(tg));
  const evalPolicy = (w, greedy) => test.reduce((s, cs) => { const sc = cs.map((c) => mlScore(c, w)); if (greedy) return s + mlExpectedCost(cs[sc.indexOf(Math.max(...sc))]); const p = mlSoftmax(sc); return s + cs.reduce((t, c, i) => t + p[i] * mlExpectedCost(c), 0); }, 0) / test.length;
  const nearest = test.reduce((s, cs) => s + mlExpectedCost(cs.reduce((b, c) => (c.eta < b.eta ? c : b))), 0) / test.length;
  return { g: mlRng(7), w: [0, 0, 0, 0], base: -10, episodes: 0, curve: [[1, evalPolicy([0, 0, 0, 0], false)]], evalPolicy, nearest, approved: evalPolicy(ML_APPROVED, true), lastReward: null };
}

// REINFORCE with a running-average baseline, exactly as LearningLab.train.
function mlRlTrain(state, episodes, lr = 0.004) {
  const g = state.g;
  let next = state.curve.length ? state.curve[state.curve.length - 1][0] * 1.35 : 2;
  for (let e = 0; e < episodes; e++) {
    const cs = mlCandidates(g), phi = cs.map(mlFeatures), p = mlSoftmax(phi.map((f) => f.reduce((s, x, i) => s + x * state.w[i], 0)));
    let u = g.uniform(), a = 0; while (a < 3 && u > p[a]) { u -= p[a]; a++; }
    const c = cs[a], accepted = g.uniform() < c.accept, pickup = accepted ? c.eta : c.eta + 1.5 + g.range(2, 5);
    const cancel = pickup > 8 && g.uniform() < 0.45, shortage = c.surge * (c.last ? 1 : 0) * g.range(6, 14);
    const reward = -pickup - 10 * (cancel ? 1 : 0) - shortage;
    const mean = [0, 1, 2, 3].map((k) => p.reduce((s, pi, i) => s + pi * phi[i][k], 0));
    for (let k = 0; k < 4; k++) state.w[k] += lr * (reward - state.base) * (phi[a][k] - mean[k]);
    state.base += 0.01 * (reward - state.base);
    state.episodes++; state.lastReward = reward;
    if (state.episodes >= next || e === episodes - 1) { state.curve.push([state.episodes, state.evalPolicy(state.w, false)]); next = Math.max(next + 1, state.episodes * 1.35); }
  }
}

function mlRl() {
  if (!ml.rl) ml.rl = mlRlNew();
  const S = ml.rl;
  const pool = ML_POOL.map(([name, zone, eta, accept, surge, last]) => ({ name, zone, eta, accept, surge, last }));
  const pNow = mlSoftmax(pool.map((c) => mlScore(c, S.w))), pApp = mlSoftmax(pool.map((c) => mlScore(c, ML_APPROVED)));
  const greedy = S.evalPolicy(S.w, true);
  return `<div class="sec-intro"><p>The ATLAS Go app dispatches rides with a <strong>policy</strong> learned by <strong>REINFORCE</strong> (policy gradient) and times couriers with a table learned by <strong>Q-learning</strong>. Both were trained on simulated rides and kitchens. In the app, the <em>Learning lab</em> retrains a dispatch policy from zero on the phone — the same code runs here.</p></div>
    ${secSection("POLICY", "Ride dispatch: softmax over four drivers", `${secCode(`features φ(driver) = [ −ETA/5,  P(accept),  −surge × last-free-driver,  −surge ]
policy     π(driver) = exp(w·φ) / Σ exp(w·φ')
reward     r = −pickup minutes − 10 × cancelled − shortage (pulling the last driver from a zone about to surge)
update     w ← w + η (r − b) (φ(chosen) − E_π[φ]),   b ← b + 0.01 (r − b)     η = 0.004`)}`)}
    ${secSection("LIVE", "Train the policy in your browser (LearningLab.train)", `<div class="sec-actions">${mlButton("rl-100", "Train 100 rides", { iconName: "play" })}${mlButton("rl-1000", "Train 1,000", { iconName: "play" })}${mlButton("rl-10000", "Train 10,000", { primary: true, iconName: "play" })}${mlButton("rl-reset", "Reset to w = 0", { iconName: "reset" })}</div>
      ${mlChart([{ points: S.curve, cls: "s3" }], { logX: S.curve.length > 2, xLabel: "training rides (episodes)", yLabel: "expected minutes per ride", hlines: [{ y: S.nearest, label: `nearest driver ${S.nearest.toFixed(2)}`, cls: "bad" }, { y: S.approved, label: `approved v1.4 ${S.approved.toFixed(2)}`, cls: "good" }] })}
      ${secTable(["Policy", "Episodes", "Weights w (ETA, accept, last-driver, surge)", "Expected minutes (300 test rides)"], [
        ["Your candidate (greedy)", S.episodes.toLocaleString(), `<code>${S.w.map((x) => x.toFixed(2)).join(", ")}</code>`, greedy.toFixed(2)],
        ["Approved policy v1.4 (bundled in the app)", "30,000", `<code>${ML_APPROVED.join(", ")}</code>`, S.approved.toFixed(2)],
        ["Nearest driver rule", "—", "—", S.nearest.toFixed(2)],
      ])}
      <p class="sec-label">Pickup at the Mardyke: who gets the ride?</p>
      ${secTable(["Driver", "ETA", "P(accept)", "Surge in zone", "Last free?", "π (your policy)", "π (approved)"], pool.map((c, i) => [c.name, c.eta + " min", c.accept.toFixed(2), c.surge.toFixed(2), c.last ? "yes" : "no", (pNow[i] * 100).toFixed(0) + " %", (pApp[i] * 100).toFixed(0) + " %"]))}
      <p class="sec-note">${icon("dice", 14)} Ava is nearest, but she is the last free driver in a zone about to surge; the approved policy prefers Morgan. Candidates trained here are never used to dispatch: activation requires offline approval, as in the starter's <code>rl.approve</code>.</p>`)}
    ${secSection("Q-LEARNING", "Courier timing (training/rl_sim.py → train_food)", `<p class="sec-text">State: kitchen slack = preparation estimate − courier travel time. Action: minutes to wait before sending the courier. Reward −0.6·courier idle − 1.2·food waiting − 0.15·total time; ε-greedy exploration decaying to 0.03 over 30 000 orders. The learned table, used by <code>courier_plan</code> in the app:</p>
      <div class="ml-qtable">${Object.entries(ML_COURIER).sort((a, b) => a[0] - b[0]).map(([s, d]) => `<span><b style="height:${4 + d * 4}px"></b><small>${d}</small><code>${s}</code></span>`).join("")}</div>
      <p class="sec-note">${icon("activity", 14)} x: slack (min) · bar: learned wait (min). The policy learned "wait about one minute less than the slack": the courier arrives just before the food, rather than waiting at the counter or letting the food cool.</p>`)}
    ${secSection("MORE", "Other learners in the app and starter", secTable(["Learner", "Method", "Where"], [
      ["Driver supply", "Tabular agent; the log records uncensored demand, so every action is updated in hindsight", "training/city_sim.py → run_rl"],
      ["Acceptance (app)", "Beta(9, 1) prior + Bernoulli updates: (accepted + 9)/(offered + 10)", "intelligence.acceptance"],
      ["Acceptance (starter)", "Logistic regression on distance and speed; Brier score", "starter/ml/discrete.py"],
      ["Starter dispatch policy", "Contextual bandit: incremental action values per demand bucket; approve() needs ≥ 8 held-out rides per cell and no loss to baseline", "starter/ml/rl.py"],
      ["Forecast-aware supply agent (1.4)", "State = calendar + LSTM forecast level; −18 % cost vs the calendar-only agent on the held-out half-year", "atlas_go/loop.py → Loop.choose (LSTM + RL loop tab)"],
      ["Agent 1 · rehearsed dispatch (1.3)", "Plays policy v1.4's top three drivers 200 times in the twin; sends the lowest total wait", "atlas_go/twin.py → agent1 (Digital twin tab)"],
      ["Actor-critic (lab)", "A learned critic V(s) replaces the running average b", "ml22_actor_critic.py (Actor & critic tab)"],
      ["MAPPO (lab)", "Dispatch and pricing actors with one shared critic", "ml23_mappo_shared_critic.py (Two agents, one critic tab)"],
    ]))}`;
}

// ================================================================== ATLAS Go 1.3: digital twin (Layer 2) — replica of atlas_go/twin.py
const ML_TWIN = { rollouts: 200, retest: 500, cap: 2.0, step: 0.5, budget: 250, topK: 3, car30: 2.2, hourly: 260, share: 0.4 };

function mlPoisson(g, lam) {
  if (lam <= 0) return 0;
  const limit = Math.exp(-lam);
  let k = 0, p = 1;
  for (;;) { p *= g.uniform(); if (p <= limit) return k; k++; }
}

// twin.rehearse: average total rider waiting over the next 30 minutes if this driver is sent.
function mlRehearse(c, ratio, g, rollouts = ML_TWIN.rollouts) {
  let total = 0;
  for (let i = 0; i < rollouts; i++) {
    const accepted = g.uniform() < c.accept;
    let wait = accepted ? c.eta : c.eta + 1.5 + g.range(2, 5);
    if (wait > 8 && g.uniform() < 0.45) wait += 10;
    const arrivals = mlPoisson(g, c.surge * 5 * ratio);
    if (c.last) { for (let k = 0; k < arrivals; k++) wait += g.range(6, 14); } else wait += arrivals * c.surge * 0.6;
    total += wait;
  }
  return total / rollouts;
}

const mlTwinPool = () => ML_POOL.map(([name, zone, eta, accept, surge, last]) => ({ name, zone, eta, accept, surge, last }));

// twin.agent1: Layer 1's ranking (policy v1.4, untouched), its top three, rehearsed; lowest total wait wins.
function mlAgent1(ratio, rollouts, seed) {
  const t0 = performance.now();
  const pool = mlTwinPool(), p = mlSoftmax(pool.map((c) => mlScore(c, ML_APPROVED)));
  const ranked = pool.map((c, i) => ({ c, p: p[i] })).sort((a, b) => b.p - a.p);
  const top = ranked.slice(0, ML_TWIN.topK).map((x) => x.c), g = mlRng(seed);
  const waits = top.map((c) => mlRehearse(c, ratio, g, rollouts));
  let best = 0;
  waits.forEach((w, i) => { if (w < waits[best]) best = i; });
  return { ranked, top, waits, choice: top[best], layer1: top[0], elapsed: performance.now() - t0 };
}

// How often does a decision with n rollouts agree with a 5,000-rollout reference?
function mlTwinStability(ratio) {
  const ref = mlAgent1(ratio, 5000, 999).choice.name;
  return [5, 20, 50, 200, 1000].map((n) => {
    let agree = 0;
    for (let s = 1; s <= 30; s++) agree += mlAgent1(ratio, n, 100 + s).choice.name === ref;
    return [n, agree / 30];
  }).concat([["ref", ref]]);
}

// twin.agent2: three plans for one area, scored by wait + 1.5 × price jump + empty km.
const mlSurgeOnly = (r) => Math.round(Math.min(ML_TWIN.cap, Math.max(1, 1 + 0.4 * (r - 1))) * 10) / 10;
const mlSmallSurge = (r) => Math.round(Math.min(ML_TWIN.cap, Math.max(1, 1 + 0.2 * (r - 1))) * 10) / 10;
function mlAreaWait(demand, free, m) {
  const load = (demand * m ** -0.7) / Math.max(0.5, free * ML_TWIN.car30);
  return 3 + 6 * Math.max(0, load - 0.55) ** 1.4;
}
function mlAgent2(ratio, free, movable = 2) {
  const demand = (ML_TWIN.hourly * ratio * ML_TWIN.share * 30) / 60 / 12; // twin.foresee, City Centre
  const plans = [["Keep prices, no moves", 1, 0], ["Surge only", mlSurgeOnly(ratio), 0], ["Small surge + move idle cars", mlSmallSurge(ratio), movable]]
    .map(([name, m, moved]) => { const wait = mlAreaWait(demand, free + moved, m); return { name, m, moved, wait, score: wait + 1.5 * (m - 1) + 0.1 * moved }; });
  let best = plans.reduce((a, b) => (b.score < a.score ? b : a));
  if (plans[0].score - best.score < 0.3) best = plans[0];
  return { demand, pressure: demand / (free * ML_TWIN.car30), plans, best, expected: mlSurgeOnly(ratio) };
}

// Agent 3 · Guardian: twin.check_dispatch and twin.check_price.
function mlCheckDispatch(d) {
  if (d.elapsed > ML_TWIN.budget) return [false, `no answer within ${ML_TWIN.budget} ms`];
  if (!d.top.includes(d.choice)) return [false, "driver is not in Layer 1's top three"];
  if ((d.declined || []).includes(d.choice.name)) return [false, "driver already declined this ride"];
  if ((d.offline || []).includes(d.choice.name)) return [false, "driver is no longer online"];
  if (d.choice.eta > d.layer1.eta + 8) return [false, `pickup ${d.choice.eta} min is far beyond Layer 1's ${d.layer1.eta} min`];
  return [true, "within limits"];
}
function mlCheckPrice(m, expected, elapsed = 0) {
  if (typeof m !== "number" || Number.isNaN(m)) return [false, "no valid price"];
  if (elapsed > ML_TWIN.budget) return [false, `no answer within ${ML_TWIN.budget} ms`];
  if (m < 1) return [false, "below the base fare"];
  if (m > ML_TWIN.cap) return [false, `×${m.toFixed(1)} is above the ×${ML_TWIN.cap.toFixed(1)} cap`];
  if (m > expected + ML_TWIN.step + 1e-9) return [false, `×${m.toFixed(1)} jumps more than ${ML_TWIN.step} above the twin's ×${expected.toFixed(1)}`];
  return [true, "within limits"];
}

// twin.retest_pricing: replay Agent 2 on 500 random demand levels before it gets control back.
function mlRetest(seed = 7, rollouts = ML_TWIN.retest) {
  const g = mlRng(seed);
  let passed = 0;
  for (let i = 0; i < rollouts; i++) {
    const r = g.range(0.3, 4.5), m = mlSurgeOnly(r), m2 = mlSurgeOnly(r + 0.25);
    passed += mlCheckPrice(m, mlSurgeOnly(r))[0] && mlCheckPrice(mlSmallSurge(r), mlSurgeOnly(r))[0] && Math.abs(m2 - m) <= ML_TWIN.step + 1e-9 && m >= 1 && m <= ML_TWIN.cap;
  }
  return { passed, rollouts };
}

// Fault drill: 3,000 normal dispatch decisions, 3,000 normal prices and 300 of each of ten fault types.
function mlFaultDrill(seed = 3) {
  const g = mlRng(seed), pool = mlTwinPool(), p = mlSoftmax(pool.map((c) => mlScore(c, ML_APPROVED)));
  const ranked = pool.map((c, i) => ({ c, p: p[i] })).sort((a, b) => b.p - a.p).map((x) => x.c);
  const top = ranked.slice(0, 3), outside = ranked[3];
  const dispatch = (extra = {}) => ({ top, layer1: top[0], choice: top[g.int(3)], elapsed: g.range(0.5, 40), declined: [], offline: [], ...extra });
  const price = () => { const r = g.range(0.3, 4.5), m = g.uniform() < 0.5 ? mlSurgeOnly(r) : mlSmallSurge(r); return [m, mlSurgeOnly(r), g.range(0.2, 30)]; };
  const faults = [
    ["Dispatch: driver outside Layer 1's top 3", () => mlCheckDispatch(dispatch({ choice: outside }))],
    ["Dispatch: driver who already declined", () => { const d = dispatch(); d.declined = [d.choice.name]; return mlCheckDispatch(d); }],
    ["Dispatch: driver gone offline", () => { const d = dispatch(); d.offline = [d.choice.name]; return mlCheckDispatch(d); }],
    ["Dispatch: pickup 9–20 min beyond Layer 1", () => { const far = { ...top[1], eta: top[0].eta + 9 + g.int(12) }, t = [top[0], far, top[2]]; return mlCheckDispatch({ top: t, layer1: t[0], choice: far, elapsed: 5 }); }],
    ["Dispatch: no answer within 250 ms", () => mlCheckDispatch(dispatch({ elapsed: g.range(251, 2000) }))],
    ["Price: not a number", () => mlCheckPrice(NaN, 1.2)],
    ["Price: below the base fare", () => mlCheckPrice(Math.round(g.range(0.3, 0.99) * 100) / 100, 1.0)],
    ["Price: above the ×2.0 cap", () => mlCheckPrice(Math.round(g.range(2.05, 5) * 10) / 10, 2.0)],
    ["Price: jump > 0.5 above the twin", () => { const e = 1 + Math.round(g.range(0, 0.4) * 10) / 10; return mlCheckPrice(Math.min(2, e + 0.6 + g.int(3) / 10), e); }],
    ["Price: no answer within 250 ms", () => { const [m, e] = price(); return mlCheckPrice(m, e, g.range(251, 2000)); }],
  ].map(([name, fn]) => { let caught = 0; for (let i = 0; i < 300; i++) caught += !fn()[0]; return [name, caught]; });
  let falseDispatch = 0, falsePrice = 0;
  for (let i = 0; i < 3000; i++) { falseDispatch += !mlCheckDispatch(dispatch())[0]; const [m, e, ms] = price(); falsePrice += !mlCheckPrice(m, e, ms)[0]; }
  return { faults, caught: faults.reduce((s, f) => s + f[1], 0), injected: faults.length * 300, falseDispatch, falsePrice };
}

function mlTwin() {
  const T = ml.twin, a1 = mlAgent1(T.ratio, T.rollouts, T.seed), a2 = mlAgent2(T.ratio, T.free);
  const [pOk, pWhy] = mlCheckPrice(T.price, a2.expected), [dOk, dWhy] = mlCheckDispatch({ ...a1, declined: [], offline: [] });
  const ratioText = T.ratio < 1.15 ? "ordinary" : T.ratio < 1.6 ? "busy" : T.ratio < 2.4 ? "very busy" : "festival-level";
  return `<div class="sec-intro"><p>ATLAS Go 1.3 adds a <strong>digital twin</strong> of Cork as a separate <strong>Layer 2</strong> on top of the learned models (Layer 1: the LSTM outlook, the REINFORCE dispatch policy v1.4, the courier Q-table), which it only <em>reads</em>. The twin <strong>mirrors</strong> every driver, ride and courier, <strong>foresees</strong> the next 30 minutes from Layer 1's calendar-aware outlook, and lets two agents <strong>rehearse</strong> decisions before anything reaches a phone. A third agent, the <strong>Guardian</strong>, checks every decision and falls back to Layer 1 if one breaks a limit. The functions below are line-by-line ports of <code>atlas_go/twin.py</code>.</p></div>
    ${secSection("LAYERS", "Two layers, one decision (twin.decide_ride)", `<ol class="sec-flow">${[
      ["Layer 1 ranks", "intelligence.rank → policy v1.4 softmax", "Unchanged since 1.2.0 (SHA-256 checked by a unit test)"],
      ["Mirror", "twin.mirror → fidelity 0–1", "Registered drivers with only a home area count 0.6"],
      ["Foresee", "twin.ratio_30, foresee, extra_requests", "Demand ÷ ordinary, per place, next 30 min"],
      ["Agent 1 rehearses", "twin.rehearse × 200 for the top 3", "Rider wait + declines + riders left waiting"],
      ["Agent 2 plans", "twin.agent2 every 5 min per area", "Keep · surge only · small surge + move idle cars"],
      ["Guardian checks", "twin.check_dispatch, check_price", "Block → Layer 1's answer; re-test 500× before handing back"],
    ].map(([t, c, s], i) => `<li><span class="sec-flow-n">${i + 1}</span><strong>${t}</strong><code>${c}</code><small>${s}</small></li>`).join("")}</ol>`)}
    ${secSection("FORESEE", "Set the demand the twin expects for the next 30 minutes", `<div class="sec-row">${mlRange("tw-ratio", "Demand ÷ ordinary (Layer 1's outlook)", 0.5, 3.5, 0.1, T.ratio, T.ratio.toFixed(2))}${mlSelect("tw-rollouts", "Rollouts per driver", [[5, "5"], [20, "20"], [50, "50"], [200, "200 (the app)"], [1000, "1,000"]], T.rollouts)}</div>
      <p class="sec-note">${icon("trend", 14)}<span class="ml-t">×${T.ratio.toFixed(1)} is ${ratioText}. For comparison, Layer 1's outlook gives about ×1.0 on an ordinary Tuesday afternoon, ×2.1 on a Jazz weekend night and ×2.8 at 13:00 on St Patrick's Day.</span></p>`)}
    ${secSection("AGENT 1", "Dispatch: rehearse Layer 1's top three at the Mardyke", `${secTable(["Layer 1 rank", "Driver", "ETA", "P(accept)", "Surge in zone", "Last free car?", "π (policy v1.4)", `Rehearsed total wait (${T.rollouts} runs, 30 min)`], a1.ranked.map((x, i) => {
        const k = a1.top.indexOf(x.c);
        return [String(i + 1), x.c === a1.choice ? `<strong>${x.c.name}</strong> ✓` : x.c.name, x.c.eta + " min", x.c.accept.toFixed(2), x.c.surge.toFixed(2), x.c.last ? "yes" : "no", (x.p * 100).toFixed(0) + " %", k >= 0 ? `${a1.waits[k].toFixed(1)} min` : "not rehearsed (outside top 3)"];
      }))}
      <p class="sec-note">${icon("dice", 14)}<span class="ml-t">${a1.choice === a1.layer1 ? `<strong>${a1.choice.name}</strong> keeps the total wait lowest, as Layer 1 chose.` : `<strong>${a1.choice.name}</strong> keeps the total wait lowest, so Agent 1 sends them instead of Layer 1's first choice <strong>${a1.layer1.name}</strong>.`} Guardian: ${dOk ? "passed" : "blocked"} (${dWhy}); decided in ${a1.elapsed.toFixed(1)} ms of the ${ML_TWIN.budget} ms budget. Raise the demand: a busy zone that loses its last free car makes everyone there wait, which Layer 1's ten-minute view cannot see.</span></p>
      <div class="sec-actions">${mlButton("tw-reseed", "Rehearse again (new random runs)", { iconName: "reset" })}${mlButton("tw-stab", "How many rollouts are enough?", { primary: true, iconName: "play" })}</div>
      ${T.stab ? secTable(["Rollouts per driver", "Same choice as 5,000 rollouts (30 decisions)"], T.stab.filter((r) => r[0] !== "ref").map(([n, a]) => [n.toLocaleString(), `<span class="${a >= 0.95 ? "cr-ok" : "cr-bad"}">${(a * 100).toFixed(0)} %</span>`])) + `<p class="sec-note"><span class="ml-t">Reference choice at ×${T.stab.ratio.toFixed(1)}: <strong>${T.stab.find((r) => r[0] === "ref")[1]}</strong>. Near a tie more rollouts are needed; the app uses 200, which ML 21 found agrees 100 % of the time on Cork's real pools.</span></p>` : ""}`)}
    ${secSection("AGENT 2", "Pricing + moves: three rehearsed plans for City Centre", `<div class="sec-row">${mlRange("tw-free", "Free cars in City Centre", 1, 8, 1, T.free, String(T.free))}</div>
      ${secTable(["Plan", "Price", "Cars moved in", "Rehearsed wait", "Score = wait + 1.5 × (price − 1) + 0.1 × moved"], a2.plans.map((pl) => [pl === a2.best ? `<strong>${pl.name}</strong> ✓` : pl.name, "×" + pl.m.toFixed(1), String(pl.moved), pl.wait.toFixed(1) + " min", pl.score.toFixed(2)]))}
      <p class="sec-note">${icon("sliders", 14)}<span class="ml-t">${a2.demand.toFixed(1)} requests expected in 30 minutes for ${T.free} free cars (pressure ${a2.pressure.toFixed(2)}). A plan must beat "keep prices" by 0.3 to be used, so prices do not flicker. The surge is capped at ×${ML_TWIN.cap.toFixed(1)} and the twin's expected price here is ×${a2.expected.toFixed(1)}.</span></p>`)}
    ${secSection("AGENT 3", "Guardian: try to get a bad price past it", `<div class="sec-row">${mlRange("tw-price", "Price proposed by Agent 2", 0.5, 3.0, 0.1, T.price, "×" + T.price.toFixed(1))}</div>
      <p class="sec-text">${pOk ? `<span class="cr-ok">Allowed</span> — ×${T.price.toFixed(1)} is ${pWhy}.` : `<span class="cr-bad">Blocked</span> — ${pWhy}. The rider sees Layer 1's base fare (×1.0), the block is logged, and Agent 2 stays paused until it passes a ${ML_TWIN.retest}-rollout re-test.`}</p>
      ${secCode(`check_dispatch: answer within 250 ms · driver in Layer 1's top 3 · not declined · still online · pickup ≤ Layer 1's + 8 min
check_price:    a number · answer within 250 ms · ≥ ×1.0 · ≤ ×2.0 · ≤ twin's expected price + 0.5
on any failure: use Layer 1's decision (intelligence.choose, base fare) → log → re-test the agent before handing back`)}
      <div class="sec-actions">${mlButton("tw-drill", "Run the fault drill (3,000 faults, 6,000 normal decisions)", { primary: true, iconName: "play" })}${mlButton("tw-retest", "Re-test Agent 2 (500 rollouts)", { iconName: "play" })}</div>
      ${T.drill ? secTable(["Injected fault", "Injected", "Caught"], T.drill.faults.map(([n, c]) => [n, "300", `<span class="${c === 300 ? "cr-ok" : "cr-bad"}">${c}</span>`]).concat([["<strong>All faults</strong>", T.drill.injected.toLocaleString(), `<strong>${T.drill.caught.toLocaleString()}</strong>`], ["False alarms on normal decisions", "6,000", `${T.drill.falseDispatch + T.drill.falsePrice}`]])) : ""}
      ${T.retest ? `<p class="sec-note">${icon("shield", 14)}<span class="ml-t">Re-test: ${T.retest.passed} of ${T.retest.rollouts} replays passed ${T.retest.passed === T.retest.rollouts ? "— Agent 2 may take control again." : "— Agent 2 stays paused."}</span></p>` : ""}`)}
    ${secSection("MEASURED", "What ML 21 found (ml_lab/machine_learning/ml21_digital_twin.py)", secTable(["Question", "Result"], [
      ["Is the twin's 30-min foresight better than reacting?", "Festival and holiday weeks: error 0.12–0.16 vs 0.43–0.65 for “last hour again” and 0.6–1.0 for “always ordinary”"],
      ["How many rehearsals for a stable choice?", "200 rollouts agree with 5,000 on 100 % of decisions; 5 rollouts on 72–100 %"],
      ["Agent 2 on St Patrick's Day 13:00, City Centre", "Wait 11.4 → 4.2 min with ×1.4 and 2 cars moved (surge only: ×1.7, 6.7 min)"],
      ["Guardian", "3,000 of 3,000 injected faults caught; 0 false alarms on 6,000 normal decisions; re-test 500/500"],
    ]))}`;
}

// ================================================================== actor and critic networks (A2C vs REINFORCE) — port of ml22_actor_critic.py
function mlAcNew() {
  const tg = mlRng(1007), test = Array.from({ length: 300 }, () => mlCandidates(tg));
  const cost = (pick) => test.reduce((s, cs) => s + mlExpectedCost(cs[pick(cs)]), 0) / test.length;
  const argmax = (xs) => xs.indexOf(Math.max(...xs));
  const g = mlRng(31), init = (n, sd) => Array.from({ length: n }, () => g.normal() * sd);
  const S = {
    gR: mlRng(7), gA: mlRng(8), rides: 0,
    rf: { w: [0, 0, 0, 0], base: -10 },
    actor: { W: Array.from({ length: 4 }, () => init(8, 0.5)), b: Array(8).fill(0), v: init(8, 0.1) },
    critic: { W: Array.from({ length: 16 }, () => init(16, 0.3)), b: Array(16).fill(0), v: init(16, 0.1), c: -8 },
    sig: { R: [0, 0, 0], A: [0, 0, 0] }, // Welford: n, mean, M2 (rides after 500)
    nearest: cost((cs) => argmax(cs.map((c) => -c.eta))), approved: cost((cs) => argmax(cs.map((c) => mlScore(c, ML_APPROVED)))),
  };
  S.evalR = () => cost((cs) => argmax(cs.map((c) => mlScore(c, S.rf.w))));
  S.evalA = () => cost((cs) => argmax(mlActorScores(S.actor, cs.map(mlFeatures)).s));
  S.curveR = [[1, S.evalR()]]; S.curveA = [[1, S.evalA()]];
  return S;
}

function mlActorScores(A, phi) {
  const h = phi.map((f) => A.b.map((bj, j) => Math.tanh(bj + f.reduce((s, x, k) => s + x * A.W[k][j], 0))));
  return { h, s: h.map((hi) => hi.reduce((s, x, j) => s + x * A.v[j], 0)) };
}
function mlCriticValue(C, phi) {
  const x = phi.flat(), h = C.b.map((bj, j) => Math.tanh(bj + x.reduce((s, xi, k) => s + xi * C.W[k][j], 0)));
  return { x, h, V: h.reduce((s, hj, j) => s + hj * C.v[j], C.c) };
}
const mlWelford = (w, x) => { w[0]++; const d = x - w[1]; w[1] += d / w[0]; w[2] += d * (x - w[1]); };

function mlRideReward(c, g) { // LearningLab.train's delayed reward
  const accepted = g.uniform() < c.accept, pickup = accepted ? c.eta : c.eta + 1.5 + g.range(2, 5);
  const cancel = pickup > 8 && g.uniform() < 0.45, shortage = c.surge * (c.last ? 1 : 0) * g.range(6, 14);
  return -pickup - 10 * (cancel ? 1 : 0) - shortage;
}
const mlSample = (p, g) => { let u = g.uniform(), a = 0; while (a < p.length - 1 && u > p[a]) { u -= p[a]; a++; } return a; };

function mlAcTrain(S, rides) {
  let next = S.curveA[S.curveA.length - 1][0] * 1.35;
  for (let e = 0; e < rides; e++) {
    // REINFORCE + running-average baseline (as the app)
    { const g = S.gR, cs = mlCandidates(g), phi = cs.map(mlFeatures), p = mlSoftmax(phi.map((f) => f.reduce((s, x, i) => s + x * S.rf.w[i], 0)));
      const a = mlSample(p, g), r = mlRideReward(cs[a], g), mean = [0, 1, 2, 3].map((k) => p.reduce((s, pi, i) => s + pi * phi[i][k], 0));
      for (let k = 0; k < 4; k++) S.rf.w[k] += 0.004 * (r - S.rf.base) * (phi[a][k] - mean[k]);
      if (S.rides >= 500) mlWelford(S.sig.R, r - S.rf.base);
      S.rf.base += 0.01 * (r - S.rf.base); }
    // A2C: actor network + critic network, advantage r − V(s)
    { const g = S.gA, cs = mlCandidates(g), phi = cs.map(mlFeatures), A = S.actor, C = S.critic;
      const { h, s } = mlActorScores(A, phi), p = mlSoftmax(s), a = mlSample(p, g), r = mlRideReward(cs[a], g);
      const cv = mlCriticValue(C, phi), adv = r - cv.V, lr = 0.002;
      if (S.rides >= 500) mlWelford(S.sig.A, adv);
      const gc = cv.h.map((hj, j) => adv * C.v[j] * (1 - hj * hj));       // critic: minimise (r − V)²
      cv.h.forEach((hj, j) => { C.v[j] += lr * adv * hj; });
      C.c += lr * adv;
      cv.x.forEach((xi, k) => { if (xi) for (let j = 0; j < 16; j++) C.W[k][j] += lr * xi * gc[j]; });
      gc.forEach((gj, j) => { C.b[j] += lr * gj; });
      const gs = p.map((pi, i) => (i === a ? 1 : 0) - pi);                 // actor: ∇ log π(a)
      const gv = A.v.map((_, j) => gs.reduce((t, gi, i) => t + gi * h[i][j], 0));
      const gpre = h.map((hi, i) => hi.map((hij, j) => gs[i] * A.v[j] * (1 - hij * hij)));
      gv.forEach((x, j) => { A.v[j] += lr * adv * x; });
      for (let k = 0; k < 4; k++) for (let j = 0; j < 8; j++) A.W[k][j] += lr * adv * phi.reduce((t, f, i) => t + f[k] * gpre[i][j], 0);
      for (let j = 0; j < 8; j++) A.b[j] += lr * adv * gpre.reduce((t, gi) => t + gi[j], 0); }
    S.rides++;
    if (S.rides >= next || e === rides - 1) { S.curveR.push([S.rides, S.evalR()]); S.curveA.push([S.rides, S.evalA()]); next = Math.max(next + 1, S.rides * 1.35); }
  }
}

function mlActorCritic() {
  if (!ml.ac) ml.ac = mlAcNew();
  const S = ml.ac, goal = S.approved + 0.1;
  const first = (curve) => { const hit = curve.find((p) => p[1] <= goal); return hit ? hit[0].toLocaleString() + " rides" : "not yet"; };
  const vr = S.sig.R[0] > 1 ? S.sig.R[2] / (S.sig.R[0] - 1) : null, va = S.sig.A[0] > 1 ? S.sig.A[2] / (S.sig.A[0] - 1) : null;
  const pool = mlTwinPool(), phi = pool.map(mlFeatures), pA = mlSoftmax(mlActorScores(S.actor, phi).s), pApp = mlSoftmax(pool.map((c) => mlScore(c, ML_APPROVED)));
  const situations = [
    ["Three cheap, willing drivers nearby", [{ eta: 1.5, accept: 0.95, surge: 0.05, last: false }, { eta: 2, accept: 0.93, surge: 0.1, last: false }, { eta: 2.5, accept: 0.9, surge: 0.05, last: false }, { eta: 7, accept: 0.6, surge: 0.4, last: false }]],
    ["The Mardyke pool (ML_POOL)", pool],
    ["Only far or reluctant drivers", [{ eta: 8, accept: 0.45, surge: 0.6, last: true }, { eta: 8.5, accept: 0.5, surge: 0.5, last: false }, { eta: 7.5, accept: 0.4, surge: 0.8, last: true }, { eta: 9, accept: 0.55, surge: 0.3, last: false }]],
  ].map(([name, cs]) => { const f = cs.map(mlFeatures), p = mlSoftmax(mlActorScores(S.actor, f).s); return [name, mlCriticValue(S.critic, f).V.toFixed(1), (-cs.reduce((t, c, i) => t + p[i] * mlExpectedCost(c), 0)).toFixed(1)]; });
  return `<div class="sec-intro"><p>REINFORCE (the RL tab) pushes the policy with <strong>r − b</strong>, where b is one running average of all rewards. It cannot tell an easy situation from a hard one, so most of r − b is about the <em>situation</em>, not the <em>choice</em>. An <strong>actor-critic</strong> adds a second network, the <strong>critic</strong> V(s), that reads the whole situation and predicts the reward to expect before any driver is chosen. The <strong>actor</strong> is then pushed by the <strong>advantage</strong> A = r − V(s): “was this choice better than usual <em>for this situation</em>?” Same dispatch problem and reward as the app's LearningLab; port of <code>ml_lab/machine_learning/ml22_actor_critic.py</code>.</p></div>
    ${secSection("NETWORKS", "Actor π(a | s) and critic V(s)", secCode(`actor   per driver i: h_i = tanh(φ_i W + b)   (4 features → 8 hidden),   score_i = h_i · v      π = softmax(scores)
critic  x = [φ_1, φ_2, φ_3, φ_4] (16 inputs) → 16 tanh → V(s)                        "how good is this situation?"
step    choose a ~ π, observe r (pickup, cancellation, shortage elsewhere)
        A = r − V(s)                                  advantage: credit due to the choice alone
        critic  φ ← φ + η (r − V(s)) ∇V(s)            (minimise squared error)
        actor   θ ← θ + η · A · ∇ log π(a | s)        η = 0.002 for both`))}
    ${secSection("LIVE", "Train both learners on the same stream of rides", `<div class="sec-actions">${mlButton("ac-500", "Train 500 rides", { iconName: "play" })}${mlButton("ac-2000", "Train 2,000", { iconName: "play" })}${mlButton("ac-8000", "Train 8,000", { primary: true, iconName: "play" })}${mlButton("ac-reset", "Reset both", { iconName: "reset" })}</div>
      ${ml.busy === "ac" ? `<p class="sec-note"><span class="ml-t">Training…</span></p>` : ""}
      ${mlChart([{ points: S.curveR, cls: "s1" }, { points: S.curveA, cls: "s3" }], { logX: S.curveA.length > 2, xLabel: "training rides", yLabel: "expected minutes per ride", hlines: [{ y: S.nearest, label: `nearest driver ${S.nearest.toFixed(2)}`, cls: "bad" }, { y: S.approved, label: `policy v1.4 ${S.approved.toFixed(2)}`, cls: "good" }] })}
      ${mlLegend([["s1", "REINFORCE + running baseline (linear policy, as the app)"], ["s3", "Actor-critic A2C (actor network + critic network)"]])}
      ${secTable(["Learner", "Rides", "Expected minutes (300 test rides, greedy)", "Within 0.1 min of v1.4 after", "Variance of the learning signal (after ride 500)"], [
        ["REINFORCE: r − b", S.rides.toLocaleString(), S.curveR[S.curveR.length - 1][1].toFixed(2), first(S.curveR), vr == null ? "—" : vr.toFixed(1)],
        ["Actor-critic: r − V(s)", S.rides.toLocaleString(), S.curveA[S.curveA.length - 1][1].toFixed(2), first(S.curveA), va == null ? "—" : va.toFixed(1)],
        ["Policy v1.4 (30,000 rides, bundled in the app)", "30,000", S.approved.toFixed(2), "—", "—"],
        ["Nearest driver rule", "—", S.nearest.toFixed(2), "—", "—"],
      ])}`)}
    ${secSection("CRITIC", "What the critic has learned: how good is each situation?", secTable(["Situation", "Critic V(s)", "Expected reward under the actor"], situations)
      + `<p class="sec-note">${icon("activity", 14)}<span class="ml-t">A well-trained critic ranks the situations like the true expected reward. Subtracting it removes the “easy or hard situation” part of every reward, so what is left — the advantage — is mostly about the driver chosen.</span></p>`
      + secTable(["Driver at the Mardyke", "π (actor)", "π (policy v1.4)"], pool.map((c, i) => [c.name, (pA[i] * 100).toFixed(0) + " %", (pApp[i] * 100).toFixed(0) + " %"]))) }
    ${secSection("MEASURED", "ML 22, three seeds", secTable(["Rides trained", "REINFORCE + baseline", "Actor-critic A2C"], [["1,000", "5.64 min", "5.52 min"], ["2,000", "5.62", "<strong>5.48</strong> (within 0.1 of v1.4)"], ["8,000", "5.47", "<strong>5.34</strong>"]])
      + `<p class="sec-note"><span class="ml-t">Policy v1.4: 5.38 min · nearest driver: 6.42. Learning-signal variance: r − b 23.4, r − V(s) 18.9. In the app, dispatch still uses policy v1.4 plus Agent 1's rehearsal; the critic is the natural next step for <code>LearningLab</code>.</span></p>`)}`;
}

// ================================================================== multi-agent RL: IPPO vs MAPPO (shared critic) — port of ml23_mappo_shared_critic.py
const ML_A1 = ["Centre car", "Mardyke car", "Kent car"], ML_A1_WAIT = [2, 3, 5];
const ML_A2 = ["do nothing", "move Kent → Mardyke", "move Centre → Mardyke", "surge ×1.3 at Mardyke"];
const ML_STEPS = 12;

function mlCity(g) {
  const E = { g };
  E.reset = () => { E.t = 0; E.cars = [1, 2, 3]; E.busy = []; E.surge = 0; };
  E.forecast = (t = E.t) => [t >= 6 ? 2.6 : 0.4, 0.6, 0.5];      // concert at the Mardyke from step 6
  E.obs1 = () => { const c = E.cars; return [1, +(c[1] > 0), +(c[0] > 0), +(c[2] > 0), +(c[0] === 1), +(c[0] >= 2)]; };
  E.obs2 = () => { const c = E.cars, f = E.forecast(E.t + 1); return [1, c[0] / 3, c[1] / 3, c[2] / 3, f[0] / 3, E.t / ML_STEPS]; };
  E.state = () => { const c = E.cars, f = E.forecast(E.t + 1); return [1, c[0] / 3, c[1] / 3, c[2] / 3, f[0] / 3, E.t / ML_STEPS, E.busy.length / 3, E.surge, (c[0] / 3) * (f[0] / 3), +(E.t >= 5 && c[0] === 0)]; };
  E.avail1 = () => [E.cars[1] > 0, E.cars[0] > 0, E.cars[2] > 0];
  E.mask1 = () => { const m = E.avail1(); return m.some(Boolean) ? m : [true, false, false]; };
  E.mask2 = () => [true, E.cars[2] > 0, E.cars[1] > 0, true];
  E.step = (a1, a2) => {
    let cost = 0;
    E.busy.filter((b) => b[0] <= E.t).forEach((b) => { E.cars[b[1]]++; });
    E.busy = E.busy.filter((b) => b[0] > E.t);
    E.surge = 0;
    if (a2 === 1 || a2 === 2) { E.cars[a2 === 1 ? 2 : 1]--; E.cars[0]++; cost += 1.5; } else if (a2 === 3) { E.surge = 1; cost += 1; }
    const av = E.avail1();
    if (av.some(Boolean)) { if (!av[a1]) a1 = av.indexOf(true); const z = [1, 0, 2][a1]; E.cars[z]--; E.busy.push([E.t + 2, z]); cost += ML_A1_WAIT[a1]; } else cost += 6;
    const f = E.forecast(); if (E.surge) f[0] *= 0.7;
    for (const z of [0, 2]) { const demand = mlPoisson(E.g, f[z]), served = Math.min(demand, E.cars[z]); E.cars[z] -= served; for (let k = 0; k < served; k++) E.busy.push([E.t + 2, z]); cost += 2 * served + 6 * (demand - served); }
    E.t++;
    return [-cost, E.t >= ML_STEPS];
  };
  return E;
}

function mlMaskedSoftmax(logits, mask) {
  const top = Math.max(...logits.filter((_, i) => mask[i])), e = logits.map((z, i) => (mask[i] ? Math.exp(z - top) : 0)), s = e.reduce((a, b) => a + b, 0);
  return e.map((x) => x / s);
}
const mlDot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
function mlRidge(X, y, lam = 1e-2) { // solve (XᵀX + λI) w = Xᵀy by Gaussian elimination
  const n = X[0].length, A = Array.from({ length: n }, (_, i) => Array.from({ length: n + 1 }, (_, j) => (j === n ? X.reduce((s, x, r) => s + x[i] * y[r], 0) : X.reduce((s, x) => s + x[i] * x[j], 0) + (i === j ? lam : 0))));
  for (let c = 0; c < n; c++) {
    let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
    [A[c], A[p]] = [A[p], A[c]];
    for (let r = 0; r < n; r++) if (r !== c) { const f = A[r][c] / A[c][c]; for (let k = c; k <= n; k++) A[r][k] -= f * A[c][k]; }
  }
  return A.map((row, i) => row[n] / row[i]);
}
function mlPpo(W, batch, lr = 0.05, clip = 0.2, epochs = 4) {
  for (let ep = 0; ep < epochs; ep++) for (const [o, mask, a, oldP, adv] of batch) {
    const p = mlMaskedSoftmax(W.map((row) => mlDot(row, o)), mask), ratio = p[a] / oldP;
    if ((adv > 0 && ratio > 1 + clip) || (adv < 0 && ratio < 1 - clip)) continue;   // clipped: no gradient
    p.forEach((pi, i) => { const gi = (i === a ? 1 : 0) - pi; if (gi) for (let k = 0; k < o.length; k++) W[i][k] += (lr * adv * ratio * gi * o[k] * 8) / batch.length; });
  }
}

function mlMarlLearner(method, seed) {
  const g = mlRng(seed * 7919), init = (r, c) => Array.from({ length: r }, () => Array.from({ length: c }, () => g.normal() * 0.01));
  return { method, g, env: mlCity(mlRng(seed * 104729)), W1: init(3, 6), W2: init(4, 6), curve: [], spread: [] };
}
function mlMarlEpisode(env, act1, act2, record) {
  env.reset();
  let total = 0, done = false;
  const rows = [];
  while (!done) {
    const o1 = env.obs1(), m1 = env.mask1(), o2 = env.obs2(), m2 = env.mask2(), s = env.state();
    const [a1, p1] = act1(o1, m1), [a2, p2] = act2(o2, m2);
    const [r, d] = env.step(a1, a2);
    total += r; done = d;
    if (record) rows.push({ o1, m1, a1, p1, o2, m2, a2, p2, s, r });
  }
  return [total, rows];
}
function mlMarlIterate(L, batch = 16) {
  const sample = (W) => (o, m) => { const p = mlMaskedSoftmax(W.map((row) => mlDot(row, o)), m), a = mlSample(p, L.g); return [a, p[a]]; };
  const data = [], totals = [];
  for (let b = 0; b < batch; b++) {
    const [total, rows] = mlMarlEpisode(L.env, sample(L.W1), sample(L.W2), true);
    totals.push(total);
    let G = 0;
    for (let k = rows.length - 1; k >= 0; k--) { G += rows[k].r; rows[k].G = G; }
    data.push(...rows);
  }
  L.curve.push([L.curve.length + 1, -totals.reduce((a, b) => a + b, 0) / batch]);
  const Gs = data.map((d) => d.G);
  let adv1, adv2;
  if (L.method === "mappo") { const w = mlRidge(data.map((d) => d.s), Gs); adv1 = adv2 = data.map((d) => d.G - mlDot(w, d.s)); }
  else { const w1 = mlRidge(data.map((d) => d.o1), Gs), w2 = mlRidge(data.map((d) => d.o2), Gs); adv1 = data.map((d) => d.G - mlDot(w1, d.o1)); adv2 = data.map((d) => d.G - mlDot(w2, d.o2)); }
  const sd = (xs) => { const m = xs.reduce((a, b) => a + b, 0) / xs.length; return Math.sqrt(xs.reduce((s, x) => s + (x - m) ** 2, 0) / xs.length) + 1e-8; };
  const s1 = sd(adv1), s2 = sd(adv2);
  L.spread.push([s1, s2]);
  mlPpo(L.W1, data.map((d, i) => [d.o1, d.m1, d.a1, d.p1, adv1[i] / s1]));
  mlPpo(L.W2, data.map((d, i) => [d.o2, d.m2, d.a2, d.p2, adv2[i] / s2]));
}
const mlGreedy = (W) => (o, m) => { const z = W.map((row, i) => (m[i] ? mlDot(row, o) : -1e9)); return [z.indexOf(Math.max(...z)), 1]; };
function mlMarlEvaluate(act1, act2, n = 300) {
  const env = mlCity(mlRng(99));
  let s = 0;
  for (let k = 0; k < n; k++) s += mlMarlEpisode(env, act1, act2, false)[0];
  return -s / n;
}

function mlMarlNew(seed = 1) {
  const g = mlRng(5);
  return {
    seed, ippo: mlMarlLearner("ippo", seed), mappo: mlMarlLearner("mappo", seed), final: null,
    nearest: mlMarlEvaluate((o, m) => [m.indexOf(true), 1], () => [0, 1]),
    random: mlMarlEvaluate((o, m) => { const ok = m.map((x, i) => (x ? i : -1)).filter((i) => i >= 0); return [ok[g.int(ok.length)], 1]; }, (o, m) => { const ok = m.map((x, i) => (x ? i : -1)).filter((i) => i >= 0); return [ok[g.int(ok.length)], 1]; }),
  };
}
function mlMarlTrain(S, iterations) {
  for (let k = 0; k < iterations; k++) { mlMarlIterate(S.ippo); mlMarlIterate(S.mappo); }
  S.final = { ippo: mlMarlEvaluate(mlGreedy(S.ippo.W1), mlGreedy(S.ippo.W2)), mappo: mlMarlEvaluate(mlGreedy(S.mappo.W1), mlGreedy(S.mappo.W2)) };
}

function mlMarl() {
  if (!ml.marl) ml.marl = mlMarlNew(ml.marlSeed || 1);
  const S = ml.marl, it = S.mappo.curve.length;
  const half = (L) => { const xs = L.spread.slice(Math.floor(L.spread.length / 2)); return xs.length ? [0, 1].map((k) => xs.reduce((s, x) => s + x[k], 0) / xs.length) : null; };
  const smooth = (c) => c.map(([x], i) => { const w = c.slice(Math.max(0, i - 4), i + 1); return [x, w.reduce((s, p) => s + p[1], 0) / w.length]; });
  let trace = "";
  if (it) {
    const env = mlCity(mlRng(0)), a1 = mlGreedy(S.mappo.W1), a2 = mlGreedy(S.mappo.W2), rows = [];
    env.reset();
    for (let t = 0; t < ML_STEPS; t++) {
      const x1 = a1(env.obs1(), env.mask1())[0], x2 = a2(env.obs2(), env.mask2())[0];
      rows.push([String(t * 5), env.cars.join(" / "), t >= 6 ? "concert out" : "", ML_A2[x2], env.avail1().some(Boolean) ? "send " + ML_A1[x1] : "no idle car — the rider waits"]);
      env.step(x1, x2);
    }
    trace = secSection("ONE HOUR", "The MAPPO team at work (greedy actors, test hour)", secTable(["Minute", "Idle cars M / C / K", "Mardyke", "Agent 2 · pricing + moves", "Agent 1 · dispatch (City Centre rider)"], rows));
  }
  const sI = half(S.ippo), sM = half(S.mappo);
  return `<div class="sec-intro"><p>In the ATLAS Go 1.3 twin two agents share one goal: <strong>Agent 1</strong> dispatches each ride and <strong>Agent 2</strong> sets prices and moves idle cars. Each one's result also depends on what the other did — the classic difficulty of <strong>multi-agent RL</strong>. The proposal behind 1.3 trains them with <strong>centralised training, decentralised execution</strong>: during training one <strong>shared critic</strong> sees the whole city; at run time each actor acts on its own view only. That is <strong>MAPPO</strong> (multi-agent PPO). <strong>IPPO</strong> gives each agent its own critic on its own view. In the app the agents are rehearsal planners (Digital twin tab); this lab trains learned versions. Port of <code>ml_lab/machine_learning/ml23_mappo_shared_critic.py</code>.</p></div>
    ${secSection("TWIN CITY", "Three zones, one hour, a concert at the Mardyke", secTable(["", "Sees", "Actions", "Reward"], [
      ["Agent 1 · dispatch (actor)", "only its idle cars (6 inputs)", ML_A1.map((a) => "send " + a).join(" · "), "team reward"],
      ["Agent 2 · pricing + moves (actor)", "zone supply, Mardyke forecast, time (6 inputs)", ML_A2.join(" · "), "team reward"],
      ["Shared critic V(s) (MAPPO only)", "everything: cars, busy cars, forecast, time, surge (10 inputs)", "—", "predicts the team's return"],
      ["Team reward", "—", "—", "−(rider waiting + 6 × unmet requests + 1.5 × empty moves + price jumps)"],
    ]) + secCode(`PPO, per actor i:   ρ = π_new(a | o_i) / π_old(a | o_i)
                    loss_i = −E[ min( ρ·A, clip(ρ, 0.8, 1.2)·A ) ]
IPPO   A_i = G_t − V_i(o_i)        each critic sees only its own agent's view
MAPPO  A   = G_t − V(s_global)     one shared, centralised critic (used only in training)`))}
    ${secSection("LIVE", "Train IPPO and MAPPO side by side (16 simulated hours per iteration)", `<div class="sec-row">${mlSelect("marl-seed", "Seed", [[1, "1"], [2, "2"], [3, "3"], [4, "4"]], S.seed)}</div>
      <div class="sec-actions">${mlButton("marl-10", "Train 10 iterations", { iconName: "play" })}${mlButton("marl-60", it >= 60 ? "Train 60 more" : "Train to 60 iterations", { primary: true, iconName: "play" })}${mlButton("marl-reset", "Reset", { iconName: "reset" })}</div>
      ${ml.busy === "marl" ? `<p class="sec-note"><span class="ml-t">Training…</span></p>` : ""}
      ${it ? mlChart([{ points: smooth(S.ippo.curve), cls: "s1" }, { points: smooth(S.mappo.curve), cls: "s3" }], { xLabel: "training iteration", yLabel: "team cost per hour (5-iteration mean)", hlines: [{ y: S.nearest, label: `nearest car ${S.nearest.toFixed(1)}`, cls: "bad" }] }) + mlLegend([["s1", "IPPO (own critics)"], ["s3", "MAPPO (one shared critic)"]]) : `<p class="sec-note"><span class="ml-t">Not trained yet. Baselines on 300 test hours: nearest car, never reposition ${S.nearest.toFixed(1)} · random ${S.random.toFixed(1)}.</span></p>`}
      ${S.final ? secTable(["Policy (300 test hours, greedy)", "Team cost per hour"], [["Nearest car, never reposition", S.nearest.toFixed(1)], ["Random", S.random.toFixed(1)], [`IPPO after ${it} iterations`, S.final.ippo.toFixed(1)], [`MAPPO after ${it} iterations`, S.final.mappo.toFixed(1)]]) : ""}
      ${sI ? secTable(["Spread of the advantages (2nd half of training)", "Agent 1", "Agent 2"], [["IPPO: own critic on own view", sI[0].toFixed(1), sI[1].toFixed(1)], ["MAPPO: shared critic on the whole city", `<strong>${sM[0].toFixed(1)}</strong>`, sM[1].toFixed(1)]]) + `<p class="sec-note">${icon("activity", 14)}<span class="ml-t">Agent 1 cannot see the concert; its own critic cannot tell a quiet early minute from the rush, so its advantages are noisy. The shared critic sees the forecast and the whole fleet and removes that noise.</span></p>` : ""}`)}
    ${trace}
    ${secSection("MEASURED", "ML 23, four seeds, 60 iterations, 500 test hours", secTable(["Policy", "Team cost per hour"], [["Nearest car, never reposition", "140.9"], ["Random", "130.3"], ["IPPO (own critics)", "112.5 ± 3.7"], ["MAPPO (one shared critic)", "113.3 ± 5.0"]])
      + secTable(["Spread of advantages", "Agent 1", "Agent 2"], [["IPPO", "29.9", "18.1"], ["MAPPO", "<strong>17.4</strong>", "17.4"]])
      + `<p class="sec-note"><span class="ml-t">Both learn to move cars to the Mardyke before the concert (about 20 % better than nearest-car). The shared critic cuts the noise in Agent 1's learning signal by about 40 % and MAPPO improves faster in mid-training; in this small twin both end at similar policies. A shared critic is about credit assignment and variance, which matters more as agents and hidden information grow.</span></p>`)}`;
}

// ================================================================== LSTM + RL as one loop (ATLAS Go 1.4, atlas_go/loop.py)
const mlSig = (x) => (x >= 0 ? 1 / (1 + Math.exp(-x)) : Math.exp(x) / (1 + Math.exp(x)));
function mlLstmHidden(X) { // loop.lstm_hidden: gates [input, forget, output, cell] × 16
  const L = ML_LSTM, nh = L.NH;
  let h = Array(nh).fill(0), c = Array(nh).fill(0);
  for (const x of X) {
    const g = L.B.slice(), z = x.concat(h);
    z.forEach((zi, i) => { if (zi) { const row = L.W[i]; for (let j = 0; j < g.length; j++) g[j] += zi * row[j]; } });
    c = c.map((cj, j) => mlSig(g[nh + j]) * cj + mlSig(g[j]) * Math.tanh(g[3 * nh + j]));
    h = c.map((cj, j) => mlSig(g[2 * nh + j]) * Math.tanh(cj));
  }
  return h;
}
const mlLstmHead = (h, V = ML_LSTM.V, C = ML_LSTM.C) => C.map((ck, k) => ck + h.reduce((s, hj, j) => s + hj * V[j][k], 0));
const ML_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
function mlLoopTime(k) {
  const t = new Date(Date.parse(ML_LOOP.start + "Z") + k * 3600e3);
  return `${ML_DAYS[(t.getUTCDay() + 6) % 7]} ${t.getUTCDate()} Oct ${String(t.getUTCHours()).padStart(2, "0")}:00`;
}

function mlLoopWhatIf(tagName, shock) {
  const X = ML_LSTM.REF_X.map((r) => r.slice()), n = X.length, tags = ML_LSTM.TAGS.slice(1);
  for (let r = n - 3; r < n; r++) {
    X[r][0] *= shock; X[r][1] *= shock;                                   // served and unserved ÷ ordinary
    if (tagName !== "none") for (let k = 0; k < tags.length; k++) X[r][24 + k] = tags[k] === tagName ? 1 : 0;  // event tag 3 hours ahead
  }
  return mlLstmHead(mlLstmHidden(X)).map((y) => Math.max(0.05, y));
}

function mlLoop() {
  const T = ml.loop, rows = ML_LOOP.rows, k = T.hour, row = rows[k];
  if (!T.parity) { const t0 = performance.now(), y = mlLstmHead(mlLstmHidden(ML_LSTM.REF_X)); T.parity = { y, ms: performance.now() - t0, err: Math.max(...y.map((v, i) => Math.abs(v - ML_LSTM.REF_Y[i]))) }; }
  const whatIf = mlLoopWhatIf(T.tag, T.shock), base = T.parity.y;
  const sum = (i, upto) => rows.slice(0, upto + 1).reduce((s, r) => s + r[i], 0);
  const cumLoop = sum(4, k), cumCal = sum(5, k), cumNone = sum(7, k);
  const actual = Array.from({ length: 6 }, (_, j) => rows[k + j] ? rows[k + j][0] / rows[k + j][1] : null);
  const nightIdx = Math.floor(k / 24), nights = ML_LOOP.updates.slice(0, nightIdx);
  const lv = ["< 1.05", "1.05–1.15", "1.15–1.3", "1.3–1.5", "1.5–1.8", "1.8–2.2", "2.2–3.0", "≥ 3.0"];
  return `<div class="sec-intro"><p>Until 1.3 the LSTM and the RL agents met only offline: the agent's experience log trained the LSTM in the simulation, and the phone used fixed tables. <strong>ATLAS Go 1.4 closes the loop on the phone</strong>: every city hour the LSTM forecasts demand, the RL supply agent acts on that forecast, the outcome is recorded, and every night both models are retrained — and kept only if they beat the current ones on held-out recent data (<strong>champion / challenger</strong>). <code>atlas_go/loop.py</code>, pure Python, no numpy.</p></div>
    ${secSection("LOOP", "Forecast → act → record → update → validate", `<ol class="sec-flow">${[
      ["Forecast", "Loop.forecast → lstm_hidden, head", "24 h in (5 measured + 30 calendar inputs) → 16 hidden → next 1–6 h ÷ ordinary"],
      ["Act", "Loop.choose(key)", "State = calendar context + LSTM level (8 buckets); action = extra drivers 0–150 %"],
      ["Record", "Loop._record → loop.json", "Served, unserved, idle, forecast, hidden state; 14 days kept"],
      ["Learn online", "Loop.step", "Challenger Q-table: hindsight update of every action from the logged demand"],
      ["Update nightly", "Loop.daily_update", "SGD on the LSTM's output layer (surge hours × 4); challenger agent"],
      ["Validate", "champion vs challenger", "LSTM: error on the last 24 h must fall ≥ 1 %; agent: replay of the last 7 days must not cost more"],
    ].map(([t, c, s], i) => `<li><span class="sec-flow-n">${i + 1}</span><strong>${t}</strong><code>${c}</code><small>${s}</small></li>`).join("")}</ol>`)}
    ${secSection("LSTM", "Run ATLAS Go's LSTM in your browser", `<p class="sec-text">The same weights as the phone (<code>lstm_weights.py</code>, ${ML_LSTM.version}: ${ML_LSTM.W.length} × ${ML_LSTM.W[0].length} gate weights, ${ML_LSTM.NH} hidden units, ${ML_LSTM.HZ} outputs) run on the reference window the app's self-test uses.</p>
      ${secTable(["Hours ahead", ...[1, 2, 3, 4, 5, 6].map(String)], [["Python (REF_Y)", ...ML_LSTM.REF_Y.map((v) => "×" + v.toFixed(3))], ["Your browser", ...base.map((v) => "×" + v.toFixed(3))]])}
      <p class="sec-note">${icon("brain", 14)}<span class="ml-t">Largest difference ${T.parity.err.toExponential(1)} — ${T.parity.err < 1e-4 ? '<span class="cr-ok">same model</span>' : '<span class="cr-bad">mismatch</span>'}; forward pass ${T.parity.ms.toFixed(1)} ms. Held out on July–December 2026 the next-hour error is ${(ML_LSTM.METRICS.h1.mape * 100).toFixed(1)} % (surge recall ${ML_LSTM.METRICS.h1.surge_recall.toFixed(2)}, precision ${ML_LSTM.METRICS.h1.surge_precision.toFixed(2)}).</span></p>
      <div class="sec-row">${mlSelect("lp-tag", "What if the next 3 hours are…", [["none", `as in the reference window (${(() => { const r = ML_LSTM.REF_X[ML_LSTM.REF_X.length - 1], k = ML_LSTM.TAGS.slice(1).findIndex((_, j) => r[24 + j] === 1); return k < 0 ? "ordinary" : ML_LSTM.TAGS[k + 1]; })()})`], ...ML_LSTM.TAGS.slice(1).map((t) => [t, t])], T.tag)}${mlRange("lp-shock", "Last 3 hours' demand × ", 0.5, 2.0, 0.1, T.shock, "×" + T.shock.toFixed(1))}</div>
      ${mlChart([{ points: base.map((v, i) => [i + 1, v]), cls: "s0" }, { points: whatIf.map((v, i) => [i + 1, v]), cls: "s3" }], { xLabel: "hours ahead", yLabel: "demand ÷ ordinary", height: 150 })}${mlLegend([["s0", "reference window"], ["s3", "your what-if"]])}
      <p class="sec-note">${icon("trend", 14)}<span class="ml-t">The event tag changes only the calendar inputs; the demand shock changes only what was measured. The LSTM uses both — and the agent's level for the coming hour would be ${lv[ML_LSTM.BUCKETS.filter((b) => whatIf[0] >= b).length]}.</span></p>`)}
    ${secSection("REPLAY", `${ML_LOOP.period}: the loop's own log, hour by hour`, `<div class="sec-row">${mlRange("lp-hour", "City hour", 0, rows.length - 1, 1, k, mlLoopTime(k))}</div>
      <div class="sec-actions">${mlButton("lp-back", "◀ 6 h")}${mlButton("lp-fwd", "6 h ▶")}${mlButton("lp-night", "Next night's update ▶", { primary: true })}</div>
      ${mlChart([{ points: rows.map((r, i) => [i, Math.min(5, r[0] / r[1])]), cls: "s0" }, { points: rows.map((r, i) => [i, r[2][0]]), cls: "s3" }], { xLabel: "hours since Mon 19 Oct 00:00", yLabel: "demand ÷ ordinary", height: 160, vline: k })}${mlLegend([["s0", "actual"], ["s3", "LSTM, 1 hour ahead"]])}
      ${mlChart([{ points: rows.map((r, i) => [i, r[3] * 100]), cls: "s3" }, { points: rows.map((r, i) => [i, r[6] * 100]), cls: "s1" }], { xLabel: "hours since Mon 19 Oct 00:00", yLabel: "extra drivers %", height: 130, vline: k })}${mlLegend([["s3", "LSTM + RL agent"], ["s1", "1.2 calendar agent"]])}
      ${secTable(["Hour", "Tag", "Forecast level", "Agent's boost", "Calendar's boost", "Cost: loop / calendar / none"], [[mlLoopTime(k), row[9], lv[row[8]], `+${(row[3] * 100).toFixed(0)} %`, `+${(row[6] * 100).toFixed(0)} %`, `${row[4].toFixed(1)} / ${row[5].toFixed(1)} / ${row[7].toFixed(1)}`]])}
      ${secTable(["Hours ahead", ...[1, 2, 3, 4, 5, 6].map(String)], [["LSTM forecast", ...row[2].map((v) => "×" + v.toFixed(2))], ["What happened", ...actual.map((v) => (v == null ? "—" : "×" + v.toFixed(2)))]])}
      ${secTable(["Cost so far (unserved + 0.25 × idle extra drivers)", "No extra drivers", "1.2 calendar agent", "LSTM + RL loop"], [[`${k + 1} hours`, cumNone.toFixed(0), cumCal.toFixed(0), `<strong>${cumLoop.toFixed(0)}</strong> (${((cumLoop / cumCal - 1) * 100).toFixed(1)} % vs calendar)`]])}
      ${nights.length ? secTable(["Night", "LSTM challenger (error on last 24 h)", "Agent challenger (replay of last 7 days)"], nights.map((u) => [mlLoopTime(Math.round((Date.parse(u.t + "Z") - Date.parse(ML_LOOP.start + "Z")) / 3600e3)).replace(" 23:00", ""),
        u.lstm ? `${u.lstm.accepted ? '<span class="cr-ok">kept</span>' : '<span class="cr-bad">rejected</span>'} ${u.lstm.before.toFixed(3)} → ${u.lstm.after.toFixed(3)} (${u.lstm.samples} samples)` : "not enough samples yet",
        u.agent ? `${u.agent.improved ? '<span class="cr-ok">new version</span>' : u.agent.accepted ? "kept (no change)" : '<span class="cr-bad">rejected</span>'} ${u.agent.champion.toFixed(0)} → ${u.agent.challenger.toFixed(0)}` : "—"])) + `<p class="sec-note">${icon("shield", 14)}<span class="ml-t">An LSTM challenger must cut the held-out error by at least 1 %; a smaller gain (as on Fri 23 Oct) is rejected as noise. The agent improved during the Jazz nights, when the logged demand showed that more extra drivers would have paid off.</span></p>` : `<p class="sec-note"><span class="ml-t">Move to the first night (23:00) to see the first validation.</span></p>`}`)}
    ${secSection("MEASURED", "What ML 24 found (ml_lab/machine_learning/ml24_lstm_rl_loop.py)", secTable(["Experiment", "Result"], [
      ["Four periods: Jazz, St Patrick's, Christmas, February", "loop 11,758 · calendar agent 13,137 (−10.5 %) · no boost 24,468; the calendar table wins around St Patrick's Day and Christmas"],
      ["Eight weeks, cost of the last two, learning on vs frozen", "−15.7 % (Jan–Feb 2027) · −1.5 % (May–Jun) · −12.1 % (Sep–Oct)"],
      ["Forecast error by horizon (28 days)", "13.4 · 12.2 · 11.7 · 12.3 · 13.2 · 14.3 % for 1–6 hours"],
      ["A deliberately bad challenger (always +150 %)", "replay cost 13,160 vs 2,177 → rejected, champion kept"],
    ]))}`;
}

// ================================================================== tuning & evaluation
const ML_ABLATION = [["ATLAS (full)", 90.0, 0.12, 1.30, 7.6], ["BIP → fixed thresholds", 121.1, 0.23, 1.49, 15.0], ["No hybrid mode", 127.0, 0.25, 1.34, 13.0], ["No hysteresis", 105.4, 0.30, 1.23, 18.2], ["No LSTM forecast", 92.6, 0.13, 1.29, 6.9], ["No anomaly detector", 89.2, 0.11, 1.30, 7.1]];

function mlEvaluation() {
  const max = 130;
  return `<div class="sec-intro"><p>An optimiser is only as convincing as its evaluation. ATLAS tunes every policy — its own and the baselines — on <strong>validation</strong> runs, then compares them on separate <strong>test</strong> runs with paired statistical tests.</p></div>
    ${secSection("TUNING", "Grid search on validation seeds 101–110 (run_cluster.tune)", secTable(["Policy", "Grid", "Chosen"], [
      ["ATLAS", "switch_pen ∈ {0.02, 0.05, 0.1} × ρ_max ∈ {0.75, 0.85} × HPA target ∈ {0.6, 0.7}", "0.02 · 0.85 · 0.7"],
      ["Microservices, HANSEL-like", "HPA target ∈ {0.5, 0.6, 0.7, 0.8} × scale-down window ∈ {120, 300 s}", "0.5 · 120 s"],
      ["PHYBRID-like / XSCALE-like", "same grid", "0.6 · 120 s / 0.6 · 300 s"],
    ]) + `<p class="sec-note">${icon("scale", 14)} Score = SLA-violation % + failed-request %; ties within 0.02 go to the cheaper setting.</p>`)}
    ${secSection("ABLATION", "What each part is worth (30 test runs, results/cluster.json)", `<div class="cr-bars">${ML_ABLATION.map(([n, p99, sla, cost, tr], i) => `<div class="cr-bar-row ml-abl"><span>${n}</span><div class="cr-bar-track"><i class="cr-bar ${i === 0 ? "pk" : "sg"}" style="width:${((p99 / max) * 82).toFixed(1)}%"></i><b>${p99.toFixed(1)} ms</b></div><div class="cr-bar-track"><small>SLA ${sla.toFixed(2)} % · cost ${cost.toFixed(2)} · ${tr} switches</small></div></div>`).join("")}</div>
      <p class="sec-note">${icon("bars", 14)} p99 latency. Replacing the optimiser with thresholds, or allowing only monolith-or-microservices, costs the most; without hysteresis the system switches 2.4× as often.</p>`)}
    ${secSection("STATISTICS", "Comparing fairly", secTable(["Practice", "Why", "Where"], [
      ["Disjoint train / validation / test", "Tuning on test data inflates results", "Seeds 101–110 vs 1–30; forecaster split by time"],
      ["Paired Wilcoxon signed-rank test", "Each test seed runs every policy on the same traffic; no normality assumption", "run_cluster.compare"],
      ["Rank-biserial correlation", "Effect size, not only a p-value", "run_cluster.compare"],
      ["Holm–Bonferroni correction", "Many comparisons inflate false positives", "run_cluster.holm"],
      ["Block bootstrap CIs", "Neighbouring minutes are correlated; resample whole days", "forecast.block_bootstrap_ci"],
    ]))}`;
}

// ================================================================== gaps
function mlGaps() {
  return `<div class="sec-intro"><p>Observations about ATLAS's optimisation and learning, each a self-contained assignment.</p></div>
  ${secTable(["#", "Observation", "Where", "Exercise"], [
    ["1", "The BIP is evaluated on a six-module e-commerce model, not on the ride-hailing services", "atlas_sim/traffic.py", "Give gateway, trips, dispatch and ML scoring visit ratios and demands; run Sim.bip on them"],
    ["2", "Enumeration is exponential", "Sim.bip", "Swap in lp_round for n = 20; measure decision time and optimality gap"],
    ["3", "Objective weights α = β = γ = 1 are fixed", "Params", "Sweep them and draw the latency–cost Pareto front"],
    ["4", "Flash-sale forecast error is 15× the normal error", "results/forecast.json", "Train for an upper quantile (pinball loss) and plan on it"],
    ["5", "REINFORCE needs thousands of rides", "LearningLab", "Done as a lab (Actor & critic tab, ML 22): move the critic into LearningLab and compare on the phone"],
    ["6", "All app and starter models use simulated data", "training/, starter/ml/", "What changes with real logs: off-policy evaluation, drift, privacy"],
    ["7", "The starter bandit has two states", "starter/ml/rl.py", "Add zone and hour to the state; keep the approval gate"],
    ["8", "Agents 1 and 2 plan by rehearsal; they do not learn", "twin.agent1, twin.agent2", "Replace them with the MAPPO actors (ML 23), keep the Guardian in front, compare in the twin"],
    ["9", "Only the LSTM's output layer is retrained on the phone", "Loop.daily_update", "Add truncated backpropagation through time and validate as for the head"],
    ["10", "The loop validates on the last 24 h / 7 days only", "loop.HOLDOUT, REPLAY_HOURS", "Longer windows and a significance test before accepting a challenger"],
    ["11", "The twin's foresight uses the calendar outlook, not the live LSTM", "twin.ratio_30", "Feed Loop.now() into foresee and measure Agent 2's plans again"],
  ])}
  ${secSection("LESSON PLAN", "Eleven sessions built on ATLAS", secTable(["Session", "Topic", "Use"], [
    ["1", "Formulating a decision as optimisation", "Coupling BIP tab: move the load"], ["2", "Integer programming and relaxations", "Solvers tab; lab section 4"],
    ["3", "Stability: switching cost and hysteresis", "Deploy a choice, change the load; ablation"], ["4", "Training as optimisation", "Forecasting tab: GD vs Adam"],
    ["5", "Unsupervised anomaly detection", "Isolation Forest tab"], ["6", "Reinforcement learning", "RL tab: train REINFORCE"], ["7", "Honest evaluation", "Tuning & evaluation tab"],
    ["8", "Digital twins and runtime shields", "Digital twin tab: rehearse, break the Guardian; ML 21"], ["9", "Actor and critic networks", "Actor & critic tab: A2C vs REINFORCE; ML 22"],
    ["10", "Multi-agent RL with a shared critic", "Two agents, one critic tab: IPPO vs MAPPO; ML 23"], ["11", "Closing the loop: LSTM + RL with validation", "LSTM + RL loop tab: replay the Jazz weekend; ML 24"],
  ]))}
  <p class="sec-note">Full write-up: <a class="sec-inline-link" href="${ML_GUIDE}">docs/MACHINE_LEARNING_OPTIMISATION.md</a> · lab: <a class="sec-inline-link" href="${ML_LAB}">ml_lab/ml_optimisation_lab.py</a> · <a class="sec-inline-link" href="${ML_MAIN}ml_lab/README.md">44 experiments</a></p>`;
}

// ================================================================== inspector
const mlZip = ML_MAIN + "atlas_sim.zip";
const mlInspect = {
  overview: { summary: "An optimiser decides the architecture every 5 s; learned forecasts and anomaly scores feed it; RL runs dispatch in the app; ATLAS Go 1.3–1.4 adds a digital twin with three agents and a live LSTM → RL loop.", files: [["docs/MACHINE_LEARNING_OPTIMISATION.md", ML_GUIDE], ["ml_lab/ml_optimisation_lab.py", ML_LAB], ["ml_lab/README.md (44 experiments)", ML_MAIN + "ml_lab/README.md"], ["atlas_sim.zip → cluster.py", mlZip]], facts: [["Optimiser", "Binary integer program"], ["Decision", "every 5 s, 64 candidates"], ["Learners", "LSTM · Isolation Forest · REINFORCE · Q-learning"], ["ATLAS Go 1.4", "Twin + 3 agents · live LSTM → RL"], ["Teaching", "A2C · MAPPO"], ["Data", "Synthetic, by design"]], questions: ["Which parts of ATLAS are optimisation and which are learning?", "Why does the optimiser need a forecast at all?"] },
  optimizer: { summary: "Choose c ∈ {0,1}⁶ minimising latency + cost + risk + switching, subject to utilisation, SLA, replicas and availability.", files: [["atlas_sim.zip → cluster.py (Sim.bip, eval_all)", mlZip], ["atlas_sim.zip → traffic.py (VISIT, DEMAND_MS)", mlZip], ["results/cluster.json", ML_MAIN + "results.zip"]], facts: [["Variables", "6 binary"], ["Candidates", "64"], ["Time", "0.27 ms per decision"], ["Tuned", "κ 0.02 · ρmax 0.85"], ["Mode share", "81 % tight · 18 % hybrid"]], questions: ["Why is the all-monolith configuration infeasible at 6000 req/s?", "What does the switching cost prevent, and what does hysteresis add?", "Why does an anomaly push one module out rather than all?"] },
  solvers: { summary: "Enumerate for small n; linearise, relax, round with a risk-aware threshold and repair for large n; branch-and-bound as the exact reference.", files: [["run_bip_timing.py", ML_MAIN + "run_bip_timing.py"], ["run_round2.py", ML_MAIN + "run_round2.py"], ["results/bip_timing.json", ML_MAIN + "results.zip"]], facts: [["n = 500, B&B", "401 ms"], ["n = 500, LP", "6.4 ms"], ["Median gap", "0.23 %"], ["Agreement", "96.4 % of 32 400 states"]], questions: ["Why can rounding an LP solution give an infeasible integer solution?", "Why make the rounding threshold depend on risk?", "When would you trust the LP method without the exact check?"] },
  forecasting: { summary: "LSTM trained with Adam, clipping and early stopping; the optimiser plans for max(load, forecast).", files: [["atlas_sim.zip → forecast.py", mlZip], ["run_forecast.py", ML_MAIN + "run_forecast.py"], ["starter/ml/forecast.py", SEC_STARTER + "ml/forecast.py"], ["android-app/training/city_sim.py", ML_MAIN + "android-app/training/city_sim.py"]], facts: [["Model", "LSTM 2 × 128"], ["Optimiser", "Adam 1e-3, clip 1.0"], ["MAE @5 min", "51.7 req/s"], ["Persistence", "72.2 req/s"]], questions: ["Why stop on validation loss rather than training loss?", "Why does the forecaster struggle during flash sales?", "What does gradient clipping protect an LSTM against?"] },
  anomaly: { summary: "Random isolation trees: short paths mean anomalies; no labels needed.", files: [["run_anomaly.py", ML_MAIN + "run_anomaly.py"], ["atlas_sim.zip → cluster.py (Sim.score, FastIForest)", mlZip], ["starter/ml/discrete.py", SEC_STARTER + "ml/discrete.py"]], facts: [["Trees", "100 (paper), 35 (starter)"], ["Sample", "256"], ["ROC-AUC", "0.9999"], ["Thresholds", "alert 0.7, emergency 0.9"]], questions: ["Why does the forest sub-sample 256 points per tree?", "What does contamination set, and what does it not change?", "Why convert the score into a crash probability for the BIP?"] },
  rl: { summary: "REINFORCE learns which driver to send; Q-learning learns when to send the courier; candidates need approval before use.", files: [["android-app/atlas_go/intelligence.py", ML_MAIN + "android-app/atlas_go/intelligence.py"], ["android-app/training/rl_sim.py", ML_MAIN + "android-app/training/rl_sim.py"], ["android-app/atlas_go/learned.py", ML_MAIN + "android-app/atlas_go/learned.py"], ["starter/ml/rl.py", SEC_STARTER + "ml/rl.py"]], facts: [["Dispatch", "REINFORCE, 4 features"], ["Courier", "Q-learning, 21 × 17 table"], ["v1.4 vs nearest", "5.38 vs 6.42 min"], ["Activation", "Offline approval only"]], questions: ["Why subtract a baseline in REINFORCE?", "Why is the reward for dispatch 'late', and why does that matter?", "Why should a newly trained policy not dispatch real rides immediately?"] },
  twin: { summary: "Layer 2 (ATLAS Go 1.3): mirror the city, foresee 30 minutes, rehearse Layer 1's top drivers and three price plans; the Guardian blocks anything out of bounds and falls back to Layer 1.", files: [["android-app/atlas_go/twin.py", ML_MAIN + "android-app/atlas_go/twin.py"], ["android-app/tests/test_twin.py", ML_MAIN + "android-app/tests/test_twin.py"], ["ml_lab/machine_learning/ml21_digital_twin.py", ML_MAIN + "ml_lab/machine_learning/ml21_digital_twin.py"], ["docs/MACHINE_LEARNING_OPTIMISATION.md §8", ML_GUIDE + "#8-the-digital-twin-mirror-foresee-rehearse-guard"]], facts: [["Rollouts", "200 per driver"], ["Horizon", "30 min"], ["Price cap", "×2.0, step ≤ 0.5"], ["Budget", "250 ms"], ["Fault drill", "3,000/3,000 caught"], ["Layer 1", "read-only, byte-identical"]], questions: ["Why does Agent 1 choose only among Layer 1's top three?", "What can the twin see that a ten-minute dispatch view cannot?", "Why must a blocked agent pass a re-test before it gets control back?", "Why is the Guardian not itself a learned model?"] },
  actorcritic: { summary: "An actor network chooses; a critic network predicts V(s); the actor is trained on the advantage r − V(s) instead of r − b.", files: [["ml_lab/machine_learning/ml22_actor_critic.py", ML_MAIN + "ml_lab/machine_learning/ml22_actor_critic.py"], ["android-app/atlas_go/intelligence.py (LearningLab)", ML_MAIN + "android-app/atlas_go/intelligence.py"], ["docs/MACHINE_LEARNING_OPTIMISATION.md §9", ML_GUIDE + "#9-actor-and-critic-networks"]], facts: [["Actor", "4 → 8 tanh → 1 per driver"], ["Critic", "16 → 16 tanh → 1"], ["To v1.4 + 0.1", "A2C 2,000 · REINFORCE 8,000 rides"], ["Signal variance", "18.9 vs 23.4"]], questions: ["What does the critic know that the running average b does not?", "Why does the critic not change the expected gradient, only its variance?", "What happens if the critic sees only the chosen driver?"] },
  marl: { summary: "Two actors (dispatch, pricing) with one team reward; MAPPO trains them with one shared, centralised critic, IPPO with one critic each.", files: [["ml_lab/machine_learning/ml23_mappo_shared_critic.py", ML_MAIN + "ml_lab/machine_learning/ml23_mappo_shared_critic.py"], ["android-app/atlas_go/twin.py (agent1, agent2)", ML_MAIN + "android-app/atlas_go/twin.py"], ["docs/MACHINE_LEARNING_OPTIMISATION.md §10", ML_GUIDE + "#10-multi-agent-rl-two-agents-one-shared-critic"]], facts: [["Agents", "2 PPO actors"], ["Critic", "shared, sees the whole city"], ["Execution", "decentralised"], ["vs nearest car", "≈ −20 % cost"], ["Agent 1 advantage spread", "17.4 vs 29.9"]], questions: ["Why is a shared reward hard for independent learners?", "Why may the critic see more than the actors, but only during training?", "When would a shared critic change the final policy, not only the speed?"] },
  loop: { summary: "Layer 1 (ATLAS Go 1.4): the LSTM forecasts every hour, the supply agent acts on it, outcomes are logged, and both models are retrained nightly and kept only if validated.", files: [["android-app/atlas_go/loop.py", ML_MAIN + "android-app/atlas_go/loop.py"], ["android-app/atlas_go/lstm_weights.py", ML_MAIN + "android-app/atlas_go/lstm_weights.py"], ["android-app/training/export_lstm.py", ML_MAIN + "android-app/training/export_lstm.py"], ["android-app/tests/test_loop.py", ML_MAIN + "android-app/tests/test_loop.py"], ["ml_lab/machine_learning/ml24_lstm_rl_loop.py", ML_MAIN + "ml_lab/machine_learning/ml24_lstm_rl_loop.py"], ["docs/MACHINE_LEARNING_OPTIMISATION.md §11", ML_GUIDE + "#11-lstm--rl-as-one-loop-forecast-act-record-update-validate"]], facts: [["LSTM", "24 h → 16 → 6 h"], ["Next-hour error", "9.3 %"], ["Agent state", "calendar + LSTM level"], ["Log", "14 days on the phone"], ["vs calendar agent", "−10.5 % cost"], ["8 weeks, learning", "−1.5 to −16 %"]], questions: ["Why validate a challenger on data it was not trained on?", "Why retrain only the output layer on the phone?", "What could go wrong if every challenger were accepted?", "Why can the supply agent learn every action in hindsight?"] },
  evaluation: { summary: "Tune on validation seeds, test on 30 paired runs, correct for multiple comparisons.", files: [["run_cluster.py", ML_MAIN + "run_cluster.py"], ["results/cluster.json", ML_MAIN + "results.zip"]], facts: [["Validation", "seeds 101–110"], ["Test", "seeds 1–30"], ["Test", "Wilcoxon + Holm"], ["Effect size", "rank-biserial"]], questions: ["Why tune the baselines as carefully as ATLAS?", "Why a paired test?", "What does Holm's correction protect against?"] },
  gaps: { summary: "Eleven observations, each a self-contained assignment.", files: [["docs/MACHINE_LEARNING_OPTIMISATION.md §13", ML_GUIDE + "#13-known-gaps--exercises-for-students"], ["docs/MACHINE_LEARNING_OPTIMISATION.md §14 (lesson plan)", ML_GUIDE + "#14-suggested-lesson-plan"]], facts: [["Exercises", "11"], ["Sessions", "11"]], questions: ["Which gap would you close first before running ATLAS in production?"] },
};

function mlInspector() {
  const t = mlTopicById[ml.topic], info = mlInspect[ml.topic];
  return `<div class="inspector-head"><span>${icon("brain", 16)} ML INSPECTOR</span><span class="status-dot" aria-hidden="true"></span></div>
    <div class="inspector-body" style="--accent:${t.status === "impl" ? "#c2f77a" : "#90bfe8"}"><div class="inspector-identity"><span class="component-icon">${icon(t.icon, 23)}</span><div><p>${t.status ? mlStatus[t.status].label : "Overview"}</p><h2 id="component-title" tabindex="-1">${t.title}</h2></div></div>
    <p class="inspector-summary">${info.summary}</p>
    <dl class="sec-facts">${info.facts.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("")}</dl>
    <div class="connection-group"><h3>Where in the code</h3>${info.files.map(([l, u]) => secLink(l, u)).join("")}</div>
    ${umlInspector(`ml/${ml.topic}`, "ml", mlTopics)}
    <div class="connection-group"><h3>Questions for students</h3><ol class="sec-questions">${info.questions.map((q) => `<li>${q}</li>`).join("")}</ol></div>
    ${t.status === "impl" ? `<p class="inspector-note"><strong>Synthetic training data</strong><span>The app and starter learners were trained on simulations; their numbers illustrate the methods.</span></p>` : ""}</div>`;
}

// ================================================================== view + events
const mlRenderers = { overview: mlOverview, optimizer: mlOptimizer, solvers: mlSolvers, forecasting: mlForecasting, anomaly: mlAnomaly, rl: mlRl, twin: mlTwin, actorcritic: mlActorCritic, marl: mlMarl, loop: mlLoop, evaluation: mlEvaluation, gaps: mlGaps };

function mlView() {
  const t = mlTopicById[ml.topic];
  return viewHeading("MACHINE LEARNING & OPTIMISATION", "How ATLAS optimises and learns", "The paper's coupling optimiser and its solvers, the LSTM forecaster, the Isolation Forest the reinforcement-learning agents, ATLAS Go's digital twin and live LSTM → RL loop, actor-critic and multi-agent RL — traced through the ATLAS code and run live in your browser.", `<a class="panel-badge sec-guide" href="${ML_GUIDE}">Teaching guide ↗</a>`)
    + `<nav class="sec-topics" aria-label="Machine learning and optimisation topics">${mlTopics.map((x) => `<button type="button" data-ml-topic="${x.id}" data-keep="ml-topic-${x.id}" aria-pressed="${x.id === ml.topic}">${icon(x.icon, 15)}${x.title}${x.status ? `<i class="sec-dot ${mlStatus[x.status].tone}" aria-label="${mlStatus[x.status].label}"></i>` : ""}</button>`).join("")}</nav>
    <div class="sec-body"><div class="sec-title-row"><h3>${t.title}</h3>${mlChip(t.status)}${umlChip(ml.topic === "overview" ? "machine-learning-and-optimisation-catalogue" : `uml-ml-${ml.topic}`, "UML catalogue")}</div>${mlRenderers[ml.topic]()}${ml.topic === "overview" ? umlTopicsSection("ml", mlTopics) : umlSection(`ml/${ml.topic}`)}</div>`;
}

function mlOpen(topic) {
  ml.topic = mlTopicById[topic] ? topic : "overview";
  state.view = "ml";
}

function mlSetHash() {
  try { history.replaceState(null, "", "#ml" + (ml.topic === "overview" ? "" : "-" + ml.topic)); } catch (error) { /* file:// */ }
}

function mlRun(busy, task) {
  ml.busy = busy;
  render();
  setTimeout(() => {
    try { task(); } catch (error) { console.error(error); announce("ML lab error: " + error.message); }
    ml.busy = "";
    render();
  }, 20);
}

function mlClick(button) {
  const { mlTopic, mlAction } = button.dataset;
  if (mlTopic) {
    ml.topic = mlTopic;
    state.view = "ml";
    mlSetHash();
    announce("Machine learning topic: " + mlTopicById[mlTopic].title);
    render();
    return true;
  }
  if (!mlAction || ml.busy) return !!mlAction;
  const b = ml.bip;
  if (mlAction === "hybrid") { b.hybrid = !b.hybrid; render(); }
  else if (mlAction === "deploy") { b.now = mlAfterOverrides(mlBipSolve(b.lam, b.a, b.anom, b.now, b.hybrid).choice, b.a, b.anom).c.slice(); announce("Deployed " + b.now.join("")); render(); }
  else if (mlAction === "reset") { Object.assign(b, { lam: 2500, a: 0, anom: 4, hybrid: true, now: [0, 0, 0, 0, 0, 0] }); render(); }
  else if (mlAction.startsWith("enum-")) {
    if (mlAction === "enum-clear") { ml.enum = []; render(); }
    else { const n = Number(mlAction.slice(5)); mlRun("enum", () => { ml.enum = ml.enum.filter((e) => e.n !== n).concat(mlEnumerateTiming(n)).sort((x, y) => x.n - y.n); }); }
  } else if (mlAction === "fc-train") mlRun("fc", () => { ml.fc = { gd: mlTrainForecaster("gd", ml.fcOpts.gd), adam: mlTrainForecaster("adam", ml.fcOpts.adam) }; });
  else if (mlAction === "forest") mlRun("forest", () => { ml.forest = mlForestGrow(ml.forestTrees, ml.forestSubtle); });
  else if (mlAction === "rl-reset") { ml.rl = mlRlNew(); render(); }
  else if (mlAction.startsWith("rl-")) mlRun("rl", () => { mlRlTrain(ml.rl, Number(mlAction.slice(3))); });
  else if (mlAction === "tw-reseed") { ml.twin.seed++; render(); }
  else if (mlAction === "tw-stab") mlRun("tw", () => { ml.twin.stab = mlTwinStability(ml.twin.ratio); ml.twin.stab.ratio = ml.twin.ratio; });
  else if (mlAction === "tw-drill") mlRun("tw", () => { ml.twin.drill = mlFaultDrill(); });
  else if (mlAction === "tw-retest") { ml.twin.retest = mlRetest(); render(); }
  else if (mlAction === "ac-reset") { ml.ac = mlAcNew(); render(); }
  else if (mlAction.startsWith("ac-")) mlRun("ac", () => { mlAcTrain(ml.ac, Number(mlAction.slice(3))); });
  else if (mlAction === "marl-reset") { ml.marl = mlMarlNew(ml.marlSeed); render(); }
  else if (mlAction.startsWith("marl-")) mlRun("marl", () => { mlMarlTrain(ml.marl, Number(mlAction.slice(5))); });
  else if (mlAction === "lp-back" || mlAction === "lp-fwd") { ml.loop.hour = Math.max(0, Math.min(ML_LOOP.rows.length - 1, ml.loop.hour + (mlAction === "lp-fwd" ? 6 : -6))); render(); }
  else if (mlAction === "lp-night") { const h = ml.loop.hour; ml.loop.hour = Math.min(ML_LOOP.rows.length - 1, h % 24 === 23 ? h + 24 : h - (h % 24) + 23); render(); }
  return true;
}

// Sliders: update the label while dragging, re-solve when released (re-rendering mid-drag would end the drag).
document.addEventListener("input", (event) => {
  const name = event.target.dataset?.mlRange;
  if (!name) return;
  const value = Number(event.target.value), out = document.getElementById("ml-out-" + name);
  if (out) out.textContent = name === "lam" ? value.toLocaleString() : name === "tw-free" ? String(value) : name === "tw-price" || name === "lp-shock" ? "×" + value.toFixed(1) : name === "lp-hour" ? mlLoopTime(value) : value.toFixed(2);
});

document.addEventListener("change", (event) => {
  const range = event.target.dataset?.mlRange;
  if (range) {
    if (range === "lam") ml.bip.lam = Number(event.target.value);
    if (range === "a") ml.bip.a = Number(event.target.value);
    if (range === "tw-ratio") { ml.twin.ratio = Number(event.target.value); ml.twin.stab = null; }
    if (range === "tw-free") ml.twin.free = Number(event.target.value);
    if (range === "tw-price") ml.twin.price = Number(event.target.value);
    if (range === "lp-shock") ml.loop.shock = Number(event.target.value);
    if (range === "lp-hour") ml.loop.hour = Number(event.target.value);
    render();
    return;
  }
  const sel = event.target.dataset?.mlSelect;
  if (!sel) return;
  if (sel === "lp-tag") { ml.loop.tag = event.target.value; render(); return; }
  const value = Number(event.target.value);
  if (sel === "tw-rollouts") { ml.twin.rollouts = value; ml.twin.stab = null; }
  if (sel === "marl-seed") { ml.marlSeed = value; ml.marl = mlMarlNew(value); }
  if (sel === "anom") ml.bip.anom = value;
  if (sel === "gd") ml.fcOpts.gd = value;
  if (sel === "adam") ml.fcOpts.adam = value;
  if (sel === "trees") ml.forestTrees = value;
  if (sel === "subtle") ml.forestSubtle = value === 1;
  render();
});
