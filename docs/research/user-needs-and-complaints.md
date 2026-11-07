# GAUGE: User Needs, Jobs-to-be-Done & Pain Points Synthesis
## Public Community Research across Reddit (r/androidapps, r/Android), Play Store Reviews, and Developer Forums

This synthesis extracts genuine user expectations, real jobs-to-be-done (JTBD), and recurring frustrations regarding Android system utilities, telemetry tools, and task managers.

---

## 1. Core Jobs-to-be-Done (JTBD)

### Job 1: "Why does my phone feel slow or warm?"
- **User Context:** The user is experiencing sluggish UI transitions, dropped frames in games, or noticeable device warmth during normal tasks.
- **Underlying Need:** The user wants to know if the device is **thermally throttled** by the OS or if the system is experiencing **memory pressure**.
- **GAUGE Solution:** Overview screen highlights thermal throttling status (`PowerManager.getThermalStatus()`) in real time, explaining in plain language whether the processor is actively limiting performance to protect hardware, alongside an honest Memory Pressure gauge.

### Job 2: "What is eating my battery, and what is its true physical health?"
- **User Context:** Battery life seems worse than when the device was new, or the phone drops percentage rapidly while in use.
- **Underlying Need:** The user wants to inspect current battery discharge rates (mA), operating voltage (mV), temperature (°C), and verified cycle counts (on Android 14+).
- **GAUGE Solution:** Live battery telemetry displays instantaneous current draw in microamperes/milliamperes, voltage, temperature, charging status, and cycle count on API 34+, with clear explanations that third-party apps cannot measure per-app mAh discharge without root.

### Job 3: "What apps have I been using, and what is running in the background?"
- **User Context:** The user wants to review recent app activity, audit screen time, and find rogue background apps.
- **Underlying Need:** Rank apps by actual foreground duration, see launch recency, and understand which apps are placed into restricted standby buckets.
- **GAUGE Solution:** App Activity view aggregates daily and weekly usage using `UsageStatsManager`, displaying launchable applications, last used timestamps, and standby tiers.

### Job 4: "Why is my storage full, and what apps take the most space?"
- **User Context:** Device displays a "Storage Almost Full" system notification.
- **Underlying Need:** Identify which installed packages are consuming the most disk space across APK code size, app data, and temporary cache.
- **GAUGE Solution:** Storage Breakdown view queries `StorageStatsManager` to list all packages sorted by size, separating app code (`appBytes`), user data (`dataBytes`), and cache (`cacheBytes`), with direct deep links to clear cache in system settings.

### Job 5: "What exact hardware, processor, and Android version do I have?"
- **User Context:** The user is troubleshooting compatibility, preparing to buy accessories, or curious about device specifications.
- **Underlying Need:** Reliable, complete enumeration of SoC manufacturer, model, core architecture, supported ABIs, display resolution, refresh rate, and sensors.
- **GAUGE Solution:** Hardware & Specs tab provides clean, copyable specifications derived directly from Android `Build`, `Display`, and `SensorManager` APIs.

### Job 6: "Can I take action on a misbehaving app safely?"
- **User Context:** An app has crashed, frozen, or is consuming excessive resources.
- **Underlying Need:** Stop the application without creating unstable background crash-restart loops.
- **GAUGE Solution:** One-tap action button navigating directly to Android's official system **App Info** screen, where the user can execute a legitimate OS-level "Force Stop" or "Clear Cache".

---

## 2. Top User Complaints & Market Anti-Patterns

### Complaint 1: "Fake RAM Boosters and Snake-Oil Optimizers"
- **Community Evidence:** Highly upvoted posts on Reddit r/androidapps ("PSA: Stop installing RAM boosters and battery savers") consistently warn that apps promising "1-tap speed boosts" are scams.
- **User Voice:** *"These apps kill background apps, which immediately relaunch, causing my phone to lag and draining my battery twice as fast."*
- **GAUGE Mandate:** **Zero fake boosters.** Gauge never pretends to "clean RAM" or "boost speed". It provides an educational guide on how Linux memory management actually works.

### Complaint 2: "Invasive Ads, Fullscreen Takeovers, and Subscription Traps"
- **Community Evidence:** Play Store reviews for top utilities (CPU-Z, CleanMaster, CCleaner) are dominated by 1-star reviews citing fullscreen popups, deceptive "Your phone is infected" alerts, and $49/year subscription traps.
- **User Voice:** *"I opened CPU-Z to check my battery temperature and was hit with a 30-second unskippable video ad with blaring audio."*
- **GAUGE Mandate:** **Zero ads, zero subscriptions, zero in-app purchases.** Gauge is completely free, clean, and respectful.

### Complaint 3: "The Monitoring App Drains More Battery Than the System"
- **Community Evidence:** GitHub issues across open-source system monitors complain of high CPU wakeups from aggressive 100ms background polling loops.
- **User Voice:** *"I installed a monitor to see why my battery was draining, and the monitor itself was using 18% of my battery in the background."*
- **GAUGE Mandate:** **Lifecycle-Aware Polling.** Gauge pauses all polling when the app is backgrounded or the screen is off. Metric sampling runs only when the user is actively viewing the screen, using efficient coroutine state flows.

### Complaint 4: "Killed by Aggressive OEM Battery Savers (Samsung, Xiaomi, Huawei)"
- **Community Evidence:** Websites like *DontKillMyApp.com* document how OEM ROMs aggressively kill background background workers and services.
- **User Voice:** *"The app stops logging after 15 minutes because Samsung's OneUI puts it into deep sleep."*
- **GAUGE Mandate:** Gauge relies on pull-to-refresh and opportunistic `WorkManager` tasks for history rather than brittle persistent background services, gracefully handling device reboots and sleep states.

### Complaint 5: "Mandatory Accounts and Cloud Telemetry"
- **Community Evidence:** Users are increasingly skeptical of utility tools that require signing in with Google or an email address just to see device stats.
- **User Voice:** *"Why does a CPU monitor need my email address and location permission? This is spyware."*
- **GAUGE Mandate:** **Zero Accounts, Zero Network Permissions.** The app omits `INTERNET` permission entirely. All data stays strictly on the device.
