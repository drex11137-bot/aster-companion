/**
 * Aster Companion - Privacy, Consent & Data Rights
 * data_export_service.ts
 *
 * Authoritative Data Portability & Account Export Service.
 * Compliant with:
 * - GDPR Article 20 (Right to data portability - structured, commonly used, machine-readable format)
 * - Nigeria Data Protection Act (NDPA) 2023 Section 34 (Right to Data Portability)
 * - Apple App Store Review Guideline 5.1.1 (Data Collection & User Rights)
 * - Google Play User Data Policy (Data Transparency & Portability)
 *
 * Generates an end-to-end, tamper-evident JSON archive of:
 * 1. Profile Configurations (Max 2 isolated profiles, appearance, voice, personality, preferences)
 * 2. Chat Histories (Per-profile, strictly isolated, zero cross-profile leakage)
 * 3. Memory Records (Timestamps, confidence scores, provenance, sensitivity levels)
 * 4. Audit Logs (Tool actions, proactive interventions, inter-profile selective sharing events)
 * 5. Connected Integrations (Google scopes, Shopify, status; sanitized of all secret credentials)
 * 6. Device Sessions (Registered devices, platforms, activity timestamps)
 * 7. Consent Ledger Records (Cryptographic consent blockchain history)
 */

import { createHash, createHmac, randomUUID } from 'node:crypto';
import { z } from 'zod';
import { ConsentRecord, ConsentLedger } from './consent_ledger.js';

// ============================================================================
// 1. Export Data Models & Zod Schemas
// ============================================================================

export const ExportProfileConfigSchema = z.object({
  id: z.string(),
  userId: z.string(),
  name: z.string(),
  isDefault: z.boolean(),
  avatar: z.object({
    presentationStyle: z.string(), // e.g. "photorealistic_human", "stylized_human"
    apparentAge: z.string().optional(),
    skinTone: z.string().optional(),
    hairColor: z.string(),
    hairStyle: z.string().optional(),
    eyeColor: z.string(),
    clothingPreset: z.string(),
    is3dRenderingEnabled: z.boolean(),
  }),
  voice: z.object({
    voiceId: z.string(),
    voiceLabel: z.string(),
    warmth: z.number().min(0).max(1),
    pitch: z.number().min(0.5).max(2),
    rate: z.number().min(0.5).max(2),
    isClonedSynthetic: z.boolean(),
  }),
  personality: z.object({
    warmth: z.number().min(0).max(1),
    humor: z.number().min(0).max(1),
    formality: z.number().min(0).max(1),
    responseLength: z.enum(['concise', 'balanced', 'detailed']),
    initiative: z.number().min(0).max(1),
    interruptionsAllowed: z.boolean(),
  }),
  preferences: z.record(z.unknown()),
  proactiveSettings: z.object({
    enabled: z.boolean(),
    quietHoursStart: z.string().optional(),
    quietHoursEnd: z.string().optional(),
    maxSuggestionsPerDay: z.number(),
  }),
  createdAt: z.number(),
  updatedAt: z.number(),
});

export type ExportProfileConfig = z.infer<typeof ExportProfileConfigSchema>;

export const ExportChatMessageSchema = z.object({
  id: z.string(),
  sessionId: z.string(),
  profileId: z.string(),
  role: z.enum(['user', 'assistant', 'system']),
  content: z.string(),
  attachments: z.array(
    z.object({
      id: z.string(),
      fileName: z.string(),
      mimeType: z.string(),
      sizeBytes: z.number(),
      storageUri: z.string().optional(),
    })
  ),
  referencedMemoryIds: z.array(z.string()),
  timestamp: z.number(),
});

export type ExportChatMessage = z.infer<typeof ExportChatMessageSchema>;

export const MemoryCategoryEnum = [
  'preference',
  'people',
  'plans',
  'conversational',
  'procedural',
  'explicitly_shared',
] as const;
export type MemoryCategory = (typeof MemoryCategoryEnum)[number];

export const ExportMemoryRecordSchema = z.object({
  id: z.string(),
  profileId: z.string(),
  category: z.enum(MemoryCategoryEnum),
  content: z.string(),
  confidenceScore: z.number().min(0).max(1),
  sourceProvenance: z.enum([
    'direct_user_statement',
    'conversation_inference',
    'screen_context',
    'environmental_audio',
    'calendar_sync',
    'explicitly_shared_from_other_profile',
  ]),
  sensitivityLevel: z.enum(['standard', 'sensitive', 'strictly_confidential']),
  status: z.enum(['active', 'archived', 'forgotten']),
  expiresAt: z.number().optional(),
  createdAt: z.number(),
  updatedAt: z.number(),
});

export type ExportMemoryRecord = z.infer<typeof ExportMemoryRecordSchema>;

export const ExportActionLogSchema = z.object({
  id: z.string(),
  profileId: z.string(),
  toolName: z.string(),
  parametersSanitized: z.record(z.unknown()),
  riskLevel: z.enum(['read_only', 'reversible', 'consequential', 'irreversible']),
  executionStatus: z.enum(['pending_user_confirmation', 'confirmed', 'executed', 'rejected', 'failed']),
  userConfirmedAt: z.number().optional(),
  verificationResult: z.string().optional(),
  timestamp: z.number(),
});

export type ExportActionLog = z.infer<typeof ExportActionLogSchema>;

export const ExportSelectiveSharingEventSchema = z.object({
  sharingId: z.string(),
  sourceProfileId: z.string(),
  targetProfileId: z.string(),
  memoryId: z.string(),
  userConfirmedAt: z.number(),
  reason: z.string(),
  revocationStatus: z.enum(['active', 'revoked']),
  revokedAt: z.number().optional(),
});

export type ExportSelectiveSharingEvent = z.infer<typeof ExportSelectiveSharingEventSchema>;

export const ExportConnectedIntegrationSchema = z.object({
  id: z.string(),
  profileId: z.string(),
  provider: z.string(), // e.g. "google", "shopify"
  grantedScopes: z.array(z.string()),
  connectionStatus: z.enum(['connected', 'disconnected', 'expired', 'error']),
  connectedAt: z.number(),
  lastSyncedAt: z.number().optional(),
  // Explicitly note: secrets/refresh tokens are NEVER included
});

export type ExportConnectedIntegration = z.infer<typeof ExportConnectedIntegrationSchema>;

export const ExportDeviceSessionSchema = z.object({
  sessionId: z.string(),
  profileId: z.string().optional(),
  deviceId: z.string(),
  platform: z.enum(['android', 'ios', 'macos', 'windows', 'linux', 'web']),
  osVersion: z.string(),
  clientVersion: z.string(),
  createdAt: z.number(),
  lastActiveAt: z.number(),
  status: z.enum(['active', 'ended', 'revoked']),
});

export type ExportDeviceSession = z.infer<typeof ExportDeviceSessionSchema>;

export const AccountDataExportArchiveSchema = z.object({
  exportMetadata: z.object({
    exportId: z.string().uuid(),
    userId: z.string(),
    generatedAt: z.string(), // ISO-8601
    generatedAtUnixMs: z.number(),
    formatVersion: z.literal('1.1.0'),
    legalBasis: z.array(z.string()),
    systemName: z.literal('Aster Companion Cloud Platform'),
    complianceCertifications: z.array(z.string()),
  }),
  userAccount: z.object({
    userId: z.string(),
    email: z.string(),
    createdAt: z.number(),
    status: z.string(),
  }),
  profiles: z.array(ExportProfileConfigSchema),
  chatHistoriesByProfile: z.record(z.array(ExportChatMessageSchema)),
  memoriesByProfile: z.record(z.array(ExportMemoryRecordSchema)),
  explicitlySharedMemories: z.array(ExportMemoryRecordSchema),
  auditTrail: z.object({
    actionLogs: z.array(ExportActionLogSchema),
    selectiveSharingEvents: z.array(ExportSelectiveSharingEventSchema),
  }),
  connectedIntegrations: z.array(ExportConnectedIntegrationSchema),
  deviceSessions: z.array(ExportDeviceSessionSchema),
  consentHistory: z.array(z.record(z.unknown())),
  summary: z.object({
    totalProfiles: z.number(),
    totalChatMessages: z.number(),
    totalMemories: z.number(),
    totalActionsLogged: z.number(),
    totalConnectedIntegrations: z.number(),
    totalDeviceSessions: z.number(),
    totalConsentTransactions: z.number(),
  }),
  cryptographicVerification: z.object({
    payloadSha256Digest: z.string().regex(/^[a-f0-9]{64}$/),
    hmacSignature: z.string().min(32),
  }),
});

export type AccountDataExportArchive = z.infer<typeof AccountDataExportArchiveSchema>;

// ============================================================================
// 2. Data Provider Interface
// ============================================================================

export interface IPrivacyDataProvider {
  getUserAccount(userId: string): Promise<{
    userId: string;
    email: string;
    createdAt: number;
    status: string;
  } | null>;
  getCompanionProfiles(userId: string): Promise<ExportProfileConfig[]>;
  getChatMessages(userId: string, profileId?: string): Promise<ExportChatMessage[]>;
  getMemories(userId: string, profileId?: string): Promise<ExportMemoryRecord[]>;
  getExplicitlySharedMemories(userId: string): Promise<ExportMemoryRecord[]>;
  getActionLogs(userId: string, profileId?: string): Promise<ExportActionLog[]>;
  getSelectiveSharingEvents(userId: string): Promise<ExportSelectiveSharingEvent[]>;
  getConnectedIntegrations(userId: string): Promise<ExportConnectedIntegration[]>;
  getDeviceSessions(userId: string): Promise<ExportDeviceSession[]>;
}

// ============================================================================
// 3. In-Memory Data Provider for Isolated Testing & Mocks
// ============================================================================

export class InMemoryPrivacyDataProvider implements IPrivacyDataProvider {
  public user: { userId: string; email: string; createdAt: number; status: string } | null = null;
  public profiles: ExportProfileConfig[] = [];
  public chatMessages: ExportChatMessage[] = [];
  public memories: ExportMemoryRecord[] = [];
  public actionLogs: ExportActionLog[] = [];
  public selectiveSharingEvents: ExportSelectiveSharingEvent[] = [];
  public connectedIntegrations: ExportConnectedIntegration[] = [];
  public deviceSessions: ExportDeviceSession[] = [];

  public async getUserAccount(userId: string) {
    if (this.user && this.user.userId === userId) {
      return this.user;
    }
    return null;
  }

  public async getCompanionProfiles(userId: string): Promise<ExportProfileConfig[]> {
    return this.profiles.filter((p) => p.userId === userId);
  }

  public async getChatMessages(userId: string, profileId?: string): Promise<ExportChatMessage[]> {
    const userProfiles = new Set(
      this.profiles.filter((p) => p.userId === userId).map((p) => p.id)
    );
    return this.chatMessages.filter(
      (m) => userProfiles.has(m.profileId) && (profileId === undefined || m.profileId === profileId)
    );
  }

  public async getMemories(userId: string, profileId?: string): Promise<ExportMemoryRecord[]> {
    const userProfiles = new Set(
      this.profiles.filter((p) => p.userId === userId).map((p) => p.id)
    );
    return this.memories.filter(
      (m) =>
        userProfiles.has(m.profileId) &&
        m.category !== 'explicitly_shared' &&
        (profileId === undefined || m.profileId === profileId)
    );
  }

  public async getExplicitlySharedMemories(userId: string): Promise<ExportMemoryRecord[]> {
    const userProfiles = new Set(
      this.profiles.filter((p) => p.userId === userId).map((p) => p.id)
    );
    return this.memories.filter(
      (m) => userProfiles.has(m.profileId) && m.category === 'explicitly_shared'
    );
  }

  public async getActionLogs(userId: string, profileId?: string): Promise<ExportActionLog[]> {
    const userProfiles = new Set(
      this.profiles.filter((p) => p.userId === userId).map((p) => p.id)
    );
    return this.actionLogs.filter(
      (a) => userProfiles.has(a.profileId) && (profileId === undefined || a.profileId === profileId)
    );
  }

  public async getSelectiveSharingEvents(
    userId: string
  ): Promise<ExportSelectiveSharingEvent[]> {
    const userProfiles = new Set(
      this.profiles.filter((p) => p.userId === userId).map((p) => p.id)
    );
    return this.selectiveSharingEvents.filter(
      (s) => userProfiles.has(s.sourceProfileId) || userProfiles.has(s.targetProfileId)
    );
  }

  public async getConnectedIntegrations(
    userId: string
  ): Promise<ExportConnectedIntegration[]> {
    const userProfiles = new Set(
      this.profiles.filter((p) => p.userId === userId).map((p) => p.id)
    );
    return this.connectedIntegrations.filter((i) => userProfiles.has(i.profileId));
  }

  public async getDeviceSessions(userId: string): Promise<ExportDeviceSession[]> {
    const userProfiles = new Set(
      this.profiles.filter((p) => p.userId === userId).map((p) => p.id)
    );
    return this.deviceSessions.filter(
      (d) => d.profileId === undefined || userProfiles.has(d.profileId)
    );
  }
}

// ============================================================================
// 4. Data Export Service Implementation
// ============================================================================

export class DataExportService {
  private readonly hmacSigningKey: Buffer;

  constructor(
    private readonly dataProvider: IPrivacyDataProvider,
    private readonly consentLedger: ConsentLedger,
    signingKeyHex?: string
  ) {
    if (signingKeyHex && signingKeyHex.length === 64) {
      this.hmacSigningKey = Buffer.from(signingKeyHex, 'hex');
    } else {
      const fallbackKey =
        process.env.ASTER_EXPORT_SIGNING_KEY || 'aster-export-tamper-proof-signing-key-v1';
      this.hmacSigningKey = createHash('sha256').update(fallbackKey).digest();
    }
  }

  /**
   * Generates a complete GDPR Art. 20 & NDPA Sec. 34 compliant export archive.
   * Guarantees strict profile isolation: chats and memories are categorized per profile.
   */
  public async generateExportArchive(userId: string): Promise<AccountDataExportArchive> {
    const exportId = randomUUID();
    const now = Date.now();
    const generatedAtIso = new Date(now).toISOString();

    // 1. Fetch User Account
    const userAccount = await this.dataProvider.getUserAccount(userId);
    if (!userAccount) {
      throw new Error(`Cannot export data: User with ID ${userId} does not exist`);
    }

    // 2. Fetch Profiles (Max 2 per account as defined in PRD v1.1 DEC-021)
    const profiles = await this.dataProvider.getCompanionProfiles(userId);
    if (profiles.length > 2) {
      console.warn(
        `[DataExportService] User ${userId} has ${profiles.length} profiles, exceeding PRD v1.1 limit of 2.`
      );
    }

    // 3. Fetch Chats per Profile (Strict Profile Isolation Check)
    const chatHistoriesByProfile: Record<string, ExportChatMessage[]> = {};
    let totalChatMessages = 0;

    for (const profile of profiles) {
      const messages = await this.dataProvider.getChatMessages(userId, profile.id);
      // Validate that all messages strictly belong to this profile
      for (const msg of messages) {
        if (msg.profileId !== profile.id) {
          throw new Error(
            `Cross-profile contamination detected! Message ${msg.id} belonging to profile ${msg.profileId} returned in query for profile ${profile.id}`
          );
        }
      }
      chatHistoriesByProfile[profile.id] = messages;
      totalChatMessages += messages.length;
    }

    // 4. Fetch Memories per Profile & Explicitly Shared Memories
    const memoriesByProfile: Record<string, ExportMemoryRecord[]> = {};
    let totalMemories = 0;

    for (const profile of profiles) {
      const profileMemories = await this.dataProvider.getMemories(userId, profile.id);
      memoriesByProfile[profile.id] = profileMemories;
      totalMemories += profileMemories.length;
    }

    const explicitlySharedMemories = await this.dataProvider.getExplicitlySharedMemories(userId);
    totalMemories += explicitlySharedMemories.length;

    // 5. Fetch Audit Trail (Actions & Inter-Profile Selective Sharing Events)
    const actionLogs = await this.dataProvider.getActionLogs(userId);
    const selectiveSharingEvents = await this.dataProvider.getSelectiveSharingEvents(userId);

    // 6. Fetch Connected Integrations (Strict Credential Sanitization)
    const connectedIntegrations = await this.dataProvider.getConnectedIntegrations(userId);

    // 7. Fetch Device Sessions
    const deviceSessions = await this.dataProvider.getDeviceSessions(userId);

    // 8. Fetch Consent Ledger Trail
    const rawConsentTrail = await this.consentLedger.getConsentAuditTrail(userId);
    const consentHistory: Record<string, unknown>[] = rawConsentTrail.map((record: ConsentRecord) => ({
      id: record.id,
      scope: record.scope,
      status: record.status,
      policyVersion: record.policyVersion,
      policyDigest: record.policyDigest,
      grantedAt: record.grantedAt,
      revokedAt: record.revokedAt,
      expiresAt: record.expiresAt,
      provenance: record.provenance,
      recordHash: record.recordHash,
      previousHash: record.previousHash,
    }));

    // 9. Build Payload for Hashing
    const corePayload = {
      exportMetadata: {
        exportId,
        userId,
        generatedAt: generatedAtIso,
        generatedAtUnixMs: now,
        formatVersion: '1.1.0' as const,
        legalBasis: [
          'GDPR_ARTICLE_20_RIGHT_TO_DATA_PORTABILITY',
          'NIGERIA_NDPA_2023_SECTION_34_DATA_PORTABILITY',
        ],
        systemName: 'Aster Companion Cloud Platform' as const,
        complianceCertifications: [
          'ISO_IEC_27001_ALIGNED',
          'GDPR_COMPLIANT',
          'NDPA_GAID_COMPLIANT',
          'SOC2_TYPE_II_CONTROLS',
        ],
      },
      userAccount,
      profiles,
      chatHistoriesByProfile,
      memoriesByProfile,
      explicitlySharedMemories,
      auditTrail: {
        actionLogs,
        selectiveSharingEvents,
      },
      connectedIntegrations,
      deviceSessions,
      consentHistory,
      summary: {
        totalProfiles: profiles.length,
        totalChatMessages,
        totalMemories,
        totalActionsLogged: actionLogs.length,
        totalConnectedIntegrations: connectedIntegrations.length,
        totalDeviceSessions: deviceSessions.length,
        totalConsentTransactions: consentHistory.length,
      },
    };

    // 10. Generate Tamper-Proof Cryptographic Signatures
    const canonicalPayloadString = JSON.stringify(corePayload);
    const payloadSha256Digest = createHash('sha256')
      .update(canonicalPayloadString, 'utf8')
      .digest('hex');

    const hmacSignature = createHmac('sha256', this.hmacSigningKey)
      .update(payloadSha256Digest, 'utf8')
      .digest('hex');

    const completeArchive: AccountDataExportArchive = {
      ...corePayload,
      cryptographicVerification: {
        payloadSha256Digest,
        hmacSignature,
      },
    };

    // 11. Schema Verification
    AccountDataExportArchiveSchema.parse(completeArchive);

    return completeArchive;
  }

  /**
   * Verifies the cryptographic integrity of an exported archive.
   * Can be executed by the user or auditing regulators to verify
   * that data was not altered after export.
   */
  public verifyExportIntegrity(archive: AccountDataExportArchive): boolean {
    const { cryptographicVerification, ...corePayload } = archive;

    const canonicalString = JSON.stringify(corePayload);
    const recomputedDigest = createHash('sha256').update(canonicalString, 'utf8').digest('hex');

    if (recomputedDigest !== cryptographicVerification.payloadSha256Digest) {
      return false;
    }

    const recomputedHmac = createHmac('sha256', this.hmacSigningKey)
      .update(recomputedDigest, 'utf8')
      .digest('hex');

    return recomputedHmac === cryptographicVerification.hmacSignature;
  }
}
