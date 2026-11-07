# GAUGE: Desktop System Monitor Feature Benchmark & Android Translation
## Comprehensive Analysis of Windows Task Manager, Resource Monitor, and macOS Activity Monitor

This document details the feature architectures, metric semantics, update cadences, and user control patterns across flagship desktop system utilities, establishing the baseline against which **GAUGE** designs its native Android experience.

---

## 1. Desktop Feature Benchmark & Android Translation Matrix

| Desktop System & View | Primary Metrics & Signals | Desktop Update Cadence | Desktop Action Model | Can Android Approximate Truthfully? | GAUGE Mobile Adaptation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Windows Task Manager:**<br>*Processes Tab* | • Apps, Background processes, Windows processes<br>• Real-time CPU % per process<br>• Memory (Private Working Set)<br>• Disk I/O (MB/s)<br>• Network (Mbps)<br>• GPU % | 1 second default<br>(High: 0.5s, Low: 4s, Paused) | • "End Task" (`TerminateProcess`)<br>• Resource values (values vs %)<br>• Efficiency Mode toggle | **Partially Feasible.**<br>Android blocks per-process CPU % and per-process RAM for other apps. | **App Activity View:**<br>Lists user apps with launch recency and total daily foreground time via `UsageStatsManager`. Direct deep link to system App Info for real Force Stop. |
| **Windows Task Manager:**<br>*Performance Tab* | • Real-time CPU graph, speed GHz, sockets, cores, logical processors, virtualization, uptime<br>• Memory in-use, available, committed, cached, paged pool<br>• Disk active time, read/write speed<br>• Wi-Fi / Ethernet throughput | 1 second default | • Copy metric details<br>• Open Resource Monitor link | **High Feasibility.**<br>System RAM, SoC core counts, uptime, and network interface totals are fully accessible. | **Overview (Performance) View:**<br>Live system RAM gauge (Available vs In-Use), SoC architecture & core topology, thermal throttling level, and network traffic since boot. |
| **Windows Task Manager:**<br>*App History Tab* | • CPU time (accumulated)<br>• Network usage (MB)<br>• Metered network usage<br>• Tile updates | Historical aggregate (Monthly window) | • Delete usage history | **High Feasibility.**<br>`UsageStatsManager` and `NetworkStatsManager` provide identical historical aggregation. | **App Usage History:**<br>User can select 24 Hours, 7 Days, or 30 Days time-windows to rank apps by foreground engagement and storage consumption. |
| **Windows Task Manager:**<br>*Startup Apps Tab* | • App name, publisher, status (Enabled/Disabled), startup impact (Low/Medium/High) | Static list on load | • Enable / Disable startup entry | **Infeasible on Android.**<br>Android does not have a user-editable startup registry; apps start via broadcast receivers (`BOOT_COMPLETED`). | **Educational Guidance:**<br>Explains Android's background execution limits and App Standby buckets (`ACTIVE`, `WORKING_SET`, `RARE`, `RESTRICTED`). |
| **Windows Resource Monitor:**<br>*Memory Tab* | • Hardware Reserved, In Use, Modified, Standby, Free<br>• Commit (KB), Working Set, Shareable, Private<br>• Hard Faults/sec | 1 second | • End Process, Suspend, Resume | **Partially Feasible.**<br>Android kernel handles memory via zRAM and LMK; `MemoryInfo` exposes Total, Available, and Threshold. | **Memory Pressure Meter:**<br>Displays Total vs Available RAM, zRAM swap status if exposed, and explicit Low-Memory pressure indicator. |
| **Windows Resource Monitor:**<br>*Disk Tab* | • Processes with Disk Activity<br>• Disk Queue Length<br>• Storage Volumes & Free Space | 1 second | • Check partition health | **Partially Feasible.**<br>Per-process disk I/O blocked. Volume total and free space fully supported. | **Storage Analytics View:**<br>Shows storage volumes, free vs used space, and per-app storage breakdown (`appBytes`, `dataBytes`, `cacheBytes`). |
| **macOS Activity Monitor:**<br>*CPU Tab* | • % CPU per process, CPU Time, Threads, Idle Wake Ups, GPU %<br>• System / User / Idle CPU load graph | 1 to 5 seconds | • Quit / Force Quit (`SIGTERM` / `SIGKILL`)<br>• Inspect process, sample | **Infeasible for Third-Party Apps.**<br>Blocked by Android SELinux `untrusted_app` policy. | **Transparent Disclosure:**<br>Accurately measures Gauge's own CPU load; displays active CPU frequencies where accessible; refuses to fake other apps' CPU %. |
| **macOS Activity Monitor:**<br>*Memory Tab* | • **Memory Pressure Graph** (Green/Yellow/Red)<br>• Physical Memory, Memory Used, App Memory, Wired, Compressed<br>• Swap Used, Cached Files | 1 to 5 seconds | • Quit process | **High Feasibility Conceptual Fit.**<br>macOS Memory Pressure is the exact conceptual equivalent of Android's LowMemory state. | **Core Memory Gauge:**<br>Adopts macOS's philosophy: Free RAM is not a health score. Displays memory pressure state (`Normal`, `Elevated`, `Critical Threshold`). |
| **macOS Activity Monitor:**<br>*Energy Tab* | • Energy Impact per app, 12 hr Power, App Nap, Prevents Sleep | Historical & live | • Quit process | **Infeasible on Android.**<br>`BatteryStats` requires signature permissions. | **Battery Telemetry View:**<br>Real-time current draw (mA), voltage (mV), battery level, temperature, and cycle count (API 34+). |
| **macOS Force Quit Dialog:** | • Simple list of running GUI applications with "(Not Responding)" indicator | Event-driven | • Force Quit button | **Partially Feasible.**<br>Third-party apps cannot force-quit other apps. | **App Actions Integration:**<br>One-tap deep link to Android's official system "App Info" page where users can legitimately tap "Force stop". |

---

## 2. Key Insights & Principles Extracted

### 2.1 The "Memory Pressure" Breakthrough (macOS Activity Monitor)
Traditional Windows users often believe "more free RAM = faster computer". In modern virtual memory systems (both Linux/Android and macOS/Darwin), unused RAM is wasted RAM because the operating system utilizes free pages for disk cache, buffers, and preloaded application code.
- macOS Activity Monitor solved this misconception by placing **Memory Pressure** at the center of its UI. If memory pressure is Green, the system is performing optimally even if "free memory" is low.
- **GAUGE applies this directly:** The Overview screen does not encourage users to "free RAM". It provides a truthful Memory Gauge that explains:
  - Total Physical RAM
  - In-Use Memory (Active apps + OS runtime)
  - Cached / Available Memory
  - Memory Pressure State (`Optimal`, `Elevated`, `Critical LMK Threshold`)

### 2.2 The "Truthful Task Management" Principle (Windows Task Manager)
Windows Task Manager gives users control, but it does so because the Win32 subsystem allows non-sandboxed process termination. On Android:
- Calling `ActivityManager.killBackgroundProcesses()` does **not** stop foreground or active background services. The Android framework immediately respawns killed processes to restore saved state.
- Indiscriminate task killing causes severe CPU spikes, battery drain, and cache thrashing.
- **GAUGE refuses to offer a fake "Kill Tasks" button.** Instead, it adopts the honest desktop approach: when an app is misbehaving, GAUGE provides a direct shortcut to the system's native **Application Details** screen (`Settings.ACTION_APPLICATION_DETAILS_SETTINGS`), where the user can execute an authentic, OS-level Force Stop.

### 2.3 The "App History" Evolution
Windows 10/11 Task Manager introduced the "App History" tab to monitor accumulated resource consumption over time rather than instantaneous spikes.
- On Android, `UsageStatsManager` is the direct counterpart to App History.
- GAUGE designs its **App Activity** view around this paradigm: users can toggle between Today (24 Hours), Past 7 Days, and Past 30 Days to see which applications are consuming the most foreground attention and device storage.
