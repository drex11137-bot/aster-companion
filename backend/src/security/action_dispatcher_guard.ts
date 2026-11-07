/**
 * Aster Companion - Action Dispatcher Security Gate
 * File: backend/src/security/action_dispatcher_guard.ts
 *
 * Implements PRD v1.1 Section 12 (Device Actions & Agentic Execution),
 * Section 12.2 (Action Authorization), and Section 16 (Threat Model).
 *
 * Security Invariants:
 * 1. Untrusted observations (screen OCR, background audio) can NEVER trigger tool commands.
 * 2. Cross-profile actions are strictly prohibited (Profile A cannot execute as Profile B).
 * 3. High-risk actions require explicit user confirmation gates.
 * 4. Indirect prompt injection attacks are intercepted and neutralized.
 */

import type {
  ActionRequest,
  ActionSecurityDecision,
  PerceptionPayload,
} from './types.ts';
import {
  ProfileIsolationSecurityError,
  PromptInjectionBlockedError,
} from './types.ts';
import { UntrustedContentSanitizer } from './untrusted_content_sanitizer.ts';

export {
  ProfileIsolationSecurityError,
  PromptInjectionBlockedError,
};

export interface ActiveSessionContext {
  userId: string;
  activeProfileId: string;
}

export class ActionDispatcherGuard {
  /**
   * Evaluates an incoming action dispatch request against adversarial & authorization constraints.
   *
   * @throws PromptInjectionBlockedError if the action was triggered by untrusted content or contains injection
   * @throws ProfileIsolationSecurityError if profile context violates session boundaries
   */
  public static evaluateAction(
    request: ActionRequest,
    sessionContext: ActiveSessionContext
  ): ActionSecurityDecision {
    // 1. Enforce Profile Isolation Boundary
    if (request.profileId !== sessionContext.activeProfileId) {
      throw new ProfileIsolationSecurityError(
        `Cross-profile action violation: Session active profile is '${sessionContext.activeProfileId}', ` +
        `but attempted action targets profile '${request.profileId}'.`
      );
    }

    if (request.userId !== sessionContext.userId) {
      throw new ProfileIsolationSecurityError(
        `Cross-user action violation: Session user '${sessionContext.userId}' does not match action user '${request.userId}'.`
      );
    }

    // 2. Sanitize and Evaluate Originating Perception Payload
    const originating = request.originatingPayload;
    const sanitized = UntrustedContentSanitizer.sanitizeObservation(originating);

    // 3. Strict Trust Boundary: Untrusted observations CANNOT dispatch actions
    if (originating.trustLevel === 'UNTRUSTED_OBSERVATION') {
      const reason = 
        `Action '${request.actionName}' blocked: Originates from untrusted observation (${originating.source}). ` +
        `PRD v1.1 mandates that perception data (OCR/transcripts) is strictly inert observation and cannot invoke tool commands.`;
      
      const threats = sanitized.detectedThreats.length > 0
        ? sanitized.detectedThreats
        : [`UntrustedObservationExecutionAttempt from ${originating.source}`];

      throw new PromptInjectionBlockedError(reason, threats, originating.content);
    }

    // 4. Inspect payload content for injection attacks even if purported as user intent
    if (sanitized.injectionDetected) {
      throw new PromptInjectionBlockedError(
        `Adversarial prompt injection detected in action dispatch payload for '${request.actionName}'.`,
        sanitized.detectedThreats,
        originating.content
      );
    }

    // 5. Evaluate Risk Level and Confirmation Requirement
    const requiresConfirmation = 
      request.riskLevel === 'consequential' || request.riskLevel === 'irreversible';

    if (requiresConfirmation && !request.confirmedByUser) {
      return {
        allowed: false,
        status: 'pending',
        reason: `Action '${request.actionName}' has risk level '${request.riskLevel}' and requires explicit user confirmation before execution.`,
        riskLevel: request.riskLevel,
        requiresConfirmation: true,
        sanitizedObservation: sanitized,
      };
    }

    // 6. Action Approved for Execution
    return {
      allowed: true,
      status: 'approved',
      reason: `Action '${request.actionName}' authorized under active profile '${request.profileId}' with user intent verified.`,
      riskLevel: request.riskLevel,
      requiresConfirmation: false,
      sanitizedObservation: sanitized,
    };
  }

  /**
   * Helper to inspect untrusted text (e.g. from screen OCR or audio) and verify
   * that it is parsed as inert observation rather than executable commands.
   */
  public static processPerceptionStream(payload: PerceptionPayload) {
    const sanitized = UntrustedContentSanitizer.sanitizeObservation(payload);
    return {
      trustLevel: 'UNTRUSTED_OBSERVATION' as const,
      isExecutableCommand: false,
      sanitized,
    };
  }
}
