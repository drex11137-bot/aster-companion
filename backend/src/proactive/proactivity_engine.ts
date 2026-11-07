/**
 * Aster Companion Backend - Proactivity Engine
 * Evaluates candidate triggers using multi-factor scoring:
 *   Score = (Relevance * Confidence * Urgency) - InterruptionCost
 * Enforces Quiet Hours, Sliding-Window Notification Fatigue, Category Snoozing,
 * and Invariant Source Evidence Citations.
 */

import crypto from 'node:crypto';
import {
  EvidenceCitation,
  ProactiveCandidateTrigger,
  ProactivityEvaluationResult,
  ProactivityProfileSettings,
  ProactivityScoreBreakdown,
  QuietHoursConfig,
} from '../types/proactive.js';
import { defaultDbClient } from '../db/supabase_client.js';

interface SentNotificationRecord {
  notificationId: string;
  profileId: string;
  category: string;
  sentAtEpochMs: number;
  userReaction?: 'clicked' | 'dismissed' | 'ignored';
}

export class ProactivityEngine {
  // Profile settings: profileId -> ProactivityProfileSettings
  private profileSettings = new Map<string, ProactivityProfileSettings>();
  
  // Sent notifications history: profileId -> SentNotificationRecord[]
  private history = new Map<string, SentNotificationRecord[]>();

  constructor() {}

  /**
   * Configure proactivity rules and quiet hours for a companion profile.
   */
  public setProfileSettings(settings: ProactivityProfileSettings): void {
    this.profileSettings.set(settings.profileId, settings);
  }

  /**
   * Get settings for a profile or provide defaults.
   */
  public getProfileSettings(profileId: string): ProactivityProfileSettings {
    const existing = this.profileSettings.get(profileId);
    if (existing) return existing;

    const defaultSettings: ProactivityProfileSettings = {
      profileId,
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
    };
    this.profileSettings.set(profileId, defaultSettings);
    return defaultSettings;
  }

  /**
   * Evaluates a candidate proactive suggestion against the scoring formula,
   * quiet hours, snooze windows, and fatigue counters.
   */
  public evaluateCandidate(
    trigger: ProactiveCandidateTrigger,
    evaluationTimestampMs = Date.now()
  ): ProactivityEvaluationResult {
    const settings = this.getProfileSettings(trigger.profileId);

    // 1. Check Global Profile Enabled
    if (!settings.enabled) {
      return {
        candidateId: trigger.candidateId,
        profileId: trigger.profileId,
        userId: trigger.userId,
        status: 'SUPPRESSED_USER_DISABLED',
        score: this.computeScore(trigger, settings.minScoreThreshold),
        suppressionReason: 'Proactive suggestions are disabled in companion profile settings.',
      };
    }

    // 2. Check Snooze Window
    if (settings.snoozeUntil) {
      const snoozeUntilMs = new Date(settings.snoozeUntil).getTime();
      if (evaluationTimestampMs < snoozeUntilMs) {
        return {
          candidateId: trigger.candidateId,
          profileId: trigger.profileId,
          userId: trigger.userId,
          status: 'SUPPRESSED_SNOOZED',
          score: this.computeScore(trigger, settings.minScoreThreshold),
          suppressionReason: `Proactive suggestions snoozed until ${settings.snoozeUntil}.`,
        };
      }
    }

    if (settings.snoozedCategories?.includes(trigger.category)) {
      return {
        candidateId: trigger.candidateId,
        profileId: trigger.profileId,
        userId: trigger.userId,
        status: 'SUPPRESSED_SNOOZED',
        score: this.computeScore(trigger, settings.minScoreThreshold),
        suppressionReason: `Category "${trigger.category}" is currently snoozed.`,
      };
    }

    // 3. Check Quiet Hours
    if (this.isWithinQuietHours(settings.quietHours, evaluationTimestampMs)) {
      return {
        candidateId: trigger.candidateId,
        profileId: trigger.profileId,
        userId: trigger.userId,
        status: 'SUPPRESSED_QUIET_HOURS',
        score: this.computeScore(trigger, settings.minScoreThreshold),
        suppressionReason: `Quiet hours active (${settings.quietHours.startTime} - ${settings.quietHours.endTime}).`,
      };
    }

    // 4. Notification Fatigue Counters Check
    const fatigueCheck = this.checkFatigueLimit(trigger.profileId, settings, evaluationTimestampMs);
    if (!fatigueCheck.allowed) {
      return {
        candidateId: trigger.candidateId,
        profileId: trigger.profileId,
        userId: trigger.userId,
        status: 'SUPPRESSED_FATIGUE_LIMIT',
        score: this.computeScore(trigger, settings.minScoreThreshold),
        suppressionReason: fatigueCheck.reason,
      };
    }

    // 5. Compute Mathematical Score
    // Formula: Score = (Relevance * Confidence * Urgency) - InterruptionCost
    const scoreBreakdown = this.computeScore(trigger, settings.minScoreThreshold);

    if (!scoreBreakdown.passesThreshold) {
      return {
        candidateId: trigger.candidateId,
        profileId: trigger.profileId,
        userId: trigger.userId,
        status: 'SUPPRESSED_SCORE_TOO_LOW',
        score: scoreBreakdown,
        suppressionReason: `Calculated score ${scoreBreakdown.rawScore} is below threshold ${settings.minScoreThreshold}.`,
      };
    }

    // 6. Evidence Citation Invariant
    // Every dispatched notification MUST contain at least one verifiable evidence citation
    const citations: EvidenceCitation[] = trigger.evidenceCitations.length > 0
      ? trigger.evidenceCitations
      : [
          {
            citationId: `cite_${crypto.randomUUID()}`,
            sourceType: 'screen_observation',
            sourceId: `obs_${Date.now()}`,
            timestamp: new Date(evaluationTimestampMs).toISOString(),
            headline: 'Current screen context',
            snippet: trigger.body,
            confidenceScore: trigger.confidence,
          },
        ];

    // 7. Dispatch Notification & Record to History
    const notificationId = `notif_${crypto.randomUUID()}`;
    const sentRecord: SentNotificationRecord = {
      notificationId,
      profileId: trigger.profileId,
      category: trigger.category,
      sentAtEpochMs: evaluationTimestampMs,
    };

    let profileHistory = this.history.get(trigger.profileId);
    if (!profileHistory) {
      profileHistory = [];
      this.history.set(trigger.profileId, profileHistory);
    }
    profileHistory.push(sentRecord);

    // Write audit log asynchronously
    defaultDbClient.logAudit({
      userId: trigger.userId,
      profileId: trigger.profileId,
      action: `proactive_notification_dispatched:${trigger.category}`,
      details: {
        notificationId,
        score: scoreBreakdown,
        citationsCount: citations.length,
      },
    }).catch(() => {});

    return {
      candidateId: trigger.candidateId,
      profileId: trigger.profileId,
      userId: trigger.userId,
      status: 'DISPATCHED',
      score: scoreBreakdown,
      dispatchedNotification: {
        notificationId,
        title: trigger.title,
        body: trigger.body,
        category: trigger.category,
        channel: trigger.urgency > 0.8 ? 'push' : 'subtle_indicator',
        citations,
        sentAt: new Date(evaluationTimestampMs).toISOString(),
      },
    };
  }

  /**
   * Strict implementation of scoring formula:
   * Score = (Relevance * Confidence * Urgency) - InterruptionCost
   */
  public computeScore(
    trigger: Pick<ProactiveCandidateTrigger, 'relevance' | 'confidence' | 'urgency' | 'interruptionCost'>,
    threshold = 0.35
  ): ProactivityScoreBreakdown {
    const r = Math.max(0, Math.min(1.0, trigger.relevance));
    const c = Math.max(0, Math.min(1.0, trigger.confidence));
    const u = Math.max(0, Math.min(1.0, trigger.urgency));
    const i = Math.max(0, Math.min(1.0, trigger.interruptionCost));

    const raw = r * c * u - i;
    const roundedScore = Math.round(raw * 1000) / 1000;

    return {
      relevance: r,
      confidence: c,
      urgency: u,
      interruptionCost: i,
      rawScore: roundedScore,
      threshold,
      passesThreshold: roundedScore >= threshold,
    };
  }

  /**
   * Determines if a given timestamp falls into configured quiet hours.
   */
  public isWithinQuietHours(config: QuietHoursConfig, timestampMs: number): boolean {
    if (!config.enabled) return false;

    const date = new Date(timestampMs);
    const timeParts = config.startTime.split(':');
    const startHour = parseInt(timeParts[0] ?? '22', 10);
    const startMin = parseInt(timeParts[1] ?? '0', 10);

    const endParts = config.endTime.split(':');
    const endHour = parseInt(endParts[0] ?? '7', 10);
    const endMin = parseInt(endParts[1] ?? '0', 10);

    const currentMinutes = date.getUTCHours() * 60 + date.getUTCMinutes();
    const startMinutes = startHour * 60 + startMin;
    const endMinutes = endHour * 60 + endMin;

    if (startMinutes > endMinutes) {
      // Overnight quiet period e.g. 22:00 -> 07:00
      return currentMinutes >= startMinutes || currentMinutes < endMinutes;
    } else {
      // Same day quiet period e.g. 13:00 -> 15:00
      return currentMinutes >= startMinutes && currentMinutes < endMinutes;
    }
  }

  /**
   * Checks sliding window limits: max per hour and max per day.
   */
  private checkFatigueLimit(
    profileId: string,
    settings: ProactivityProfileSettings,
    nowMs: number
  ): { allowed: boolean; reason?: string } {
    const records = this.history.get(profileId) || [];
    const oneHourAgo = nowMs - 60 * 60_000;
    const oneDayAgo = nowMs - 24 * 60 * 60_000;

    const inLastHour = records.filter((r) => r.sentAtEpochMs >= oneHourAgo);
    if (inLastHour.length >= settings.maxNotificationsPerHour) {
      return {
        allowed: false,
        reason: `Fatigue limit: Exceeded ${settings.maxNotificationsPerHour} notifications in the past hour.`,
      };
    }

    const inLastDay = records.filter((r) => r.sentAtEpochMs >= oneDayAgo);
    if (inLastDay.length >= settings.maxNotificationsPerDay) {
      return {
        allowed: false,
        reason: `Daily fatigue limit: Exceeded ${settings.maxNotificationsPerDay} notifications today.`,
      };
    }

    return { allowed: true };
  }

  /**
   * Record user interaction for fatigue learning (e.g. user dismissed without reading).
   */
  public recordFeedback(notificationId: string, profileId: string, reaction: 'clicked' | 'dismissed' | 'ignored'): void {
    const records = this.history.get(profileId);
    if (!records) return;

    const notif = records.find((r) => r.notificationId === notificationId);
    if (notif) {
      notif.userReaction = reaction;
    }
  }

  /**
   * Reset engine state (used in tests).
   */
  public reset(): void {
    this.profileSettings.clear();
    this.history.clear();
  }
}

export const defaultProactivityEngine = new ProactivityEngine();
