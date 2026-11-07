import { describe, it, expect } from 'vitest';
import {
  CascadeDeletionWorker,
  InMemoryDataStoreProvider,
  InMemoryStorageBucketProvider,
  InMemoryDeletionCertificateStore,
} from '../../src/privacy/cascade_deletion_worker.js';

describe('CascadeDeletionWorker Unit & Integration Tests', () => {
  it('performs complete cascade deletion across all tables and storage buckets for full account', async () => {
    const datastore = new InMemoryDataStoreProvider();
    const storage = new InMemoryStorageBucketProvider();
    const certStore = new InMemoryDeletionCertificateStore();

    const worker = new CascadeDeletionWorker(datastore, storage, certStore);

    const userId = 'usr_erasure_target_999';

    // Populate datastore
    datastore.users.push({ id: userId, email: 'erasure@example.com' });
    datastore.companionProfiles.push(
      { id: 'prof_aster', userId },
      { id: 'prof_nova', userId }
    );
    datastore.memories.push(
      { id: 'mem_1', userId, profileId: 'prof_aster' },
      { id: 'mem_2', userId, profileId: 'prof_nova' }
    );
    datastore.chatMessages.push(
      { id: 'msg_1', userId, profileId: 'prof_aster' },
      { id: 'msg_2', userId, profileId: 'prof_nova' }
    );
    datastore.events.push(
      { id: 'evt_1', userId, profileId: 'prof_aster' }
    );
    datastore.actions.push(
      { id: 'act_1', userId, profileId: 'prof_aster' }
    );
    datastore.voiceModels.push(
      { id: 'vm_1', userId, profileId: 'prof_aster' }
    );
    datastore.sessions.push(
      { id: 'sess_1', userId, profileId: 'prof_aster' }
    );
    datastore.integrationTokens.push(
      { id: 'tok_1', userId, profileId: 'prof_aster' }
    );
    datastore.consentRecords.push(
      { id: 'cons_1', userId, profileId: 'prof_aster', isTombstoned: false }
    );

    // Populate storage buckets
    await storage.putObject('media-chunks', `users/${userId}/chunks/chunk_001.bin`);
    await storage.putObject('voice-samples', `users/${userId}/samples/voice_raw.wav`);
    await storage.putObject('visual-frames', `users/${userId}/frames/frame_001.jpg`);
    await storage.putObject('attachments', `users/${userId}/attachments/doc.pdf`);
    await storage.putObject('attachments', `${userId}/direct_attachment.png`);

    // Execute deletion
    const result = await worker.executeCascadeDeletion({
      userId,
      scope: 'FULL_ACCOUNT',
      requestedBy: 'USER',
      reason: 'GDPR Article 17 Erasure request submitted via app settings',
    });

    expect(result.success).toBe(true);
    expect(result.certificate).toBeDefined();

    // Verify datastore is completely purged
    expect(datastore.users.length).toBe(0);
    expect(datastore.companionProfiles.length).toBe(0);
    expect(datastore.memories.length).toBe(0);
    expect(datastore.chatMessages.length).toBe(0);
    expect(datastore.events.length).toBe(0);
    expect(datastore.actions.length).toBe(0);
    expect(datastore.voiceModels.length).toBe(0);
    expect(datastore.sessions.length).toBe(0);
    expect(datastore.integrationTokens.length).toBe(0);
    expect(datastore.consentRecords[0]?.isTombstoned).toBe(true);

    // Verify storage buckets are clean
    for (const b of ['media-chunks', 'voice-samples', 'visual-frames', 'attachments']) {
      const remaining = await storage.listObjectsByPrefix(b, `users/${userId}`);
      expect(remaining.length).toBe(0);
    }

    // Verify certificate details and cryptographic signature
    const cert = result.certificate;
    expect(cert.purgedCounts.profiles).toBe(2);
    expect(cert.purgedCounts.memories).toBe(2);
    expect(cert.purgedCounts.chatMessages).toBe(2);
    expect(cert.purgedCounts.storageObjectsRemoved).toBe(5);
    expect(cert.deletionScope).toBe('FULL_ACCOUNT');

    // Cryptographic verification of certificate
    const isValidSignature = worker.verifyCertificateSignature(cert);
    expect(isValidSignature).toBe(true);

    // Verify certificate was persisted in store
    const storedCert = await certStore.getCertificate(cert.certificateId);
    expect(storedCert).not.toBeNull();
  });

  it('supports single profile deletion while isolating other profile data', async () => {
    const datastore = new InMemoryDataStoreProvider();
    const storage = new InMemoryStorageBucketProvider();
    const certStore = new InMemoryDeletionCertificateStore();

    const worker = new CascadeDeletionWorker(datastore, storage, certStore);

    const userId = 'usr_multi_profile_123';

    // Account has Profile A (Aster) and Profile B (Nova)
    datastore.users.push({ id: userId, email: 'multi@example.com' });
    datastore.companionProfiles.push(
      { id: 'prof_aster', userId },
      { id: 'prof_nova', userId }
    );
    datastore.memories.push(
      { id: 'mem_aster_1', userId, profileId: 'prof_aster' },
      { id: 'mem_nova_1', userId, profileId: 'prof_nova' }
    );
    datastore.chatMessages.push(
      { id: 'msg_aster_1', userId, profileId: 'prof_aster' },
      { id: 'msg_nova_1', userId, profileId: 'prof_nova' }
    );

    await storage.putObject('visual-frames', `users/${userId}/profiles/prof_nova/frame1.jpg`);
    await storage.putObject('visual-frames', `users/${userId}/profiles/prof_aster/frame1.jpg`);

    // Purge only Profile B (Nova)
    const result = await worker.executeCascadeDeletion({
      userId,
      profileId: 'prof_nova',
      scope: 'COMPANION_PROFILE_ONLY',
      requestedBy: 'USER',
      reason: 'User decided to reset Nova companion profile',
    });

    expect(result.success).toBe(true);

    // Profile A must remain intact
    expect(datastore.users.length).toBe(1);
    expect(datastore.companionProfiles.map((p) => p.id)).toEqual(['prof_aster']);
    expect(datastore.memories.map((m) => m.id)).toEqual(['mem_aster_1']);
    expect(datastore.chatMessages.map((c) => c.id)).toEqual(['msg_aster_1']);

    // Only Nova storage frame was removed
    const asterFrames = await storage.listObjectsByPrefix(
      'visual-frames',
      `users/${userId}/profiles/prof_aster/`
    );
    expect(asterFrames.length).toBe(1);

    const novaFrames = await storage.listObjectsByPrefix(
      'visual-frames',
      `users/${userId}/profiles/prof_nova/`
    );
    expect(novaFrames.length).toBe(0);
  });
});
