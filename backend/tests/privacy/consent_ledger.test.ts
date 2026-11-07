import { describe, it, expect, vi } from 'vitest';
import {
  ConsentLedger,
  InMemoryConsentRepository,
  computeSha256,
  hashIpAddress,
  ConsentProvenance,
} from '../../src/privacy/consent_ledger.js';

describe('ConsentLedger Unit & Integration Tests', () => {
  const dummyProvenance: ConsentProvenance = {
    deviceId: 'android_pixel_8_pro_001',
    platform: 'android',
    appVersion: '1.1.0',
    ipHash: hashIpAddress('192.168.1.100'),
    userAgent: 'AsterCompanion/1.1.0 (Linux; Android 14; Pixel 8 Pro)',
    affirmationText: 'I explicitly grant continuous screen awareness capture permissions.',
  };

  it('records explicit consent for screen awareness with cryptographic chaining', async () => {
    const repository = new InMemoryConsentRepository();
    const ledger = new ConsentLedger(repository);

    const record = await ledger.grantConsent({
      userId: 'usr_maya_777',
      profileId: 'prof_aster_primary',
      scope: 'screen_awareness:capture',
      policyVersion: '1.1.0',
      policyDigest: computeSha256('privacy_policy_v1.1'),
      provenance: dummyProvenance,
    });

    expect(record.status).toBe('GRANTED');
    expect(record.previousHash).toBe(ConsentLedger.GENESIS_HASH);
    expect(record.recordHash).toBeDefined();

    const hasConsent = await ledger.hasConsent(
      'usr_maya_777',
      'screen_awareness:capture',
      'prof_aster_primary'
    );
    expect(hasConsent).toBe(true);

    const integrity = await ledger.verifyLedgerIntegrity('usr_maya_777');
    expect(integrity.isValid).toBe(true);
    expect(integrity.totalRecords).toBe(1);
  });

  it('maintains tamper-evident cryptographic blockchain across multiple consent grants', async () => {
    const repository = new InMemoryConsentRepository();
    const ledger = new ConsentLedger(repository);

    const rec1 = await ledger.grantConsent({
      userId: 'usr_test_chain',
      scope: 'screen_awareness:capture',
      policyVersion: '1.1.0',
      policyDigest: computeSha256('policy1'),
      provenance: dummyProvenance,
    });

    const rec2 = await ledger.grantConsent({
      userId: 'usr_test_chain',
      scope: 'environmental_audio:mic',
      policyVersion: '1.1.0',
      policyDigest: computeSha256('policy2'),
      provenance: {
        ...dummyProvenance,
        affirmationText: 'I consent to environmental audio capture.',
      },
    });

    const rec3 = await ledger.grantConsent({
      userId: 'usr_test_chain',
      scope: 'synthetic_voice:model_training',
      policyVersion: '1.1.0',
      policyDigest: computeSha256('policy3'),
      provenance: {
        ...dummyProvenance,
        affirmationText: 'I authorize synthetic voice model training on my recorded voice.',
      },
    });

    expect(rec1.previousHash).toBe(ConsentLedger.GENESIS_HASH);
    expect(rec2.previousHash).toBe(rec1.recordHash);
    expect(rec3.previousHash).toBe(rec2.recordHash);

    const integrity = await ledger.verifyLedgerIntegrity('usr_test_chain');
    expect(integrity.isValid).toBe(true);
    expect(integrity.totalRecords).toBe(3);
  });

  it('detects tampering if a record in the ledger is modified', async () => {
    const repository = new InMemoryConsentRepository();
    const ledger = new ConsentLedger(repository);

    await ledger.grantConsent({
      userId: 'usr_tamper_target',
      scope: 'screen_awareness:capture',
      policyVersion: '1.1.0',
      policyDigest: computeSha256('policy1'),
      provenance: dummyProvenance,
    });

    await ledger.grantConsent({
      userId: 'usr_tamper_target',
      scope: 'google_integration:photos_picker',
      policyVersion: '1.1.0',
      policyDigest: computeSha256('policy2'),
      provenance: dummyProvenance,
    });

    // Tamper with record in repository to simulate unauthorized database modification
    const internalRecords = (repository as unknown as { records: ConsentRecord[] }).records;
    const original = internalRecords[0]!;
    internalRecords[0] = {
      ...original,
      policyVersion: '2.0.0_hacked',
    };

    const integrity = await ledger.verifyLedgerIntegrity('usr_tamper_target');
    expect(integrity.isValid).toBe(false);
    expect(integrity.error).toContain('Corrupted record hash');
  });

  it('evaluates expiration and revocation states correctly', async () => {
    const repository = new InMemoryConsentRepository();
    const ledger = new ConsentLedger(repository);

    // 1. Expired consent
    await ledger.grantConsent({
      userId: 'usr_expiration_test',
      scope: 'screen_awareness:capture',
      policyVersion: '1.1.0',
      policyDigest: computeSha256('policy'),
      provenance: dummyProvenance,
      expiresInMs: -1000, // expired 1s ago
    });

    const expiredEval = await ledger.evaluateScope('usr_expiration_test', 'screen_awareness:capture');
    expect(expiredEval.hasAccess).toBe(false);
    expect(expiredEval.status).toBe('EXPIRED');

    // 2. Revoked consent
    await ledger.grantConsent({
      userId: 'usr_revocation_test',
      scope: 'environmental_audio:mic',
      policyVersion: '1.1.0',
      policyDigest: computeSha256('policy'),
      provenance: dummyProvenance,
    });

    const revokedRecord = await ledger.revokeConsent({
      userId: 'usr_revocation_test',
      scope: 'environmental_audio:mic',
      deviceId: 'android_pixel_8_pro_001',
      reason: 'User turned off microphone switch in Quick Settings',
    });

    expect(revokedRecord.status).toBe('REVOKED');
    const revokedEval = await ledger.evaluateScope('usr_revocation_test', 'environmental_audio:mic');
    expect(revokedEval.hasAccess).toBe(false);
    expect(revokedEval.status).toBe('REVOKED');
  });

  it('triggers registered revocation listeners immediately upon revocation', async () => {
    const repository = new InMemoryConsentRepository();
    const ledger = new ConsentLedger(repository);

    const screenCaptureListener = vi.fn();
    const globalListener = vi.fn();

    ledger.onRevoke('screen_awareness:capture', screenCaptureListener);
    ledger.onRevoke('*', globalListener);

    await ledger.grantConsent({
      userId: 'usr_event_test',
      scope: 'screen_awareness:capture',
      policyVersion: '1.1.0',
      policyDigest: computeSha256('policy'),
      provenance: dummyProvenance,
    });

    await ledger.revokeConsent({
      userId: 'usr_event_test',
      scope: 'screen_awareness:capture',
      deviceId: 'android_pixel_8_pro_001',
      reason: 'User tapped instant stop in Awareness Panel',
    });

    expect(screenCaptureListener).toHaveBeenCalledTimes(1);
    expect(screenCaptureListener).toHaveBeenCalledWith(
      expect.objectContaining({
        userId: 'usr_event_test',
        scope: 'screen_awareness:capture',
        reason: 'User tapped instant stop in Awareness Panel',
      })
    );

    expect(globalListener).toHaveBeenCalledTimes(1);
  });
});
