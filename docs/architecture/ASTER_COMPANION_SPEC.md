# Aster Companion: Technical Specification & Implementation Blueprint (v1.1)

---

## 1. Executive Summary & Brand Identity

**Aster Companion** is an autonomous, multimodal, cross-platform digital AI companion designed for Android, iOS, and Laptop desktop clients, backed by a resilient Supabase cloud infrastructure.

- **Brand**: Aster Companion
- **Default Companion Name**: Aster (fully editable by user)
- **Secondary Companion Name**: Nova (for the isolated 2nd profile)
- **Core Personality**: Warm, capable, honest, emotionally sensitive, intellectually rigorous.
- **Design Aesthetic**:
  - Deep Graphite/Black base (`#121110`)
  - Elevated Card Surfaces (`#1C1A18`, `#22201E`)
  - Warm Amber Accent (`#E59843`, `#F5A623`)
  - Restrained Violet Accent (`#7966F3`) for user speech bubbles
  - Warm Cream Typography (`#FAF8F5`)
  - Muted Charcoal Subtitles (`#A09E9B`)
  - Ambient Luminous Halo Glow on the realistic human avatar

---

## 2. System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CLIENT ECOSYSTEM                                │
│  ┌──────────────────────┐  ┌─────────────────────┐  ┌────────────────┐ │
│  │  Android Native App  │  │   iOS Native App    │  │ Laptop Web App │ │
│  │ (Compose, Room, MP)  │  │ (SwiftUI,ReplayKit) │  │(React 18, Vite)│ │
│  └──────────┬───────────┘  └──────────┬──────────┘  └───────┬────────┘ │
└─────────────┼─────────────────────────┼─────────────────────┼──────────┘
              │                         │                     │
              ▼                         ▼                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 EDGE GATEWAY & REALTIME ORCHESTRATION                  │
│   • TLS 1.3 Encryption      • JWT & Profile Token Auth                 │
│   • WebRTC Voice Broker     • Monotonic Event Ingestion                │
│   • Adaptive Frame Buffer   • Action Confirmation Gatekeeper           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      SUPABASE CLOUD PLATFORM                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ PostgreSQL 16 with Default-Deny Row-Level Security (RLS)        │  │
│  │  • max 2 companion profiles per account enforcement trigger      │  │
│  │  • Strict profile-level isolation (Profile A cannot read B)      │  │
│  │  • pgvector (HNSW index) for episodic & semantic memories        │  │
│  │  • Durable event stream with SHA-256 integrity checksums         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────┐    ┌───────────────────────────────┐  │
│  │ Supabase Realtime Channels  │    │  Encrypted Object Storage     │  │
│  │ (Presence & Cross-Device)   │    │  (Resumable Chunk Ingest)     │  │
│  └─────────────────────────────┘    └───────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      MODULAR AI & INTEGRATIONS                         │
│  • OpenAI Realtime API (WebRTC)   • Gemini Live API (Bidi WebSocket)   │
│  • Google Photos Picker & Drive   • Google Calendar & Contacts         │
│  • Shopify Storefront API         • Tavily & Exa Live Web Search       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Account Structure & Two-Profile Isolation (PRD §9)

1. **Max Two Profiles**:
   Each user account supports at most two companion profiles (e.g. `Aster` for everyday productivity, `Nova` for private reflection). This boundary is enforced by a PostgreSQL database trigger (`check_max_two_profiles()`).
2. **Strict Profile-Level Row-Level Security (RLS)**:
   Every query to `memories`, `chat_conversations`, `chat_messages`, `events`, `sessions`, and `actions` requires `profile_id = current_setting('app.active_profile_id')`. Profile A cannot read, insert, update, or delete Profile B's data under any condition.
3. **Single Active Profile Per Device**:
   A device can run only one companion profile at a time. Switching profiles suspends the current session, flushes outbox buffers, resets conversational context, and boots the destination profile without context leakage.
4. **Explicit Item-Level Sharing**:
   No automatic memory sharing exists between profiles. Sharing a specific memory requires:
   - User confirmation modal.
   - Record created in `memory_shares` table with `confirmed_by_user = true`.
   - Immediate revocation capability.

---

## 4. Multimodal Real-Time Voice & Screen Awareness

1. **Full-Duplex Voice**:
   - WebRTC connection to OpenAI Realtime or Gemini Live.
   - Client-side VAD (Voice Activity Detection) with instant barge-in support: when the user speaks, Aster immediately cuts audio output and cancels generation (`response.cancel`).
2. **Screen Awareness Architecture**:
   - **Android**: `MediaProjection` foreground service with `FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION`.
   - **iOS**: `RPBroadcastSampleHandler` ReplayKit broadcast extension with <50MB RAM ceiling.
   - **Laptop**: `navigator.mediaDevices.getDisplayMedia`.
   - **Honest Metrics**: Tracks and reports `capture_fps`, `upload_fps`, `ingest_fps`, and `analysis_fps` independently.
   - **Contextual Control Panel**: Instant floating pill indicator showing active profile and 1-tap pause/mute/stop controls.

---

## 5. Offline-First Resumable Continuity (PRD §6)

1. **Local Outbox Queue**:
   All captured events, chat messages, and memory notes are staged locally in SQLite / Room DB with monotonic sequence numbers and SHA-256 checksums.
2. **Resumable Chunked Upload**:
   Supports network disconnects and packet loss using checkpointed acknowledgment tokens.
3. **Honest Gap Reporting**:
   If frames or audio packets are lost due to device suspension, network dropout, or OS throttling, Aster flags an unrecoverable gap and never fabricates synthetic history.

---

## 6. External Integrations & Two-Step Action Approvals (PRD §11 & §12)

| Integration | Mechanism | Authorization Scope | User Approval Requirement |
|---|---|---|---|
| **Google Photos** | Android Photo Picker / API | Selected items only | Zero background scanning; explicit user selection |
| **Google Drive** | Drive REST API v3 | `drive.file`, `drive.readonly` | Read-only search auto-allowed; file creation confirmed |
| **Gmail** | Gmail API (CASA Tier 2) | `gmail.readonly`, `gmail.compose` | Reading drafts allowed; **Sending email requires confirmation** |
| **Google Calendar**| Calendar API v3 | `calendar.events` | Draft view allowed; **Event creation/deletion requires confirmation** |
| **Shopify** | Storefront GraphQL | Store catalog read-only | Search auto-allowed; **Purchases require biometric confirmation** |
| **Web Search** | Tavily / Exa neural | Public web search | Auto-allowed with safe browsing filters |

---

## 7. Security, Privacy & Regulatory Compliance (PRD §16)

- **OWASP MASVS-v2 Compliance**: Secure Android Keystore & iOS Keychain storage for tokens.
- **OWASP Top 10 for LLM (2025)**: Defensive sanitization of screen OCR and audio transcripts to prevent indirect prompt injection.
- **Nigeria NDPA / NDPC GAID & EU GDPR**:
  - Full Article 20 data portability JSON export.
  - Full Article 17 right-to-erasure cascade deletion across database and object storage.
- **Zero Secrets Policy**: API keys and master tokens are stored only in server-side vaults and never transmitted to mobile clients.
