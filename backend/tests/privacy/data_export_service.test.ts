import { describe, it, expect } from 'vitest';
import {
  DataExportService,
  InMemoryPrivacyDataProvider,
  ExportProfileConfig,
  ExportChatMessage,
  ExportMemoryRecord,
  ExportActionLog,
  ExportConnectedIntegration,
  ExportDeviceSession,
} from '../../src/privacy/data_export_service.js';
import { ConsentLedger, InMemoryConsentRepository, computeSha256 } from '../../src/privacy/consent_ledger.js';

describe('DataExportService Unit & Integration Tests', () => {
  it('generates a full GDPR Art. 20 & NDPA Sec. 34 compliant export bundle', async () => {
    const dataProvider = new InMemoryPrivacyDataProvider();
    const consentRepo = new InMemoryConsentRepository();
    const consentLedger = new ConsentLedger(consentRepo);

    const userId = 'usr_maya_portability';

    // Set up user
    dataProvider.user = {
      userId,
      email: 'maya@example.com',
      createdAt: Date.now() - 30 * 86400000,
      status: 'active',
    };

    // Set up profiles (Aster and Nova)
    const profileAster: ExportProfileConfig = {
      id: 'prof_aster',
      userId,
      name: 'Aster',
      isDefault: true,
      avatar: {
        presentationStyle: 'photorealistic_human',
        apparentAge: '28',
        skinTone: 'warm_olive',
        hairColor: 'Auburn',
        hairStyle: 'Long wavy',
        eyeColor: 'Hazel',
        clothingPreset: 'Casual blazer',
        is3dRenderingEnabled: true,
      },
      voice: {
        voiceId: 'voice_warm_01',
        voiceLabel: 'Warm voice',
        warmth: 0.85,
        pitch: 1.0,
        rate: 1.0,
        isClonedSynthetic: false,
      },
      personality: {
        warmth: 0.9,
        humor: 0.6,
        formality: 0.3,
        responseLength: 'concise',
        initiative: 0.7,
        interruptionsAllowed: false,
      },
      preferences: { morningGreeting: true },
      proactiveSettings: {
        enabled: true,
        quietHoursStart: '22:00',
        quietHoursEnd: '07:00',
        maxSuggestionsPerDay: 5,
      },
      createdAt: Date.now() - 30 * 86400000,
      updatedAt: Date.now() - 1000,
    };

    const profileNova: ExportProfileConfig = {
      id: 'prof_nova',
      userId,
      name: 'Nova',
      isDefault: false,
      avatar: {
        presentationStyle: 'stylized_human',
        hairColor: 'Silver',
        eyeColor: 'Blue',
        clothingPreset: 'Minimalist tech',
        is3dRenderingEnabled: true,
      },
      voice: {
        voiceId: 'voice_energetic_02',
        voiceLabel: 'Energetic',
        warmth: 0.6,
        pitch: 1.1,
        rate: 1.1,
        isClonedSynthetic: false,
      },
      personality: {
        warmth: 0.7,
        humor: 0.8,
        formality: 0.1,
        responseLength: 'balanced',
        initiative: 0.8,
        interruptionsAllowed: true,
      },
      preferences: { workoutReminders: true },
      proactiveSettings: {
        enabled: true,
        maxSuggestionsPerDay: 8,
      },
      createdAt: Date.now() - 15 * 86400000,
      updatedAt: Date.now() - 2000,
    };

    dataProvider.profiles = [profileAster, profileNova];

    // Chat messages (strictly isolated)
    const chatAster: ExportChatMessage = {
      id: 'msg_ast_1',
      sessionId: 'sess_1',
      profileId: 'prof_aster',
      role: 'user',
      content: 'Can you plan my Saturday?',
      attachments: [],
      referencedMemoryIds: ['mem_1'],
      timestamp: Date.now() - 86400000,
    };

    const chatNova: ExportChatMessage = {
      id: 'msg_nov_1',
      sessionId: 'sess_2',
      profileId: 'prof_nova',
      role: 'user',
      content: 'Give me a fast tempo running playlist.',
      attachments: [],
      referencedMemoryIds: [],
      timestamp: Date.now() - 43200000,
    };

    dataProvider.chatMessages = [chatAster, chatNova];

    // Memories
    const memoryAster: ExportMemoryRecord = {
      id: 'mem_1',
      profileId: 'prof_aster',
      category: 'preference',
      content: 'Prefers short answers in the morning',
      confidenceScore: 0.95,
      sourceProvenance: 'direct_user_statement',
      sensitivityLevel: 'standard',
      status: 'active',
      createdAt: Date.now() - 86400000,
      updatedAt: Date.now() - 86400000,
    };

    dataProvider.memories = [memoryAster];

    // Action logs
    const actionLog: ExportActionLog = {
      id: 'act_1',
      profileId: 'prof_aster',
      toolName: 'google_calendar_create_event',
      parametersSanitized: { title: 'Call Dad', time: '19:30' },
      riskLevel: 'reversible',
      executionStatus: 'executed',
      userConfirmedAt: Date.now() - 10000,
      verificationResult: 'Event created with ID evt_778',
      timestamp: Date.now() - 10000,
    };

    dataProvider.actionLogs = [actionLog];

    // Connected integration (sanitized, no tokens)
    const integration: ExportConnectedIntegration = {
      id: 'int_1',
      profileId: 'prof_aster',
      provider: 'google',
      grantedScopes: ['https://www.googleapis.com/auth/calendar.events'],
      connectionStatus: 'connected',
      connectedAt: Date.now() - 2000000,
      lastSyncedAt: Date.now() - 1000,
    };

    dataProvider.connectedIntegrations = [integration];

    // Device session
    const session: ExportDeviceSession = {
      sessionId: 'sess_1',
      profileId: 'prof_aster',
      deviceId: 'pixel_8_pro_id',
      platform: 'android',
      osVersion: '14.0',
      clientVersion: '1.1.0',
      createdAt: Date.now() - 86400000,
      lastActiveAt: Date.now() - 1000,
      status: 'active',
    };

    dataProvider.deviceSessions = [session];

    // Consent records
    await consentLedger.grantConsent({
      userId,
      profileId: 'prof_aster',
      scope: 'screen_awareness:capture',
      policyVersion: '1.1.0',
      policyDigest: computeSha256('policy'),
      provenance: {
        deviceId: 'pixel_8_pro_id',
        platform: 'android',
        appVersion: '1.1.0',
        ipHash: computeSha256('ip_hash_salt'),
        userAgent: 'AsterClient/1.1.0',
        affirmationText: 'I consent to screen awareness.',
      },
    });

    const exportService = new DataExportService(dataProvider, consentLedger);
    const archive = await exportService.generateExportArchive(userId);

    // Assertions on archive structure
    expect(archive.exportMetadata.formatVersion).toBe('1.1.0');
    expect(archive.exportMetadata.legalBasis).toContain('GDPR_ARTICLE_20_RIGHT_TO_DATA_PORTABILITY');
    expect(archive.exportMetadata.legalBasis).toContain('NIGERIA_NDPA_2023_SECTION_34_DATA_PORTABILITY');

    // Strict profile isolation check
    expect(archive.profiles.length).toBe(2);
    expect(archive.chatHistoriesByProfile['prof_aster']?.length).toBe(1);
    expect(archive.chatHistoriesByProfile['prof_nova']?.length).toBe(1);
    expect(archive.chatHistoriesByProfile['prof_aster']?.[0]?.content).toBe('Can you plan my Saturday?');
    expect(archive.chatHistoriesByProfile['prof_nova']?.[0]?.content).toBe(
      'Give me a fast tempo running playlist.'
    );

    // Cryptographic verification
    expect(archive.cryptographicVerification.payloadSha256Digest).toBeDefined();
    expect(archive.cryptographicVerification.hmacSignature).toBeDefined();

    const isVerified = exportService.verifyExportIntegrity(archive);
    expect(isVerified).toBe(true);
  });

  it('detects tampering in export archives during verification', async () => {
    const dataProvider = new InMemoryPrivacyDataProvider();
    const consentRepo = new InMemoryConsentRepository();
    const consentLedger = new ConsentLedger(consentRepo);

    const userId = 'usr_tamper_archive';
    dataProvider.user = {
      userId,
      email: 'tamper@example.com',
      createdAt: Date.now(),
      status: 'active',
    };

    const exportService = new DataExportService(dataProvider, consentLedger);
    const archive = await exportService.generateExportArchive(userId);

    // Tamper with data
    // @ts-expect-error tamper test
    archive.userAccount.email = 'tampered_email@attacker.com';

    const isValid = exportService.verifyExportIntegrity(archive);
    expect(isValid).toBe(false);
  });
});
