/**
 * Aster Companion Backend - Voice Quota & Rate Limit Tracker
 * Strictly enforces per-user and per-profile voice minute quotas and concurrency boundaries.
 */

import { QuotaStatus } from '../types/voice.js';

export interface QuotaTrackerOptions {
  dailyMinuteLimit?: number;      // Default: 120 minutes / day
  maxConcurrentSessions?: number; // Default: 1 per device, max 2 per account
  rateLimitWindowMs?: number;     // Sliding window for session creation requests (default 60s)
  maxRequestsPerWindow?: number;  // Max requests in window (default 10)
}

interface ProfileQuotaRecord {
  userId: string;
  profileId: string;
  usedSecondsToday: number;
  lastResetEpochMs: number;
  activeSessionIds: Set<string>;
  recentRequestTimestamps: number[];
}

export class VoiceQuotaTracker {
  private readonly dailyMinuteLimit: number;
  private readonly maxConcurrentSessions: number;
  private readonly rateLimitWindowMs: number;
  private readonly maxRequestsPerWindow: number;

  private records = new Map<string, ProfileQuotaRecord>();

  constructor(options?: QuotaTrackerOptions) {
    this.dailyMinuteLimit = options?.dailyMinuteLimit ?? 120;
    this.maxConcurrentSessions = options?.maxConcurrentSessions ?? 1;
    this.rateLimitWindowMs = options?.rateLimitWindowMs ?? 60_000;
    this.maxRequestsPerWindow = options?.maxRequestsPerWindow ?? 10;
  }

  private getRecordKey(userId: string, profileId: string): string {
    return `${userId}:${profileId}`;
  }

  private getOrCreateRecord(userId: string, profileId: string): ProfileQuotaRecord {
    const key = this.getRecordKey(userId, profileId);
    let record = this.records.get(key);

    const now = Date.now();
    const startOfTodayUtc = new Date(now);
    startOfTodayUtc.setUTCHours(0, 0, 0, 0);

    if (!record) {
      record = {
        userId,
        profileId,
        usedSecondsToday: 0,
        lastResetEpochMs: startOfTodayUtc.getTime(),
        activeSessionIds: new Set<string>(),
        recentRequestTimestamps: [],
      };
      this.records.set(key, record);
    } else if (record.lastResetEpochMs < startOfTodayUtc.getTime()) {
      // Midnight UTC rollover
      record.usedSecondsToday = 0;
      record.lastResetEpochMs = startOfTodayUtc.getTime();
      record.recentRequestTimestamps = [];
    }

    return record;
  }

  /**
   * Check if a profile is allowed to open a new voice session.
   */
  public checkEligibility(userId: string, profileId: string): {
    allowed: boolean;
    reason?: string;
    quotaStatus: QuotaStatus;
  } {
    const record = this.getOrCreateRecord(userId, profileId);
    const now = Date.now();

    // 1. Sliding window rate limiting
    record.recentRequestTimestamps = record.recentRequestTimestamps.filter(
      (ts) => now - ts < this.rateLimitWindowMs
    );

    if (record.recentRequestTimestamps.length >= this.maxRequestsPerWindow) {
      return {
        allowed: false,
        reason: 'Rate limit exceeded: Too many session creation requests. Please wait.',
        quotaStatus: this.getQuotaStatus(userId, profileId),
      };
    }

    // 2. Concurrency limit check (PRD Section 9.5: 1 active profile session per device)
    if (record.activeSessionIds.size >= this.maxConcurrentSessions) {
      return {
        allowed: false,
        reason: `Concurrent session limit reached: Only ${this.maxConcurrentSessions} voice session may be active simultaneously.`,
        quotaStatus: this.getQuotaStatus(userId, profileId),
      };
    }

    // 3. Daily quota check
    const usedMinutes = record.usedSecondsToday / 60;
    if (usedMinutes >= this.dailyMinuteLimit) {
      return {
        allowed: false,
        reason: `Daily quota exhausted: Reached ${this.dailyMinuteLimit} voice minutes allocated for today.`,
        quotaStatus: this.getQuotaStatus(userId, profileId),
      };
    }

    return {
      allowed: true,
      quotaStatus: this.getQuotaStatus(userId, profileId),
    };
  }

  /**
   * Register a new active session for the profile.
   */
  public registerSession(userId: string, profileId: string, sessionId: string): void {
    const record = this.getOrCreateRecord(userId, profileId);
    record.recentRequestTimestamps.push(Date.now());
    record.activeSessionIds.add(sessionId);
  }

  /**
   * Record voice consumption in seconds.
   */
  public addUsage(userId: string, profileId: string, seconds: number): void {
    const record = this.getOrCreateRecord(userId, profileId);
    record.usedSecondsToday += Math.max(0, seconds);
  }

  /**
   * Deregister a session when it closes or disconnects.
   */
  public releaseSession(userId: string, profileId: string, sessionId: string): void {
    const record = this.getOrCreateRecord(userId, profileId);
    record.activeSessionIds.delete(sessionId);
  }

  /**
   * Query the current quota status for a profile.
   */
  public getQuotaStatus(userId: string, profileId: string): QuotaStatus {
    const record = this.getOrCreateRecord(userId, profileId);
    const usedMinutes = Math.round((record.usedSecondsToday / 60) * 100) / 100;
    const remainingMinutes = Math.max(0, Math.round((this.dailyMinuteLimit - usedMinutes) * 100) / 100);

    const tomorrowUtc = new Date(record.lastResetEpochMs);
    tomorrowUtc.setUTCDate(tomorrowUtc.getUTCDate() + 1);

    return {
      userId,
      profileId,
      usedMinutesToday: usedMinutes,
      allocatedMinutesToday: this.dailyMinuteLimit,
      remainingMinutesToday: remainingMinutes,
      activeConcurrentSessions: record.activeSessionIds.size,
      isThrottled: usedMinutes >= this.dailyMinuteLimit,
      resetsAt: tomorrowUtc.toISOString(),
    };
  }

  /**
   * Reset quota state (used primarily in tests).
   */
  public reset(): void {
    this.records.clear();
  }
}
