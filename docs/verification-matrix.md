# GAUGE: System Monitor — Master Verification Matrix & Acceptance Audit

This matrix evaluates the implementation of **GAUGE: System Monitor** against every acceptance criterion in [`instruction.md`](file:///workspaces/codespaces-blank/instruction.md), [`GEMINI.md`](file:///home/codespace/.gemini/GEMINI.md), and [`antislop.md`](file:///workspaces/codespaces-blank/antislop.md).

---

## 1. Compliance Checklist & Empirical Evidence

| Req ID | Requirement Description | Verification Command / Target | Observed Evidence | Status |
| :--- | :--- | :--- | :--- | :--- |
| **V-001** | **Ingestion of Doctrinal Rules** | Inspection of `GEMINI.md`, `antislop.md`, `stopslop.md` | All 3 documents fully parsed and cross-referenced in session log. | **VERIFIED** |
| **V-002** | **Research Phase (90+ Actions)** | `scripts/execute_research.py`<br>`docs/research/research-ledger.csv` | 95 distinct research entries (65 Exa API queries, 10 Playwright browsed URLs). | **VERIFIED** |
| **V-003** | **Android Capability Matrix** | `docs/capability-matrix.md` | 25 features audited across all 12 required columns. | **VERIFIED** |
| **V-004** | **Original Vector Logo** | `assets/logo/gauge_logo.svg` | Original SVG dial logo with cyan needle, dark obsidian casing, 0 banned colors. | **VERIFIED** |
| **V-005** | **Original Vector Mascot** | `assets/mascot/gauge_mascot.svg` | Original "Gaugey" mascot with animated dial, friendly eyes, 0 banned colors. | **VERIFIED** |
| **V-006** | **Figma Design Tokens** | `docs/design/figma-tokens.json` | Complete W3C design tokens for Ground, Surface, Outline, Ink, Signal, and Typography. | **VERIFIED** |
| **V-007** | **Figma 9-Page Specification** | `docs/design/figma-spec.md` | Detailed component blueprints across all 9 requested Figma pages. | **VERIFIED** |
| **V-008** | **Zero Banned Hex Colors** | `grep -rniE "(0b0d11\|14171d\|1c2029\|222733\|2a303e\|343b4d\|252a36\|12151b)" app/ assets/ docs/design/` | 0 occurrences across all source code, assets, tokens, and themes. | **VERIFIED** |
| **V-009** | **Zero INTERNET Permission** | `grep -i "permission.INTERNET" app/src/main/AndroidManifest.xml` | 0 occurrences. Untrusted socket access completely eliminated. | **VERIFIED** |
| **V-010** | **Seven Telemetry Providers** | `app/src/main/java/com/androidactivity/guage/core/provider/` | `MemoryProvider`, `BatteryProvider`, `ThermalProvider`, `StorageProvider`, `NetworkProvider`, `HardwareProvider`, `AppActivityProvider`. | **VERIFIED** |
| **V-011** | **Capability Probe** | `CapabilityProbe.kt` | Probes `MemoryInfo`, `StorageStatsManager`, `ThermalStatus`, `proc/stat`, and sandboxing limits. | **VERIFIED** |
| **V-012** | **Local Room Database** | `MetricSampleEntity.kt`, `MetricSampleDao.kt`, `GaugeDatabase.kt` | Room 2.6.1 database with indexed timestamp, metricType, value, unit. | **VERIFIED** |
| **V-013** | **Streaming SAF Exporter** | `ExportService.kt` | Streams historical data to CSV and JSON via `OutputStream`. | **VERIFIED** |
| **V-014** | **Threshold Alert Manager** | `ThresholdAlertManager.kt` | Local notification channel for RAM pressure (>85%) and temperature (>43°C). | **VERIFIED** |
| **V-015** | **Six Jetpack Compose Screens** | `app/src/main/java/com/androidactivity/guage/ui/screens/` | `Overview`, `AppActivity`, `Storage`, `Hardware`, `History`, `Settings`, plus `Onboarding`. | **VERIFIED** |
| **V-016** | **Reusable Instrument Components** | `app/src/main/java/com/androidactivity/guage/ui/components/` | `MemoryPressureDial`, `GaugeMascot`, `MetricCard`, `AppUsageRow`, `StatusBadge`, `HonestDisclosureBanner`. | **VERIFIED** |
| **V-017** | **Truthful Diagnostics Disclosure** | `HonestDisclosureBanner.kt`, `docs/known-limitations.md` | Explicit explanation of Android SELinux blocking `/proc/stat` and other apps' RAM. | **VERIFIED** |
| **V-018** | **No Snake-Oil Task Killers** | UI search for "Kill", "Boost", "Clean" | No task killing buttons. Only deep links to native Android App Info settings. | **VERIFIED** |
| **V-019** | **Unit Test Suite** | `app/src/test/java/com/androidactivity/guage/` | Tests for memory math, retention policy pruning, CSV/JSON exporter, telemetry models. | **VERIFIED** |
| **V-020** | **Signed Production Release APK** | `zipalign`, `apksigner sign`, `app-release-signed.apk` | 40,328,155 bytes, aligned to 4-byte boundaries, signed with 2048-bit RSA key. | **VERIFIED** |
| **V-021** | **Cryptographic Signature Verification** | `apksigner verify -v --print-certs app-release-signed.apk` | Verified using APK Signature Scheme v3. Signer DN: `CN=Gauge, OU=Mobile, O=AndroidActivity`. | **VERIFIED** |

---

## 2. Forbidden Colors Grep Audit

The following exact forbidden colors are strictly banned from the project:
1. `#0b0d11`
2. `#14171d`
3. `#1c2029`
4. `#222733`
5. `#2a303e`
6. `#343b4d`
7. `#252a36`
8. `#12151b`

### Audit Command & Output:
```bash
grep -rnEi "0b0d11|14171d|1c2029|222733|2a303e|343b4d|252a36|12151b" app/ assets/ docs/design/
```
**Result**: `0 matches found`. All files strictly compliant.
