import { test, describe } from 'vitest';
import assert from 'node:assert/strict';
import { ProactiveScoringEngine } from '../../dist/proactive/index.js';
import type {
  ProactiveCandidate,
  UserContext,
  ProfileProactiveSettings,
  QuietHoursConfig,
} from '../../dist/proactive/index.js';

function createMockSettings(overrides?: Partial<ProfileProactiveSettings>): ProfileProactiveSettings {
  const quietHours: QuietHoursConfig = {
    enabled: true,
    startHour: 22, // 10 PM
    startMinute: 0,
    endHour: 7, // 7 AM
    endMinute: 0,
    timezone: 'UTC',
    allowCriticalOverride: true,
    allowedCategoriesDuringQuietHours: ['emergency'],
  };

  return {
    profileId: 'profile_test_1',
    globalEnabled: true,
    enabledCategories: {
      calendar: true,
      reminder: true,
      briefing: true,
      communication: true,
      suggestion: true,
      system: true,
      emergency: true,
    },
    quietHours,
    deliveryThreshold: 0.25,
    maxNotificationsPerHour: 3,
    maxNotificationsPerDay: 10,
    initiativeLevel: 'balanced',
    personalityWarmth: 0.5,
    ...overrides,
  };
}

function createMockCandidate(overrides?: Partial<ProactiveCandidate>): ProactiveCandidate {
  return {
    id: 'cand_test_1',
    profileId: 'profile_test_1',
    category: 'reminder',
    title: 'Call Dad',
    body: 'Reminder to call Dad regarding dinner plans.',
    relevance: 0.9,
    confidence: 0.9,
    urgency: 0.8,
    priorityLevel: 'high',
    createdAt: new Date('2026-11-01T15:00:00Z'),
    ...overrides,
  };
}

function createMockContext(overrides?: Partial<UserContext>): UserContext {
  return {
    userState: 'idle',
    screenOn: true,
    audioPlaying: false,
    inCall: false,
    isDoNotDisturb: false,
    batteryLevel: 0.8,
    isCharging: false,
    currentTimestamp: new Date('2026-11-01T15:00:00Z'),
    timezone: 'UTC',
    ...overrides,
  };
}

test('Multi-factor score computation: Score = (Relevance * Confidence * Urgency) - InterruptionCost', () => {
  const engine = new ProactiveScoringEngine();
  const settings = createMockSettings();
  const candidate = createMockCandidate({
    relevance: 0.8,
    confidence: 0.9,
    urgency: 0.7,
  });
  // idle context has base interruption cost 0.15
  const context = createMockContext({ userState: 'idle' });

  const decision = engine.evaluateCandidate(candidate, context, settings);

  // Raw score = (0.8 * 0.9 * 0.7) - 0.15 = 0.504 - 0.15 = 0.354
  assert.equal(decision.shouldDeliver, true);
  assert.equal(decision.reason, 'threshold_passed');
  assert.ok(Math.abs(decision.scoreBreakdown.rawScore - 0.354) < 0.001);
  assert.ok(Math.abs(decision.scoreBreakdown.finalScore - 0.354) < 0.001);
  assert.equal(decision.scoreBreakdown.interruptionCost, 0.15);
});

test('Dynamic user state evaluation impacts InterruptionCost and delivery', () => {
  const engine = new ProactiveScoringEngine();
  const settings = createMockSettings({ deliveryThreshold: 0.20 });

  const candidate = createMockCandidate({
    relevance: 0.7,
    confidence: 0.8,
    urgency: 0.5,
  });
  // Product = 0.7 * 0.8 * 0.5 = 0.280

  // 1. Idle: cost 0.15 -> Score = 0.336 - 0.15 = 0.186 (Threshold 0.20 -> rejected)
  const idleContext = createMockContext({ userState: 'idle' });
  const idleDecision = engine.evaluateCandidate(candidate, idleContext, settings);
  assert.equal(idleDecision.shouldDeliver, false);
  assert.equal(idleDecision.reason, 'threshold_not_met');

  // If candidate is higher urgency (0.9), product = 0.7 * 0.8 * 0.9 = 0.504
  const urgentCandidate = createMockCandidate({
    relevance: 0.7,
    confidence: 0.8,
    urgency: 0.9,
  });
  const idleUrgentDecision = engine.evaluateCandidate(urgentCandidate, idleContext, settings);
  // Score = 0.504 - 0.15 = 0.354 >= 0.20 -> delivered
  assert.equal(idleUrgentDecision.shouldDeliver, true);
  assert.equal(idleUrgentDecision.reason, 'threshold_passed');

  // 2. In Meeting: base cost 0.85 -> InterruptionCost >= 0.85
  const meetingContext = createMockContext({ userState: 'in_meeting' });
  const meetingDecision = engine.evaluateCandidate(urgentCandidate, meetingContext, settings);
  assert.equal(meetingDecision.shouldDeliver, false);
  assert.equal(meetingDecision.reason, 'threshold_not_met');
  assert.ok(meetingDecision.scoreBreakdown.interruptionCost >= 0.85);

  // 3. Driving: base cost 0.90 -> blocks standard notifications
  const drivingContext = createMockContext({ userState: 'driving' });
  const drivingDecision = engine.evaluateCandidate(urgentCandidate, drivingContext, settings);
  assert.equal(drivingDecision.shouldDeliver, false);
  assert.ok(drivingDecision.scoreBreakdown.interruptionCost >= 0.90);

  // 4. In call: adds 0.35 modifier
  const inCallContext = createMockContext({ userState: 'active', inCall: true });
  const inCallDecision = engine.evaluateCandidate(urgentCandidate, inCallContext, settings);
  assert.equal(inCallDecision.shouldDeliver, false);
  assert.ok(inCallDecision.scoreBreakdown.interruptionCost >= 0.70);
});

test('Quiet hours logic: enforces overnight window (10 PM to 7 AM) and defers delivery', () => {
  const engine = new ProactiveScoringEngine();
  const settings = createMockSettings();

  // Test during quiet hours: 11:30 PM (23:30)
  const quietHoursContext = createMockContext({
    currentTimestamp: new Date('2026-11-01T23:30:00Z'),
    timezone: 'UTC',
  });
  const candidate = createMockCandidate();

  const decision = engine.evaluateCandidate(candidate, quietHoursContext, settings);
  assert.equal(decision.shouldDeliver, false);
  assert.equal(decision.reason, 'quiet_hours_active');
  assert.ok(decision.deferredUntil !== undefined);

  // Expected deferred time is 7:00 AM on next day (2026-11-02T07:00:00Z)
  const deferredIso = decision.deferredUntil.toISOString();
  assert.ok(deferredIso.includes('2026-11-02T07:00:00.000Z'));
});

test('Quiet hours logic: allows critical emergency alerts to override', () => {
  const engine = new ProactiveScoringEngine();
  const settings = createMockSettings();

  const quietHoursContext = createMockContext({
    currentTimestamp: new Date('2026-11-01T23:30:00Z'),
    timezone: 'UTC',
  });

  const emergencyCandidate = createMockCandidate({
    category: 'emergency',
    priorityLevel: 'emergency',
    urgency: 1.0,
    relevance: 1.0,
    confidence: 1.0,
  });

  const decision = engine.evaluateCandidate(emergencyCandidate, quietHoursContext, settings);
  assert.equal(decision.shouldDeliver, true);
  assert.equal(decision.reason, 'emergency_override');
});

test('Anti-fatigue throttler: applies exponential backoff on user dismissals', () => {
  const engine = new ProactiveScoringEngine({
    baseCooldownSeconds: 900, // 15 min
    backoffFactor: 2.0,
  });
  const settings = createMockSettings({ deliveryThreshold: 0.10 });
  const candidate = createMockCandidate({
    relevance: 0.9,
    confidence: 0.9,
    urgency: 0.9,
  });

  // Check exponential backoff durations
  assert.equal(engine.calculateCooldownSeconds(0), 0);
  assert.equal(engine.calculateCooldownSeconds(1), 900); // 15m
  assert.equal(engine.calculateCooldownSeconds(2), 1800); // 30m
  assert.equal(engine.calculateCooldownSeconds(3), 3600); // 60m
  assert.equal(engine.calculateCooldownSeconds(4), 7200); // 120m

  const t0 = new Date('2026-11-01T14:00:00Z');
  // First dismissal at 14:00
  engine.recordFeedback({
    notificationId: 'cand_1',
    profileId: 'profile_test_1',
    category: 'reminder',
    actionTaken: 'dismiss',
    timestamp: t0,
  });

  // Candidate evaluated 5 minutes later (14:05) -> should be in 15m cooldown
  const t1 = new Date('2026-11-01T14:05:00Z');
  const contextT1 = createMockContext({ currentTimestamp: t1 });
  const decisionT1 = engine.evaluateCandidate(candidate, contextT1, settings);

  assert.equal(decisionT1.shouldDeliver, false);
  assert.equal(decisionT1.reason, 'fatigue_cooldown');
  assert.ok(decisionT1.deferredUntil !== undefined);
  assert.equal(decisionT1.deferredUntil.toISOString(), '2026-11-01T14:15:00.000Z');

  // Candidate evaluated 20 minutes later (14:20) -> cooldown expired!
  const t2 = new Date('2026-11-01T14:20:00Z');
  const contextT2 = createMockContext({ currentTimestamp: t2 });
  const decisionT2 = engine.evaluateCandidate(candidate, contextT2, settings);

  assert.equal(decisionT2.shouldDeliver, true);
  assert.equal(decisionT2.reason, 'threshold_passed');
});

test('Anti-fatigue throttler: user engagement immediately resets dismissal backoff', () => {
  const engine = new ProactiveScoringEngine();
  const settings = createMockSettings();
  const candidate = createMockCandidate();

  const t0 = new Date('2026-11-01T14:00:00Z');
  // Dismissal #1
  engine.recordFeedback({
    notificationId: 'cand_1',
    profileId: 'profile_test_1',
    category: 'reminder',
    actionTaken: 'dismiss',
    timestamp: t0,
  });

  // User engages: clicks / views details
  const t1 = new Date('2026-11-01T14:02:00Z');
  engine.recordFeedback({
    notificationId: 'cand_2',
    profileId: 'profile_test_1',
    category: 'reminder',
    actionTaken: 'view_details',
    timestamp: t1,
  });

  // Evaluate at 14:03 -> fatigue cooldown has been reset!
  const contextT2 = createMockContext({ currentTimestamp: new Date('2026-11-01T14:03:00Z') });
  const decision = engine.evaluateCandidate(candidate, contextT2, settings);
  assert.equal(decision.shouldDeliver, true);
  assert.equal(decision.reason, 'threshold_passed');
});

test('Sliding window frequency cap enforces hourly rate limit', () => {
  const engine = new ProactiveScoringEngine();
  const settings = createMockSettings({ maxNotificationsPerHour: 2 });
  const candidate = createMockCandidate();
  const now = new Date('2026-11-01T15:00:00Z');

  // Simulate 2 deliveries in past 30 minutes
  engine.recordDelivery('profile_test_1', 'reminder', new Date('2026-11-01T14:30:00Z'));
  engine.recordDelivery('profile_test_1', 'reminder', new Date('2026-11-01T14:45:00Z'));

  const context = createMockContext({ currentTimestamp: now });
  const decision = engine.evaluateCandidate(candidate, context, settings);

  assert.equal(decision.shouldDeliver, false);
  assert.equal(decision.reason, 'rate_limited');
});

test('Profile isolation: dismissals on Profile A do not penalize Profile B', () => {
  const engine = new ProactiveScoringEngine();
  const settingsA = createMockSettings({ profileId: 'profile_A' });
  const settingsB = createMockSettings({ profileId: 'profile_B' });

  const candidateA = createMockCandidate({ profileId: 'profile_A' });
  const candidateB = createMockCandidate({ profileId: 'profile_B' });

  const t0 = new Date('2026-11-01T14:00:00Z');
  // Profile A dismisses
  engine.recordFeedback({
    notificationId: 'n1',
    profileId: 'profile_A',
    category: 'reminder',
    actionTaken: 'dismiss',
    timestamp: t0,
  });

  const t1 = new Date('2026-11-01T14:05:00Z');
  const context = createMockContext({ currentTimestamp: t1 });

  // Profile A is on cooldown
  const decisionA = engine.evaluateCandidate(candidateA, context, settingsA);
  assert.equal(decisionA.shouldDeliver, false);
  assert.equal(decisionA.reason, 'fatigue_cooldown');

  // Profile B is unaffected and passes!
  const decisionB = engine.evaluateCandidate(candidateB, context, settingsB);
  assert.equal(decisionB.shouldDeliver, true);
  assert.equal(decisionB.reason, 'threshold_passed');
});
