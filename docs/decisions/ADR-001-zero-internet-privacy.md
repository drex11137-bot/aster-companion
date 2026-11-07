# ADR-001: Zero-Internet Architecture & Local-First Privacy

## Status
Accepted

## Context
System utilities and hardware monitors on mobile platforms frequently monetize through third-party ad networks, telemetry analytics, and data broker SDKs. These SDKs track device identifiers, installed packages, and battery habits.

## Decision
GAUGE strictly omits `android.permission.INTERNET` from `AndroidManifest.xml`. The application has zero socket creation capabilities at the Linux kernel and SELinux levels. All metrics, time-series data, and hardware specifications remain exclusively on the user's physical device.

## Consequences
- **Positive**: 100% offline, privacy guaranteed by OS kernel, zero risk of data exfiltration.
- **Trade-off**: Cloud synchronization and remote diagnostics are impossible by design; data portability is provided via Storage Access Framework (SAF) local file export (CSV / JSON).
