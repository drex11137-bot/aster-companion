/**
 * Aster Companion Backend - Proactivity Engine Types
 * Multi-Factor Scoring, Quiet Hours, Fatigue Management, and Evidence Citations
 */

export interface EvidenceCitation {
  citationId: string;
  sourceType: 'screen_observation' | 'memory' | 'calendar_event' | 'behavioral_pattern' | 'photo';
  sourceId: string;
  timestamp: string; // ISO timestamp
  headline: string;
  snippet: string;
  confidenceScore: number;
  deepLink?: string;
}

export interface ProactiveCandidateTrigger {
  candidateId: string;
  profileId: string;
  userId: string;
  category: 'reminder' | 'task_suggestion' | 'contextual_insight' | 'continuity_alert' | 'shopping_offer';
  title: string;
  body: string;
  relevance: number;       // 0.0 - 1.0: Contextual match with active user activity
  confidence: number;      // 0.0 - 1.0: Detector / model certainty
  urgency: number;         // 0.0 - 1.0: Time sensitivity
  interruptionCost: number;// 0.0 - 1.0: Inconvenience to user (e.g. video playing, driving, active call)
  actionPayload?: {
    actionName: string;
    arguments: Record<string, unknown>;
  };
  evidenceCitations: EvidenceCitation[];
}

export type ProactiveDecisionStatus = 
  | 'DISPATCHED'
  | 'SUPPRESSED_SCORE_TOO_LOW'
  | 'SUPPRESSED_QUIET_HOURS'
  | 'SUPPRESSED_FATIGUE_LIMIT'
  | 'SUPPRESSED_SNOOZED'
  | 'SUPPRESSED_USER_DISABLED';

export interface ProactivityScoreBreakdown {
  relevance: number;
  confidence: number;
  urgency: number;
  interruptionCost: number;
  rawScore: number; // (relevance * confidence * urgency) - interruptionCost
  threshold: number;
  passesThreshold: boolean;
}

export interface ProactivityEvaluationResult {
  candidateId: string;
  profileId: string;
  userId: string;
  status: ProactiveDecisionStatus;
  score: ProactivityScoreBreakdown;
  suppressionReason?: string;
  dispatchedNotification?: {
    notificationId: string;
    title: string;
    body: string;
    category: string;
    channel: 'push' | 'in_app' | 'subtle_indicator';
    citations: EvidenceCitation[];
    sentAt: string;
  };
}

export interface QuietHoursConfig {
  enabled: boolean;
  startTime: string; // "22:00"
  endTime: string;   // "07:00"
  timezone: string;  // e.g. "America/New_York", "UTC"
}

export interface ProactivityProfileSettings {
  profileId: string;
  enabled: boolean;
  minScoreThreshold: number; // default: 0.35
  maxNotificationsPerHour: number; // default: 3
  maxNotificationsPerDay: number;  // default: 10
  quietHours: QuietHoursConfig;
  snoozeUntil?: string; // ISO timestamp
  snoozedCategories?: string[];
}
