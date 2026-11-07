/**
 * Aster Companion - External Integrations & OAuth Service
 * integration_manager.ts
 *
 * Centralized Integration Manager:
 * - Per-integration connection status lifecycle (CONNECTED, DISCONNECTED, EXPIRED, REVOKED, ERROR, PENDING_AUTH)
 * - Scope auditing & CASA Tier 2 compliance checks
 * - RFC 7009 immediate token revocation endpoint
 * - Two-step Action Approval Gate with risk classification (READ_ONLY, REVERSIBLE, CONSEQUENTIAL, DESTRUCTIVE)
 * - Cryptographic audit trail logging for all sensitive external integration operations.
 */

import { createHash, randomBytes, timingSafeEqual } from 'node:crypto';
import {
  OAuthPKCEHandler,
  OAuthTokens,
  StoredRefreshTokenRecord,
  TokenEncryptionService,
} from './oauth_pkce_handler.js';
import {
  GOOGLE_SCOPES,
  CASA_RESTRICTED_SCOPES,
  ActionApprovalTicket,
  ApprovalRequiredError,
} from './google_integrations.js';

// ============================================================================
// Types and Enums
// ============================================================================

export type IntegrationProvider =
  | 'google_photos'
  | 'google_drive'
  | 'google_gmail'
  | 'google_calendar'
  | 'google_contacts'
  | 'shopify';

export type ConnectionStatus =
  | 'CONNECTED'
  | 'DISCONNECTED'
  | 'EXPIRED'
  | 'REVOKED'
  | 'ERROR'
  | 'PENDING_AUTH';

export type ActionRiskLevel =
  | 'READ_ONLY'      // safe queries, searches, inspection
  | 'REVERSIBLE'     // drafts, staged proposals, carts
  | 'CONSEQUENTIAL'  // external message sends, calendar bookings
  | 'DESTRUCTIVE';   // deletions, credentials revocations

export interface IntegrationConnectionRecord {
  id: string;
  profileId: string;
  provider: IntegrationProvider;
  status: ConnectionStatus;
  accountIdentifier?: string; // e.g. "user@example.com" or "shop.myshopify.com"
  grantedScopes: string[];
  tokenFamilyId?: string;
  connectedAt: number;
  lastUsedAt?: number;
  expiresAt?: number;
  errorDetails?: string;
  metadata?: Record<string, unknown>;
}

export interface ScopeAuditReport {
  profileId: string;
  provider: IntegrationProvider;
  grantedScopes: string[];
  requiredScopes: string[];
  missingScopes: string[];
  hasRestrictedCasaScopes: boolean;
  casaScopesPresent: string[];
  isHealthy: boolean;
  recommendedAction?: 'NONE' | 'REAUTHENTICATE_MISSING_SCOPES' | 'CASA_AUDIT_REQUIRED';
}

export interface IntegrationAuditLogEntry {
  id: string;
  timestamp: number;
  profileId: string;
  provider: IntegrationProvider;
  actionType: string;
  riskLevel: ActionRiskLevel;
  actionHash: string;
  status: 'PROPOSED' | 'APPROVED' | 'REJECTED' | 'EXECUTED' | 'FAILED' | 'REVOKED';
  metadata?: Record<string, unknown>;
}

export interface StagedActionProposal {
  ticketId: string;
  profileId: string;
  provider: IntegrationProvider;
  actionType: string;
  riskLevel: ActionRiskLevel;
  summary: string;
  payload: Record<string, unknown>;
  actionHash: string;
  confirmationToken: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CONSUMED' | 'EXPIRED';
  createdAt: number;
  expiresAt: number;
  approvedAt?: number;
  consumedAt?: number;
}

// Provider Scope Requirements Map
export const PROVIDER_REQUIRED_SCOPES: Record<IntegrationProvider, string[]> = {
  google_photos: [GOOGLE_SCOPES.PHOTOS_PICKER],
  google_drive: [GOOGLE_SCOPES.DRIVE_FILE, GOOGLE_SCOPES.DRIVE_READONLY],
  google_gmail: [GOOGLE_SCOPES.GMAIL_READONLY, GOOGLE_SCOPES.GMAIL_COMPOSE],
  google_calendar: [GOOGLE_SCOPES.CALENDAR_READONLY, GOOGLE_SCOPES.CALENDAR_EVENTS],
  google_contacts: [GOOGLE_SCOPES.CONTACTS_READONLY],
  shopify: ['unauthenticated_read_product_listings'],
};

// ============================================================================
// Integration Manager Implementation
// ============================================================================

export class IntegrationManager {
  // Keyed by `${profileId}:${provider}`
  private readonly connections = new Map<string, IntegrationConnectionRecord>();
  // In-memory active tokens (temporary cache keyed by `${profileId}:${provider}`)
  private readonly activeAccessTokens = new Map<string, { token: string; expiresAt: number }>();
  // Staged action proposals for human-in-the-loop confirmation
  private readonly stagedActions = new Map<string, StagedActionProposal>();
  // Audit trail log
  private readonly auditLogs: IntegrationAuditLogEntry[] = [];
  public readonly oauthHandler: OAuthPKCEHandler;
  private readonly fetchFn: typeof fetch;

  constructor(
    oauthHandler: OAuthPKCEHandler = new OAuthPKCEHandler(),
    fetchFn: typeof fetch = fetch
  ) {
    this.oauthHandler = oauthHandler;
    this.fetchFn = fetchFn;
  }

  private makeKey(profileId: string, provider: IntegrationProvider): string {
    return `${profileId}::${provider}`;
  }

  // ==========================================================================
  // Connection Lifecycle
  // ==========================================================================

  /**
   * Registers or updates an active integration connection.
   */
  public registerConnection(
    profileId: string,
    provider: IntegrationProvider,
    tokens: OAuthTokens,
    grantedScopes: string[],
    accountIdentifier?: string,
    tokenFamilyId?: string
  ): IntegrationConnectionRecord {
    const key = this.makeKey(profileId, provider);
    const now = Date.now();
    const expiresAt = now + tokens.expiresIn * 1000;

    const record: IntegrationConnectionRecord = {
      id: `conn_${randomBytes(8).toString('hex')}`,
      profileId,
      provider,
      status: 'CONNECTED',
      accountIdentifier,
      grantedScopes,
      tokenFamilyId,
      connectedAt: now,
      lastUsedAt: now,
      expiresAt,
    };

    this.connections.set(key, record);
    this.activeAccessTokens.set(key, { token: tokens.accessToken, expiresAt });

    this.logAudit({
      profileId,
      provider,
      actionType: 'INTEGRATION_CONNECTED',
      riskLevel: 'REVERSIBLE',
      payload: { accountIdentifier, scopes: grantedScopes },
      status: 'EXECUTED',
    });

    return record;
  }

  /**
   * Retrieves connection record for a profile and provider.
   */
  public getConnection(profileId: string, provider: IntegrationProvider): IntegrationConnectionRecord | undefined {
    return this.connections.get(this.makeKey(profileId, provider));
  }

  /**
   * Lists all connection records for a companion profile.
   */
  public listConnectionsForProfile(profileId: string): IntegrationConnectionRecord[] {
    const results: IntegrationConnectionRecord[] = [];
    for (const record of this.connections.values()) {
      if (record.profileId === profileId) {
        results.push({ ...record });
      }
    }
    return results;
  }

  /**
   * Retrieves an active valid access token, auto-refreshing if expired.
   */
  public async getValidAccessToken(
    profileId: string,
    provider: IntegrationProvider,
    refreshConfig?: {
      clientId: string;
      clientSecret?: string;
      tokenEndpoint: string;
    }
  ): Promise<string> {
    const key = this.makeKey(profileId, provider);
    const conn = this.connections.get(key);

    if (!conn || conn.status !== 'CONNECTED') {
      throw new Error(`Integration '${provider}' is not connected for profile ${profileId}`);
    }

    const cached = this.activeAccessTokens.get(key);
    const now = Date.now();

    // If cached token has at least 60 seconds of validity remaining
    if (cached && cached.expiresAt > now + 60 * 1000) {
      conn.lastUsedAt = now;
      return cached.token;
    }

    // Attempt token refresh if token family and config are available
    if (conn.tokenFamilyId && refreshConfig) {
      try {
        const refreshResult = await this.oauthHandler.refreshAccessToken(
          {
            providerId: provider,
            clientId: refreshConfig.clientId,
            clientSecret: refreshConfig.clientSecret,
            authorizationEndpoint: '',
            tokenEndpoint: refreshConfig.tokenEndpoint,
            defaultScopes: conn.grantedScopes,
            redirectUri: '',
          },
          profileId,
          conn.tokenFamilyId,
          this.fetchFn
        );

        const newExpiresAt = now + refreshResult.tokens.expiresIn * 1000;
        this.activeAccessTokens.set(key, {
          token: refreshResult.tokens.accessToken,
          expiresAt: newExpiresAt,
        });

        conn.expiresAt = newExpiresAt;
        conn.lastUsedAt = now;

        this.logAudit({
          profileId,
          provider,
          actionType: 'TOKEN_REFRESH_ROTATED',
          riskLevel: 'READ_ONLY',
          payload: { generation: refreshResult.rotationRecord.generation },
          status: 'EXECUTED',
        });

        return refreshResult.tokens.accessToken;
      } catch (err: unknown) {
        conn.status = 'ERROR';
        conn.errorDetails = err instanceof Error ? err.message : String(err);
        throw new Error(`Token refresh failed for ${provider}: ${conn.errorDetails}`);
      }
    }

    if (cached) {
      // Return existing token as last resort if no refresh config is present
      return cached.token;
    }

    throw new Error(`No valid access token available for ${provider}`);
  }

  // ==========================================================================
  // Scope Auditing & CASA Tier 2 Verification
  // ==========================================================================

  /**
   * Audits granted scopes against required and CASA restricted scopes.
   */
  public auditScopes(profileId: string, provider: IntegrationProvider): ScopeAuditReport {
    const conn = this.getConnection(profileId, provider);
    const grantedScopes = conn?.grantedScopes || [];
    const required = PROVIDER_REQUIRED_SCOPES[provider] || [];

    const missingScopes = required.filter((req) => !grantedScopes.includes(req));

    const casaScopesPresent = grantedScopes.filter((scope) =>
      CASA_RESTRICTED_SCOPES.includes(scope as (typeof CASA_RESTRICTED_SCOPES)[number])
    );

    const hasRestrictedCasaScopes = casaScopesPresent.length > 0;
    const isHealthy = Boolean(conn && conn.status === 'CONNECTED' && missingScopes.length === 0);

    let recommendedAction: ScopeAuditReport['recommendedAction'] = 'NONE';
    if (missingScopes.length > 0) {
      recommendedAction = 'REAUTHENTICATE_MISSING_SCOPES';
    } else if (hasRestrictedCasaScopes) {
      recommendedAction = 'CASA_AUDIT_REQUIRED';
    }

    return {
      profileId,
      provider,
      grantedScopes,
      requiredScopes: required,
      missingScopes,
      hasRestrictedCasaScopes,
      casaScopesPresent,
      isHealthy,
      recommendedAction,
    };
  }

  // ==========================================================================
  // Immediate Token Revocation Endpoint (RFC 7009)
  // ==========================================================================

  /**
   * RFC 7009 Token Revocation:
   * Immediately revokes the OAuth token upstream, revokes the refresh token family,
   * purges active caches, and marks the connection as REVOKED.
   */
  public async revokeIntegration(
    profileId: string,
    provider: IntegrationProvider,
    revocationEndpoint = 'https://oauth2.googleapis.com/revoke'
  ): Promise<{ revoked: boolean; provider: IntegrationProvider }> {
    const key = this.makeKey(profileId, provider);
    const conn = this.connections.get(key);

    if (!conn) {
      return { revoked: false, provider };
    }

    // 1. Upstream RFC 7009 revocation if we have an active or refresh token
    const cached = this.activeAccessTokens.get(key);
    const tokenToRevoke = cached?.token;

    if (tokenToRevoke) {
      try {
        await this.fetchFn(`${revocationEndpoint}?token=${encodeURIComponent(tokenToRevoke)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
      } catch (err) {
        // Continue local purge even if upstream returns non-200 or network error
      }
    }

    // 2. Revoke refresh token family
    if (conn.tokenFamilyId) {
      this.oauthHandler.tokenRotationManager.revokeFamily(
        conn.tokenFamilyId,
        'User requested immediate RFC 7009 revocation'
      );
    }

    // 3. Purge cached credentials immediately
    this.activeAccessTokens.delete(key);

    // 4. Update status
    conn.status = 'REVOKED';
    conn.errorDetails = undefined;

    this.logAudit({
      profileId,
      provider,
      actionType: 'RFC_7009_REVOCATION',
      riskLevel: 'DESTRUCTIVE',
      payload: { connectionId: conn.id },
      status: 'REVOKED',
    });

    return { revoked: true, provider };
  }

  // ==========================================================================
  // Action Approval Gate (Two-Step Human-In-The-Loop)
  // ==========================================================================

  /**
   * Stages an action requiring confirmation (Consequential or Destructive).
   * Generates a cryptographic proposal ticket.
   */
  public stageActionProposal(
    profileId: string,
    provider: IntegrationProvider,
    actionType: string,
    riskLevel: ActionRiskLevel,
    summary: string,
    payload: Record<string, unknown>,
    ttlMs = 15 * 60 * 1000
  ): StagedActionProposal {
    const ticketId = `act_${randomBytes(12).toString('hex')}`;
    const confirmationToken = randomBytes(24).toString('base64url');
    const actionHash = createHash('sha256').update(JSON.stringify(payload)).digest('hex');
    const now = Date.now();

    const proposal: StagedActionProposal = {
      ticketId,
      profileId,
      provider,
      actionType,
      riskLevel,
      summary,
      payload,
      actionHash,
      confirmationToken,
      status: 'PENDING',
      createdAt: now,
      expiresAt: now + ttlMs,
    };

    this.stagedActions.set(ticketId, proposal);

    this.logAudit({
      profileId,
      provider,
      actionType,
      riskLevel,
      payload,
      status: 'PROPOSED',
    });

    return proposal;
  }

  /**
   * User approves the staged proposal (e.g. taps "Confirm & Send" on Action Card).
   */
  public approveProposal(ticketId: string): StagedActionProposal {
    const proposal = this.stagedActions.get(ticketId);
    if (!proposal) {
      throw new Error(`Staged action ticket ${ticketId} not found`);
    }
    if (Date.now() > proposal.expiresAt) {
      proposal.status = 'EXPIRED';
      throw new Error(`Staged action ticket ${ticketId} has expired`);
    }
    if (proposal.status !== 'PENDING') {
      throw new Error(`Staged action ticket ${ticketId} is already ${proposal.status}`);
    }

    proposal.status = 'APPROVED';
    proposal.approvedAt = Date.now();

    this.logAudit({
      profileId: proposal.profileId,
      provider: proposal.provider,
      actionType: proposal.actionType,
      riskLevel: proposal.riskLevel,
      payload: proposal.payload,
      status: 'APPROVED',
    });

    return proposal;
  }

  /**
   * Validates and consumes an approved action ticket before executing the external effect.
   * Single-use ticket consumption prevents replay attacks.
   */
  public validateAndConsumeApproval(
    ticketId: string,
    providedConfirmationToken: string,
    expectedPayload: Record<string, unknown>
  ): ActionApprovalTicket {
    const proposal = this.stagedActions.get(ticketId);
    if (!proposal) {
      throw new ApprovalRequiredError('UNKNOWN_ACTION', ticketId);
    }

    if (Date.now() > proposal.expiresAt) {
      proposal.status = 'EXPIRED';
      throw new Error(`Approval ticket ${ticketId} has expired`);
    }

    if (proposal.status !== 'APPROVED') {
      throw new ApprovalRequiredError(proposal.actionType, ticketId);
    }

    // Verify token using timing-safe comparison
    const bufA = Buffer.from(proposal.confirmationToken, 'utf8');
    const bufB = Buffer.from(providedConfirmationToken, 'utf8');
    if (bufA.length !== bufB.length || !timingSafeEqual(bufA, bufB)) {
      throw new Error('Invalid confirmation token presented for action execution');
    }

    // Verify payload integrity matches the proposal
    const expectedHash = createHash('sha256').update(JSON.stringify(expectedPayload)).digest('hex');
    if (proposal.actionHash !== expectedHash) {
      throw new Error('Action payload does not match approved ticket hash');
    }

    // Mark as consumed
    proposal.status = 'CONSUMED';
    proposal.consumedAt = Date.now();

    this.logAudit({
      profileId: proposal.profileId,
      provider: proposal.provider,
      actionType: proposal.actionType,
      riskLevel: proposal.riskLevel,
      payload: proposal.payload,
      status: 'EXECUTED',
    });

    return {
      ticketId: proposal.ticketId,
      profileId: proposal.profileId,
      actionType: proposal.actionType as ActionApprovalTicket['actionType'],
      actionHash: proposal.actionHash,
      confirmationToken: proposal.confirmationToken,
      approved: true,
      approvedAt: proposal.approvedAt,
      expiresAt: proposal.expiresAt,
      summary: proposal.summary,
      payload: proposal.payload,
    };
  }

  // ==========================================================================
  // Audit Trail Logging
  // ==========================================================================

  private logAudit(entry: {
    profileId: string;
    provider: IntegrationProvider;
    actionType: string;
    riskLevel: ActionRiskLevel;
    payload: Record<string, unknown>;
    status: IntegrationAuditLogEntry['status'];
  }): void {
    const actionHash = createHash('sha256').update(JSON.stringify(entry.payload)).digest('hex');
    const record: IntegrationAuditLogEntry = {
      id: `audit_${randomBytes(8).toString('hex')}`,
      timestamp: Date.now(),
      profileId: entry.profileId,
      provider: entry.provider,
      actionType: entry.actionType,
      riskLevel: entry.riskLevel,
      actionHash,
      status: entry.status,
      metadata: entry.payload,
    };
    this.auditLogs.push(record);
  }

  public getAuditLogsForProfile(profileId: string): IntegrationAuditLogEntry[] {
    return this.auditLogs.filter((l) => l.profileId === profileId);
  }
}
