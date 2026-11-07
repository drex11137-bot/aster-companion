# Aster Companion: API & Protocol Specification (v1.1)

---

## 1. Overview & General Architecture

The **Aster Companion API** is an OpenAPI 3.1.0 compliant REST, WebRTC, and WebSocket interface providing secure communication between mobile (Android/iOS) and laptop clients, the edge broker layer, and the Supabase PostgreSQL platform.

### 1.1 Base URLs
- **REST Edge API**: `https://api.astercompanion.com/api`
- **Realtime WebRTC Signaling**: `https://api.astercompanion.com/api/realtime/session`
- **Voice Edge WebSocket**: `wss://realtime.astercompanion.com/api/realtime/voice`
- **Frame Ingestion WebSocket**: `wss://ingest.astercompanion.com/api/ingest/stream`

### 1.2 Authentication & Security Headers
All protected REST endpoints and WebSocket handshakes require standard Bearer token authentication and the explicit active profile identifier:

| Header Name | Type | Description |
| :--- | :--- | :--- |
| `Authorization` | `string` | `Bearer <Supabase_JWT_Token>` issued upon login |
| `X-Profile-ID` | `UUID` | Active companion profile UUID. Matches `current_setting('app.active_profile_id')` |
| `X-Device-ID` | `string` | Unique hardware identifier of the calling device |
| `Idempotency-Key` | `UUID` | Required on state-mutating requests (`/api/actions/execute`, `/api/memory/share`) |

### 1.3 Standard Error Format (RFC 7807 Problem Details)
All HTTP errors return `Content-Type: application/problem+json`:
```json
{
  "type": "https://api.astercompanion.com/errors/profile-limit-exceeded",
  "title": "Profile Limit Exceeded",
  "status": 409,
  "detail": "Account already possesses the maximum allowed 2 companion profiles (PRD §9.1).",
  "instance": "/api/profiles",
  "code": "MAX_PROFILES_REACHED",
  "timestamp": "2026-11-01T12:00:00Z"
}
```

---

## 2. Authentication & Companion Profile Management

### 2.1 Register New Account
`POST /api/auth/register`  
Creates a new primary account and establishes baseline credentials in Supabase GoTrue Auth.

#### Request Body
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "display_name": "Alex",
  "device_id": "android-hw-a89c20",
  "platform": "android"
}
```

#### Response (`201 Created`)
```json
{
  "user_id": "d3b07384-d113-494b-9c8e-0123456789ab",
  "email": "user@example.com",
  "access_token": "eyJhbGciOi...",
  "refresh_token": "rt_87361a9...",
  "expires_in": 3600
}
```

---

### 2.2 List Companion Profiles
`GET /api/profiles`  
Retrieves all companion profiles associated with the authenticated account (max 2 profiles per PRD §9.1).

#### Response (`200 OK`)
```json
{
  "profiles": [
    {
      "id": "e4a18204-c324-4f4b-8712-111111111111",
      "user_id": "d3b07384-d113-494b-9c8e-0123456789ab",
      "name": "Aster",
      "is_default": true,
      "personality": {
        "warmth": 0.85,
        "humor": 0.70,
        "formality": 0.30,
        "response_length": "concise",
        "proactivity_level": "moderate"
      },
      "avatar": {
        "presentation": "feminine",
        "apparent_age": 28,
        "hair_style": "long_wavy",
        "hair_color": "#2A1810",
        "skin_tone": "#E0AC69",
        "clothing_preset": "graphite_blazer",
        "ambient_glow_color": "#E59843"
      },
      "voice": {
        "provider": "openai",
        "voice_id": "shimmer",
        "speaking_rate": 1.05,
        "pitch_shift": 0.0
      },
      "created_at": "2026-11-01T08:00:00Z"
    },
    {
      "id": "f5b29315-d435-4e5c-9823-222222222222",
      "user_id": "d3b07384-d113-494b-9c8e-0123456789ab",
      "name": "Nova",
      "is_default": false,
      "personality": {
        "warmth": 0.60,
        "humor": 0.20,
        "formality": 0.80,
        "response_length": "detailed",
        "proactivity_level": "low"
      },
      "avatar": {
        "presentation": "masculine",
        "apparent_age": 34,
        "hair_style": "short_fade",
        "hair_color": "#1A1A1A",
        "skin_tone": "#8D5524",
        "clothing_preset": "minimalist_turtleneck",
        "ambient_glow_color": "#7966F3"
      },
      "voice": {
        "provider": "gemini",
        "voice_id": "Aoede",
        "speaking_rate": 0.95,
        "pitch_shift": -0.05
      },
      "created_at": "2026-11-01T09:30:00Z"
    }
  ],
  "total_count": 2,
  "max_allowed": 2
}
```

---

### 2.3 Create Companion Profile (Max 2 Enforced)
`POST /api/profiles`  
Creates a new companion profile. If the account already has 2 profiles, the server rejects the request with HTTP `409 Conflict`.

#### Request Body
```json
{
  "name": "Nova",
  "personality": {
    "warmth": 0.60,
    "humor": 0.20,
    "formality": 0.80,
    "response_length": "detailed"
  },
  "avatar": {
    "presentation": "masculine",
    "apparent_age": 34,
    "hair_style": "short_fade",
    "hair_color": "#1A1A1A",
    "skin_tone": "#8D5524"
  },
  "voice": {
    "provider": "gemini",
    "voice_id": "Aoede"
  }
}
```

#### Response (`201 Created`)
```json
{
  "id": "f5b29315-d435-4e5c-9823-222222222222",
  "name": "Nova",
  "created_at": "2026-11-01T12:00:00Z"
}
```

#### Error Response (`409 Conflict - Profile Limit Exceeded`)
```json
{
  "type": "https://api.astercompanion.com/errors/profile-limit-exceeded",
  "title": "Max Profile Limit Exceeded",
  "status": 409,
  "detail": "Account already possesses the maximum allowed 2 companion profiles (PRD §9.1). Delete an existing profile before creating a new one.",
  "code": "MAX_PROFILES_REACHED"
}
```

---

### 2.4 Profile Switching & Device Lock
`POST /api/profiles/{profile_id}/switch`  
Activates the chosen companion profile on the calling device while guaranteeing that no other profile is concurrently active on that device (PRD §9.5).

#### Request Body
```json
{
  "device_id": "android-hw-a89c20",
  "previous_session_id": "sess_8910a",
  "flush_outbox": true
}
```

#### Response (`200 OK`)
```json
{
  "status": "SWITCHED",
  "active_profile_id": "e4a18204-c324-4f4b-8712-111111111111",
  "device_id": "android-hw-a89c20",
  "new_session_id": "sess_9921b",
  "active_profile_name": "Aster",
  "switched_at": "2026-11-01T12:05:00Z"
}
```

---

## 3. Realtime Voice Broker & Full-Duplex WebRTC

### 3.1 Request Ephemeral Voice Session Credentials
`POST /api/realtime/session`  
Vends a short-lived ephemeral client secret (TTL 60s) allowing direct WebRTC or WebSocket streaming to OpenAI Realtime or Gemini Live. Master API keys never leave the server.

#### Request Body
```json
{
  "provider": "openai",
  "modalities": ["audio", "text"],
  "voice": "shimmer",
  "input_audio_format": "pcm16",
  "output_audio_format": "pcm16",
  "turn_detection": {
    "type": "server_vad",
    "threshold": 0.5,
    "prefix_padding_ms": 300,
    "silence_duration_ms": 400
  }
}
```

#### Response (`200 OK`)
```json
{
  "session_id": "sess_rt_99382",
  "ephemeral_key": "ek_live_89127409127304",
  "webrtc_endpoint": "https://api.openai.com/v1/realtime",
  "expires_at": 1730440060,
  "profile_id": "e4a18204-c324-4f4b-8712-111111111111"
}
```

---

### 3.2 Realtime Voice WebSocket Protocol (`wss://realtime.astercompanion.com/api/realtime/voice`)
For platforms using direct WebSocket streaming, the client and server exchange strict JSON frames and binary audio chunks.

#### 1. Client Event: Speech Started (Barge-In)
Dispatched immediately when client Silero VAD detects speech onset.
```json
{
  "event_id": "evt_01",
  "type": "input_audio_buffer.speech_started",
  "audio_start_ms": 1240,
  "item_id": "msg_user_382"
}
```

#### 2. Client Event: Append Audio Buffer
Dispatches raw 16kHz 16-bit linear PCM audio chunk (Base64 encoded or binary sub-protocol).
```json
{
  "event_id": "evt_02",
  "type": "input_audio_buffer.append",
  "audio": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA..."
}
```

#### 3. Client Event: Cancel Response
Cancels active model speech generation during barge-in.
```json
{
  "event_id": "evt_03",
  "type": "response.cancel"
}
```

#### 4. Server Event: Streaming Audio Delta
```json
{
  "event_id": "evt_srv_88",
  "type": "response.audio.delta",
  "response_id": "resp_001",
  "item_id": "item_001",
  "output_index": 0,
  "content_index": 0,
  "delta": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA..."
}
```

---

## 4. Continuous Frame Ingestion API

### 4.1 Ingest Screen Frame
`POST /api/ingest/frame`  
Accepts a timestamped screen capture frame with monotonic sequence numbers, perceptual hash checksums, and client telemetry.

#### Headers
```http
Content-Type: multipart/form-data
X-Profile-ID: e4a18204-c324-4f4b-8712-111111111111
X-Device-ID: android-hw-a89c20
X-Capture-FPS: 60.0
X-Upload-FPS: 1.0
```

#### Multipart Form Fields
- `metadata`: JSON payload:
  ```json
  {
    "device_sequence": 1042,
    "timestamp_epoch_ms": 1730440000120,
    "phash": "a8f3b2c1d4e5f607",
    "hamming_distance_from_previous": 18,
    "source_app_package": "com.android.chrome",
    "gap_detected": false,
    "gap_duration_ms": 0
  }
  ```
- `frame`: Binary JPEG image payload (`image/jpeg`).

#### Response (`202 Accepted`)
```json
{
  "status": "ACCEPTED",
  "frame_id": "frm_991823",
  "device_sequence": 1042,
  "ingest_timestamp": "2026-11-01T12:00:00.125Z",
  "analysis_status": "QUEUED"
}
```

---

## 5. Memory Search & Explicit Item Sharing

### 5.1 Hybrid Memory Search
`POST /api/memory/search`  
Executes cosine distance vector similarity search and BM25 text search against the PostgreSQL `memories` table, strictly constrained to `app.active_profile_id`.

#### Request Body
```json
{
  "query": "What movies did we discuss watching last week?",
  "categories": ["episodic", "semantic"],
  "min_confidence": 0.70,
  "limit": 5
}
```

#### Response (`200 OK`)
```json
{
  "memories": [
    {
      "id": "mem_001",
      "profile_id": "e4a18204-c324-4f4b-8712-111111111111",
      "category": "episodic",
      "content": "User was watching Inception on Netflix and discussed Christopher Nolan's sound design.",
      "confidence": 0.94,
      "provenance": {
        "source": "screen_awareness",
        "package": "com.netflix.mediaclient",
        "timestamp": "2026-10-25T20:15:00Z"
      },
      "similarity_score": 0.89
    }
  ],
  "profile_id": "e4a18204-c324-4f4b-8712-111111111111",
  "total_found": 1
}
```

---

### 5.2 Explicit Memory Sharing (PRD §9.4)
`POST /api/memory/share`  
Deliberately shares a specific memory item from the active profile to the secondary companion profile under the same account. Requires explicit user confirmation.

#### Request Body
```json
{
  "memory_id": "mem_001",
  "source_profile_id": "e4a18204-c324-4f4b-8712-111111111111",
  "target_profile_id": "f5b29315-d435-4e5c-9823-222222222222",
  "user_confirmed": true,
  "confirmation_timestamp": "2026-11-01T12:10:00Z"
}
```

#### Response (`201 Created`)
```json
{
  "share_id": "shr_88291a",
  "memory_id": "mem_001",
  "source_profile_id": "e4a18204-c324-4f4b-8712-111111111111",
  "target_profile_id": "f5b29315-d435-4e5c-9823-222222222222",
  "confirmed_by_user": true,
  "created_at": "2026-11-01T12:10:00Z",
  "revoked_at": null
}
```

---

### 5.3 Revoke Memory Share
`DELETE /api/memory/share/{share_id}`  
Instantly revokes access to the shared memory. RLS policies immediately block the target profile from querying this row.

#### Response (`200 OK`)
```json
{
  "share_id": "shr_88291a",
  "status": "REVOKED",
  "revoked_at": "2026-11-01T12:15:00Z"
}
```

---

## 6. Action Approvals & Idempotency Gatekeeper

### 6.1 Propose Agentic Action
`POST /api/actions/propose`  
Submitted by the reasoning agent when tool invocation is needed. Gated by risk level.

#### Request Body
```json
{
  "tool_name": "gmail.send_message",
  "risk_level": "consequential",
  "parameters": {
    "to": "partner@company.com",
    "subject": "Q3 Contract Signed",
    "body": "Hi, please find the signed agreement attached."
  },
  "rationale": "User instructed: 'Send the signed contract to our partner.'"
}
```

#### Response (`200 OK`)
```json
{
  "action_id": "act_88392",
  "status": "PENDING_APPROVAL",
  "risk_level": "consequential",
  "requires_user_confirmation": true,
  "confirmation_token": "conf_tok_7721839a820",
  "preview": {
    "title": "Send Email",
    "recipient": "partner@company.com",
    "subject": "Q3 Contract Signed"
  }
}
```

---

### 6.2 Execute Approved Action (Idempotency Enforced)
`POST /api/actions/execute`  
Executes an approved action. Guarantees that duplicate submissions with the same `Idempotency-Key` return the cached execution result without re-executing external side effects.

#### Headers
```http
Idempotency-Key: 7b8f9e20-4a1b-4f5c-8d3e-9012345678ab
X-Profile-ID: e4a18204-c324-4f4b-8712-111111111111
```

#### Request Body
```json
{
  "action_id": "act_88392",
  "confirmation_token": "conf_tok_7721839a820"
}
```

#### Response (`200 OK`)
```json
{
  "action_id": "act_88392",
  "status": "COMPLETED",
  "idempotency_key": "7b8f9e20-4a1b-4f5c-8d3e-9012345678ab",
  "executed_at": "2026-11-01T12:20:00Z",
  "tool_result": {
    "message_id": "gm_msg_991823091",
    "status": "SENT"
  },
  "verified": true
}
```

---

## 7. External Integrations & OAuth 2.0 PKCE

### 7.1 Start OAuth PKCE Flow
`POST /api/integrations/oauth/start`  
Generates a cryptographically random `state`, `code_verifier`, and `code_challenge` (S256) per RFC 7636.

#### Request Body
```json
{
  "provider": "google",
  "scopes": [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/drive.file"
  ],
  "redirect_uri": "com.astercompanion.app:/oauth2callback"
}
```

#### Response (`200 OK`)
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&response_type=code&scope=...&code_challenge=...&code_challenge_method=S256&state=...",
  "state": "st_99812a8301b",
  "expires_in": 300
}
```

---

### 7.2 Disconnect External Integration
`DELETE /api/integrations/{provider}`  
Revokes access tokens with the third-party identity provider and permanently removes encrypted refresh tokens from the database.

#### Response (`200 OK`)
```json
{
  "provider": "google",
  "status": "DISCONNECTED",
  "tokens_revoked": true,
  "disconnected_at": "2026-11-01T12:25:00Z"
}
```
