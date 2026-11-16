# Verified Android handover

Application source: [56c95f1ad6f39be63315c131317c432c0c530b1a](https://github.com/FUllSCIPTS/ATLAS/commit/56c95f1ad6f39be63315c131317c432c0c530b1a).

Successful full build and acceptance: [GitHub Actions run](https://github.com/FUllSCIPTS/ATLAS/actions/runs/43961614528).

## Results

- 244 Python domain and persistence cases passed.
- Standard desktop UI: 353 assertions passed.
- Narrow desktop UI with font scale 1.2: 353 assertions passed.
- Android 16 emulator: 418 assertions passed; 32 actual app screenshots captured.
- APK and release AAB built for arm64-v8a and x86_64.
- Bundletool validated the release AAB.
- Release manifest checked: target API 36, non-debuggable, backups disabled, and only the declared foreground permissions (Internet and network state for map tiles; fine and coarse location, asked at run time); no background location or billing.
- Non-debuggable release variant installed and launched separately; process and fatal crash logs checked.
- PASS: 232 64-bit ELF libraries/extensions aligned to 16 KB; 2 Python data archives validated

The source, screenshots, build workflow and documentation are in this repository.
The [release](https://github.com/FUllSCIPTS/ATLAS/releases/tag/atlas-go-v1.5.0) contains the screenshot archive, checksums and evidence.
The APK and AABs are shared on request from a [restricted Google Drive folder](https://drive.google.com/drive/folders/1iio7hs5A7p5sM2GOh3rroG2XemnXw6KV).

## Public binary SHA-256

| File | SHA-256 |
|---|---|
| `atlas-go-demo.apk` | `9e012541192b153d61b0a40d944629372d6f5bff8c780d100ce66f8f5bdd9281` |
| `atlas-go-unsigned.aab` | `903746b3225543c08d11ef2f1a7c2addfebcc5f575282679ae746e0d21b58766` |

## Signing and Play submission

The AAB is unsigned. Sign it using the private upload-key backup handed to the owner,
or add the CI signing secrets described in [the Google Play guide](../docs/GOOGLE_PLAY.md).
The private key and password are never in the repository, logs, artifacts or release files. Store listing/account declarations,
any required closed testing, Play pre-launch checks and Google review remain owner steps.

No real rides, food deliveries or money: journeys are simulated and bank payments use a sandbox bank. The learned policies run locally from bundled constants; the optional ATLAS server (PostgreSQL) is tested separately by the server workflow.
Phone hardware, accessibility and production-service checks remain outside the emulator evidence.
