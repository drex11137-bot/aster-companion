# Aster Companion: Operations & Runbooks Master Guide (v1.1)

---

## 1. Daily Operational Commands & Environment Setup

This section provides verified, non-destructive commands for engineers and operations staff managing the Aster Companion multi-platform ecosystem.

### 1.1 Toolchain Inventory & Version Requirements
The engineering workstation and CI/CD pipelines require the following software versions:

| Subsystem | Required Version | Verification Command |
| :--- | :--- | :--- |
| **Node.js** | `>= 20.0.0` (Target: Node 22 LTS / 24) | `node -v` |
| **npm** | `>= 10.0.0` | `npm -v` |
| **Java JDK** | OpenJDK 17 or 21 | `java -version` |
| **Android SDK** | API Level 34 / 35 (Build-Tools `34.0.0`) | `sdkmanager --list_installed` |
| **Supabase CLI** | `>= 2.0.0` | `supabase -v` |
| **PostgreSQL Client** | `psql` (PostgreSQL 16) | `psql --version` |
| **Python** | `>= 3.11.0` (for test harnesses & scripts) | `python3 --version` |
| **Docker / Podman** | Docker Engine 24+ (for local Supabase stack) | `docker --version` |

### 1.2 Local Supabase Stack Lifecycle
Aster Companion relies on Supabase for PostgreSQL 16, pgvector, GoTrue Auth, Realtime, and S3-compatible Storage.

```bash
# 1. Initialize Supabase project (if not already initialized)
supabase init

# 2. Start all local Supabase containers (Postgres, Kong, Auth, Realtime, Storage)
supabase start

# 3. Check status and retrieve local credentials & API endpoints
supabase status

# Expected output sample:
#         API URL: http://127.0.0.1:54321
#     GraphQL URL: http://127.0.0.1:54321/graphql/v1
#          DB URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres
#      Studio URL: http://127.0.0.1:54323
#    Inbucket URL: http://127.0.0.1:54324
#        anon key: eyJhbGciOi...
# service_role key: eyJhbGciOi...

# 4. Stop local Supabase stack (preserves persistent volumes)
supabase stop

# 5. Stop local Supabase stack and wipe database state
supabase stop --no-backup
```

### 1.3 Database Migration Execution & Seeding
Database migrations are versioned sequentially in [`backend/supabase/migrations/`](file:///workspaces/codespaces-blank/backend/supabase/migrations).

```bash
# Apply pending migrations to the local database
supabase db push

# Re-run all migrations from scratch and execute seed data
supabase db reset

# Verify migration integrity and inspect diff against remote/shadow database
supabase db diff

# Run automated RLS and schema validation script
python3 scripts/verify_database_rls.py
```

---

## 2. Build Workflows & CI/CD Pipelines

### 2.1 Android Native Client (`app/`)
The Android client is built with Gradle 8.x, Kotlin 2.0, and Jetpack Compose.

```bash
# 1. Clean build directory and caches
./gradlew clean

# 2. Run unit tests and generate test reports
./gradlew testDebugUnitTest

# 3. Build release APK
./gradlew assembleRelease

# 4. Build Android App Bundle (AAB) for Google Play distribution
./gradlew bundleRelease

# 5. Verify cryptographic alignment and v2/v3 signature
zipalign -c -v 4 app/build/outputs/apk/release/app-release-unsigned.apk
apksigner verify --verbose --print-certs app-release-signed.apk
```

### 2.2 Laptop Web Client (`web/`)
The desktop client is a high-performance single-page application built with React 18, TypeScript, and Vite.

```bash
cd /workspaces/codespaces-blank/web

# 1. Install dependencies
npm ci

# 2. Run TypeScript strict type verification
npm run typecheck

# 3. Run ESLint code quality checks
npm run lint

# 4. Start local development server (binds to http://localhost:5173)
npm run dev

# 5. Compile production bundle into web/dist/
npm run build

# 6. Execute headless browser integration tests
npm run test:e2e
```

### 2.3 Backend Gateway & Voice Broker (`backend/`)
The backend service routes WebRTC signaling, verifies JWT profile tokens, and manages continuous frame ingestion.

```bash
cd /workspaces/codespaces-blank/backend

# 1. Install dependencies
npm ci

# 2. Run Vitest automated test suite (including profile isolation tests)
npm test

# 3. Run in live watch mode for rapid iteration
npm run dev

# 4. Build production JavaScript bundle into backend/dist/
npm run build

# 5. Start production Node.js service
npm start
```

### 2.4 iOS Client Handoff Workflow (`ios/AsterCompanion`)
Because Apple Darwin frameworks (UIKit, ReplayKit, Metal) cannot compile natively on Linux containers, engineers follow the deterministic macOS handoff protocol documented in [`docs/ios-macos-handoff.md`](file:///workspaces/codespaces-blank/docs/ios-macos-handoff.md):

```bash
# 1. Generate handoff manifest JSON
python3 scripts/generate_ios_handoff.py \
  --repo-url "https://github.com/aster/aster-companion" \
  --branch main \
  --scheme AsterCompanion \
  --output docs/schemas/sample-handoff.json

# 2. Validate manifest against JSON Schema
python3 -m jsonschema -i docs/schemas/sample-handoff.json docs/schemas/ios-handoff.schema.json

# 3. On macOS Build Runner / Fastlane Agent:
xcodebuild clean -workspace ios/AsterCompanion.xcworkspace -scheme AsterCompanion
xcodebuild archive \
  -workspace ios/AsterCompanion.xcworkspace \
  -scheme AsterCompanion \
  -configuration Release \
  -archivePath build/AsterCompanion.xcarchive \
  -destination 'generic/platform=iOS'
```

---

## 3. Monitoring & Telemetry Runbook

### 3.1 Four-Rate FPS Telemetry Framework
Per PRD §5.3, the system independently measures four frame rates to guarantee transparency and prevent deceptive performance claims:

| Metric Name | Prometheus Identifier | Definition | Normal Range |
| :--- | :--- | :--- | :--- |
| **Capture FPS** | `aster_screen_capture_fps` | Rate of raw display frames acquired by OS APIs | 30.0 – 120.0 FPS |
| **Upload FPS** | `aster_screen_upload_fps` | Rate of compressed frames transmitted after adaptive pHash filter | 0.2 – 5.0 FPS |
| **Ingest FPS** | `aster_screen_ingest_fps` | Rate of authenticated frames received and accepted by edge gateway | 0.2 – 5.0 FPS |
| **Analysis FPS** | `aster_screen_analysis_fps` | Rate of frames processed by OCR, UI segmentation, or AI reasoning | 0.2 – 2.0 FPS |

#### Telemetry Diagnostic Queries (PromQL)

```promql
# 1. Verify client adaptive filtering efficiency (Ratio of Capture to Upload)
aster_screen_capture_fps / clamp_min(aster_screen_upload_fps, 0.1)

# 2. Detect backend ingestion bottleneck / backpressure (Ingest > Analysis for > 15s)
(aster_screen_ingest_fps - aster_screen_analysis_fps) > 1.5

# 3. Detect unrecorded video awareness tracking gaps across active devices
sum by (profile_id, device_id) (rate(aster_tracking_gaps_total[5m]))
```

### 3.2 Error Rate Monitoring & Key Health Indicators

```promql
# 1. Full-Duplex Voice Barge-in Latency (P95 in milliseconds)
histogram_quantile(0.95, sum(rate(aster_voice_barge_in_latency_ms_bucket[5m])) by (le))
# ALERT THRESHOLD: > 250ms triggers WARNING; > 500ms triggers CRITICAL

# 2. WebRTC Audio Packet Loss Rate
rate(aster_webrtc_audio_packets_lost_total[5m]) / 
(rate(aster_webrtc_audio_packets_lost_total[5m]) + rate(aster_webrtc_audio_packets_received_total[5m]))
# ALERT THRESHOLD: > 3.0% triggers WARNING; > 8.0% triggers CRITICAL

# 3. Row-Level Security Access Violation Attempts (Potential Cross-Profile Leak Attempt)
sum by (user_id, attempted_profile_id) (rate(aster_security_rls_violations_total[5m]))
# ALERT THRESHOLD: > 0 immediately triggers SEVERITY 1 SECURITY INCIDENT
```

### 3.3 Alerting & Escalation Matrix

| Severity Level | Trigger Condition | Automated Action | Engineer SLA |
| :--- | :--- | :--- | :--- |
| **SEV-1 (Critical)** | RLS security violation detected; database connection pool > 95%; Voice Broker down | Freeze active sessions; route traffic to standby; alert on-call lead via PagerDuty | **< 15 minutes** |
| **SEV-2 (High)** | Voice barge-in P95 > 500ms; Analysis FPS = 0 while Ingest FPS > 1; OAuth refresh failure rate > 5% | Enable aggressive adaptive frame drop; clear backpressure queues; restart worker pods | **< 30 minutes** |
| **SEV-3 (Medium)** | Upload FPS drops to zero unexpectedly; device thermal throttling active; outbox queue > 200 items | Issue client telemetry warning banner; prompt user to check power/thermal state | **< 4 hours** |

---

## 4. Disaster Recovery & Security Incident Runbooks

### 4.1 Database Restore & Point-in-Time Recovery (PITR)
In the event of accidental data corruption or hardware failure, follow this exact procedure:

```bash
# Step 1: Place API Gateway in maintenance mode
curl -X POST https://api.astercompanion.com/admin/maintenance/enable \
  -H "Authorization: Bearer $ASTER_ADMIN_KEY"

# Step 2: Terminate active database connections
psql "$DATABASE_ADMIN_URL" -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'postgres' AND pid <> pg_backend_pid();"

# Step 3: Perform point-in-time recovery or restore from verified daily snapshot
# Example restore from encrypted pg_dump archive:
pg_restore --clean --if-exists --no-owner --no-privileges \
  --dbname="$DATABASE_ADMIN_URL" \
  /var/backups/aster/aster_production_snapshot_20261101.dump

# Step 4: Validate database integrity post-restore
psql "$DATABASE_ADMIN_URL" -c "
-- Verify max 2 profiles trigger exists
SELECT tgname FROM pg_trigger WHERE tgname = 'enforce_max_two_profiles_trigger';
-- Verify RLS is enabled on all critical tables
SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';
-- Check row count sanity
SELECT count(*) FROM public.profiles;
SELECT count(*) FROM public.memories;
"

# Step 5: Disable maintenance mode
curl -X POST https://api.astercompanion.com/admin/maintenance/disable \
  -H "Authorization: Bearer $ASTER_ADMIN_KEY"
```

### 4.2 Emergency Session Revocation & Rogue Device Isolation
If a user reports a lost/compromised phone or laptop, or if unauthorized access is suspected:

```bash
# 1. Revoke all active sessions for a specific user ID via Supabase Admin API
curl -X POST "https://$SUPABASE_PROJECT_REF.supabase.co/auth/v1/admin/users/$USER_ID/logout" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY"

# 2. De-register and blacklist the specific rogue device in PostgreSQL
psql "$DATABASE_ADMIN_URL" -c "
UPDATE public.devices 
SET is_active = false, 
    revoked_at = NOW(), 
    revocation_reason = 'User reported device compromised'
WHERE device_id = '$COMPROMISED_DEVICE_ID' AND user_id = '$USER_ID';

-- Disconnect active WebRTC voice channels and Realtime presence
DELETE FROM public.sessions 
WHERE device_id = '$COMPROMISED_DEVICE_ID';
"

# 3. Broadcast force-disconnect event over Supabase Realtime channel
curl -X POST "https://$SUPABASE_PROJECT_REF.supabase.co/realtime/v1/api/broadcast" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "device:'$COMPROMISED_DEVICE_ID'",
    "event": "FORCE_LOGOUT",
    "payload": { "reason": "SECURITY_REVOCATION", "timestamp": "'$(date -u +%FT%TZ)'" }
  }'
```

### 4.3 Zero-Downtime Secret & Token Rotation
Execute token rotation following the dual-key staging pattern:

```bash
# 1. Rotate Supabase Service Role Key
# In Supabase Console -> Project Settings -> API:
# Generate a secondary Service Role Key.
# Deploy secondary key to backend environment variables:
supabase secrets set SUPABASE_SERVICE_ROLE_KEY="$NEW_SERVICE_ROLE_KEY"

# 2. Rotate OpenAI Realtime & Google Gemini API Keys
# Update backend secret store:
supabase secrets set OPENAI_API_KEY="$NEW_OPENAI_KEY"
supabase secrets set GEMINI_API_KEY="$NEW_GEMINI_KEY"
# Trigger rolling restart of Edge Gateway pods:
kubectl rollout restart deployment/aster-edge-gateway -n production

# 3. Rotate OAuth Application Client Secrets (Google Cloud & Shopify)
# In Google Cloud Console: Add new client secret, preserve old secret for 24 hours.
# Update backend OAuth broker:
supabase secrets set GOOGLE_CLIENT_SECRET="$NEW_GOOGLE_SECRET"
# Once validated, remove previous client secret from Google Console.
```

### 4.4 Data Subject Erasure Runbook (GDPR Art. 17 & Nigeria NDPA GAID)
When a user requests permanent account deletion:

```sql
-- Comprehensive Cascade Deletion Transaction
BEGIN;

-- 1. Identify all profile IDs belonging to the user
CREATE TEMP TABLE user_profiles_to_delete AS
SELECT id AS profile_id FROM public.profiles WHERE user_id = '$TARGET_USER_ID';

-- 2. Delete all explicit memory shares
DELETE FROM public.memory_shares
WHERE source_profile_id IN (SELECT profile_id FROM user_profiles_to_delete)
   OR target_profile_id IN (SELECT profile_id FROM user_profiles_to_delete);

-- 3. Delete all vector embeddings & memories
DELETE FROM public.memories
WHERE profile_id IN (SELECT profile_id FROM user_profiles_to_delete);

-- 4. Delete all chat messages, conversations, events, and action records
DELETE FROM public.chat_messages WHERE user_id = '$TARGET_USER_ID';
DELETE FROM public.chat_conversations WHERE user_id = '$TARGET_USER_ID';
DELETE FROM public.events WHERE user_id = '$TARGET_USER_ID';
DELETE FROM public.actions WHERE user_id = '$TARGET_USER_ID';
DELETE FROM public.tool_executions WHERE user_id = '$TARGET_USER_ID';

-- 5. Delete device registrations and sessions
DELETE FROM public.sessions WHERE user_id = '$TARGET_USER_ID';
DELETE FROM public.devices WHERE user_id = '$TARGET_USER_ID';

-- 6. Delete companion profiles
DELETE FROM public.profiles WHERE user_id = '$TARGET_USER_ID';

-- 7. Delete auth user record in Supabase GoTrue
DELETE FROM auth.users WHERE id = '$TARGET_USER_ID';

COMMIT;
```
*Note: Post-deletion, run the object storage cleanup job to purge all S3 binary objects under `user-media/$TARGET_USER_ID/` and `avatar-assets/$TARGET_USER_ID/`.*
