# GAUGE: System Monitor — Permissions & Privacy Specification

## 1. Zero-Internet Architecture Pledge

`GAUGE: System Monitor` (`com.androidactivity.guage`) is engineered with an uncompromising **Privacy-by-Design** architecture. 

### Hard Compile-Time Enforcement
In `app/src/main/AndroidManifest.xml`:
```xml
<!-- Privacy by Design: ZERO android.permission.INTERNET -->
```
The application **does not declare** `android.permission.INTERNET`. At the Linux kernel and Android OS level:
- Untrusted socket creation (`socket(AF_INET, ...)`) is blocked by SELinux and Android permission checks.
- No HTTP/HTTPS connections can be initiated.
- No background analytics, third-party tracking SDKs (Firebase, Adjust, AppsFlyer), or advertising SDKs can be integrated.
- 100% of telemetry samples, hardware records, and historical logs remain strictly on the user's physical device.

---

## 2. Declared Android Permissions & Rationale

| Permission | Protection Level | Purpose | Graceful Degradation Behavior |
| :--- | :--- | :--- | :--- |
| `android.permission.PACKAGE_USAGE_STATS` | AppOp / Special Access | Querying `UsageStatsManager.queryUsageStats()` to calculate accurate foreground screen time and last active timestamps for installed packages. | **Fully Functional Fallback**: If the user does not grant Usage Access, GAUGE queries `PackageManager.queryIntentActivities()` with `ACTION_MAIN` + `CATEGORY_LAUNCHER` to display installed launcher applications without foreground duration numbers. |
| `android.permission.POST_NOTIFICATIONS` | Runtime (API 33+) | Sending local diagnostic notifications when memory pressure exceeds user-configured thresholds (e.g. > 85% RAM pressure or > 43°C battery temp). | **Graceful Silent Operation**: If denied or disabled, background threshold notifications are skipped without disrupting telemetry monitoring. |

---

## 3. Deliberately Omitted Dangerous Permissions

Many traditional "system cleaners" or deceptive utility apps abuse invasive permissions. GAUGE **refuses** to request:

| Invasive Permission | Why Deceptive Apps Request It | Why GAUGE Refuses It |
| :--- | :--- | :--- |
| `android.permission.KILL_BACKGROUND_PROCESSES` | Fake "Boost RAM" / "Clean Memory" buttons. | **Snake-oil anti-pattern**. Modern Android automatically manages cached processes via LMK (Low Memory Killer). Killing background apps forces the OS to restart services, consuming more battery and CPU. GAUGE only links users to official Android App Settings. |
| `android.permission.READ_PHONE_STATE` | Extracting IMEI, IMSI, or SIM card serial numbers for device fingerprinting. | Device identity is sufficiently reported via `android.os.Build` public constants (`MANUFACTURER`, `MODEL`, `DEVICE`, `BOARD`). Cellular identity is private. |
| `android.permission.ACCESS_FINE_LOCATION` / `COARSE_LOCATION` | Tracking user physical location or harvesting Wi-Fi BSSID geolocation. | Telemetry monitoring does not require physical coordinates. Network monitoring uses `ConnectivityManager` and `TrafficStats` solely for interface types and byte counts. |
| `android.permission.MANAGE_EXTERNAL_STORAGE` / `READ_MEDIA_*` | Scanning user photos, documents, and videos under the guise of "cleaning junk files". | GAUGE uses `StorageStatsManager` and `StatFs` to query aggregate volume statistics without reading private user files. File export uses Storage Access Framework (SAF), where the user explicitly chooses the destination. |

---

## 4. Local Data Retention & Pruning

All historical telemetry is recorded in an offline SQLite database via Android Room (`GaugeDatabase`):
1. **User-Controlled Retention**:
   - `7 Days` (Default): Samples older than 168 hours are pruned during sampling iterations.
   - `30 Days`: Extended diagnostic window for device performance debugging.
   - `90 Days`: Long-term battery degradation and memory trend tracking.
2. **Explicit User Erase**:
   - The user can instantly wipe the entire database at any time via Settings -> "Clear DB" (with confirmation dialog).
3. **Data Portability**:
   - The user can stream their local metrics history to CSV or JSON files via Storage Access Framework (`ACTION_CREATE_DOCUMENT`), saving directly to their preferred folder or external storage without intermediary servers.

---

## 5. Security & Threat Modeling Audit

- **Data at Rest**: Telemetry samples are stored within private application internal storage (`/data/user/0/com.androidactivity.guage/databases/gauge.db`), protected by Android Linux UID isolation (mode `0700`).
- **No Inter-Process Communication (IPC) Leaks**: All `Activity`, `Provider`, and `Receiver` components are non-exported (`exported="false"`) except `MainActivity`, which is protected by the standard Android launcher intent-filter.
- **Backup Exclusion**: `android:allowBackup="false"` and `android:dataExtractionRules` prevent cloud backup or ADB extraction of sensitive usage statistics without root privileges.
