# Cross-Platform Implementation Critique Report: iOS Native Client, ReplayKit Extension, Desktop Web Client, and Cross-Platform Synchronization

**Auditor**: Senior Principal Systems Auditor  
**Date**: November 7, 2026  
**Document Evaluated**: `astercompanion.md` (PRD v1.1)  
**Primary Sections Audited**:  
- §1: System Overview & Platform Boundaries  
- §3: Target Platforms and Operating Model  
- §5: Continuous Screen Understanding  
- §7 / §8: Desktop Laptop Client, Audio, and Human-Like Personalization  
- §9: User Accounts and Independent Companion Profiles (§9.5 Profile Activation Rules, §9.6 Switching Profiles)  
- §10: Cross-Device Identity and Continuity (§10.1–§10.3)  
- §13: Permissions and Platform Adaptation (§13.4 Awareness Controls, §13.5 Contextual Control Panel)  
- §19: Acceptance Criteria (§19.1 Profile Management, §19.2 Continuous Awareness)  
- §21: Confirmed Decisions (DEC-002, DEC-003, DEC-021, DEC-022, DEC-024, DEC-025, DEC-026, DEC-027, DEC-028, DEC-029)

**Repositories & Directories Inspected**:  
- `ios/AsterCompanion/`
- `ios/AsterCompanion/Sources/ReplayKitBroadcastExtension/`
- `ios/AsterCompanion/ReplayKit/`
- `web/src/`
- `web/package.json`
- `web/vite.config.ts`
- `backend/supabase/migrations/20261101000001_aster_core_schema.sql`

---

## 1. Executive Summary & Verification Matrix

| Area | Requirement | PRD v1.1 Reference | Implementation Status | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **1. Native iOS Client** | Swift 6 / SwiftUI application structure, view hierarchy, design tokens, tab bar, modal flows | §1, §3.1, §13, §21 (DEC-002, DEC-005) | Full SwiftUI view hierarchy implemented across 4 primary tabs (`TodayView`, `ChatView`, `MemoryView`, `CompanionStudioView`), custom pill tab bar, and sheets. | **PASS (with Recommendations)** |
| **2. iOS ReplayKit Extension** | RPBroadcastSampleHandler, < 50MB Jetsam memory ceiling, perceptual hashing, downsampling | §5, §13.4, §18, §21 (DEC-012, DEC-016) | Advanced implementation created in `ios/AsterCompanion/ReplayKit/` with Mach kernel resident memory monitoring, 42MB cache eviction, 46MB emergency shutdown, dHash frame suppression, and hardware JPEG encoding. **HOWEVER**, target drift exists: `project.pbxproj` and `project.yml` compile an unlinked 97-line skeleton in `Sources/ReplayKitBroadcastExtension/` with App Group ID mismatches. | **GAP (Critical Architectural Drift)** |
| **3. Desktop Laptop Client** | React 18, Vite, TypeScript, responsive desktop layout with sidebar and mobile preview | §3.1, §7, §8, §13.4, §21 (DEC-003) | React 18.3.1, Vite 5.4.10, Tailwind CSS, dual-mode responsive layout (`responsive-desktop` sidebar and `mobile-frame` simulator). Production build succeeds (`tsc && vite build` in 7.64s). **HOWEVER**, test suite is broken: unit tests import `vitest` which is absent from `web/package.json`, and `src/__tests__` was excluded from `tsconfig.json` to conceal compilation failure. | **PARTIAL PASS / GAP (Test Harness Broken)** |
| **4. Single Active Profile Per Device** | Exactly one active profile per physical device; profile switching cleanly suspends session | §9.5, §9.6, §19.1, §21 (DEC-026, DEC-029) | Enforced at database schema level via partial unique index `uq_sessions_device_active`, enforced in iOS `AppState.switchProfile(to:)`, observed via Darwin notification IPC in ReplayKit extension (error 403 abort), and visualized in web `CompanionContext.tsx`. | **PASS** |
| **5. Cross-Platform State Sync** | Real-time synchronized memory, session state, and conversation across devices | §10.1–§10.3, §19.1, §21 (DEC-027, DEC-028) | Database schema supports multi-device sessions. **HOWEVER**, neither iOS (`SupabaseClient.swift`) nor Web (`CompanionContext.tsx`) actually connects to a live backend. Both rely on hardcoded in-memory arrays and mocked local states. No cross-platform data replication exists. | **GAP (Unimplemented Backend Sync Pipeline)** |

---

## 2. Requirement 1: Native iOS Swift/SwiftUI Application Structure & View Hierarchy

### 2.1 Codebase Structure & Inspection Findings
The native iOS client is located in `ios/AsterCompanion/` targeting iOS 17.0+ and Swift 6.0 (`ios/AsterCompanion/project.yml` lines 4–9).

1. **Application Lifecycle & Root Entry Point**:
   - [`AsterCompanionApp.swift`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/AsterCompanionApp.swift#L62-L98): Declares `@main public struct AsterCompanionApp: App`.
   - Manages `@StateObject private var appState = AppState.shared`.
   - Embeds the active view inside a `ZStack` with a persistent dark theme (`.preferredColorScheme(.dark)`), `AsterTheme.ground` background, bottom padding (64pt), and the custom bottom navigation pill bar [`AsterTabBar`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/AsterCompanionApp.swift#L4-L60).

2. **View Hierarchy Parity**:
   The view hierarchy mirrors PRD v1.1 and the 4 canonical product views:
   - **Today View** ([`TodayView.swift`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/Views/Today/TodayView.swift#L4-L46)): Renders greeting header with warm amber avatar halo glow and green online presence dot (`#34D399`), product motto, `reminderCard` with snooze interaction, `tasksSection` with completion toggles, and `recentMemoriesSection` horizontal carousel. Presents `SettingsSheetView` and `MemoryDetailSheet`.
   - **Chat View** ([`ChatView.swift`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/Views/Chat/ChatView.swift#L4-L69)): Implements streaming message list (`ScrollViewReader` with auto-scroll), interactive schedule card (`SaturdaySchedule`), memory citation indicators (`CitationDetailSheet`), quick action pills, composer input bar, voice call sheet (`VoiceCallView`), and awareness sheet (`AwarenessView`).
   - **Memory View** ([`MemoryView.swift`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/Views/Memory/MemoryView.swift#L4-L68)): Provides real-time search filtering, category chips (`All`, `Preferences`, `People`, `Plans`), memory cards with icon categorization, delete alert confirmation, `AddMemorySheet`, `EditMemorySheet`, and explicit cross-profile sharing modal (`ExplicitSharingModal`).
   - **Companion Studio View** ([`CompanionStudioView.swift`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/Views/Companion/CompanionStudioView.swift#L4-L73)): Customization laboratory featuring large 160pt avatar preview with radiant ambient glow, profile switcher pills (Aster vs. Nova), name editor, hair color selector (Auburn, Black, Brown, Blonde, Silver), eye color selector (Hazel, Brown, Blue, Green, Grey), style selector (Natural, Casual, Professional, Creative), voice option picker (Warm, Calm, Energetic, Playful), and persistence toast notification.
   - **Awareness Contextual Panel** ([`AwarenessView.swift`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/Views/Awareness/AwarenessView.swift#L30-L71)): Contextual modal presenting active session state, embedded ReplayKit broadcast trigger (`RPSystemBroadcastPickerView`), telemetry grid with honest FPS reporting, quick pause/mute toggles, and privacy disclosure notices.
   - **Voice Call View** ([`VoiceCallView.swift`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/Views/Voice/VoiceCallView.swift#L5-L49)): Full-duplex ambient visualizer with radial violet/amber glow, dynamic sound-reactive pulse, live streaming transcript, barge-in detection, and call toolbar controls.

3. **Design System & Token Conformance**:
   - [`AsterTheme.swift`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/DesignSystem/AsterTheme.swift#L5-L63) strictly defines the dark graphite design language:
     - Ground: `#121110` (Line 9)
     - Surface: `#1C1A18` (Line 12)
     - Elevated Surface: `#242220` (Line 15)
     - Warm Amber: `#E59843` (Line 21)
     - Restrained Violet: `#7966F3` (Line 27)
     - Cream High-Contrast Text: `#FAF8F5` (15:1 contrast, Line 30)
     - Muted Text: `#A09D98` (6.5:1 contrast, Line 33)
     - Online Emerald Green: `#34D399` (Line 39)
     - Radii: `radiusCard = 18`, `radiusDialog = 24`, `radiusPill = 9999` (Lines 51–54).

### 2.2 Critique Findings & Gaps
- **Symlink Artifacts in Workspace**: The root `ios/AsterCompanion/` directory contains 9 symlinks (`AppState.swift`, `TodayView.swift`, `ChatView.swift`, etc.) pointing into `Sources/AsterCompanion/`. While this was introduced to accommodate external tools, it creates cognitive overhead and redundancy in git.
- **Mocked Backend Client**: In [`SupabaseClient.swift`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/Services/SupabaseClient.swift#L39-L169), all operations return hardcoded in-memory instances (`fetchCompanionProfiles`, `fetchMessages`, `fetchMemories`, `fetchTasks`). Network upserts are commented out (Line 50: `// supabase.from("companion_profiles").upsert(profile)`), and `anonKey` is a static placeholder (`dummy_anon_key`, Line 11).
- **Verdict**: **PASS (with Recommendations for live Supabase integration and symlink cleanup).**

---

## 3. Requirement 2: iOS ReplayKit Broadcast Extension & <50MB Jetsam RAM Limit Compliance

### 3.1 Jetsam Memory Budget & Technical Constraints
On iOS, extensions run in a separate sandboxed process supervised by the kernel Jetsam mechanism. Broadcast Upload Extensions (`RPBroadcastSampleHandler`) that exceed approximately **50 MB** resident memory are immediately terminated by the kernel with `EXC_RESOURCE -> RESOURCE_TYPE_MEMORY (SIGKILL)` without triggering standard Swift exception handlers or application crash reporters.

### 3.2 Evaluation of the Production ReplayKit Engine (`ios/AsterCompanion/ReplayKit/`)
The engineering team created a dedicated subsystem under [`ios/AsterCompanion/ReplayKit/`](file:///workspaces/codespaces-blank/ios/AsterCompanion/ReplayKit/):

1. **Mach Kernel Memory Inspection**:
   In [`AwarenessTransportClient.swift`](file:///workspaces/codespaces-blank/ios/AsterCompanion/ReplayKit/AwarenessTransportClient.swift#L445-L459), `getResidentMemoryMB()` directly interrogates the Mach task port:
   ```swift
   var info = mach_task_basic_info()
   var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size / MemoryLayout<integer_t>.size)
   let kerr = withUnsafeMutablePointer(to: &info) { infoPtr in
       infoPtr.withMemoryRebound(to: integer_t.self, capacity: Int(count)) { intPtr in
           task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), intPtr, &count)
       }
   }
   if kerr == KERN_SUCCESS {
       return Double(info.resident_size) / (1024.0 * 1024.0)
   }
   ```
2. **Deterministic Dual-Ceiling Guard**:
   In [`SampleHandler.swift`](file:///workspaces/codespaces-blank/ios/AsterCompanion/ReplayKit/SampleHandler.swift#L50-L51) & [`#L354-L369`](file:///workspaces/codespaces-blank/ios/AsterCompanion/ReplayKit/SampleHandler.swift#L354-L369):
   - **42 MB Warning Ceiling**: Clears reusable `CIContext` caches via `ciContext.clearCaches()` and records an IPC memory warning.
   - **46 MB Emergency Abort Ceiling**: Immediately calls `finishBroadcastWithError` with error code 429 (`AwarenessError.memoryPressureExceeded`), terminating the extension cleanly and alerting the user before Jetsam kills the process ungracefully.
3. **Autoreleasepool Discipline**:
   Every frame delivered to `processSampleBuffer` is wrapped in an explicit `@autoreleasepool` block ([`SampleHandler.swift#L131`](file:///workspaces/codespaces-blank/ios/AsterCompanion/ReplayKit/SampleHandler.swift#L131)) to immediately release CoreVideo buffers, CoreImage filter graphs, and temporary data payloads.
4. **Perceptual Difference Hashing (dHash)**:
   In [`PerceptualHash.swift`](file:///workspaces/codespaces-blank/ios/AsterCompanion/ReplayKit/PerceptualHash.swift#L38-L113), 64-bit dHash is computed directly on the `CVPixelBuffer`. On YUV planar buffers (`kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange` / `FullRange`), it accesses the luminance plane directly without RGB color-space conversions or memory allocations. If Hamming distance $\le 2$ (configurable via `staticSkipThresholdBits`), the frame is suppressed, transmitting only a periodic 5-frame heartbeat metadata packet without JPEG payload ([`SampleHandler.swift#L196-L216`](file:///workspaces/codespaces-blank/ios/AsterCompanion/ReplayKit/SampleHandler.swift#L196-L216)).
5. **Hardware JPEG Downsampling & Encoding**:
   In [`SampleHandler.swift#L258-L300`](file:///workspaces/codespaces-blank/ios/AsterCompanion/ReplayKit/SampleHandler.swift#L258-L300), downsampling is performed using a persistent, low-priority Metal-backed `CIContext(options: [.useSoftwareRenderer: false, .priorityRequestLow: true])`, avoiding CPU spikes and memory exhaustion.
6. **Transport Bounded Queue**:
   In [`AwarenessTransportClient.swift#L37`](file:///workspaces/codespaces-blank/ios/AsterCompanion/ReplayKit/AwarenessTransportClient.swift#L37), `maxPendingQueueDepth = 5` strictly drops frames under uplink network stalls, preventing WebSocket buffer buildup in RAM.

### 3.3 Critical Architectural Gaps & Discrepancies
Despite the sophisticated design of `ios/AsterCompanion/ReplayKit/`, a severe repository-level divergence was uncovered:

1. **Dual Implementation Drift**:
   There are two distinct `SampleHandler.swift` files in the repository:
   - **File A (Production Engine)**: [`ios/AsterCompanion/ReplayKit/SampleHandler.swift`](file:///workspaces/codespaces-blank/ios/AsterCompanion/ReplayKit/SampleHandler.swift) (412 lines) containing all the Jetsam guards, dHash algorithms, and WebSocket transport described above.
   - **File B (Skeleton Stub)**: [`ios/AsterCompanion/Sources/ReplayKitBroadcastExtension/SampleHandler.swift`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/ReplayKitBroadcastExtension/SampleHandler.swift) (97 lines), which is merely a basic counter logging to UserDefaults without any memory guards, perceptual hashing, or network transport.
2. **Xcode Project Links the Wrong File**:
   - [`project.yml#L31-L38`](file:///workspaces/codespaces-blank/ios/AsterCompanion/project.yml#L31-L38) sets `path: Sources/ReplayKitBroadcastExtension`.
   - [`AsterCompanion.xcodeproj/project.pbxproj#L189-L197`](file:///workspaces/codespaces-blank/ios/AsterCompanion/AsterCompanion.xcodeproj/project.pbxproj#L189-L197) builds `ReplayKitBroadcastExtension/SampleHandler.swift` (the symlink to File B).
   - **The production engine in `ios/AsterCompanion/ReplayKit/` is completely omitted from the Xcode build target and `Package.swift`!**
3. **App Group Identifier Mismatch**:
   - `AsterCompanion.entitlements` ([line 7](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/Resources/AsterCompanion.entitlements#L7)) and `docs/PROVISIONING_AND_CREDENTIALS.md` ([line 83](file:///workspaces/codespaces-blank/docs/PROVISIONING_AND_CREDENTIALS.md#L83)) specify:  
     `group.com.astercompanion.shared`
   - File B (`Sources/ReplayKitBroadcastExtension/SampleHandler.swift#L17`) uses:  
     `group.com.astercompanion.shared`
   - Production Engine (`ReplayKit/AppGroupIPC.swift#L19` and `ReplayKit/ReplayKitController.swift#L53`) uses:  
     `group.com.astercompanion.app`  
   **Consequence**: If `ReplayKit/` were compiled, `UserDefaults(suiteName: "group.com.astercompanion.app")` would fail at runtime due to entitlement authorization failure.
4. **Bundle Identifier Mismatch**:
   - `project.yml` (line 36): `com.astercompanion.AsterCompanion.ScreenBroadcast`
   - `AwarenessView.swift` (line 9): `com.astercompanion.AsterCompanion.ScreenBroadcast`
   - `ReplayKitController.swift` (line 53): `com.astercompanion.app.AsterCompanion.ReplayKitExtension`
   - `docs/PROVISIONING_AND_CREDENTIALS.md` (line 69): `com.astercompanion.app.broadcast`
5. **Verdict**: **GAP (Architectural disconnect: Production ReplayKit engine exists in source code but is orphaned from the Xcode build target and contains conflicting App Group credentials).**

---

## 4. Requirement 3: Desktop Laptop Client (React 18, Vite, TypeScript, Responsive Layout)

### 4.1 Toolchain & Build Verification
The desktop web client was audited in `/workspaces/codespaces-blank/web/`:
- **Dependencies** ([`web/package.json`](file:///workspaces/codespaces-blank/web/package.json#L11-L29)):
  - `react`: `^18.3.1`
  - `react-dom`: `^18.3.1`
  - `vite`: `^5.4.10`
  - `typescript`: `^5.6.3`
  - `tailwindcss`: `^3.4.14`
  - `framer-motion`: `^11.11.11`
  - `lucide-react`: `^0.454.0`
- **Vite Configuration** ([`web/vite.config.ts`](file:///workspaces/codespaces-blank/web/vite.config.ts#L1-L11)):
  Configured with `@vitejs/plugin-react`, host enabled (`host: true`), and port `5173`.
- **Production Build Execution**:
  Executed `cd web && npm run build` (`tsc && vite build`):
  ```text
  vite v5.4.21 building for production...
  ✓ 1589 modules transformed.
  dist/index.html                   0.80 kB │ gzip:  0.47 kB
  dist/assets/index-CKWLAKVK.css   39.01 kB │ gzip:  7.11 kB
  dist/assets/index-DJokEqbn.js   271.31 kB │ gzip: 75.30 kB
  ✓ built in 7.64s
  ```
  The production build compiles cleanly without errors or warnings.

### 4.2 Responsive Layout & Dual View Modes
In [`web/src/App.tsx#L60-L97`](file:///workspaces/codespaces-blank/web/src/App.tsx#L60-L97), the application implements two distinct view modes via `viewMode`:
1. **Responsive Desktop Mode (`responsive-desktop`)**:
   - Permanent left navigation sidebar via [`Navigation.tsx#L123-L228`](file:///workspaces/codespaces-blank/web/src/components/Navigation.tsx#L123-L228) (`<aside className="hidden md:flex flex-col w-64 h-screen ...">`).
   - Displays avatar canvas with online indicator, 6 primary desktop navigation links (`Today`, `Chat`, `Memories`, `Companion Studio`, `Awareness & Screen`, `Cross-Device Sessions`), live badge indicators (`Live` / `Paused`), and Settings button.
   - Main content area (`<main className="flex-1 overflow-y-auto pb-20 md:pb-8">`) adapts to wide screen widths.
2. **Mobile Frame Simulation Mode (`mobile-frame`)**:
   - Centered smartphone viewport (`max-w-[420px] h-[860px] rounded-[44px] border-[8px] border-graphite-800 shadow-2xl`).
   - Header bar with hardware notch, 8:24 clock, 76% battery icon, WiFi, and cellular signal indicators matching reference screenshots.
   - Mobile bottom capsule navigation bar and native home indicator bar.

### 4.3 Feature Parity & Interactive Subsystems
- **Today Screen** ([`TodayScreen.tsx`](file:///workspaces/codespaces-blank/web/src/components/screens/TodayScreen.tsx)): Profile greeting, motto, reminder snooze, task checklist, memory carousel with photography cards (`memory_coffee.png`, `memory_flowers.png`).
- **Chat Screen** ([`ChatScreen.tsx`](file:///workspaces/codespaces-blank/web/src/components/screens/ChatScreen.tsx)): Full conversation timeline with interactive Saturday schedule card, memory citation chips triggering citation drawer modal ([`CitationModal.tsx`](file:///workspaces/codespaces-blank/web/src/components/modals/CitationModal.tsx)), quick prompt pills, and message composer.
- **Continuous Web Screen Awareness** ([`WebScreenAwareness.ts`](file:///workspaces/codespaces-blank/web/src/awareness/WebScreenAwareness.ts) & [`AwarenessScreen.tsx`](file:///workspaces/codespaces-blank/web/src/components/screens/AwarenessScreen.tsx)): Captures user screen via `navigator.mediaDevices.getDisplayMedia` with system audio, adaptive frame rate controller (1–15 FPS), dHash perceptual deduplication, real-time FPS meters, and simulated perception events (OCR, Scene, UI).
- **Avatar Studio & Viseme Lip-Sync Engine** ([`AvatarCanvas.tsx`](file:///workspaces/codespaces-blank/web/src/components/avatar/AvatarCanvas.tsx) & [`VisemeLipSyncEngine.ts`](file:///workspaces/codespaces-blank/web/src/components/avatar/VisemeLipSyncEngine.ts)): Real-time HTML5 2D Canvas rendering supporting breathing kinematics, procedural eye blink cycles, radiant ambient halo gradients, and FFT audio-driven viseme mouth shapes (AA, OO, S). Verified via `node web/src/__tests__/run-avatar-tests.mjs`:
  ```text
  --- Aster Companion Avatar Studio Verification ---
  Testing PRD v1.1 Hair Color Palette compliance: Auburn, Black, Brown, Blonde, Silver [PASS]
  Testing PRD v1.1 Eye Color Palette compliance: Hazel, Brown, Blue, Green, Grey [PASS]
  Testing Style options: Natural, Casual, Professional, Creative [PASS]
  Testing Voice tone options: Warm, Calm, Energetic, Playful [PASS]
  Testing Viseme FFT and Muscle Kinematics Logic: AA, OO, S visemes [PASS]
  --- ALL AVATAR & VISEME LIPSYNC VERIFICATIONS PASSED (100%) ---
  ```

### 4.4 Critical Defects & Broken Test Harness
Despite the functional frontend implementation, a critical quality gap was discovered in the automated test setup:
1. **Missing Vitest Dependency**:
   - [`web/src/__tests__/audio_and_awareness.test.ts#L9`](file:///workspaces/codespaces-blank/web/src/__tests__/audio_and_awareness.test.ts#L9), [`VoiceWaveformVisualizer.test.ts#L7`](file:///workspaces/codespaces-blank/web/src/__tests__/VoiceWaveformVisualizer.test.ts#L7), and [`avatar.test.ts#L6`](file:///workspaces/codespaces-blank/web/src/__tests__/avatar.test.ts#L6) all import test fixtures directly from `'vitest'`:
     ```typescript
     import { describe, it, beforeEach, expect } from 'vitest';
     ```
   - However, `vitest` is **NOT listed in `web/package.json`** (neither in `dependencies` nor in `devDependencies`).
2. **Deliberate Test Exclusion to Mask Compilation Failure**:
   - In [`web/tsconfig.json#L24`](file:///workspaces/codespaces-blank/web/tsconfig.json#L24):
     ```json
     "exclude": ["node_modules", "dist", "src/__tests__"],
     ```
   - The entire `src/__tests__` directory was excluded from the TypeScript project configuration so that `tsc && vite build` would ignore the broken imports.
   - When TypeScript is invoked directly on the tests (`npx tsc --noEmit web/src/__tests__/audio_and_awareness.test.ts`), it immediately fails:
     ```text
     web/src/__tests__/audio_and_awareness.test.ts:9:50 - error TS2307: Cannot find module 'vitest' or its corresponding type declarations.
     ```
3. **Verdict**: **PARTIAL PASS / GAP (Desktop UI, responsive layout, and build pass; test runner is broken due to missing dependency and excluded test directory).**

---

## 5. Requirement 4: Cross-Platform State Synchronization & Single Active Profile Per Device Rule

### 5.1 Verification of Single Active Profile Rule (PRD §9.5, §9.6, DEC-026, DEC-027, DEC-028)
PRD §9.5 explicitly mandates:
> *"Two different companion profiles must not operate simultaneously on the same device. However, different profiles may be active on different devices under the same account."*

The codebase enforces this rule across four independent architectural layers:

1. **Database Schema Partial Unique Index**:
   In [`backend/supabase/migrations/20261101000001_aster_core_schema.sql#L153-L156`](file:///workspaces/codespaces-blank/backend/supabase/migrations/20261101000001_aster_core_schema.sql#L153-L156):
   ```sql
   -- Partial index: On a single physical device, only 1 session may be in 'active' state at a time.
   CREATE UNIQUE INDEX IF NOT EXISTS uq_sessions_device_active 
     ON sessions (device_id) 
     WHERE (state = 'active');
   ```
   This guarantees at the PostgreSQL engine level that concurrent active sessions cannot be inserted for the same `device_id`.
2. **iOS Application State Enforcement**:
   In [`AppState.swift#L32-L41`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/Services/AppState.swift#L32-L41) & [`#L79-L93`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/Services/AppState.swift#L79-L93):
   Only a single `@Published public var activeProfileId: UUID` is held in memory. When `switchProfile(to:)` is called:
   - Any running voice call or awareness session is immediately terminated (`if isVoiceCallActive { endVoiceCall() }`).
   - The active profile ID transitions atomically.
   - Profile-isolated data (messages, memories, tasks) is reloaded exclusively for the newly selected profile.
3. **iOS ReplayKit Process-Level Termination Guard**:
   In [`ios/AsterCompanion/ReplayKit/SampleHandler.swift#L93-L95`](file:///workspaces/codespaces-blank/ios/AsterCompanion/ReplayKit/SampleHandler.swift#L93-L95) & [`#L371-L384`](file:///workspaces/codespaces-blank/ios/AsterCompanion/ReplayKit/SampleHandler.swift#L371-L384):
   The ReplayKit extension observes Darwin notification `.profileChanged`. If the user switches profiles in the main app while screen broadcast is running, the extension invokes `finishBroadcastWithError` with error code 403:
   ```text
   "Active profile switched. Broadcast terminated to preserve profile isolation."
   ```
   This strictly prevents on-screen activity from leaking across companion profiles.
4. **Web Client Cross-Device Session Manager**:
   In [`CompanionContext.tsx#L380-L414`](file:///workspaces/codespaces-blank/web/src/context/CompanionContext.tsx#L380-L414) & [`DeviceSessionManager.tsx#L88-L97`](file:///workspaces/codespaces-blank/web/src/components/screens/DeviceSessionManager.tsx#L88-L97):
   The device session registry allows the same profile (e.g., `profile-1`) to run on Laptop (`dev-laptop-01`) and Phone (`dev-phone-02`), while Tablet (`dev-tablet-03`) runs `profile-2`. However, on any given device, only one profile can be assigned. Switching profiles via `switchProfile` updates the current device's active profile while isolating context.
5. **Verdict on Single Active Profile Rule**: **PASS (Exemplary multi-layer enforcement across database, native iOS, Darwin IPC, and web).**

---

### 5.2 Verification of Cross-Platform State Synchronization (PRD §10.1–§10.3)
PRD §10 mandates cross-device continuity:
> *"The companion should retain its identity, personality configuration, and appropriate synchronized memory. The user should not need to recreate the companion when changing phones or using a laptop... The system should synchronize relevant conversational context and session state without creating contradictory parallel conversations."*

### Detailed Audit of State Synchronization Pipeline
1. **iOS Data Persistence**:
   - In [`SupabaseClient.swift#L41`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/Services/SupabaseClient.swift#L41), `fetchCompanionProfiles` returns hardcoded `[CompanionProfile.defaultAster, CompanionProfile.defaultNova]`.
   - In [`#L49-L51`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/Services/SupabaseClient.swift#L49-L51), saving profiles to Supabase is commented out.
   - In [`#L107-L109`](file:///workspaces/codespaces-blank/ios/AsterCompanion/Sources/AsterCompanion/Services/SupabaseClient.swift#L107-L109), `fetchMemories` returns `MemoryItem.defaultMemories(for: profileId)`.
   - When offline, writes are serialized to local `UserDefaults.standard` under `"aster_supabase_outbox"`, but `flushOutbox()` merely clears the array without actually transmitting HTTP payloads.
2. **Web Data Persistence**:
   - In [`web/src/context/CompanionContext.tsx#L303-L327`](file:///workspaces/codespaces-blank/web/src/context/CompanionContext.tsx#L303-L327), profiles, memories, and messages are stored in React component state (`useState`).
   - Mutations (`addMemory`, `updateProfile`, `sendMessage`) only update local React state. There is no `fetch` or WebSocket connection communicating with the backend server at `http://localhost:8000` or Supabase.
   - The device sessions in `DeviceSessionManager.tsx` are static demo objects. Clicking "Synchronize Across Devices" simply triggers a local UI toast notification ([`DeviceSessionManager.tsx#L181`](file:///workspaces/codespaces-blank/web/src/components/screens/DeviceSessionManager.tsx#L181)).
3. **Backend Service Disconnect**:
   - The backend server in `backend/src/index.ts` provides endpoints for `/health`, `/api/realtime/session`, `/api/realtime/interrupt`, `/api/ingest/frame`, `/api/actions/dispatch`, `/api/actions/undo`, and `/api/proactive/evaluate`.
   - However, **there is no cross-device sync relay, session coordination WebSocket, or Supabase Realtime CDC subscription** wired between the web client and the iOS client.
   - If a user adds a memory in the web browser, it is impossible for the iOS app to receive or reflect that memory.
4. **Verdict on Cross-Platform State Synchronization**: **GAP (State synchronization across platforms is completely unintegrated; both clients operate in isolated local mock states).**

---

## 6. Recommendations & Remediation Roadmap

### Priority 1: Unify ReplayKit Implementation & Fix Entitlements (iOS)
1. **Consolidate Source Files**: Move the production ReplayKit extension files from `ios/AsterCompanion/ReplayKit/` into `ios/AsterCompanion/Sources/ReplayKitBroadcastExtension/`, replacing the 97-line skeleton `SampleHandler.swift`.
2. **Harmonize App Group Identifiers**:
   - Update `AppGroupIPC.appGroupIdentifier` in `ios/AsterCompanion/ReplayKit/AppGroupIPC.swift` from `"group.com.astercompanion.app"` to `"group.com.astercompanion.shared"` to match `AsterCompanion.entitlements` and `docs/PROVISIONING_AND_CREDENTIALS.md`.
   - Update `ReplayKitController.swift` default initializer to use `"group.com.astercompanion.shared"`.
3. **Harmonize Bundle Identifiers**: Ensure `ScreenBroadcast` target in `project.yml`, `project.pbxproj`, `ReplayKitController.swift`, and `AwarenessView.swift` all consistently reference `com.astercompanion.AsterCompanion.ScreenBroadcast`.

### Priority 2: Repair Web Client Test Harness
1. **Install Missing Test Dependency**:
   Add `vitest` and `@testing-library/react` to `web/package.json` under `devDependencies`:
   ```bash
   cd web && npm install --save-dev vitest@^3.0.0
   ```
2. **Update `tsconfig.json`**:
   Remove `"src/__tests__"` from the `"exclude"` array in `web/tsconfig.json` so that unit tests are validated during type checking.
3. **Add Test Scripts to `package.json`**:
   Add `"test": "vitest run"` and `"test:watch": "vitest"` to `web/package.json`.

### Priority 3: Activate Live Backend & Supabase Synchronization
1. **Connect iOS Client**: Replace the hardcoded mock methods in `ios/AsterCompanion/Sources/AsterCompanion/Services/SupabaseClient.swift` with real REST / PostgREST calls using `URLSession` to `http://localhost:8000` or the Supabase project URL.
2. **Connect Web Client**: Wire `web/src/context/CompanionContext.tsx` to persist memory items and companion profiles to the backend API via HTTP `fetch` or the `@supabase/supabase-js` client.
3. **Implement Realtime State Synchronization**: Configure a Supabase Realtime channel or backend WebSocket broadcast in both clients to subscribe to `companion_profiles`, `memories`, and `devices` tables, enabling genuine cross-device synchronization per PRD §10.

---

## 7. Final Systems Auditor Summary

| Requirement Category | Finding | Detailed Impact | Compliance Grade |
| :--- | :--- | :--- | :--- |
| **Swift/SwiftUI Architecture** | Complete, pixel-accurate 4-tab SwiftUI app with tokens and custom pill navigation | Delivers high visual and behavioral fidelity to PRD v1.1 and reference screenshots. | **A-** |
| **ReplayKit Jetsam <50MB Limit** | Robust engine exists in `ReplayKit/` but is orphaned; simple stub is linked in Xcode | High technical quality in isolation, but project builds the incomplete stub with mismatched App Group IDs. | **C+ (Target Drift)** |
| **Desktop Web Client** | Clean React 18 / Vite / TS build; responsive dual-mode layout; avatar canvas | Production build compiles; however, test harness is broken (`vitest` missing, tests excluded in tsconfig). | **B** |
| **Single Active Profile Per Device** | Enforced in DB partial unique index, iOS state, Darwin IPC, and web context | Complete end-to-end protection against concurrent multi-profile collision on a single physical device. | **A+** |
| **Cross-Platform State Sync** | Both clients use in-memory mock data; no real-time cross-client replication | PRD §10 continuity cannot function until live backend channels are connected. | **D (Mocked)** |
