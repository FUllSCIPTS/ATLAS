// ATLAS Architecture Explorer — "Foundations" topics for the Cryptography and Security views.
// Every standalone unit of docs/CRYPTOGRAPHY.md (C1–C10.5) and docs/INFORMATION_SECURITY.md (S1–S13.6)
// as what / why / how, with live labs: toy RSA and real RSA-OAEP, Diffie–Hellman and real ECDH,
// toy ECDSA with nonce-reuse key recovery, AES-GCM tampering and nonce reuse, a toy ML-KEM-shaped KEM,
// ML-DSA rejection sampling, a Winternitz one-time signature, access control, password entropy,
// TOTP (RFC 6238), PKCE (RFC 7636) and injection/XSS encoding.
// Loaded after crypto.js (reuses the helpers of security.js and crypto.js) and before explorer.js.

const FD_CRYPTO_GUIDE = SEC_MAIN + "docs/CRYPTOGRAPHY.md#";
const FD_SEC_GUIDE = SEC_MAIN + "docs/INFORMATION_SECURITY.md#";

// ------------------------------------------------------------------ unit content
// [id, short title, group, anchor, what, why, how[], pitfalls[], lab?, related topic?]
const fdCryptoUnits = [
  ["C1", "Goals, keys and security levels", "Basics", "c1--plaintext-ciphertext-keys-and-security-goals",
    "The five building blocks — hash, MAC, symmetric cipher/AEAD, key agreement/KEM and digital signature — and the goals they serve: confidentiality, integrity, authenticity and non-repudiation.",
    "Networks, disks and phones are untrusted. Cryptography turns one small, well-protected secret (a key) into protection for large amounts of data, and lets strangers agree keys and verify authors.",
    ["Kerckhoffs's principle: everything but the key may be public — ATLAS publishes all of its code.", "n-bit security: the best attack costs about 2<sup>n</sup> operations; 128 bits is beyond all computers on Earth.", "Symmetric (one shared key, fast) vs asymmetric (key pair, slow, solves key distribution); real systems are hybrid, as TLS is.", "Equal strength: AES-128 ≈ SHA-256 collisions ≈ RSA-3072 ≈ P-256; all asymmetric rows fall to Shor's algorithm."],
    ["Inventing your own cipher", "Treating Base64 or hex as encryption", "Encrypting without authenticating"]],
  ["C2", "Hash functions: SHA-256 and SHA-3", "Basics", "c2--sha-256-encoding-avalanche-preimages-and-collisions",
    "A keyless function from any message to a fixed digest (SHA-256: 32 bytes) that behaves like a random function.",
    "Fingerprints for downloads, the input to every signature (hash-then-sign), the core of HMAC, PBKDF2 and HKDF, and the only assumption behind hash-based post-quantum signatures.",
    ["Pad the message to a multiple of 512 bits, appending its length.", "Merkle–Damgård chaining: state = compress(state, block), 64 rounds per block.", "The final state is the digest — which is why SHA-256(secret‖m) allows length extension; SHA-3's sponge does not.", "Generic costs for b bits: preimage 2<sup>b</sup>, collision 2<sup>b/2</sup> (birthday bound)."],
    ["MD5 and SHA-1 are broken for signatures", "Hashing a phone number does not hide it", "A hash alone has no key: anyone can recompute it"], null, "hashes"],
  ["C3", "Checksums vs cryptographic hashes", "Basics", "c3--checksums-cryptographic-hashes-and-artifact-verification",
    "CRC32, parity and Luhn digits detect accidents; a cryptographic digest detects deliberate change — if the expected value is trustworthy.",
    "A CRC is linear and keyless, so an attacker can change data and fix the CRC. Verifying a download is only as good as the channel the expected digest came from.",
    ["CRC = remainder of polynomial division over GF(2); CRC(a⊕b) = CRC(a)⊕CRC(b)⊕CRC(0) for equal lengths.", "Compute SHA-256 of the exact bytes you downloaded.", "Obtain the expected digest from a second channel, or check a signature over it.", "Link the bytes to the publisher with the APK signature and the pinned certificate."],
    ["Taking the file and its .sha256 from the same mirror", "Comparing only the first few hex characters"], null, "hashes"],
  ["C4", "MACs and HMAC", "Basics", "c4--message-authentication-codes-hmac-and-length-extension",
    "A keyed checksum: tag = MAC(K, m). Only key holders can produce or check it.",
    "Integrity and origin between parties that share a key: cookies, webhooks, API request signing, TLS Finished, Kerberos tickets. Far faster and smaller than signatures.",
    ["Pad the key to the block size (64 bytes for SHA-256).", "inner = H((K ⊕ 0x36…) ‖ m); tag = H((K ⊕ 0x5c…) ‖ inner).", "The outer hash hides the inner state, which defeats length extension.", "Verify with a constant-time comparison (hmac.compare_digest)."],
    ["No non-repudiation: both sides hold the key", "No replay protection without a nonce, counter or timestamp", "No confidentiality: combine with encryption or use an AEAD"]],
  ["C5", "Password hashing, HKDF and randomness", "Basics", "c5--password-hashing-salt-pbkdf2-hkdf-and-randomness",
    "Slow, salted password KDFs (PBKDF2, bcrypt, scrypt, Argon2id); fast key derivation from strong secrets (HKDF); and cryptographically secure randomness.",
    "Stolen password databases are attacked offline at billions of fast hashes per second; predictable random numbers have broken real keys.",
    ["Unique 16-byte salt per account (public), so equal passwords give different verifiers.", "Work factor: ATLAS uses 200 000 PBKDF2 iterations; OWASP suggests 600 000 or Argon2id (19 MiB, t = 2).", "HKDF: PRK = HMAC(salt, IKM), then expand with labels — TLS 1.3 derives all keys this way.", "Use secrets / os.urandom / crypto.getRandomValues — never Math.random or Python's random."],
    ["One global salt", "HKDF on a password (it is fast)", "Tokens from the clock or a PRNG"], null, null],
  ["C6", "Authenticated encryption and the nonce rule", "Symmetric", "c6--authenticated-encryption-aes-gcm-and-the-nonce-rule",
    "AEAD: Encrypt(K, nonce, AD, P) → C‖tag; decryption returns the exact plaintext or rejects.",
    "Unauthenticated encryption is malleable and has leaked plaintexts through padding oracles. TLS 1.3 allows only AEAD ciphers.",
    ["AES-GCM: counter-mode keystream XORed with the plaintext.", "GHASH over the associated data and ciphertext gives a 128-bit tag.", "The receiver checks the tag in constant time before releasing plaintext.", "Never reuse (key, nonce): C₁ ⊕ C₂ = P₁ ⊕ P₂ and tags become forgeable."],
    ["Random 96-bit nonces: at most 2<sup>32</sup> messages per key", "Using plaintext before the tag is checked"], "aead"],
  ["C6.1", "AES, ChaCha20 and modes of operation", "Symmetric", "c61--symmetric-ciphers-aes-chacha20-and-modes-of-operation",
    "AES is a 128-bit block cipher (keys 128/192/256, 10/12/14 rounds); ChaCha20 is a stream cipher; a mode says how to encrypt long messages.",
    "All bulk data — TLS records, disks, Wi-Fi, messaging — is protected symmetrically. The wrong mode silently destroys security even though AES is unbroken.",
    ["Each AES round: SubBytes (S-box), ShiftRows, MixColumns, AddRoundKey.", "ECB encrypts blocks independently and leaks patterns — never use it.", "CBC needs a random IV and a MAC; CTR turns AES into a stream cipher.", "Use GCM or ChaCha20-Poly1305 (constant-time in software, preferred on phones without AES hardware)."],
    ["ECB as a library default", "Static IVs", "Key stored next to the ciphertext"], "aead"],
  ["C7", "Public-key cryptography", "Public key", "c7--publicprivate-keys-rsa-and-digital-signatures",
    "Trapdoor one-way functions and key pairs: encryption, key encapsulation, key agreement and signatures.",
    "Solves what symmetric cryptography cannot: agreeing keys with strangers and letting anyone verify an author (non-repudiation).",
    ["Hard problems: factoring (RSA), discrete log (DH), elliptic-curve discrete log (ECDH, ECDSA) — all broken by Shor; lattices and hashes are not.", "Hash-then-sign: sign H(m), so the signature is only as strong as the hash.", "EUF-CMA: even after seeing chosen signatures, no forgery on a new message.", "128-bit sizes: RSA-3072 384 B; P-256 key 64 B, signature 64 B; Ed25519 32 B / 64 B."],
    ["Textbook RSA (no padding)", "Signing with SHA-1"], null, "signatures"],
  ["C7.1", "RSA", "Public key", "c71--rsa-what-it-is-why-it-is-used-and-how-it-works",
    "Rivest–Shamir–Adleman (1977): encryption and signatures whose security rests on factoring n = p·q.",
    "Fast verification and universal support: ATLAS's upload key (RSA-4096), mTLS certificates (RSA-2048) and bundle signature (SHA256withRSA) are RSA. Weaknesses: large keys, no forward secrecy as key transport, broken by Shor.",
    ["Pick random primes p, q; n = p·q; λ(n) = lcm(p−1, q−1).", "e = 65537; d = e<sup>−1</sup> mod λ(n) (extended Euclid).", "Encrypt c = m<sup>e</sup> mod n, decrypt m = c<sup>d</sup> mod n; sign s = m<sup>d</sup>, verify s<sup>e</sup> = m.", "Real use needs padding: OAEP for encryption, PSS (or PKCS#1 v1.5) for signatures; CRT makes private operations ~4× faster."],
    ["Textbook RSA is deterministic and malleable", "PKCS#1 v1.5 encryption: Bleichenbacher / ROBOT", "Shared primes from bad RNGs; fault attacks on CRT"], "rsa"],
  ["C7.2", "Diffie–Hellman, ECDH and X25519", "Public key", "c72--diffiehellman-key-agreement-finite-field-ecdh-and-x25519",
    "Two parties compute the same secret g<sup>ab</sup> from public values g<sup>a</sup> and g<sup>b</sup>. Key agreement, not encryption.",
    "Every TLS 1.3, SSH, WireGuard and Signal session starts with it; ephemeral keys give forward secrecy.",
    ["Alice sends A = g<sup>a</sup> mod p, Bob sends B = g<sup>b</sup> mod p.", "Both compute g<sup>ab</sup>; an eavesdropper faces the discrete-log problem.", "Feed the secret and the transcript into HKDF — never use the raw value as a key.", "Authenticate the exchange (TLS signs the transcript with CertificateVerify) or a man in the middle wins."],
    ["Small/shared groups (Logjam)", "Unvalidated public values (small-subgroup, invalid-curve)", "Static keys: no forward secrecy"], "dh"],
  ["C7.3", "Elliptic curves, ECDSA and Ed25519", "Public key", "c73--elliptic-curve-cryptography-and-ecdsa-plus-eddsa",
    "Points on y² = x³ + ax + b (mod p) form a group; k·G is easy, recovering k is the ECDLP. ECDSA and Ed25519 are signatures built on it.",
    "~12× smaller keys than RSA at the same strength: passkeys, Android attestation, payments, TLS, Bitcoin (secp256k1).",
    ["Add points with the chord-and-tangent rule; multiply with constant-time double-and-add.", "ECDSA sign: r = x(k·G) mod n, s = k<sup>−1</sup>(z + r·d) mod n with a fresh secret nonce k.", "Verify: X = (z·w)·G + (r·w)·Q with w = s<sup>−1</sup>; accept if x(X) mod n = r.", "Ed25519 derives the nonce from the key and message, so it cannot repeat."],
    ["Reused nonce → private key (PS3, 2010)", "Biased nonce bits → lattice attacks", "(r, n−s) malleability; unvalidated points"], "ecdsa"],
  ["C8", "Certificates, PKI and mutual TLS", "Trust", "c8--certificates-chain-of-trust-pki-and-mutual-tls",
    "An X.509 certificate binds a public key to a name and is signed by an issuer; a PKI decides whom to believe.",
    "Public keys are just numbers; certificates let ~100 trusted roots vouch for billions of servers.",
    ["Build the chain to a trusted root; verify every signature and validity period.", "Issuers need CA:TRUE and keyCertSign; leaves need the right EKU (serverAuth / clientAuth).", "The SAN must match the hostname or IP; check revocation or rely on short lifetimes (heading to 47 days by 2029).", "Certificate Transparency logs every public certificate; pinning trades CA risk for rotation risk."],
    ["verify=False", "Checking the chain but not the hostname"], null, "pki"],
  ["C9", "Signed software and the supply chain", "Trust", "c9--signed-software-and-supply-chain-integrity",
    "Everything between the keyboard and the user's device: source, dependencies, CI, signing keys, registries, updates.",
    "Attacks such as SolarWinds, dependency confusion and the xz-utils backdoor target the chain; a valid signature on a backdoored build is still valid.",
    ["Pin dependencies and tools by digest (ATLAS pins bundletool by SHA-256).", "Build on isolated runners; record provenance (SLSA, in-toto).", "Sign with protected keys; APK v2 signs the whole file, v3 adds key rotation.", "Publish signatures in transparency logs (Sigstore) so verifiers check identity, not a key file."],
    ["Pinning actions by movable tag", "Unsigned SHA256SUMS"], null, "signatures"],
  ["C10", "Post-quantum: why and which families", "Post-quantum", "c10--post-quantum-security-lamport-lwe-and-hybrid-exchange",
    "Classical algorithms believed secure against quantum computers — not quantum key distribution.",
    "Shor breaks RSA, DH, ECDH, ECDSA and EdDSA; recorded traffic can be decrypted later. NIST IR 8547 (final, October 2026) deprecates them after 2030 and disallows them after 2035.",
    ["Mosca: if secrecy lifetime + migration time > time to a quantum computer, you are already late.", "Grover only square-roots key search: AES-256 and SHA-256 stay.", "Families: lattices (ML-KEM, ML-DSA, FN-DSA), hashes (SLH-DSA, LMS, XMSS), codes (HQC, McEliece).", "LWE: b = ⟨a, s⟩ + small error mod q hides s, yet the key holder can still decode."],
    ["Assuming new schemes are as mature as old ones (SIKE and Rainbow broke in 2022)"], "lwe", "pqc"],
  ["C10.1", "ML-KEM (FIPS 203)", "Post-quantum", "c101--ml-kem-fips-203-post-quantum-key-encapsulation",
    "Module-lattice key encapsulation: KeyGen → (ek, dk); Encaps(ek) → (K, c); Decaps(dk, c) → K. From CRYSTALS-Kyber.",
    "Replaces (EC)DH for key establishment. ML-KEM-768 is NIST's default; the hybrid X25519MLKEM768 already protects much of today's HTTPS.",
    ["Polynomials of 256 coefficients mod q = 3329, in k × k matrices (k = 2, 3, 4); multiplied with the NTT.", "KeyGen: t = A·s + e with small s, e.", "Encrypt: u = Aᵀ·r + e₁, v = tᵀ·r + e₂ + ⌈q/2⌋·m; decrypt rounds v − sᵀ·u.", "Fujisaki–Okamoto: decapsulation re-encrypts and, on mismatch, returns a pseudo-random key (implicit rejection)."],
    ["Non-constant-time code (KyberSlash, 2024)", "Leaking why decapsulation failed", "Using the secret without binding the transcript"], "kem"],
  ["C10.2", "ML-DSA (FIPS 204) and FN-DSA", "Post-quantum", "c102--ml-dsa-fips-204-and-fn-dsa-post-quantum-lattice-signatures",
    "Module-lattice signatures (from CRYSTALS-Dilithium) using \"Fiat–Shamir with aborts\"; FN-DSA (Falcon, draft FIPS 206) is a compact NTRU-lattice alternative.",
    "Replaces RSA and ECDSA in certificates, code and firmware signing. ML-DSA-65: 1 952 B key, 3 309 B signature; FN-DSA-512: ~666 B signatures.",
    ["KeyGen: t = A·s₁ + s₂, publish the high bits t₁.", "Sign: mask y, w = A·y, challenge c = H(μ ‖ high bits of w), z = y + c·s₁.", "Reject and retry if z or w − c·s₂ would leak information (about 4 tries on average).", "Verify: recompute the high bits of A·z − c·t₁·2<sup>d</sup> with the hint and compare the challenge."],
    ["Larger certificate chains (+10–15 KB)", "FN-DSA needs constant-time floating-point sampling"], "mldsa"],
  ["C10.3", "Hash-based signatures and SLH-DSA (FIPS 205)", "Post-quantum", "c103--hash-based-signatures-lamport-winternitz-merkle-trees-lmsxmss-and-slh-dsa-fips-205",
    "Signatures whose only assumption is a secure hash: Lamport → Winternitz → Merkle trees → LMS/XMSS (stateful) and SLH-DSA (stateless).",
    "The most conservative post-quantum choice, ideal for long-lived roots and firmware; CNSA 2.0 already mandates LMS/XMSS for firmware.",
    ["Winternitz: sign a digit b by hashing a secret b times; verify by hashing 15 − b more times to the public chain end.", "A checksum stops an attacker from raising digits.", "A Merkle tree turns many one-time keys into one public root.", "SLH-DSA: a hypertree of Merkle trees with a FORS few-time key at the bottom; 32-byte key, 7 856-byte signature (128s)."],
    ["Reusing a one-time key (lab: Lamport forgery)", "Restoring an LMS/XMSS key from an old backup"], "wots", "pqc"],
  ["C10.4", "HQC and Classic McEliece", "Post-quantum", "c104--other-post-quantum-kems-hqc-and-classic-mceliece",
    "Code-based KEMs: decrypting requires decoding a disguised error-correcting code. HQC was selected in March 2025 as a second KEM.",
    "Algorithmic diversity: a backup if structured lattices were ever broken. McEliece has 45+ years of analysis but ~261 KB public keys.",
    ["Encode a random message, add an error of known weight.", "Only the holder of the secret code structure can decode and remove it.", "A Fujisaki–Okamoto-style transform gives CCA security."],
    ["Key sizes break protocols that assume small keys"]],
  ["C10.5", "Migrating: hybrids and crypto-agility", "Post-quantum", "c105--migrating-to-post-quantum-cryptography-hybrids-crypto-agility-and-atlas",
    "Replacing quantum-vulnerable algorithms everywhere, using hybrids (classical + post-quantum) that stay secure if either holds.",
    "New schemes may have hidden weaknesses and many peers lack support; hybrids protect against quantum attackers and surprise breaks.",
    ["X25519MLKEM768 (0x11EC): client sends 1 184 + 32 B, server 1 088 + 32 B; both secrets go into the TLS key schedule.", "Composite certificates pair ML-DSA with ECDSA/Ed25519.", "Inventory → prioritise by Mosca → abstract algorithm choice → deploy hybrids → rotate keys.", "For ATLAS: hybrid TLS and mTLS first (location data), then the 2059 upload key."],
    ["MTU, database columns or QR codes sized for 32-byte keys"], null, "pqc"],
];

const fdSecUnits = [
  ["S1", "CIA, risk and threat modelling", "Foundations", "s1--information-security-cia-and-threat-modelling",
    "Confidentiality, integrity and availability (plus authenticity and accountability); assets, threats, vulnerabilities, controls and risk.",
    "Breaches harm people and organisations; security is a design property that is cheapest to build in early.",
    ["Identify assets (accounts, ride history, signing keys).", "Draw a data-flow diagram with trust boundaries; apply STRIDE to each crossing.", "Risk = likelihood × impact; mitigate, transfer, avoid or accept.", "Apply design principles: least privilege, fail-safe defaults, complete mediation, defence in depth."],
    ["Treating encryption as the whole of security", "No owner for residual risk"], "stride"],
  ["S2", "Identity and the IAAA chain", "Foundations", "s2--identity-authentication-authorization-and-accountability",
    "Identification, authentication, authorisation, accountability; factors you know, have and are.",
    "Most breaches abuse identity: stolen passwords, hijacked sessions, missing authorisation checks.",
    ["Authenticate with evidence; MFA needs factors from different categories.", "NIST assurance levels: AAL1 single factor, AAL2 two factors, AAL3 phishing-resistant hardware.", "Authorise each action on each object.", "Log with unique identities and synchronised clocks."],
    ["Password + security question is not MFA", "Shared accounts destroy accountability"]],
  ["S3", "Password storage and offline attacks", "Authentication", "s3--password-storage-salt-pbkdf2-and-offline-attacks",
    "Store a verifier = KDF(password, salt, cost), never the password.",
    "Databases leak; users reuse passwords, so a cracked password opens other accounts (credential stuffing).",
    ["Unique salt defeats rainbow tables; a slow KDF slows every guess.", "Random-password entropy = length × log₂(alphabet); human choices are far weaker.", "NIST SP 800-63B: allow long passphrases, block breached passwords, drop arbitrary composition rules.", "Online guessing is a different problem, handled by rate limits and MFA (S6)."],
    ["Fast hashes (SHA-256) for passwords", "Believing lockout protects a stolen file"], "entropy", "passwords"],
  ["S4", "Input validation and canonicalisation", "Application", "s4--input-validation-registration-and-unique-identities",
    "Check type, length, range, format and business rules on the trusted side; normalise equivalent forms first; encode on output.",
    "Untrusted input drives the injection family and many logic bugs; duplicate identities break \"one account per email\".",
    ["Allow-list valid forms rather than deny-listing bad ones.", "Canonicalise (Unicode NFKC, lower-case domain, E.164 phones), then validate.", "Repeat client checks on the server.", "Parameterise queries and encode output — validation is not a substitute."],
    ["Deny-lists such as stripping <code>&lt;script&gt;</code>", "Validation proves format, not ownership"], "inject"],
  ["S5", "Access-control models and IDOR", "Application", "s5--rbac-least-privilege-and-state-machines",
    "DAC, MAC (Bell–LaPadula, Biba), RBAC, ABAC and ReBAC decide whether a subject may act on an object.",
    "Broken access control is first in the OWASP Top 10; the typical bug is a missing object-level check (IDOR).",
    ["Deny by default; check every request in the layer that acts.", "Check role and ownership: a driver may advance only their own trip.", "Use state machines for when an action is legal.", "Separate duties and test denied cases, not only allowed ones."],
    ["Hiding a button instead of enforcing a rule"], "access", "identity"],
  ["S6", "Sign-in defences, TOTP and passkeys", "Authentication", "s6--sign-in-lockout-account-enumeration-and-timing-attacks",
    "Lockout and rate limits, uniform errors, timing defences and stronger factors.",
    "The login form is reachable by every attacker: guessing, stuffing, enumeration and lockout-based denial of service.",
    ["Persist counters and add back-off; also rate-limit per source.", "Same message and same work (dummy hash) for unknown accounts.", "TOTP = HMAC(secret, ⌊time/30⌋) truncated to 6 digits — phishable.", "Passkeys sign a challenge bound to the real origin — phishing-resistant."],
    ["Lockout as a DoS tool against a known user", "SMS codes and push fatigue"], "totp", "login"],
  ["S7", "Sessions, cookies and CSRF", "Application", "s7--sessions-guest-state-logout-and-deletion",
    "The credential issued after login: how it is created, stored, sent, refreshed and revoked.",
    "A stolen session bypasses passwords and MFA; fixation and CSRF abuse sessions without stealing them.",
    ["≥128-bit random IDs, regenerated at login and privilege change.", "Cookies: Secure, HttpOnly, SameSite; idle and absolute timeouts.", "Revoke on logout, password change and deletion.", "JWTs need short lifetimes and rotated refresh tokens because revocation is hard."],
    ["Tokens in URLs or logs", "Logout that only deletes the client copy"]],
  ["S8", "Stored-data integrity", "Application", "s8--saved-state-validation-atomic-writes-and-integrity",
    "Schema and invariant validation, crash-safe writes, MACs against tampering, rollback detection and backups.",
    "Corrupt or forged state can crash the app, grant privileges or lose payments.",
    ["Write to a temp file, fsync, then atomic replace.", "Validate structure and invariants; quarantine bad files.", "A MAC with a Keystore key stops edits by someone who can write the file.", "A separately stored version counter stops rollback; 3-2-1 backups restore availability."],
    ["Thinking schema validation stops a deliberate attacker"]],
  ["S9", "API security and gateways", "Services", "s9--secure-apis-gateways-and-bearer-tokens",
    "Authenticate callers, authorise every operation and object, protect credentials and limit abuse.",
    "Attackers script APIs directly; OWASP API Top 10 (2023) is led by broken object-level authorisation.",
    ["Gateway: TLS, authentication, route allow-list, rate limits, strip client identity headers.", "Services re-check identity and object ownership.", "Explicit request/response schemas prevent mass assignment.", "JWT: pin the algorithm, verify signature, iss, aud, exp — then authorise."],
    ["alg: none or algorithm confusion", "Static shared internal tokens"], null, "gateway"],
  ["S10", "SSO, OAuth 2.0, OIDC and PKCE", "Services", "s10--sso-oauth-20-and-oidc",
    "Federated identity: an IdP authenticates once; OAuth delegates API access; OIDC adds the ID token; SAML is the XML enterprise equivalent.",
    "One strong login with MFA, central revocation, and no passwords handed to apps.",
    ["App sends code_challenge = BASE64URL(SHA-256(verifier)) with state and nonce.", "User authenticates at the IdP; a one-time code returns to a registered redirect URI.", "App redeems code + verifier — an interceptor lacks the verifier.", "ID token is for the app; access token is for the API; refresh tokens rotate."],
    ["Implicit and password flows (deprecated, RFC 9700)", "Accepting ID tokens at APIs"], "pkce", "sso"],
  ["S11", "Kerberos", "Services", "s11--kerberos-tickets-and-its-six-message-exchange",
    "Ticket-based authentication with a trusted KDC and symmetric keys (RFC 4120); the default in Active Directory.",
    "Single sign-on, mutual authentication and replay protection inside a domain, with no PKI.",
    ["AS exchange: a TGT sealed with the krbtgt key.", "TGS exchange: a service ticket sealed with the service's key.", "AP exchange: ticket + fresh authenticator; replay cache; ±5 min clocks.", "Attacks to defend: AS-REP roasting, Kerberoasting, pass-the-ticket, golden and silver tickets."],
    ["Weak service-account passwords", "A leaked krbtgt key"], null, "kerberos"],
  ["S12", "TLS 1.3 and mTLS", "Services", "s12--tls-mtls-and-certificate-verification",
    "A secure channel with server (optionally client) authentication, confidentiality, integrity and forward secrecy.",
    "Everything ATLAS sends over the Internet would otherwise be readable and editable on the path.",
    ["ClientHello with key shares (often X25519MLKEM768); ServerHello with the server's share.", "Handshake keys from HKDF over the shared secret and transcript.", "Certificate + CertificateVerify (signature over the transcript) authenticate the server; Finished is an HMAC.", "TLS 1.3 removed RSA key transport, CBC, RC4 and SHA-1; 0-RTT data can be replayed."],
    ["Disabling verification", "No HSTS"], null, "transport"],
  ["S13", "Secure deployment", "Operations", "s13--supply-chain-deployed-secrets-and-boundaries",
    "Hardened configuration, secret management, least-privilege runtime, exposure control, patching and verifiable builds.",
    "Many incidents are configuration: exposed databases, default credentials, committed keys, unpatched servers.",
    ["Secrets in a manager or CI secrets; rotate; scan commits; refuse defaults.", "Bind to loopback or private networks; publish only what users need.", "Run unprivileged and sandboxed (systemd DynamicUser, ProtectSystem=strict).", "Patch on a schedule; review infrastructure as code; pin images by digest."],
    ["Secrets remain in Git history after deletion"], null, "transport"],
  ["S13.1", "Network security and zero trust", "Operations", "s131--network-security-firewalls-segmentation-vpns-and-zero-trust",
    "Firewalls, WAFs, segmentation, DMZs, VPNs, IDS/IPS and zero-trust access.",
    "Phishing and compromised laptops erased the trusted inside; flat networks let attackers move laterally to the database.",
    ["Default deny: Internet → gateway on 443 only.", "Only services may reach PostgreSQL on 5432.", "Administration only through a VPN or bastion with MFA.", "Authenticate every call (mTLS) instead of trusting network location."],
    ["A WAF is not a substitute for fixing injection"], null, "controls"],
  ["S13.2", "OWASP Top 10, XSS and CSRF", "Application", "s132--web-application-vulnerabilities-the-owasp-top-10",
    "The most critical web-application risks (2021): access control, crypto failures, injection, insecure design, misconfiguration, outdated components, authentication, integrity, logging, SSRF.",
    "A common vocabulary and minimum baseline for developers, testers and auditors.",
    ["XSS: encode output for its context and set a strict Content-Security-Policy.", "CSRF: SameSite cookies, anti-CSRF tokens, Origin checks, re-authentication.", "Injection: parameterised queries.", "SSRF: allow-list destinations; block internal ranges."],
    ["Escaping for HTML but inserting into JavaScript"], "inject"],
  ["S13.3", "Logging and incident response", "Operations", "s133--security-logging-monitoring-and-incident-response",
    "Security logs, monitoring and alerting (SIEM), and the incident-response life cycle (NIST SP 800-61).",
    "Prevention fails eventually; without logs you cannot detect, scope, notify (GDPR: 72 hours) or learn.",
    ["Log logins, lockouts, 401/403, admin changes and integrity events — never passwords or tokens.", "Protect logs (append-only, off-host) and synchronise clocks.", "Preparation → detection and analysis → containment, eradication, recovery → lessons learned.", "Alert on stuffing patterns, success after many failures and new admin accounts."],
    ["Logging the attempted password"]],
  ["S13.4", "Privacy and GDPR", "Governance", "s134--privacy-and-data-protection-gdpr",
    "Data protection law (GDPR, Ireland's Data Protection Act 2018) and privacy engineering.",
    "Location traces reveal homes, workplaces, health visits and relationships.",
    ["Article 5: lawfulness, purpose limitation, minimisation, accuracy, storage limitation, security, accountability.", "Article 25: privacy by design and by default (ATLAS overwrites driver location).", "Article 35: impact assessment for large-scale tracking; Article 33: breach notice within 72 hours.", "Pseudonymised data is still personal data; true anonymisation of traces is hard."],
    ["Calling a hashed phone number anonymous"]],
  ["S13.5", "Governance and frameworks", "Governance", "s135--security-governance-standards-and-risk-frameworks",
    "Policies, ownership and assurance; ISO/IEC 27001 (93 Annex A controls), NIST CSF 2.0, CIS Controls, PCI DSS, NIS2.",
    "Controls decay without owners; governance aligns spending with risk and provides evidence.",
    ["Policy → standard → procedure → guideline.", "Classify controls by nature (administrative, technical, physical) and function (preventive, detective, protective).", "CSF 2.0 functions: Govern, Identify, Protect, Detect, Respond, Recover.", "Keep a risk register with owners and review it."],
    ["Policies nobody can follow"]],
  ["S13.6", "Social engineering and malware", "Governance", "s136--human-factors-social-engineering-and-malware",
    "Phishing, pretexting, business email compromise, MFA fatigue; viruses, trojans, ransomware, overlay banking trojans.",
    "Stolen credentials and phishing are among the most common ways in; ransomware halts hospitals and transport.",
    ["Phishing-resistant MFA (passkeys) and email authentication (SPF, DKIM, DMARC).", "Out-of-band checks for payment or bank-detail changes.", "Endpoint detection, patching, app allow-listing; install apps only from trusted stores.", "Offline or immutable backups with tested restores."],
    ["Blaming users instead of making reporting easy"]],
];

// ------------------------------------------------------------------ state
const fd = {
  crypto: { unit: "C7.1" },
  security: { unit: "S1" },
  busy: "",
  rsa: { p: "61", q: "53", e: "17", m: "65", oaep: null },
  dh: { a: "6", b: "15", mitm: false, ecdh: null },
  ecdsa: { m1: "fare=12.50", m2: "fare=99.00", k: "10", result: null },
  aead: { text: "pickup 51.8985N 8.4756W", result: null },
  lwe: { result: null },
  kem: { result: null },
  mldsa: { result: null },
  wots: { result: null },
  stride: null,
  entropy: { pw: "Summer2026!" },
  totp: { result: null },
  pkce: { result: null },
  inject: { email: "nobody@x.ie' OR '1'='1", dish: "<img src=x onerror=alert(1)>" },
  access: { user: "driver-a", action: "advance", trip: "own-accepted" },
};

const fdUnitList = (view) => (view === "crypto" ? fdCryptoUnits : fdSecUnits);
const fdUnitById = (view, id) => fdUnitList(view).find((u) => u[0] === id) || fdUnitList(view)[0];
const fdInput = (name, label, value, attrs = "") => `<label class="sec-field"><span>${label}</span><input data-fd-input="${name}" data-keep="fd-${name}" value="${secEsc(value)}" ${attrs}></label>`;
const fdBtn = (action, label, primary = false, ic = "") => `<button type="button" class="sec-btn ${primary ? "primary" : ""}" data-fd-action="${action}" data-keep="fd-${action}" ${fd.busy ? "disabled" : ""}>${ic ? icon(ic, 14) : ""}${label}</button>`;

// ------------------------------------------------------------------ number helpers (BigInt)
const fdMod = (a, n) => ((a % n) + n) % n;
function fdPow(b, e, n) { let r = 1n; b = fdMod(b, n); while (e > 0n) { if (e & 1n) r = r * b % n; b = b * b % n; e >>= 1n; } return r; }
function fdInv(a, n) { let [r0, r1, s0, s1] = [fdMod(a, n), n, 1n, 0n]; while (r1) { const q = r0 / r1; [r0, r1] = [r1, r0 - q * r1]; [s0, s1] = [s1, s0 - q * s1]; } return r0 === 1n ? fdMod(s0, n) : null; }
function fdGcd(a, b) { while (b) [a, b] = [b, a % b]; return a; }
function fdIsPrime(n) { if (n < 2n) return false; for (let d = 2n; d * d <= n; d++) if (n % d === 0n) return false; return true; }
const fdBig = (s) => { try { const v = BigInt(String(s).trim()); return v; } catch { return null; } };

// ------------------------------------------------------------------ labs: cryptography
function fdRsaLab() {
  const R = fd.rsa, p = fdBig(R.p), q = fdBig(R.q), e = fdBig(R.e), m = fdBig(R.m);
  let body = `<div class="sec-row">${fdInput("rsa.p", "Prime p", R.p)}${fdInput("rsa.q", "Prime q", R.q)}${fdInput("rsa.e", "Public exponent e", R.e)}${fdInput("rsa.m", "Message m (number &lt; n)", R.m)}</div>`;
  const errs = [];
  if (p === null || q === null || e === null || m === null) errs.push("Enter whole numbers.");
  else {
    if (p > 1000000007n || q > 1000000007n) errs.push("Keep p and q below 10⁹ in this toy (real RSA-2048 uses 1024-bit primes).");
    else { if (!fdIsPrime(p)) errs.push(`p = ${p} is not prime.`); if (!fdIsPrime(q)) errs.push(`q = ${q} is not prime.`); }
    if (p === q) errs.push("p and q must differ.");
  }
  if (!errs.length) {
    const n = p * q, phi = (p - 1n) * (q - 1n), d = fdInv(e, phi);
    if (!d) errs.push(`gcd(e, φ(n)) = ${fdGcd(e, phi)} ≠ 1: choose another e.`);
    else if (m >= n || m < 0n) errs.push(`m must be between 0 and n − 1 = ${n - 1n}.`);
    else {
      const c = fdPow(m, e, n), back = fdPow(c, d, n), s = fdPow(m, d, n), ver = fdPow(s, e, n);
      const c2 = c * fdPow(2n, e, n) % n, m2 = fdPow(c2, d, n);
      const dp = d % (p - 1n), dq = d % (q - 1n), qi = fdInv(q, p), m1 = fdPow(c, dp, p), mq = fdPow(c, dq, q), crt = mq + fdMod(qi * (m1 - mq), p) * q;
      body += secCode(`n = p·q = ${n}\nφ(n) = (p−1)(q−1) = ${phi}\nd = e⁻¹ mod φ(n) = ${d}        (check: e·d mod φ = ${e * d % phi})\n\nencrypt  c = m^e mod n = ${c}\ndecrypt  c^d mod n     = ${back}\nCRT      d_p = ${dp}, d_q = ${dq}, q⁻¹ mod p = ${qi} → ${crt}\n\nsign     s = m^d mod n = ${s}\nverify   s^e mod n     = ${ver}`)
        + `<ul class="sec-checks">${secCheck(back === m, `Decryption returns m = ${m}`)}${secCheck(ver === m, "Signature verifies with the public key")}${secCheck(false, `Malleability: multiply c by 2<sup>e</sup> → ciphertext ${c2} decrypts to ${m2} = 2·m mod n`, "Textbook RSA lets an attacker transform ciphertexts without the key — real RSA uses OAEP / PSS padding")}${secCheck(false, `Deterministic: encrypting m again gives the same ${c}`, "An attacker can test guesses such as YES/NO")}</ul>`;
    }
  }
  if (errs.length) body += `<p class="sec-note cr-bad">${errs.join(" ")}</p>`;
  const O = fd.rsa.oaep;
  body += `<p class="sec-label">Real RSA-OAEP 2048 in your browser (Web Crypto)</p><div class="sec-actions">${fdBtn("rsa-oaep", O ? "Run again" : "Generate a 2048-bit key and encrypt twice", true, "key")}</div>`
    + (fd.busy === "rsa" ? `<p class="sec-note">Generating key…</p>` : "")
    + (O ? secCode(`modulus  2048 bits, e = 65537 (key generated in ${O.ms.toFixed(0)} ms)\nmessage  "${O.text}"\nc₁ = ${secShort(O.c1, 64)}\nc₂ = ${secShort(O.c2, 64)}\nciphertext size ${O.len} bytes`) + `<ul class="sec-checks">${secCheck(O.c1 !== O.c2, "Same message, different ciphertexts", "OAEP adds randomness, so guesses cannot be tested")}${secCheck(O.ok, "Both decrypt to the original message")}</ul>` : "");
  return body;
}

async function fdRsaOaep() {
  const t0 = performance.now();
  const kp = await crypto.subtle.generateKey({ name: "RSA-OAEP", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }, false, ["encrypt", "decrypt"]);
  const ms = performance.now() - t0, text = "ride R-1001 pickup code 4821";
  const c1 = await crypto.subtle.encrypt({ name: "RSA-OAEP" }, kp.publicKey, secEnc.encode(text));
  const c2 = await crypto.subtle.encrypt({ name: "RSA-OAEP" }, kp.publicKey, secEnc.encode(text));
  const d1 = secDec.decode(await crypto.subtle.decrypt({ name: "RSA-OAEP" }, kp.privateKey, c1));
  const d2 = secDec.decode(await crypto.subtle.decrypt({ name: "RSA-OAEP" }, kp.privateKey, c2));
  fd.rsa.oaep = { ms, text, c1: secHex(c1), c2: secHex(c2), len: c1.byteLength, ok: d1 === text && d2 === text };
}

function fdDhLab() {
  const D = fd.dh, p = 23n, g = 5n, a = fdBig(D.a), b = fdBig(D.b);
  let body = `<p class="sec-text">Public group: p = 23, g = 5 (toy size; real groups are 2048+ bits or a 256-bit curve).</p><div class="sec-row">${fdInput("dh.a", "Alice's secret a", D.a)}${fdInput("dh.b", "Bob's secret b", D.b)}</div>
    <label class="sec-check-toggle"><input type="checkbox" data-fd-check="dh.mitm" ${D.mitm ? "checked" : ""}> Mallory sits in the middle (unauthenticated exchange)</label>`;
  if (a === null || b === null || a < 1n || b < 1n || a > 21n || b > 21n) return body + `<p class="sec-note cr-bad">Choose a and b between 1 and 21.</p>`;
  const A = fdPow(g, a, p), B = fdPow(g, b, p);
  if (!D.mitm) {
    const ka = fdPow(B, a, p), kb = fdPow(A, b, p);
    body += secCode(`Alice → Bob   A = g^a mod p = 5^${a} mod 23 = ${A}\nBob → Alice   B = g^b mod p = 5^${b} mod 23 = ${B}\nAlice computes B^a mod p = ${ka}\nBob computes   A^b mod p = ${kb}\nEavesdropper sees p, g, A, B — must solve a discrete logarithm`) + `<ul class="sec-checks">${secCheck(ka === kb, `Shared secret ${ka} on both sides; next step: HKDF(secret, transcript)`)}</ul>`;
  } else {
    const m1 = 3n, m2 = 7n, M1 = fdPow(g, m1, p), M2 = fdPow(g, m2, p);
    const kAlice = fdPow(M2, a, p), kBob = fdPow(M1, b, p);
    body += secCode(`Alice → Mallory  A = ${A}      Mallory → Bob    M1 = g^3 = ${M1}\nBob → Mallory    B = ${B}      Mallory → Alice  M2 = g^7 = ${M2}\nAlice's key  = M2^a = ${kAlice}   (Mallory computes A^7 = ${fdPow(A, m2, p)})\nBob's key    = M1^b = ${kBob}   (Mallory computes B^3 = ${fdPow(B, m1, p)})`) + `<ul class="sec-checks">${secCheck(false, "Mallory shares one key with each side and relays traffic", "Fix: sign the handshake transcript with a certified key — TLS 1.3 CertificateVerify")}</ul>`;
  }
  const E = D.ecdh;
  body += `<p class="sec-label">Real elliptic-curve Diffie–Hellman (Web Crypto)</p><div class="sec-actions">${fdBtn("dh-ecdh", E ? "Run again" : "Run ECDH P-256 and X25519", true, "key")}</div>` + (E ? secCode(E.lines.join("\n")) + `<ul class="sec-checks">${E.checks.map(([ok, t]) => secCheck(ok, t)).join("")}</ul>` : "");
  return body;
}

async function fdEcdh() {
  const lines = [], checks = [];
  for (const [label, gen, bits] of [["P-256", { name: "ECDH", namedCurve: "P-256" }, 256], ["X25519", { name: "X25519" }, 256]]) {
    try {
      const alice = await crypto.subtle.generateKey(gen, true, ["deriveBits"]), bob = await crypto.subtle.generateKey(gen, true, ["deriveBits"]);
      const alg = gen.name === "ECDH" ? (k) => ({ name: "ECDH", public: k }) : (k) => ({ name: "X25519", public: k });
      const s1 = secHex(await crypto.subtle.deriveBits(alg(bob.publicKey), alice.privateKey, bits));
      const s2 = secHex(await crypto.subtle.deriveBits(alg(alice.publicKey), bob.privateKey, bits));
      const pub = new Uint8Array(await crypto.subtle.exportKey("raw", alice.publicKey)).length;
      lines.push(`${label.padEnd(7)} public key ${pub} bytes · secret ${secShort(s1, 32)}`);
      checks.push([s1 === s2, `${label}: both sides derived the same 32-byte secret`]);
    } catch (error) { lines.push(`${label.padEnd(7)} not supported by this browser`); }
  }
  fd.dh.ecdh = { lines, checks };
}

// toy curve y^2 = x^3 + 2x + 2 over F_17, G = (5, 1) of prime order 19
const FD_EC = { p: 17n, a: 2n, n: 19n, G: [5n, 1n] };
function fdEcAdd(P, Q) {
  const { p, a } = FD_EC;
  if (!P) return Q; if (!Q) return P;
  const [x1, y1] = P, [x2, y2] = Q;
  if (x1 === x2 && fdMod(y1 + y2, p) === 0n) return null;
  const l = P[0] === Q[0] && P[1] === Q[1] ? fdMod((3n * x1 * x1 + a) * fdInv(2n * y1, p), p) : fdMod((y2 - y1) * fdInv(fdMod(x2 - x1, p), p), p);
  const x3 = fdMod(l * l - x1 - x2, p);
  return [x3, fdMod(l * (x1 - x3) - y1, p)];
}
function fdEcMul(k, P) { let R = null; k = fdMod(k, FD_EC.n); while (k > 0n) { if (k & 1n) R = fdEcAdd(R, P); P = fdEcAdd(P, P); k >>= 1n; } return R; }
const fdPt = (P) => (P ? `(${P[0]}, ${P[1]})` : "O");
async function fdEcHash(msg) { return BigInt("0x" + secHex(await crypto.subtle.digest("SHA-256", secEnc.encode(msg)))) % FD_EC.n; }

async function fdEcdsaRun() {
  const n = FD_EC.n, d = 7n, Q = fdEcMul(d, FD_EC.G), k = fdBig(fd.ecdsa.k);
  if (k === null || k < 1n || k > 18n) { fd.ecdsa.result = { error: "Choose a nonce k between 1 and 18." }; return; }
  const sign = (z) => { const r = fdEcMul(k, FD_EC.G)[0] % n; return [r, fdMod(fdInv(k, n) * (z + r * d), n)]; };
  const verify = (z, [r, s]) => { const w = fdInv(s, n); const X = fdEcAdd(fdEcMul(z * w, FD_EC.G), fdEcMul(r * w, Q)); return !!X && X[0] % n === r; };
  const z1 = await fdEcHash(fd.ecdsa.m1), z2 = await fdEcHash(fd.ecdsa.m2);
  const s1 = sign(z1), s2 = sign(z2);
  const out = { Q, z1, z2, s1, s2, v1: verify(z1, s1), vx: verify(z2, s1), d };
  if (s1[1] === 0n || s2[1] === 0n) out.note = "s = 0 for this nonce: a real signer would pick a new k.";
  if (z1 !== z2 && s1[1] !== s2[1]) {
    const kRec = fdMod((z1 - z2) * fdInv(fdMod(s1[1] - s2[1], n), n), n);
    out.kRec = kRec; out.dRec = fdMod((s1[1] * kRec - z1) * fdInv(s1[0], n), n);
  } else out.note = "These two messages hash to the same value mod 19 (tiny group); change one message.";
  fd.ecdsa.result = out;
}

function fdEcdsaLab() {
  const E = fd.ecdsa, R = E.result, mult = [];
  for (let i = 1n; i <= 19n; i++) mult.push([String(i), fdPt(fdEcMul(i, FD_EC.G))]);
  let body = `<p class="sec-text">Curve y² = x³ + 2x + 2 over F<sub>17</sub>, base point G = (5, 1) of order n = 19. Private key d = 7, public key Q = 7·G = ${fdPt(fdEcMul(7n, FD_EC.G))}.</p>
    <div class="fd-mult">${mult.map(([i, P]) => `<span><b>${i}G</b>${P}</span>`).join("")}</div>
    <div class="sec-row">${fdInput("ecdsa.m1", "Message 1", E.m1)}${fdInput("ecdsa.m2", "Message 2", E.m2)}${fdInput("ecdsa.k", "Nonce k (reused!)", E.k)}</div>
    <div class="sec-actions">${fdBtn("ecdsa-run", "Sign both with the same nonce, then attack", true, "pen")}</div>`;
  if (R?.error) return body + `<p class="sec-note cr-bad">${R.error}</p>`;
  if (R) {
    body += secCode(`z₁ = SHA-256(m₁) mod 19 = ${R.z1}     z₂ = SHA-256(m₂) mod 19 = ${R.z2}\nsig₁ = (r, s) = (${R.s1[0]}, ${R.s1[1]})     sig₂ = (${R.s2[0]}, ${R.s2[1]})   ← same r: same nonce\n` + (R.kRec !== undefined ? `\nk = (z₁ − z₂)/(s₁ − s₂) mod 19 = ${R.kRec}\nd = (s₁·k − z₁)/r mod 19      = ${R.dRec}` : ""))
      + `<ul class="sec-checks">${secCheck(R.v1, "Signature 1 verifies with Q")}${secCheck(!R.vx, "Signature 1 does not verify for message 2")}${R.dRec !== undefined ? secCheck(false, `Private key recovered: d = ${R.dRec}${R.dRec === R.d ? " (correct)" : ""}`, "Never reuse an ECDSA nonce — use RFC 6979 deterministic nonces or Ed25519") : ""}</ul>`
      + (R.note ? `<p class="sec-note">${R.note}</p>` : "");
  }
  return body + `<p class="sec-note">Real ECDSA P-256 signing and tampering tests are in the <button type="button" class="sec-inline-link fd-link" data-cr-topic="signatures">Digital signatures</button> tab.</p>`;
}

async function fdAeadRun() {
  const key = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
  const nonce = secRand(12), ad = secEnc.encode("atlas-state-v1"), pt = secEnc.encode(fd.aead.text);
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv: nonce, additionalData: ad }, key, pt));
  const ok = secDec.decode(await crypto.subtle.decrypt({ name: "AES-GCM", iv: nonce, additionalData: ad }, key, ct));
  const flipped = ct.slice(); flipped[0] ^= 1;
  let tamper = "accepted"; try { await crypto.subtle.decrypt({ name: "AES-GCM", iv: nonce, additionalData: ad }, key, flipped); } catch { tamper = "rejected"; }
  let adCheck = "accepted"; try { await crypto.subtle.decrypt({ name: "AES-GCM", iv: nonce, additionalData: secEnc.encode("atlas-state-v0") }, key, ct); } catch { adCheck = "rejected"; }
  const ctrKey = await crypto.subtle.generateKey({ name: "AES-CTR", length: 128 }, false, ["encrypt"]), counter = secRand(16);
  const p1 = secEnc.encode("pickup 51.8985N 8.4756W"), p2 = secEnc.encode("dropoff 51.9030N 8.4690W");
  const c1 = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-CTR", counter, length: 64 }, ctrKey, p1));
  const c2 = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-CTR", counter, length: 64 }, ctrKey, p2));
  const len = Math.min(c1.length, c2.length), x = [], guess = [];
  for (let i = 0; i < len; i++) { x.push(c1[i] ^ c2[i]); guess.push(String.fromCharCode(c1[i] ^ c2[i] ^ p1[i])); }
  fd.aead.result = { ct: secHex(ct), len: ct.length, ok: ok === fd.aead.text, tamper, adCheck, x: secHex(new Uint8Array(x)), recovered: guess.join(""), p2: secDec.decode(p2.slice(0, len)) };
}

function fdAeadLab() {
  const A = fd.aead, R = A.result;
  return `<div class="sec-row">${fdInput("aead.text", "Plaintext", A.text)}</div><div class="sec-actions">${fdBtn("aead-run", R ? "Run again" : "Encrypt with AES-256-GCM, tamper, reuse a nonce", true, "lock")}</div>`
    + (R ? secCode(`ciphertext + 16-byte tag (${R.len} bytes)\n${secShort(R.ct, 96)}`) + `<ul class="sec-checks">${secCheck(R.ok, "Correct key, nonce and associated data → plaintext returned")}${secCheck(R.tamper === "rejected", `One ciphertext bit flipped → ${R.tamper}`, "The tag check fails before any plaintext is released")}${secCheck(R.adCheck === "rejected", `Associated data changed from v1 to v0 → ${R.adCheck}`, "Header is authenticated though not encrypted")}</ul>`
      + `<p class="sec-label">Nonce reuse with AES-CTR (the keystream inside GCM)</p>` + secCode(`c₁ ⊕ c₂ = ${secShort(R.x, 64)}  (= p₁ ⊕ p₂, no key needed)\nattacker knows p₁ = "pickup 51.8985N 8.4756W"\nrecovers p₂      = "${R.recovered}"`) + `<ul class="sec-checks">${secCheck(false, `Second message recovered without the key: "${R.p2}"`, "Never reuse a (key, nonce) pair")}</ul>` : "");
}

// LWE one-bit toy (Regev)
function fdLweRun() {
  const q = 97, n = 8, m = 20, rnd = (k) => crypto.getRandomValues(new Uint32Array(1))[0] % k;
  const s = Array.from({ length: n }, () => rnd(q));
  const A = Array.from({ length: m }, () => Array.from({ length: n }, () => rnd(q)));
  const e = Array.from({ length: m }, () => rnd(3) - 1);
  const b = A.map((row, i) => fdMod(BigInt(row.reduce((t, a, j) => t + a * s[j], 0) + e[i]), BigInt(q)));
  const trials = [];
  let correct = 0;
  for (let t = 0; t < 200; t++) {
    const bit = rnd(2), rows = A.map((_, i) => i).filter(() => rnd(2));
    const u = Array.from({ length: n }, (_, j) => rows.reduce((t2, i) => t2 + A[i][j], 0) % q);
    const v = (rows.reduce((t2, i) => t2 + Number(b[i]), 0) + bit * Math.floor(q / 2)) % q;
    const noisy = fdMod(BigInt(v - u.reduce((t2, x, j) => t2 + x * s[j], 0)), BigInt(q));
    const dec = noisy > BigInt(Math.floor(q / 4)) && noisy < BigInt(Math.floor(3 * q / 4)) ? 1 : 0;
    if (dec === bit) correct++;
    if (t < 6) trials.push(`bit ${bit} → v − ⟨u, s⟩ = ${String(noisy).padStart(2)} → decoded ${dec}`);
  }
  fd.lwe.result = { s: s.join(", "), b: b.slice(0, 6).join(", "), e: e.slice(0, 6).join(", "), trials, correct };
}

function fdLweLab() {
  const R = fd.lwe.result;
  return `<p class="sec-text">Learning with errors, one bit at a time (Regev): q = 97, secret of 8 numbers, 20 noisy equations. Encrypting adds q/2 for a 1; the key holder subtracts ⟨u, s⟩ and rounds.</p><div class="sec-actions">${fdBtn("lwe-run", R ? "New key and 200 encryptions" : "Generate an LWE key and encrypt 200 bits", true, "atom")}</div>`
    + (R ? secCode(`secret s     = [${R.s}]\npublic b     = [${R.b}, …]  (= A·s + e mod 97)\nerrors e     = [${R.e}, …]  (small, secret)\n\n${R.trials.join("\n")}`) + `<ul class="sec-checks">${secCheck(R.correct === 200, `${R.correct} of 200 bits decrypted correctly`, "Values near 0 decode as 0, values near 48 decode as 1")}</ul>` : "")
    + `<p class="sec-note">A post-quantum signature from hashes alone is live in the <button type="button" class="sec-inline-link fd-link" data-cr-topic="pqc">Post-quantum</button> tab (Lamport).</p>`;
}

// toy KEM with the shape of ML-KEM: R_q = Z_3329[X]/(X^16 + 1), k = 2
const FD_KEM = { Q: 3329, N: 16, K: 2, ETA: 2 };
function fdPrng(seedBytes) { // xoshiro128** seeded from 16 bytes: deterministic coins for the re-encryption check
  const v = new DataView(seedBytes.buffer, seedBytes.byteOffset, 16);
  let [a, b, c, d] = [v.getUint32(0), v.getUint32(4), v.getUint32(8), v.getUint32(12) | 1];
  return () => { const r = Math.imul(((Math.imul(b, 5) << 7) | (Math.imul(b, 5) >>> 25)), 9) >>> 0; const t = b << 9; c ^= a; d ^= b; b ^= c; a ^= d; c ^= t; d = (d << 11) | (d >>> 21); return r; };
}
function fdPoly(rng, small) { const { Q, N, ETA } = FD_KEM; return Array.from({ length: N }, () => { if (!small) return rng() % Q; let s = 0; for (let i = 0; i < ETA; i++) s += (rng() & 1) - ((rng() >>> 1) & 1); return s; }); }
function fdPmul(a, b) { const { Q, N } = FD_KEM, o = new Array(N).fill(0); for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) { const k = i + j, t = a[i] * b[j]; if (k < N) o[k] = (o[k] + t) % Q; else o[k - N] = (o[k - N] - t) % Q; } return o.map((x) => ((x % Q) + Q) % Q); }
const fdPadd = (a, b) => a.map((x, i) => (((x + b[i]) % FD_KEM.Q) + FD_KEM.Q) % FD_KEM.Q);
const fdDot = (u, v) => u.map((a, i) => fdPmul(a, v[i])).reduce(fdPadd);
function fdExpand(rho) { const rng = fdPrng(rho), { K } = FD_KEM; return Array.from({ length: K }, () => Array.from({ length: K }, () => fdPoly(rng, false))); }
function fdMatVec(A, v, tr) { const { K } = FD_KEM; return Array.from({ length: K }, (_, i) => fdDot(Array.from({ length: K }, (_, j) => (tr ? A[j][i] : A[i][j])), v)); }
function fdPkeEnc(ek, bits, coins) {
  const { K, Q } = FD_KEM, A = fdExpand(ek.rho), rng = fdPrng(coins);
  const r = Array.from({ length: K }, () => fdPoly(rng, true)), e1 = Array.from({ length: K }, () => fdPoly(rng, true)), e2 = fdPoly(rng, true);
  const u = fdMatVec(A, r, true).map((x, i) => fdPadd(x, e1[i]));
  const v = fdPadd(fdPadd(fdDot(ek.t, r), e2), bits.map((b) => b * ((Q + 1) / 2)));
  return { u, v };
}
function fdPkeDec(s, ct) { const { Q } = FD_KEM, w = fdPadd(ct.v, fdDot(s, ct.u).map((x) => Q - x)); return { bits: w.map((c) => (c > Q / 4 && c < 3 * Q / 4 ? 1 : 0)), w }; }
async function fdG(m, ek) { const h = new Uint8Array(await crypto.subtle.digest("SHA-256", secEnc.encode(JSON.stringify(ek)))); const buf = new Uint8Array(m.length + 32); buf.set(m); buf.set(h, m.length); const g = new Uint8Array(await crypto.subtle.digest("SHA-512", buf)); return { key: g.slice(0, 32), coins: g.slice(32, 48) }; }
const fdBits = (m) => Array.from({ length: FD_KEM.N }, (_, i) => (m[i >> 3] >> (i & 7)) & 1);
const fdFromBits = (bits) => Uint8Array.from({ length: FD_KEM.N / 8 }, (_, i) => bits.slice(8 * i, 8 * i + 8).reduce((t, b, j) => t | (b << j), 0));
async function fdKemRun() {
  const { K, Q } = FD_KEM, t0 = performance.now();
  const rho = secRand(16), rng = fdPrng(secRand(16)), A = fdExpand(rho);
  const s = Array.from({ length: K }, () => fdPoly(rng, true)), e = Array.from({ length: K }, () => fdPoly(rng, true));
  const ek = { rho: Array.from(rho), t: fdMatVec(A, s).map((x, i) => fdPadd(x, e[i])) }, ekRho = { ...ek, rho };
  const z = secRand(32);
  const decaps = async (ct) => { const { bits, w } = fdPkeDec(s, ct); const { key, coins } = await fdG(fdFromBits(bits), ek); const again = fdPkeEnc(ekRho, bits, coins); const same = JSON.stringify(again) === JSON.stringify(ct); return { key: same ? secHex(key) : secHex(await crypto.subtle.digest("SHA-256", secEnc.encode(secHex(z) + JSON.stringify(ct)))), same, w }; };
  const m = secRand(FD_KEM.N / 8), { key, coins } = await fdG(m, ek), ct = fdPkeEnc(ekRho, fdBits(m), coins);
  const good = await decaps(ct);
  const bad = structuredClone(ct); bad.v[0] = (bad.v[0] + Math.floor(Q / 2)) % Q;
  const rej = await decaps(bad);
  const noise = good.w.map((c, i) => { const target = fdBits(m)[i] ? (Q + 1) / 2 : 0; let d = c - target; if (d > Q / 2) d -= Q; if (d < -Q / 2) d += Q; return d; });
  fd.kem.result = { serverKey: secHex(key), clientKey: good.key, same: good.same, rejKey: rej.key, rejSame: rej.same, noise, maxNoise: Math.max(...noise.map(Math.abs)), ms: performance.now() - t0, t0: ek.t[0].slice(0, 6), u0: ct.u[0].slice(0, 6), v: ct.v.slice(0, 6) };
}

function fdKemLab() {
  const R = fd.kem.result, { Q, N, K } = FD_KEM;
  return `<p class="sec-text">Same algebra as ML-KEM — polynomials mod q = 3329 and X<sup>${N}</sup> + 1, a ${K} × ${K} module, small noise, ⌈q/2⌋ encoding and the Fujisaki–Okamoto re-encryption check — but with ${N} coefficients instead of 256 and no compression. Not secure, not FIPS 203.</p>
    <div class="sec-actions">${fdBtn("kem-run", R ? "New key pair and encapsulation" : "KeyGen → Encaps → Decaps", true, "atom")}</div>`
    + (fd.busy === "kem" ? `<p class="sec-note">Computing…</p>` : "")
    + (R ? secCode(`ek.t[0] = [${R.t0.join(", ")}, …]   (= A·s + e)\nct.u[0] = [${R.u0.join(", ")}, …]   ct.v = [${R.v.join(", ")}, …]\n\nnoise per coefficient after v − sᵀu: [${R.noise.join(", ")}]\nlargest |noise| = ${R.maxNoise}  <  q/4 = ${Math.floor(Q / 4)}  → every bit decodes\n\nserver key (Encaps) ${secShort(R.serverKey, 40)}\nclient key (Decaps) ${secShort(R.clientKey, 40)}\ntampered ciphertext → ${secShort(R.rejKey, 40)}`)
      + `<ul class="sec-checks">${secCheck(R.same && R.serverKey === R.clientKey, "Both sides hold the same 32-byte key")}${secCheck(!R.rejSame && R.rejKey !== R.serverKey, "Tampered ciphertext → re-encryption mismatch → pseudo-random key (implicit rejection)", "No error message an attacker could learn from")}</ul>` : "")
    + secTable(["Parameter set", "Category", "k", "Encaps key", "Ciphertext", "Secret"], [["ML-KEM-512", "1", "2", "800 B", "768 B", "32 B"], ["ML-KEM-768", "3", "3", "1 184 B", "1 088 B", "32 B"], ["ML-KEM-1024", "5", "4", "1 568 B", "1 568 B", "32 B"]]);
}

function fdMldsaRun() {
  const GAMMA = 1000, BETA = 60, rnd = (k) => crypto.getRandomValues(new Uint32Array(1))[0] % k;
  const stats = [-20, 20].map((secret) => {
    let tries = 0; const zs = [];
    while (zs.length < 20000) { tries++; const y = rnd(2 * GAMMA + 1) - GAMMA, c = (rnd(2) ? 1 : -1) * (1 + rnd(3)), z = y + c * secret; if (Math.abs(z) <= GAMMA - BETA) zs.push(z); }
    const mean = zs.reduce((a, b) => a + b, 0) / zs.length;
    const unsafe = []; for (let i = 0; i < 20000; i++) { const y = rnd(2 * GAMMA + 1) - GAMMA, c = (rnd(2) ? 1 : -1) * (1 + rnd(3)); unsafe.push(y + c * secret); }
    return { secret, min: Math.min(...zs), max: Math.max(...zs), mean, rate: zs.length / tries, umin: Math.min(...unsafe), umax: Math.max(...unsafe) };
  });
  fd.mldsa.result = stats;
}

function fdMldsaLab() {
  const R = fd.mldsa.result;
  return `<p class="sec-text">ML-DSA reveals z = y + c·s₁. If z were published every time, its edges would leak s₁. In this one-dimensional toy y is uniform in ±1000 and |c·s| ≤ 60; signing restarts whenever |z| &gt; 940.</p><div class="sec-actions">${fdBtn("mldsa-run", R ? "Sample again" : "Sign 20 000 times with secret −20 and +20", true, "pen")}</div>`
    + (R ? secTable(["Secret", "Without aborts: z range", "With aborts: z range", "Mean z", "Accepted per try"], R.map((r) => [String(r.secret), `${r.umin} … ${r.umax}`, `${r.min} … ${r.max}`, r.mean.toFixed(1), (r.rate * 100).toFixed(1) + "%"])) + `<ul class="sec-checks">${secCheck(R[0].min === R[1].min && R[0].max === R[1].max, "With aborts both secrets give the same range: z reveals nothing", "Without aborts the range is shifted by the secret — a leak")}</ul>` : "")
    + secTable(["Parameter set", "Category", "Public key", "Signature"], [["ML-DSA-44", "2", "1 312 B", "2 420 B"], ["ML-DSA-65", "3", "1 952 B", "3 309 B"], ["ML-DSA-87", "5", "2 592 B", "4 627 B"], ["FN-DSA-512 (draft FIPS 206)", "1", "897 B", "≈ 666 B"], ["Ed25519 (classical)", "—", "32 B", "64 B"]]);
}

async function fdChain(x, times) { for (let i = 0; i < times; i++) x = new Uint8Array(await crypto.subtle.digest("SHA-256", x)); return x; }
async function fdDigits(msg) {
  const d = new Uint8Array(await crypto.subtle.digest("SHA-256", secEnc.encode(msg)));
  const ds = [...d].flatMap((b) => [b >> 4, b & 15]); const cs = ds.reduce((t, x) => t + 15 - x, 0);
  return ds.concat([(cs >> 8) & 15, (cs >> 4) & 15, cs & 15]);
}
async function fdWotsRun() {
  const t0 = performance.now(), sk = Array.from({ length: 67 }, () => secRand(32));
  const pk = await Promise.all(sk.map((x) => fdChain(x, 15)));
  const msg = "atlas-go-1.2.0.apk", digits = await fdDigits(msg);
  const sig = await Promise.all(sk.map((x, i) => fdChain(x, digits[i])));
  const verify = async (m) => { const ds = await fdDigits(m); const ends = await Promise.all(sig.map((s, i) => fdChain(s, 15 - ds[i]))); return ends.every((e, i) => secHex(e) === secHex(pk[i])); };
  const ok = await verify(msg), bad = await verify("atlas-go-6.6.6.apk");
  let leaves = await Promise.all(Array.from({ length: 8 }, async (_, i) => new Uint8Array(await crypto.subtle.digest("SHA-256", secEnc.encode(secHex(pk[0]) + i)))));
  while (leaves.length > 1) { const next = []; for (let i = 0; i < leaves.length; i += 2) { const b = new Uint8Array(64); b.set(leaves[i]); b.set(leaves[i + 1], 32); next.push(new Uint8Array(await crypto.subtle.digest("SHA-256", b))); } leaves = next; }
  fd.wots.result = { digits, ok, bad, root: secHex(leaves[0]), ms: performance.now() - t0 };
}

function fdWotsLab() {
  const R = fd.wots.result;
  return `<p class="sec-text">Winternitz one-time signature with w = 16: 64 message digits + 3 checksum digits = 67 hash chains of length 15. SLH-DSA builds trees of such keys.</p><div class="sec-actions">${fdBtn("wots-run", R ? "New key" : "Generate a WOTS key and sign atlas-go-1.2.0.apk", true, "pen")}</div>`
    + (R ? secCode(`digits  ${R.digits.slice(0, 32).map((d) => d.toString(16)).join("")}…\n        (sign digit b = hash the secret b times; verify = hash 15 − b more times)\nchecksum digits ${R.digits.slice(64).join(", ")}\nsignature 67 × 32 = 2 144 bytes (Lamport: 8 192)   ·   ${R.ms.toFixed(0)} ms\nMerkle root over 8 one-time public keys: ${secShort(R.root, 32)}`) + `<ul class="sec-checks">${secCheck(R.ok, "Signature verifies for atlas-go-1.2.0.apk")}${secCheck(!R.bad, "Same signature fails for atlas-go-6.6.6.apk")}</ul>` : "")
    + secTable(["SLH-DSA set", "Category", "Public key", "Signature"], [["128s / 128f", "1", "32 B", "7 856 / 17 088 B"], ["192s / 192f", "3", "48 B", "16 224 / 35 664 B"], ["256s / 256f", "5", "64 B", "29 792 / 49 856 B"]]);
}

// ------------------------------------------------------------------ labs: security
function fdStrideLab() {
  return secTable(["Threat", "Violates", "ATLAS question", "Control"], [
    ["Spoofing", "Authenticity", "Can someone log in as a driver?", "Passwords + lockout; mTLS between services"],
    ["Tampering", "Integrity", "Can state.json or a request be modified?", "Validation; MACs; signatures"],
    ["Repudiation", "Accountability", "Can a seller deny editing a menu?", "Audit log (gap)"],
    ["Information disclosure", "Confidentiality", "Can ride history leak from a lost phone?", "App sandbox; encryption at rest (gap)"],
    ["Denial of service", "Availability", "Can an attacker lock every user out?", "Temporary lockout; body-size limits"],
    ["Elevation of privilege", "Authorisation", "Can a passenger act as a driver?", "Two-layer RBAC"],
  ]) + `<p class="sec-note">${icon("shield", 14)} Risk = likelihood × impact. Treat each row: mitigate, transfer, avoid or accept — and name an owner for what remains.</p>`;
}

const FD_COMMON = ["password", "123456", "12345678", "qwerty", "password1", "iloveyou", "letmein", "welcome", "admin", "summer2026!", "cork2026", "atlas123"];
function fdEntropyLab() {
  const pw = fd.entropy.pw, sets = [[/[a-z]/, 26], [/[A-Z]/, 26], [/[0-9]/, 10], [/[^A-Za-z0-9]/, 33]];
  const alpha = sets.reduce((t, [re, n]) => t + (re.test(pw) ? n : 0), 0) || 1;
  const bits = pw.length * Math.log2(alpha), common = FD_COMMON.includes(pw.toLowerCase());
  const pattern = /^[A-Z]?[a-z]+\d{2,4}[!?.]?$/.test(pw);
  const fmt = (s) => s < 1 ? "under a second" : s < 3600 ? `${s.toFixed(0)} s` : s < 86400 * 365 ? `${(s / 86400).toFixed(1)} days` : `${(s / 31536000).toExponential(1)} years`;
  const rate = 1e5, effective = common ? 10 : pattern ? 30 : bits;
  return `<div class="sec-row">${fdInput("entropy.pw", "Candidate password (stays in your browser)", pw, 'autocomplete="off" spellcheck="false"')}</div>`
    + secCode(`length ${pw.length} · alphabet ${alpha} → formula entropy ${bits.toFixed(1)} bits\nrealistic estimate ${effective.toFixed(0)} bits${common ? " (on a common-password list)" : pattern ? " (Word + digits + symbol pattern: tried early)" : ""}\noffline, PBKDF2 × 200 000 at 10⁵ guesses/s: ${fmt(2 ** effective / 2 / rate)} on average`)
    + `<ul class="sec-checks">${secCheck(pw.length >= 8 && pw.length <= 128 && /[A-Za-z]/.test(pw) && /\d/.test(pw), "Meets the ATLAS policy (8–128 chars, a letter and a digit)")}${secCheck(!common && !pattern && bits >= 50, "Hard to guess offline", "NIST SP 800-63B: prefer long passphrases and block breached passwords over composition rules")}</ul>`;
}

async function fdTotp(secret, time, digits = 6) {
  const key = await crypto.subtle.importKey("raw", secret, { name: "HMAC", hash: "SHA-1" }, false, ["sign"]);
  const msg = new Uint8Array(8); new DataView(msg.buffer).setBigUint64(0, BigInt(Math.floor(time / 30)));
  const mac = new Uint8Array(await crypto.subtle.sign("HMAC", key, msg)), off = mac[19] & 15;
  const code = ((mac[off] & 0x7f) << 24 | mac[off + 1] << 16 | mac[off + 2] << 8 | mac[off + 3]) % 10 ** digits;
  return String(code).padStart(digits, "0");
}
async function fdTotpRun() {
  const rfc = secEnc.encode("12345678901234567890"), now = Math.floor(Date.now() / 1000);
  const v1 = await fdTotp(rfc, 59, 8), v2 = await fdTotp(rfc, 1111111109, 8);
  const user = secRand(20), codes = await Promise.all([-30, 0, 30].map((d) => fdTotp(user, now + d)));
  fd.totp.result = { v1, v2, codes, left: 30 - (now % 30), secret: secHex(user) };
}
function fdTotpLab() {
  const R = fd.totp.result;
  return `<p class="sec-text">TOTP (RFC 6238): code = truncate(HMAC-SHA1(secret, ⌊unix time / 30⌋)) mod 10⁶. Computed here with Web Crypto.</p><div class="sec-actions">${fdBtn("totp-run", R ? "Refresh" : "Run the RFC 6238 test vectors and a fresh secret", true, "clock")}</div>`
    + (R ? secCode(`RFC 6238, SHA-1, T = 59         → ${R.v1}   (expected 94287082)\nRFC 6238, SHA-1, T = 1111111109 → ${R.v2}   (expected 07081804)\n\nnew secret ${secShort(R.secret, 24)}\nprevious ${R.codes[0]} · current ${R.codes[1]} · next ${R.codes[2]}   (${R.left} s left; servers accept ±1 step)`) + `<ul class="sec-checks">${secCheck(R.v1 === "94287082" && R.v2 === "07081804", "Matches the RFC test vectors")}${secCheck(false, "A phishing page can relay a TOTP code within 30 s", "Passkeys sign the real origin, so a look-alike site gets nothing usable")}</ul>` : "");
}

const fdB64u = (bytes) => btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
async function fdPkceRun() {
  const s256 = async (v) => fdB64u(new Uint8Array(await crypto.subtle.digest("SHA-256", secEnc.encode(v))));
  const rfcV = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk", rfc = await s256(rfcV);
  const verifier = fdB64u(secRand(32)), challenge = await s256(verifier), stolen = fdB64u(secRand(32));
  fd.pkce.result = { rfc, verifier, challenge, ok: (await s256(verifier)) === challenge, stolenOk: (await s256(stolen)) === challenge };
}
function fdPkceLab() {
  const R = fd.pkce.result;
  return `<div class="sec-actions">${fdBtn("pkce-run", R ? "New verifier" : "Create a PKCE pair and redeem the code", true, "key")}</div>`
    + (R ? secCode(`RFC 7636 example: S256("dBjftJeZ…EjXk") = ${R.rfc}\n\n1. app keeps   code_verifier  = ${R.verifier}\n2. app sends   code_challenge = ${R.challenge}  (method S256)\n3. IdP returns a one-time code to the registered redirect URI\n4. token request: code + verifier → IdP checks BASE64URL(SHA-256(verifier)) = challenge`) + `<ul class="sec-checks">${secCheck(R.rfc === "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM", "RFC 7636 test vector matches")}${secCheck(R.ok, "Legitimate app redeems the code")}${secCheck(!R.stolenOk, "A malicious app with the intercepted code but a guessed verifier is refused")}</ul>` : "")
    + `<p class="sec-note">The full OpenID Connect flow with real ES256 tokens is in the <button type="button" class="sec-inline-link fd-link" data-sec-topic="sso">Single sign-on</button> tab.</p>`;
}

function fdInjectLab() {
  const I = fd.inject, sqlEsc = I.email.replace(/'/g, "''");
  const unsafe = `SELECT * FROM users WHERE email = '${I.email}'`;
  const alwaysTrue = /'\s*or\s*'?1'?\s*=\s*'?1/i.test(I.email);
  return `<div class="sec-row">${fdInput("inject.email", "Login email (attacker-controlled)", I.email)}${fdInput("inject.dish", "Dish name shown to every rider", I.dish)}</div>`
    + `<p class="sec-label">SQL built by string concatenation</p>${secCode(unsafe)}<p class="sec-label">Parameterised query (driver sends code and data separately)</p>${secCode(`SELECT * FROM users WHERE email = ?      params = ['${sqlEsc}']`)}`
    + `<ul class="sec-checks">${secCheck(!alwaysTrue, alwaysTrue ? "Concatenated query: WHERE clause is always true → every account returned" : "Concatenated query looks harmless for this input — but only by luck", "Input became SQL code")}${secCheck(true, "Parameterised query: the whole input is one string value — no rows match")}</ul>`
    + `<p class="sec-label">HTML output, raw vs encoded</p>${secCode(`raw:     ${I.dish}\nencoded: ${secEsc(I.dish)}`)}`
    + `<ul class="sec-checks">${secCheck(!/[<>"']/.test(I.dish), /[<>"']/.test(I.dish) ? "Raw insertion would run markup in every rider's browser (XSS)" : "No markup characters in this input")}${secCheck(true, "Encoded output is displayed as text; a strict CSP (script-src 'self') is the second layer")}</ul>`;
}

const FD_TRIPS = { "unassigned-pending": { driver: null, state: "pending" }, "own-accepted": { driver: "driver-a", state: "accepted" }, "own-complete": { driver: "driver-a", state: "complete" }, "other-accepted": { driver: "driver-b", state: "accepted" } };
const FD_USERS = { "driver-a": "driver", "rider-7": "passenger", "seller-3": "seller" };
const FD_PERMS = { passenger: ["book", "order"], driver: ["go_online", "accept", "advance"], seller: ["edit_menu", "accept_order"] };
const FD_NEXT = { "pending:accept": "accepted", "accepted:advance": "in_progress", "in_progress:advance": "complete" };
function fdAccessLab() {
  const A = fd.access, role = FD_USERS[A.user], trip = FD_TRIPS[A.trip];
  const roleOk = FD_PERMS[role].includes(A.action), tripAction = ["accept", "advance"].includes(A.action);
  const ownerOk = !tripAction || trip.driver === null || trip.driver === A.user, next = FD_NEXT[`${trip.state}:${A.action}`], stateOk = !tripAction || !!next;
  const sel = (name, opts, v) => `<label class="sec-field"><span>${name}</span><select data-fd-select="access.${name.toLowerCase()}" data-keep="fd-access-${name}">${opts.map((o) => `<option ${o === v ? "selected" : ""}>${o}</option>`).join("")}</select></label>`;
  return `<div class="sec-row">${sel("User", Object.keys(FD_USERS), A.user)}${sel("Action", ["book", "accept", "advance", "edit_menu"], A.action)}${sel("Trip", Object.keys(FD_TRIPS), A.trip)}</div>`
    + `<ul class="sec-checks">${secCheck(roleOk, `Role check (RBAC): ${role} ${roleOk ? "may" : "may not"} ${A.action}`)}${tripAction ? secCheck(ownerOk, `Object check: trip assigned to ${trip.driver || "nobody"}`, ownerOk ? "" : "Missing this check is an IDOR — OWASP A01") : ""}${tripAction ? secCheck(stateOk, `State machine: ${trip.state} → ${next || "no legal transition"}`) : ""}</ul>`
    + `<p class="sec-note">${roleOk && ownerOk && stateOk ? `<strong>Allowed.</strong>` : `<strong>Denied</strong> — by default, at the layer that performs the action (store.py), not only in the UI.`}</p>`;
}

// ------------------------------------------------------------------ registry and rendering
const fdLabs = {
  rsa: ["LIVE LAB", "RSA by hand, then real RSA-OAEP", fdRsaLab],
  dh: ["LIVE LAB", "Diffie–Hellman, a man in the middle, and real ECDH", fdDhLab],
  ecdsa: ["LIVE LAB", "Toy ECDSA and the reused-nonce attack", fdEcdsaLab],
  aead: ["LIVE LAB", "AES-256-GCM: tampering and nonce reuse", fdAeadLab],
  lwe: ["LIVE LAB", "Learning with errors, one bit at a time", fdLweLab],
  kem: ["LIVE LAB", "A toy KEM with the shape of ML-KEM", fdKemLab],
  mldsa: ["LIVE LAB", "Why ML-DSA aborts: rejection sampling", fdMldsaLab],
  wots: ["LIVE LAB", "Winternitz one-time signature and a Merkle root", fdWotsLab],
  stride: ["WORKED EXAMPLE", "STRIDE on ATLAS", fdStrideLab],
  entropy: ["LIVE LAB", "How guessable is a password?", fdEntropyLab],
  totp: ["LIVE LAB", "TOTP codes with Web Crypto", fdTotpLab],
  pkce: ["LIVE LAB", "PKCE: why an intercepted code is useless", fdPkceLab],
  inject: ["LIVE LAB", "SQL injection and XSS: concatenate vs parameterise and encode", fdInjectLab],
  access: ["LIVE LAB", "Role, ownership and state checks", fdAccessLab],
};

function fdView(view) {
  const units = fdUnitList(view), cur = fdUnitById(view, fd[view].unit), [id, title, , anchor, what, why, how, pitfalls, lab, related] = cur;
  const guide = (view === "crypto" ? FD_CRYPTO_GUIDE : FD_SEC_GUIDE) + anchor;
  const groups = [...new Set(units.map((u) => u[2]))];
  const topicAttr = view === "crypto" ? "data-cr-topic" : "data-sec-topic";
  const relatedTitle = related ? (view === "crypto" ? crTopicById : secTopicById)[related]?.title : null;
  return `<div class="sec-intro"><p>Every unit of the <a class="sec-inline-link" href="${guide.split("#")[0]}">${view === "crypto" ? "cryptography" : "information-security"} teaching guide</a> on one page, each standing alone: <strong>what</strong> it is, <strong>why</strong> it matters, <strong>how</strong> it works and the usual pitfalls${view === "crypto" ? " — with live labs for RSA, Diffie–Hellman, ECDSA, AES-GCM, lattices (LWE, ML-KEM, ML-DSA) and hash-based signatures" : " — with live labs for access control, passwords, TOTP, PKCE and injection"}. Everything runs in your browser.</p></div>
    <div class="fd-units">${groups.map((g) => `<div class="fd-group"><p class="sec-label">${g}</p><div>${units.filter((u) => u[2] === g).map((u) => `<button type="button" data-fd-unit="${view}:${u[0]}" data-keep="fd-unit-${u[0]}" aria-pressed="${u[0] === id}"><b>${u[0]}</b>${u[1]}${u[8] ? `<i class="fd-live" title="Live lab">●</i>` : ""}</button>`).join("")}</div></div>`).join("")}</div>
    <article class="fd-unit-card" aria-labelledby="fd-unit-title">
      <p class="section-kicker">UNIT ${id}</p><h3 id="fd-unit-title">${title}</h3>
      <div class="fd-columns">
        <div><p class="sec-label">What it is</p><p class="sec-text">${what}</p></div>
        <div><p class="sec-label">Why it matters</p><p class="sec-text">${why}</p></div>
      </div>
      <p class="sec-label">How it works</p><ol class="fd-steps">${how.map((s) => `<li>${s}</li>`).join("")}</ol>
      ${pitfalls?.length ? `<p class="sec-label">Pitfalls</p><ul class="fd-pitfalls">${pitfalls.map((s) => `<li>${s}</li>`).join("")}</ul>` : ""}
      <p class="sec-note">${icon("file", 14)} Full unit with worked numbers, Python and diagrams: <a class="sec-inline-link" href="${guide}">${view === "crypto" ? "CRYPTOGRAPHY" : "INFORMATION_SECURITY"}.md § ${id}</a>${relatedTitle ? ` · ATLAS lab: <button type="button" class="sec-inline-link fd-link" ${topicAttr}="${related}">${relatedTitle}</button>` : ""}</p>
    </article>
    ${lab ? secSection(fdLabs[lab][0], fdLabs[lab][1], fdLabs[lab][2]()) : ""}`;
}

// ------------------------------------------------------------------ wire into the Cryptography and Security views
crTopics.splice(1, 0, { id: "learn", title: "Foundations", icon: "layers", status: null });
crTopicById.learn = crTopics[1];
crRenderers.learn = () => fdView("crypto");
crInspect.learn = {
  summary: "Nineteen standalone units — from hashes to ML-KEM — each as what, why and how, with eight live labs.",
  files: [["docs/CRYPTOGRAPHY.md", SEC_CRYPTO_GUIDE], ["security_lab/crypto_lab.py", SEC_MAIN + "security_lab/crypto_lab.py"], ["Cryptography Colab notebook", SEC_MAIN + "security_lab/Cryptography_Colab_Labs.ipynb"]],
  facts: [["Units", String(fdCryptoUnits.length)], ["Live labs", "8"], ["Public key", "RSA · DH · ECDSA · Ed25519"], ["Post-quantum", "ML-KEM · ML-DSA · FN-DSA · SLH-DSA · HQC"]],
  questions: ["Why does reusing an ECDSA nonce reveal the private key?", "Why does ML-KEM decapsulation re-encrypt?", "Which ATLAS key should move to post-quantum first?"],
};
secTopics.splice(1, 0, { id: "learn", title: "Foundations", icon: "layers", status: null });
secTopicById.learn = secTopics[1];
secRenderers.learn = () => fdView("security");
secInspect.learn = {
  summary: "Nineteen standalone units — CIA to incident response — each as what, why and how, with six live labs.",
  files: [["docs/INFORMATION_SECURITY.md", SEC_GUIDE], ["security_lab/password_storage_demo.py", SEC_MAIN + "security_lab/password_storage_demo.py"], ["Information Security Colab notebook", SEC_MAIN + "security_lab/Information_Security_Colab_Labs.ipynb"]],
  facts: [["Units", String(fdSecUnits.length)], ["Live labs", "6"], ["Frameworks", "STRIDE · OWASP · NIST · ISO 27001 · GDPR"]],
  questions: ["Which STRIDE threat does an audit log address?", "Why does PKCE make an intercepted code useless?", "Why is a passkey phishing-resistant while TOTP is not?"],
};

async function fdRun(busy, task) {
  fd.busy = busy; render();
  try { await task(); } catch (error) { console.error(error); announce("Lab error: " + error.message); }
  fd.busy = ""; render();
}

const fdActions = {
  "rsa-oaep": () => fdRun("rsa", fdRsaOaep),
  "dh-ecdh": () => fdRun("dh", fdEcdh),
  "ecdsa-run": () => fdRun("ecdsa", fdEcdsaRun),
  "aead-run": () => fdRun("aead", fdAeadRun),
  "lwe-run": () => fdRun("lwe", async () => fdLweRun()),
  "kem-run": () => fdRun("kem", fdKemRun),
  "mldsa-run": () => fdRun("mldsa", async () => fdMldsaRun()),
  "wots-run": () => fdRun("wots", fdWotsRun),
  "totp-run": () => fdRun("totp", fdTotpRun),
  "pkce-run": () => fdRun("pkce", fdPkceRun),
};

document.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  const { fdUnit, fdAction } = button.dataset;
  if (fdUnit) {
    const [view, id] = fdUnit.split(":");
    fd[view].unit = id;
    announce(`Unit ${id}: ${fdUnitById(view, id)[1]}`);
    render();
    document.getElementById("fd-unit-title")?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  } else if (fdAction && !fd.busy) fdActions[fdAction]?.();
});

function fdSet(path, value) { const [group, key] = path.split("."); fd[group][key] = value; }
document.addEventListener("change", (event) => {
  const { fdInput: inp, fdSelect: sel, fdCheck: chk } = event.target.dataset || {};
  if (inp) { fdSet(inp, event.target.value); if (inp.startsWith("ecdsa")) fd.ecdsa.result = null; render(); }
  else if (sel) { fdSet(sel, event.target.value); render(); }
  else if (chk) { fdSet(chk, event.target.checked); render(); }
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && event.target.dataset?.fdInput) { fdSet(event.target.dataset.fdInput, event.target.value); render(); }
});
