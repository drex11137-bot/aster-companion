/**
 * Aster Companion - Proactive Intelligence Engine
 * Scoring Engine & Context Evaluator
 *
 * Implements:
 * 1. Multi-factor notification scoring:
 *    Score = (Relevance * Confidence * Urgency) - InterruptionCost
 * 2. Dynamic user state evaluation (active, idle, driving, sleeping, in_meeting, focus_work, exercising).
 * 3. Quiet hours logic with overnight wrap-around, timezone awareness, and emergency bypass.
 * 4. Anti-fatigue throttler with exponential backoff on user dismissals and engagement recovery.
 */

import {
  NotificationCategory,
  ProactiveCandidate,
  UserContext,
  ProfileProactiveSettings,
  QuietHoursConfig,
  ScoringDecision,
  ScoringBreakdown,
  NotificationFeedback,
  FatigueTrackerRecord,
} from './types.js';

export interface ScoringEngineOptions {
  baseCooldownSeconds?: number; // Default: 900 (15 min)
  backoffFactor?: number; // Default: 2.0
  maxCooldownSeconds?: number; // Default: 86400 (24h)
  defaultDeliveryThreshold?: number; // Default: 0.25
}

export class ProactiveScoringEngine {
  private readonly baseCooldownSeconds: number;
  private readonly backoffFactor: number;
  private readonly maxCooldownSeconds: number;
  private readonly defaultDeliveryThreshold: number;

  // In-memory fatigue and delivery tracking partitioned by profileId + category
  // Key format: `${profileId}:${category}` and `${profileId}:global`
  private readonly fatigueRecords = new Map<string, FatigueTrackerRecord>();

  constructor(options?: ScoringEngineOptions) {
    this.baseCooldownSeconds = options?.baseCooldownSeconds ?? 900;
    this.backoffFactor = options?.backoffFactor ?? 2.0;
    this.maxCooldownSeconds = options?.maxCooldownSeconds ?? 86400;
    this.defaultDeliveryThreshold = options?.defaultDeliveryThreshold ?? 0.25;
  }

  /**
   * Evaluates a proactive notification candidate against the user's current context
   * and profile settings, returning a comprehensive ScoringDecision.
   */
  public evaluateCandidate(
    candidate: ProactiveCandidate,
    context: UserContext,
    settings: ProfileProactiveSettings
  ): ScoringDecision {
    const evaluatedAt = this.resolveDate(context.currentTimestamp);

    // 1. Check Global and Category Enablement
    if (!settings.globalEnabled) {
      return this.buildDecision(candidate, false, 'category_disabled', {
        relevance: candidate.relevance,
        confidence: candidate.confidence,
        urgency: candidate.urgency,
        interruptionCost: 1.0,
        rawScore: 0,
        fatiguePenalty: 0,
        finalScore: 0,
      }, evaluatedAt);
    }

    if (settings.enabledCategories[candidate.category] === false) {
      return this.buildDecision(candidate, false, 'category_disabled', {
        relevance: candidate.relevance,
        confidence: candidate.confidence,
        urgency: candidate.urgency,
        interruptionCost: 1.0,
        rawScore: 0,
        fatiguePenalty: 0,
        finalScore: 0,
      }, evaluatedAt);
    }

    // 2. Evaluate Emergency / Critical Status
    const isEmergency =
      candidate.category === 'emergency' ||
      candidate.priorityLevel === 'emergency' ||
      candidate.priorityLevel === 'critical' ||
      (candidate.urgency >= 0.95 && candidate.overrideQuietHours === true);

    // 3. Evaluate Quiet Hours
    const timezone = context.timezone || settings.quietHours.timezone || 'UTC';
    const inQuietHours = this.isQuietHours(evaluatedAt, settings.quietHours, timezone);

    if (inQuietHours) {
      const allowedCategories = settings.quietHours.allowedCategoriesDuringQuietHours ?? [];
      const isCategoryExempt = allowedCategories.includes(candidate.category);

      if (isEmergency && settings.quietHours.allowCriticalOverride) {
        // Critical emergency overrides quiet hours
        const breakdown = this.calculateBreakdown(candidate, context, settings, 0.05);
        return this.buildDecision(candidate, true, 'emergency_override', breakdown, evaluatedAt);
      }

      if (!isCategoryExempt) {
        // Defer notification until quiet hours end
        const deferredUntil = this.calculateQuietHoursEndTime(evaluatedAt, settings.quietHours, timezone);
        const interruptionCost = 0.95;
        const rawScore = (candidate.relevance * candidate.confidence * candidate.urgency) - interruptionCost;
        return {
          candidateId: candidate.id,
          profileId: candidate.profileId,
          shouldDeliver: false,
          reason: 'quiet_hours_active',
          scoreBreakdown: {
            relevance: candidate.relevance,
            confidence: candidate.confidence,
            urgency: candidate.urgency,
            interruptionCost,
            rawScore,
            fatiguePenalty: 0,
            finalScore: rawScore,
          },
          deferredUntil,
          evaluatedAt,
        };
      }
    }

    // 4. Anti-Fatigue Throttler & Exponential Backoff Check
    const fatigueRecord = this.getFatigueRecord(candidate.profileId, candidate.category);
    const cooldownDurationSeconds = this.calculateCooldownSeconds(fatigueRecord.consecutiveDismissals);

    if (!isEmergency && cooldownDurationSeconds > 0 && fatigueRecord.lastDismissedAt) {
      const elapsedSeconds = (evaluatedAt.getTime() - fatigueRecord.lastDismissedAt.getTime()) / 1000;
      if (elapsedSeconds < cooldownDurationSeconds) {
        const deferredUntil = new Date(fatigueRecord.lastDismissedAt.getTime() + (cooldownDurationSeconds * 1000));
        const breakdown = this.calculateBreakdown(candidate, context, settings, 0.8);
        return {
          candidateId: candidate.id,
          profileId: candidate.profileId,
          shouldDeliver: false,
          reason: 'fatigue_cooldown',
          scoreBreakdown: breakdown,
          deferredUntil,
          evaluatedAt,
        };
      }
    }

    // 5. Sliding-Window Frequency Capping Check (Rate Limiter)
    if (!isEmergency) {
      const globalRecord = this.getFatigueRecord(candidate.profileId, 'suggestion'); // use global delivery tracking
      const isRateLimited = this.isRateLimited(globalRecord, settings, evaluatedAt);
      if (isRateLimited) {
        const breakdown = this.calculateBreakdown(candidate, context, settings, 0.7);
        return this.buildDecision(candidate, false, 'rate_limited', breakdown, evaluatedAt);
      }
    }

    // 6. Compute Interruption Cost & Multi-Factor Score
    const interruptionCost = this.calculateInterruptionCost(context, settings);
    const fatiguePenalty = this.calculateFatiguePenalty(fatigueRecord.consecutiveDismissals);

    // Multi-factor formula:
    // Score = (Relevance * Confidence * Urgency) - InterruptionCost
    const rawScore = (candidate.relevance * candidate.confidence * candidate.urgency) - interruptionCost;
    const finalScore = rawScore - fatiguePenalty;

    const breakdown: ScoringBreakdown = {
      relevance: candidate.relevance,
      confidence: candidate.confidence,
      urgency: candidate.urgency,
      interruptionCost,
      rawScore,
      fatiguePenalty,
      finalScore,
    };

    // 7. Determine Threshold Delivery
    const effectiveThreshold = this.calculateEffectiveThreshold(settings);

    if (isEmergency && finalScore > -0.5) {
      return this.buildDecision(candidate, true, 'emergency_override', breakdown, evaluatedAt);
    }

    if (finalScore >= effectiveThreshold) {
      return this.buildDecision(candidate, true, 'threshold_passed', breakdown, evaluatedAt);
    }

    return this.buildDecision(candidate, false, 'threshold_not_met', breakdown, evaluatedAt);
  }

  /**
   * Dynamically evaluates user state and context modifiers to compute InterruptionCost in [0.0, 1.0].
   */
  public calculateInterruptionCost(context: UserContext, settings: ProfileProactiveSettings): number {
    let baseCost = 0.15;

    // Base cost by UserState
    switch (context.userState) {
      case 'idle':
        baseCost = 0.15;
        break;
      case 'active':
        baseCost = 0.45;
        // If user is actively using a high-intensity app
        if (context.activeAppId && this.isHighFocusApp(context.activeAppId)) {
          baseCost = 0.65;
        }
        break;
      case 'focus_work':
        baseCost = 0.70;
        break;
      case 'exercising':
        baseCost = 0.60;
        break;
      case 'in_meeting':
        baseCost = 0.85;
        break;
      case 'driving':
        baseCost = 0.90;
        break;
      case 'sleeping':
        baseCost = 0.98;
        break;
      default:
        baseCost = 0.40;
    }

    // Context Modifiers
    let modifiers = 0.0;

    if (context.inCall) {
      modifiers += 0.35;
    }

    if (context.isDoNotDisturb) {
      modifiers += 0.40;
    }

    if (context.audioPlaying && !context.inCall) {
      modifiers += 0.10;
    }

    if (context.batteryLevel !== undefined && context.batteryLevel < 0.15 && !context.isCharging) {
      modifiers += 0.15; // Preserve device battery and minimize non-essential wakes
    }

    // Personality & Initiative Tuning
    if (settings.initiativeLevel === 'conservative') {
      modifiers += 0.08;
    } else if (settings.initiativeLevel === 'proactive') {
      modifiers -= 0.08;
    }

    // Personality warmth modifier
    if (settings.personalityWarmth !== undefined) {
      // Warm companion is slightly less abrupt
      modifiers -= (settings.personalityWarmth - 0.5) * 0.05;
    }

    const totalCost = baseCost + modifiers;
    return Math.max(0.0, Math.min(1.0, totalCost));
  }

  /**
   * Quiet Hours Logic:
   * Accurately calculates whether given time falls within user-defined silent window,
   * accounting for overnight wrap-around (e.g. 22:00 -> 07:00) and timezones.
   */
  public isQuietHours(time: Date, config: QuietHoursConfig, timezone: string): boolean {
    if (!config.enabled) {
      return false;
    }

    const localTime = this.getZonedTime(time, timezone);
    const currentMinutes = localTime.hour * 60 + localTime.minute;
    const startMinutes = config.startHour * 60 + config.startMinute;
    const endMinutes = config.endHour * 60 + config.endMinute;

    if (startMinutes === endMinutes) {
      // 24-hour quiet hours
      return true;
    }

    if (startMinutes > endMinutes) {
      // Overnight window (e.g. 22:00 -> 07:00)
      return currentMinutes >= startMinutes || currentMinutes < endMinutes;
    }

    // Daytime window (e.g. 13:00 -> 15:00)
    return currentMinutes >= startMinutes && currentMinutes < endMinutes;
  }

  /**
   * Calculates the exact Date when the next quiet hours window ends.
   */
  public calculateQuietHoursEndTime(time: Date, config: QuietHoursConfig, timezone: string): Date {
    const localTime = this.getZonedTime(time, timezone);
    const currentMinutes = localTime.hour * 60 + localTime.minute;
    const endMinutes = config.endHour * 60 + config.endMinute;

    let daysToAdd = 0;
    if (config.startHour > config.endHour) {
      // Overnight window (e.g. 22:00 -> 07:00)
      if (currentMinutes >= config.startHour * 60 + config.startMinute) {
        // We are before midnight, end is tomorrow morning
        daysToAdd = 1;
      } else {
        // We are after midnight, end is today morning
        daysToAdd = 0;
      }
    } else {
      // Daytime window
      if (currentMinutes >= endMinutes) {
        daysToAdd = 1;
      }
    }

    // Construct end time
    const result = new Date(time.getTime());
    const remainingMinutes = (daysToAdd * 24 * 60) + (endMinutes - currentMinutes);
    result.setTime(result.getTime() + (remainingMinutes * 60 * 1000) - (localTime.second * 1000));
    return result;
  }

  /**
   * Anti-fatigue Feedback Handler:
   * Records user interaction and updates consecutive dismissal counters.
   */
  public recordFeedback(feedback: NotificationFeedback): void {
    const record = this.getFatigueRecord(feedback.profileId, feedback.category);
    const globalRecord = this.getFatigueRecord(feedback.profileId, 'suggestion');

    const isEngagement =
      feedback.actionTaken === 'click' ||
      feedback.actionTaken === 'view_details' ||
      feedback.actionTaken === 'snooze_15m' ||
      feedback.actionTaken === 'snooze_1h' ||
      feedback.actionTaken === 'custom_action';

    if (isEngagement) {
      // Engaging with notification immediately resets consecutive dismissals
      record.consecutiveDismissals = 0;
      record.lastEngagedAt = feedback.timestamp;
      globalRecord.consecutiveDismissals = 0;
      globalRecord.lastEngagedAt = feedback.timestamp;
    } else if (feedback.actionTaken === 'dismiss') {
      // User dismissed without engaging -> increment fatigue counter
      record.consecutiveDismissals += 1;
      record.lastDismissedAt = feedback.timestamp;
      globalRecord.consecutiveDismissals += 1;
      globalRecord.lastDismissedAt = feedback.timestamp;
    }
  }

  /**
   * Marks notification as successfully delivered to maintain frequency sliding windows.
   */
  public recordDelivery(profileId: string, category: NotificationCategory, deliveredAt: Date): void {
    const record = this.getFatigueRecord(profileId, category);
    const globalRecord = this.getFatigueRecord(profileId, 'suggestion');

    record.lastDeliveredAt = deliveredAt;
    record.deliveryTimestamps.push(deliveredAt);

    globalRecord.lastDeliveredAt = deliveredAt;
    globalRecord.deliveryTimestamps.push(deliveredAt);

    // Prune delivery timestamps older than 24h
    const cutoff = deliveredAt.getTime() - (24 * 60 * 60 * 1000);
    record.deliveryTimestamps = record.deliveryTimestamps.filter((t) => t.getTime() > cutoff);
    globalRecord.deliveryTimestamps = globalRecord.deliveryTimestamps.filter((t) => t.getTime() > cutoff);
  }

  /**
   * Calculates exponential backoff cooldown in seconds:
   * Cooldown = BaseCooldown * (BackoffFactor ^ (dismissals - 1))
   */
  public calculateCooldownSeconds(consecutiveDismissals: number): number {
    if (consecutiveDismissals <= 0) {
      return 0;
    }
    const computed = this.baseCooldownSeconds * Math.pow(this.backoffFactor, consecutiveDismissals - 1);
    return Math.min(this.maxCooldownSeconds, Math.round(computed));
  }

  /**
   * Additive fatigue penalty applied to final score.
   */
  private calculateFatiguePenalty(consecutiveDismissals: number): number {
    if (consecutiveDismissals <= 0) {
      return 0.0;
    }
    // Scales up with dismissals, capped at 0.35
    return Math.min(0.35, consecutiveDismissals * 0.08);
  }

  /**
   * Checks sliding window frequency limits (per hour and per day).
   */
  private isRateLimited(
    record: FatigueTrackerRecord,
    settings: ProfileProactiveSettings,
    now: Date
  ): boolean {
    const oneHourAgo = now.getTime() - (60 * 60 * 1000);
    const oneDayAgo = now.getTime() - (24 * 60 * 60 * 1000);

    let countLastHour = 0;
    let countLastDay = 0;

    for (const ts of record.deliveryTimestamps) {
      const timeMs = ts.getTime();
      if (timeMs >= oneDayAgo) {
        countLastDay++;
        if (timeMs >= oneHourAgo) {
          countLastHour++;
        }
      }
    }

    if (countLastHour >= settings.maxNotificationsPerHour) {
      return true;
    }

    if (countLastDay >= settings.maxNotificationsPerDay) {
      return true;
    }

    return false;
  }

  private calculateEffectiveThreshold(settings: ProfileProactiveSettings): number {
    let threshold = settings.deliveryThreshold || this.defaultDeliveryThreshold;

    if (settings.initiativeLevel === 'conservative') {
      threshold += 0.10;
    } else if (settings.initiativeLevel === 'proactive') {
      threshold -= 0.08;
    }

    return Math.max(0.05, Math.min(0.90, threshold));
  }

  private getFatigueRecord(profileId: string, category: NotificationCategory): FatigueTrackerRecord {
    const key = `${profileId}:${category}`;
    let record = this.fatigueRecords.get(key);
    if (!record) {
      record = {
        profileId,
        category,
        consecutiveDismissals: 0,
        deliveryTimestamps: [],
      };
      this.fatigueRecords.set(key, record);
    }
    return record;
  }

  private isHighFocusApp(appId: string): boolean {
    const focusPatterns = ['camera', 'game', 'videoplayer', 'youtube', 'netflix', 'zoom', 'teams', 'meet'];
    const lower = appId.toLowerCase();
    return focusPatterns.some((pattern) => lower.includes(pattern));
  }

  private getZonedTime(date: Date, timezone: string): { hour: number; minute: number; second: number } {
    try {
      const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: timezone,
        hour12: false,
        hour: 'numeric',
        minute: 'numeric',
        second: 'numeric',
      });
      const parts = formatter.formatToParts(date);
      let hour = 0;
      let minute = 0;
      let second = 0;

      for (const part of parts) {
        if (part.type === 'hour') hour = parseInt(part.value, 10);
        if (part.type === 'minute') minute = parseInt(part.value, 10);
        if (part.type === 'second') second = parseInt(part.value, 10);
      }
      if (hour === 24) hour = 0;
      return { hour, minute, second };
    } catch {
      // Fallback to UTC if timezone is invalid
      return {
        hour: date.getUTCHours(),
        minute: date.getUTCMinutes(),
        second: date.getUTCSeconds(),
      };
    }
  }

  private resolveDate(value?: Date | string): Date {
    if (!value) return new Date();
    return typeof value === 'string' ? new Date(value) : value;
  }

  private calculateBreakdown(
    candidate: ProactiveCandidate,
    context: UserContext,
    settings: ProfileProactiveSettings,
    costOverride?: number
  ): ScoringBreakdown {
    const interruptionCost = costOverride ?? this.calculateInterruptionCost(context, settings);
    const rawScore = (candidate.relevance * candidate.confidence * candidate.urgency) - interruptionCost;
    return {
      relevance: candidate.relevance,
      confidence: candidate.confidence,
      urgency: candidate.urgency,
      interruptionCost,
      rawScore,
      fatiguePenalty: 0,
      finalScore: rawScore,
    };
  }

  private buildDecision(
    candidate: ProactiveCandidate,
    shouldDeliver: boolean,
    reason: ScoringDecision['reason'],
    breakdown: ScoringBreakdown,
    evaluatedAt: Date
  ): ScoringDecision {
    return {
      candidateId: candidate.id,
      profileId: candidate.profileId,
      shouldDeliver,
      reason,
      scoreBreakdown: breakdown,
      evaluatedAt,
    };
  }
}
