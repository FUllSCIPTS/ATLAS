"""Build the Security & cryptography catalogue for the UML blueprint and the explorer.

One table below maps every security and cryptography concept taught in the Architecture
Explorer (Security and Cryptography tabs) to the function, constant or file that implements it.
The script resolves current line numbers and writes:

  docs/UML_BLUEPRINT.md   block between <!-- BEGIN/END SECURITY CATALOG --> with one anchor per row
  ../dist/uml-catalog.js  the same rows for the explorer, so each lab links to its catalogue entry

Android app, research and workflow files live on the `main` branch; pass a checkout of it:

    python scripts/security_catalog.py --main ../../ATLAS-main
    python scripts/security_catalog.py --main ../../ATLAS-main --check   # fail if stale
"""
import argparse
import ast
import io
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # architecture-explorer/starter
EXPLORER = ROOT.parent                               # architecture-explorer
REPO = EXPLORER.parent                               # repository root (architecture-explorer branch)
MARKDOWN = ROOT / "docs/UML_BLUEPRINT.md"
SCRIPT_OUT = EXPLORER / "dist/uml-catalog.js"
BLUEPRINT_URL = "https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md"
MAIN_URL = "https://github.com/FUllSCIPTS/ATLAS/blob/main/"
ARCH_URL = "https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/"
EXPLORER_URL = "https://fullscipts.github.io/ATLAS/"
STATUS = {"impl": "Implemented", "demo": "Demo-grade", "teach": "Teaching extension", "lab": "Explorer / lab"}

# Locations. "main:" = file on the main branch; "arch:" = file in architecture-explorer/;
# "zip:" = file inside prototype.zip on main. Symbol "=NAME" finds an assignment, "~REGEX" a line.
ROWS = [
    # id, concept, location, symbol, status
    # ---- Security: password storage
    ("sec-pw-params", "Work factor and lockout limits", "main:android-app/atlas_go/accounts.py", "=PBKDF2_ITERATIONS", "impl"),
    ("sec-pw-hash", "Hash a password (salt + PBKDF2-HMAC-SHA256)", "main:android-app/atlas_go/accounts.py", "hash_password", "impl"),
    ("sec-pw-verify", "Verify a password (constant-time compare)", "main:android-app/atlas_go/accounts.py", "verify_password", "impl"),
    ("sec-pw-policy", "Password policy (8–128, letter + digit)", "main:android-app/atlas_go/accounts.py", "check_password", "impl"),
    ("sec-pw-public", "Strip salt and hash before display", "main:android-app/atlas_go/accounts.py", "public_view", "impl"),
    ("sec-pw-register", "Store only {salt, hash, iterations} at registration", "main:android-app/atlas_go/store.py", "LocalStore.register", "impl"),
    ("sec-pw-test", "Test: same password, different salts and hashes", "main:android-app/tests/test_accounts_geo.py", "test_password_hash_roundtrip_and_salt", "impl"),
    ("sec-pw-lab", "Explorer lab: PBKDF2 with the app's parameters", "arch:dist/security.js", "secPwHash", "lab"),
    ("sec-pw-lab-verify", "Explorer lab: verify_password replica", "arch:dist/security.js", "secPwVerify", "lab"),
    ("sec-pw-cli", "Command-line lab: salts, cost per guess, dictionary attack", "main:security_lab/password_storage_demo.py", "main", "lab"),
    # ---- Security: login and lockout
    ("sec-login", "Sign in, 5 failures → 60 s lockout, generic error", "main:android-app/atlas_go/store.py", "LocalStore.login", "impl"),
    ("sec-login-failures", "Failure counter kept in memory only", "main:android-app/atlas_go/store.py", "~self.failures = \\{\\}", "impl"),
    ("sec-login-session", "Session validated on load (must name an account)", "main:android-app/atlas_go/store.py", "LocalStore.validate", "impl"),
    ("sec-login-guest", "Guest mode (no identity, least privilege)", "main:android-app/atlas_go/store.py", "LocalStore.continue_as_guest", "impl"),
    ("sec-login-logout", "Sign out", "main:android-app/atlas_go/store.py", "LocalStore.logout", "impl"),
    ("sec-login-clear", "Clear the password field after submit", "main:android-app/atlas_go/app.py", "AtlasGoApp.submit_login", "impl"),
    ("sec-login-lab", "Explorer lab: LocalStore.login replica", "arch:dist/security.js", "secLoginAttempt", "lab"),
    # ---- Security: identity and roles
    ("sec-id-email", "Identity proofing: email format", "main:android-app/atlas_go/accounts.py", "clean_email", "impl"),
    ("sec-id-phone", "Identity proofing: phone normalised to E.164", "main:android-app/atlas_go/accounts.py", "clean_phone", "impl"),
    ("sec-id-licence", "Driver licence number (self-declared)", "main:android-app/atlas_go/accounts.py", "clean_licence", "impl"),
    ("sec-id-business", "Food-business number (self-declared)", "main:android-app/atlas_go/accounts.py", "clean_business", "impl"),
    ("sec-id-delete", "De-provision with re-authentication, anonymise history", "main:android-app/atlas_go/store.py", "LocalStore.delete_account", "impl"),
    ("sec-rbac-screens", "RBAC layer 1: screen allow-list per role", "main:android-app/atlas_go/app.py", "AtlasGoApp.render", "impl"),
    ("sec-rbac-online", "RBAC layer 2: only drivers go online", "main:android-app/atlas_go/store.py", "LocalStore.set_online", "impl"),
    ("sec-rbac-location", "RBAC layer 2: only drivers share location", "main:android-app/atlas_go/store.py", "LocalStore.update_location", "impl"),
    ("sec-rbac-respond", "RBAC layer 2: a driver answers only their own job", "main:android-app/atlas_go/store.py", "LocalStore.driver_respond", "impl"),
    ("sec-rbac-book", "RBAC layer 2: only passengers or guests book", "main:android-app/atlas_go/store.py", "LocalStore.book", "impl"),
    ("sec-rbac-checkout", "RBAC layer 2: only passengers or guests order food", "main:android-app/atlas_go/store.py", "LocalStore.checkout", "impl"),
    ("sec-rbac-kitchen", "RBAC layer 2: a seller edits only their own kitchen", "main:android-app/atlas_go/store.py", "LocalStore._my_kitchen", "impl"),
    # ---- Security: gateway authentication
    ("sec-gw-routes", "Route allow-list (method, role, regex)", "arch:starter/services/gateway.py", "=ROUTES", "demo"),
    ("sec-gw-proxy", "Authenticate, check role, assert identity, forward", "arch:starter/services/gateway.py", "proxy", "demo"),
    ("sec-gw-keys", "Bearer keys per actor (demo defaults)", "arch:starter/packages/config.py", "=KEYS", "demo"),
    ("sec-gw-equal", "Timing-safe comparison (hmac.compare_digest)", "arch:starter/packages/config.py", "equal", "demo"),
    ("sec-gw-internal", "Service re-check: internal token and actor role", "arch:starter/packages/config.py", "internal_actor", "demo"),
    ("sec-gw-trips", "Trip Service accepts only gateway-asserted riders", "arch:starter/services/trips.py", "book", "demo"),
    ("sec-gw-dispatch", "Dispatch Service accepts only gateway-asserted drivers", "arch:starter/services/dispatch.py", "offers", "demo"),
    ("sec-gw-lab", "Explorer lab: gateway checks step by step", "arch:dist/security.js", "secGatewayRun", "lab"),
    # ---- Security: SSO (teaching extension)
    ("sec-sso-lab", "OIDC + PKCE flow with ES256 tokens", "arch:dist/security.js", "secSsoNext", "lab"),
    ("sec-sso-target", "Where JWT validation would replace bearer keys", "arch:starter/services/gateway.py", "proxy", "teach"),
    # ---- Security: Kerberos (teaching extension)
    ("sec-krb-setup", "KDC database and string-to-key (PBKDF2)", "arch:dist/security.js", "secKrbSetup", "lab"),
    ("sec-krb-messages", "The six messages AS-REQ … AP-REP", "arch:dist/security.js", "secKrbNext", "lab"),
    ("sec-krb-ap", "Service checks: integrity, expiry, skew, replay cache", "arch:dist/security.js", "secKrbVerifyAp", "lab"),
    ("sec-krb-seal", "AES-256-GCM seal used for tickets", "arch:dist/security.js", "secSeal", "lab"),
    ("sec-krb-target", "What a Kerberos AP-REQ would replace in Dispatch", "arch:starter/packages/config.py", "internal_actor", "teach"),
    # ---- Security: transport and deployment
    ("sec-tls-ca", "Private CA, serverAuth and clientAuth certificates", "zip:prototype/proto_run.py", "make_certs", "impl"),
    ("sec-tls-client", "Client presents its certificate, verifies the server", "zip:prototype/proto_run.py", "client_ctx", "impl"),
    ("sec-tls-server", "Server requires a client certificate (CERT_REQUIRED)", "zip:prototype/module_server.py", "~CERT_REQUIRED", "impl"),
    ("sec-dep-headers", "Security headers and CSP", "arch:server.mjs", "=securityHeaders", "impl"),
    ("sec-dep-reply", "Every response carries the headers", "arch:server.mjs", "reply", "impl"),
    ("sec-dep-loopback", "Listen on 127.0.0.1 only", "arch:server.mjs", "~\\.listen\\(", "impl"),
    ("sec-dep-systemd", "systemd sandbox (DynamicUser, ProtectSystem)", "arch:deploy/atlas-explorer.service", "~DynamicUser", "impl"),
    # ---- Cryptography: hashes and checksums
    ("cr-hash-sums", "Release SHA256SUMS written by CI", "main:.github/workflows/atlas-android.yml", "~> release/SHA256SUMS", "impl"),
    ("cr-hash-handover", "Release SHA256SUMS for hand-over", "main:android-app/scripts/finalize-handover.py", "~hashlib.sha256", "impl"),
    ("cr-hash-pin-tool", "Pinned build tool (bundletool SHA-256)", "main:.github/workflows/atlas-android.yml", "~sha256sum -c -", "impl"),
    ("cr-hash-record", "Signed bundle must equal the recorded SHA-256", "main:.github/workflows/publish-signed-android.yml", "~record\\['sha256'\\]", "impl"),
    ("cr-hash-restore", "Restore signed bundle; both hashes must match", "main:android-app/releases/restore-signed-bundle.py", "restore", "impl"),
    ("cr-hash-inventory", "SHA-256 of every source file in the blueprint", "arch:starter/scripts/generate_blueprint.py", "inventory", "impl"),
    ("cr-hash-checksum", "Non-cryptographic state checksum", "zip:prototype/module_server.py", "PaymentModule.checksum", "impl"),
    ("cr-hash-c3", "Recovery class C3: checksum mismatch → restore", "main:run_recovery_mc.py", "~C3", "impl"),
    ("cr-hash-lab-file", "Explorer lab: hash a download, compare with SHA256SUMS", "arch:dist/crypto.js", "crHashFile", "lab"),
    ("cr-hash-lab-avalanche", "Explorer lab: avalanche effect", "arch:dist/crypto.js", "crUpdateAvalanche", "lab"),
    ("cr-hash-lab-checksum", "Explorer lab: checksum vs SHA-256", "arch:dist/crypto.js", "crChecksum", "lab"),
    ("cr-hash-cli", "Command-line lab: checksum collision", "main:security_lab/crypto_lab.py", "section_checksum", "lab"),
    # ---- Cryptography: PKI
    ("cr-pki-ca", "Private CA for mutual TLS", "zip:prototype/proto_run.py", "make_certs", "impl"),
    ("cr-pki-client", "Client context: trust anchor + client certificate", "zip:prototype/proto_run.py", "client_ctx", "impl"),
    ("cr-pki-server", "Server: CERT_REQUIRED against ca.crt", "zip:prototype/module_server.py", "~CERT_REQUIRED", "impl"),
    ("cr-pki-webpki", "Web PKI: HTTPS tile download verified with certifi", "main:android-app/atlas_go/livemap.py", "TileLoader._fetch", "impl"),
    ("cr-pki-cert", "Upload certificate (RSA-4096, self-signed)", "main:android-app/releases/upload-certificate.pem", "", "impl"),
    ("cr-pki-pin", "Certificate pinning: SHA-256 of the DER certificate", "main:android-app/scripts/ci-sign-bundle.py", "certificate_sha256", "impl"),
    ("cr-pki-pin-ci", "Publish workflow re-checks the pin", "main:.github/workflows/publish-signed-android.yml", "~upload_certificate_sha256", "impl"),
    ("cr-pki-lab-pin", "Explorer lab: recompute the real pin", "arch:dist/crypto.js", "crPin", "lab"),
    ("cr-pki-lab-issue", "Explorer lab: issue a certificate", "arch:dist/crypto.js", "crIssue", "lab"),
    ("cr-pki-lab-verify", "Explorer lab: chain, CA flag, validity, EKU checks", "arch:dist/crypto.js", "crVerifyCert", "lab"),
    ("cr-pki-cli", "Command-line lab: certificate and pin", "main:security_lab/crypto_lab.py", "section_certificate", "lab"),
    # ---- Cryptography: signatures
    ("cr-sig-sign", "Sign the bundle: jarsigner SHA256withRSA, then verify", "main:android-app/scripts/sign-release.py", "main", "impl"),
    ("cr-sig-ci", "CI signing with the upload key from encrypted secrets", "main:android-app/scripts/ci-sign-bundle.py", "main", "impl"),
    ("cr-sig-apk", "APK Signature Scheme v2/v3; verify with apksigner", "main:android-app/releases/1.2.0/README.md", "~apksigner verify", "impl"),
    ("cr-sig-lab-keys", "Explorer lab: generate ECDSA or RSA key pair", "arch:dist/crypto.js", "crSigKeys", "lab"),
    ("cr-sig-lab-sign", "Explorer lab: hash-then-sign", "arch:dist/crypto.js", "crSigSign", "lab"),
    ("cr-sig-lab-verify", "Explorer lab: verify, tamper, wrong key", "arch:dist/crypto.js", "crSigVerify", "lab"),
    ("cr-sig-cli", "Command-line lab: textbook RSA hash-then-sign", "main:security_lab/crypto_lab.py", "section_rsa", "lab"),
    # ---- Cryptography: post-quantum (teaching extension)
    ("cr-pqc-lab-keys", "Lamport keys from SHA-256 only", "arch:dist/crypto.js", "crLamportKeys", "lab"),
    ("cr-pqc-lab-sign", "Lamport sign: reveal one secret per hash bit", "arch:dist/crypto.js", "crLamportSign", "lab"),
    ("cr-pqc-lab-verify", "Lamport verify", "arch:dist/crypto.js", "crLamportVerify", "lab"),
    ("cr-pqc-lab-forge", "Forgery after key reuse", "arch:dist/crypto.js", "crLamportForge", "lab"),
    ("cr-pqc-cli", "Command-line lab: Lamport one-time signature", "main:security_lab/crypto_lab.py", "section_pqc", "lab"),
]

# Explorer topics → rows. Rows may appear under several topics.
TOPICS = {
    "security/passwords": ["sec-pw-params", "sec-pw-hash", "sec-pw-verify", "sec-pw-policy", "sec-pw-public", "sec-pw-register", "sec-pw-test", "sec-pw-lab", "sec-pw-lab-verify", "sec-pw-cli"],
    "security/login": ["sec-login", "sec-login-failures", "sec-login-session", "sec-login-guest", "sec-login-logout", "sec-login-clear", "sec-pw-verify", "sec-login-lab"],
    "security/identity": ["sec-pw-register", "sec-id-email", "sec-id-phone", "sec-id-licence", "sec-id-business", "sec-id-delete", "sec-rbac-screens", "sec-rbac-online", "sec-rbac-location", "sec-rbac-respond", "sec-rbac-book", "sec-rbac-checkout", "sec-rbac-kitchen"],
    "security/gateway": ["sec-gw-routes", "sec-gw-proxy", "sec-gw-keys", "sec-gw-equal", "sec-gw-internal", "sec-gw-trips", "sec-gw-dispatch", "sec-gw-lab"],
    "security/sso": ["sec-sso-target", "sec-gw-keys", "sec-sso-lab"],
    "security/kerberos": ["sec-krb-target", "sec-krb-setup", "sec-krb-messages", "sec-krb-ap", "sec-krb-seal"],
    "security/transport": ["sec-tls-ca", "sec-tls-client", "sec-tls-server", "sec-dep-headers", "sec-dep-reply", "sec-dep-loopback", "sec-dep-systemd", "cr-sig-sign"],
    "security/gaps": ["sec-pw-params", "sec-login-failures", "sec-gw-keys", "sec-gw-internal", "sec-id-licence", "sec-gw-proxy"],
    "crypto/hashes": ["cr-hash-sums", "cr-hash-handover", "cr-hash-pin-tool", "cr-hash-record", "cr-hash-restore", "cr-hash-inventory", "cr-hash-checksum", "cr-hash-c3", "cr-hash-lab-avalanche", "cr-hash-lab-file", "cr-hash-lab-checksum", "cr-hash-cli"],
    "crypto/pki": ["cr-pki-ca", "cr-pki-client", "cr-pki-server", "cr-pki-webpki", "cr-pki-cert", "cr-pki-pin", "cr-pki-pin-ci", "cr-pki-lab-pin", "cr-pki-lab-issue", "cr-pki-lab-verify", "cr-pki-cli"],
    "crypto/signatures": ["cr-sig-sign", "cr-sig-ci", "cr-pki-pin", "cr-sig-apk", "cr-sig-lab-keys", "cr-sig-lab-sign", "cr-sig-lab-verify", "cr-sig-cli"],
    "crypto/pqc": ["cr-pki-webpki", "cr-pki-ca", "cr-sig-sign", "cr-pqc-lab-keys", "cr-pqc-lab-sign", "cr-pqc-lab-verify", "cr-pqc-lab-forge", "cr-pqc-cli"],
    "crypto/gaps": ["cr-hash-checksum", "cr-hash-sums", "cr-pki-cert", "cr-pki-webpki", "sec-gw-internal"],
}
TOPIC_TITLES = {
    "security/passwords": "Security → Password storage", "security/login": "Security → Login & lockout",
    "security/identity": "Security → Identity & roles", "security/gateway": "Security → Gateway auth",
    "security/sso": "Security → Single sign-on", "security/kerberos": "Security → Kerberos",
    "security/transport": "Security → mTLS & deployment", "security/gaps": "Security → Gaps & exercises",
    "crypto/hashes": "Cryptography → Hashes & checksums", "crypto/pki": "Cryptography → PKI & certificates",
    "crypto/signatures": "Cryptography → Digital signatures", "crypto/pqc": "Cryptography → Post-quantum",
    "crypto/gaps": "Cryptography → Gaps & exercises",
}


def read(location, main):
    kind, path = location.split(":", 1)
    if kind == "main":
        return (main / path).read_text(encoding="utf-8")
    if kind == "arch":
        return (EXPLORER / path).read_text(encoding="utf-8")
    with zipfile.ZipFile(main / "prototype.zip") as archive:
        return archive.read(path).decode("utf-8")


def python_symbols(text):
    found = {}
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found[f"{node.name}.{item.name}"] = item.lineno
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.setdefault(node.name, node.lineno)
    return found


def locate(text, path, symbol):
    if not symbol:
        return 1
    lines = text.splitlines()
    if symbol.startswith("~"):
        pattern = re.compile(symbol[1:])
        hits = [i for i, line in enumerate(lines, 1) if pattern.search(line)]
    elif symbol.startswith("="):
        pattern = re.compile(rf"^\s*(?:const |let |var )?{re.escape(symbol[1:])}\s*=")
        hits = [i for i, line in enumerate(lines, 1) if pattern.search(line)]
    elif path.endswith(".py"):
        line = python_symbols(text).get(symbol)
        hits = [line] if line else []
    else:
        pattern = re.compile(rf"^\s*(?:async\s+)?function\s+{re.escape(symbol)}\b|^\s*(?:const|let)\s+{re.escape(symbol)}\s*=")
        hits = [i for i, line in enumerate(lines, 1) if pattern.search(line)]
    if not hits:
        raise SystemExit(f"Cannot find {symbol!r} in {path}")
    return hits[0]


def resolve(main):
    rows, cache = {}, {}
    for row_id, concept, location, symbol, status in ROWS:
        if row_id in rows:
            raise SystemExit(f"Duplicate id {row_id}")
        if location not in cache:
            cache[location] = read(location, main)
        kind, path = location.split(":", 1)
        line = locate(cache[location], path, symbol)
        if kind == "main":
            plain = "?plain=1" if path.endswith(".md") else ""
            url = absolute = f"{MAIN_URL}{path}{plain}#L{line}"
            shown = path
        elif kind == "arch":
            relative = "../" + path[len("starter/"):] if path.startswith("starter/") else "../../" + path
            url, absolute, shown = f"{relative}#L{line}", f"{ARCH_URL}{path}#L{line}", "architecture-explorer/" + path
        else:
            url = absolute = f"{MAIN_URL}prototype.zip"
            shown = f"prototype.zip → {path}"
        if symbol.startswith("~"):
            text = cache[location].splitlines()[line - 1].strip().replace("|", "\\|").replace("`", "'")
            name = text if len(text) <= 72 else text[:69] + "..."
        else:
            name = symbol.lstrip("=")
        rows[row_id] = dict(concept=concept, symbol=name, path=shown, line=line, url=url, absolute=absolute, status=status)
    for topic, ids in TOPICS.items():
        missing = [i for i in ids if i not in rows]
        if missing:
            raise SystemExit(f"{topic} references unknown ids {missing}")
    return rows


def markdown(rows):
    out = ["Every concept in the Architecture Explorer's **Security** and **Cryptography** tabs, linked to the",
           "function, constant or file that implements it. Each row has a stable anchor that the explorer links to.",
           "Status: **Implemented** (in the code), **Demo-grade** (implemented with deliberately simple choices),",
           "**Teaching extension** (not in ATLAS; shows where a standard protocol would attach) or **Explorer / lab**",
           "(teaching code in the explorer or `security_lab/`). Generated by `scripts/security_catalog.py`.", ""]
    anchored = set()
    for topic, ids in TOPICS.items():
        view, key = topic.split("/")
        lab = f"{EXPLORER_URL}#{'security' if view == 'security' else 'crypto'}-{key}"
        out += [f'<a name="uml-{view}-{key}"></a>', "", f"### {TOPIC_TITLES[topic]}", "",
                f"[Open in the explorer ↗]({lab})", "",
                "| Concept | Function / symbol | Location | Status |", "| --- | --- | --- | --- |"]
        for row_id in ids:
            row = rows[row_id]
            anchor = "" if row_id in anchored else f'<a name="{row_id}"></a>'
            anchored.add(row_id)
            symbol = f"`{row['symbol']}`" if row["symbol"] else "—"
            out.append(f"| {anchor}{row['concept']} | {symbol} | [{row['path']} L{row['line']}]({row['url']}) | {STATUS[row['status']]} |")
        out.append("")
    return "\n".join(out).rstrip()


def script(rows):
    exported = {k: {f: v[f] for f in ("concept", "symbol", "path", "line", "status")} | {"source": v["absolute"]} for k, v in rows.items()}
    data = {"blueprint": BLUEPRINT_URL, "status": STATUS, "rows": exported, "topics": TOPICS}
    return ("// Generated by architecture-explorer/starter/scripts/security_catalog.py; do not edit by hand.\n"
            "// Maps every Security and Cryptography concept to its entry in the UML blueprint catalogue.\n"
            "const umlCatalog = " + json.dumps(data, indent=1, ensure_ascii=False) + ";\n")


def replace_block(document, content):
    start, end = "<!-- BEGIN SECURITY CATALOG -->", "<!-- END SECURITY CATALOG -->"
    if document.count(start) != 1 or document.count(end) != 1:
        raise SystemExit(f"Expected one SECURITY CATALOG marker pair in {MARKDOWN.name}")
    before, rest = document.split(start, 1)
    _, after = rest.split(end, 1)
    return f"{before}{start}\n\n{content}\n\n{end}{after}"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--main", type=Path, required=True, help="checkout of the main branch")
    parser.add_argument("--check", action="store_true", help="fail if an output is stale")
    args = parser.parse_args()
    rows = resolve(args.main.resolve())
    outputs = {MARKDOWN: replace_block(MARKDOWN.read_text(encoding="utf-8"), markdown(rows)), SCRIPT_OUT: script(rows)}
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                parser.exit(1, f"{path.relative_to(EXPLORER)} is stale. Run python scripts/security_catalog.py --main PATH.\n")
        else:
            path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
