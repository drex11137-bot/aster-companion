# ADR-004: Offline Room Persistence & Storage Access Framework Export

## Status
Accepted

## Context
Users diagnosing battery drain, thermal throttling, or memory pressure require historical time-series data. However, unconstrained local logging risks filling storage, while exporting files via legacy external storage permissions requires invasive runtime storage grants.

## Decision
1. GAUGE uses Android Room 2.6.1 with an indexed SQLite schema (`MetricSampleEntity`).
2. Automatic retention policies prune records older than user selection (7, 30, or 90 days).
3. Export is performed via Android Storage Access Framework (`ACTION_CREATE_DOCUMENT`), streaming CSV or JSON data directly to a user-selected file URI without requiring broad filesystem permissions.

## Consequences
- **Positive**: Strict bounded database size (< 5MB for 7 days), zero storage permission requests, standard RFC 4180 CSV and JSON data portability.
- **Trade-off**: Requires user interaction to pick an export destination via system file picker.
