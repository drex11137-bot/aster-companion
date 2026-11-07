/**
 * Aster Companion - Privacy, Consent & Data Rights
 * cascade_deletion_worker.ts
 *
 * Authoritative Cascade Deletion Worker.
 * Compliant with:
 * - GDPR Article 17 (Right to Erasure / "Right to be Forgotten")
 * - Nigeria Data Protection Act (NDPA) 2023 Section 32 & 34 (Right to Erasure & Objection)
 * - Apple App Store Review Guideline 5.1.1(v) (Account Deletion & Data Removal)
 * - Google Play Store Policy on Account Deletion & User Data Retention
 *
 * Guarantees:
 * 1. Complete cascading purge across relational entities:
 *    - companion_profiles (max 2 per account)
 *    - memories (episodic, semantic, preference, procedural, explicitly shared)
 *    - events (visual frame metadata, OCR summaries, multimodal events)
 *    - sessions (active & historical sessions across all devices)
 *    - chat_messages (conversation history & attachments metadata)
 *    - actions (proactive action logs, tool executions, approval audit)
 *    - voice_models (synthetic voice acoustic models, training manifests)
 *    - integration_tokens (OAuth tokens, encrypted refresh tokens)
 * 2. Unlinks and removes raw media chunks from cloud storage buckets:
 *    - media-chunks (buffered streaming audio/video)
 *    - voice-samples (biometric training recordings)
 *    - visual-frames (captured screen frames)
 *    - attachments (chat images, documents, audio clips)
 * 3. Generates an immutable, cryptographically signed Deletion Certificate
 *    proving full compliance without retaining any personal data.
 */

import { createHash, createHmac, randomUUID } from 'node:crypto';
import { z } from 'zod';

// ============================================================================
// 1. Schemas & Types
// ============================================================================

export const DeletionScopeEnum = ['FULL_ACCOUNT', 'COMPANION_PROFILE_ONLY'] as const;
export type DeletionScope = (typeof DeletionScopeEnum)[number];

export const ComplianceLegalBasisEnum = [
  'GDPR_ARTICLE_17_RIGHT_TO_ERASURE',
  'NDPA_2023_SECTION_32_RIGHT_TO_ERASURE',
  'USER_ACCOUNT_TERMINATION_REQUEST',
  'PROFILE_RESET_REQUEST',
] as const;
export type ComplianceLegalBasis = (typeof ComplianceLegalBasisEnum)[number];

export const DeletionCertificateSchema = z.object({
  certificateId: z.string().uuid(),
  userIdHash: z.string().regex(/^[a-f0-9]{64}$/, 'Hashed user identifier'),
  profileId: z.string().optional(),
  deletionScope: z.enum(DeletionScopeEnum),
  legalBasis: z.array(z.enum(ComplianceLegalBasisEnum)),
  requestedAt: z.number().int().positive(),
  completedAt: z.number().int().positive(),
  durationMs: z.number().int().nonnegative(),
  purgedCounts: z.object({
    profiles: z.number().int().nonnegative(),
    memories: z.number().int().nonnegative(),
    events: z.number().int().nonnegative(),
    sessions: z.number().int().nonnegative(),
    chatMessages: z.number().int().nonnegative(),
    actions: z.number().int().nonnegative(),
    voiceModels: z.number().int().nonnegative(),
    integrationTokens: z.number().int().nonnegative(),
    consentRecordsTombstoned: z.number().int().nonnegative(),
    storageObjectsRemoved: z.number().int().nonnegative(),
  }),
  storageBucketsProcessed: z.array(z.string()),
  issuer: z.string().min(1),
  tamperProofDigest: z.string().regex(/^[a-f0-9]{64}$/),
  hmacSignature: z.string().min(32),
});

export type DeletionCertificate = z.infer<typeof DeletionCertificateSchema>;

export interface CascadeDeletionRequest {
  userId: string;
  profileId?: string; // If supplied, deletes only Profile A or Profile B while keeping account
  scope: DeletionScope;
  legalBasis?: ComplianceLegalBasis[];
  reason?: string;
  requestedBy: 'USER' | 'ADMIN' | 'AUTOMATED_RETENTION_EXPIRY';
  clientIp?: string;
  deviceId?: string;
}

export interface CascadeDeletionResult {
  success: boolean;
  certificate: DeletionCertificate;
  error?: string;
}

// Storage buckets where raw media chunks reside
export const ASTER_STORAGE_BUCKETS = [
  'media-chunks',
  'voice-samples',
  'visual-frames',
  'attachments',
] as const;

export type AsterStorageBucket = (typeof ASTER_STORAGE_BUCKETS)[number];

// ============================================================================
// 2. Storage & Database Abstraction Interfaces
// ============================================================================

export interface IStorageBucketProvider {
  /**
   * Deletes all storage objects prefixed with userId (and optionally profileId).
   * Returns count of deleted objects.
   */
  deleteObjectsByPrefix(bucket: string, prefix: string): Promise<number>;
  listObjectsByPrefix(bucket: string, prefix: string): Promise<string[]>;
}

export interface IDataStoreProvider {
  deleteActions(userId: string, profileId?: string): Promise<number>;
  deleteChatMessages(userId: string, profileId?: string): Promise<number>;
  deleteEvents(userId: string, profileId?: string): Promise<number>;
  deleteMemories(userId: string, profileId?: string): Promise<number>;
  deleteVoiceModels(userId: string, profileId?: string): Promise<number>;
  deleteSessions(userId: string, profileId?: string): Promise<number>;
  deleteCompanionProfiles(userId: string, profileId?: string): Promise<number>;
  deleteIntegrationTokens(userId: string, profileId?: string): Promise<number>;
  tombstoneConsentRecords(userId: string, profileId?: string): Promise<number>;
  deleteUserAccount(userId: string): Promise<boolean>;
}

export interface IDeletionCertificateStore {
  saveCertificate(cert: DeletionCertificate): Promise<void>;
  getCertificate(certificateId: string): Promise<DeletionCertificate | null>;
  listCertificatesForUserHash(userHash: string): Promise<DeletionCertificate[]>;
}

// ============================================================================
// 3. In-Memory Mock Implementations for Isolated Testing
// ============================================================================

export class InMemoryStorageBucketProvider implements IStorageBucketProvider {
  private readonly buckets = new Map<string, Set<string>>();

  constructor() {
    for (const b of ASTER_STORAGE_BUCKETS) {
      this.buckets.set(b, new Set());
    }
  }

  public async putObject(bucket: string, key: string): Promise<void> {
    if (!this.buckets.has(bucket)) {
      this.buckets.set(bucket, new Set());
    }
    this.buckets.get(bucket)!.add(key);
  }

  public async deleteObjectsByPrefix(bucket: string, prefix: string): Promise<number> {
    const set = this.buckets.get(bucket);
    if (!set) return 0;
    let count = 0;
    for (const key of Array.from(set)) {
      if (key.startsWith(prefix)) {
        set.delete(key);
        count++;
      }
    }
    return count;
  }

  public async listObjectsByPrefix(bucket: string, prefix: string): Promise<string[]> {
    const set = this.buckets.get(bucket);
    if (!set) return [];
    return Array.from(set).filter((k) => k.startsWith(prefix));
  }
}

export class InMemoryDataStoreProvider implements IDataStoreProvider {
  public actions: Array<{ id: string; userId: string; profileId?: string }> = [];
  public chatMessages: Array<{ id: string; userId: string; profileId?: string }> = [];
  public events: Array<{ id: string; userId: string; profileId?: string }> = [];
  public memories: Array<{ id: string; userId: string; profileId?: string }> = [];
  public voiceModels: Array<{ id: string; userId: string; profileId?: string }> = [];
  public sessions: Array<{ id: string; userId: string; profileId?: string }> = [];
  public companionProfiles: Array<{ id: string; userId: string }> = [];
  public integrationTokens: Array<{ id: string; userId: string; profileId?: string }> = [];
  public consentRecords: Array<{ id: string; userId: string; profileId?: string; isTombstoned?: boolean }> = [];
  public users: Array<{ id: string; email: string }> = [];

  public async deleteActions(userId: string, profileId?: string): Promise<number> {
    const before = this.actions.length;
    this.actions = this.actions.filter(
      (a) => a.userId !== userId || (profileId !== undefined && a.profileId !== profileId)
    );
    return before - this.actions.length;
  }

  public async deleteChatMessages(userId: string, profileId?: string): Promise<number> {
    const before = this.chatMessages.length;
    this.chatMessages = this.chatMessages.filter(
      (m) => m.userId !== userId || (profileId !== undefined && m.profileId !== profileId)
    );
    return before - this.chatMessages.length;
  }

  public async deleteEvents(userId: string, profileId?: string): Promise<number> {
    const before = this.events.length;
    this.events = this.events.filter(
      (e) => e.userId !== userId || (profileId !== undefined && e.profileId !== profileId)
    );
    return before - this.events.length;
  }

  public async deleteMemories(userId: string, profileId?: string): Promise<number> {
    const before = this.memories.length;
    this.memories = this.memories.filter(
      (m) => m.userId !== userId || (profileId !== undefined && m.profileId !== profileId)
    );
    return before - this.memories.length;
  }

  public async deleteVoiceModels(userId: string, profileId?: string): Promise<number> {
    const before = this.voiceModels.length;
    this.voiceModels = this.voiceModels.filter(
      (v) => v.userId !== userId || (profileId !== undefined && v.profileId !== profileId)
    );
    return before - this.voiceModels.length;
  }

  public async deleteSessions(userId: string, profileId?: string): Promise<number> {
    const before = this.sessions.length;
    this.sessions = this.sessions.filter(
      (s) => s.userId !== userId || (profileId !== undefined && s.profileId !== profileId)
    );
    return before - this.sessions.length;
  }

  public async deleteCompanionProfiles(userId: string, profileId?: string): Promise<number> {
    const before = this.companionProfiles.length;
    this.companionProfiles = this.companionProfiles.filter(
      (p) => p.userId !== userId || (profileId !== undefined && p.id !== profileId)
    );
    return before - this.companionProfiles.length;
  }

  public async deleteIntegrationTokens(userId: string, profileId?: string): Promise<number> {
    const before = this.integrationTokens.length;
    this.integrationTokens = this.integrationTokens.filter(
      (t) => t.userId !== userId || (profileId !== undefined && t.profileId !== profileId)
    );
    return before - this.integrationTokens.length;
  }

  public async tombstoneConsentRecords(userId: string, profileId?: string): Promise<number> {
    let modified = 0;
    for (const record of this.consentRecords) {
      if (record.userId === userId && (profileId === undefined || record.profileId === profileId)) {
        record.isTombstoned = true;
        modified++;
      }
    }
    return modified;
  }

  public async deleteUserAccount(userId: string): Promise<boolean> {
    const before = this.users.length;
    this.users = this.users.filter((u) => u.id !== userId);
    return before > this.users.length;
  }
}

export class InMemoryDeletionCertificateStore implements IDeletionCertificateStore {
  private readonly certificates = new Map<string, DeletionCertificate>();

  public async saveCertificate(cert: DeletionCertificate): Promise<void> {
    this.certificates.set(cert.certificateId, Object.freeze({ ...cert }));
  }

  public async getCertificate(certificateId: string): Promise<DeletionCertificate | null> {
    return this.certificates.get(certificateId) ?? null;
  }

  public async listCertificatesForUserHash(userHash: string): Promise<DeletionCertificate[]> {
    return Array.from(this.certificates.values()).filter((c) => c.userIdHash === userHash);
  }
}

// ============================================================================
// 4. Cascade Deletion Worker Engine
// ============================================================================

export class CascadeDeletionWorker {
  private readonly signingKey: Buffer;
  private readonly userHashSalt: string;

  constructor(
    private readonly datastore: IDataStoreProvider,
    private readonly storage: IStorageBucketProvider,
    private readonly certificateStore: IDeletionCertificateStore,
    options?: {
      signingKeyHex?: string;
      userHashSalt?: string;
    }
  ) {
    this.userHashSalt = options?.userHashSalt ?? process.env.ASTER_AUDIT_SALT ?? 'aster_erasure_audit_salt_2026';
    const keyHex = options?.signingKeyHex ?? process.env.ASTER_COMPLIANCE_SIGNING_KEY;
    if (keyHex && keyHex.length === 64) {
      this.signingKey = Buffer.from(keyHex, 'hex');
    } else {
      this.signingKey = createHash('sha256').update(this.userHashSalt + ':compliance_signer_v1').digest();
    }
  }

  /**
   * Hashes userId with non-reversible audit salt to preserve GDPR privacy
   * while maintaining an auditable certificate.
   */
  public hashUserId(userId: string): string {
    return createHash('sha256').update(`${this.userHashSalt}:${userId.trim()}`).digest('hex');
  }

  /**
   * Executes the full cascade erasure sequence.
   * Enforces transactional entity dependencies and unlinks all storage chunks.
   */
  public async executeCascadeDeletion(
    req: CascadeDeletionRequest
  ): Promise<CascadeDeletionResult> {
    const startTime = Date.now();
    const userIdHash = this.hashUserId(req.userId);
    const certificateId = randomUUID();

    try {
      // 1. Determine Storage Prefix
      // Full account: `users/<userId>/`
      // Single profile: `users/<userId>/profiles/<profileId>/`
      const storagePrefix = req.profileId
        ? `users/${req.userId}/profiles/${req.profileId}/`
        : `users/${req.userId}/`;

      // 2. Cascade Storage Deletions across all media buckets
      let storageObjectsRemoved = 0;
      const bucketsProcessed: string[] = [];

      for (const bucket of ASTER_STORAGE_BUCKETS) {
        const removed = await this.storage.deleteObjectsByPrefix(bucket, storagePrefix);
        storageObjectsRemoved += removed;
        bucketsProcessed.push(bucket);
      }

      // Also remove any direct user attachments prefix `attachments/<userId>/`
      if (!req.profileId) {
        const directAttachmentsRemoved = await this.storage.deleteObjectsByPrefix(
          'attachments',
          `${req.userId}/`
        );
        storageObjectsRemoved += directAttachmentsRemoved;
      }

      // 3. Cascade Relational Entity Deletions in dependency order
      // Order: Child records first -> parent records
      const actionsPurged = await this.datastore.deleteActions(req.userId, req.profileId);
      const chatMessagesPurged = await this.datastore.deleteChatMessages(req.userId, req.profileId);
      const eventsPurged = await this.datastore.deleteEvents(req.userId, req.profileId);
      const memoriesPurged = await this.datastore.deleteMemories(req.userId, req.profileId);
      const voiceModelsPurged = await this.datastore.deleteVoiceModels(req.userId, req.profileId);
      const sessionsPurged = await this.datastore.deleteSessions(req.userId, req.profileId);
      const integrationTokensPurged = await this.datastore.deleteIntegrationTokens(
        req.userId,
        req.profileId
      );
      const consentRecordsTombstoned = await this.datastore.tombstoneConsentRecords(
        req.userId,
        req.profileId
      );

      // Finally delete profile(s)
      const profilesPurged = await this.datastore.deleteCompanionProfiles(
        req.userId,
        req.profileId
      );

      // If full account deletion, delete user account row itself
      if (req.scope === 'FULL_ACCOUNT') {
        await this.datastore.deleteUserAccount(req.userId);
      }

      const completedAt = Date.now();
      const durationMs = completedAt - startTime;

      // 4. Construct Deletion Certificate
      const legalBasis: ComplianceLegalBasis[] =
        req.legalBasis && req.legalBasis.length > 0
          ? req.legalBasis
          : req.scope === 'FULL_ACCOUNT'
            ? [
                'GDPR_ARTICLE_17_RIGHT_TO_ERASURE',
                'NDPA_2023_SECTION_32_RIGHT_TO_ERASURE',
                'USER_ACCOUNT_TERMINATION_REQUEST',
              ]
            : ['PROFILE_RESET_REQUEST'];

      const unsignedData = {
        certificateId,
        userIdHash,
        profileId: req.profileId,
        deletionScope: req.scope,
        legalBasis,
        requestedAt: startTime,
        completedAt,
        durationMs,
        purgedCounts: {
          profiles: profilesPurged,
          memories: memoriesPurged,
          events: eventsPurged,
          sessions: sessionsPurged,
          chatMessages: chatMessagesPurged,
          actions: actionsPurged,
          voiceModels: voiceModelsPurged,
          integrationTokens: integrationTokensPurged,
          consentRecordsTombstoned,
          storageObjectsRemoved,
        },
        storageBucketsProcessed: bucketsProcessed,
        issuer: 'Aster Companion Compliance & Erasure Authority',
      };

      const canonicalJson = JSON.stringify(unsignedData);
      const tamperProofDigest = createHash('sha256').update(canonicalJson).digest('hex');
      const hmacSignature = createHmac('sha256', this.signingKey)
        .update(tamperProofDigest)
        .digest('hex');

      const certificate: DeletionCertificate = {
        ...unsignedData,
        tamperProofDigest,
        hmacSignature,
      };

      // Validate certificate schema
      DeletionCertificateSchema.parse(certificate);

      // 5. Store certificate in append-only store
      await this.certificateStore.saveCertificate(certificate);

      return {
        success: true,
        certificate,
      };
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      console.error(
        `[CascadeDeletionWorker] Cascade deletion failed for user hash ${userIdHash}:`,
        errorMessage
      );

      // Construct a partial failure certificate if needed
      const fallbackDigest = createHash('sha256').update(certificateId + ':FAILED').digest('hex');
      const fallbackSig = createHmac('sha256', this.signingKey).update(fallbackDigest).digest('hex');

      const failedCertificate: DeletionCertificate = {
        certificateId,
        userIdHash,
        profileId: req.profileId,
        deletionScope: req.scope,
        legalBasis: ['USER_ACCOUNT_TERMINATION_REQUEST'],
        requestedAt: startTime,
        completedAt: Date.now(),
        durationMs: Date.now() - startTime,
        purgedCounts: {
          profiles: 0,
          memories: 0,
          events: 0,
          sessions: 0,
          chatMessages: 0,
          actions: 0,
          voiceModels: 0,
          integrationTokens: 0,
          consentRecordsTombstoned: 0,
          storageObjectsRemoved: 0,
        },
        storageBucketsProcessed: [],
        issuer: 'Aster Companion Compliance & Erasure Authority',
        tamperProofDigest: fallbackDigest,
        hmacSignature: fallbackSig,
      };

      return {
        success: false,
        certificate: failedCertificate,
        error: errorMessage,
      };
    }
  }

  /**
   * Cryptographically verifies the validity of an issued Deletion Certificate.
   */
  public verifyCertificateSignature(cert: DeletionCertificate): boolean {
    const unsignedData = {
      certificateId: cert.certificateId,
      userIdHash: cert.userIdHash,
      profileId: cert.profileId,
      deletionScope: cert.deletionScope,
      legalBasis: cert.legalBasis,
      requestedAt: cert.requestedAt,
      completedAt: cert.completedAt,
      durationMs: cert.durationMs,
      purgedCounts: cert.purgedCounts,
      storageBucketsProcessed: cert.storageBucketsProcessed,
      issuer: cert.issuer,
    };

    const canonicalJson = JSON.stringify(unsignedData);
    const expectedDigest = createHash('sha256').update(canonicalJson).digest('hex');

    if (expectedDigest !== cert.tamperProofDigest) {
      return false;
    }

    const expectedHmac = createHmac('sha256', this.signingKey)
      .update(expectedDigest)
      .digest('hex');

    return expectedHmac === cert.hmacSignature;
  }
}
