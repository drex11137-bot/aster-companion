# ADR-002: Truthful Diagnostics & Rejection of Snake-Oil "RAM Cleaners"

## Status
Accepted

## Context
A prevalent anti-pattern in the Android utility ecosystem is the "RAM Booster" or "Task Killer". On modern Android (API 29+), Linux kernel Low Memory Killer (LMK) manages cached memory automatically. Force-killing cached processes triggers OS restarts, wasting CPU cycles and battery power. Furthermore, SELinux blocks untrusted apps from reading `/proc/stat` or inspecting other apps' private memory.

## Decision
1. GAUGE completely rejects "Kill Background Apps", "Boost RAM", and "Cool CPU" buttons.
2. GAUGE provides deep links directly to official Android App Settings (`Settings.ACTION_APPLICATION_DETAILS_SETTINGS`), empowering the user to make informed choices.
3. GAUGE never fakes global CPU percentages or other apps' memory; instead, it discloses Android SELinux security boundaries transparently.

## Consequences
- **Positive**: Compliant with Google Play Developer Policies and Anti-Slop doctrine; establishes technical credibility and trust with power users.
- **Trade-off**: Requires clear educational messaging (`HonestDisclosureBanner`) explaining why certain metrics are restricted on modern Android.
