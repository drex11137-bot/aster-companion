# Aster Companion — Authoritative Privacy Policy Specification

**Document Version:** 1.1.0  
**Effective Date:** October 31, 2026  
**Regulatory Class:** Multi-jurisdictional AI Companion, Agentic Workflow & Continuous Perception Platform  
**Compliance Standards:**
- **GDPR** (EU Regulation 2016/679)
- **Nigeria Data Protection Act (NDPA)** 2023 & NDPC GAID (General Application and Implementation Directive)
- **Apple App Store Review Guidelines** § 5.1.1 (Data Collection and Storage) & § 5.1.2 (Data Use and Sharing)
- **Google Play User Data Policy** (Prominent Disclosure, Sensitive Scopes, Runtime Permissions & Account Deletion)
- **California Consumer Privacy Act (CCPA) / CPRA** (Cal. Civ. Code § 1798.100 et seq.)

---

## 1. Executive Summary & Privacy-by-Design Architecture

Aster Companion ("Aster", "the Service", "the Platform") is a cloud-first, multimodal, personalized digital companion designed for cross-device operation across Android, iOS, and desktop platforms. Aster is engineered under the principle of **Zero Unauthorized Leakage** and **Absolute Transparency**.

### 1.1 Architectural Pillars
1. **Isolated Companion Profiles**: Each user account supports a maximum of two independently personalized companion profiles (e.g., Profile A: "Aster", Profile B: "Nova"). As established in PRD v1.1 Decision DEC-021 through DEC-024, these profiles maintain **strict cryptographic and logical isolation**. Memories, chat histories, preferences, and operational contexts are segregated at the database schema, query, and cache levels. There is zero automatic or implicit sharing between profiles.
2. **Explicit Item-Level Sharing (DEC-026)**: Cross-profile context transfer can occur *only* when the user explicitly reviews, authorizes, and confirms the sharing of a specific memory record. Every shared record generates a tamper-evident audit trail and supports immediate revocation or erasure.
3. **User-Controlled Awareness**: Continuous screen understanding and environmental audio awareness are disabled by default. They can only be initiated through explicit, runtime opt-in consent accompanied by non-obstructive visual status indicators and instant one-tap pause/stop controls.
4. **No Sale or Third-Party Behavioral Ad Monetization**: We do not sell user data, train general public foundation models on private user conversations, or license personal data to third-party ad brokers.

---

## 2. Platform-Specific Compliance Disclosures

### 2.1 Apple App Store Guideline 5.1.1 & 5.1.2 Conformance

| App Store Requirement | Aster Architectural & Operational Implementation |
| :--- | :--- |
| **5.1.1(i) Data Collection & Storage** | Aster only requests access to device sensors (Screen Capture, Microphone, Photo Library) when the user initiates a feature requiring that data. Sensor access requires platform authorization modal dialogs with prominent, unambiguous purpose statements. |
| **5.1.1(ii) Minimal Data Gathering** | Frame capture employs adaptive sampling and client-side perceptual differencing (`perceptual_diff.ts`). Static screens produce zero server ingestion bandwidth. Buffers are temporary and bounded. |
| **5.1.1(iii) Safari & Web Tracking** | Aster does not access cross-app IDFA (Identifier for Advertisers) or Safari browsing history. Web searches conducted via integrations operate through dedicated, isolated outbound proxy calls with zero tracking cookies. |
| **5.1.1(v) Account Deletion** | Aster provides direct, in-app account deletion under **Settings > Privacy & Security > Delete Account**. Initiating deletion triggers our automated Cascade Deletion Worker (`cascade_deletion_worker.ts`), permanently purging all companion profiles, memories, chat messages, biometric voice models, and raw media chunks within 60 seconds, issuing an immutable deletion certificate. |
| **5.1.2 Data Use & Sharing** | No personal data or user-generated content is shared with unauthorized third parties. External integrations (Google, Shopify) require dedicated OAuth authorization code grants with PKCE and least-privilege scopes. |

### 2.2 Google Play User Data & Permission Policy Conformance

| Google Play Requirement | Aster Architectural & Operational Implementation |
| :--- | :--- |
| **Prominent Disclosure & Consent** | Prior to launching `MediaProjection` screen capture or foreground audio recording, Aster displays a fullscreen, explicit disclosure detailing: (1) what data is captured (on-screen content), (2) why it is needed (contextual assistance), and (3) that capture can be paused or terminated at any instant via the persistent status bar notification. |
| **Foreground Service (FGS) Policy** | Media projection runs strictly under `FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION`. Microphone capture runs strictly under `FOREGROUND_SERVICE_TYPE_MICROPHONE`. A persistent, non-dismissible notification is displayed while active, providing one-tap **Stop Capture** and **Mute Mic** controls. |
| **Photo & Video Permissions (READ_MEDIA_IMAGES)** | In compliance with Android 13/14 Photo Picker requirements, Aster uses the system **Android Photo Picker** (`ACTION_PICK_IMAGES`). Aster never requests broad `READ_MEDIA_IMAGES` or `READ_EXTERNAL_STORAGE` permissions, accessing only user-selected media items. |
| **Account Deletion Web Requirement** | In accordance with Google Play's Account Deletion policy, Aster provides both an in-app deletion button and a publicly accessible web portal endpoint (`https://companion.aster.io/privacy/delete-account`) allowing users to request complete account and data erasure without needing the app installed. |

### 2.3 Nigeria Data Protection Act (NDPA) 2023 & NDPC GAID Conformance

| NDPA 2023 Statutory Section | Aster Compliance Mechanism |
| :--- | :--- |
| **Section 24 (Principles of Data Processing)** | Lawfulness, fairness, and transparency: Data processing is strictly bound to explicit consent (Section 26) and contract performance. |
| **Section 26 (Consent Requirements)** | Explicit, affirmative opt-in consent recorded in an immutable, cryptographically chained ledger (`consent_ledger.ts`) with SHA-256 block hashing and tamper-evident provenance (device ID, IP hash, policy digest, timestamp). |
| **Section 32 (Right to Erasure)** | Cascade deletion removes all personal data from database tables and cloud storage buckets upon request. |
| **Section 34 (Right to Data Portability)** | Data Export Service (`data_export_service.ts`) delivers complete, structured, machine-readable JSON archives within moments of user request. |
| **NDPC GAID High-Risk AI Assessment** | Multimodal continuous perception and voice cloning undergo algorithmic risk auditing, bias evaluation, and continuous data minimization logging. |

### 2.4 EU General Data Protection Regulation (GDPR) Articles 6, 7, 9, 15, 17, 20 & 25

- **Article 6(1)(a) & 7 (Consent)**: Specific, informed, and unambiguous consent tracked with millisecond timestamps and versioned policy digests in `ConsentLedger`.
- **Article 9 (Special Category Data - Biometrics)**: Synthetic voice cloning requires an explicit, separate biometric processing consent module with affirmative non-impersonation declarations.
- **Article 15 (Right of Access)**: Real-time in-app inspection of all stored memories, chat histories, active sessions, and integration tokens.
- **Article 17 (Right to Erasure - "Forgotten")**: Full cascade deletion across relational databases (`companion_profiles`, `memories`, `events`, `sessions`, `chat_messages`, `actions`, `voice_models`) and storage buckets (`media-chunks`, `voice-samples`, `visual-frames`, `attachments`).
- **Article 20 (Right to Data Portability)**: Automated generation of tamper-evident JSON export packages secured by HMAC-SHA256 signatures.
- **Article 25 (Data Protection by Design and by Default)**: Awareness sensors are disabled by default; cloud storage retention policies strictly enforce automatic pruning of unindexed temporary media chunks within 24 hours.

---

## 3. Data Categories Collected and Processed

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA COLLECTION TAXONOMY                        │
├──────────────────────────┬─────────────────────────────────────────────┤
│ Category                 │ Scope & Attributes                          │
├──────────────────────────┼─────────────────────────────────────────────┤
│ Account & Identity       │ User ID (UUID), Email, Auth Credentials,   │
│                          │ Registration Date, Subscription Status      │
├──────────────────────────┼─────────────────────────────────────────────┤
│ Companion Profiles       │ Profile A & B Names, Avatar Appearance     │
│ (Max 2 Isolated)         │ (Hair, Eyes, Style, 3D Preset), Voice ID,   │
│                          │ Warmth/Humor/Formality Parameters           │
├──────────────────────────┼─────────────────────────────────────────────┤
│ Conversational Data      │ User Prompts, Aster Responses, Timestamps, │
│                          │ Multi-modal Attachments, Session IDs        │
├──────────────────────────┼─────────────────────────────────────────────┤
│ Long-Term Memory System  │ Preference Memory, People/Social Context,   │
│                          │ Plans, Procedural Preferences, Explicitly   │
│                          │ Shared Records (with Confidence Scores)     │
├──────────────────────────┼─────────────────────────────────────────────┤
│ Multimodal Awareness     │ Screen Frame Buffers (when active), OCR    │
│ (Opt-in Only)            │ Text Summaries, UI Node Hierarchies,       │
│                          │ Ambient Audio Buffers (Ephemeral)           │
├──────────────────────────┼─────────────────────────────────────────────┤
│ Biometric Voice Models   │ User Training Audio Samples, Acoustic       │
│ (Explicit Consent Only)  │ Embeddings for Synthetic Voice Cloning      │
├──────────────────────────┼─────────────────────────────────────────────┤
│ External Integrations    │ Google OAuth Scopes (Photos Picker, Drive,  │
│                          │ Calendar, Contacts, Gmail Restricted),      │
│                          │ Shopify Store Connection Data               │
├──────────────────────────┼─────────────────────────────────────────────┤
│ Telemetry & Audit Logs   │ Proactive Action Invocations, User Approval │
│                          │ Approvals/Rejections, Device Registry,     │
│                          │ Consent Ledger Transactions                 │
└──────────────────────────┴─────────────────────────────────────────────┘
```

---

## 4. Companion Profile Isolation & Dual-Companion Architecture

Under PRD v1.1 Decision DEC-021:
- A user account may host a maximum of two independently configured companion profiles (e.g., Profile 1: "Aster", Profile 2: "Nova").
- **Zero Cross-Profile Contamination**:
  1. Profile A and Profile B have separate database foreign keys.
  2. Supabase / PostgreSQL Row-Level Security (RLS) policies enforce `profile_id = current_setting('app.active_profile_id')`.
  3. LLM retrieval-augmented generation (RAG) vector searches strictly filter by active `profile_id`. Profile A can never access vector embeddings of Profile B.
  4. Only one profile can be active per physical device at any given moment. Switching profiles pauses and terminates the active session, clearing device RAM buffers before activating the new profile.
- **Selective Memory Sharing (DEC-024 / DEC-026)**:
  - If a user wishes to share a memory (e.g. "Maya prefers oat flat whites") from Aster to Nova, Aster displays an explicit confirmation dialog.
  - Upon confirmation, a clone of the memory record is created under Nova with `source_provenance = 'explicitly_shared_from_other_profile'` and logged in the `selective_sharing_events` audit table.
  - The user can revoke or delete this shared memory at any time.

---

## 5. Multimodal Awareness & Sensor Controls

### 5.1 Screen Awareness Capture
- **Platform Mechanisms**:
  - Android: `MediaProjection` API with system permission dialog and foreground notification.
  - iOS: User-initiated ReplayKit Broadcast Extension (`RPBroadcastSampleHandler`).
  - Desktop: Web MediaDevices `getDisplayMedia()` or macOS `ScreenCaptureKit`.
- **Minimization & Local Processing**:
  - Screen capture utilizes perceptual hash diffing (`perceptual_diff.ts`). If screen content has not changed by at least 1.5% Hamming distance, frames are dropped locally without network transmission.
  - Visual frames transmitted to the cloud are processed for scene understanding and OCR. Raw frame images in `visual-frames` storage buckets are automatically purged after 24 hours unless explicitly pinned by the user as an attachment.

### 5.2 Environmental Audio Capture
- Environmental microphone monitoring is a distinct, separate opt-in from screen capture.
- Audio chunks are processed in rolling ring-buffers in memory for wake-word and context detection. Unprocessed raw audio chunks in `media-chunks` bucket are purged on rolling 60-minute windows.

### 5.3 Instant Revocation & Awareness Controls
- The **Awareness Status Panel** in the app header displays:
  - Active Companion Profile
  - Current Awareness Mode (Screen / Audio / Idle)
  - Real-time Capture FPS and Ingest Health
  - One-tap **Pause Awareness** and **Stop Awareness** controls.
- Revoking consent instantly stops local capture pipelines and invokes `ConsentLedger.revokeConsent()`, which triggers downstream listeners to flush active streaming sockets and wipe in-flight server buffers.

---

## 6. Retention Schedules & Automated Cascade Deletion

### 6.1 Retention Schedule Matrix

| Data Entity | Default Storage Tier | Retention Period | Automatic Expiration Policy |
| :--- | :--- | :--- | :--- |
| **Raw Screen Frame Chunks** | Object Storage (`visual-frames`) | 24 Hours | Automated TTL lifecycle rule deletes objects after 24 hours. |
| **Raw Audio Chunks** | Object Storage (`media-chunks`) | 1 Hour | Rolling ring-buffer deletion. |
| **OCR & Event Summaries** | PostgreSQL (`events`) | 30 Days | Ephemeral events pruned after 30 days unless tagged to long-term memory. |
| **Chat Messages** | PostgreSQL (`chat_messages`) | User Lifetime | Retained until user deletes message, clears session, or closes account. |
| **Long-Term Memories** | PostgreSQL (`memories`) | User Lifetime | Inspectable, editable, and forgettable in Memory Manager at any time. |
| **Biometric Voice Models** | Object Storage + Model Weights | User Lifetime | Retained until voice profile reset or account deletion. |
| **Consent Ledger** | Append-Only Table (`consent_records`)| Account Lifetime | Tombstoned upon account closure; hashed certificates retained for legal defense. |

### 6.2 Cascade Deletion Execution Pipeline
When a user requests account deletion via in-app settings or the web portal:
1. **Authentication & Invalidation**: User credentials and active JWTs/sessions are immediately invalidated.
2. **Upstream Integration Disconnect**: All OAuth refresh tokens for Google, Shopify, etc. are revoked with provider revocation endpoints.
3. **Storage Bucket Purge**: `CascadeDeletionWorker` scans all object storage buckets (`media-chunks`, `voice-samples`, `visual-frames`, `attachments`) prefixed with `users/<userId>/` and executes batch unlinking.
4. **Relational Cascade Erasure**: In transactional order, all rows linked to `userId` across `actions`, `chat_messages`, `events`, `memories`, `voice_models`, `sessions`, `companion_profiles`, and `integration_tokens` are deleted.
5. **Deletion Certificate Issuance**: An immutable cryptographic certificate (`DeletionCertificate`) is generated containing SHA-256 hashes of deleted object counts, duration, and HMAC-SHA256 signature by the compliance authority. Zero PII is retained.

---

## 7. Data Portability & Machine-Readable Export (GDPR Art. 20 / NDPA Sec. 34)

Users have the statutory right to export their complete digital footprint. Aster provides a one-click Data Export function under **Settings > Privacy > Download My Data**:
- **Format**: Structured, portable JSON archive (`aster_export_<exportId>.json`).
- **Archive Contents**:
  - Account configuration and profile configurations (Avatar 3D settings, voice settings, personality parameters).
  - Profile-isolated chat histories.
  - Memory database with category tags, confidence scores, and provenance.
  - Audit trail of tool actions and inter-profile selective sharing events.
  - Connected integration scopes (sanitized: zero tokens or passwords).
  - Device session history.
  - Cryptographic consent ledger history.
- **Tamper-Evident Verification**: The export archive contains a canonical payload SHA-256 hash and digital HMAC signature verifiable via `DataExportService.verifyExportIntegrity()`.

---

## 8. Data Security & Storage Architecture

- **Encryption at Rest**: All database tables, vector embeddings, and object storage buckets are encrypted using AES-256 with Customer-Managed Encryption Keys (CMEK) rotated every 90 days.
- **Encryption in Transit**: All communication between client apps, laptop clients, edge proxies, and cloud services uses TLS 1.3 with HSTS (HTTP Strict Transport Security).
- **OAuth Refresh Token Security**: External integration refresh tokens are encrypted using AES-256-GCM with Additional Authenticated Data (AAD) binding to the specific user and profile (`oauth_pkce_handler.ts`). Replay attacks and token reuse trigger immediate family revocation.
- **Prompt Injection Defense**: All captured screen OCR, audio transcripts, and external API inputs are treated as untrusted and passed through our multi-stage sanitizer (`prompt_injection_sanitizer.ts`) to prevent indirect prompt injection and unauthorized agent action execution.

---

## 9. Children’s Privacy & Age Restrictions

Aster Companion is strictly intended for individuals aged **18 years or older** (or the age of legal majority in the user's jurisdiction). We do not knowingly collect, solicit, or maintain personal information from children under 13 (or under 16 in the EEA/UK under GDPR Article 8, or under 18 under NDPA Section 31). If we discover that a minor has created an account, our Cascade Deletion Worker immediately terminates the account and permanently purges all associated records.

---

## 10. Contact Information & Data Protection Officer (DPO)

For inquiries regarding this Privacy Policy, exercising statutory rights (access, rectification, erasure, portability, objection), or regulatory compliance auditing, contact:

- **Data Protection Officer (DPO)**: `dpo@astercompanion.com`
- **Privacy & Security Team**: `privacy@astercompanion.com`
- **Global Compliance Office**: Aster Technologies Inc., 100 Montgomery St, Suite 2100, San Francisco, CA 94104, USA
- **Nigeria Data Protection Representative**: Aster Technologies Africa Ltd., Victoria Island, Lagos, Nigeria (`ndpa-compliance@astercompanion.com`)
