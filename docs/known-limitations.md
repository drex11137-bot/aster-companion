# GAUGE: System Monitor — Known Platform Limitations & Truthful Disclosures

In accordance with the **Anti-Slop Doctrine** and **GEMINI.md §1 & §7**, GAUGE never fakes metrics, manufactures synthetic readings, or promises capabilities blocked by the Android operating system. This document truthfully discloses every platform boundary and architectural limitation.

---

## 1. SELinux & Linux Kernel Sandboxing Restrictions

### 1.1 Global CPU Utilization (`/proc/stat`)
- **Limitation**: On Android 7.0 (API 24) and higher, Google tightened SELinux policies (`domain.te`, `app.te`). Untrusted applications (`untrusted_app` SELinux domain) are strictly blocked from reading `/proc/stat`.
- **System Response**: Attempting to open `/proc/stat` returns `EACCES (Permission denied)`.
- **Competitor Scam**: Fraudulent "RAM Cleaners" and fake system monitors generate fake fluctuating percentages (e.g. `Random.nextInt(15, 45)%`) or misrepresent CPU clock frequency as utilization.
- **GAUGE Truthful Handling**: GAUGE explicitly tests `/proc/stat` accessibility via `CapabilityProbe.probe()`. When blocked, GAUGE refuses to show fake global CPU percentages. Instead, GAUGE provides:
  - Exact physical / logical CPU core counts via `/sys/devices/system/cpu/possible`.
  - Self-app CPU runtime seconds (`Process.getElapsedCpuTime()`).
  - An honest capability badge disclosing the Android SELinux restriction.

### 1.2 Other Applications' Private Memory (`getProcessMemoryInfo`)
- **Limitation**: `ActivityManager.getProcessMemoryInfo(int[] pids)` returns zeroed or generic dummy data for other apps' PIDs on modern Android unless the caller holds system signature privileges.
- **System Response**: Inter-process memory inspection is denied by the Android zygote sandboxing model.
- **GAUGE Truthful Handling**: GAUGE reports truthful **system-wide** memory metrics (`ActivityManager.MemoryInfo`: `totalMem`, `availMem`, `threshold`, and `lowMemory`), providing accurate device-level RAM pressure rather than fabricated per-package memory metrics.

---

## 2. Hardware Subsystem Boundaries

### 2.1 Thermal Headroom API Availability
- **Limitation**: `PowerManager.getThermalHeadroom(int forecastSeconds)` was introduced in Android 11 (API 30). Furthermore, it requires OEM Hardware Abstraction Layer (HAL) support.
- **System Response**: On devices lacking HAL implementation (including the Android SDK generic emulator), `getThermalHeadroom()` returns `Float.NaN`.
- **GAUGE Truthful Handling**: GAUGE inspects API level and checks for `NaN`. When unsupported, the UI displays "RESTRICTED / NOT SUPPORTED" with a link to platform requirements.

### 2.2 Battery Instantaneous Current (`BATTERY_PROPERTY_CURRENT_NOW`)
- **Limitation**: Reading battery current draw in microamperes requires a dedicated fuel gauge IC with coulomb-counting circuitry.
- **System Response**: Many low-cost OEM chipsets and emulators do not wire this hardware sensor, returning `Long.MIN_VALUE` (or 0).
- **GAUGE Truthful Handling**: GAUGE checks for `Long.MIN_VALUE` and displays charging state, voltage (mV), and battery temperature (°C) without faking mA numbers.

---

## 3. Toolchain & API Constraints

### 3.1 Figma Public REST API Write Limitations
- **Limitation**: The public Figma REST API (`api.figma.com/v1`) only supports reading file nodes, styles, and comments, or publishing component updates to existing Enterprise library files. It **does not support** programmatic creation of brand-new `.fig` binary files from scratch via API.
- **Truthful Handling**: As required by `instruction.md`, GAUGE does not pretend to create a remote cloud `.fig` file via read-only endpoints. Instead, GAUGE provides:
  1. Authoritative W3C design tokens (`docs/design/figma-tokens.json`).
  2. Complete 9-page structural layout and component specifications (`docs/design/figma-spec.md`).
  3. Original vector SVG assets (`assets/logo/gauge_logo.svg` and `assets/mascot/gauge_mascot.svg`).
  4. Native Jetpack Compose implementation identically matching the design specification.

### 3.2 Tavily MCP Account Quota Limit
- **Limitation**: The Tavily MCP server reached its monthly plan limit during early project initialization (`usage-limit-exceeded`).
- **Truthful Handling**: All 90+ research queries were routed through the **Exa MCP / Exa Search API** and **Playwright headless browser**, with every query, URL, and timestamp recorded in [`docs/research/research-ledger.csv`](file:///workspaces/codespaces-blank/docs/research/research-ledger.csv).
