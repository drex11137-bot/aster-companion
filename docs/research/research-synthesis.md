# GAUGE: System Monitor — Comprehensive Research Synthesis
## Evidence-Based Feasibility, Platform Boundaries, User Needs, and Architectural Directives

**Project:** GAUGE: System Monitor  
**Target Platform:** Native Android (Kotlin + Jetpack Compose)  
**Supported OS:** Android 10 (API 29) through Android 14/15 (API 34/35)  
**Research Date:** October 2026  
**Auditable Ledger:** [`docs/research/research-ledger.csv`](file:///workspaces/codespaces-blank/docs/research/research-ledger.csv) (95 distinct actions)  

---

## 1. Executive Summary

This research synthesis establishes the technical foundation, empirical constraints, and architectural boundaries for **GAUGE**, a truthful, local-first Android system monitor and app activity manager.

Unlike desktop operating systems (Windows, macOS, Linux desktop), Android enforces a strict, process-isolated security sandbox governed by Linux kernel user-IDs, SELinux policies, and Android framework permission gates. Decades of third-party "task killer", "RAM booster", and "CPU cooler" applications on Android have relied on placebo animations, misleading metrics, and harmful process-killing loops that fight Android’s native LowMemoryKiller (LMKD).

**GAUGE rejects this snake-oil entirely.** Grounded in empirical API testing, official AOSP documentation, and 95 distinct research actions across Android internals, desktop Task Manager benchmarks, competitor audits, and user sentiment analysis, GAUGE delivers:
1. **Absolute Truth in Metrics:** Every metric displays its origin, sampling interval, and confidence level. Inaccessible metrics are clearly labeled as restricted by Android security, never faked.
2. **Quad-Surface Architecture:** Organized into **Overview (Performance)**, **App Activity**, **Storage Breakdown**, and **Hardware & System Specs**.
3. **Dual-Tier Permission Model:** Full utility out-of-the-box in Standard Mode; enhanced per-app foreground time and package storage breakdown when the user explicitly grants `PACKAGE_USAGE_STATS`.
4. **Zero-Internet Privacy Guarantee:** Built with zero network permissions (`android.permission.INTERNET` is omitted from the manifest). All metric history resides in an encrypted/private Room database on the device.
5. **Anti-Slop Craftsmanship:** Designed strictly under the Anti-Slop UI Doctrine: zero banned colors, zero generic purple gradients, zero fake dashboard mockups, and high-contrast accessible typography.

---

## 2. Android Sandboxing Reality vs. Desktop Task Manager

To build a credible Android equivalent of Windows Task Manager or macOS Activity Monitor, we must distinguish between desktop and mobile security models:

| Dimension | Desktop (Windows / macOS) | Android Platform Reality (API 29+) | GAUGE Implementation Strategy |
| :--- | :--- | :--- | :--- |
| **Process Visibility** | Full visibility into all PIDs, threads, and memory allocations via Win32 / mach APIs. | Restricted. SELinux blocks reading `/proc` across UIDs; `getRunningAppProcesses()` returns only caller app. | Transparently disclose sandbox limits; show aggregate system memory and user-launchable apps. |
| **Per-App CPU %** | Real-time CPU % calculated by diffing `/proc/[pid]/stat` or Windows performance counters. | Untrusted apps cannot read CPU ticks of other processes since Android 8.0. | Show self-app CPU usage accurately; monitor active CPU frequency scaling where accessible. |
| **Task Termination** | "End Task" sends `SIGKILL` / `TerminateProcess`, instantly killing any user process. | `killBackgroundProcesses` only kills cached processes, which Android immediately restarts. | **No fake "End Task" button.** Provide deep links to system "App Info" where users can legitimately Force Stop. |
| **Per-App Memory** | Full working set, committed bytes, and paging activity per process. | `ActivityManager.getProcessMemoryInfo` returns 0s for other PIDs on modern retail devices without root. | Display system-wide RAM metrics (`totalMem`, `availMem`, `threshold`, `lowMemory`) from `ActivityManager.MemoryInfo`. |
| **App Usage History** | Windows App History / macOS Screen Time tracks CPU time and network transfer. | `UsageStatsManager` tracks daily/weekly foreground time and last used timestamp via `PACKAGE_USAGE_STATS`. | Full integration with `UsageStatsManager` to rank apps by real foreground time and launch recency. |
| **Storage Breakdown** | Unrestricted filesystem traversal over disks and partitions. | Scoped Storage (API 30+) blocks arbitrary filesystem scanning. | `StorageStatsManager.queryStatsForPackage` and `StorageManager.getStorageVolumes` for safe breakdown. |
| **Battery Attribution** | Desktop battery reports discharge rate and estimated run time. | Third-party apps cannot access per-app battery discharge without root. | Real-time voltage, current draw (uA), battery level, temperature, and cycle count (API 34+). |

---

## 3. The 10 Product Surfaces: Feasibility & Implementation

### 3.1 Overview (System Snapshot & Performance)
- **Live Memory Telemetry:** Total RAM, Available RAM, Used RAM, Low Memory Pressure flag, and Threshold from `ActivityManager.getMemoryInfo()`.
- **CPU & SoC Architecture:** Number of logical cores via `Runtime.getRuntime().availableProcessors()`, supported ABIs (`arm64-v8a`), and CPU scaling frequencies.
- **Thermal Status:** Direct integration with `PowerManager.getThermalStatus()` and `OnThermalStatusChangedListener` (API 29+) to detect throttling (`NONE`, `MODERATE`, `SEVERE`, `CRITICAL`).
- **Battery Health & Charge:** Real-time percentage, charging state, battery technology, voltage (mV), and instantaneous current draw (uA) from `BatteryManager`.

### 3.2 App Activity & Usage
- **Launcher-Visible App Discovery:** Discovered via `PackageManager.queryIntentActivities(Intent(ACTION_MAIN, CATEGORY_LAUNCHER))` avoiding Google Play policy issues with `QUERY_ALL_PACKAGES`.
- **Foreground Time & Last Active:** Queried through `UsageStatsManager.queryUsageStats()` with user-selected intervals (24 Hours, 7 Days, 30 Days).
- **App Standby Buckets:** Enumeration of whether an app is `ACTIVE`, `WORKING_SET`, `FREQUENT`, `RARE`, or `RESTRICTED`.

### 3.3 Storage Analytics
- **Primary & Secondary Volume Inspection:** Total, used, and free space derived from `StorageManager.getStorageVolumes()` and `StatFs`.
- **Package Storage Breakdown:** App code size (`appBytes`), user data size (`dataBytes`), and cache size (`cacheBytes`) via `StorageStatsManager.queryStatsForPackage()`.
- **System Storage Estimation:** Truthfully calculated as Volume Total minus Sum of accessible files and apps, explicitly labelled as "System & Reserved".

### 3.4 Hardware, SoC & Display Specifications
- **Device & OS:** Model, manufacturer, board, hardware, Android release, API level, build fingerprint, and Android security patch date.
- **Display Metrics:** Physical resolution (width x height px), density DPI, refresh rate (Hz), and supported display modes via `Display.getSupportedModes()`.
- **Sensors:** Comprehensive enumeration of hardware sensors via `SensorManager.getSensorList(Sensor.TYPE_ALL)` with vendor, power, and resolution.
- **Graphics & ABI:** OpenGL ES major/minor versions and Vulkan hardware level support via `PackageManager.getSystemAvailableFeatures()`.

### 3.5 History, Trends & Retention
- **Local Time-Series Persistence:** Bounded sampling of memory pressure and battery status stored in a Room SQLite database.
- **User-Configurable Retention:** Automated retention policy (7, 30, or 90 days) with explicit "Clear History" action.
- **Export Capabilities:** User-mediated export to standard CSV and JSON formats using Android's Storage Access Framework (`ACTION_CREATE_DOCUMENT`), requiring zero dangerous storage permissions.

### 3.6 Educational Guidance & Contextual Diagnostics
- **Memory Management Explained:** Plain-English guide explaining Linux page cache, LowMemoryKiller (LMKD), and why "free RAM is wasted RAM".
- **Thermal Throttling Guide:** What happens when an SoC enters `MODERATE` or `SEVERE` thermal states, and how ambient temperature affects clock speeds.
- **Battery Longevity Guide:** Explaining charging cycles, voltage plateaus, and lithium-ion degradation mechanisms without snake-oil promises.

---

## 4. Anti-Slop UI & Visual Identity Directives

In accordance with `GEMINI.md`, `stopslop.md`, and `antislop.md`, GAUGE enforces strict aesthetic and craft disciplines:

1. **Strictly Forbidden Hex Palette:**  
   The following 8 colors are prohibited from all styles, themes, SVGs, and drawables:  
   `#0b0d11`, `#14171d`, `#1c2029`, `#222733`, `#2a303e`, `#343b4d`, `#252a36`, `#12151b`.
2. **Instrument-Grade Visual Thesis:**  
   The interface feels like a precision laboratory instrument—calm, readable, and functional. It uses a high-contrast charcoal slate ground (`#111318`), crisp technical paper surfaces (`#1A1C23`), laboratory amber (`#F59E0B`) for warnings, signal emerald (`#10B981`) for healthy telemetry, and electric cyan (`#06B6D4`) for active primary actions.
3. **No Decorative Placeholders:**  
   No arbitrary purple-blue gradients, no glassmorphism backdrop blur on flat backgrounds, no cards-inside-cards, no pulsing fake status dots, and no generic icons in rounded pastel squares.
4. **Expressive Mascot Identity:**  
   A compact, vector-drawn dial/gauge character that reacts to device states (Calm, Busy, Throttled, Charging) without cluttering the UI.

---

## 5. Security, Privacy & Quality Governance

- **Zero Network Permitted:** Manifest completely omits `android.permission.INTERNET`. No telemetry SDKs, no crash analytics, no ad networks.
- **Minimal Permissions:** Only standard permissions needed for local hardware inspection:
  - `android.permission.PACKAGE_USAGE_STATS` (optional, for App Activity)
  - `android.permission.POST_NOTIFICATIONS` (optional, for local threshold alerts on Android 13+)
- **Verification Gate:** Every claim in the UI is tied to an automated unit or instrumentation test.
