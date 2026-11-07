/**
 * Aster Companion - Security Module Barrel Export
 * File: backend/src/security/index.ts
 */

export * from './types.ts';
export * from './untrusted_content_sanitizer.ts';
export * from './action_dispatcher_guard.ts';

export {
  PromptInjectionSanitizer,
  PromptInjectionDetectedError,
} from './prompt_injection_sanitizer.ts';

export type {
  PerceptualSourceType,
  DetectedThreat,
  SanitizationResult,
  StructuredPerceptualPayload,
  ThreatSeverity,
  ThreatCategory,
  ThreatLevel,
} from './prompt_injection_sanitizer.ts';

export {
  SecurityPolicyEnforcer,
} from './security_policy_enforcer.ts';

export type {
  AuthContext,
  ToolCallRequest,
  PolicyDecision,
  ResourceOwnershipRecord,
  ActionApprovalTicket,
  ProfilePolicyConfig,
  SecurityAuditEntry,
  EnforcementResult,
} from './security_policy_enforcer.ts';
