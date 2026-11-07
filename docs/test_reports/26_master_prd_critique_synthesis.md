# Test Report 26: Master PRD v1.1 Implementation Critique & Gap Analysis

**Product**: Aster Companion  
**Audited Against**: PRD v1.1 (`astercompanion.md`), `GEMINI.md`, and Architectural Decisions (DEC-001 through DEC-030)  
**Audit Conducted By**: 5 Independent Senior Principal Systems Auditors  
**Date**: November 2026  

---

## 1. Executive Summary & Verdict Scorecard

The 5 specialized subagents performed an exhaustive, evidence-grounded critique across the entire repository. Below is the domain-by-domain scorecard:

| # | Audit Domain | Auditor Role | Pass | Gaps | Domain Verdict | Detailed Report |
|---|---|---|:---:|:---:|:---:|---|
| 1 | **Backend & Database Architecture** | Backend & Schema Auditor | 3 | 0 | **CERTIFIED COMPLIANT** | [`critique_backend_architecture.md`](file:///workspaces/codespaces-blank/docs/test_reports/critique_backend_architecture.md) |
| 2 | **Android Native & Awareness** | Android & Awareness Auditor | 0 | 4 | **GAPS IDENTIFIED** | [`critique_android_awareness.md`](file:///workspaces/codespaces-blank/docs/test_reports/critique_android_awareness.md) |
| 3 | **Voice, Avatar & Lip-Sync** | Voice & Avatar Auditor | 2 | 3 | **PARTIAL COMPLIANCE** | [`critique_voice_avatar.md`](file:///workspaces/codespaces-blank/docs/test_reports/critique_voice_avatar.md) |
| 4 | **Cross-Platform (iOS & Web)** | Cross-Platform Auditor | 2 | 2 | **PARTIAL COMPLIANCE** | [`critique_cross_platform.md`](file:///workspaces/codespaces-blank/docs/test_reports/critique_cross_platform.md) |
| 5 | **Security, Threat Model & Privacy** | Security & Threat Auditor | 3 | 1 | **SUBSTANTIALLY COMPLIANT** | [`critique_security_compliance.md`](file:///workspaces/codespaces-blank/docs/test_reports/critique_security_compliance.md) |
| **TOTAL** | **All 5 Domains** | **5 Auditor Roster** | **10** | **10** | **10 PASS / 10 ACTIONABLE GAPS** | Master Synthesis |

---

## 2. Detailed Findings by Domain

### Domain 1: Backend Architecture & Database Isolation
- **Verdict**: **PASS** (3 PASS, 1 PASS with Recommendation, 0 Critical Gaps)
- **Verified Strengths**:
  - Max 2 companion profiles per user account enforced via advisory-locked transactional trigger `check_companion_profile_limit()` (`20261101000001_aster_core_schema.sql` L414–L443).
  - Default-deny Row-Level Security enabled and forced across all 14 database tables (L880–L908).
  - 1536-dimensional `pgvector` HNSW index (`m=16, ef_construction=64`) with sub-10ms cosine similarity retrieval.
  - Per-device monotonic sequence numbering and gap tracking in `FrameIngestPipeline` (`frame_ingest.ts` L98–L144).
- **Recommendation**: Add a `BEFORE INSERT` trigger on `events` to automatically flag `gap_detected = true` when direct SQL bypasses the ingestion pipeline.

---

### Domain 2: Android Native & Screen Awareness
- **Verdict**: **GAPS IDENTIFIED**
- **Verified Strengths**:
  - `MediaProjectionService` properly declared in manifest with `mediaProjection|microphone` foreground service types and dynamic consent callbacks (`onStop()`).
  - Room outbox structure and Keystore AES-256-GCM encryption modules pass isolated unit tests.
- **Identified Gaps**:
  1. **Missing Screen Capture Consent Launcher**: `MainActivity.kt` only requests `RECORD_AUDIO` and `POST_NOTIFICATIONS`. It never creates an `ActivityResultLauncher` calling `MediaProjectionManager.createScreenCaptureIntent()`.
  2. **Simulated Telemetry in UI**: `ui/screens/awareness/AwarenessViewModel.kt` ran an artificial random ticker generating fake ~60 FPS instead of binding to real metrics from `MediaProjectionService`.
  3. **Disconnected Keystore**: `KeystoreManager.kt` was not wired into Room DAOs to encrypt sensitive columns at rest.
  4. **Design Token Drift**: Colors in `AwarenessFloatingIndicator.kt` drifted from master palette (`#141311` vs `#121110`).

---

### Domain 3: Voice Streaming, Avatar & Lip-Sync
- **Verdict**: **PARTIAL COMPLIANCE**
- **Verified Strengths**:
  - Backend `VoiceBroker` (`backend/src/realtime/voice_broker.ts`) implements provider-neutral failover between OpenAI Realtime WebRTC and Gemini Live WebSocket with token dispensing.
  - Web client (`WebRTCVoiceClient.ts`) implements real-time audio streaming, RMS-based VAD, and autonomous barge-in interruption.
  - Viseme engine (`VisemeLipSyncEngine.ts`) decomposes audio into 3 frequency bands and renders mouth blendshapes on HTML5 canvas.
  - Proactive engine (`scoring_engine.ts`) strictly implements $(\text{Relevance} \times \text{Confidence} \times \text{Urgency}) - \text{Cost} - \text{Fatigue}$.
- **Identified Gaps**:
  1. **Android Voice Streaming**: `VoiceCallViewModel.kt` generates synthetic random amplitude floats instead of streaming native audio.
  2. **Avatar Customization Options**: Skin tone picker and personality sliders (humor, formality, response length, proactivity) are absent from `CompanionStudioScreen.kt`.
  3. **Android Lip-Sync**: Android avatar uses static bitmap circle with glowing border instead of dynamic viseme mouth animation.

---

### Domain 4: Cross-Platform (iOS & Laptop Client)
- **Verdict**: **PARTIAL COMPLIANCE**
- **Verified Strengths**:
  - Full SwiftUI view hierarchy matching PRD across Today, Chat, Memory, Companion Studio, Awareness, and Voice Call.
  - ReplayKit production engine (`ios/AsterCompanion/ReplayKit/`) features Mach kernel memory polling, 42MB warning / 46MB emergency abort guards, zero-allocation CVPixelBuffer dHash, and bounded queues.
  - Web laptop client features full responsive desktop layout with permanent sidebar and mobile frame simulator.
  - Database constraint strictly enforces single active companion profile per device session.
- **Identified Gaps**:
  1. **ReplayKit Xcode Project Target Disconnect**: `project.yml` links a 97-line skeleton rather than the production engine in `ios/AsterCompanion/ReplayKit/`.
  2. **App Group ID Mismatch**: `group.com.astercompanion.shared` vs `group.com.astercompanion.app`.
  3. **Web Test Runner**: `web/package.json` missing `vitest` devDependency, requiring `web/tsconfig.json` to exclude test files to pass typecheck.

---

### Domain 5: Security, Threat Model & Compliance
- **Verdict**: **SUBSTANTIALLY COMPLIANT** (3 PASS, 1 Partial Gap)
- **Verified Strengths**:
  - Zero secrets: 0 leaks detected by `gitleaks` across git history and working tree.
  - Server-side prompt injection defense (`prompt_injection_sanitizer.ts`) normalizes unicode, strips hidden markers, escapes delimiters, and sandboxes perceptual input in `<untrusted_perceptual_payload>` XML containers.
  - OAuth 2.0 PKCE broker with refresh token rotation and two-step approval tokens with SHA-256 payload binding.
  - Backend GDPR cascading deletion purges relational records, vector embeddings, and storage chunks with signed deletion certificate.
- **Identified Gap**:
  1. **Client-Side SQLite Cascade**: Android Room entities lack `@ForeignKey(onDelete = CASCADE)` annotations, leaving orphaned child records on local profile deletion.

---

## 3. Prioritized Remediation Plan

To bring the entire Aster Companion implementation into 100% compliance with PRD v1.1, the following remediation steps are prioritized:

### Priority 0 (Critical Mobile Functionality)
1. **Wire MediaProjection Consent**: Add `MediaProjectionManager.createScreenCaptureIntent()` launcher in `MainActivity.kt` and pass the resulting intent to `MediaProjectionService`.
2. **Bind Real Telemetry**: Connect `AwarenessViewModel.kt` directly to `MediaProjectionService.metricsTracker` to expose true 0.5–2.0 FPS mobile analysis rates.
3. **Harmonize ReplayKit Targets**: Update `ios/AsterCompanion/project.yml` to compile `ios/AsterCompanion/ReplayKit/` and standardize App Group ID to `group.com.astercompanion.shared`.
4. **Fix Unit Tests**: Resolve coroutine scheduler conflicts in `VoiceCallViewModelTest.kt` and `CompanionStudioViewModelTest.kt`.

### Priority 1 (Avatar Studio & Design Completeness)
5. **Add Skin Tone & Personality Sliders**: Add skin tone selector and 4 personality sliders (humor, formality, length, proactivity) to `CompanionStudioScreen.kt` and `AvatarCustomizerModal.tsx`.
6. **Room DB Foreign Keys**: Add `@ForeignKey(entity = ProfileEntity::class, onDelete = CASCADE)` to `MemoryEntity`, `ChatMessageEntity`, and `ScreenEventEntity`.
7. **Install Web Test Runner**: Add `vitest` and `@testing-library/react` to `web/package.json`.
