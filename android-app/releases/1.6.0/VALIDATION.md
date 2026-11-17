# ATLAS Go 1.6.0 validation

Application source: [7bccbf0](https://github.com/FUllSCIPTS/ATLAS/commit/7bccbf003e8f2e88681f3977f11237beeba8af25). Build and acceptance: [GitHub Actions run](https://github.com/FUllSCIPTS/ATLAS/actions/runs/44033764144).

| Check | Result |
|---|---|
| Python unit tests | 300 (299 passed, 1 display-only test skipped without a display); 56 are new (`tests/test_prebook_sos.py`) |
| Desktop UI acceptance, 440 × 940 | 412 assertions, 35 screenshots ([ui-results-440x940.json](ui-results-440x940.json)) |
| Desktop UI acceptance, 360 × 780 at font scale 1.2 | 412 assertions, 35 screenshots ([ui-results-360x780.json](ui-results-360x780.json)) |
| Android 16 emulator | 483 assertions, 35 OS screenshots, no crash ([android-ui-results.json](android-ui-results.json), [screenshots](atlas-go-1.6.0-screenshots.zip)) |
| Build | APK and release AAB for arm64-v8a and x86_64; bundletool validated the AAB |
| Release manifest | target API 36, not debuggable, backups disabled, exactly the four declared permissions (Internet, network state, fine and coarse location); no background location, no billing, no `CALL_PHONE`, no `SEND_SMS` |
| Native alignment | [native-alignment.txt](native-alignment.txt): 232 64-bit libraries aligned to 16 KB |
| Release variant | installed and launched separately; process and fatal-crash logs checked |
| Server tests on PostgreSQL 16 | 59 passed (the server is unchanged in 1.6.0) |

Not tested: the `tel:` and `sms:` hand-off on a physical phone (the emulator run checks the link the app hands over, not the dialler or messaging app), and a pre-booking whose pickup time passes while Android has the app in the background.

The run's own record is [`../VALIDATION.md`](../VALIDATION.md), which always describes the latest build the workflow verified.
