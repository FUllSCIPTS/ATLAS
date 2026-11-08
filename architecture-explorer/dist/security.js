// ATLAS Architecture Explorer — Security view (information-security teaching layer).
// Loaded before explorer.js. Uses explorer.js globals at call time: state, render, announce, icon, $.
// All cryptography is real and runs in the browser with Web Crypto: PBKDF2, SHA-256, AES-GCM, ECDSA P-256.
// Status tags: "impl" = in the ATLAS code today, "demo" = implemented with demo-grade choices,
// "teach" = teaching extension (standard protocol mapped onto ATLAS components; not in the ATLAS code).

const securityIcons = {
  shield: '<path d="M12 3 5 6v5c0 4.6 3 8.4 7 10 4-1.6 7-5.4 7-10V6Z"/><path d="m9 12 2 2 4-4"/>',
  lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
  key: '<circle cx="8" cy="15" r="4"/><path d="m11 12 9-9m-4 4 3 3m-6 0 2 2"/>',
  ticket: '<path d="M3 8a2 2 0 0 0 0 4v0a2 2 0 0 1 0 4v2h18v-2a2 2 0 0 1 0-4 2 2 0 0 1 0-4V6H3Z"/><path d="M14 6v12" stroke-dasharray="2 2"/>',
  idcard: '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2"/><path d="M6 16c.6-1.4 1.7-2 3-2s2.4.6 3 2m3-6h3m-3 3h3"/>',
  door: '<path d="M14 3H6v18h8M14 3l5 2v14l-5 2Z"/><path d="M11 12h.01"/>',
  bug: '<rect x="8" y="7" width="8" height="12" rx="4"/><path d="M12 7V5m-4 6H4m4 4H4m12-4h4m-4 4h4M9 4l1 2m5-2-1 2"/>',
  check: '<path d="m5 12 4 4 10-10"/>',
  cross: '<path d="m6 6 12 12M18 6 6 18"/>',
  clock: '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/>',
};

const SEC_MAIN = "https://github.com/FUllSCIPTS/ATLAS/blob/main/";
const SEC_STARTER = "https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/";
const SEC_EXPLORER = "https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/";
const SEC_GUIDE = SEC_MAIN + "docs/INFORMATION_SECURITY.md";

const secStatus = {
  impl: { label: "Implemented", tone: "impl", text: "In the ATLAS code today" },
  demo: { label: "Demo-grade", tone: "demo", text: "Implemented with deliberately simple choices" },
  teach: { label: "Teaching extension", tone: "teach", text: "Standard protocol mapped onto ATLAS; not in the ATLAS code" },
};

const secTopics = [
  { id: "overview", title: "Security map", icon: "shield", status: null },
  { id: "passwords", title: "Password storage", icon: "lock", status: "impl" },
  { id: "login", title: "Login & lockout", icon: "door", status: "impl" },
  { id: "identity", title: "Identity & roles", icon: "idcard", status: "impl" },
  { id: "gateway", title: "Gateway auth", icon: "gateway", status: "demo" },
  { id: "sso", title: "Single sign-on", icon: "key", status: "teach" },
  { id: "kerberos", title: "Kerberos live", icon: "ticket", status: "teach" },
  { id: "transport", title: "mTLS & deployment", icon: "cloud", status: "impl" },
  { id: "gaps", title: "Gaps & exercises", icon: "bug", status: null },
];
const secTopicById = Object.fromEntries(secTopics.map((t) => [t.id, t]));

const sec = {
  topic: "overview",
  busy: "",
  fields: { pw: "cork2026", pw2: "cork2026", pwLogin: "", krbPassword: "Drive2026" },
  pw: { records: [], plain: null, verify: null, ms: 0 },
  login: null,
  gateway: { scenario: "ok", step: -1 },
  sso: { scenario: "normal", steps: [], ctx: null },
  krb: { scenario: "normal", steps: [], ctx: null },
};

// ------------------------------------------------------------------ crypto helpers (Web Crypto)
const secEnc = new TextEncoder();
const secDec = new TextDecoder();
const secHex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
const secRand = (n) => crypto.getRandomValues(new Uint8Array(n));
const secShort = (h, n = 24) => (h.length > n ? h.slice(0, n) + "…" : h);
const secB64u = (bytes) => btoa(String.fromCharCode(...new Uint8Array(bytes))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const secFromB64u = (text) => Uint8Array.from(atob(text.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((text.length + 3) % 4)), (c) => c.charCodeAt(0));
const secEsc = (text) => String(text).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const secClock = (ms) => new Date(ms).toISOString().slice(11, 19) + " UTC";

async function secPbkdf2(password, salt, iterations, hash = "SHA-256", bits = 256) {
  const base = await crypto.subtle.importKey("raw", secEnc.encode(password), "PBKDF2", false, ["deriveBits"]);
  return new Uint8Array(await crypto.subtle.deriveBits({ name: "PBKDF2", hash, salt, iterations }, base, bits));
}

async function secSha256(bytes) {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", typeof bytes === "string" ? secEnc.encode(bytes) : bytes));
}

function secEqual(a, b) { // constant-time in spirit: always walks the full length, like hmac.compare_digest
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

async function secSeal(keyBytes, object) { // AES-256-GCM: confidentiality + integrity
  const key = await crypto.subtle.importKey("raw", keyBytes, "AES-GCM", false, ["encrypt"]);
  const iv = secRand(12);
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, secEnc.encode(JSON.stringify(object))));
  const out = new Uint8Array(12 + ct.length);
  out.set(iv); out.set(ct, 12);
  return out;
}

async function secOpen(keyBytes, sealed) {
  const key = await crypto.subtle.importKey("raw", keyBytes, "AES-GCM", false, ["decrypt"]);
  const plain = await crypto.subtle.decrypt({ name: "AES-GCM", iv: sealed.slice(0, 12) }, key, sealed.slice(12));
  return JSON.parse(secDec.decode(plain));
}

async function secFingerprint(bytes) { return secHex(await secSha256(bytes)).slice(0, 12); }

// ------------------------------------------------------------------ shared markup
function secChip(status) {
  if (!status) return "";
  const s = secStatus[status];
  return `<span class="sec-chip ${s.tone}" title="${s.text}">${s.label}</span>`;
}

function secCode(text) { return `<pre class="sec-code"><code>${secEsc(text)}</code></pre>`; }

function secCheck(ok, text, detail = "") {
  return `<li class="sec-check ${ok ? "ok" : "fail"}">${icon(ok ? "check" : "cross", 14)}<span>${text}${detail ? `<small>${detail}</small>` : ""}</span></li>`;
}

function secField(name, label, type = "text", hint = "") {
  return `<label class="sec-field"><span>${label}</span><input data-sec-input="${name}" data-keep="sec-in-${name}" type="${type}" value="${secEsc(sec.fields[name] ?? "")}" autocomplete="off" spellcheck="false" placeholder="${secEsc(hint)}"></label>`;
}

function secButton(action, label, { primary = false, iconName = "", disabled = false } = {}) {
  return `<button type="button" class="sec-btn${primary ? " primary" : ""}" data-sec-action="${action}" data-keep="sec-${action}"${disabled || sec.busy ? " disabled" : ""}>${iconName ? icon(iconName, 15) : ""}${label}</button>`;
}

function secSelect(name, options, value) {
  return `<label class="sec-field compact"><span>Scenario</span><select data-sec-select="${name}" data-keep="sec-sel-${name}">${options.map(([v, l]) => `<option value="${v}"${v === value ? " selected" : ""}>${l}</option>`).join("")}</select></label>`;
}

function secTable(head, rows, cls = "") {
  return `<div class="sec-table-wrap"><table class="sec-table ${cls}"><thead><tr>${head.map((h) => `<th scope="col">${h}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c, i) => (i === 0 ? `<th scope="row">${c}</th>` : `<td>${c}</td>`)).join("")}</tr>`).join("")}</tbody></table></div>`;
}

function secLink(label, url) { return `<a class="sec-file" href="${url}">${icon("file", 14)}<code>${label}</code>${icon("diagonal", 12)}</a>`; }

function secSection(kicker, title, body) {
  return `<section class="sec-section"><p class="section-kicker">${kicker}</p><h3>${title}</h3>${body}</section>`;
}

// ------------------------------------------------------------------ UML catalogue links (data: uml-catalog.js)
const UML_FALLBACK = SEC_STARTER + "docs/UML_BLUEPRINT.md";
const umlData = () => (typeof umlCatalog === "object" ? umlCatalog : null);
const umlHref = (anchor) => (umlData()?.blueprint || UML_FALLBACK) + "#" + anchor;

function umlChip(anchor, label = "UML catalogue") {
  return `<a class="uml-chip" href="${umlHref(anchor)}" title="Open this entry in the UML blueprint catalogue">${icon("layers", 13)}${label}<span aria-hidden="true">↗</span></a>`;
}

// Full table at the end of a topic: every concept → function → source → catalogue entry.
function umlSection(topicKey) {
  const data = umlData();
  const ids = data?.topics?.[topicKey];
  if (!ids) return "";
  const [view, key] = topicKey.split("/");
  const rows = ids.map((id) => {
    const r = data.rows[id];
    return [`${r.concept}<small> ${data.status[r.status]}</small>`, r.symbol ? `<code>${secEsc(r.symbol)}</code>` : "—", `<a class="sec-inline-link" href="${r.source}">${secEsc(r.path.split("/").pop())} L${r.line}</a>`, umlChip(id, "Entry")];
  });
  return secSection("UML CATALOGUE", "Every concept on this page in the UML blueprint", `<p class="sec-text">Each concept links to its function in the <a class="sec-inline-link" href="${umlHref(`uml-${view}-${key}`)}">UML blueprint's ${umlCatalogueName(view)}</a>, alongside the class diagrams and the generated symbol catalogue.</p>` + secTable(["Concept", "Function / symbol", "Source", "UML catalogue"], rows, "uml-table"));
}

// The ML view has its own catalogue section; Security and Cryptography share one.
const umlCatalogueName = (view) => (view === "ml" ? "machine learning and optimisation catalogue" : "security and cryptography catalogue");
const umlCatalogueAnchor = (view) => umlCatalogueName(view).replace(/ /g, "-");

// Overview: one link per topic section of the catalogue.
function umlTopicsSection(view, topics) {
  const data = umlData();
  if (!data) return "";
  const rows = topics.filter((t) => data.topics[`${view}/${t.id}`]).map((t) => [t.title, `${data.topics[`${view}/${t.id}`].length} concepts`, umlChip(`uml-${view}-${t.id}`, "Section")]);
  return secSection("UML CATALOGUE", "Every topic in the UML blueprint", `<p class="sec-text">Each topic below has a section in the <a class="sec-inline-link" href="${umlHref(umlCatalogueAnchor(view))}">${umlCatalogueName(view)}</a> of the UML blueprint, with one entry per function.</p>` + secTable(["Topic", "Entries", "UML catalogue"], rows, "uml-table"));
}

// Compact list for the inspector.
function umlInspector(topicKey, view, topics) {
  const data = umlData();
  if (!data) return "";
  if (topicKey.endsWith("/overview")) {
    return `<div class="connection-group"><h3>In the UML catalogue</h3>${topics.filter((t) => data.topics[`${view}/${t.id}`]).map((t) => `<a class="uml-row" href="${umlHref(`uml-${view}-${t.id}`)}"><span>${t.title}</span><code>${data.topics[`${view}/${t.id}`].length} entries</code>${icon("diagonal", 12)}</a>`).join("")}</div>`;
  }
  const ids = data.topics[topicKey] || [];
  return `<div class="connection-group"><h3>In the UML catalogue</h3>${ids.map((id) => { const r = data.rows[id]; return `<a class="uml-row" href="${umlHref(id)}"><span>${r.concept}</span><code>${secEsc(r.symbol || r.path.split("/").pop())}</code>${icon("diagonal", 12)}</a>`; }).join("")}</div>`;
}

// ------------------------------------------------------------------ topic: overview
const secMap = [
  ["passwords", "lock", "Password storage", "impl", "Salted PBKDF2-HMAC-SHA256, 200 000 iterations; constant-time verify; secrets never shown", "android-app/atlas_go/accounts.py"],
  ["login", "door", "Authentication", "impl", "Email + password; 5 failures → 60 s lockout; one error message for every failure", "android-app/atlas_go/store.py"],
  ["identity", "idcard", "Identity lifecycle", "impl", "Register → sign in → sign out → delete with re-authentication and anonymisation", "store.py · PRIVACY.md"],
  ["identity", "layers", "Role-based access", "impl", "Passenger · driver · food seller; enforced on screens and again on every command", "app.py · store.py"],
  ["gateway", "gateway", "Gateway authentication", "demo", "Bearer key → constant-time match → route allow-list → asserted actor → service re-check", "starter/services/gateway.py"],
  ["sso", "key", "Single sign-on", "teach", "OpenID Connect + PKCE with one ATLAS identity provider; gateway verifies signed JWTs", "Guide §7"],
  ["kerberos", "ticket", "Kerberos", "teach", "KDC tickets for the driver app → Dispatch Service; live AES-GCM with attack scenarios", "Guide §8"],
  ["transport", "cloud", "Mutual TLS", "impl", "Prototype: private CA, serverAuth/clientAuth certificates, CERT_REQUIRED", "prototype/proto_run.py"],
  ["transport", "shield", "Secure deployment", "impl", "Loopback + SSH tunnel, CSP and security headers, systemd sandbox, signed APKs", "server.mjs · releases/"],
];

function secOverview() {
  return `<div class="sec-intro"><p>ATLAS is a full ride-hailing and food-delivery system, so it exercises the core of information security end to end. Each control below links to a live lab. Tags say whether it is <strong>in the ATLAS code</strong>, <strong>demo-grade</strong>, or a <strong>teaching extension</strong> mapped onto ATLAS components.</p>
    <div class="sec-legend">${Object.keys(secStatus).map((k) => `<span>${secChip(k)}<small>${secStatus[k].text}</small></span>`).join("")}</div></div>
    <div class="sec-grid">${secMap.map(([topic, ic, title, status, text, where]) => `<button type="button" class="sec-card" data-sec-topic="${topic}" data-keep="sec-card-${title}"><span class="sec-card-top">${icon(ic, 18)}${secChip(status)}</span><strong>${title}</strong><span>${text}</span><code>${where}</code></button>`).join("")}</div>
    ${secSection("CIA TRIAD IN ATLAS", "Where each property comes from", secTable(["Property", "Mechanism in ATLAS", "Where"], [
      ["Confidentiality", "Passwords never stored; mutual TLS between processes; app-private storage; SSH-only access to the explorer", "accounts.py · prototype · server.mjs"],
      ["Integrity", "Constant-time hash checks; route allow-list; atomic state writes with validation; signed APKs + SHA-256 sums", "store.py · gateway.py · releases/"],
      ["Availability", "Lockout is temporary (60 s), not permanent; damaged state quarantined, not fatal; ATLAS self-healing and recovery (the paper)", "store.py · atlas_sim/cluster.py"],
    ]))}`;
}

// ------------------------------------------------------------------ topic: passwords
async function secPwHash(again = false) {
  const password = again ? sec.fields.pw2 : sec.fields.pw;
  if (password.length < 8 || password.length > 128 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
    sec.pw.policy = "check_password: password must be 8 to 128 characters with at least one letter and one number.";
    return;
  }
  sec.pw.policy = "";
  const salt = secRand(16);
  const t0 = performance.now();
  const hash = await secPbkdf2(password, salt, 200000);
  const ms = performance.now() - t0;
  const record = { salt: secHex(salt), hash: secHex(hash), iterations: 200000 };
  if (again) sec.pw.records = [sec.pw.records[0], record].filter(Boolean);
  else sec.pw.records = [record];
  sec.pw.ms = ms;
  sec.pw.plain = secHex(await secSha256(password));
  sec.pw.verify = null;
}

async function secPwVerify() {
  const record = sec.pw.records[0];
  if (!record) return;
  const salt = Uint8Array.from(record.salt.match(/../g), (h) => parseInt(h, 16));
  const t0 = performance.now();
  const digest = await secPbkdf2(sec.fields.pwLogin, salt, record.iterations);
  const expected = Uint8Array.from(record.hash.match(/../g), (h) => parseInt(h, 16));
  sec.pw.verify = { ok: secEqual(digest, expected), recomputed: secHex(digest), ms: performance.now() - t0 };
}

function secPasswords() {
  const [a, b] = sec.pw.records;
  const perGuess = sec.pw.ms || 0;
  return `<div class="sec-intro"><p>ATLAS Go never keeps a password. <code>LocalStore.register</code> calls <code>hash_password</code>, which draws a fresh 16-byte salt and runs <strong>PBKDF2-HMAC-SHA256 for 200 000 iterations</strong>. Only <code>{salt, hash, iterations}</code> reaches <code>state.json</code>. This lab runs the same algorithm and parameters in your browser.</p></div>
  ${secSection("STEP 1", "Register: hash a password", `<div class="sec-row">${secField("pw", "Password typed at registration", "text")}${secButton("pw-hash", sec.busy === "pw" ? "Hashing 200 000 rounds…" : "Hash it like ATLAS", { primary: true, iconName: "lock" })}</div>
    ${sec.pw.policy ? `<ul class="sec-checks">${secCheck(false, sec.pw.policy)}</ul>` : ""}
    ${a ? `<p class="sec-label">Stored in <code>state.json</code> — the password itself is discarded</p>${secCode(JSON.stringify({ id: "U-1731000000000000000", role: "passenger", email: "aoife@example.ie", ...a }, null, 2))}<p class="sec-note">${icon("clock", 14)} Took <strong>${perGuess.toFixed(0)} ms</strong> here. An attacker pays that for <em>every</em> guess against this record.</p>` : ""}`)}
  ${a ? secSection("STEP 2", "Why the salt matters", `<div class="sec-row">${secField("pw2", "Second account, same password", "text")}${secButton("pw-again", "Register second account", { iconName: "user" })}</div>
    ${b ? secTable(["", "Salt", "Stored hash"], [["Account A", `<code>${secShort(a.salt, 16)}</code>`, `<code>${secShort(a.hash, 28)}</code>`], ["Account B", `<code>${secShort(b.salt, 16)}</code>`, `<code>${secShort(b.hash, 28)}</code>`]]) + `<ul class="sec-checks">${secCheck(a.hash !== b.hash, a.hash !== b.hash ? "Different hashes — a leaked file does not reveal that two users share a password" : "Same hash (different passwords would differ anyway)")}</ul>` : ""}
    <p class="sec-label">Compare: an <em>unsalted</em> SHA-256 (what ATLAS does <strong>not</strong> do)</p>${secCode("sha256(\"" + sec.fields.pw + "\") = " + (sec.pw.plain || ""))}<p class="sec-note">Identical for every user with this password, computable in nanoseconds, and listed in public rainbow tables for common passwords.</p>`) : ""}
  ${a ? secSection("STEP 3", "Sign in: verify", `<div class="sec-row">${secField("pwLogin", "Password typed at sign-in", "password", "try the right and a wrong one")}${secButton("pw-verify", sec.busy === "pwv" ? "Recomputing…" : "verify_password()", { primary: true, iconName: "key" })}</div>
    ${sec.pw.verify ? `<ul class="sec-checks">${secCheck(true, "Read stored salt and iterations from the record")}${secCheck(true, "Recompute PBKDF2 with them", `<code>${secShort(sec.pw.verify.recomputed, 32)}</code> in ${sec.pw.verify.ms.toFixed(0)} ms`)}${secCheck(sec.pw.verify.ok, sec.pw.verify.ok ? "hmac.compare_digest → equal: signed in" : "hmac.compare_digest → different: \"Email or password is not correct.\"", "Compares every byte, so timing does not reveal how close a guess was")}</ul>` : ""}`) : ""}
  ${secSection("THE CODE", "accounts.py", secCode(`PBKDF2_ITERATIONS = 200_000

def hash_password(password, salt=None, iterations=PBKDF2_ITERATIONS):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return dict(salt=salt.hex(), hash=digest.hex(), iterations=iterations)

def verify_password(password, record):
    salt = bytes.fromhex(record['salt']); expected = bytes.fromhex(record['hash'])
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, int(record['iterations']))
    return hmac.compare_digest(digest, expected)`) + secLink("android-app/atlas_go/accounts.py", SEC_MAIN + "android-app/atlas_go/accounts.py#L27-L42"))}`;
}

// ------------------------------------------------------------------ topic: login (replica of LocalStore.login)
async function secLoginInit() {
  const salt = secRand(16);
  sec.login = {
    account: { id: "U-1", email: "aoife@example.ie", role: "passenger", salt, hash: await secPbkdf2("cork2026", salt, 200000) },
    failures: {}, now: Date.now(), session: null, log: [],
  };
}

async function secLoginAttempt(email, password) {
  const L = sec.login;
  const [count0, until] = L.failures[email] || [0, 0];
  const entry = { at: L.now, email, steps: [] };
  if (until > L.now) {
    entry.steps.push([false, `Locked: until > now → "Too many attempts. Try again in ${Math.ceil((until - L.now) / 1000)} seconds."`]);
    entry.steps.push([true, "Password not even checked — no PBKDF2 work, no information leaked"]);
    L.log.unshift(entry);
    return;
  }
  const account = L.account.email === email ? L.account : null;
  let ok = false;
  if (account) ok = secEqual(await secPbkdf2(password, account.salt, 200000), account.hash);
  if (!ok) {
    const count = count0 + 1;
    L.failures[email] = count >= 5 ? [0, L.now + 60000] : [count, 0];
    entry.steps.push([false, account ? "Account found, PBKDF2 recomputed, digest differs" : "No account with this email"]);
    entry.steps.push([false, `"Email or password is not correct."`, "Identical message in both cases — no user enumeration"]);
    entry.steps.push([count < 5, count >= 5 ? "5th failure → failures[email] = [0, now + 60 s]: locked" : `failures[email] = [${count}, 0]`]);
  } else {
    delete L.failures[email];
    L.session = account.id;
    entry.steps.push([true, "PBKDF2 digest matches (compare_digest)"]);
    entry.steps.push([true, `failures cleared; session = "${account.id}" (role ${account.role}) saved atomically`]);
  }
  L.log.unshift(entry);
  L.log = L.log.slice(0, 8);
}

function secLogin() {
  const L = sec.login;
  if (!L) return `<div class="sec-intro"><p>A browser replica of <code>LocalStore.login</code> with one registered passenger, <code>aoife@example.ie</code> / <code>cork2026</code>, and a simulated clock you can advance.</p></div>${secButton("login-init", sec.busy === "login" ? "Hashing the account password…" : "Create the demo account", { primary: true, iconName: "user" })}`;
  const state0 = L.failures["aoife@example.ie"] || [0, 0];
  const locked = state0[1] > L.now;
  return `<div class="sec-intro"><p>A browser replica of <code>LocalStore.login</code> (same rules, same PBKDF2 cost). Registered passenger: <code>aoife@example.ie</code> / <code>cork2026</code>. The lockout counter lives in memory, exactly as in the app.</p></div>
    <div class="sec-status-row"><span class="sec-pill">${icon("clock", 14)} Clock ${secClock(L.now)}</span><span class="sec-pill ${locked ? "bad" : ""}">failures[aoife] = [${state0[0]}, ${state0[1] ? secClock(state0[1]) : 0}]</span><span class="sec-pill ${L.session ? "good" : ""}">session = ${L.session ? `"${L.session}"` : "None"}</span></div>
    <div class="sec-actions">${secButton("login-wrong", "Wrong password", { iconName: "cross" })}${secButton("login-unknown", "Unknown email", { iconName: "user" })}${secButton("login-right", "Correct password", { primary: true, iconName: "check" })}${secButton("login-tick", "Advance clock 60 s", { iconName: "clock" })}${secButton("login-reset", "Reset", { iconName: "reset" })}</div>
    ${sec.busy === "login" ? `<p class="sec-note">Running PBKDF2…</p>` : ""}
    <div class="sec-log">${L.log.map((e) => `<div class="sec-log-entry"><p><code>${secClock(e.at)}</code> login(<code>${secEsc(e.email)}</code>, …)</p><ul class="sec-checks">${e.steps.map(([ok, t, d]) => secCheck(ok, t, d)).join("")}</ul></div>`).join("") || `<p class="sec-note">Try five wrong passwords, then the right one.</p>`}</div>
    ${secSection("THE CODE", "store.py → LocalStore.login", secCode(`count, until = self.failures.get(email, [0, 0])
if until > now:
    raise ValueError(f'Too many attempts. Try again in {int(until - now) + 1} seconds.')
account = next((a for a in self.accounts if a['email'] == email), None)
if account is None or not acc.verify_password(password or '', account):
    count += 1
    self.failures[email] = [0, now + acc.LOCKOUT_SECONDS] if count >= acc.MAX_FAILED_LOGINS else [count, 0]
    raise ValueError('Email or password is not correct.')
self.failures.pop(email, None)
self.session, self.guest = account['id'], False`) + secLink("android-app/atlas_go/store.py", SEC_MAIN + "android-app/atlas_go/store.py#L304-L319"))}`;
}

// ------------------------------------------------------------------ topic: identity & roles
function secIdentity() {
  const yes = `<span class="sec-yes">${icon("check", 13)}</span>`;
  const no = `<span class="sec-no">${icon("cross", 13)}</span>`;
  const stages = [
    ["Register", "register(role, …)", "Validate email, E.164 phone, role fields; check_password; hash_password; unique email; id = U-&lt;ns&gt;"],
    ["Sign in", "login(email, password)", "PBKDF2 verify; lockout; session = id"],
    ["Use", "role-gated commands", "Every store command re-checks the role"],
    ["Sign out", "logout()", "session = None (drivers stay online until they go offline)"],
    ["Delete", "delete_account(password)", "Re-authenticate; refuse during an active ride/order; remove account; anonymise history; close seller kitchen"],
  ];
  return `<div class="sec-intro"><p><strong>Identity management</strong> is the whole lifecycle of an identity, not just login. ATLAS Go implements every stage on the phone; the server roadmap (<code>docs/ARCHITECTURE.md</code> → Identity) adds email/phone verification, password reset and tokens in the Android Keystore.</p></div>
    <ol class="sec-flow">${stages.map(([t, c, d], i) => `<li><span class="sec-flow-n">${i + 1}</span><strong>${t}</strong><code>${c}</code><small>${d}</small></li>`).join("")}</ol>
    ${secSection("IDENTITY RECORD", "What is stored per role", secTable(["Field", "Passenger", "Driver", "Food seller", "Assurance"], [
      ["Name, email, E.164 phone", yes, yes, yes, "Format-checked"],
      ["salt · hash · iterations", yes, yes, yes, "Credential (§ Password storage)"],
      ["Vehicle, plate (241-C-1234), seats", no, yes, no, "Self-declared"],
      ["SPSV licence number", no, yes, no, "Self-declared, not verified with the NTA"],
      ["Kitchen, food-business number", no, no, yes, "Self-declared, not verified with the FSAI"],
      ["Last phone location", no, "Only after consent; overwritten", no, "Data minimisation"],
    ]))}
    ${secSection("AUTHORISATION", "Role-based access control — enforced twice", secTable(["Capability", "Passenger", "Driver", "Seller", "Enforced in"], [
      ["Book ride / order food", yes, no, no, "store.book · store.checkout"],
      ["Go online, share location", no, yes, no, "store.set_online · update_location"],
      ["Accept ride request", no, yes, no, "store.driver_respond (own job only)"],
      ["Edit menu, accept order", no, no, yes, "store._my_kitchen (own kitchen only)"],
      ["Open driver/seller screens", no, "own", "own", "app.render allow-list"],
    ]) + secCode(`allowed = {'driver': ('driver','map','activity','profile','privacy','intelligence','account'),
           'seller': ('seller','seller_menu','activity','profile','privacy','intelligence','account')}
if self.store.user and self.store.role in allowed and self.screen not in allowed[self.store.role]:
    self.screen = self.home_screen()`) + `<p class="sec-note">Defence in depth: the screen allow-list stops accidental navigation; the store's own role checks stop a UI bug from becoming a privilege escalation.</p>`)}`;
}

// ------------------------------------------------------------------ topic: gateway (mirror of gateway.py + config.py)
const secKeys = { "rider-a": "rider-demo", "driver-a": "driver-a-demo", "driver-b": "driver-b-demo" };
const secRoutes = [
  ["GET", "rider", /^trips\/[a-f0-9-]{36}$/, "Trip"], ["POST", "rider", /^trips$/, "Trip"],
  ["POST", "driver", /^trips\/[a-f0-9-]{36}\/milestones$/, "Trip"], ["GET", "driver", /^offers$/, "Dispatch"],
  ["POST", "driver", /^offers\/[a-f0-9-]{36}\/accept$/, "Dispatch"], ["PUT", "driver", /^availability$/, "Dispatch"],
];
const secGatewayScenarios = {
  ok: { label: "Driver lists offers (valid key)", method: "GET", url: "/v1/driver/offers", auth: "driver-a-demo", headers: {} },
  wrongrole: { label: "Driver key on a rider route", method: "POST", url: "/v1/rider/trips", auth: "driver-a-demo", headers: {} },
  badkey: { label: "Guessed key", method: "GET", url: "/v1/driver/offers", auth: "driver-a-demo1", headers: {} },
  unknown: { label: "Route not on the allow-list", method: "DELETE", url: "/v1/driver/offers", auth: "driver-a-demo", headers: {} },
  forged: { label: "Client forges X-Atlas-Actor", method: "GET", url: "/v1/driver/offers", auth: "driver-b-demo", headers: { "X-Atlas-Actor": "driver-a", "X-Atlas-Internal": "guess" } },
  bypass: { label: "Call Dispatch directly, skip gateway", method: "GET", url: "http://dispatch:8002/v1/driver/offers", auth: "", headers: { "X-Atlas-Actor": "driver-a" }, direct: true },
};

function secGatewayRun(s) {
  const steps = [];
  const internal = "atlas-compose-local";
  if (s.direct) {
    steps.push([true, "Request reaches Dispatch Service without passing the gateway"]);
    steps.push([false, "internal_actor(): hmac.compare_digest(X-Atlas-Internal, TOKEN) fails → 403 \"Internal service\"", "Services do not trust the network alone"]);
    return { steps, status: 403 };
  }
  const [, , role, ...rest] = s.url.split("/");
  const path = rest.join("/");
  const route = secRoutes.find(([m, r, re]) => m === s.method && r === role && re.test(path));
  steps.push([!!route, route ? `Route allow-list: (${s.method}, ${role}, ${path}) → ${route[3]} Service` : `No (${s.method}, ${role}, ${path}) in ROUTES → 404 "Unknown route"`, "Checked before any authentication work"]);
  if (!route) return { steps, status: 404 };
  const actor = Object.keys(secKeys).find((k) => secKeys[k] === s.auth) || null;
  steps.push([!!actor, actor ? `Bearer key matches KEYS["${actor}"] (hmac.compare_digest)` : "Bearer key matches no entry in KEYS"]);
  const roleOk = !!actor && ((role === "rider") === actor.startsWith("rider-"));
  if (!actor || !roleOk) {
    if (actor) steps.push([false, `Role check: route role "${role}" but actor "${actor}"`]);
    steps.push([false, `401 "Provide a valid demo key for this role"`]);
    return { steps, status: 401 };
  }
  steps.push([true, `Role check: "${actor}" may use ${role} routes`]);
  if (s.headers["X-Atlas-Actor"]) steps.push([true, `Client-supplied X-Atlas-Actor: ${s.headers["X-Atlas-Actor"]} is discarded`, "The gateway builds a fresh header set; only Content-Type and Idempotency-Key are copied"]);
  steps.push([true, `Forward with X-Atlas-Actor: ${actor}, X-Atlas-Internal: ${internal}`]);
  steps.push([true, `${route[3]} Service internal_actor(): token matches, "${actor}" ∈ ${role === "rider" ? "('rider-a',)" : "DRIVERS"}`]);
  steps.push([true, `200 OK — data scoped to ${actor}`]);
  return { steps, status: 200 };
}

function secGateway() {
  const s = secGatewayScenarios[sec.gateway.scenario];
  const result = secGatewayRun(s);
  const shown = sec.gateway.step < 0 ? result.steps.length : Math.min(sec.gateway.step + 1, result.steps.length);
  const req = `${s.method} ${s.url}\n${s.auth ? `Authorization: Bearer ${s.auth}\n` : ""}${Object.entries(s.headers).map(([k, v]) => `${k}: ${v}`).join("\n")}`.trim();
  return `<div class="sec-intro"><p>The server starter authenticates at the edge and propagates identity inward — the same shape as SSO and Kerberos. Pick a request; each check below mirrors a line of <code>gateway.py</code> or <code>config.py</code>.</p></div>
    <div class="sec-row">${secSelect("gateway", Object.entries(secGatewayScenarios).map(([k, v]) => [k, v.label]), sec.gateway.scenario)}${secButton("gw-step", shown < result.steps.length ? "Next check" : "Replay", { iconName: "play" })}${secButton("gw-all", "Show all", { iconName: "chevron" })}</div>
    <div class="sec-two"><div><p class="sec-label">HTTP request</p>${secCode(req)}</div><div><p class="sec-label">Result</p><p class="sec-status sec-http-${result.status === 200 ? "ok" : "fail"}">${shown === result.steps.length ? `HTTP ${result.status}` : "…"}</p></div></div>
    <ul class="sec-checks">${result.steps.slice(0, shown).map(([ok, t, d]) => secCheck(ok, t, d)).join("")}</ul>
    ${secSection("THE CODE", "gateway.py → proxy()", secCode(`origin = next((url for (method, allowed_role, pattern), url in ROUTES.items()
               if method == request.method and role == allowed_role and re.fullmatch(pattern, path)), None)
if origin is None:
    raise HTTPException(404, "Unknown route")
key = request.headers.get("Authorization", "").removeprefix("Bearer ")
actor = next((name for name, expected in KEYS.items() if equal(key, expected)), None)
if actor is None or (role == "rider") != actor.startswith("rider-"):
    raise HTTPException(401, "Provide a valid demo key for this role")
headers = {"X-Atlas-Actor": actor, "X-Atlas-Internal": TOKEN}`) + secLink("starter/services/gateway.py", SEC_STARTER + "services/gateway.py#L46-L67") + secLink("starter/packages/config.py", SEC_STARTER + "packages/config.py#L20-L30"))}
    <p class="sec-note">${secChip("demo")} Keys default to <code>*-demo</code> values and the internal token is one static shared secret over plain HTTP between containers. The SSO and Kerberos tabs show the standard replacements.</p>`;
}

// ------------------------------------------------------------------ topic: SSO (OIDC + PKCE, real ES256 JWT)
const secSsoScenarios = [["normal", "Normal sign-in, then SSO to the seller portal"], ["stolen", "Attacker steals the authorisation code"], ["tamper", "Passenger edits role claim to \"driver\""], ["expired", "Expired access token"]];

async function secSsoNext() {
  const S = sec.sso;
  if (!S.ctx) S.ctx = { keys: await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]) };
  const c = S.ctx;
  const n = S.steps.length;
  const push = (title, from, to, wire, checks, done = false) => S.steps.push({ title, from, to, wire, checks, done });
  const user = S.scenario === "tamper" ? { sub: "U-passenger-7", role: "passenger" } : { sub: "U-driver-a", role: "driver" };
  if (n === 0) {
    c.verifier = secB64u(secRand(32));
    c.challenge = secB64u(await secSha256(c.verifier));
    push("① App creates a PKCE pair", "ATLAS Go app", "(local)", `code_verifier  = ${c.verifier}\ncode_challenge = BASE64URL(SHA-256(code_verifier))\n               = ${c.challenge}`, [[true, "The verifier never leaves the phone until the token request"]]);
  } else if (n === 1) {
    c.state = secB64u(secRand(9));
    push("② Redirect to the identity provider", "ATLAS Go app", "ATLAS Identity (IdP)", `GET https://id.atlas.local/authorize\n  ?response_type=code&client_id=atlas-go\n  &redirect_uri=ie.atlas.go:/callback&scope=openid atlas.rides\n  &state=${c.state}\n  &code_challenge=${secShort(c.challenge, 22)}&code_challenge_method=S256`, [[true, "Password is typed into the IdP's page, never into ATLAS Go"]]);
  } else if (n === 2) {
    c.code = secB64u(secRand(18));
    push("③ User authenticates once at the IdP", "Driver", "ATLAS Identity (IdP)", `password → PBKDF2 verify (as in Password storage)\n+ second factor (TOTP)\nSet-Cookie: idp_session=${secB64u(secRand(12))}; Secure; HttpOnly\n302 ie.atlas.go:/callback?code=${c.code}&state=${c.state}`, [[true, "IdP session cookie established — this is what makes the next app sign-in silent"], [true, "state echoed back → app rejects responses it did not ask for (CSRF)"]]);
  } else if (n === 3) {
    const verifier = S.scenario === "stolen" ? secB64u(secRand(32)) : c.verifier;
    const ok = secB64u(await secSha256(verifier)) === c.challenge;
    const wire = `POST https://id.atlas.local/token\ngrant_type=authorization_code&code=${secShort(c.code, 14)}\n&code_verifier=${secShort(verifier, 22)}${S.scenario === "stolen" ? "   ← attacker's own guess" : ""}`;
    if (!ok) { push("④ Token request", S.scenario === "stolen" ? "Attacker app" : "ATLAS Go app", "ATLAS Identity (IdP)", wire, [[false, "SHA-256(code_verifier) ≠ code_challenge → 400 invalid_grant", "PKCE makes an intercepted code worthless"]], true); return; }
    const now = Math.floor(Date.now() / 1000);
    const payload = { iss: "https://id.atlas.local", aud: "atlas-gateway", sub: user.sub, role: user.role, iat: now, exp: S.scenario === "expired" ? now - 30 : now + 600 };
    const header = { alg: "ES256", typ: "JWT", kid: "atlas-2026" };
    const signingInput = secB64u(secEnc.encode(JSON.stringify(header))) + "." + secB64u(secEnc.encode(JSON.stringify(payload)));
    const sig = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, c.keys.privateKey, secEnc.encode(signingInput));
    c.jwt = signingInput + "." + secB64u(sig);
    c.payload = payload;
    push("④ Token request → signed access token", "ATLAS Go app", "ATLAS Identity (IdP)", `${wire}\n\n200 { access_token: "${secShort(c.jwt, 40)}", expires_in: 600 }\n\nheader  ${JSON.stringify(header)}\npayload ${JSON.stringify(payload)}\nsignature ES256 (ECDSA P-256) ${secShort(secB64u(sig), 30)}`, [[true, "SHA-256(code_verifier) = code_challenge"], [true, "Token signed with the IdP's private key; the gateway only needs the public key"]]);
  } else if (n === 4) {
    let token = c.jwt;
    if (S.scenario === "tamper") {
      const [h, , s] = token.split(".");
      token = h + "." + secB64u(secEnc.encode(JSON.stringify({ ...c.payload, role: "driver" }))) + "." + s;
    }
    const [h, p, s] = token.split(".");
    const valid = await crypto.subtle.verify({ name: "ECDSA", hash: "SHA-256" }, c.keys.publicKey, secFromB64u(s), secEnc.encode(h + "." + p));
    const claims = JSON.parse(secDec.decode(secFromB64u(p)));
    const now = Math.floor(Date.now() / 1000);
    const checks = [[valid, valid ? "Signature verifies with the IdP public key (JWKS)" : "Signature does NOT verify → 401", valid ? "" : "Changing one claim changes the signing input"]];
    if (valid) {
      checks.push([claims.iss === "https://id.atlas.local", `iss = ${claims.iss}`]);
      checks.push([claims.aud === "atlas-gateway", `aud = ${claims.aud}`]);
      checks.push([claims.exp > now, claims.exp > now ? `exp in ${claims.exp - now} s` : `exp passed ${now - claims.exp} s ago → 401, refresh the token`]);
      if (claims.exp > now) {
        checks.push([claims.role === "driver", claims.role === "driver" ? "role = driver → may call GET /v1/driver/offers" : `role = ${claims.role} → 401 for driver routes`]);
        if (claims.role === "driver") checks.push([true, `Forward with X-Atlas-Actor: ${claims.sub} — Dispatch Service unchanged`]);
      }
    }
    push("⑤ Call ATLAS through the gateway", S.scenario === "tamper" ? "Tampering passenger" : "ATLAS Go app", "API Gateway", `GET /v1/driver/offers\nAuthorization: Bearer ${secShort(token, 46)}${S.scenario === "tamper" ? "\n(payload edited: role passenger → driver)" : ""}`, checks, !(valid && claims.exp > now && claims.role === "driver") || S.scenario !== "normal");
  } else if (n === 5) {
    push("⑥ Single sign-on: open the seller portal", "Seller portal (browser)", "ATLAS Identity (IdP)", `GET https://id.atlas.local/authorize?client_id=atlas-seller-portal&…\nCookie: idp_session=…\n302 https://seller.atlas.local/callback?code=…`, [[true, "IdP session cookie present → no password prompt"], [true, "New token with aud = the portal; same identity, same MFA"], [true, "Revoke once at the IdP → every ATLAS app loses access"]], true);
  }
}

function secMessages(steps) {
  return `<div class="sec-msgs">${steps.map((m) => `<article class="sec-msg ${m.checks.every(([ok]) => ok) ? "" : "failed"}"><header><strong>${m.title}</strong><span>${m.from} → ${m.to}</span></header>${secCode(m.wire)}<ul class="sec-checks">${m.checks.map(([ok, t, d]) => secCheck(ok, t, d)).join("")}</ul></article>`).join("")}</div>`;
}

function secSso() {
  const S = sec.sso;
  const done = S.steps.length && S.steps[S.steps.length - 1].done;
  return `<div class="sec-intro"><p><strong>Not in the ATLAS code.</strong> ATLAS has four front ends — passenger app, driver app, seller portal, explorer. With SSO one <em>ATLAS Identity</em> provider authenticates the user once (OpenID Connect, authorisation code + PKCE) and the gateway accepts its signed tokens in place of today's static bearer keys. Tokens below are real ES256 JWTs signed in your browser.</p></div>
    <div class="sec-row">${secSelect("sso", secSsoScenarios, S.scenario)}${secButton("sso-next", done ? "Finished — reset to rerun" : `Next message (${S.steps.length}/6)`, { primary: !done, iconName: "play", disabled: done })}${secButton("sso-reset", "Reset", { iconName: "reset" })}</div>
    ${secMessages(S.steps)}
    ${secSection("MAPPING", "SSO roles → ATLAS components", secTable(["SSO role", "ATLAS component", "Today"], [
      ["End user", "Passenger, driver, food seller", "Same"],
      ["Client / relying party", "ATLAS Go app, driver web app, seller portal, explorer", "Each app holds its own static key"],
      ["Identity provider", "ATLAS Identity (e.g. Keycloak) or the university IdP via SAML", "None — gateway checks KEYS"],
      ["Resource server", "API Gateway → Trip and Dispatch services", "Same"],
      ["Token", "Signed JWT: sub, role, aud, exp (10 min) + refresh token in Android Keystore", "Never-expiring demo key"],
    ]))}`;
}

// ------------------------------------------------------------------ topic: Kerberos (real AES-GCM, PBKDF2 string-to-key)
const secKrbScenarios = [["normal", "Normal exchange"], ["wrongpw", "Wrong password typed"], ["skew", "Driver's phone clock 7 min fast"], ["tamper", "Attacker flips a byte in the service ticket"], ["expired", "Service ticket already expired"], ["replay", "Attacker replays the captured AP-REQ"]];
const SEC_REALM = "ATLAS.LOCAL";
const SEC_SKEW = 300; // seconds, the Kerberos default

async function secKrbSetup() {
  const salt = secEnc.encode(SEC_REALM + "driver-a");
  const ctx = {
    K_C: await secPbkdf2("Drive2026", salt, 4096, "SHA-1"), // RFC 3962 string-to-key: PBKDF2, salt = realm + principal, 4096 rounds
    K_TGS: secRand(32), K_S: secRand(32), replay: new Set(), known: { app: [], kdc: ["K_C", "K_TGS", "K_S"], dispatch: ["K_S"] },
  };
  ctx.fp = { K_C: await secFingerprint(ctx.K_C), K_TGS: await secFingerprint(ctx.K_TGS), K_S: await secFingerprint(ctx.K_S) };
  return ctx;
}

async function secKrbNext() {
  const K = sec.krb;
  if (!K.ctx) K.ctx = await secKrbSetup();
  const c = K.ctx;
  const n = K.steps.length;
  const kdcNow = () => Math.floor(Date.now() / 1000);
  const appNow = () => kdcNow() + (K.scenario === "skew" ? 420 : 0);
  const push = (title, from, to, wire, checks, done = false) => K.steps.push({ title, from, to, wire, checks, done });
  const skewOk = (t) => Math.abs(t - kdcNow()) <= SEC_SKEW;
  const fail = (title, from, to, wire, checks) => push(title, from, to, wire, checks, true);

  if (n === 0) {
    const typed = K.scenario === "wrongpw" ? sec.fields.krbPassword + "x" : sec.fields.krbPassword;
    c.K_C_app = await secPbkdf2(typed, secEnc.encode(SEC_REALM + "driver-a"), 4096, "SHA-1");
    c.nonce1 = secHex(secRand(4));
    const ts = appNow();
    const padata = await secSeal(c.K_C_app, { patimestamp: ts });
    const wire = `AS-REQ\n  cname   driver-a@${SEC_REALM}\n  sname   krbtgt/${SEC_REALM}\n  nonce   ${c.nonce1}\n  padata  PA-ENC-TIMESTAMP {${secClock(ts * 1000)}}K_C = ${secShort(secHex(padata), 40)}\n\n(app: password "${K.scenario === "wrongpw" ? typed : "•".repeat(typed.length)}" → PBKDF2(realm+principal, 4096) → K_C, fp ${await secFingerprint(c.K_C_app)})`;
    let pa;
    try { pa = await secOpen(c.K_C, padata); } catch { fail("① AS-REQ — pre-authentication", "Driver app", "KDC · AS", wire, [[false, "KDC cannot decrypt the timestamp with its stored K_C → KDC_ERR_PREAUTH_FAILED", "Wrong password ⇒ wrong key. The password itself never crossed the network"]]); return; }
    if (!skewOk(pa.patimestamp)) { fail("① AS-REQ — pre-authentication", "Driver app", "KDC · AS", wire, [[true, "Timestamp decrypts with K_C (right password)"], [false, `|client time − KDC time| = ${pa.patimestamp - kdcNow()} s > ${SEC_SKEW} s → KRB_AP_ERR_SKEW`, "Kerberos needs synchronised clocks (NTP)"]]); return; }
    push("① AS-REQ — pre-authentication", "Driver app", "KDC · AS", wire, [[true, "KDC decrypts the timestamp with stored K_C → the app knows the password"], [true, `Clock skew ${pa.patimestamp - kdcNow()} s ≤ ${SEC_SKEW} s`]]);
    c.known.app.push("K_C");
  } else if (n === 1) {
    c.K_CTGS = secRand(32);
    const now = kdcNow();
    c.tgt = await secSeal(c.K_TGS, { cname: "driver-a", key: secHex(c.K_CTGS), authtime: now, endtime: now + 36000 });
    const encPart = await secSeal(c.K_C, { key: secHex(c.K_CTGS), nonce: c.nonce1, endtime: now + 36000 });
    const part = await secOpen(c.K_C_app, encPart);
    push("② AS-REP — ticket-granting ticket", "KDC · AS", "Driver app", `AS-REP\n  ticket (TGT)  {cname, K_C,TGS, endtime}K_TGS = ${secShort(secHex(c.tgt), 40)}\n  enc-part      {K_C,TGS, nonce, endtime}K_C  = ${secShort(secHex(encPart), 40)}\n\n(app decrypts enc-part: K_C,TGS fp ${await secFingerprint(c.K_CTGS)}, valid until ${secClock((now + 36000) * 1000)})`, [[part.nonce === c.nonce1, `Nonce ${part.nonce} matches the request → reply is fresh`], [true, "App cannot read the TGT (sealed with K_TGS); it just stores it"], [true, "App now forgets the password and K_C — it has K_C,TGS for the day"]]);
    c.known.app = ["K_C,TGS"]; c.known.kdc.push("K_C,TGS");
  } else if (n === 2) {
    c.nonce2 = secHex(secRand(4));
    const ctime = appNow();
    const auth = await secSeal(c.K_CTGS, { cname: "driver-a", ctime });
    const wire = `TGS-REQ\n  sname          HTTP/dispatch.atlas@${SEC_REALM}\n  ticket (TGT)   ${secShort(secHex(c.tgt), 40)}\n  authenticator  {cname, ${secClock(ctime * 1000)}}K_C,TGS = ${secShort(secHex(auth), 30)}\n  nonce          ${c.nonce2}`;
    const tgt = await secOpen(c.K_TGS, c.tgt);
    const a = await secOpen(Uint8Array.from(tgt.key.match(/../g), (h) => parseInt(h, 16)), auth);
    const key = `${a.cname}|${a.ctime}`;
    const fresh = !c.replay.has(key);
    c.replay.add(key);
    push("③ TGS-REQ — ask for a Dispatch ticket", "Driver app", "KDC · TGS", wire, [[true, "TGS decrypts the TGT with K_TGS → learns K_C,TGS"], [tgt.endtime > kdcNow(), "TGT not expired"], [a.cname === tgt.cname, "Authenticator cname = TGT cname (driver-a)"], [skewOk(a.ctime) && fresh, "Authenticator within ±5 min and not in the replay cache"]]);
  } else if (n === 3) {
    c.K_CS = secRand(32);
    const now = kdcNow();
    const endtime = K.scenario === "expired" ? now - 60 : now + 36000;
    c.ticket = await secSeal(c.K_S, { cname: "driver-a", realm: SEC_REALM, key: secHex(c.K_CS), endtime });
    const encPart = await secSeal(c.K_CTGS, { key: secHex(c.K_CS), nonce: c.nonce2, sname: "HTTP/dispatch.atlas" });
    const part = await secOpen(c.K_CTGS, encPart);
    push("④ TGS-REP — service ticket for Dispatch", "KDC · TGS", "Driver app", `TGS-REP\n  ticket    {cname, K_C,S, endtime}K_S  = ${secShort(secHex(c.ticket), 40)}\n  enc-part  {K_C,S, nonce, sname}K_C,TGS = ${secShort(secHex(encPart), 40)}\n\n(service ticket valid until ${secClock(endtime * 1000)}${K.scenario === "expired" ? " — already past" : ""})`, [[part.nonce === c.nonce2, `Nonce ${part.nonce} matches`], [true, "Ticket sealed with Dispatch's own key K_S — the KDC is not needed again"]]);
    c.known.app.push("K_C,S"); c.known.kdc.push("K_C,S");
  } else if (n === 4) {
    const ctime = appNow();
    const auth = await secSeal(c.K_CS, { cname: "driver-a", ctime });
    let ticket = c.ticket;
    if (K.scenario === "tamper") { ticket = ticket.slice(); ticket[30] ^= 1; }
    c.apreq = { ticket, auth };
    const wire = `AP-REQ  (with GET /v1/driver/offers)\n  ticket         ${secShort(secHex(ticket), 40)}${K.scenario === "tamper" ? "   ← byte 30 flipped" : ""}\n  authenticator  {cname, ${secClock(ctime * 1000)}}K_C,S = ${secShort(secHex(auth), 30)}`;
    const r = await secKrbVerifyAp(c, ticket, auth);
    if (!r.ok) { fail("⑤ AP-REQ — present ticket to Dispatch", "Driver app", "Dispatch Service", wire, r.checks); return; }
    push("⑤ AP-REQ — present ticket to Dispatch", "Driver app", "Dispatch Service", wire, r.checks);
    c.known.dispatch.push("K_C,S");
    c.ctime = r.ctime;
  } else if (n === 5) {
    const aprep = await secSeal(c.K_CS, { ctime: c.ctime });
    const back = await secOpen(c.K_CS, aprep);
    push("⑥ AP-REP — Dispatch proves itself", "Dispatch Service", "Driver app", `AP-REP\n  enc-part {ctime = ${secClock(back.ctime * 1000)}}K_C,S = ${secShort(secHex(aprep), 40)}\n\n200 OK  offers for driver-a@${SEC_REALM}`, [[back.ctime === c.ctime, "App decrypts and sees its own timestamp → it is talking to the real Dispatch Service (mutual authentication)"], [true, "Identity propagated to Dispatch as X-Atlas-Actor: driver-a — no password, no static key, no KDC round-trip"]], K.scenario !== "replay");
  } else if (n === 6 && K.scenario === "replay") {
    const r = await secKrbVerifyAp(c, c.apreq.ticket, c.apreq.auth);
    fail("⑦ Replay — attacker resends the captured AP-REQ", "Attacker", "Dispatch Service", `AP-REQ (byte-for-byte copy of ⑤, captured on the network)\n  ticket         ${secShort(secHex(c.apreq.ticket), 40)}\n  authenticator  ${secShort(secHex(c.apreq.auth), 30)}`, r.checks);
  }
}

async function secKrbVerifyAp(c, ticketBytes, authBytes) {
  const checks = [];
  let t;
  try { t = await secOpen(c.K_S, ticketBytes); } catch {
    checks.push([false, "AES-GCM tag check fails decrypting the ticket with K_S → KRB_AP_ERR_BAD_INTEGRITY", "One flipped bit is detected; the ticket cannot be edited (e.g. to change cname)"]);
    return { ok: false, checks };
  }
  checks.push([true, "Dispatch decrypts the ticket with its own K_S → learns cname and K_C,S"]);
  const now = Math.floor(Date.now() / 1000);
  if (t.endtime <= now) { checks.push([false, `Ticket endtime ${secClock(t.endtime * 1000)} has passed → KRB_AP_ERR_TKT_EXPIRED`, "The app must go back to the TGS (step ③) — no password needed while the TGT is valid"]); return { ok: false, checks }; }
  checks.push([true, "Ticket not expired"]);
  const a = await secOpen(Uint8Array.from(t.key.match(/../g), (h) => parseInt(h, 16)), authBytes);
  checks.push([a.cname === t.cname, `Authenticator cname "${a.cname}" = ticket cname "${t.cname}"`]);
  if (Math.abs(a.ctime - now) > SEC_SKEW) { checks.push([false, "Authenticator outside ±5 min → KRB_AP_ERR_SKEW"]); return { ok: false, checks }; }
  const key = `ap|${a.cname}|${a.ctime}`;
  if (c.replay.has(key)) { checks.push([false, "(cname, ctime) already in Dispatch's replay cache → KRB_AP_ERR_REPEAT", "The attacker had valid ciphertext but could not make a fresh authenticator without K_C,S"]); return { ok: false, checks }; }
  c.replay.add(key);
  checks.push([true, "Within ±5 min and not seen before → added to the replay cache"]);
  return { ok: true, checks, ctime: a.ctime };
}

function secKrb() {
  const K = sec.krb;
  const done = K.steps.length && K.steps[K.steps.length - 1].done;
  const total = K.scenario === "replay" ? 7 : 6;
  const c = K.ctx;
  const has = (who, k) => c && c.known[who].includes(k);
  const keyRows = [["K_C", "from the password"], ["K_TGS", "krbtgt key"], ["K_C,TGS", "session key, ②"], ["K_S", "Dispatch's key"], ["K_C,S", "session key, ④"]];
  const cell = (ok) => (ok ? `<span class="sec-yes">${icon("key", 13)}</span>` : `<span class="sec-dim">—</span>`);
  return `<div class="sec-intro"><p><strong>Not in the ATLAS code.</strong> Kerberos replaces the starter's static keys with short-lived tickets from a trusted third party. Here the <strong>driver app</strong> (<code>driver-a@${SEC_REALM}</code>) obtains a ticket for the <strong>Dispatch Service</strong> from an <em>ATLAS Identity</em> KDC. Every ciphertext is real AES-256-GCM made in your browser at the current time; the password-to-key step is PBKDF2 with realm + principal as salt, as in RFC 3962.</p></div>
    <div class="sec-row">${secField("krbPassword", "Driver password (KDC holds the key for Drive2026)", "text")}${secSelect("krb", secKrbScenarios, K.scenario)}</div>
    <div class="sec-actions">${secButton("krb-next", done ? "Finished — reset to rerun" : `Next message (${K.steps.length}/${total})`, { primary: !done, iconName: "play", disabled: done })}${secButton("krb-all", "Run to the end", { iconName: "chevron", disabled: done })}${secButton("krb-reset", "Reset", { iconName: "reset" })}${sec.busy === "krb" ? `<span class="sec-note">Encrypting…</span>` : ""}</div>
    ${secMessages(K.steps)}
    ${secSection("WHO HOLDS WHICH KEY", "Updated live as messages flow", secTable(["Key", "Driver app", "KDC (AS + TGS)", "Dispatch Service"], keyRows.map(([k, d]) => [`<code>${k}</code><small> ${d}${c && c.fp[k] ? ` · fp ${c.fp[k]}` : ""}</small>`, cell(has("app", k)), cell(has("kdc", k)), cell(has("dispatch", k))]), "sec-keys") + `<p class="sec-note">Dispatch never learns the password or K_C; the app never learns K_TGS or K_S. Compromising Trip Service would not let anyone mint tickets for Dispatch — unlike the starter's single shared <code>X-Atlas-Internal</code> token.</p>`)}
    ${secSection("MAPPING", "Kerberos principals → ATLAS", secTable(["Kerberos", "ATLAS stand-in", "Replaces today's"], [
      ["Client C", "Driver app, driver-a@ATLAS.LOCAL", "Bearer key driver-a-demo"],
      ["AS + TGS = KDC", "ATLAS Identity service", "KEYS dict in config.py"],
      ["Service S", "HTTP/dispatch.atlas (Dispatch Service)", "internal_actor() + shared token"],
      ["Authenticator + replay cache", "Per-request freshness proof", "Nothing (static key can be replayed)"],
      ["AP-REP", "Dispatch proves its identity", "Nothing (no mutual authentication)"],
    ]))}`;
}

// ------------------------------------------------------------------ topic: transport & deployment
function secTransport() {
  return `<div class="sec-intro"><p>Security outside the application code: how processes authenticate each other on the wire, how the explorer is hosted, and how users can trust the app they download.</p></div>
    ${secSection("MUTUAL TLS · PROTOTYPE", "Two processes that prove who they are", `<ol class="sec-flow">${[
      ["Private CA", "openssl req -x509 … /CN=atlas-ca", "basicConstraints CA:TRUE, keyUsage keyCertSign, 30 days"],
      ["Server certificate", "extendedKeyUsage=serverAuth", "subjectAltName=IP:127.0.0.1 binds it to the address"],
      ["Client certificate", "extendedKeyUsage=clientAuth", "Cannot be reused as a server certificate"],
      ["Server requires a client cert", "verify_mode = ssl.CERT_REQUIRED", "No certificate from atlas-ca → handshake fails"],
      ["Client verifies the server", "create_default_context(cafile=ca.crt)", "Plus load_cert_chain to present its own identity"],
    ].map(([t, c, d], i) => `<li><span class="sec-flow-n">${i + 1}</span><strong>${t}</strong><code>${c}</code><small>${d}</small></li>`).join("")}</ol><p class="sec-note">Certificates are generated at run time and never committed. <code>results/prototype.json</code> measures the cost of HTTPS + mTLS vs plain HTTP, and of a full handshake per call — a concrete answer to "what does security cost?".</p>${secLink("prototype/proto_run.py (prototype.zip)", SEC_MAIN + "prototype.zip")}`)}
    ${secSection("EXPLORER SERVER", "server.mjs and the systemd unit", secTable(["Control", "Setting", "Threat"], [
      ["Network exposure", "Listens on 127.0.0.1 only; reach it through an SSH tunnel", "Direct attack from the network"],
      ["Methods", "GET and HEAD; anything else → 405", "Unexpected write paths"],
      ["Files", "Fixed in-memory list; unknown path → 404", "Path traversal"],
      ["CSP", "default-src 'none'; script-src 'self'; frame-ancestors 'none'; form-action 'none'", "XSS, clickjacking, form exfiltration"],
      ["Headers", "nosniff · no-referrer · no-store · noindex", "MIME sniffing, URL leakage, caching"],
      ["systemd", "DynamicUser, NoNewPrivileges, ProtectSystem=strict, ProtectHome, PrivateTmp", "Blast radius after compromise"],
    ]) + secLink("architecture-explorer/server.mjs", SEC_EXPLORER + "server.mjs") + secLink("deploy/atlas-explorer.service", SEC_EXPLORER + "deploy/atlas-explorer.service"))}
    ${secSection("SUPPLY CHAIN · ATLAS GO", "Trusting the APK you install", `<p class="sec-text">Releases ship with APK v2/v3 signatures, a published upload certificate, a release manifest and <code>SHA256SUMS</code>. Verify before installing:</p>${secCode("sha256sum -c SHA256SUMS\napksigner verify --print-certs atlas-go-1.2.0.apk")}${secLink("android-app/releases/", "https://github.com/FUllSCIPTS/ATLAS/tree/main/android-app/releases")}`)}`;
}

// ------------------------------------------------------------------ topic: gaps
function secGaps() {
  return `<div class="sec-intro"><p>Real properties of the current code — ready-made "find it, fix it, test it" assignments.</p></div>
    ${secTable(["#", "Gap", "Where", "Exercise"], [
      ["1", "PBKDF2 at 200 000 iterations; OWASP suggests 600 000 for PBKDF2-HMAC-SHA256", "accounts.py", "Time it on a phone; rehash on login when iterations are below target; compare Argon2id"],
      ["2", "Lockout counter is memory-only, per email", "store.py → self.failures", "Restart resets it. Persist it; add exponential back-off"],
      ["3", "No MFA, no password reset", "—", "Add TOTP (RFC 6238); design a reset flow that does not enable account takeover"],
      ["4", "state.json not encrypted at rest", "store.py", "Encrypt with a key held in the Android Keystore"],
      ["5", "Default demo keys and internal token", "starter/packages/config.py", "Refuse to start with defaults outside local mode"],
      ["6", "Static shared internal token over plain HTTP", "gateway.py · compose.yaml", "Replace with mTLS (prototype) or signed short-lived tokens"],
      ["7", "Bearer keys never expire", "gateway.py", "Replace with OIDC access tokens (SSO tab)"],
      ["8", "Licence and business numbers are self-declared", "accounts.py", "Discuss identity assurance levels; design verification"],
    ])}
    ${secSection("LESSON PLAN", "Eight sessions built on ATLAS", secTable(["Session", "Topic", "Use"], [
      ["1", "CIA triad, threat modelling", "Security map + Architecture tab (STRIDE)"],
      ["2", "Password storage", "Password storage tab + security_lab/password_storage_demo.py"],
      ["3", "Authentication & identity", "Login & lockout, Identity & roles"],
      ["4", "Authorisation", "Gateway auth: driver key on rider route"],
      ["5", "SSO & federation", "Single sign-on tab"],
      ["6", "Kerberos", "Kerberos live: run every attack scenario"],
      ["7", "Transport security", "Run the prototype; remove the client cert"],
      ["8", "Secure engineering", "Fix one gap above with a test"],
    ]))}
    <p class="sec-note">Full write-up: <a class="sec-inline-link" href="${SEC_GUIDE}">docs/INFORMATION_SECURITY.md</a></p>`;
}

// ------------------------------------------------------------------ inspector
const secInspect = {
  overview: { summary: "Nine controls across the Android app, the server starter, the prototype and the explorer server.", files: [["docs/INFORMATION_SECURITY.md", SEC_GUIDE], ["security_lab/password_storage_demo.py", SEC_MAIN + "security_lab/password_storage_demo.py"]], facts: [["Implemented", "Passwords, login, identity, RBAC, mTLS, deployment"], ["Demo-grade", "Gateway keys and internal token"], ["Teaching extension", "SSO, Kerberos"]], questions: ["Which control protects which letter of CIA?", "Where is the trust boundary between the app and the server?"] },
  passwords: { summary: "One-way, salted, deliberately slow. The record carries its own iteration count so the cost can be raised later.", files: [["android-app/atlas_go/accounts.py", SEC_MAIN + "android-app/atlas_go/accounts.py#L27-L42"], ["android-app/tests/test_accounts_geo.py", SEC_MAIN + "android-app/tests/test_accounts_geo.py#L9-L15"], ["android-app/docs/PRIVACY.md", SEC_MAIN + "android-app/docs/PRIVACY.md"]], facts: [["Algorithm", "PBKDF2-HMAC-SHA256"], ["Iterations", "200 000"], ["Salt", "16 random bytes per account"], ["Output", "32 bytes, hex"], ["Compare", "hmac.compare_digest"], ["Policy", "8–128 chars, letter + digit"]], questions: ["Why hash rather than encrypt?", "What does the salt stop, and what does it not stop?", "Why store the iteration count?", "Why is an upper length limit a security control?"] },
  login: { summary: "Online guessing is throttled; failures look identical whether or not the account exists.", files: [["android-app/atlas_go/store.py → login", SEC_MAIN + "android-app/atlas_go/store.py#L304-L319"], ["android-app/atlas_go/accounts.py (limits)", SEC_MAIN + "android-app/atlas_go/accounts.py#L16-L18"]], facts: [["Max failures", "5"], ["Lockout", "60 s"], ["Counter", "In memory, per email"], ["Session", "Account id in state.json, validated on load"]], questions: ["Why not lock permanently?", "What attack does the generic message prevent?", "What happens to the counter if the app restarts?"] },
  identity: { summary: "The lifecycle from registration to deletion, with roles enforced at two layers.", files: [["android-app/atlas_go/store.py", SEC_MAIN + "android-app/atlas_go/store.py#L260-L357"], ["android-app/atlas_go/app.py → render", SEC_MAIN + "android-app/atlas_go/app.py#L428-L435"], ["android-app/docs/ARCHITECTURE.md (Identity roadmap)", SEC_MAIN + "android-app/docs/ARCHITECTURE.md"]], facts: [["Roles", "passenger · driver · seller"], ["Identifier", "U-<nanoseconds>, email unique"], ["Re-auth", "Required to delete"], ["Erasure", "Account removed, history anonymised"]], questions: ["Which identity attributes are verified and which only claimed?", "Why re-ask the password before deletion?", "Why check roles in the store if the UI already hides screens?"] },
  gateway: { summary: "Authenticate at the edge, propagate identity inward, re-check inside each service.", files: [["starter/services/gateway.py", SEC_STARTER + "services/gateway.py#L46-L67"], ["starter/packages/config.py", SEC_STARTER + "packages/config.py"], ["starter/services/dispatch.py", SEC_STARTER + "services/dispatch.py"]], facts: [["Client credential", "Static bearer key per actor"], ["Comparison", "hmac.compare_digest"], ["Route control", "Allow-list: method + role + regex"], ["Internal trust", "X-Atlas-Internal shared token"], ["Body limit", "8 KiB"]], questions: ["Why check the route before the key?", "What stops a client from sending its own X-Atlas-Actor?", "What breaks if the internal token leaks?"] },
  sso: { summary: "One identity provider, many ATLAS front ends. The gateway verifies signatures instead of looking up shared keys.", files: [["docs/INFORMATION_SECURITY.md §7", SEC_GUIDE + "#7-single-sign-on-sso-for-atlas--teaching-extension"]], facts: [["Protocol", "OpenID Connect"], ["Flow", "Authorization code + PKCE (S256)"], ["Token", "JWT, ES256, 10 min"], ["Gateway checks", "signature, iss, aud, exp, role"]], questions: ["What does PKCE add for a mobile app?", "Why can the gateway verify tokens without calling the IdP?", "What is the cost of a single point of authentication?"] },
  kerberos: { summary: "Symmetric-key tickets from a trusted third party. The password is used once to derive K_C and never crosses the network.", files: [["docs/INFORMATION_SECURITY.md §8", SEC_GUIDE + "#8-kerberos-step-by-step-on-atlas-components--teaching-extension"]], facts: [["Realm", SEC_REALM], ["Client", "driver-a"], ["Service", "HTTP/dispatch.atlas"], ["Clock skew", "±300 s"], ["TGT lifetime", "10 h"], ["Cipher (demo)", "AES-256-GCM"], ["String-to-key", "PBKDF2-SHA1, 4096, salt realm+principal"]], questions: ["Why can't the driver app read its own TGT?", "Which field defeats a replay?", "What would a stolen K_TGS allow (golden ticket)?", "Why must clocks be synchronised?"] },
  transport: { summary: "Mutual authentication on the wire, a locked-down host for the explorer, and verifiable releases.", files: [["prototype.zip → proto_run.py, module_server.py", SEC_MAIN + "prototype.zip"], ["architecture-explorer/server.mjs", SEC_EXPLORER + "server.mjs"], ["android-app/releases/", "https://github.com/FUllSCIPTS/ATLAS/tree/main/android-app/releases"]], facts: [["mTLS", "Private CA, CERT_REQUIRED"], ["Cert lifetime", "30 days"], ["Explorer bind", "127.0.0.1"], ["Release integrity", "APK v2/v3 + SHA-256"]], questions: ["What does mutual TLS add over ordinary HTTPS?", "Why is serverAuth vs clientAuth key usage important?", "Why bind to loopback instead of adding a login page?"] },
  gaps: { summary: "Eight known gaps, each a self-contained assignment.", files: [["docs/INFORMATION_SECURITY.md §11", SEC_GUIDE + "#11-known-gaps--exercises-for-students"]], facts: [["Exercises", "8"], ["Sessions", "8"]], questions: ["Which gap would you fix first, and why?"] },
};

function securityInspector() {
  const t = secTopicById[sec.topic];
  const info = secInspect[sec.topic];
  return `<div class="inspector-head"><span>${icon("shield", 16)} SECURITY INSPECTOR</span><span class="status-dot" aria-hidden="true"></span></div>
    <div class="inspector-body" style="--accent:${t.status === "teach" ? "#c4aeff" : t.status === "demo" ? "#ffc983" : "#c2f77a"}"><div class="inspector-identity"><span class="component-icon" style="--accent:inherit">${icon(t.icon, 23)}</span><div><p>${t.status ? secStatus[t.status].label : "Overview"}</p><h2 id="component-title" tabindex="-1">${t.title}</h2></div></div>
    <p class="inspector-summary">${info.summary}</p>
    <dl class="sec-facts">${info.facts.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("")}</dl>
    <div class="connection-group"><h3>Where in the code</h3>${info.files.map(([l, u]) => secLink(l, u)).join("")}</div>
    ${umlInspector(`security/${sec.topic}`, "security", secTopics)}
    <div class="connection-group"><h3>Questions for students</h3><ol class="sec-questions">${info.questions.map((q) => `<li>${q}</li>`).join("")}</ol></div>
    ${t.status === "teach" ? `<p class="inspector-note"><strong>Teaching extension</strong><span>ATLAS does not contain this protocol. The lab maps it onto real ATLAS components so students can see where each message would go.</span></p>` : ""}</div>`;
}

// ------------------------------------------------------------------ view + events
const secRenderers = { overview: secOverview, passwords: secPasswords, login: secLogin, identity: secIdentity, gateway: secGateway, sso: secSso, kerberos: secKrb, transport: secTransport, gaps: secGaps };

function securityView() {
  if (!globalThis.crypto?.subtle) {
    return viewHeading("INFORMATION SECURITY", "Security", "Web Crypto is unavailable: open the explorer over HTTPS or on localhost.");
  }
  const t = secTopicById[sec.topic];
  return viewHeading("INFORMATION SECURITY", "How ATLAS is secured", "Authentication, password storage, identity, access control, SSO and Kerberos — traced through the ATLAS code and run live in your browser.", `<a class="panel-badge sec-guide" href="${SEC_GUIDE}">Teaching guide ↗</a>`)
    + `<nav class="sec-topics" aria-label="Security topics">${secTopics.map((x) => `<button type="button" data-sec-topic="${x.id}" data-keep="sec-topic-${x.id}" aria-pressed="${x.id === sec.topic}">${icon(x.icon, 15)}${x.title}${x.status ? `<i class="sec-dot ${secStatus[x.status].tone}" aria-label="${secStatus[x.status].label}"></i>` : ""}</button>`).join("")}</nav>
    <div class="sec-body"><div class="sec-title-row"><h3>${t.title}</h3>${secChip(t.status)}${umlChip(sec.topic === "overview" ? "uml-security-passwords" : `uml-security-${sec.topic}`, "UML catalogue")}</div>${secRenderers[sec.topic]()}${sec.topic === "overview" ? umlTopicsSection("security", secTopics) : umlSection(`security/${sec.topic}`)}</div>`;
}

function securityOpen(topic) {
  sec.topic = secTopicById[topic] ? topic : "overview";
  state.view = "security";
}

function secSetHash() {
  try { history.replaceState(null, "", "#security" + (sec.topic === "overview" ? "" : "-" + sec.topic)); } catch (error) { /* file:// */ }
}

async function secRun(busy, task) {
  sec.busy = busy;
  render();
  try { await task(); } catch (error) { console.error(error); announce("Security lab error: " + error.message); }
  sec.busy = "";
  render();
}

function securityClick(button) {
  const { secTopic, secAction } = button.dataset;
  if (secTopic) {
    sec.topic = secTopic;
    if (state.view !== "security") state.view = "security";
    secSetHash();
    announce("Security topic: " + secTopicById[secTopic].title);
    render();
    return true;
  }
  if (!secAction || sec.busy) return !!secAction;
  const actions = {
    "pw-hash": () => secRun("pw", () => secPwHash(false)),
    "pw-again": () => secRun("pw", () => secPwHash(true)),
    "pw-verify": () => secRun("pwv", secPwVerify),
    "login-init": () => secRun("login", secLoginInit),
    "login-wrong": () => secRun("login", () => secLoginAttempt("aoife@example.ie", "wrong-pass1")),
    "login-unknown": () => secRun("login", () => secLoginAttempt("nobody@example.ie", "cork2026")),
    "login-right": () => secRun("login", () => secLoginAttempt("aoife@example.ie", "cork2026")),
    "login-tick": () => { sec.login.now += 60000; render(); },
    "login-reset": () => secRun("login", secLoginInit),
    "gw-step": () => { const total = secGatewayRun(secGatewayScenarios[sec.gateway.scenario]).steps.length; sec.gateway.step = sec.gateway.step < 0 || sec.gateway.step + 1 >= total ? 0 : sec.gateway.step + 1; render(); },
    "gw-all": () => { sec.gateway.step = -1; render(); },
    "sso-next": () => secRun("sso", secSsoNext),
    "sso-reset": () => { sec.sso.steps = []; sec.sso.ctx = null; render(); },
    "krb-next": () => secRun("krb", secKrbNext),
    "krb-all": () => secRun("krb", async () => { for (let i = 0; i < 8; i++) { const s = sec.krb.steps; if (s.length && s[s.length - 1].done) break; const before = s.length; await secKrbNext(); if (sec.krb.steps.length === before) break; } }),
    "krb-reset": () => { sec.krb.steps = []; sec.krb.ctx = null; render(); },
  };
  actions[secAction]?.();
  return true;
}

document.addEventListener("input", (event) => {
  const name = event.target.dataset?.secInput;
  if (name) sec.fields[name] = event.target.value;
});

document.addEventListener("change", (event) => {
  const name = event.target.dataset?.secSelect;
  if (!name) return;
  if (name === "gateway") { sec.gateway.scenario = event.target.value; sec.gateway.step = 0; }
  if (name === "sso") { sec.sso.scenario = event.target.value; sec.sso.steps = []; sec.sso.ctx = null; }
  if (name === "krb") { sec.krb.scenario = event.target.value; sec.krb.steps = []; sec.krb.ctx = null; }
  render();
});
