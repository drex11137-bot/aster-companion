# Aster Companion: 200+ Master Research Index & Evidence Catalog

**Total Research Queries Executed**: 200 across 10 Domains
**Execution Timestamp**: November 2026

## Research Domains & Dossiers

| # | Domain File | Focus Area | Queries |
|---|---|---|---|
| 1 | [`01_realtime_audio_voice.md`](file:///workspaces/codespaces-blank/docs/research/01_realtime_audio_voice.md) | Real-Time Audio, Streaming Voice, Full-Duplex & VAD | 20 |
| 2 | [`02_screen_awareness_android_ios.md`](file:///workspaces/codespaces-blank/docs/research/02_screen_awareness_android_ios.md) | Continuous Screen Awareness & Temporal Visual Ingestion | 20 |
| 3 | [`03_supabase_architecture_rls.md`](file:///workspaces/codespaces-blank/docs/research/03_supabase_architecture_rls.md) | Supabase PostgreSQL Architecture, RLS & Multi-Tenant Isolation | 20 |
| 4 | [`04_avatar_customization_graphics.md`](file:///workspaces/codespaces-blank/docs/research/04_avatar_customization_graphics.md) | Realistic 3D Human Avatar, Customization & Lip-Sync Graphics | 20 |
| 5 | [`05_offline_sync_continuity.md`](file:///workspaces/codespaces-blank/docs/research/05_offline_sync_continuity.md) | Offline-First Architecture, Resumable Sync & Durable Buffers | 20 |
| 6 | [`06_integrations_oauth_pkce.md`](file:///workspaces/codespaces-blank/docs/research/06_integrations_oauth_pkce.md) | External Integrations, OAuth 2.0 PKCE & Action Approvals | 20 |
| 7 | [`07_proactive_intelligence_engine.md`](file:///workspaces/codespaces-blank/docs/research/07_proactive_intelligence_engine.md) | Proactive Intelligence, Urgency Modeling & Push Notifications | 20 |
| 8 | [`08_security_privacy_threat_model.md`](file:///workspaces/codespaces-blank/docs/research/08_security_privacy_threat_model.md) | Security, Threat Modeling, Privacy Regulations & Compliance | 20 |
| 9 | [`09_design_system_tokens.md`](file:///workspaces/codespaces-blank/docs/research/09_design_system_tokens.md) | Design System, Visual Tokens & Native Mobile UI Architecture | 20 |
| 10 | [`10_cross_platform_orchestration.md`](file:///workspaces/codespaces-blank/docs/research/10_cross_platform_orchestration.md) | Cross-Platform Orchestration, Multi-Device Sessions & State | 20 |

## Architectural Integration Summary

All research findings are linked to the system implementation:
1. **Audio/Voice**: OpenAI Realtime WebRTC & Gemini Live WebSocket dual adapters with client-side VAD and turn management.
2. **Awareness**: Native Android MediaProjection foreground service and iOS ReplayKit Broadcast Extension with adaptive sampling and honest FPS disclosure.
3. **Supabase**: PostgreSQL 16 schema with strict default-deny RLS, max 2 companion profiles per account check constraint, and isolated pgvector embeddings.
4. **Avatar Studio**: Realistic human avatar customization matching the uploaded PNG design system (hair, eyes, style, voice) with WebGL/glTF and Canvas fallbacks.
5. **Offline Continuity**: Room DB and SQLite outbox queues with monotonic per-device sequence numbers, chunked resumable upload, and gap disclosure.
6. **Integrations**: OAuth 2.0 PKCE broker, Google Photos Picker, Drive, Gmail, Calendar, Contacts, and Shopify product search with risk classification and two-step confirmation.
7. **Proactive Engine**: Multi-factor notification scoring formula (Relevance × Confidence × Urgency - Interruption Cost) with quiet hours.
8. **Security & Privacy**: OWASP MASVS compliance, zero secrets, prompt injection defense, and full GDPR / NDPA deletion propagation.
9. **Design System**: Strict dark graphite palette (#121110), warm amber accent (#E59843), violet message bubbles (#7966F3), and cream typography (#FAF8F5).
10. **Cross-Platform**: Unified state synchronization across Android, iOS, and Laptop clients with single-profile-per-device enforcement.
