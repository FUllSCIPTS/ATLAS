// ATLAS Architecture Explorer — Cryptography view (hashes, checksums, PKI, signatures, post-quantum).
// Loaded after security.js (reuses its helpers: secHex, secRand, secShort, secEsc, secSha256, secChip,
// secCode, secCheck, secTable, secLink, secSection, secStatus) and before explorer.js.
// All cryptography runs in the browser with Web Crypto: SHA-1/256/512, ECDSA P-256, RSA PKCS#1 v1.5.

const cryptoIcons = {
  hash: '<path d="M9 4 7 20M17 4l-2 16M4 9h16M3 15h16"/>',
  cert: '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M7 9h10M7 12h6"/><circle cx="17" cy="17" r="3"/><path d="m15.5 19.5-1 2.5 2.5-1 2.5 1-1-2.5"/>',
  pen: '<path d="M4 20h4L19 9l-4-4L4 16Z"/><path d="m13 7 4 4"/>',
  atom: '<circle cx="12" cy="12" r="1.6"/><ellipse cx="12" cy="12" rx="9" ry="3.6"/><ellipse cx="12" cy="12" rx="9" ry="3.6" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="9" ry="3.6" transform="rotate(120 12 12)"/>',
  upload: '<path d="M12 16V4m-5 5 5-5 5 5M4 20h16"/>',
};

const CR_UPLOAD_CERT_B64 = "MIIFNzCCAx+gAwIBAgIIRkhup1pNI1YwDQYJKoZIhvcNAQEMBQAwSTETMBEGA1UEChMKRlVsbFNDSVBUUzEYMBYGA1UECxMPQW5kcm9pZCBSZWxlYXNlMRgwFgYDVQQDEw9BVExBUyBHbyBVcGxvYWQwIBcNMjYxMTA1MDczMTAyWhgPMjA1OTA5MTMwNzMxMDJaMEkxEzARBgNVBAoTCkZVbGxTQ0lQVFMxGDAWBgNVBAsTD0FuZHJvaWQgUmVsZWFzZTEYMBYGA1UEAxMPQVRMQVMgR28gVXBsb2FkMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA0Zbjd8syKjZGLbpYND1iUNaB5I/ultK4IXBbCLRDIvZeC++4iResFgKcwKXkfTVjXrIIKXnhsArvRh6Tdwai4nI9M+pggD1QpXvN8TirhzM6HxZcS5aSRIwxdZ4di+w25AF+l2WQXQ6eT1xhxICpiYKUc3LzpZDjEgSBZXpqujb5EAFMQbmZEUXDftmncpFoYWw8u0jWDuPEO5tT1MSI/nlrUJpdWxVRJ/Qm8pCEaOiPmFubOxXz58y3rtrQOm/+ZnWOoaJPinadaLrA5syTUr4yVbKH2lXq0mJtsTl+0arDya7tUs2ULtWVtLL+1WiDywsAVM9pjsHbOiJGhrxXglxUimbqdSkvHhrqiWNiDaZjb3zwYBad0gWtf0Oj6cFGLnPNklpUftTYw+EleiE96qXpQm+OpELHfS38tyY5JQ8ixALiQoP7JkvHLjsewSvbob8Ka5ueLzOwm5anx/sRUlJLbJ56XfUSAqPbKOIqCcJy0KeEViImNP0fBQ6yQMz9URmShiekyu5ofIy/VkrsSmYpKP6BHyfZfDU03Ymqf6+uv4vHc+cpPWmNP5CzsMtqXFlcYWlBFVUL8xGZOp3i3e+OSWgwTYYTXFDtaC28NX1gS/Id8ohJ6QaCrd/1utj1EjA8kJdvGngmZcCg2iLnI5nVnN2UCKygawKgo5YB1pMCAwEAAaMhMB8wHQYDVR0OBBYEFOQRJXYi2BM/JAdnigEg7gc0lntaMA0GCSqGSIb3DQEBDAUAA4ICAQCKqLsdlzHXbpuOu3NVn5/nxEFZO947YiHbG1biOWgakV+Wtf+n8F2zffwnEozih8xkBg1wltwSRfKVva+9O6QH/TZAo/Ocb3/TRIq9kWOnKweDXKNpThKrSevdW8UYn2k6zPJjDPq4re+PeLlK4S+/nQzFFlOZt1pUOQkyThDgOuwbbI1/ylsboKdERLZ5fnBVh2d5FO/fC7LHCxEyJsftV2U0IpQ+LhL/cfedvds6i8HFzN1kcvd6ZbmHj4VD39UoFx77CBH8N58sed+OJq6Z8igSF48egwTZISa5YuXEyFMlTPnGBYAcbfpt00FWIqVAM7HKT5MJGUwD0ytg50fyV/DMKTaN+DOnCcIZ64lYFoACRo1M5EiAyH3HFyUmpa4rGUp0K7ehbOCnr1xlqIX2yKDH57AC1HU50PsHHpsovnQjpcZdNfVQyQR5wxAzCu2zNteQaGF8NedJ9g+jGF2OMnmEs+8wFI6fQEcZR4MAeMEPFw+Tp9gBXOW9n6rHYhdY+H/WBnGcE6Z1kEBj6Jp3EUmMaYl71beUUbJdTmQlkRIv0RcBMghGgbBoGJG91xCS6P7syAKxOs0EPOeznpM3jYkqyaZK8LTB0xKppbFFwKpnUx+6MKnQT2VQ0oPsZCUG95x2ai2CArez9v29KSW9H2XxcQzVw1HoQ8JogZXQMA==";
const CR_UPLOAD_PIN = "059076082129b3ed2f08c5b88a207bdebf2bba88304c0821b77d128c034944d7";
const CR_PUBLISHED = [
  ["737c41ec935e4a87d849a04b1434fbe66fa47bdcb9420387e2a94f58400813cb", "atlas-go-1.2.0.apk", "1.2.0"],
  ["603330022c5557da665b56585f20aa75453b6e789e344a11897ce57c43ff1ca7", "atlas-go-1.2.0-unsigned.aab", "1.2.0"],
  ["eaefd2ca3d357e072502deedc378bded7df2c936ee54c708d3ab2e90b9818370", "atlas-go-demo.apk", "1.1.0"],
  ["132a083e7f97219d8ce8616eae12e3f3aeecb37a85d6136a1a538121a7d114c7", "atlas-go-unsigned.aab", "1.1.0"],
  ["9932955f7b078a939f67964d83dc86fa5bdaa2a0c294adf34316dbcebdec216a", "atlas-go-play.aab (signed)", "1.0.0"],
  ["867fc0646a113ce79bbdc43aba2ca1ecf540c27812bb41626f5f34b5e9eee731", "atlas-go-demo.apk", "1.0.0"],
  ["4887149df14fc81662a6ade71bc83a38b24861ba4fcb45fd87974264d4017b40", "atlas-go-unsigned.aab", "1.0.0"],
];

const crTopics = [
  { id: "overview", title: "Crypto map", icon: "shield", status: null },
  { id: "hashes", title: "Hashes & checksums", icon: "hash", status: "impl" },
  { id: "pki", title: "PKI & certificates", icon: "cert", status: "impl" },
  { id: "signatures", title: "Digital signatures", icon: "pen", status: "impl" },
  { id: "pqc", title: "Post-quantum", icon: "atom", status: "teach" },
  { id: "gaps", title: "Gaps & exercises", icon: "bug", status: null },
];
const crTopicById = Object.fromEntries(crTopics.map((t) => [t.id, t]));

const cr = {
  topic: "overview",
  busy: "",
  fields: { hashA: "ATLAS ride R-1001 fare 1250", hashB: "ATLAS ride R-1001 fare 1251", sigMsg: "atlas-go-1.2.0.apk — release build 3" },
  hash: { file: null, swapped: false },
  pin: null,
  pki: { scenario: "normal", root: null, rogue: null, server: null, client: null, result: null },
  sig: { alg: "ecdsa", keys: null, other: null, signature: null, signedMsg: "", results: [], keyMs: 0, signMs: 0, pubBytes: 0 },
  lamport: { keys: null, signs: [], forged: null, verify: null },
};

const CR_SIG_ALGS = {
  ecdsa: { label: "ECDSA P-256 with SHA-256", gen: { name: "ECDSA", namedCurve: "P-256" }, sign: { name: "ECDSA", hash: "SHA-256" }, exp: "spki" },
  rsa: { label: "SHA256withRSA, 2048-bit (as jarsigner, PKCS#1 v1.5)", gen: { name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }, sign: { name: "RSASSA-PKCS1-v1_5" }, exp: "spki" },
};

// ------------------------------------------------------------------ helpers
const crB64ToBytes = (b64) => Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
async function crDigest(alg, data) { return secHex(await crypto.subtle.digest(alg, typeof data === "string" ? new TextEncoder().encode(data) : data)); }
function crBits(hex) { return [...hex].flatMap((h) => parseInt(h, 16).toString(2).padStart(4, "0").split("").map(Number)); }

function crButton(action, label, { primary = false, iconName = "", disabled = false } = {}) {
  return `<button type="button" class="sec-btn${primary ? " primary" : ""}" data-cr-action="${action}" data-keep="cr-${action}"${disabled || cr.busy ? " disabled" : ""}>${iconName ? icon(iconName, 15) : ""}${label}</button>`;
}

function crField(name, label, hint = "") {
  return `<label class="sec-field wide"><span>${label}</span><input data-cr-input="${name}" data-keep="cr-in-${name}" type="text" value="${secEsc(cr.fields[name] ?? "")}" autocomplete="off" spellcheck="false" placeholder="${secEsc(hint)}"></label>`;
}

function crSelect(name, label, options, value) {
  return `<label class="sec-field compact"><span>${label}</span><select data-cr-select="${name}" data-keep="cr-sel-${name}">${options.map(([v, l]) => `<option value="${v}"${v === value ? " selected" : ""}>${l}</option>`).join("")}</select></label>`;
}

// ------------------------------------------------------------------ overview
const crMap = [
  ["learn", "layers", "Foundations: 19 standalone units", null, "RSA, Diffie–Hellman, ECDSA, AES-GCM, ML-KEM, ML-DSA, SLH-DSA — what, why and how, with live labs", "docs/CRYPTOGRAPHY.md"],
  ["hashes", "hash", "SHA-256 release checksums", "impl", "Every release ships SHA256SUMS; users run sha256sum -c", "android-app/releases/*/SHA256SUMS"],
  ["hashes", "hash", "Pinned build tool", "impl", "CI refuses bundletool.jar unless its SHA-256 matches the committed value", ".github/workflows/atlas-android.yml"],
  ["hashes", "layers", "Checksum vs hash", "impl", "Prototype recovery compares (count, total, len): catches lost updates, not tampering", "prototype/module_server.py"],
  ["pki", "cert", "Private CA + mutual TLS", "impl", "Root CA, serverAuth and clientAuth certificates, CERT_REQUIRED, 30 days", "prototype/proto_run.py"],
  ["pki", "cloud", "Web PKI", "impl", "Map tiles over HTTPS, verified against public CAs in certifi", "android-app/atlas_go/livemap.py"],
  ["pki", "key", "Certificate pinning", "impl", "CI recomputes the upload certificate's SHA-256 and fails on any mismatch", "scripts/ci-sign-bundle.py"],
  ["signatures", "pen", "Signed Play bundle", "impl", "jarsigner SHA256withRSA with an RSA-4096 upload key, then verified", "scripts/sign-release.py"],
  ["signatures", "pen", "Signed APK", "impl", "APK Signature Scheme v2 and v3; check with apksigner verify", "releases/1.2.0/"],
  ["pqc", "atom", "Post-quantum", "teach", "Which ATLAS keys Shor would break; ML-KEM, ML-DSA, SLH-DSA; live Lamport signature", "docs/CRYPTOGRAPHY.md §6"],
];

function crOverview() {
  return `<div class="sec-intro"><p>Cryptography in ATLAS protects the <strong>integrity of what users install</strong>, the <strong>identity of processes and servers</strong>, and the <strong>secrecy of passwords</strong>. Each card opens a live lab using the real values from the repository. Post-quantum cryptography is not in ATLAS; its tab shows where it would go.</p>
    <div class="sec-legend">${Object.keys(secStatus).map((k) => `<span>${secChip(k)}<small>${secStatus[k].text}</small></span>`).join("")}</div></div>
    <div class="sec-grid">${crMap.map(([topic, ic, title, status, text, where]) => `<button type="button" class="sec-card" data-cr-topic="${topic}" data-keep="cr-card-${title}"><span class="sec-card-top">${icon(ic, 18)}${secChip(status)}</span><strong>${title}</strong><span>${text}</span><code>${where}</code></button>`).join("")}</div>
    ${secSection("INVENTORY", "Every cryptographic primitive in ATLAS", secTable(["Primitive", "Algorithm", "Where", "Quantum-safe?"], [
      ["Hash", "SHA-256", "SHA256SUMS, CI pins, signing records, blueprint inventory", "Yes (Grover: ~2<sup>128</sup>)"],
      ["Key derivation", "PBKDF2-HMAC-SHA256 × 200 000", "accounts.py (passwords)", "Yes"],
      ["MAC / compare", "HMAC, compare_digest", "accounts.py, starter config.py", "Yes"],
      ["Checksum", "(count, total, len)", "prototype recovery", "Not a security control"],
      ["Certificates", "RSA-2048, X.509 v3", "prototype private CA (mTLS)", "<span class=\"cr-bad\">No — Shor</span>"],
      ["TLS key exchange", "(EC)DHE via OpenSSL", "map tiles, prototype mTLS", "<span class=\"cr-bad\">No — Shor; harvest-now-decrypt-later</span>"],
      ["Code signing", "RSA-4096, SHA256withRSA; APK v2/v3", "upload key (valid to 2059), APK", "<span class=\"cr-bad\">No — Shor</span>"],
    ]))}`;
}

// ------------------------------------------------------------------ hashes
async function crHashFile(file) {
  const t0 = performance.now();
  const sum = await crDigest("SHA-256", await file.arrayBuffer());
  const match = CR_PUBLISHED.find(([h]) => h === sum);
  cr.hash.file = { name: file.name, size: file.size, sum, match, ms: performance.now() - t0 };
}

async function crUpdateAvalanche() {
  const out = document.getElementById("cr-avalanche");
  if (!out) return;
  const [a, b] = await Promise.all([crDigest("SHA-256", cr.fields.hashA), crDigest("SHA-256", cr.fields.hashB)]);
  const ba = crBits(a), bb = crBits(b);
  const diff = ba.filter((bit, i) => bit !== bb[i]).length;
  const s1 = await crDigest("SHA-1", cr.fields.hashA), s512 = await crDigest("SHA-512", cr.fields.hashA);
  out.innerHTML = `<p class="sec-label">SHA-256(A)</p>${secCode(a)}<p class="sec-label">SHA-256(B)</p>${secCode(b)}
    <div class="cr-bitgrid" role="img" aria-label="${diff} of 256 bits differ">${ba.map((bit, i) => `<i class="${bit !== bb[i] ? "on" : ""}"></i>`).join("")}</div>
    <p class="sec-note">${icon("hash", 14)} <strong>${diff} of 256</strong> output bits differ (${(diff / 2.56).toFixed(0)}%). An ideal hash flips about half for any change, so the digest reveals nothing about how similar the inputs were.</p>
    <p class="sec-label">Same input A, other algorithms</p>${secCode(`SHA-1   (160-bit, collisions found in 2017 — do not use) ${s1}\nSHA-512 (512-bit) ${s512}`)}`;
}

async function crChecksum() {
  const honest = { seen: ["p1", "p2", "p3"], total: 3000, count: 3 };
  const state = cr.hash.swapped ? { seen: ["p1", "p2", "pX"], total: 3000, count: 3 } : honest;
  const c = (s) => `(${s.count}, ${s.total}, ${s.seen.length})`;
  const h = async (s) => crDigest("SHA-256", JSON.stringify(s));
  return { cs: c(state), csHonest: c(honest), h: await h(state), hHonest: await h(honest), state };
}

function crHashes() {
  const f = cr.hash.file;
  return `<div class="sec-intro"><p>A cryptographic hash turns any input into a fixed 32-byte fingerprint that is one-way and collision-resistant. ATLAS uses SHA-256 so that users and CI can prove a file is <strong>exactly</strong> the one that was built and tested.</p></div>
  ${secSection("LIVE", "Avalanche effect", `<div class="sec-row">${crField("hashA", "Input A")}${crField("hashB", "Input B — change one character")}</div><div id="cr-avalanche"><p class="sec-note">Computing…</p></div>`)}
  ${secSection("VERIFY A DOWNLOAD", "Check an ATLAS Go file against the published SHA256SUMS", `<p class="sec-text">Choose an APK or AAB you downloaded. Its SHA-256 is computed <strong>in your browser</strong> (nothing is uploaded) and compared with every hash ATLAS has published.</p>
    <label class="cr-drop">${icon("upload", 18)}<span>Choose a file to hash</span><input type="file" data-cr-file="hash" data-keep="cr-file"></label>
    ${cr.busy === "file" ? `<p class="sec-note">Hashing…</p>` : ""}
    ${f ? `${secCode(`${f.sum}  ${f.name}  (${f.size.toLocaleString()} bytes, ${f.ms.toFixed(0)} ms)`)}<ul class="sec-checks">${secCheck(!!f.match, f.match ? `Matches the published SHA-256 for ${f.match[1]} (${f.match[2]})` : "No published ATLAS hash matches", f.match ? "Bit-for-bit the file CI built and tested" : "Corrupted, tampered with, or not an ATLAS release file")}</ul>` : ""}
    ${secTable(["Published SHA-256", "File", "Release"], CR_PUBLISHED.map(([h, n, v]) => [`<code>${secShort(h, 20)}</code>`, n, v]))}
    <p class="sec-label">The same check on the command line</p>${secCode("sha256sum -c SHA256SUMS")}`)}
  ${secSection("CHECKSUM VS HASH", "The prototype's recovery checksum", `<p class="sec-text">After restoring a module, the prototype compares <code>checksum() = (count, total, len(seen))</code> (crash class C3 in <code>run_recovery_mc.py</code>). Swap one payment id and compare.</p>
    <div class="sec-actions">${crButton("swap", cr.hash.swapped ? "Restore honest state" : "Swap payment p3 → pX", { iconName: "reset" })}</div><div id="cr-checksum"><p class="sec-note">Computing…</p></div>`)}
  ${secSection("WHERE ATLAS USES SHA-256", "Four integrity checks", secTable(["Use", "Code", "Fails when"], [
    ["Release checksums", "<code>sha256sum release/*.apk release/*.aab &gt; SHA256SUMS</code>", "A download is corrupted or replaced"],
    ["Pinned build tool", "<code>echo 'a099cfa1…e29  /tmp/bundletool.jar' | sha256sum -c -</code>", "The download server serves a different bundletool"],
    ["Signing record", "<code>actual == record['sha256']</code> (publish-signed-android.yml)", "The signed bundle is not the tested one"],
    ["Blueprint inventory", "<code>hashlib.sha256(path.read_bytes())</code> (generate_blueprint.py)", "Documentation and code drift apart"],
  ]) + secLink(".github/workflows/atlas-android.yml", SEC_MAIN + ".github/workflows/atlas-android.yml") + secLink("android-app/releases/1.2.0/SHA256SUMS", SEC_MAIN + "android-app/releases/1.2.0/SHA256SUMS"))}`;
}

async function crHashesAfterRender() {
  await crUpdateAvalanche();
  const box = document.getElementById("cr-checksum");
  if (!box) return;
  const r = await crChecksum();
  box.innerHTML = `${secTable(["", "seen", "checksum()", "SHA-256 of state"], [
    ["Honest", "p1, p2, p3", `<code>${r.csHonest}</code>`, `<code>${secShort(r.hHonest, 18)}</code>`],
    [cr.hash.swapped ? "Altered" : "Current", r.state.seen.join(", "), `<code>${r.cs}</code>`, `<code>${secShort(r.h, 18)}</code>`],
  ])}<ul class="sec-checks">${secCheck(!cr.hash.swapped || r.cs !== r.csHonest, cr.hash.swapped ? "checksum() is identical — the swap goes unnoticed" : "Same state, same checksum", cr.hash.swapped ? "Fine for detecting a lost update after a crash; useless against a deliberate change" : "")}${secCheck(!cr.hash.swapped || r.h !== r.hHonest, cr.hash.swapped ? "SHA-256 differs — the swap is detected" : "SHA-256 identical for identical state")}</ul>`;
}

// ------------------------------------------------------------------ PKI
async function crPin() {
  const der = crB64ToBytes(CR_UPLOAD_CERT_B64);
  const t0 = performance.now();
  const sum = await crDigest("SHA-256", der);
  cr.pin = { sum, ok: sum === CR_UPLOAD_PIN, bytes: der.length, ms: performance.now() - t0 };
}

const crPkiScenarios = [
  ["normal", "Normal mutual TLS"],
  ["wrongeku", "Client presents the server certificate"],
  ["expired", "Client certificate expired"],
  ["rogue", "Client certificate from an attacker's CA"],
  ["tamper", "Attacker edits CN in a valid certificate"],
  ["leafca", "Server certificate used to issue a new certificate"],
];
const crKeyAlg = { name: "ECDSA", namedCurve: "P-256" };
const crSigAlg = { name: "ECDSA", hash: "SHA-256" };

async function crIssue(issuer, tbs) {
  const pair = await crypto.subtle.generateKey(crKeyAlg, true, ["sign", "verify"]);
  const spki = new Uint8Array(await crypto.subtle.exportKey("spki", pair.publicKey));
  const body = { ...tbs, publicKey: secHex(spki) };
  const signer = issuer ? issuer.privateKey : pair.privateKey;
  const sig = new Uint8Array(await crypto.subtle.sign(crSigAlg, signer, new TextEncoder().encode(JSON.stringify(body))));
  return { body, sig: secHex(sig), privateKey: pair.privateKey, publicKey: pair.publicKey, fp: (await crDigest("SHA-256", JSON.stringify(body) + secHex(sig))).slice(0, 16) };
}

async function crPkiSetup() {
  const now = Math.floor(Date.now() / 1000);
  const day = 86400;
  const P = cr.pki;
  P.root = await crIssue(null, { subject: "CN=atlas-ca", issuer: "CN=atlas-ca", ca: true, keyUsage: ["keyCertSign", "cRLSign"], notBefore: now, notAfter: now + 30 * day });
  P.server = await crIssue(P.root, { subject: "CN=server", san: "IP:127.0.0.1", issuer: "CN=atlas-ca", ca: false, eku: "serverAuth", notBefore: now, notAfter: now + 30 * day });
  P.client = await crIssue(P.root, { subject: "CN=client", issuer: "CN=atlas-ca", ca: false, eku: "clientAuth", notBefore: now, notAfter: now + 30 * day });
  P.rogue = await crIssue(null, { subject: "CN=atlas-ca", issuer: "CN=atlas-ca", ca: true, keyUsage: ["keyCertSign"], notBefore: now, notAfter: now + 30 * day });
  P.result = null;
}

async function crVerifyCert(cert, issuerCert, trusted, wantEku) {
  const checks = [];
  const now = Math.floor(Date.now() / 1000);
  checks.push([cert.body.issuer === issuerCert.body.subject, `Issuer "${cert.body.issuer}" matches CA subject "${issuerCert.body.subject}"`]);
  checks.push([issuerCert.body.ca === true, issuerCert.body.ca ? "Issuer has basicConstraints CA:TRUE" : "Issuer has CA:FALSE — a leaf certificate cannot issue certificates"]);
  const ok = await crypto.subtle.verify(crSigAlg, issuerCert.publicKey, crB64Hex(cert.sig), new TextEncoder().encode(JSON.stringify(cert.body)));
  checks.push([ok, ok ? "Signature verifies with the issuer's public key" : "Signature does NOT verify with the trusted CA's key", ok ? "" : "The certificate was not signed by this CA, or its contents were changed after signing"]);
  const anchored = issuerCert === trusted;
  checks.push([anchored, anchored ? "Issuer is the trust anchor loaded from ca.crt" : "Issuer is not the trust anchor (ca.crt)"]);
  checks.push([cert.body.notBefore <= now && now < cert.body.notAfter, cert.body.notAfter <= now ? "Validity period has ended" : "Within its validity period"]);
  if (wantEku) checks.push([cert.body.eku === wantEku, `Extended key usage: ${cert.body.eku} (needed: ${wantEku})`]);
  return checks;
}
function crB64Hex(hex) { return Uint8Array.from(hex.match(/../g), (h) => parseInt(h, 16)); }

async function crPkiRun() {
  const P = cr.pki;
  if (!P.root) await crPkiSetup();
  const steps = [];
  const s = P.scenario;
  let client = P.client, clientIssuer = P.root;
  if (s === "wrongeku") client = P.server;
  if (s === "expired") { const signed = await crIssue(P.root, { ...P.client.body, notBefore: P.client.body.notBefore - 40 * 86400, notAfter: P.client.body.notBefore - 10 * 86400 }); client = signed; }
  if (s === "rogue") { client = await crIssue(P.rogue, { subject: "CN=client", issuer: "CN=atlas-ca", ca: false, eku: "clientAuth", notBefore: P.client.body.notBefore, notAfter: P.client.body.notAfter }); clientIssuer = P.root; }
  if (s === "tamper") client = { ...P.client, body: { ...P.client.body, subject: "CN=admin" } };
  steps.push({ title: "① Client verifies the server certificate", from: "Module server", to: "Caller", wire: `server presents: ${P.server.body.subject}, ${P.server.body.san}, EKU ${P.server.body.eku}, issuer ${P.server.body.issuer}`, checks: await crVerifyCert(P.server, P.root, P.root, "serverAuth") });
  if (s === "leafca") {
    const forged = await crIssue(P.server, { subject: "CN=client", issuer: "CN=server", ca: false, eku: "clientAuth", notBefore: P.client.body.notBefore, notAfter: P.client.body.notAfter });
    steps.push({ title: "② Server verifies the client certificate", from: "Caller", to: "Module server", wire: `client presents: CN=client, issued by CN=server (the server's own key used as a CA)`, checks: await crVerifyCert(forged, P.server, P.root, "clientAuth") });
  } else {
    steps.push({ title: "② Server verifies the client certificate (CERT_REQUIRED)", from: "Caller", to: "Module server", wire: `client presents: ${client.body.subject}, EKU ${client.body.eku}, issuer ${client.body.issuer}, valid until ${new Date(client.body.notAfter * 1000).toISOString().slice(0, 10)}${s === "rogue" ? "  (signed by the attacker's own 'atlas-ca')" : ""}${s === "tamper" ? "  (CN edited after signing)" : ""}`, checks: await crVerifyCert(client, clientIssuer, P.root, "clientAuth") });
  }
  P.result = steps;
}

function crPki() {
  const P = cr.pki;
  const pin = cr.pin;
  return `<div class="sec-intro"><p>A <strong>private key</strong> stays secret; the matching <strong>public key</strong> is shared. A <strong>certificate</strong> binds a public key to a name and is signed by an issuer. A <strong>PKI</strong> decides which issuers to believe. ATLAS uses three trust models: its own CA, the public Web PKI, and a pinned self-signed certificate.</p></div>
  ${secSection("REAL CERTIFICATE", "The ATLAS Go upload certificate", secTable(["Field", "Value"], [
    ["Subject = Issuer", "O=FUllSCIPTS, OU=Android Release, CN=ATLAS Go Upload (self-signed)"],
    ["Public key", "RSA, 4096 bits"],
    ["Signature algorithm", "sha384WithRSAEncryption"],
    ["Validity", "5 Nov 2026 → 13 Sep 2059"],
    ["Version", "X.509 v3, one extension (subjectKeyIdentifier)"],
    ["Pinned SHA-256", `<code>${secShort(CR_UPLOAD_PIN, 28)}</code> in SIGNED_VALIDATION.json`],
  ]) + `<p class="sec-text">A self-signed certificate has no CA vouching for it, so CI trusts it by <strong>pinning</strong>: it hashes the DER bytes and compares with the committed value. Do the same with the real certificate:</p>
    <div class="sec-actions">${crButton("pin", "Recompute the pin from upload-certificate.pem", { primary: true, iconName: "hash" })}</div>
    ${pin ? `${secCode(`SHA-256(DER, ${pin.bytes} bytes) = ${pin.sum}\npinned                        = ${CR_UPLOAD_PIN}`)}<ul class="sec-checks">${secCheck(pin.ok, pin.ok ? "Match: CI would accept a bundle signed with this certificate" : "Mismatch: CI would fail the job")}</ul>` : ""}
    ${secCode(`# ci-sign-bundle.py
pem = keytool -printcert -rfc -jarfile bundle
fingerprint = hashlib.sha256(ssl.PEM_cert_to_DER_cert(pem)).hexdigest()
assert fingerprint == record['upload_certificate_sha256']`)}${secLink("android-app/releases/upload-certificate.pem", SEC_MAIN + "android-app/releases/upload-certificate.pem")}${secLink("android-app/scripts/ci-sign-bundle.py", SEC_MAIN + "android-app/scripts/ci-sign-bundle.py")}`)}
  ${secSection("LIVE", "Build the prototype's private CA, then connect", `<p class="sec-text">Mirrors <code>proto_run.py</code>: a root CA and two leaves with <code>serverAuth</code> and <code>clientAuth</code>. Keys are real ECDSA P-256 made in your browser; certificates are simplified to JSON instead of X.509 DER so every field is readable.</p>
    <div class="sec-row">${crSelect("pki", "Scenario", crPkiScenarios, P.scenario)}${crButton("pki-run", P.root ? "Run handshake checks" : "Create CA and run", { primary: true, iconName: "play" })}${crButton("pki-reset", "New keys", { iconName: "reset" })}</div>
    ${P.root ? secTable(["Certificate", "Subject", "Issuer", "CA", "Usage", "Fingerprint"], [
      ["Root (ca.crt)", P.root.body.subject, P.root.body.issuer, "TRUE", "keyCertSign, cRLSign", `<code>${P.root.fp}</code>`],
      ["Server", `${P.server.body.subject}, ${P.server.body.san}`, P.server.body.issuer, "FALSE", "serverAuth", `<code>${P.server.fp}</code>`],
      ["Client", P.client.body.subject, P.client.body.issuer, "FALSE", "clientAuth", `<code>${P.client.fp}</code>`],
    ]) : ""}
    ${P.result ? secMessages(P.result) : ""}
    <p class="sec-label">The real commands in proto_run.py</p>${secCode(`openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.crt -days 30 -subj /CN=atlas-ca \\
  -addext basicConstraints=critical,CA:TRUE -addext keyUsage=critical,keyCertSign,cRLSign
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -days 30 -extfile server.ext   # EKU serverAuth, SAN IP:127.0.0.1
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -days 30 -extfile client.ext   # EKU clientAuth
# module_server.py: ctx.load_verify_locations("ca.crt"); ctx.verify_mode = ssl.CERT_REQUIRED`)}`)}
  ${secSection("TRUST MODELS", "Who does ATLAS trust, and why?", secTable(["Model", "In ATLAS", "Trust anchor", "Revocation story"], [
    ["Private CA", "Prototype mTLS", "ca.crt, created per run", "30-day lifetime; delete the CA"],
    ["Web PKI", "Map tiles (requests + certifi)", "~100+ public root CAs", "CRL/OCSP, short lifetimes"],
    ["Pinning", "Upload key in CI", "One SHA-256 committed in Git", "Change the pin; Play upload-key reset"],
  ]))}`;
}

// ------------------------------------------------------------------ signatures
async function crSigKeys() {
  const A = CR_SIG_ALGS[cr.sig.alg];
  const t0 = performance.now();
  cr.sig.keys = await crypto.subtle.generateKey(A.gen, true, ["sign", "verify"]);
  cr.sig.keyMs = performance.now() - t0;
  cr.sig.other = await crypto.subtle.generateKey(A.gen, true, ["sign", "verify"]);
  cr.sig.pubBytes = (await crypto.subtle.exportKey("spki", cr.sig.keys.publicKey)).byteLength;
  cr.sig.pubFp = (await crDigest("SHA-256", await crypto.subtle.exportKey("spki", cr.sig.keys.publicKey))).slice(0, 24);
  cr.sig.signature = null;
  cr.sig.results = [];
}

async function crSigSign() {
  if (!cr.sig.keys) await crSigKeys();
  const A = CR_SIG_ALGS[cr.sig.alg];
  const t0 = performance.now();
  cr.sig.signature = new Uint8Array(await crypto.subtle.sign(A.sign, cr.sig.keys.privateKey, new TextEncoder().encode(cr.fields.sigMsg)));
  cr.sig.signMs = performance.now() - t0;
  cr.sig.signedMsg = cr.fields.sigMsg;
  cr.sig.digest = await crDigest("SHA-256", cr.fields.sigMsg);
  cr.sig.results = [];
}

async function crSigVerify(kind) {
  const A = CR_SIG_ALGS[cr.sig.alg];
  let msg = cr.sig.signedMsg, key = cr.sig.keys.publicKey, sig = cr.sig.signature, label;
  if (kind === "ok") label = "Verify the release as signed";
  if (kind === "edited") { msg = cr.fields.sigMsg === cr.sig.signedMsg ? cr.sig.signedMsg + " " : cr.fields.sigMsg; label = "Verify the release after one byte is changed"; }
  if (kind === "wrongkey") { key = cr.sig.other.publicKey; label = "Verify with someone else's public key"; }
  if (kind === "flip") { sig = sig.slice(); sig[sig.length - 1] ^= 1; label = "Verify after one bit of the signature is flipped"; }
  const ok = await crypto.subtle.verify(A.sign, key, sig, new TextEncoder().encode(msg));
  cr.sig.results.unshift([ok, `${label} → ${ok ? "VALID" : "INVALID"}`, ok ? "Only the private-key holder could have produced this, and the bytes are unchanged" : kind === "edited" ? "The SHA-256 of the data changed, so the signature no longer matches" : kind === "wrongkey" ? "Authenticity: the signature binds to one specific key pair" : "The signature value itself is integrity-checked"]);
  cr.sig.results = cr.sig.results.slice(0, 6);
}

function crSignatures() {
  const S = cr.sig;
  return `<div class="sec-intro"><p>A digital signature proves <strong>integrity</strong> (the bytes did not change) and <strong>authenticity</strong> (the private-key holder produced them), and anyone can check it with the public key. It is computed over a SHA-256 <strong>hash</strong> of the data — hash-then-sign. ATLAS signs every Android release this way.</p></div>
  ${secSection("LIVE", "Sign a release and try to break it", `<div class="sec-row">${crSelect("sig", "Algorithm", Object.entries(CR_SIG_ALGS).map(([k, v]) => [k, v.label]), S.alg)}${crButton("sig-keys", S.keys ? "New key pair" : "Generate key pair", { iconName: "key" })}</div>
    ${S.keys ? secCode(`private key  stays in the keystore (non-extractable in real use)\npublic key   ${S.pubBytes} bytes SPKI, SHA-256 fingerprint ${S.pubFp}…\nkey pair generated in ${S.keyMs.toFixed(0)} ms`) : ""}
    <div class="sec-row">${crField("sigMsg", "Release content (stand-in for the APK bytes)")}${crButton("sig-sign", "Sign", { primary: true, iconName: "pen" })}</div>
    ${S.signature ? `${secCode(`SHA-256(release) = ${S.digest}\nsignature        = ${secShort(secHex(S.signature), 64)}  (${S.signature.length} bytes, ${S.signMs.toFixed(1)} ms)`)}
      <div class="sec-actions">${crButton("sig-v-ok", "Verify", { iconName: "check" })}${crButton("sig-v-edited", "Change the release, verify", { iconName: "cross" })}${crButton("sig-v-wrongkey", "Verify with another key", { iconName: "key" })}${crButton("sig-v-flip", "Flip a signature bit, verify", { iconName: "bug" })}</div>
      <ul class="sec-checks">${S.results.map(([ok, t, d]) => secCheck(ok, t, d)).join("")}</ul>` : ""}`)}
  ${secSection("IN ATLAS", "How a release is signed", `<ol class="sec-flow">${[
    ["Build and test", "atlas-android.yml", "Unsigned AAB; SHA-256 recorded"],
    ["Sign", "jarsigner -sigalg SHA256withRSA -digestalg SHA-256", "RSA-4096 upload key from a PKCS#12 keystore; passwords passed by env name"],
    ["Verify", "jarsigner -verify", "Run immediately after signing"],
    ["Pin check", "SHA-256(certificate) == pinned", "Any other key fails the job"],
    ["Distribute", "APK v2 + v3, SHA256SUMS", "User runs apksigner verify --print-certs"],
  ].map(([t, c, d], i) => `<li><span class="sec-flow-n">${i + 1}</span><strong>${t}</strong><code>${c}</code><small>${d}</small></li>`).join("")}</ol>
    ${secTable(["Artefact", "Scheme", "What is signed"], [
      ["Play bundle (.aab)", "JAR signing, SHA256withRSA (PKCS#1 v1.5)", "SHA-256 of each entry in META-INF/MANIFEST.MF, then the manifest"],
      ["Installable APK", "APK Signature Scheme v2 and v3", "The whole file (v2); v3 adds key rotation"],
    ])}${secLink("android-app/scripts/sign-release.py", SEC_MAIN + "android-app/scripts/sign-release.py")}${secLink("android-app/releases/1.2.0/README.md", SEC_MAIN + "android-app/releases/1.2.0/README.md")}`)}`;
}

// ------------------------------------------------------------------ PQC (Lamport one-time signature)
async function crLamportKeys() {
  const sk = [], pk = [];
  for (let i = 0; i < 256; i++) {
    const a = secRand(32), b = secRand(32);
    sk.push([a, b]);
    pk.push([new Uint8Array(await crypto.subtle.digest("SHA-256", a)), new Uint8Array(await crypto.subtle.digest("SHA-256", b))]);
  }
  cr.lamport = { keys: { sk, pk, fp: (await crDigest("SHA-256", new Uint8Array(pk.flatMap(([a, b]) => [...a, ...b])))).slice(0, 16) }, signs: [], forged: null, verify: null };
}
async function crMsgBits(text) { return crBits(await crDigest("SHA-256", text)); }
async function crLamportSign(text) {
  const bits = await crMsgBits(text);
  return { text, bits, sig: bits.map((b, i) => cr.lamport.keys.sk[i][b]) };
}
async function crLamportVerify(text, sig) {
  const bits = await crMsgBits(text);
  for (let i = 0; i < 256; i++) {
    const h = new Uint8Array(await crypto.subtle.digest("SHA-256", sig[i]));
    if (!secEqual(h, cr.lamport.keys.pk[i][bits[i]])) return false;
  }
  return true;
}
function crLamportKnown() {
  const known = Array.from({ length: 256 }, () => [false, false]);
  for (const s of cr.lamport.signs) s.bits.forEach((b, i) => { known[i][b] = true; });
  return known;
}
async function crLamportForge() {
  const known = crLamportKnown();
  const t0 = performance.now();
  for (let n = 0; n < 20000; n++) {
    const text = `atlas-go-1.2.0-malicious-${n}.apk`;
    const bits = await crMsgBits(text);
    if (bits.every((b, i) => known[i][b])) {
      const sig = bits.map((b, i) => cr.lamport.signs.find((s) => s.bits[i] === b).sig[i]);
      cr.lamport.forged = { text, tries: n + 1, ok: await crLamportVerify(text, sig), ms: performance.now() - t0 };
      return;
    }
  }
  cr.lamport.forged = { text: null, tries: 20000, ok: false, ms: performance.now() - t0 };
}

function crPqc() {
  const L = cr.lamport;
  const known = L.keys ? crLamportKnown() : null;
  const both = known ? known.filter(([a, b]) => a && b).length : 0;
  const single = known ? known.filter(([a, b]) => a !== b).length : 0;
  const sizes = [["RSA-4096 (ATLAS upload key)", 512, 512, "bad"], ["ECDSA P-256", 64, 64, "bad"], ["ML-DSA-65 (FIPS 204)", 1952, 3309, "ok"], ["SLH-DSA-SHA2-128s (FIPS 205)", 32, 7856, "ok"], ["Lamport one-time (this lab)", 16384, 8192, "ok"]];
  const max = 16384;
  return `<div class="sec-intro"><p><strong>Not in the ATLAS code.</strong> A large quantum computer running <strong>Shor's algorithm</strong> breaks RSA and elliptic curves — every public key in ATLAS. <strong>Grover's algorithm</strong> only square-roots the cost of attacking hashes, so SHA-256, HMAC and PBKDF2 stay safe. This tab maps that onto ATLAS and runs a signature scheme built only from SHA-256.</p></div>
  ${secSection("IMPACT ON ATLAS", "What a quantum computer would break", secTable(["ATLAS component", "Primitive", "Quantum impact", "Migration"], [
    ["Release checksums, CI pins", "SHA-256", "Safe (preimage ~2<sup>128</sup>)", "None"],
    ["Password storage", "PBKDF2-HMAC-SHA256", "Safe", "Raise iterations (classical advice)"],
    ["Map tiles, prototype mTLS — key exchange", "(EC)DHE", "<span class=\"cr-bad\">Broken; recorded traffic decryptable later</span>", "Hybrid X25519 + ML-KEM-768 (FIPS 203)"],
    ["Prototype mTLS — certificates", "RSA-2048", "<span class=\"cr-bad\">Forgeable</span>", "ML-DSA (FIPS 204) certificates"],
    ["Upload key, valid to 2059", "RSA-4096", "<span class=\"cr-bad\">Forgeable — longest-lived key in ATLAS</span>", "Rotate (APK v3) to a PQ scheme once Android supports one"],
  ]))}
  ${secSection("SIZES", "Public key and signature sizes (bytes)", `<div class="cr-bars">${sizes.map(([n, pk, sg, tone]) => `<div class="cr-bar-row"><span>${n}</span><div class="cr-bar-track"><i class="cr-bar pk" style="width:${Math.max(0.6, (pk / max) * 82)}%"></i><b>${pk.toLocaleString()}</b></div><div class="cr-bar-track"><i class="cr-bar sg ${tone}" style="width:${Math.max(0.6, (sg / max) * 82)}%"></i><b>${sg.toLocaleString()}</b></div></div>`).join("")}<p class="sec-note"><i class="cr-key pk"></i> public key <i class="cr-key sg"></i> signature — classical schemes are tiny but quantum-breakable; post-quantum schemes trade size for safety.</p></div>`)}
  ${secSection("LIVE", "Lamport one-time signature — the idea behind SLH-DSA", `<p class="sec-text">Private key: 256 pairs of random 32-byte values. Public key: their SHA-256 hashes. To sign, hash the message and reveal one value per bit. Security rests only on SHA-256 — no factoring, no curves.</p>
    <div class="sec-actions">${crButton("lam-keys", L.keys ? "New key pair" : "Generate Lamport keys", { primary: !L.keys, iconName: "key" })}${L.keys ? crButton("lam-sign", L.signs.length ? "Sign another release (reuse key!)" : "Sign atlas-go-1.2.0.apk", { primary: true, iconName: "pen" }) : ""}${L.signs.length ? crButton("lam-verify", "Verify, then tamper", { iconName: "check" }) : ""}${L.signs.length >= 2 ? crButton("lam-forge", "Try to forge a malicious release", { iconName: "bug" }) : ""}</div>
    ${cr.busy === "lam" ? `<p class="sec-note">Hashing…</p>` : ""}
    ${L.keys ? secCode(`private key  512 × 32 bytes = 16,384 bytes\npublic key   512 × 32 bytes = 16,384 bytes (fingerprint ${L.keys.fp}…)\nsignatures made with this key: ${L.signs.length}`) : ""}
    ${L.verify ? `<ul class="sec-checks">${secCheck(L.verify[0], `Verify "${L.signs[0].text}" → ${L.verify[0] ? "VALID" : "INVALID"}`)}${secCheck(!L.verify[1], `Verify the same signature on "${L.signs[0].text}x" → ${L.verify[1] ? "VALID" : "INVALID"}`, "Different hash bits select different public-key halves")}</ul>` : ""}
    ${L.keys && L.signs.length ? `<p class="sec-label">Secret halves revealed so far (per bit position)</p><div class="cr-bitgrid lam" role="img" aria-label="${both} positions fully revealed">${known.map(([a, b]) => `<i class="${a && b ? "both" : a || b ? "one" : ""}"></i>`).join("")}</div><p class="sec-note"><i class="cr-key one"></i> one half known <i class="cr-key both"></i> both halves known: <strong>${both}</strong> of 256. A message is forgeable when every bit it needs is known; chance ≈ 2<sup>−${single}</sup>.</p>` : ""}
    ${L.forged ? `<ul class="sec-checks">${secCheck(!L.forged.ok, L.forged.ok ? `FORGED a valid signature for "${L.forged.text}" after ${L.forged.tries.toLocaleString()} tries (${(L.forged.ms / 1000).toFixed(1)} s)` : `No forgery in ${L.forged.tries.toLocaleString()} tries — reuse the key a few more times and try again`, L.forged.ok ? "Key reuse destroyed security. One-time means one time; SLH-DSA uses a hash tree of many one-time keys." : `${single} positions still have only one known half`)}</ul>` : ""}`)}
  ${secSection("STANDARDS", "NIST post-quantum standards (August 2024)", secTable(["Standard", "Algorithm", "Type", "Basis", "Where it would fit in ATLAS"], [
    ["FIPS 203", "ML-KEM", "Key encapsulation", "Module lattices", "TLS for tiles, gateway and service mTLS (hybrid with X25519)"],
    ["FIPS 204", "ML-DSA", "Signature", "Module lattices", "mTLS certificates; future app signing"],
    ["FIPS 205", "SLH-DSA", "Signature", "Hash functions only", "Long-lived roots of trust, e.g. a release-signing root"],
    ["Draft FIPS 206", "FN-DSA (Falcon)", "Signature", "NTRU lattices", "Compact certificate chains, once final"],
    ["Selected March 2025", "HQC", "Key encapsulation", "Error-correcting codes", "Backup KEM if lattices were ever broken"],
  ]) + `<p class="sec-note">${icon("atom", 14)} Hybrid KEM: combine a classical and a post-quantum shared secret with a KDF, so a session stays secure if either one holds. Browsers already negotiate <strong>X25519MLKEM768</strong> in TLS 1.3.</p>
    <p class="sec-note">${icon("clock", 14)} <strong>Deadlines.</strong> NIST IR 8547 (final, October 2026) deprecates RSA, finite-field and elliptic-curve Diffie–Hellman, ECDSA and EdDSA after 2030 and disallows them after 2035, at every key size.</p>
    <p class="sec-note">${icon("layers", 14)} How ML-KEM, ML-DSA and SLH-DSA work, with live toy versions: <button type="button" class="sec-inline-link fd-link" data-cr-topic="learn">Foundations → C10.1–C10.5</button></p>`)}`;
}

// ------------------------------------------------------------------ gaps
function crGaps() {
  return `<div class="sec-intro"><p>Observations about ATLAS's cryptography, each a self-contained assignment.</p></div>
  ${secTable(["#", "Observation", "Where", "Exercise"], [
    ["1", "Recovery checksum is not collision-resistant", "prototype/module_server.py", "Replace with SHA-256 over a canonical snapshot; measure the cost"],
    ["2", "SHA256SUMS is not itself signed", "android-app/releases/", "Sign it so the checksum file cannot be swapped with the download"],
    ["3", "Upload certificate valid until 2059", "upload-certificate.pem", "Discuss key lifetime, APK v3 rotation and quantum exposure"],
    ["4", "Tile requests trust the whole Web PKI", "livemap.py", "Discuss pinning for an operator back end, and its failure modes"],
    ["5", "Service traffic in the starter is plain HTTP", "starter/compose.yaml", "Reuse the prototype's private CA for mTLS"],
    ["6", "No machine-readable crypto inventory", "—", "Add the inventory to CI: the first step of a post-quantum migration"],
  ])}
  ${secSection("LESSON PLAN", "Six sessions built on ATLAS", secTable(["Session", "Topic", "Use"], [
    ["1", "Hash functions", "Hashes tab: avalanche; verify a real APK"],
    ["2", "Checksums, hashes, MACs", "Swap a payment; crypto lab 4, 5, 8, 9"],
    ["3", "Keys and certificates", "PKI tab: build a CA, run every scenario"],
    ["4", "Trust models", "Private CA vs Web PKI vs pinning; recompute the pin"],
    ["5", "Digital signatures", "Signatures tab: ECDSA vs RSA sizes; tamper; crypto lab 15-17"],
    ["6", "Post-quantum", "Lamport: sign, reuse, forge; crypto lab 18-20; plan ATLAS's migration"],
    ["Any", "Foundations", "Pre-read the matching standalone unit (C1–C10.5) and run its live lab"],
  ]))}
  <p class="sec-note">Full write-up: <a class="sec-inline-link" href="${SEC_MAIN}docs/CRYPTOGRAPHY.md">docs/CRYPTOGRAPHY.md</a> · lab: <a class="sec-inline-link" href="${SEC_MAIN}security_lab/README.md">security_lab/ (20 experiments in five files)</a></p>`;
}

// ------------------------------------------------------------------ inspector
const SEC_CRYPTO_GUIDE = SEC_MAIN + "docs/CRYPTOGRAPHY.md";
const crInspect = {
  overview: { summary: "Hashes guard what users install, certificates identify processes and servers, signatures prove who built a release.", files: [["docs/CRYPTOGRAPHY.md", SEC_CRYPTO_GUIDE], ["security_lab/crypto_lab.py", SEC_MAIN + "security_lab/crypto_lab.py"]], facts: [["Hash", "SHA-256"], ["Signatures", "RSA-4096 · SHA256withRSA · APK v2/v3"], ["PKI", "Private CA · Web PKI · pinning"], ["PQC", "Teaching extension"]], questions: ["Which ATLAS key would you rotate first, and why?", "Which uses need integrity only, and which need authenticity?"] },
  hashes: { summary: "SHA-256 gives every file a fingerprint; a checksum only catches accidents.", files: [["android-app/releases/1.2.0/SHA256SUMS", SEC_MAIN + "android-app/releases/1.2.0/SHA256SUMS"], [".github/workflows/atlas-android.yml", SEC_MAIN + ".github/workflows/atlas-android.yml"], ["android-app/scripts/finalize-handover.py", SEC_MAIN + "android-app/scripts/finalize-handover.py"], ["run_recovery_mc.py (class C3)", SEC_MAIN + "run_recovery_mc.py"]], facts: [["Algorithm", "SHA-256 (FIPS 180-4)"], ["Output", "32 bytes"], ["Release files", "APK, AAB"], ["Tool pin", "bundletool 1.18.3"]], questions: ["Why must the expected hash come from a different channel than the file?", "Why is the prototype's checksum adequate for crash recovery but not for security?", "Why is SHA-1 no longer acceptable?"] },
  pki: { summary: "Three trust models: a private CA for mTLS, the public Web PKI for tiles, and a pinned self-signed certificate for signing.", files: [["prototype.zip → proto_run.py", SEC_MAIN + "prototype.zip"], ["android-app/releases/upload-certificate.pem", SEC_MAIN + "android-app/releases/upload-certificate.pem"], ["android-app/releases/SIGNED_VALIDATION.json", SEC_MAIN + "android-app/releases/SIGNED_VALIDATION.json"], ["android-app/atlas_go/livemap.py", SEC_MAIN + "android-app/atlas_go/livemap.py"]], facts: [["Prototype CA", "RSA-2048, 30 days"], ["Leaves", "serverAuth / clientAuth"], ["Upload cert", "RSA-4096, to 2059"], ["Pin", "059076…44d7"]], questions: ["What does basicConstraints CA:FALSE prevent?", "Why can a pinned self-signed certificate be safer than the Web PKI here?", "What is lost if the upload key leaks, and how is it recovered?"] },
  signatures: { summary: "Hash-then-sign with the private key; anyone verifies with the public key.", files: [["android-app/scripts/sign-release.py", SEC_MAIN + "android-app/scripts/sign-release.py"], ["android-app/scripts/ci-sign-bundle.py", SEC_MAIN + "android-app/scripts/ci-sign-bundle.py"], ["android-app/docs/GOOGLE_PLAY.md", SEC_MAIN + "android-app/docs/GOOGLE_PLAY.md"]], facts: [["AAB", "SHA256withRSA, RSA-4096"], ["APK", "Scheme v2 + v3"], ["Key store", "PKCS#12 / Actions secret"], ["Private key in repo", "Never"]], questions: ["Why sign the hash rather than the whole file?", "What does a checksum add that a signature does not, and vice versa?", "Why does the two-key model (upload vs app signing) reduce risk?"] },
  pqc: { summary: "Shor breaks every public key in ATLAS; SHA-256-based tools survive. Hash-based signatures need only a secure hash.", files: [["docs/CRYPTOGRAPHY.md §6", SEC_CRYPTO_GUIDE + "#6-post-quantum-cryptography--teaching-extension"], ["security_lab/crypto_lab.py §6", SEC_MAIN + "security_lab/crypto_lab.py"]], facts: [["KEM", "ML-KEM (FIPS 203)"], ["Signatures", "ML-DSA (204), SLH-DSA (205)"], ["Lamport pk", "16 KB"], ["Lamport sig", "8 KB, one-time"]], questions: ["Why is 'harvest now, decrypt later' a threat to location data today?", "Why is a one-time signature key unsafe to reuse?", "Why use a hybrid KEM during migration?"] },
  gaps: { summary: "Six observations, each a self-contained assignment.", files: [["docs/CRYPTOGRAPHY.md §7", SEC_CRYPTO_GUIDE + "#7-known-gaps--exercises-for-students"]], facts: [["Exercises", "6"], ["Sessions", "6"]], questions: ["Which gap matters most for users installing the APK?"] },
};

function cryptoInspector() {
  const t = crTopicById[cr.topic];
  const info = crInspect[cr.topic];
  return `<div class="inspector-head"><span>${icon("key", 16)} CRYPTO INSPECTOR</span><span class="status-dot" aria-hidden="true"></span></div>
    <div class="inspector-body" style="--accent:${t.status === "teach" ? "#c4aeff" : "#c2f77a"}"><div class="inspector-identity"><span class="component-icon">${icon(t.icon, 23)}</span><div><p>${t.status ? secStatus[t.status].label : "Overview"}</p><h2 id="component-title" tabindex="-1">${t.title}</h2></div></div>
    <p class="inspector-summary">${info.summary}</p>
    <dl class="sec-facts">${info.facts.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("")}</dl>
    <div class="connection-group"><h3>Where in the code</h3>${info.files.map(([l, u]) => secLink(l, u)).join("")}</div>
    ${umlInspector(`crypto/${cr.topic}`, "crypto", crTopics)}
    <div class="connection-group"><h3>Questions for students</h3><ol class="sec-questions">${info.questions.map((q) => `<li>${q}</li>`).join("")}</ol></div>
    ${t.status === "teach" ? `<p class="inspector-note"><strong>Teaching extension</strong><span>ATLAS contains no post-quantum cryptography. This tab shows where it would apply.</span></p>` : ""}</div>`;
}

// ------------------------------------------------------------------ view + events
const crRenderers = { overview: crOverview, hashes: crHashes, pki: crPki, signatures: crSignatures, pqc: crPqc, gaps: crGaps };

function cryptoView() {
  if (!globalThis.crypto?.subtle) return viewHeading("CRYPTOGRAPHY", "Cryptography", "Web Crypto is unavailable: open the explorer over HTTPS or on localhost.");
  const t = crTopicById[cr.topic];
  if (cr.topic === "hashes") setTimeout(crHashesAfterRender, 0);
  return viewHeading("CRYPTOGRAPHY", "How ATLAS uses cryptography", "Hashes and checksums, keys and certificates, digital signatures and post-quantum cryptography — traced through the ATLAS code and run live in your browser.", `<a class="panel-badge sec-guide" href="${SEC_CRYPTO_GUIDE}">Teaching guide ↗</a>`)
    + `<nav class="sec-topics" aria-label="Cryptography topics">${crTopics.map((x) => `<button type="button" data-cr-topic="${x.id}" data-keep="cr-topic-${x.id}" aria-pressed="${x.id === cr.topic}">${icon(x.icon, 15)}${x.title}${x.status ? `<i class="sec-dot ${secStatus[x.status].tone}" aria-label="${secStatus[x.status].label}"></i>` : ""}</button>`).join("")}</nav>
    <div class="sec-body"><div class="sec-title-row"><h3>${t.title}</h3>${secChip(t.status)}${umlChip(cr.topic === "overview" ? "uml-crypto-hashes" : `uml-crypto-${cr.topic}`, "UML catalogue")}</div>${crRenderers[cr.topic]()}${cr.topic === "overview" ? umlTopicsSection("crypto", crTopics) : umlSection(`crypto/${cr.topic}`)}</div>`;
}

function cryptoOpen(topic) {
  cr.topic = crTopicById[topic] ? topic : "overview";
  state.view = "crypto";
}

function crSetHash() {
  try { history.replaceState(null, "", "#crypto" + (cr.topic === "overview" ? "" : "-" + cr.topic)); } catch (error) { /* file:// */ }
}

async function crRun(busy, task) {
  cr.busy = busy;
  render();
  try { await task(); } catch (error) { console.error(error); announce("Cryptography lab error: " + error.message); }
  cr.busy = "";
  render();
}

function cryptoClick(button) {
  const { crTopic, crAction } = button.dataset;
  if (crTopic) {
    cr.topic = crTopic;
    state.view = "crypto";
    crSetHash();
    announce("Cryptography topic: " + crTopicById[crTopic].title);
    render();
    return true;
  }
  if (!crAction || cr.busy) return !!crAction;
  const actions = {
    swap: () => { cr.hash.swapped = !cr.hash.swapped; render(); },
    pin: () => crRun("pin", crPin),
    "pki-run": () => crRun("pki", crPkiRun),
    "pki-reset": () => crRun("pki", async () => { await crPkiSetup(); await crPkiRun(); }),
    "sig-keys": () => crRun("sig", crSigKeys),
    "sig-sign": () => crRun("sig", crSigSign),
    "sig-v-ok": () => crRun("sig", () => crSigVerify("ok")),
    "sig-v-edited": () => crRun("sig", () => crSigVerify("edited")),
    "sig-v-wrongkey": () => crRun("sig", () => crSigVerify("wrongkey")),
    "sig-v-flip": () => crRun("sig", () => crSigVerify("flip")),
    "lam-keys": () => crRun("lam", crLamportKeys),
    "lam-sign": () => crRun("lam", async () => { const n = cr.lamport.signs.length; cr.lamport.signs.push(await crLamportSign(n ? `atlas-go-1.2.${n}.apk` : "atlas-go-1.2.0.apk")); cr.lamport.forged = null; }),
    "lam-verify": () => crRun("lam", async () => { const s = cr.lamport.signs[0]; cr.lamport.verify = [await crLamportVerify(s.text, s.sig), await crLamportVerify(s.text + "x", s.sig)]; }),
    "lam-forge": () => crRun("lam", crLamportForge),
  };
  actions[crAction]?.();
  return true;
}

document.addEventListener("input", (event) => {
  const name = event.target.dataset?.crInput;
  if (!name) return;
  cr.fields[name] = event.target.value;
  if (name === "hashA" || name === "hashB") crUpdateAvalanche();
});

document.addEventListener("change", (event) => {
  const { crSelect: sel, crFile } = event.target.dataset || {};
  if (crFile && event.target.files?.[0]) { crRun("file", () => crHashFile(event.target.files[0])); return; }
  if (!sel) return;
  if (sel === "pki") { cr.pki.scenario = event.target.value; cr.pki.result = null; }
  if (sel === "sig") { cr.sig.alg = event.target.value; cr.sig.keys = null; cr.sig.signature = null; cr.sig.results = []; }
  render();
});
