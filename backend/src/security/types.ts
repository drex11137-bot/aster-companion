/**
 * Aster Companion - Security Architecture Types
 * File: backend/src/security/types.ts
 *
 * Implements PRD v1.1 Section 12 (Device Actions & Agentic Execution),
 * Section 16 (Security & Privacy), and OWASP LLM01 Prompt Injection Defenses.
 */

export type ContentTrustLevel =
  | 'AUTHENTICATED_USER_INTENT'
  | 'UNTRUSTED_OBSERVATION'
  | 'SYSTEM_INTERNAL';

export type PerceptionSource =
  | 'user_chat'
  | 'verified_user_voice'
  | 'screen_ocr'
  | 'audio_transcript'
  | 'clipboard'
  | 'external_api'
  | 'system_notification';

export type ActionRiskLevel =
  | 'read_only'
  | 'reversible'
  | 'consequential'
  | 'irreversible';

export type ActionStatus =
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'executed'
  | 'blocked';

export interface PerceptionPayload {
  source: PerceptionSource;
  trustLevel: ContentTrustLevel;
  content: string;
  metadata?: Record<string, unknown>;
  timestamp?: string;
}

export interface SanitizedObservation {
  source: PerceptionSource;
  trustLevel: ContentTrustLevel;
  safeContent: string;
  originalLength: number;
  injectionDetected: boolean;
  detectedThreats: string[];
  demarcatedContent: string;
}

export interface ActionRequest {
  id?: string;
  profileId: string;
  userId: string;
  actionName: string;
  arguments: Record<string, unknown>;
  riskLevel: ActionRiskLevel;
  originatingPayload: PerceptionPayload;
  idempotencyKey?: string;
  confirmedByUser?: boolean;
}

export interface ActionSecurityDecision {
  allowed: boolean;
  status: ActionStatus;
  reason: string;
  riskLevel: ActionRiskLevel;
  requiresConfirmation: boolean;
  sanitizedObservation?: SanitizedObservation;
}

export class PromptInjectionBlockedError extends Error {
  public readonly threats: string[];
  public readonly payloadContent?: string;

  constructor(
    message: string,
    threats: string[],
    payloadContent?: string
  ) {
    super(message);
    this.name = 'PromptInjectionBlockedError';
    this.threats = threats;
    this.payloadContent = payloadContent;
  }
}

export class ProfileIsolationSecurityError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ProfileIsolationSecurityError';
  }
}
