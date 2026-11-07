# GAUGE: Play Store App Store Optimization (ASO) & Keyword Analysis
## Evidence-Based Keyword Relevance, Search Intent, Play Store Policy Compliance, and Store Metadata

This document outlines the App Store Optimization (ASO) strategy for **GAUGE: System Monitor** on the Google Play Store, grounded in empirical search intent analysis, competitor metadata audits, and strict compliance with Google Play Developer Policies.

---

## 1. Candidate Keyword Analysis & Feasibility Evaluation

| Candidate Keyword Term | Primary Search Intent | Relevance to GAUGE | Competition Signal | Target Placement in Listing | Implementation Dependency | Decision & Rationale |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **System Monitor** | High-intent users looking for real-time device resource telemetry. | **100%** | Moderate (Dominated by legacy tools). | Title, Short Description, Full Description H1. | Core overview metrics (`ActivityManager`, `BatteryManager`). | **USE (Primary Target)**<br>Anchors product identity: `Gauge: System Monitor`. |
| **Task Manager** | Users wanting to see what apps are running or taking memory. | **85%** | High (High volume, high user expectation). | Short Description, Features list, Educational FAQ. | `UsageStatsManager` (App Activity) & system Settings deep links. | **USE WITH CONTEXT**<br>Use carefully: explain GAUGE is an honest mobile task & activity manager, rejecting fake "task killers". |
| **App Activity** | Users wanting to audit app screen time and recent usage. | **100%** | Low to Moderate. | Short Description, Screenshots, Tab Title. | `UsageStatsManager` foreground tracking. | **USE (Core Feature)**<br>Accurate, professional description of usage stats. |
| **Storage Analyzer** | Users diagnosing full storage and looking for heavy apps. | **95%** | High. | Short Description, Features section, Screenshot 3. | `StorageStatsManager` & `StorageManager`. | **USE (Core Feature)**<br>Directly maps to Storage Breakdown tab. |
| **Battery Monitor** | Users diagnosing battery drain, voltage, current, and temperature. | **90%** | Very High. | Short Description, Features section, Screenshot 4. | `BatteryManager` broadcast & property APIs. | **USE (Core Feature)**<br>Accurate representation of live battery current (mA) and temp. |
| **Device Info / Hardware Info** | Users checking SoC model, cores, display refresh rate, and sensors. | **90%** | High. | Features section, Store Tags. | `Build`, `Display`, and `SensorManager` APIs. | **USE (Secondary Target)**<br>Covers the Hardware & Specs tab. |
| **CPU Monitor** | Power users inspecting processor clock speeds and core counts. | **75%** | Moderate. | Features section. | SoC core detection and active sysfs frequencies where accessible. | **USE WITH CAVEAT**<br>Do not claim whole-system CPU %; focus on core frequency & topology. |
| **Thermal Status** | Gamers & power users checking overheating and throttling. | **85%** | Low (High opportunity niche). | Features section, Search keywords. | `PowerManager.getThermalStatus()` API. | **USE (Differentiator)**<br>Rarely highlighted by competitors despite being a native API. |
| **RAM Booster / Memory Cleaner** | Users wanting to speed up phone by clearing RAM. | **0%** | High (Toxic / Scam query). | **STRICTLY REJECTED** | N/A (Counter-productive to OS memory management). | **REJECT**<br>Violates Play Store policy against deceptive claims. Addressed only in educational in-app FAQ. |
| **Speed Up Phone / Cool Down CPU** | Users believing software can magically cool down hardware. | **0%** | High (Snake-oil search). | **STRICTLY REJECTED** | N/A (Physically impossible). | **REJECT**<br>Deceptive marketing strictly prohibited. |

---

## 2. Google Play Store Metadata Specification

### 2.1 Product Title (Strict 30 Character Limit)
```text
Gauge: System Monitor
```
- **Character Count:** 21 / 30 characters.
- **Compliance:** Contains zero promotional adjectives ("Free", "Best", "Top"). Clear brand + primary category keyword.

### 2.2 Short Description (Strict 80 Character Limit)
```text
Real-time device performance, app activity, storage and battery insights.
```
- **Character Count:** 72 / 80 characters.
- **Compliance:** Accurate, concise summary of the four primary product surfaces without buzzwords.

### 2.3 Full Description (Structured for Truth & Compliance)

```markdown
Gauge is a truthful, local-first system monitor and app activity manager for Android.

Inspired by desktop utilities like Windows Task Manager and macOS Activity Monitor, Gauge gives you accurate, real-time visibility into your device's hardware, performance, memory pressure, and installed applications—with zero ads, zero tracking, and no fake "speed boosters."

KEY FEATURES:

1. REAL-TIME SYSTEM TELEMETRY
• Live Memory Gauge: View total physical RAM, in-use memory, and available memory from official Android APIs.
• Memory Pressure Indicator: Understand when Android's LowMemoryKiller is under strain without fake "RAM cleaning" myths.
• CPU & Core Architecture: Inspect your SoC model, core topology, 64-bit ABI support, and clock frequency scaling where supported.
• Thermal Throttling: Real-time status from Android's PowerManager (Normal, Moderate, Severe, Critical) to diagnose overheating during gaming or charging.

2. APP ACTIVITY & USAGE AUDIT
• Real Foreground Tracking: See which apps you use most with daily and weekly usage history via Android Usage Access.
• App Standby Tiers: Identify whether the system has placed background apps into Active, Working Set, Frequent, or Restricted standby buckets.
• Fast App Actions: Jump directly to the official Android App Info screen to safely Force Stop misbehaving apps or clear cache.

3. STORAGE ANALYTICS
• Disk Volume Overview: Inspect total, used, and free space across internal and external storage volumes.
• Package Breakdown: Analyze installed apps by APK code size, user data, and temporary cache without needing invasive storage permissions.
• System Storage: Truthful accounting of reserved operating system space.

4. BATTERY & HARDWARE HEALTH
• Live Electrical Metrics: Real-time current draw in milliamps (mA), operating voltage (mV), and battery temperature (°C).
• Battery Cycle Count: View verified hardware battery cycle counts on supported Android 14+ devices.
• Display & Sensors: Check your exact screen resolution, density DPI, refresh rate (60Hz/90Hz/120Hz), and all physical onboard sensors.

5. LOCAL-FIRST PRIVACY & HISTORY
• 100% Offline: Gauge contains ZERO internet permissions. Your device metrics never leave your phone.
• Bounded History: Record performance trends locally with customizable 7, 30, or 90-day automatic retention.
• Data Export: Export your performance logs to standard CSV or JSON anytime via Android's secure file picker.

WHY GAUGE DOES NOT INCLUDE A "RAM CLEANER":
Modern Android uses Linux virtual memory management: unused RAM is wasted RAM. Killing background apps forces Android to immediately reload them, causing battery drain and stutter. Gauge teaches you how Android actually manages memory and helps you take real control safely.

PERMISSIONS & TRANSPARENCY:
• Usage Access (Optional): Required only to calculate app foreground time and package storage breakdown.
• Notifications (Optional): Required only if you enable local threshold alerts on Android 13+.
• Internet: NONE. Gauge does not request, contain, or use network access.
```

---

## 3. Play Store Policy Compliance Verification

- **Misleading Claims Policy:** Passed. Zero promises of "cooling CPU", "boosting speed", or "extending battery life by 50%".
- **Package Visibility Policy:** Passed. Queries only launcher-intent packages, fully complying with Google Play's restrictive `QUERY_ALL_PACKAGES` policy.
- **Privacy Policy:** Passed. Zero remote data collection; privacy policy explicitly documents that zero bits leave the device.
