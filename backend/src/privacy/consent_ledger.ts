/**
 * Aster Companion - Privacy, Consent & Data Rights
 * consent_ledger.ts
 *
 * Authoritative, immutable, tamper-evident consent tracking ledger.
 * Implements strict explicit consent tracking for:
 * 1. Screen awareness capture (MediaProjection / ReplayKit / ScreenCaptureKit)
 * 2. Environmental audio recording (ambient microphone & other-app playback)
 * 3. Synthetic voice cloning authorization (biometric speech training & non-impersonation)
 * 4. Google integration scopes (Photos Picker, Drive, Gmail restricted, Calendar, Contacts)
 *
 * Compliant with:
 * - GDPR Article 7 (Conditions for consent) & Article 9 (Special categories of data)
 * - Nigeria Data Protection Act (NDPA) 2023 Section 26 (Consent) & NDPC GAID
 * - Apple App Store Review Guideline 5.1.1 (Data Collection & Storage)
 * - Google Play User Data Policy (Prominent Disclosure & Consent)
 */

import { createHash, randomUUID } from 'node:crypto';
import { z } from 'zod';

// ============================================================================
// 1. Consent Scopes & Enums
// ============================================================================

export const ScreenAwarenessScopes = [
  'screen_awareness:capture',
  'screen_awareness:ocr',
  'screen_awareness:ui_understanding',
] as const;

export const EnvironmentalAudioScopes = [
  'environmental_audio:mic',
  'environmental_audio:other_app_playback',
] as const;

export const SyntheticVoiceScopes = [
  'synthetic_voice:voice_sample_recording',
  'synthetic_voice:model_training',
  'synthetic_voice:synthesis_playback',
  'synthetic_voice:non_impersonation_affirmation',
] as const;

export const GoogleIntegrationScopes = [
  'google_integration:photos_picker',
  'google_integration:drive_readonly',
  'google_integration:gmail_restricted',
  'google_integration:calendar',
  'google_integration:contacts',
] as const;

export const AllConsentScopes = [
  ...ScreenAwarenessScopes,
  ...EnvironmentalAudioScopes,
  ...SyntheticVoiceScopes,
  ...GoogleIntegrationScopes,
] as const;

export type ScreenAwarenessScope = (typeof ScreenAwarenessScopes)[number];
export type EnvironmentalAudioScope = (typeof EnvironmentalAudioScopes)[number];
export type SyntheticVoiceScope = (typeof SyntheticVoiceScopes)[number];
export type GoogleIntegrationScope = (typeof GoogleIntegrationScopes)[number];
export type ConsentScope = (typeof AllConsentScopes)[number];

export const ConsentStatusEnum = ['GRANTED', 'REVOKED', 'EXPIRED', 'DENIED'] as const;
export type ConsentStatus = (typeof ConsentStatusEnum)[number];

export const ClientPlatformEnum = [
  'android',
  'ios',
  'macos',
  'windows',
  'linux',
  'web',
] as const;
export type ClientPlatform = (typeof ClientPlatformEnum)[number];

// ============================================================================
// 2. Zod Validation Schemas
// ============================================================================

export const ConsentProvenanceSchema = z.object({
  deviceId: z.string().min(1, 'Device ID is required'),
  platform: z.enum(ClientPlatformEnum),
  appVersion: z.string().min(1, 'App version is required'),
  ipHash: z.string().regex(/^[a-f0-9]{64}$/, 'IP hash must be a SHA-256 hexadecimal string'),
  userAgent: z.string().min(1, 'User agent is required'),
  affirmationText: z.string().min(1, 'Affirmation statement text is required'),
});

export type ConsentProvenance = z.infer<typeof ConsentProvenanceSchema>;

export const ConsentRecordSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().min(1, 'User ID is required'),
  profileId: z.string().optional(), // Profile-scoped consent if applicable (Aster Profile A vs B)
  scope: z.enum(AllConsentScopes),
  status: z.enum(ConsentStatusEnum),
  policyVersion: z.string().min(1),
  policyDigest: z.string().regex(/^[a-f0-9]{64}$/, 'Policy digest must be a SHA-256 hash'),
  grantedAt: z.number().int().positive(),
  revokedAt: z.number().int().positive().optional(),
  expiresAt: z.number().int().positive().optional(),
  provenance: ConsentProvenanceSchema,
  previousHash: z.string(), // Cryptographic link to previous ledger entry for user
  recordHash: z.string(),   // SHA-256 hash of this record
  metadata: z.record(z.unknown()).optional(),
});

export type ConsentRecord = z.infer<typeof ConsentRecordSchema>;

export interface GrantConsentParams {
  userId: string;
  profileId?: string;
  scope: ConsentScope;
  policyVersion: string;
  policyDigest: string;
  provenance: ConsentProvenance;
  expiresInMs?: number;
  metadata?: Record<string, unknown>;
}

export interface RevokeConsentParams {
  userId: string;
  profileId?: string;
  scope: ConsentScope;
  deviceId: string;
  reason: string;
}

// ============================================================================
// 3. Cryptographic Hashing Utilities
// ============================================================================

export function computeSha256(data: string): string {
  return createHash('sha256').update(data, 'utf8').digest('hex');
}

export function hashIpAddress(ip: string, salt = 'aster_consent_salt_v1'): string {
  return computeSha256(`${salt}:${ip.trim()}`);
}

export function computeRecordHash(
  recordWithoutHash: Omit<ConsentRecord, 'recordHash'>
): string {
  const canonicalString = JSON.stringify({
    id: recordWithoutHash.id,
    userId: recordWithoutHash.userId,
    profileId: recordWithoutHash.profileId || null,
    scope: recordWithoutHash.scope,
    status: recordWithoutHash.status,
    policyVersion: recordWithoutHash.policyVersion,
    policyDigest: recordWithoutHash.policyDigest,
    grantedAt: recordWithoutHash.grantedAt,
    revokedAt: recordWithoutHash.revokedAt || null,
    expiresAt: recordWithoutHash.expiresAt || null,
    provenance: {
      deviceId: recordWithoutHash.provenance.deviceId,
      platform: recordWithoutHash.provenance.platform,
      appVersion: recordWithoutHash.provenance.appVersion,
      ipHash: recordWithoutHash.provenance.ipHash,
      userAgent: recordWithoutHash.provenance.userAgent,
      affirmationText: recordWithoutHash.provenance.affirmationText,
    },
    previousHash: recordWithoutHash.previousHash,
    metadata: recordWithoutHash.metadata || null,
  });

  return computeSha256(canonicalString);
}

// ============================================================================
// 4. Persistence Repository Interface
// ============================================================================

export interface IConsentRepository {
  appendRecord(record: ConsentRecord): Promise<void>;
  getRecordsByUserId(userId: string): Promise<ConsentRecord[]>;
  getLatestRecord(
    userId: string,
    scope: ConsentScope,
    profileId?: string
  ): Promise<ConsentRecord | null>;
  getAllActiveConsents(userId: string, profileId?: string): Promise<ConsentRecord[]>;
}

/**
 * In-memory thread-safe implementation of IConsentRepository for local testing
 * and microservice caching.
 */
export class InMemoryConsentRepository implements IConsentRepository {
  private readonly records: ConsentRecord[] = [];

  public async appendRecord(record: ConsentRecord): Promise<void> {
    this.records.push(Object.freeze({ ...record }));
  }

  public async getRecordsByUserId(userId: string): Promise<ConsentRecord[]> {
    return this.records
      .filter((r) => r.userId === userId)
      .sort((a, b) => a.grantedAt - b.grantedAt);
  }

  public async getLatestRecord(
    userId: string,
    scope: ConsentScope,
    profileId?: string
  ): Promise<ConsentRecord | null> {
    const userRecords = this.records.filter(
      (r) =>
        r.userId === userId &&
        r.scope === scope &&
        (profileId === undefined || r.profileId === undefined || r.profileId === profileId)
    );

    if (userRecords.length === 0) return null;
    return userRecords[userRecords.length - 1] ?? null;
  }

  public async getAllActiveConsents(userId: string, profileId?: string): Promise<ConsentRecord[]> {
    const now = Date.now();
    const map = new Map<string, ConsentRecord>();

    // Scan sequentially to pick latest for each scope
    for (const record of this.records) {
      if (record.userId !== userId) continue;
      if (profileId && record.profileId && record.profileId !== profileId) continue;

      const key = `${record.scope}:${record.profileId ?? 'global'}`;
      map.set(key, record);
    }

    const activeList: ConsentRecord[] = [];
    for (const record of map.values()) {
      if (record.status === 'GRANTED') {
        if (!record.expiresAt || record.expiresAt > now) {
          activeList.push(record);
        }
      }
    }
    return activeList;
  }

  public clear(): void {
    this.records.length = 0;
  }
}

// ============================================================================
// 5. Revocation Callbacks / Event System
// ============================================================================

export type RevocationListener = (event: {
  userId: string;
  profileId?: string;
  scope: ConsentScope;
  deviceId: string;
  reason: string;
  revokedAt: number;
}) => Promise<void> | void;

// ============================================================================
// 6. Consent Ledger Main Engine
// ============================================================================

export class ConsentLedger {
  private readonly repository: IConsentRepository;
  private readonly revocationListeners: Map<ConsentScope | '*', Set<RevocationListener>> =
    new Map();

  // Genesis hash constant for user consent blockchain
  public static readonly GENESIS_HASH =
    '0000000000000000000000000000000000000000000000000000000000000000';

  constructor(repository?: IConsentRepository) {
    this.repository = repository ?? new InMemoryConsentRepository();
  }

  /**
   * Registers a callback fired immediately when a scope consent is revoked.
   * Useful for stopping active MediaProjection screen capture, muting environmental mic,
   * purging audio/video buffers, or disconnecting OAuth tokens.
   */
  public onRevoke(scope: ConsentScope | '*', listener: RevocationListener): () => void {
    if (!this.revocationListeners.has(scope)) {
      this.revocationListeners.set(scope, new Set());
    }
    const set = this.revocationListeners.get(scope)!;
    set.add(listener);

    return () => {
      set.delete(listener);
    };
  }

  /**
   * Records explicit, affirmative opt-in consent for a capability scope.
   * Calculates the chained hash linking to the user's previous ledger entry.
   */
  public async grantConsent(params: GrantConsentParams): Promise<ConsentRecord> {
    ConsentProvenanceSchema.parse(params.provenance);

    const existingRecords = await this.repository.getRecordsByUserId(params.userId);
    const previousHash =
      existingRecords.length > 0
        ? existingRecords[existingRecords.length - 1]!.recordHash
        : ConsentLedger.GENESIS_HASH;

    const now = Date.now();
    const expiresAt = params.expiresInMs ? now + params.expiresInMs : undefined;

    const unsignedRecord: Omit<ConsentRecord, 'recordHash'> = {
      id: randomUUID(),
      userId: params.userId,
      profileId: params.profileId,
      scope: params.scope,
      status: 'GRANTED',
      policyVersion: params.policyVersion,
      policyDigest: params.policyDigest,
      grantedAt: now,
      expiresAt,
      provenance: params.provenance,
      previousHash,
      metadata: params.metadata,
    };

    const recordHash = computeRecordHash(unsignedRecord);
    const completeRecord: ConsentRecord = {
      ...unsignedRecord,
      recordHash,
    };

    ConsentRecordSchema.parse(completeRecord);
    await this.repository.appendRecord(completeRecord);
    return completeRecord;
  }

  /**
   * Explicitly denies consent during an opt-in prompt.
   */
  public async recordDenial(params: GrantConsentParams): Promise<ConsentRecord> {
    ConsentProvenanceSchema.parse(params.provenance);

    const existingRecords = await this.repository.getRecordsByUserId(params.userId);
    const previousHash =
      existingRecords.length > 0
        ? existingRecords[existingRecords.length - 1]!.recordHash
        : ConsentLedger.GENESIS_HASH;

    const now = Date.now();
    const unsignedRecord: Omit<ConsentRecord, 'recordHash'> = {
      id: randomUUID(),
      userId: params.userId,
      profileId: params.profileId,
      scope: params.scope,
      status: 'DENIED',
      policyVersion: params.policyVersion,
      policyDigest: params.policyDigest,
      grantedAt: now,
      provenance: params.provenance,
      previousHash,
      metadata: params.metadata,
    };

    const recordHash = computeRecordHash(unsignedRecord);
    const completeRecord: ConsentRecord = {
      ...unsignedRecord,
      recordHash,
    };

    ConsentRecordSchema.parse(completeRecord);
    await this.repository.appendRecord(completeRecord);
    return completeRecord;
  }

  /**
   * Revokes an existing consent.
   * Appends an immutable REVOKED entry to the ledger and immediately triggers revocation hooks.
   */
  public async revokeConsent(params: RevokeConsentParams): Promise<ConsentRecord> {
    const existingRecords = await this.repository.getRecordsByUserId(params.userId);
    const previousHash =
      existingRecords.length > 0
        ? existingRecords[existingRecords.length - 1]!.recordHash
        : ConsentLedger.GENESIS_HASH;

    const latest = await this.repository.getLatestRecord(
      params.userId,
      params.scope,
      params.profileId
    );

    const now = Date.now();
    const policyVersion = latest?.policyVersion ?? '1.1.0';
    const policyDigest =
      latest?.policyDigest ?? computeSha256('aster-default-policy-v1.1');

    const unsignedRecord: Omit<ConsentRecord, 'recordHash'> = {
      id: randomUUID(),
      userId: params.userId,
      profileId: params.profileId,
      scope: params.scope,
      status: 'REVOKED',
      policyVersion,
      policyDigest,
      grantedAt: latest?.grantedAt ?? now,
      revokedAt: now,
      provenance: {
        deviceId: params.deviceId,
        platform: latest?.provenance.platform ?? 'android',
        appVersion: latest?.provenance.appVersion ?? '1.1.0',
        ipHash: latest?.provenance.ipHash ?? computeSha256('revocation-internal'),
        userAgent: latest?.provenance.userAgent ?? 'Aster-Client-Revocation',
        affirmationText: `Consent revoked: ${params.reason}`,
      },
      previousHash,
      metadata: {
        revocationReason: params.reason,
        priorConsentId: latest?.id,
      },
    };

    const recordHash = computeRecordHash(unsignedRecord);
    const completeRecord: ConsentRecord = {
      ...unsignedRecord,
      recordHash,
    };

    ConsentRecordSchema.parse(completeRecord);
    await this.repository.appendRecord(completeRecord);

    // Trigger revocation callbacks asynchronously
    await this.notifyRevocation({
      userId: params.userId,
      profileId: params.profileId,
      scope: params.scope,
      deviceId: params.deviceId,
      reason: params.reason,
      revokedAt: now,
    });

    return completeRecord;
  }

  /**
   * Checks whether active, unexpired, unrevoked consent is granted for a given scope.
   */
  public async hasConsent(
    userId: string,
    scope: ConsentScope,
    profileId?: string
  ): Promise<boolean> {
    const record = await this.repository.getLatestRecord(userId, scope, profileId);
    if (!record) return false;
    if (record.status !== 'GRANTED') return false;
    if (record.expiresAt && Date.now() > record.expiresAt) return false;
    return true;
  }

  /**
   * Evaluates the current state of a consent scope, including expiration detection.
   */
  public async evaluateScope(
    userId: string,
    scope: ConsentScope,
    profileId?: string
  ): Promise<{
    hasAccess: boolean;
    status: ConsentStatus | 'NOT_REQUESTED';
    record?: ConsentRecord;
    reason?: string;
  }> {
    const record = await this.repository.getLatestRecord(userId, scope, profileId);
    if (!record) {
      return {
        hasAccess: false,
        status: 'NOT_REQUESTED',
        reason: 'Consent has never been requested or granted for this scope',
      };
    }

    if (record.status === 'REVOKED') {
      return {
        hasAccess: false,
        status: 'REVOKED',
        record,
        reason: `Consent was explicitly revoked at ${new Date(record.revokedAt!).toISOString()}`,
      };
    }

    if (record.status === 'DENIED') {
      return {
        hasAccess: false,
        status: 'DENIED',
        record,
        reason: 'Consent was explicitly denied by the user',
      };
    }

    if (record.expiresAt && Date.now() > record.expiresAt) {
      return {
        hasAccess: false,
        status: 'EXPIRED',
        record,
        reason: `Consent expired at ${new Date(record.expiresAt).toISOString()}`,
      };
    }

    return {
      hasAccess: true,
      status: 'GRANTED',
      record,
    };
  }

  /**
   * Retrieves all active consent grants for a user or profile.
   */
  public async getActiveConsents(userId: string, profileId?: string): Promise<ConsentRecord[]> {
    return this.repository.getAllActiveConsents(userId, profileId);
  }

  /**
   * Retrieves complete chronological audit trail of all consent transactions for a user.
   */
  public async getConsentAuditTrail(
    userId: string,
    scope?: ConsentScope
  ): Promise<ConsentRecord[]> {
    const records = await this.repository.getRecordsByUserId(userId);
    if (!scope) return records;
    return records.filter((r) => r.scope === scope);
  }

  /**
   * Cryptographically verifies the integrity of the user's consent blockchain.
   * Returns true if all hashes match and chain is intact without tampering.
   */
  public async verifyLedgerIntegrity(userId: string): Promise<{
    isValid: boolean;
    totalRecords: number;
    tamperedRecordId?: string;
    error?: string;
  }> {
    const records = await this.repository.getRecordsByUserId(userId);
    if (records.length === 0) {
      return { isValid: true, totalRecords: 0 };
    }

    let expectedPreviousHash = ConsentLedger.GENESIS_HASH;

    for (let i = 0; i < records.length; i++) {
      const record = records[i]!;

      // 1. Check previous hash continuity
      if (record.previousHash !== expectedPreviousHash) {
        return {
          isValid: false,
          totalRecords: records.length,
          tamperedRecordId: record.id,
          error: `Broken chain link at index ${i}: expected previousHash ${expectedPreviousHash}, found ${record.previousHash}`,
        };
      }

      // 2. Recompute and verify record hash
      const { recordHash, ...unsigned } = record;
      const recomputedHash = computeRecordHash(unsigned);

      if (recomputedHash !== recordHash) {
        return {
          isValid: false,
          totalRecords: records.length,
          tamperedRecordId: record.id,
          error: `Corrupted record hash at index ${i} (${record.id}): recomputed ${recomputedHash} vs stored ${recordHash}`,
        };
      }

      expectedPreviousHash = recordHash;
    }

    return { isValid: true, totalRecords: records.length };
  }

  private async notifyRevocation(event: {
    userId: string;
    profileId?: string;
    scope: ConsentScope;
    deviceId: string;
    reason: string;
    revokedAt: number;
  }): Promise<void> {
    const specificListeners = this.revocationListeners.get(event.scope) ?? new Set();
    const wildcardListeners = this.revocationListeners.get('*') ?? new Set();

    const allListeners = [...specificListeners, ...wildcardListeners];
    await Promise.all(
      allListeners.map(async (fn) => {
        try {
          await fn(event);
        } catch (err) {
          console.error(
            `[ConsentLedger] Error executing revocation listener for scope ${event.scope}:`,
            err
          );
        }
      })
    );
  }
}
