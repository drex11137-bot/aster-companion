/**
 * Aster Companion - Security Policy Enforcer & BOLA Guard Unit Tests
 * security_policy_enforcer.test.ts
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { createHash } from 'node:crypto';
import {
  SecurityPolicyEnforcer,
  InMemoryResourceOwnershipResolver,
  AuthContext,
  ToolCallRequest,
  ActionApprovalTicket,
  BolaAuthorizationError,
  CrossProfileIsolationViolationError,
  ParameterTamperingViolationError,
  ActionConfirmationRequiredError,
  SecurityPolicyViolationError,
} from '../../src/security/security_policy_enforcer.js';

describe('SecurityPolicyEnforcer', () => {
  let resolver: InMemoryResourceOwnershipResolver;
  let enforcer: SecurityPolicyEnforcer;

  const USER_ALICE = 'usr_alice_123';
  const USER_BOB = 'usr_bob_456';
  const PROFILE_ASTER_1 = 'prof_alice_aster_prod';
  const PROFILE_NOVA_2 = 'prof_alice_nova_private';

  const defaultAuthContext: AuthContext = {
    userId: USER_ALICE,
    activeProfileId: PROFILE_ASTER_1,
    deviceId: 'dev_pixel_9_pro',
    clientPlatform: 'android',
    grantedScopes: [
      'https://www.googleapis.com/auth/photopicker.mediaitems.readonly',
      'https://www.googleapis.com/auth/drive.readonly',
      'https://www.googleapis.com/auth/drive.file',
      'https://www.googleapis.com/auth/gmail.readonly',
      'https://www.googleapis.com/auth/gmail.compose',
      'https://www.googleapis.com/auth/calendar.events',
      'https://www.googleapis.com/auth/calendar.events.readonly',
    ],
  };

  beforeEach(() => {
    resolver = new InMemoryResourceOwnershipResolver();
    enforcer = new SecurityPolicyEnforcer(resolver);

    // Register test profiles
    enforcer.registerProfilePolicy({
      profileId: PROFILE_ASTER_1,
      profileName: 'Aster',
      isReadOnly: false,
    });

    enforcer.registerProfilePolicy({
      profileId: PROFILE_NOVA_2,
      profileName: 'Nova',
      isReadOnly: true, // Nova is private reflection profile in read-only mode
    });
  });

  describe('1. Profile Permission Validation', () => {
    it('permits valid read-only tool for active profile', async () => {
      const toolCall: ToolCallRequest = {
        callId: 'call_1',
        toolName: 'web_search_tavily',
        arguments: { query: 'Asteroid belt distances' },
      };

      const result = await enforcer.enforce(toolCall, defaultAuthContext);
      expect(result.allowed).toBe(true);
      expect(result.decision).toBe('PERMIT');
    });

    it('blocks mutating tools when profile is configured in READ_ONLY mode', async () => {
      const novaContext: AuthContext = {
        ...defaultAuthContext,
        activeProfileId: PROFILE_NOVA_2,
      };

      const toolCall: ToolCallRequest = {
        callId: 'call_2',
        toolName: 'memory_create',
        arguments: { content: 'New reflection note' },
      };

      await expect(enforcer.enforce(toolCall, novaContext)).rejects.toThrowError(
        SecurityPolicyViolationError
      );
    });

    it('blocks tools that are explicitly blacklisted for a profile', async () => {
      enforcer.registerProfilePolicy({
        profileId: 'prof_restricted',
        profileName: 'RestrictedProfile',
        deniedTools: ['drive_search_files'],
      });

      const restrictedContext: AuthContext = {
        ...defaultAuthContext,
        activeProfileId: 'prof_restricted',
      };

      const toolCall: ToolCallRequest = {
        callId: 'call_3',
        toolName: 'drive_search_files',
        arguments: { query: 'taxes.pdf' },
      };

      await expect(enforcer.enforce(toolCall, restrictedContext)).rejects.toThrow(
        /Tool 'drive_search_files' is explicitly blacklisted/
      );
    });
  });

  describe('2. Broken Object Level Authorization (BOLA / IDOR) Guards', () => {
    it('permits resource access when user owns the object', async () => {
      resolver.registerResource({
        resourceType: 'photo',
        resourceId: 'photo_sunset_101',
        ownerUserId: USER_ALICE,
        ownerProfileId: PROFILE_ASTER_1,
      });

      const toolCall: ToolCallRequest = {
        callId: 'call_photo_1',
        toolName: 'photos_get_item',
        arguments: { photoId: 'photo_sunset_101' },
      };

      const result = await enforcer.enforce(toolCall, defaultAuthContext);
      expect(result.allowed).toBe(true);
      expect(result.decision).toBe('PERMIT');
    });

    it('BLOCKS access with BolaAuthorizationError when user tries to access another users resource (Cross-Tenant)', async () => {
      resolver.registerResource({
        resourceType: 'drive_file',
        resourceId: 'file_confidential_bob_doc',
        ownerUserId: USER_BOB,
        ownerProfileId: 'prof_bob_default',
      });

      const toolCall: ToolCallRequest = {
        callId: 'call_attack_idor',
        toolName: 'drive_get_file',
        arguments: { fileId: 'file_confidential_bob_doc' },
      };

      await expect(enforcer.enforce(toolCall, defaultAuthContext)).rejects.toThrowError(
        BolaAuthorizationError
      );
    });

    it('BLOCKS access to nonexistent or deleted resources', async () => {
      const toolCall: ToolCallRequest = {
        callId: 'call_missing_res',
        toolName: 'calendar_get_event',
        arguments: { eventId: 'event_nonexistent_999' },
      };

      await expect(enforcer.enforce(toolCall, defaultAuthContext)).rejects.toThrow(
        /does not exist or has been deleted/
      );
    });
  });

  describe('3. Multi-Companion Cross-Profile Data Isolation (PRD §9)', () => {
    it('BLOCKS access with CrossProfileIsolationViolationError when Profile 1 accesses Profile 2 memory', async () => {
      // Alice owns both profiles, but Profile 2 (Nova) private memory MUST NOT be read by Profile 1 (Aster)
      resolver.registerResource({
        resourceType: 'memory',
        resourceId: 'mem_sensitive_therapy_entry',
        ownerUserId: USER_ALICE,
        ownerProfileId: PROFILE_NOVA_2,
      });

      const toolCall: ToolCallRequest = {
        callId: 'call_cross_profile_leak',
        toolName: 'memory_retrieve',
        arguments: { memoryId: 'mem_sensitive_therapy_entry' },
      };

      // Active profile is Aster (Profile 1)
      await expect(enforcer.enforce(toolCall, defaultAuthContext)).rejects.toThrowError(
        CrossProfileIsolationViolationError
      );
    });

    it('allows access to memory when active profile matches owner profile', async () => {
      resolver.registerResource({
        resourceType: 'memory',
        resourceId: 'mem_sensitive_therapy_entry',
        ownerUserId: USER_ALICE,
        ownerProfileId: PROFILE_NOVA_2,
      });

      const novaContext: AuthContext = {
        ...defaultAuthContext,
        activeProfileId: PROFILE_NOVA_2,
      };

      const toolCall: ToolCallRequest = {
        callId: 'call_valid_nova_read',
        toolName: 'memory_retrieve',
        arguments: { memoryId: 'mem_sensitive_therapy_entry' },
      };

      const result = await enforcer.enforce(toolCall, novaContext);
      expect(result.allowed).toBe(true);
      expect(result.decision).toBe('PERMIT');
    });
  });

  describe('4. Parameter Tampering & Identity Injection Protection', () => {
    it('detects and rejects attempts to override userId inside tool arguments', async () => {
      const maliciousToolCall: ToolCallRequest = {
        callId: 'call_tamper_user',
        toolName: 'web_search_tavily',
        arguments: {
          query: 'restaurants',
          userId: 'usr_hacked_victim',
        },
      };

      await expect(enforcer.enforce(maliciousToolCall, defaultAuthContext)).rejects.toThrowError(
        ParameterTamperingViolationError
      );
    });

    it('detects and rejects attempts to spoof profile_id inside tool arguments', async () => {
      const maliciousToolCall: ToolCallRequest = {
        callId: 'call_tamper_profile',
        toolName: 'memory_search',
        arguments: {
          query: 'notes',
          profile_id: PROFILE_NOVA_2, // Attempting to switch profile context via arg injection
        },
      };

      await expect(enforcer.enforce(maliciousToolCall, defaultAuthContext)).rejects.toThrowError(
        ParameterTamperingViolationError
      );
    });
  });

  describe('5. Two-Step Action Approval Gate & Biometrics (PRD §12)', () => {
    it('demands user confirmation ticket for high-risk action (gmail_send_message)', async () => {
      const highRiskCall: ToolCallRequest = {
        callId: 'call_send_email',
        toolName: 'gmail_send_message',
        arguments: { to: 'colleague@work.com', subject: 'Report', body: 'Draft' },
      };

      await expect(enforcer.enforce(highRiskCall, defaultAuthContext)).rejects.toThrowError(
        ActionConfirmationRequiredError
      );
    });

    it('permits high-risk action when approved ticket with matching payload hash is provided', async () => {
      const emailArgs = { to: 'colleague@work.com', subject: 'Report', body: 'Draft' };
      const canonicalJson = JSON.stringify(emailArgs, Object.keys(emailArgs).sort());
      const actionHash = createHash('sha256').update(canonicalJson, 'utf8').digest('hex');

      const ticket: ActionApprovalTicket = {
        ticketId: 'tkt_approved_email_42',
        userId: USER_ALICE,
        profileId: PROFILE_ASTER_1,
        actionType: 'GMAIL_SEND',
        actionHash,
        confirmationToken: 'conf_tok_abc',
        approved: true,
        approvedAt: Date.now() - 1000,
        expiresAt: Date.now() + 60000,
      };

      resolver.registerTicket(ticket);

      const highRiskCall: ToolCallRequest = {
        callId: 'call_send_email',
        toolName: 'gmail_send_message',
        arguments: emailArgs,
        approvalTicketId: 'tkt_approved_email_42',
      };

      const result = await enforcer.enforce(highRiskCall, defaultAuthContext);
      expect(result.allowed).toBe(true);
      expect(result.decision).toBe('PERMIT');
    });

    it('rejects action if arguments were tampered with after ticket approval', async () => {
      const originalArgs = { to: 'colleague@work.com', subject: 'Report', body: 'Draft' };
      const canonicalJson = JSON.stringify(originalArgs, Object.keys(originalArgs).sort());
      const actionHash = createHash('sha256').update(canonicalJson, 'utf8').digest('hex');

      const ticket: ActionApprovalTicket = {
        ticketId: 'tkt_tampered_email',
        userId: USER_ALICE,
        profileId: PROFILE_ASTER_1,
        actionType: 'GMAIL_SEND',
        actionHash,
        confirmationToken: 'conf_tok_abc',
        approved: true,
        expiresAt: Date.now() + 60000,
      };

      resolver.registerTicket(ticket);

      // Attacker changes recipient from colleague@work.com to evil@attacker.com
      const tamperedCall: ToolCallRequest = {
        callId: 'call_send_email_tampered',
        toolName: 'gmail_send_message',
        arguments: { to: 'evil@attacker.com', subject: 'Report', body: 'Draft' },
        approvalTicketId: 'tkt_tampered_email',
      };

      await expect(enforcer.enforce(tamperedCall, defaultAuthContext)).rejects.toThrow(
        /Action payload hash mismatch!/
      );
    });

    it('enforces biometric verification for Shopify checkout', async () => {
      const checkoutArgs = { cartId: 'cart_123', shippingAddressId: 'addr_456' };
      const canonicalJson = JSON.stringify(checkoutArgs, Object.keys(checkoutArgs).sort());
      const actionHash = createHash('sha256').update(canonicalJson, 'utf8').digest('hex');

      // Ticket is approved by user, but biometricConfirmed is FALSE
      const ticket: ActionApprovalTicket = {
        ticketId: 'tkt_shopify_no_bio',
        userId: USER_ALICE,
        profileId: PROFILE_ASTER_1,
        actionType: 'SHOPIFY_CHECKOUT',
        actionHash,
        confirmationToken: 'conf_tok_xyz',
        approved: true,
        biometricConfirmed: false,
        expiresAt: Date.now() + 60000,
      };

      resolver.registerTicket(ticket);

      const shopifyCall: ToolCallRequest = {
        callId: 'call_shopify_checkout',
        toolName: 'shopify_initiate_checkout',
        arguments: checkoutArgs,
        approvalTicketId: 'tkt_shopify_no_bio',
      };

      await expect(enforcer.enforce(shopifyCall, defaultAuthContext)).rejects.toThrow(
        /requires biometric verification/
      );
    });
  });

  describe('6. OAuth Scope Enforcement', () => {
    it('rejects tool call when required scope is missing from auth context', async () => {
      const contextWithoutCalendar: AuthContext = {
        ...defaultAuthContext,
        grantedScopes: ['https://www.googleapis.com/auth/gmail.readonly'],
      };

      const toolCall: ToolCallRequest = {
        callId: 'call_cal_no_scope',
        toolName: 'calendar_list_events',
        arguments: { timeMin: '2026-11-01T00:00:00Z' },
      };

      await expect(enforcer.enforce(toolCall, contextWithoutCalendar)).rejects.toThrow(
        /Tool 'calendar_list_events' requires one of/
      );
    });
  });

  describe('7. Audit Logging', () => {
    it('records immutable audit entries for all decisions', async () => {
      const toolCall: ToolCallRequest = {
        callId: 'call_audit_test',
        toolName: 'web_search_exa',
        arguments: { query: 'Quantum computing news' },
      };

      await enforcer.enforce(toolCall, defaultAuthContext);
      const auditLog = enforcer.getAuditLog();

      expect(auditLog.length).toBeGreaterThan(0);
      const lastEntry = auditLog[auditLog.length - 1]!;
      expect(lastEntry.userId).toBe(USER_ALICE);
      expect(lastEntry.profileId).toBe(PROFILE_ASTER_1);
      expect(lastEntry.toolName).toBe('web_search_exa');
      expect(lastEntry.decision).toBe('PERMIT');
      expect(lastEntry.riskLevel).toBe('READ_ONLY');
      expect(lastEntry.timestamp).toBeDefined();
    });
  });
});
