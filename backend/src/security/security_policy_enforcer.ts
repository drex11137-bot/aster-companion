/**
 * Aster Companion - Security Policy & BOLA / IDOR Enforcer
 * security_policy_enforcer.ts
 *
 * Enforces strict authorization, Broken Object Level Authorization (BOLA / IDOR) guards,
 * two-step action confirmation gates, and profile isolation for all LLM tool executions.
 *
 * Implements:
 * 1. OWASP Top 10 for LLM Applications (2025) LLM06: Excessive Agency prevention
 * 2. OWASP API Security Top 10 (2023) API1: Broken Object Level Authorization (BOLA)
 * 3. PRD §9 & §16 Multi-Companion Two-Profile Backend Isolation Guarantees
 */

import { createHash, timingSafeEqual } from 'node:crypto';

// ============================================================================
// Types & Context Interfaces
// ============================================================================

export type ClientPlatform = 'android' | 'ios' | 'web' | 'desktop';

export interface AuthContext {
  userId: string;
  activeProfileId: string;
  deviceId: string;
  clientPlatform: ClientPlatform;
  grantedScopes: string[];
  sessionTokenExpiry?: number;
}

export interface ToolCallRequest {
  callId: string;
  toolName: string;
  arguments: Record<string, unknown>;
  approvalTicketId?: string;
  confirmationToken?: string;
}

export type ActionRiskLevel = 'READ_ONLY' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type PolicyDecision =
  | 'PERMIT'
  | 'DENY_FORBIDDEN_TOOL'
  | 'DENY_BOLA_VIOLATION'
  | 'DENY_CROSS_PROFILE_LEAKAGE'
  | 'DENY_SCOPE_MISSING'
  | 'DENY_PARAM_TAMPERING'
  | 'REQUIRES_USER_APPROVAL'
  | 'REQUIRES_BIOMETRIC_CONFIRMATION';

export interface ResourceOwnershipRecord {
  resourceType: 'photo' | 'email' | 'event' | 'drive_file' | 'memory' | 'ticket';
  resourceId: string;
  ownerUserId: string;
  ownerProfileId?: string; // Some resources are scoped strictly to profile
  isDeleted?: boolean;
}

export interface ActionApprovalTicket {
  ticketId: string;
  userId: string;
  profileId: string;
  actionType: string;
  actionHash: string; // SHA-256 of the arguments payload
  confirmationToken: string;
  approved: boolean;
  approvedAt?: number;
  expiresAt: number;
  biometricConfirmed?: boolean;
}

export interface ProfilePolicyConfig {
  profileId: string;
  profileName: string;
  isReadOnly?: boolean;
  allowedTools?: string[]; // If specified, only these tools can be invoked
  deniedTools?: string[]; // Tools explicitly prohibited for this profile
  highRiskActionsRequireApproval?: boolean;
}

export interface SecurityAuditEntry {
  auditId: string;
  timestamp: string;
  userId: string;
  profileId: string;
  deviceId: string;
  toolName: string;
  decision: PolicyDecision;
  riskLevel: ActionRiskLevel;
  reason: string;
  resourceEvaluated?: {
    type: string;
    id: string;
  };
}

export interface EnforcementResult {
  allowed: boolean;
  decision: PolicyDecision;
  riskLevel: ActionRiskLevel;
  reason: string;
  auditEntry: SecurityAuditEntry;
}

// ============================================================================
// Custom Security Errors
// ============================================================================

export class SecurityPolicyViolationError extends Error {
  constructor(public readonly decision: PolicyDecision, message: string) {
    super(`[Security Policy Violation - ${decision}]: ${message}`);
    this.name = 'SecurityPolicyViolationError';
  }
}

export class BolaAuthorizationError extends SecurityPolicyViolationError {
  constructor(
    public readonly resourceType: string,
    public readonly resourceId: string,
    public readonly attemptedUserId: string
  ) {
    super(
      'DENY_BOLA_VIOLATION',
      `BOLA/IDOR attempt: User '${attemptedUserId}' is not authorized to access ${resourceType} id '${resourceId}'`
    );
    this.name = 'BolaAuthorizationError';
  }
}

export class CrossProfileIsolationViolationError extends SecurityPolicyViolationError {
  constructor(
    public readonly resourceType: string,
    public readonly resourceId: string,
    public readonly activeProfileId: string,
    public readonly ownerProfileId: string
  ) {
    super(
      'DENY_CROSS_PROFILE_LEAKAGE',
      `Cross-Profile Boundary Violation: Active profile '${activeProfileId}' cannot access ${resourceType} '${resourceId}' belonging to isolated profile '${ownerProfileId}'`
    );
    this.name = 'CrossProfileIsolationViolationError';
  }
}

export class ParameterTamperingViolationError extends SecurityPolicyViolationError {
  constructor(public readonly paramKey: string, public readonly attemptedValue: unknown) {
    super(
      'DENY_PARAM_TAMPERING',
      `Parameter Tampering detected: Attempted to forge or override identity context in '${paramKey}' with value '${String(attemptedValue)}'`
    );
    this.name = 'ParameterTamperingViolationError';
  }
}

export class ActionConfirmationRequiredError extends SecurityPolicyViolationError {
  constructor(public readonly toolName: string, public readonly ticketId?: string) {
    super(
      'REQUIRES_USER_APPROVAL',
      `High-risk action '${toolName}' requires two-step user confirmation before execution. Ticket: ${ticketId || 'NONE'}`
    );
    this.name = 'ActionConfirmationRequiredError';
  }
}

// ============================================================================
// Tool Metadata & Permission Catalog
// ============================================================================

interface ToolSecurityMetadata {
  name: string;
  riskLevel: ActionRiskLevel;
  requiredScopes: string[];
  requiresTwoStepApproval: boolean;
  requiresBiometricConfirmation: boolean;
  resourceIdParameterKey?: string;
  resourceType?: ResourceOwnershipRecord['resourceType'];
}

export const TOOL_SECURITY_CATALOG: Record<string, ToolSecurityMetadata> = {
  // Photos Integration
  photos_picker_create_session: {
    name: 'photos_picker_create_session',
    riskLevel: 'LOW',
    requiredScopes: ['https://www.googleapis.com/auth/photopicker.mediaitems.readonly'],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
  },
  photos_picker_get_items: {
    name: 'photos_picker_get_items',
    riskLevel: 'LOW',
    requiredScopes: ['https://www.googleapis.com/auth/photopicker.mediaitems.readonly'],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
    resourceIdParameterKey: 'sessionId',
    resourceType: 'photo',
  },
  photos_get_item: {
    name: 'photos_get_item',
    riskLevel: 'LOW',
    requiredScopes: ['https://www.googleapis.com/auth/photopicker.mediaitems.readonly'],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
    resourceIdParameterKey: 'photoId',
    resourceType: 'photo',
  },

  // Google Drive
  drive_search_files: {
    name: 'drive_search_files',
    riskLevel: 'READ_ONLY',
    requiredScopes: [
      'https://www.googleapis.com/auth/drive.readonly',
      'https://www.googleapis.com/auth/drive.file',
    ],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
  },
  drive_get_file: {
    name: 'drive_get_file',
    riskLevel: 'READ_ONLY',
    requiredScopes: [
      'https://www.googleapis.com/auth/drive.readonly',
      'https://www.googleapis.com/auth/drive.file',
    ],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
    resourceIdParameterKey: 'fileId',
    resourceType: 'drive_file',
  },
  drive_delete_file: {
    name: 'drive_delete_file',
    riskLevel: 'CRITICAL',
    requiredScopes: ['https://www.googleapis.com/auth/drive.file'],
    requiresTwoStepApproval: true,
    requiresBiometricConfirmation: false,
    resourceIdParameterKey: 'fileId',
    resourceType: 'drive_file',
  },

  // Gmail (CASA Tier 2)
  gmail_search_messages: {
    name: 'gmail_search_messages',
    riskLevel: 'READ_ONLY',
    requiredScopes: ['https://www.googleapis.com/auth/gmail.readonly'],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
  },
  gmail_read_thread: {
    name: 'gmail_read_thread',
    riskLevel: 'READ_ONLY',
    requiredScopes: ['https://www.googleapis.com/auth/gmail.readonly'],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
    resourceIdParameterKey: 'threadId',
    resourceType: 'email',
  },
  gmail_draft_message: {
    name: 'gmail_draft_message',
    riskLevel: 'LOW',
    requiredScopes: ['https://www.googleapis.com/auth/gmail.compose'],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
  },
  gmail_send_message: {
    name: 'gmail_send_message',
    riskLevel: 'HIGH',
    requiredScopes: ['https://www.googleapis.com/auth/gmail.compose'],
    requiresTwoStepApproval: true,
    requiresBiometricConfirmation: false,
  },

  // Google Calendar
  calendar_list_events: {
    name: 'calendar_list_events',
    riskLevel: 'READ_ONLY',
    requiredScopes: [
      'https://www.googleapis.com/auth/calendar.events.readonly',
      'https://www.googleapis.com/auth/calendar.events',
    ],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
  },
  calendar_get_event: {
    name: 'calendar_get_event',
    riskLevel: 'READ_ONLY',
    requiredScopes: [
      'https://www.googleapis.com/auth/calendar.events.readonly',
      'https://www.googleapis.com/auth/calendar.events',
    ],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
    resourceIdParameterKey: 'eventId',
    resourceType: 'event',
  },
  calendar_create_event: {
    name: 'calendar_create_event',
    riskLevel: 'MEDIUM',
    requiredScopes: ['https://www.googleapis.com/auth/calendar.events'],
    requiresTwoStepApproval: true,
    requiresBiometricConfirmation: false,
  },
  calendar_delete_event: {
    name: 'calendar_delete_event',
    riskLevel: 'HIGH',
    requiredScopes: ['https://www.googleapis.com/auth/calendar.events'],
    requiresTwoStepApproval: true,
    requiresBiometricConfirmation: false,
    resourceIdParameterKey: 'eventId',
    resourceType: 'event',
  },

  // Shopify Integration
  shopify_search_products: {
    name: 'shopify_search_products',
    riskLevel: 'READ_ONLY',
    requiredScopes: [],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
  },
  shopify_initiate_checkout: {
    name: 'shopify_initiate_checkout',
    riskLevel: 'CRITICAL',
    requiredScopes: [],
    requiresTwoStepApproval: true,
    requiresBiometricConfirmation: true,
  },

  // Web Search (Tavily & Exa)
  web_search_tavily: {
    name: 'web_search_tavily',
    riskLevel: 'READ_ONLY',
    requiredScopes: [],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
  },
  web_search_exa: {
    name: 'web_search_exa',
    riskLevel: 'READ_ONLY',
    requiredScopes: [],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
  },

  // Companion Episodic & Semantic Memory
  memory_search: {
    name: 'memory_search',
    riskLevel: 'READ_ONLY',
    requiredScopes: [],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
  },
  memory_retrieve: {
    name: 'memory_retrieve',
    riskLevel: 'READ_ONLY',
    requiredScopes: [],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
    resourceIdParameterKey: 'memoryId',
    resourceType: 'memory',
  },
  memory_create: {
    name: 'memory_create',
    riskLevel: 'LOW',
    requiredScopes: [],
    requiresTwoStepApproval: false,
    requiresBiometricConfirmation: false,
  },
  memory_share_request: {
    name: 'memory_share_request',
    riskLevel: 'HIGH',
    requiredScopes: [],
    requiresTwoStepApproval: true,
    requiresBiometricConfirmation: false,
    resourceIdParameterKey: 'memoryId',
    resourceType: 'memory',
  },
  memory_delete: {
    name: 'memory_delete',
    riskLevel: 'HIGH',
    requiredScopes: [],
    requiresTwoStepApproval: true,
    requiresBiometricConfirmation: false,
    resourceIdParameterKey: 'memoryId',
    resourceType: 'memory',
  },
};

// ============================================================================
// Resource Ownership Resolver Interface
// ============================================================================

export interface IResourceOwnershipResolver {
  resolveOwnership(
    resourceType: ResourceOwnershipRecord['resourceType'],
    resourceId: string
  ): Promise<ResourceOwnershipRecord | null>;

  resolveApprovalTicket(ticketId: string): Promise<ActionApprovalTicket | null>;
}

// In-Memory Resolver for testing and mock policy execution
export class InMemoryResourceOwnershipResolver implements IResourceOwnershipResolver {
  private readonly resources = new Map<string, ResourceOwnershipRecord>();
  private readonly tickets = new Map<string, ActionApprovalTicket>();

  public registerResource(record: ResourceOwnershipRecord): void {
    const key = `${record.resourceType}:${record.resourceId}`;
    this.resources.set(key, record);
  }

  public registerTicket(ticket: ActionApprovalTicket): void {
    this.tickets.set(ticket.ticketId, ticket);
  }

  public async resolveOwnership(
    resourceType: ResourceOwnershipRecord['resourceType'],
    resourceId: string
  ): Promise<ResourceOwnershipRecord | null> {
    const key = `${resourceType}:${resourceId}`;
    return this.resources.get(key) || null;
  }

  public async resolveApprovalTicket(ticketId: string): Promise<ActionApprovalTicket | null> {
    return this.tickets.get(ticketId) || null;
  }
}

// ============================================================================
// SecurityPolicyEnforcer Class
// ============================================================================

export class SecurityPolicyEnforcer {
  private readonly auditLog: SecurityAuditEntry[] = [];

  constructor(
    private readonly resourceResolver: IResourceOwnershipResolver,
    private readonly profilePolicies = new Map<string, ProfilePolicyConfig>()
  ) {}

  /**
   * Registers or updates a profile's operational policy configuration.
   */
  public registerProfilePolicy(policy: ProfilePolicyConfig): void {
    this.profilePolicies.set(policy.profileId, policy);
  }

  /**
   * Evaluates and enforces the full security matrix for an incoming LLM tool execution call.
   * Throws specific SecurityPolicyViolationError subclasses on failure, or returns EnforcementResult.
   */
  public async enforce(
    toolCall: ToolCallRequest,
    authContext: AuthContext,
    options: { throwOnError?: boolean } = {}
  ): Promise<EnforcementResult> {
    const throwOnError = options.throwOnError ?? true;
    const { toolName, arguments: toolArgs } = toolCall;
    const { userId, activeProfileId, grantedScopes } = authContext;

    // 1. Parameter Tampering & Injection Protection:
    // Ensure untrusted LLM arguments don't spoof userId or profileId
    this.validateParameterIntegrity(toolArgs, userId, activeProfileId);

    // 2. Lookup Tool Security Metadata
    const toolMeta = TOOL_SECURITY_CATALOG[toolName];
    if (!toolMeta) {
      return this.recordDecision(
        authContext,
        toolCall,
        'DENY_FORBIDDEN_TOOL',
        'CRITICAL',
        `Unrecognized tool '${toolName}' not present in security catalog`,
        throwOnError
      );
    }

    // 3. Profile Policy Validation: Check Profile Restrictions
    const profilePolicy = this.profilePolicies.get(activeProfileId);
    if (profilePolicy) {
      if (profilePolicy.isReadOnly && toolMeta.riskLevel !== 'READ_ONLY') {
        return this.recordDecision(
          authContext,
          toolCall,
          'DENY_FORBIDDEN_TOOL',
          toolMeta.riskLevel,
          `Profile '${profilePolicy.profileName}' (${activeProfileId}) is in READ_ONLY mode. Mutating tool '${toolName}' is forbidden.`,
          throwOnError
        );
      }

      if (profilePolicy.deniedTools && profilePolicy.deniedTools.includes(toolName)) {
        return this.recordDecision(
          authContext,
          toolCall,
          'DENY_FORBIDDEN_TOOL',
          toolMeta.riskLevel,
          `Tool '${toolName}' is explicitly blacklisted for profile '${profilePolicy.profileName}' (${activeProfileId})`,
          throwOnError
        );
      }

      if (profilePolicy.allowedTools && !profilePolicy.allowedTools.includes(toolName)) {
        return this.recordDecision(
          authContext,
          toolCall,
          'DENY_FORBIDDEN_TOOL',
          toolMeta.riskLevel,
          `Tool '${toolName}' is not in the whitelist for profile '${profilePolicy.profileName}' (${activeProfileId})`,
          throwOnError
        );
      }
    }

    // 4. OAuth Scope Authorization Validation
    if (toolMeta.requiredScopes.length > 0) {
      const hasRequiredScope = toolMeta.requiredScopes.some((scope) =>
        grantedScopes.includes(scope)
      );
      if (!hasRequiredScope) {
        return this.recordDecision(
          authContext,
          toolCall,
          'DENY_SCOPE_MISSING',
          toolMeta.riskLevel,
          `Tool '${toolName}' requires one of [${toolMeta.requiredScopes.join(', ')}], but granted scopes are [${grantedScopes.join(', ')}]`,
          throwOnError
        );
      }
    }

    // 5. BOLA / IDOR Resource Ownership Verification
    if (toolMeta.resourceIdParameterKey && toolMeta.resourceType) {
      const rawResourceId = toolArgs[toolMeta.resourceIdParameterKey];
      if (typeof rawResourceId === 'string' && rawResourceId.trim().length > 0) {
        const ownership = await this.resourceResolver.resolveOwnership(
          toolMeta.resourceType,
          rawResourceId
        );

        if (!ownership) {
          return this.recordDecision(
            authContext,
            toolCall,
            'DENY_BOLA_VIOLATION',
            'HIGH',
            `Referenced ${toolMeta.resourceType} resource '${rawResourceId}' does not exist or has been deleted`,
            throwOnError,
            { type: toolMeta.resourceType, id: rawResourceId }
          );
        }

        // BOLA Check 1: Tenant / User Ownership
        if (ownership.ownerUserId !== userId) {
          if (throwOnError) {
            throw new BolaAuthorizationError(toolMeta.resourceType, rawResourceId, userId);
          }
          return this.recordDecision(
            authContext,
            toolCall,
            'DENY_BOLA_VIOLATION',
            'CRITICAL',
            `BOLA/IDOR attempt: User '${userId}' does not own ${toolMeta.resourceType} '${rawResourceId}'`,
            false,
            { type: toolMeta.resourceType, id: rawResourceId }
          );
        }

        // BOLA Check 2: Cross-Profile Boundary Check (PRD §9 isolation)
        if (ownership.ownerProfileId && ownership.ownerProfileId !== activeProfileId) {
          if (throwOnError) {
            throw new CrossProfileIsolationViolationError(
              toolMeta.resourceType,
              rawResourceId,
              activeProfileId,
              ownership.ownerProfileId
            );
          }
          return this.recordDecision(
            authContext,
            toolCall,
            'DENY_CROSS_PROFILE_LEAKAGE',
            'CRITICAL',
            `Cross-profile leakage attempt: Resource belongs to profile '${ownership.ownerProfileId}', but active profile is '${activeProfileId}'`,
            false,
            { type: toolMeta.resourceType, id: rawResourceId }
          );
        }
      }
    }

    // 6. Two-Step Action Approval Gate (PRD §12 Action Authorization)
    if (toolMeta.requiresTwoStepApproval) {
      const ticketId = toolCall.approvalTicketId;
      if (!ticketId) {
        if (throwOnError) {
          throw new ActionConfirmationRequiredError(toolName);
        }
        return this.recordDecision(
          authContext,
          toolCall,
          'REQUIRES_USER_APPROVAL',
          toolMeta.riskLevel,
          `High-risk action '${toolName}' requires an approved ActionApprovalTicket before execution`,
          false
        );
      }

      const ticket = await this.resourceResolver.resolveApprovalTicket(ticketId);
      if (!ticket) {
        return this.recordDecision(
          authContext,
          toolCall,
          'DENY_BOLA_VIOLATION',
          'HIGH',
          `Approval ticket '${ticketId}' does not exist`,
          throwOnError
        );
      }

      // Check ticket ownership
      if (ticket.userId !== userId || ticket.profileId !== activeProfileId) {
        if (throwOnError) {
          throw new BolaAuthorizationError('ticket', ticketId, userId);
        }
        return this.recordDecision(
          authContext,
          toolCall,
          'DENY_BOLA_VIOLATION',
          'CRITICAL',
          `Approval ticket '${ticketId}' does not belong to user '${userId}' / profile '${activeProfileId}'`,
          false
        );
      }

      // Check expiration
      if (Date.now() > ticket.expiresAt) {
        return this.recordDecision(
          authContext,
          toolCall,
          'DENY_FORBIDDEN_TOOL',
          toolMeta.riskLevel,
          `Approval ticket '${ticketId}' has expired`,
          throwOnError
        );
      }

      // Check user approval
      if (!ticket.approved) {
        return this.recordDecision(
          authContext,
          toolCall,
          'REQUIRES_USER_APPROVAL',
          toolMeta.riskLevel,
          `Approval ticket '${ticketId}' has not been confirmed by the user`,
          throwOnError
        );
      }

      // Check biometric confirmation if mandated (e.g. Shopify checkout)
      if (toolMeta.requiresBiometricConfirmation && !ticket.biometricConfirmed) {
        return this.recordDecision(
          authContext,
          toolCall,
          'REQUIRES_BIOMETRIC_CONFIRMATION',
          'CRITICAL',
          `Action '${toolName}' requires biometric verification (fingerprint / FaceID)`,
          throwOnError
        );
      }

      // Verify payload hash integrity (protects against parameter substitution after approval)
      const currentActionHash = this.computePayloadHash(toolArgs);
      if (!this.timingSafeHashCompare(currentActionHash, ticket.actionHash)) {
        return this.recordDecision(
          authContext,
          toolCall,
          'DENY_PARAM_TAMPERING',
          'CRITICAL',
          `Action payload hash mismatch! Arguments were modified after user approval was granted`,
          throwOnError
        );
      }
    }

    // 7. All checks passed: PERMIT execution
    return this.recordDecision(
      authContext,
      toolCall,
      'PERMIT',
      toolMeta.riskLevel,
      `Action '${toolName}' fully authorized under active profile '${activeProfileId}'`,
      false
    );
  }

  /**
   * Retrieves historical audit entries recorded during evaluation.
   */
  public getAuditLog(): ReadonlyArray<SecurityAuditEntry> {
    return this.auditLog;
  }

  // ============================================================================
  // Private Helper Methods
  // ============================================================================

  /**
   * Prevents LLM tool arguments from overriding or tampering with authenticated identity.
   */
  private validateParameterIntegrity(
    args: Record<string, unknown>,
    authenticatedUserId: string,
    activeProfileId: string
  ): void {
    const sensitiveKeys = ['userId', 'user_id', 'profileId', 'profile_id', 'auth_uid'];

    for (const key of sensitiveKeys) {
      if (key in args) {
        const value = args[key];
        if (typeof value === 'string') {
          if (
            (key.includes('user') && value !== authenticatedUserId) ||
            (key.includes('profile') && value !== activeProfileId)
          ) {
            throw new ParameterTamperingViolationError(key, value);
          }
        }
      }
    }
  }

  private recordDecision(
    authContext: AuthContext,
    toolCall: ToolCallRequest,
    decision: PolicyDecision,
    riskLevel: ActionRiskLevel,
    reason: string,
    throwException: boolean,
    resourceEvaluated?: { type: string; id: string }
  ): EnforcementResult {
    const auditId = `audit_${createHash('sha256').update(Date.now() + toolCall.callId).digest('hex').slice(0, 16)}`;
    const auditEntry: SecurityAuditEntry = {
      auditId,
      timestamp: new Date().toISOString(),
      userId: authContext.userId,
      profileId: authContext.activeProfileId,
      deviceId: authContext.deviceId,
      toolName: toolCall.toolName,
      decision,
      riskLevel,
      reason,
      resourceEvaluated,
    };

    this.auditLog.push(auditEntry);

    const allowed = decision === 'PERMIT';

    if (!allowed && throwException) {
      throw new SecurityPolicyViolationError(decision, reason);
    }

    return {
      allowed,
      decision,
      riskLevel,
      reason,
      auditEntry,
    };
  }

  private computePayloadHash(args: Record<string, unknown>): string {
    const canonicalJson = JSON.stringify(args, Object.keys(args).sort());
    return createHash('sha256').update(canonicalJson, 'utf8').digest('hex');
  }

  private timingSafeHashCompare(hashA: string, hashB: string): boolean {
    const bufA = Buffer.from(hashA, 'utf8');
    const bufB = Buffer.from(hashB, 'utf8');
    if (bufA.length !== bufB.length) return false;
    return timingSafeEqual(bufA, bufB);
  }
}
