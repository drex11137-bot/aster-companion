# GAUGE: Figma Master Design Specification & Page Architecture
## Page Inventory, Component Library, Responsive Constraints, and Prototype User Flows

**Figma User Account:** Drex (`drex11137@gmail.com` | User ID `1635332431188827930`)  
**Design Tokens:** [`docs/design/figma-tokens.json`](file:///workspaces/codespaces-blank/docs/design/figma-tokens.json)  
**Vector Brand Assets:** [`assets/logo/gauge_logo.svg`](file:///workspaces/codespaces-blank/assets/logo/gauge_logo.svg) | [`assets/mascot/gauge_mascot.svg`](file:///workspaces/codespaces-blank/assets/mascot/gauge_mascot.svg)  
**Status Report on API Capabilities:** As established during initial tool reconnaissance, the public Figma REST API supports read operations (`get_figma_data`, `get_comments`, `get_variables`, `get_components`) and interaction posting (`post_comment`, `post_dev_resource`), but does not permit automated creation of brand new `.fig` files from scratch via API without an existing file key. This document and its accompanying token schemas represent the complete, ready-to-import design artifact specification.

---

## 1. Master Page Structure (9 Canonical Pages)

```text
GAUGE — Figma Document Hierarchy
├── 00 — Research & References (Competitor benchmarks, Mobbin patterns, WCAG contrast audits)
├── 01 — Foundations (Color tokens, typography scale, spacing grids, elevation, shape tokens)
├── 02 — Components (Metric tiles, list rows, action buttons, chips, filter tabs, dialogs)
├── 03 — Onboarding (3-step skippable setup, capability overview, permission transparency)
├── 04 — Main App (Overview/Performance, App Activity, Storage, Hardware Specs)
├── 05 — App Details & Actions (App inspector, storage breakdown, system deep links)
├── 06 — History & Reports (Time-series trend charts, retention selector, CSV/JSON export)
├── 07 — Settings & Permissions (Threshold alerts, quiet hours, data pruning, about GAUGE)
└── 08 — Prototype Flows (Interactive wiring from onboarding through deep-link actions)
```

---

## 2. Page-by-Page Specifications

### Page 00 — Research & References
- **Frame 00.1 — Desktop Benchmarks:** Side-by-side comparison of Windows Task Manager (Performance + App History) and macOS Activity Monitor (Memory Pressure).
- **Frame 00.2 — Competitor Teardowns:** Audit of CPU-Z, DevCheck, and AIDA64, highlighting visual defects (ad clutter, outdated Holo UI) and structural opportunities.
- **Frame 00.3 — Banned Colors Audit Board:** Swatches of the 8 prohibited colors paired with their verified GAUGE replacement tokens.
- **Frame 00.4 — Contrast Proof Board:** Mathematical contrast proofs verifying WCAG AAA (14.8:1) for primary ink and AA (6.2:1) for secondary ink.

### Page 01 — Foundations
- **Color Variables Collection:** Dual-mode semantic color variables (`Light` and `Dark` modes) mapped to `GaugeGround`, `GaugeSurface`, `GaugeOutline`, `GaugeInk`, `GaugeAccent`, and `GaugeSignal`.
- **Typography Scale:**
  - `Display / Large`: 32sp / 38sp line-height (SemiBold)
  - `Title / Screen`: 20sp / 26sp line-height (SemiBold)
  - `Body / Primary`: 15sp / 22sp line-height (Regular)
  - `Telemetry / Number Large`: 28sp / 32sp line-height (Monospace Bold)
  - `Telemetry / Number Medium`: 18sp / 22sp line-height (Monospace Bold)
  - `Label / Uppercase`: 11sp / 14sp line-height (Monospace Tracked +0.06em)
- **Grid & Constraints:** 4dp base spacing grid, 16dp horizontal page margins, responsive constraints (`Scale` or `Left & Right`).

### Page 02 — Component Library & Variants
1. **`MetricTile`:**
   - Variants: `State=Normal`, `State=Warning`, `State=Critical`, `State=Charging`.
   - Elements: Metric label, big monospace value, unit chip, status indicator dot, optional trend sparkline.
2. **`MemoryPressureGauge`:**
   - Circular meter displaying Available vs In-Use RAM with calibrated tick marks and color-coded threshold arc (`Optimal`, `Elevated`, `Critical`).
3. **`AppListItem`:**
   - Variants: `ViewMode=UsageStats`, `ViewMode=StorageBreakdown`.
   - Elements: App icon (40x40dp), app label, package name, primary metric (foreground duration / total MB), secondary metadata (standby bucket / cache size), chevron.
4. **`ActionButton`:**
   - Variants: `Type=Primary`, `Type=Secondary`, `Type=Destructive`, `Type=IconOnly`.
   - States: `Default`, `Hover`, `Pressed`, `Disabled`, `Loading`.
5. **`FilterTabRow`:**
   - Segmented tab control (`Today`, `7 Days`, `30 Days`) with smooth sliding pill highlight.
6. **`EmptyStateCard`:**
   - Mascot illustration ("Gaugey" looking observant), title, clear explanation of why data is absent, and single next-step button.
7. **`PermissionEducationSheet`:**
   - Bottom sheet explaining why Usage Access is needed, with privacy guarantees ("Data never leaves device") and "Open Settings" primary action.

### Page 03 — Onboarding (3-Step Skippable Flow)
- **Step 1 — Welcome to Truthful Monitoring:**
  - Mascot waving, headline: "Truth Before Appearance", bullet points: Zero ads, zero fake boosters, 100% offline.
  - Buttons: "Get Started" (Primary), "Skip" (Text link).
- **Step 2 — What Would You Like to Understand First?**
  - Interactive selection chips: "Device Performance & Heat", "Battery Health & Charging", "Storage & Heavy Apps", "App Screen Time".
  - Selection reorders shortcuts on the Home tab.
- **Step 3 — Transparency & Capability Check:**
  - Real-time probe of detected device capabilities (API level, SoC model, RAM size).
  - Optional Usage Access rationale card with "Grant in Settings" and "Continue with Standard Access" buttons.

### Page 04 — Main App Surfaces (375px Phone & 768px Tablet)
- **Surface 1: Overview (Home):**
  - Header: Device model + battery pill + thermal status badge.
  - Core Gauge: Memory Pressure dial with live GB readings.
  - Secondary Row: Battery voltage/current draw, SoC core frequency, network throughput since boot.
  - Quick Shortcuts: "Inspect Heavy Apps", "Storage Breakdown", "Hardware Details".
- **Surface 2: App Activity:**
  - Search bar + Sort filter (By Foreground Time, By Launch Recency).
  - Time window picker (24h, 7d, 30d).
  - Scrollable list of launchable apps with progress bars representing relative usage share.
- **Surface 3: Storage Breakdown:**
  - Volume capacity bar (Internal Storage: Used vs Free).
  - Category breakdown: Apps, System/OS, Free Space.
  - Package size ranking (Code vs Data vs Cache).
- **Surface 4: Hardware & System Specs:**
  - Grouped accordion cards: Processor (Cores, ABIs), Display (Resolution, Refresh Rate, Density), Battery (Tech, Voltage, Temp, Cycles), Sensors (List of physical sensors).

### Page 05 — App Details & Action Sheet
- Tapping any app opens an inspectable sheet:
  - Full package name, version, target SDK.
  - Exact storage consumption: APK code size, user data, cache size.
  - Usage stats: Total foreground time, last time active, current standby bucket.
  - System Actions: "Open App" (Launches app), "App Info in Settings" (Deep link to system settings for Force Stop / Clear Cache).

### Page 06 — History & Reports
- Bounded time-series graphs (Memory load over last hour/day, battery temperature trend).
- Retention selector (7, 30, 90 days).
- Export button launching SAF file saver for CSV or JSON.

### Page 07 — Settings & Permissions
- Theme switcher (Dark, Light, System).
- Threshold alert toggles (Thermal Throttling Alert, Low Memory Alert).
- "Clear Metric History" button with confirmation modal.
- Privacy & Policy statement (Zero internet permission confirmation).

### Page 08 — Prototype Flows & Micro-Interactions
- Onboarding → Home screen transition with staggered fade-and-rise entrance (300ms cubic-bezier).
- App list drill-down to App Detail bottom sheet.
- Usage Access education sheet → native Settings deep link.
- Memory Pressure dial animating from 0% to current live reading on view appearance.
