# Aster Companion: Provisioning, Credentials & Regulatory Compliance Guide (v1.1)

---

## 1. Zero-Faked-Logic & "Unconfigured Until Provisioned" Doctrine

Aster Companion adheres to a fundamental architectural principle: **Never fake features, never stub logic with mock delays, and never claim unverified cloud or platform capabilities.**

When external API keys, enterprise OAuth client credentials, operating system entitlements, or third-party security certifications (such as Google CASA Tier 2) have not yet been granted or provisioned:
1. The underlying service adapter must register its operational state as `UNCONFIGURED`.
2. The user interface must display clear, truthful status indicators (e.g., `Setup Required` badge) and guide the user to the appropriate configuration flow.
3. The reasoning engine must honestly disclose to the user: *"Google Calendar integration is currently unconfigured. You can connect your Google account in Settings."*
4. Under no circumstances should an unconfigured integration generate synthetic emails, fabricated calendar events, or fake search results.

---

## 2. Complete Environment Variable Specification

### 2.1 Backend Gateway & Edge Services (`backend/.env`)

| Variable Name | Required | Secret? | Default / Example Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `NODE_ENV` | Yes | No | `production` | Node.js runtime environment (`development`, `test`, `production`) |
| `PORT` | Yes | No | `8080` | Port for the backend API and WebSocket server |
| `SUPABASE_URL` | Yes | No | `https://xyz.supabase.co` | Supabase project API gateway endpoint |
| `SUPABASE_ANON_KEY` | Yes | No | `eyJhbGciOi...` | Supabase public anonymous API key (JWT) |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | **YES** | `eyJhbGciOi...` | Supabase privileged service role key (bypasses RLS for admin tasks) |
| `DATABASE_URL` | Yes | **YES** | `postgresql://postgres:[PW]@xyz.pooler.supabase.com:6543/postgres?pgbouncer=true` | Direct pooled PostgreSQL connection string |
| `DATABASE_DIRECT_URL` | Yes | **YES** | `postgresql://postgres:[PW]@xyz.supabase.com:5432/postgres` | Direct non-pooled PostgreSQL URL for migrations and DDL |
| `OPENAI_API_KEY` | Conditional | **YES** | `sk-proj-...` | OpenAI API key for Realtime Voice API (WebRTC) |
| `GEMINI_API_KEY` | Conditional | **YES** | `AIzaSy...` | Google Cloud API key for Gemini Multimodal Live API |
| `GOOGLE_CLIENT_ID` | Conditional | No | `123456789-abc.apps.googleusercontent.com` | Google OAuth 2.0 Web Client ID |
| `GOOGLE_CLIENT_SECRET` | Conditional | **YES** | `GOCSPX-...` | Google OAuth 2.0 Web Client Secret |
| `TAVILY_API_KEY` | Conditional | **YES** | `tvly-...` | Tavily Neural Search API key for live web search |
| `EXA_API_KEY` | Optional | **YES** | `exa-...` | Exa Neural Search API key |
| `TOKEN_ENCRYPTION_KEY` | Yes | **YES** | `64-hex-char-aes-256-key` | 256-bit AES-GCM master key for encrypting stored OAuth refresh tokens |
| `JWT_SECRET` | Yes | **YES** | `base64-random-secret` | Supabase JWT signing secret for edge verification |

### 2.2 Laptop Web Client (`web/.env`)

| Variable Name | Required | Secret? | Default / Example Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `VITE_SUPABASE_URL` | Yes | No | `https://xyz.supabase.co` | Supabase API URL for browser client |
| `VITE_SUPABASE_ANON_KEY` | Yes | No | `eyJhbGciOi...` | Supabase public anon key |
| `VITE_BACKEND_API_URL` | Yes | No | `https://api.astercompanion.com` | Edge API Gateway endpoint |
| `VITE_REALTIME_WS_URL` | Yes | No | `wss://realtime.astercompanion.com` | Edge Voice WebSocket endpoint |
| `VITE_GOOGLE_OAUTH_CLIENT_ID`| Conditional | No | `123456789-web.apps.googleusercontent.com` | Web OAuth Client ID for Google PKCE login |

### 2.3 Android Native Client (`app/local.properties` & Build Config)

| Property Name | Required | Secret? | Example Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `supabase.url` | Yes | No | `https://xyz.supabase.co` | Supabase project URL injected into `BuildConfig` |
| `supabase.anonKey` | Yes | No | `eyJhbGciOi...` | Supabase anon key injected into `BuildConfig` |
| `backend.apiUrl` | Yes | No | `https://api.astercompanion.com` | Backend REST/WebSocket gateway |
| `google.oauthClientId` | Conditional | No | `123456789-android.apps.googleusercontent.com` | Google OAuth Android client ID matching package & SHA-1 |
| `RELEASE_KEYSTORE_PASSWORD` | Release | **YES** | Environment Secret | Password for release APK signing keystore |
| `RELEASE_KEY_ALIAS` | Release | No | `aster_release_key` | Keystore key alias |
| `RELEASE_KEY_PASSWORD` | Release | **YES** | Environment Secret | Keystore private key password |

---

## 3. Apple Developer Program, Entitlements & Provisioning

To compile, run, and distribute the native iOS application (`ios/AsterCompanion`) and its ReplayKit Broadcast Upload Extension, configure the Apple Developer portal as follows:

### 3.1 App Identifiers & App Groups
1. **Main Application App ID**: `com.astercompanion.app`
2. **ReplayKit Broadcast Extension App ID**: `com.astercompanion.app.broadcast`
3. **App Group**: `group.com.astercompanion.shared`
   - Both `com.astercompanion.app` and `com.astercompanion.app.broadcast` must belong to this App Group to permit shared memory-mapped ring buffers and configuration handover under iOS memory limits.

### 3.2 Required Entitlements

#### Main App (`AsterCompanion.entitlements`)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.application-groups</key>
    <array>
        <string>group.com.astercompanion.shared</string>
    </array>
    <key>keychain-access-groups</key>
    <array>
        <string>$(AppIdentifierPrefix)com.astercompanion.shared</string>
    </array>
    <key>aps-environment</key>
    <string>development</string>
</dict>
</plist>
```

#### ReplayKit Broadcast Extension (`AsterCompanionBroadcast.entitlements`)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.application-groups</key>
    <array>
        <string>group.com.astercompanion.shared</string>
    </array>
</dict>
</plist>
```

### 3.3 Info.plist Background Modes & Privacy Declarations
In `ios/AsterCompanion/Info.plist`:
- `UIBackgroundModes`:
  - `audio` (required for background voice streaming and full-duplex conversational audio)
  - `fetch` (for background timeline sync)
  - `processing` (for local offline outbox consolidation)
  - `remote-notification` (for APNs push alerts)
- `NSMicrophoneUsageDescription`: *"Aster Companion requires microphone access to hear your voice during full-duplex conversations and optional audio awareness."*
- `NSPhotoLibraryUsageDescription`: *"Aster Companion accesses photos you explicitly choose to inspect or share."*

### 3.4 Apple Privacy Manifest (`PrivacyInfo.xcprivacy`)
Apple mandates an explicit privacy manifest declaring required-reason APIs:
1. `NSPrivacyAccessedAPITypeUserDefaults`: Declares app preferences and active profile ID storage.
2. `NSPrivacyAccessedAPITypeFileTimestamp`: Declares local offline outbox and media chunk caching.
3. `NSPrivacyAccessedAPITypeSystemBootTime`: Declares calculation of monotonic device event sequences to detect system reboots.
4. `NSPrivacyAccessedAPITypeDiskSpace`: Declares monitoring available device storage to prevent overflowing device flash memory during continuous awareness buffering.

---

## 4. Google Cloud Console & Workspace Setup

### 4.1 Google Cloud Project Configuration
1. Create a dedicated Google Cloud Project: `aster-companion-prod`.
2. Configure **OAuth Consent Screen**:
   - User Type: `External`
   - Application Name: `Aster Companion`
   - Support Email: `support@astercompanion.com`
   - Application Homepage: `https://astercompanion.com`
   - Privacy Policy URL: `https://astercompanion.com/privacy`
   - Terms of Service URL: `https://astercompanion.com/terms`

### 4.2 OAuth 2.0 Credentials
Create 3 separate client IDs in Google Cloud Console:

1. **Android Client ID**:
   - Package name: `com.androidactivity.guage` (or updated release ID `com.astercompanion.app`)
   - SHA-1 Certificate Fingerprint: Registered from debug keystore and release signing keystore.
2. **iOS Client ID**:
   - Bundle ID: `com.astercompanion.app`
3. **Web Client ID (with Client Secret)**:
   - Authorized Javascript Origins: `https://app.astercompanion.com`, `http://localhost:5173`
   - Authorized Redirect URIs: `https://api.astercompanion.com/api/integrations/oauth/callback`, `com.astercompanion.app:/oauth2callback`

### 4.3 Enabling Google Workspace & Data APIs
Enable the following APIs in Google Cloud Console:
- **Google Photos Picker API** (`photospicker.googleapis.com`): Zero-permission user-mediated photo selection.
- **Google Drive API v3** (`drive.googleapis.com`): For authorized file searches.
- **Gmail API v1** (`gmail.googleapis.com`): Restricted scope for reading/sending email summaries.
- **Google Calendar API v3** (`calendar-json.googleapis.com`): For viewing and creating schedule entries.
- **People / Contacts API** (`people.googleapis.com`): For resolving social contact references.

---

## 5. Google CASA (Cloud Application Security Assessment) Review

### 5.1 Why CASA Tier 2 is Mandatory
Google mandates CASA Tier 2 verification for any third-party application requesting **Restricted Scopes** (specifically `https://www.googleapis.com/auth/gmail.readonly`, `https://www.googleapis.com/auth/gmail.send`, or unrestricted Google Drive scopes). Without passing CASA Tier 2, Google will restrict the app to a maximum of 100 test users and display a severe *"Google hasn't verified this app"* warning screen.

### 5.2 CASA Tier 2 Requirements Checklist

| Requirement | Standard | Aster Companion Implementation |
| :--- | :--- | :--- |
| **SAST Code Scanning** | OWASP ASVS Level 2 | Automated Semgrep & SonarQube scans in GitHub Actions with zero high/critical vulnerabilities. |
| **Third-Party DAST Assessment** | Authorized Lab Scan | Formal dynamic testing conducted by an authorized CASA lab (e.g. Bishop Fox, DeepStrike, Leviathan). |
| **Transport Encryption** | TLS 1.3 / Strict Cipher Suites | Enforced on all ingress endpoints with HSTS (`max-age=31536000; includeSubDomains`). |
| **Token Storage at Rest** | OWASP MASVS Storage | Google OAuth refresh tokens encrypted in PostgreSQL using AES-256-GCM envelope encryption. |
| **Principle of Least Privilege** | Google User Data Policy | Aster Companion requests only incremental scopes (e.g. `drive.file` instead of full `drive`). |
| **Annual Recertification** | Google Security Review | Formal Letter of Assessment (LoA) renewed annually and submitted to Google Trust & Safety. |

---

## 6. Supabase Cloud Infrastructure Provisioning

### 6.1 Database Extensions
Execute in the Supabase SQL Editor or include in the initial migration:
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector"; -- pgvector for high-dimensional embeddings
```

### 6.2 Storage Buckets & Access Policies
Create 4 dedicated Supabase Storage buckets:

1. `user-media` (Private): For uploaded images, attachments, and frame snapshots.
2. `avatar-assets` (Public Read): For 3D avatar GLTF models, texture maps, and clothing presets.
3. `audio-recordings` (Private): Encrypted audio chunks for user-initiated voice notes.
4. `memory-exports` (Private): Temporary Article 20 GDPR export zip files.

#### Storage RLS Policy Example (`user-media`)
```sql
-- Allow authenticated users to view only their own uploaded media
CREATE POLICY "Allow individual user media access"
ON storage.objects FOR SELECT
TO authenticated
USING (
    bucket_id = 'user-media' 
    AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Allow authenticated users to upload media to their own directory
CREATE POLICY "Allow individual user media uploads"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'user-media' 
    AND (storage.foldername(name))[1] = auth.uid()::text
);
```

---

## 7. Third-Party AI Services Provisioning

### 7.1 OpenAI Realtime API (WebRTC)
1. In the OpenAI Platform Console (`platform.openai.com`), create an API key with permissions for `model.realtime`.
2. Configure monthly budget quotas and spending limits to prevent DoS cost overruns.
3. Verify support for `gpt-4o-realtime-preview-2024-12-17` or later.
4. Voice models provisioned: `shimmer`, `alloy`, `echo`, `verse`.

### 7.2 Google Gemini Multimodal Live API
1. In Google AI Studio / Google Cloud Vertex AI, enable the Gemini Multimodal Live API.
2. Secure an API key or Service Account JSON with Vertex AI User permissions.
3. Voice models provisioned: `Aoede`, `Puck`, `Charon`, `Kore`, `Fenrir`.
4. Audio format: Bidirectional 16kHz PCM audio streaming over WebSockets.

---

## 8. "Unconfigured Until Provisioned" Client State Model

Clients on Android, iOS, and Web implement the following deterministic state machine for all external integrations and AI providers:

```text
    ┌───────────────────────────┐
    │       UNCONFIGURED        │ ◄─── Missing API key, OAuth client ID, or entitlement
    └─────────────┬─────────────┘
                  │ Engineer or User provides credentials
                  ▼
    ┌───────────────────────────┐
    │       CONFIGURING         │ ◄─── Dynamic validation & health-probe ping
    └─────────────┬─────────────┘
                  │ Health probe passes (HTTP 200)
                  ▼
    ┌───────────────────────────┐
    │          READY            │ ◄─── Fully operational
    └──────┬──────────────┬─────┘
           │              │
Token expires             Quota or Network failure
           ▼              ▼
    ┌─────────────┐ ┌─────────────┐
    │   EXPIRED   │ │  DEGRADED   │
    └─────────────┘ └─────────────┘
```

### UI Implementation Rules:
- When state is `UNCONFIGURED`: The UI component shows a subdued card with an informative badge (`Setup Required`). Tapping opens the relevant Settings screen.
- Tool Calls: The reasoning agent checks `integration.status === 'READY'`. If `UNCONFIGURED`, the action is suppressed, and Aster reports: *"The requested integration is not yet configured. Please configure it in Settings to enable this capability."*
- Zero Stubs: The system NEVER simulates a fake response when a service is unconfigured.
