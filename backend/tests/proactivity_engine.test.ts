import { describe, it, expect, beforeEach } from 'vitest';
import { ProactivityEngine } from '../src/proactive/proactivity_engine.js';
import { ProactiveCandidateTrigger } from '../src/types/proactive.js';

describe('ProactivityEngine & Assistance Optimization', () => {
  let engine: ProactivityEngine;

  beforeEach(() => {
    engine = new ProactivityEngine();
  });

  describe('Mathematical Scoring Formula', () => {
    it('should compute exact formula: Score = (Relevance * Confidence * Urgency) - InterruptionCost', () => {
      // Relevance=0.9, Confidence=0.9, Urgency=0.8, InterruptionCost=0.1
      // (0.9 * 0.9 * 0.8) - 0.1 = 0.648 - 0.1 = 0.548
      const breakdown = engine.computeScore(
        {
          relevance: 0.9,
          confidence: 0.9,
          urgency: 0.8,
          interruptionCost: 0.1,
        },
        0.35
      );

      expect(breakdown.rawScore).toBe(0.548);
      expect(breakdown.passesThreshold).toBe(true);

      // Candidate with high interruption cost (e.g. user driving or in meeting)
      // (0.8 * 0.7 * 0.6) - 0.8 = 0.336 - 0.8 = -0.464
      const busyBreakdown = engine.computeScore(
        {
          relevance: 0.8,
          confidence: 0.7,
          urgency: 0.6,
          interruptionCost: 0.8,
        },
        0.35
      );

      expect(busyBreakdown.rawScore).toBe(-0.464);
      expect(busyBreakdown.passesThreshold).toBe(false);
    });

    it('should suppress candidate when score is below threshold', () => {
      const trigger: ProactiveCandidateTrigger = {
        candidateId: 'cand_low',
        profileId: 'prof_low',
        userId: 'user_1',
        category: 'task_suggestion',
        title: 'Organize desktop files',
        body: 'You have some files on your desktop.',
        relevance: 0.4,
        confidence: 0.5,
        urgency: 0.2,
        interruptionCost: 0.3,
        evidenceCitations: [],
      };

      // Disable quiet hours for clean score test
      engine.setProfileSettings({
        profileId: 'prof_low',
        enabled: true,
        minScoreThreshold: 0.35,
        maxNotificationsPerHour: 3,
        maxNotificationsPerDay: 10,
        quietHours: { enabled: false, startTime: '22:00', endTime: '07:00', timezone: 'UTC' },
      });

      const result = engine.evaluateCandidate(trigger);
      expect(result.status).toBe('SUPPRESSED_SCORE_TOO_LOW');
      expect(result.score.passesThreshold).toBe(false);
      expect(result.dispatchedNotification).toBeUndefined();
    });
  });

  describe('Quiet Hours Enforcement', () => {
    it('should suppress non-emergency notifications during configured overnight quiet hours', () => {
      const trigger: ProactiveCandidateTrigger = {
        candidateId: 'cand_night',
        profileId: 'prof_night',
        userId: 'user_1',
        category: 'reminder',
        title: 'Review weekly summary',
        body: 'Your weekly recap is ready.',
        relevance: 0.95,
        confidence: 0.95,
        urgency: 0.9,
        interruptionCost: 0.05,
        evidenceCitations: [],
      };

      engine.setProfileSettings({
        profileId: 'prof_night',
        enabled: true,
        minScoreThreshold: 0.35,
        maxNotificationsPerHour: 3,
        maxNotificationsPerDay: 10,
        quietHours: {
          enabled: true,
          startTime: '22:00',
          endTime: '07:00',
          timezone: 'UTC',
        },
      });

      // 23:30 UTC -> inside quiet hours
      const nightTimestamp = new Date('2026-11-01T23:30:00Z').getTime();
      const nightResult = engine.evaluateCandidate(trigger, nightTimestamp);
      expect(nightResult.status).toBe('SUPPRESSED_QUIET_HOURS');
      expect(nightResult.suppressionReason).toContain('Quiet hours active');

      // 14:00 UTC -> daytime, outside quiet hours
      const dayTimestamp = new Date('2026-11-01T14:00:00Z').getTime();
      const dayResult = engine.evaluateCandidate(trigger, dayTimestamp);
      expect(dayResult.status).toBe('DISPATCHED');
    });
  });

  describe('Notification Fatigue Sliding-Window Limiter', () => {
    it('should suppress notifications once hourly limit is reached', () => {
      const profileId = 'prof_fatigue';
      engine.setProfileSettings({
        profileId,
        enabled: true,
        minScoreThreshold: 0.3,
        maxNotificationsPerHour: 2, // Limit: 2 per hour
        maxNotificationsPerDay: 10,
        quietHours: { enabled: false, startTime: '22:00', endTime: '07:00', timezone: 'UTC' },
      });

      const makeTrigger = (id: string): ProactiveCandidateTrigger => ({
        candidateId: id,
        profileId,
        userId: 'user_fatigue',
        category: 'reminder',
        title: `Reminder ${id}`,
        body: 'High value reminder',
        relevance: 0.9,
        confidence: 0.9,
        urgency: 0.9,
        interruptionCost: 0.1,
        evidenceCitations: [],
      });

      const now = new Date('2026-11-01T12:00:00Z').getTime();

      const r1 = engine.evaluateCandidate(makeTrigger('c1'), now);
      expect(r1.status).toBe('DISPATCHED');

      const r2 = engine.evaluateCandidate(makeTrigger('c2'), now + 10_000);
      expect(r2.status).toBe('DISPATCHED');

      // 3rd attempt within the same hour exceeds maxNotificationsPerHour
      const r3 = engine.evaluateCandidate(makeTrigger('c3'), now + 20_000);
      expect(r3.status).toBe('SUPPRESSED_FATIGUE_LIMIT');
      expect(r3.suppressionReason).toContain('Fatigue limit: Exceeded 2 notifications');
    });
  });

  describe('Snooze Windows', () => {
    it('should suppress notifications when profile has an active snooze window', () => {
      const profileId = 'prof_snooze';
      const now = Date.now();
      const snoozeUntil = new Date(now + 30 * 60_000).toISOString(); // Snooze for 30 min

      engine.setProfileSettings({
        profileId,
        enabled: true,
        minScoreThreshold: 0.3,
        maxNotificationsPerHour: 5,
        maxNotificationsPerDay: 10,
        quietHours: { enabled: false, startTime: '22:00', endTime: '07:00', timezone: 'UTC' },
        snoozeUntil,
      });

      const trigger: ProactiveCandidateTrigger = {
        candidateId: 'c_snooze',
        profileId,
        userId: 'user_snooze',
        category: 'task_suggestion',
        title: 'Task suggestion',
        body: 'Suggestion body',
        relevance: 0.9,
        confidence: 0.9,
        urgency: 0.9,
        interruptionCost: 0.1,
        evidenceCitations: [],
      };

      const result = engine.evaluateCandidate(trigger, now + 5000);
      expect(result.status).toBe('SUPPRESSED_SNOOZED');
      expect(result.suppressionReason).toContain('Proactive suggestions snoozed');
    });
  });

  describe('Evidence Citations Invariant', () => {
    it('should link every dispatched proactive notification to verifiable source evidence citations', () => {
      const profileId = 'prof_cite';
      engine.setProfileSettings({
        profileId,
        enabled: true,
        minScoreThreshold: 0.3,
        maxNotificationsPerHour: 5,
        maxNotificationsPerDay: 10,
        quietHours: { enabled: false, startTime: '22:00', endTime: '07:00', timezone: 'UTC' },
      });

      const trigger: ProactiveCandidateTrigger = {
        candidateId: 'c_cite',
        profileId,
        userId: 'user_cite',
        category: 'reminder',
        title: 'Call Dad at 7:30 PM',
        body: 'You have a scheduled call with Dad.',
        relevance: 0.9,
        confidence: 0.95,
        urgency: 0.85,
        interruptionCost: 0.1,
        evidenceCitations: [
          {
            citationId: 'cite_cal_1',
            sourceType: 'calendar_event',
            sourceId: 'event_dad_call',
            timestamp: new Date().toISOString(),
            headline: 'Calendar Event: Call Dad',
            snippet: 'Scheduled for 7:30 PM Today',
            confidenceScore: 0.98,
          },
        ],
      };

      const result = engine.evaluateCandidate(trigger);
      expect(result.status).toBe('DISPATCHED');
      expect(result.dispatchedNotification).toBeDefined();
      expect(result.dispatchedNotification?.citations.length).toBe(1);
      expect(result.dispatchedNotification?.citations[0]?.sourceType).toBe('calendar_event');
      expect(result.dispatchedNotification?.citations[0]?.sourceId).toBe('event_dad_call');
      expect(result.dispatchedNotification?.citations[0]?.snippet).toContain('Scheduled for 7:30 PM');
    });
  });
});
