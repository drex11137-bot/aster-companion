import { test, describe } from 'vitest';
import assert from 'node:assert/strict';
import * as crypto from 'node:crypto';
import {
  FcmV1Dispatcher,
  ApnsHttp2Dispatcher,
  UnifiedNotificationDispatcher,
  DEFAULT_PROACTIVE_ACTIONS,
} from '../../dist/proactive/index.js';
import type {
  ProactiveCandidate,
  DeviceRegistration,
  ScoringDecision,
} from '../../dist/proactive/index.js';

// Generate dynamic RSA and EC keys for real cryptographic testing
const rsaKeyPair = crypto.generateKeyPairSync('rsa', {
  modulusLength: 2048,
  publicKeyEncoding: { type: 'spki', format: 'pem' },
  privateKeyEncoding: { type: 'pkcs8', format: 'pem' },
});

const ecKeyPair = crypto.generateKeyPairSync('ec', {
  namedCurve: 'prime256v1', // P-256
  publicKeyEncoding: { type: 'spki', format: 'pem' },
  privateKeyEncoding: { type: 'pkcs8', format: 'pem' },
});

function createMockCandidate(overrides?: Partial<ProactiveCandidate>): ProactiveCandidate {
  return {
    id: 'cand_test_disp',
    profileId: 'profile_test_1',
    category: 'reminder',
    title: 'Time for team standup',
    body: 'Daily engineering sync begins in 5 minutes.',
    relevance: 0.9,
    confidence: 0.95,
    urgency: 0.85,
    citation: {
      sourceMemoryId: 'mem_sync_123',
      screenEventTimestamp: '2026-11-01T15:00:00Z',
      sourceType: 'calendar',
      snippet: 'Calendar event: Daily Engineering Sync',
      confidenceScore: 0.98,
    },
    createdAt: new Date('2026-11-01T15:00:00Z'),
    ...overrides,
  };
}

test('FcmV1Dispatcher: builds valid FCM v1 payload with Android config, citations, and actions', () => {
  const dispatcher = new FcmV1Dispatcher({
    projectId: 'aster-companion-prod',
    clientEmail: 'fcm-service@aster-companion-prod.iam.gserviceaccount.com',
    privateKey: rsaKeyPair.privateKey,
  });

  const candidate = createMockCandidate();
  const rawPayload = dispatcher.buildPayload(candidate, 'android_device_token_xyz', 0.65) as {
    message: {
      token: string;
      notification: { title: string; body: string };
      android: { priority: string; notification: { channel_id: string; tag: string } };
      data: Record<string, string>;
    };
  };

  const { message } = rawPayload;
  assert.equal(message.token, 'android_device_token_xyz');
  assert.equal(message.notification.title, 'Time for team standup');
  assert.equal(message.notification.body, 'Daily engineering sync begins in 5 minutes.');
  assert.equal(message.android.priority, 'HIGH');
  assert.equal(message.android.notification.channel_id, 'aster_proactive');
  assert.equal(message.android.notification.tag, 'aster_reminder_profile_test_1');

  // Verify citation linkage in data payload
  assert.equal(message.data.source_memory_id, 'mem_sync_123');
  assert.equal(message.data.screen_event_timestamp, '2026-11-01T15:00:00Z');
  assert.equal(message.data.citation_type, 'calendar');
  assert.equal(message.data.citation_snippet, 'Calendar event: Daily Engineering Sync');
  assert.equal(message.data.citation_confidence, '0.98');
  assert.equal(message.data.score, '0.650');

  // Verify rich interactive actions
  const actions = JSON.parse(message.data.actions);
  assert.equal(actions.length, 3);
  assert.equal(actions[0].id, 'snooze_15m');
  assert.equal(actions[1].id, 'view_details');
  assert.equal(actions[2].id, 'dismiss');
});

test('FcmV1Dispatcher: dispatches Android notification with OAuth token exchange and handles success', async () => {
  let fcmRequestCalled = false;
  let sentBody: Record<string, unknown> | undefined;

  const dispatcher = new FcmV1Dispatcher({
    projectId: 'aster-companion-test',
    clientEmail: 'fcm@aster.iam.gserviceaccount.com',
    privateKey: rsaKeyPair.privateKey,
    accessTokenProvider: async () => 'mock_google_oauth2_token_abc',
    customTransport: async (url, options) => {
      fcmRequestCalled = true;
      sentBody = JSON.parse(options.body);
      assert.ok(options.headers.Authorization === 'Bearer mock_google_oauth2_token_abc');
      return {
        status: 200,
        body: JSON.stringify({ name: 'projects/aster-companion-test/messages/msg_98765' }),
      };
    },
  });

  const candidate = createMockCandidate();
  const result = await dispatcher.dispatch(candidate, 'android_token_123', 0.72);

  assert.equal(fcmRequestCalled, true);
  assert.equal(result.success, true);
  assert.equal(result.platform, 'android');
  assert.equal(result.messageId, 'projects/aster-companion-test/messages/msg_98765');
  assert.equal(result.statusCode, 200);
  assert.ok(sentBody !== undefined);
});

test('FcmV1Dispatcher: detects UNREGISTERED device and signals unregistration flag', async () => {
  const dispatcher = new FcmV1Dispatcher({
    projectId: 'aster-companion-test',
    clientEmail: 'fcm@aster.iam.gserviceaccount.com',
    privateKey: rsaKeyPair.privateKey,
    accessTokenProvider: async () => 'mock_token',
    customTransport: async () => {
      return {
        status: 404,
        body: JSON.stringify({
          error: {
            code: 404,
            message: 'Requested entity was not found.',
            status: 'UNREGISTERED',
          },
        }),
      };
    },
  });

  const candidate = createMockCandidate();
  const result = await dispatcher.dispatch(candidate, 'stale_android_token', 0.5);

  assert.equal(result.success, false);
  assert.equal(result.shouldUnregisterToken, true);
  assert.equal(result.statusCode, 404);
});

test('ApnsHttp2Dispatcher: builds valid APNs payload with aps alert, category, and aster payload', () => {
  const dispatcher = new ApnsHttp2Dispatcher({
    keyId: 'ABC1234XYZ',
    teamId: 'TEAM987654',
    bundleId: 'com.aster.companion',
    privateKey: ecKeyPair.privateKey,
  });

  const candidate = createMockCandidate();
  const rawPayload = dispatcher.buildPayload(candidate, 0.75) as {
    aps: {
      alert: { title: string; body: string };
      category: string;
      sound: string;
      badge: number;
    };
    aster: {
      notification_id: string;
      profile_id: string;
      category: string;
      score: number;
      citation: { source_memory_id: string; citation_type?: string; source_type?: string };
      actions: typeof DEFAULT_PROACTIVE_ACTIONS;
    };
  };

  assert.equal(rawPayload.aps.alert.title, 'Time for team standup');
  assert.equal(rawPayload.aps.alert.body, 'Daily engineering sync begins in 5 minutes.');
  assert.equal(rawPayload.aps.category, 'ASTER_ACTIONABLE_PROACTIVE');
  assert.equal(rawPayload.aps.sound, 'default');
  assert.equal(rawPayload.aps.badge, 1);

  assert.equal(rawPayload.aster.notification_id, 'cand_test_disp');
  assert.equal(rawPayload.aster.profile_id, 'profile_test_1');
  assert.equal(rawPayload.aster.score, 0.75);
  assert.equal(rawPayload.aster.citation.source_memory_id, 'mem_sync_123');
  assert.equal(rawPayload.aster.citation.source_type, 'calendar');
  assert.equal(rawPayload.aster.actions.length, 3);
  assert.equal(rawPayload.aster.actions[0].id, 'snooze_15m');
});

test('ApnsHttp2Dispatcher: signs ES256 JWT using p8 EC private key and dispatches successfully', async () => {
  let apnsHostCalled = '';
  let apnsPathCalled = '';
  let apnsHeaders: Record<string, string> = {};

  const dispatcher = new ApnsHttp2Dispatcher({
    keyId: 'KID1234567',
    teamId: 'TEAM765432',
    bundleId: 'com.aster.companion',
    privateKey: ecKeyPair.privateKey,
    isProduction: true,
    customTransport: async (host, path, headers, body) => {
      apnsHostCalled = host;
      apnsPathCalled = path;
      apnsHeaders = headers;
      assert.ok(body.includes('Time for team standup'));
      return {
        status: 200,
        headers: { 'apns-id': 'apns-uuid-123456-7890' },
        body: '',
      };
    },
  });

  // Verify JWT minting
  const jwt = dispatcher.getOrMintApnsJwt();
  assert.ok(jwt.split('.').length === 3);

  const candidate = createMockCandidate();
  const result = await dispatcher.dispatch(candidate, 'ios_device_token_abc', 0.8);

  assert.equal(apnsHostCalled, 'api.push.apple.com');
  assert.equal(apnsPathCalled, '/3/device/ios_device_token_abc');
  assert.equal(apnsHeaders['apns-topic'], 'com.aster.companion');
  assert.equal(apnsHeaders['apns-priority'], '10');
  assert.ok(apnsHeaders.authorization.startsWith('bearer '));

  assert.equal(result.success, true);
  assert.equal(result.platform, 'ios');
  assert.equal(result.messageId, 'apns-uuid-123456-7890');
  assert.equal(result.statusCode, 200);
});

test('ApnsHttp2Dispatcher: handles 410 Unregistered and signals token cleanup', async () => {
  const dispatcher = new ApnsHttp2Dispatcher({
    keyId: 'KID1234567',
    teamId: 'TEAM765432',
    bundleId: 'com.aster.companion',
    privateKey: ecKeyPair.privateKey,
    customTransport: async () => {
      return {
        status: 410,
        headers: {},
        body: JSON.stringify({ reason: 'Unregistered' }),
      };
    },
  });

  const candidate = createMockCandidate();
  const result = await dispatcher.dispatch(candidate, 'uninstalled_device_token', 0.4);

  assert.equal(result.success, false);
  assert.equal(result.statusCode, 410);
  assert.equal(result.shouldUnregisterToken, true);
});

test('UnifiedNotificationDispatcher: coordinates delivery and respects scoring decision', async () => {
  const fcmDispatcher = new FcmV1Dispatcher({
    projectId: 'test-proj',
    clientEmail: 'fcm@test.iam.gserviceaccount.com',
    privateKey: rsaKeyPair.privateKey,
    accessTokenProvider: async () => 'token_123',
    customTransport: async () => ({
      status: 200,
      body: JSON.stringify({ name: 'projects/test-proj/messages/fcm_msg_1' }),
    }),
  });

  const apnsDispatcher = new ApnsHttp2Dispatcher({
    keyId: 'KID1234567',
    teamId: 'TEAM765432',
    bundleId: 'com.aster.companion',
    privateKey: ecKeyPair.privateKey,
    customTransport: async () => ({
      status: 200,
      headers: { 'apns-id': 'apns_msg_1' },
      body: '',
    }),
  });

  const unified = new UnifiedNotificationDispatcher({
    fcm: fcmDispatcher,
    apns: apnsDispatcher,
  });

  const devices: DeviceRegistration[] = [
    { deviceToken: 'tok_android_1', platform: 'android', profileId: 'profile_test_1' },
    { deviceToken: 'tok_ios_1', platform: 'ios', profileId: 'profile_test_1' },
  ];

  const candidate = createMockCandidate();

  // 1. Rejected decision: shouldDeliver = false -> dispatcher sends nothing
  const rejectedDecision: ScoringDecision = {
    candidateId: candidate.id,
    profileId: candidate.profileId,
    shouldDeliver: false,
    reason: 'threshold_not_met',
    scoreBreakdown: {
      relevance: 0.5,
      confidence: 0.5,
      urgency: 0.5,
      interruptionCost: 0.8,
      rawScore: -0.675,
      fatiguePenalty: 0,
      finalScore: -0.675,
    },
    evaluatedAt: new Date(),
  };

  const resultsRejected = await unified.dispatchCandidate(candidate, rejectedDecision, devices);
  assert.equal(resultsRejected.length, 0);

  // 2. Approved decision: shouldDeliver = true -> dispatches to both platforms
  const approvedDecision: ScoringDecision = {
    ...rejectedDecision,
    shouldDeliver: true,
    reason: 'threshold_passed',
    scoreBreakdown: {
      ...rejectedDecision.scoreBreakdown,
      finalScore: 0.65,
    },
  };

  const resultsApproved = await unified.dispatchCandidate(candidate, approvedDecision, devices);
  assert.equal(resultsApproved.length, 2);

  const androidResult = resultsApproved.find((r) => r.platform === 'android');
  assert.ok(androidResult !== undefined);
  assert.equal(androidResult.success, true);
  assert.equal(androidResult.messageId, 'projects/test-proj/messages/fcm_msg_1');

  const iosResult = resultsApproved.find((r) => r.platform === 'ios');
  assert.ok(iosResult !== undefined);
  assert.equal(iosResult.success, true);
  assert.equal(iosResult.messageId, 'apns_msg_1');
});
