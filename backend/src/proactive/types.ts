/**
 * Aster Companion - Proactive Intelligence & Notification Subsystem
 * Core Domain Types & Data Contracts
 *
 * Adheres strictly to Aster PRD v1.1:
 * - Multi-factor scoring: Score = (Relevance * Confidence * Urgency) - InterruptionCost
 * - Profile isolation: max two companion profiles per account
 * - Transparent citation linkage: memory IDs and screen event timestamps
 * - Rich interactive payloads (Snooze 15m, View Details, Dismiss)
 */

export type UserState =
  | 'active'
  | 'idle'
  | 'driving'
  | 'sleeping'
  | 'in_meeting'
  | 'focus_work'
  | 'exercising';

export type NotificationCategory =
  | 'calendar'
  | 'reminder'
  | 'briefing'
  | 'communication'
  | 'suggestion'
  | 'system'
  | 'emergency';

export type UrgencyLevel = 'low' | 'medium' | 'high' | 'critical' | 'emergency';

export type ActionType = 'snooze' | 'navigate' | 'dismiss' | 'confirm' | 'custom';

export interface NotificationAction {
  id: string;
  title: string;
  type: ActionType;
  payload?: Record<string, unknown>;
  isDestructive?: boolean;
  isAuthenticationRequired?: boolean;
}

export type CitationSourceType =
  | 'memory'
  | 'screen_event'
  | 'calendar'
  | 'email'
  | 'audio_transcript'
  | 'external';

export interface CitationLinkage {
  sourceMemoryId?: string;
  screenEventTimestamp?: string;
  sourceType: CitationSourceType;
  snippet?: string;
  confidenceScore?: number;
  metadata?: Record<string, unknown>;
}

export interface ProactiveCandidate {
  id: string;
  profileId: string;
  category: NotificationCategory;
  title: string;
  body: string;
  subtitle?: string;
  relevance: number; // [0.0, 1.0]
  confidence: number; // [0.0, 1.0]
  urgency: number; // [0.0, 1.0]
  priorityLevel?: UrgencyLevel;
  citation?: CitationLinkage;
  actions?: NotificationAction[];
  targetPlatform?: 'android' | 'ios' | 'all';
  createdAt: Date | string;
  expiresAt?: Date | string;
  overrideQuietHours?: boolean;
  metadata?: Record<string, unknown>;
}

export interface QuietHoursConfig {
  enabled: boolean;
  startHour: number; // 0 - 23 (e.g. 22 for 10 PM)
  startMinute: number; // 0 - 59
  endHour: number; // 0 - 23 (e.g. 7 for 7 AM)
  endMinute: number; // 0 - 59
  timezone: string; // e.g. "America/New_York", "UTC", "Africa/Lagos"
  allowCriticalOverride: boolean;
  allowedCategoriesDuringQuietHours?: NotificationCategory[];
}

export interface UserContext {
  userState: UserState;
  screenOn: boolean;
  activeAppId?: string;
  audioPlaying: boolean;
  inCall: boolean;
  isDoNotDisturb: boolean;
  batteryLevel?: number; // 0.0 - 1.0
  isCharging?: boolean;
  currentTimestamp?: Date | string;
  timezone?: string;
  locationState?: 'home' | 'work' | 'transit' | 'unknown';
}

export interface ProfileProactiveSettings {
  profileId: string;
  globalEnabled: boolean;
  enabledCategories: Record<NotificationCategory, boolean>;
  quietHours: QuietHoursConfig;
  deliveryThreshold: number; // Minimum score needed to dispatch (e.g. 0.25)
  maxNotificationsPerHour: number; // Frequency cap per hour (e.g. 3)
  maxNotificationsPerDay: number; // Frequency cap per day (e.g. 12)
  initiativeLevel: 'conservative' | 'balanced' | 'proactive';
  personalityWarmth?: number; // 0.0 - 1.0
}

export interface ScoringBreakdown {
  relevance: number;
  confidence: number;
  urgency: number;
  interruptionCost: number;
  rawScore: number;
  fatiguePenalty: number;
  finalScore: number;
}

export type ScoringDecisionReason =
  | 'threshold_passed'
  | 'threshold_not_met'
  | 'quiet_hours_active'
  | 'rate_limited'
  | 'fatigue_cooldown'
  | 'category_disabled'
  | 'emergency_override';

export interface ScoringDecision {
  candidateId: string;
  profileId: string;
  shouldDeliver: boolean;
  reason: ScoringDecisionReason;
  scoreBreakdown: ScoringBreakdown;
  deferredUntil?: Date;
  evaluatedAt: Date;
}

export interface NotificationFeedback {
  notificationId: string;
  profileId: string;
  category: NotificationCategory;
  actionTaken: 'click' | 'dismiss' | 'snooze_15m' | 'snooze_1h' | 'view_details' | 'custom_action';
  timestamp: Date;
}

export interface FatigueTrackerRecord {
  profileId: string;
  category: NotificationCategory;
  consecutiveDismissals: number;
  lastDismissedAt?: Date;
  lastEngagedAt?: Date;
  lastDeliveredAt?: Date;
  deliveryTimestamps: Date[];
}

export type DevicePlatform = 'android' | 'ios';

export interface DeviceRegistration {
  deviceToken: string;
  platform: DevicePlatform;
  profileId: string;
  appVersion?: string;
  lastActiveAt?: Date;
}

export interface DispatchResult {
  notificationId: string;
  platform: DevicePlatform;
  deviceToken: string;
  success: boolean;
  messageId?: string;
  statusCode?: number;
  error?: string;
  shouldUnregisterToken?: boolean;
  sentAt: Date;
}

// Scheduled Trigger Domain Types
export interface WeatherContext {
  temperatureC: number;
  temperatureF: number;
  conditionDescription: string;
  conditionCode: 'sunny' | 'partly_cloudy' | 'cloudy' | 'rain' | 'thunderstorm' | 'snow' | 'windy';
  precipitationProbability: number; // 0.0 - 1.0
  isSevereAlert: boolean;
  severeAlertTitle?: string;
}

export interface CalendarEventSummary {
  id: string;
  title: string;
  startTime: Date | string;
  endTime: Date | string;
  isAllDay: boolean;
  location?: string;
  meetingUrl?: string;
  attendeesCount?: number;
}

export interface PendingReminderItem {
  id: string;
  title: string;
  dueTime: Date | string;
  isHighPriority: boolean;
  sourceMemoryId?: string;
  sourceQuote?: string;
}

export interface MorningBriefingPayload {
  profileId: string;
  userName?: string;
  companionName?: string;
  date: Date;
  weather: WeatherContext;
  schedule: CalendarEventSummary[];
  reminders: PendingReminderItem[];
}

export interface EveningWindDownPayload {
  profileId: string;
  userName?: string;
  companionName?: string;
  date: Date;
  completedTasksCount: number;
  pendingPriorities: PendingReminderItem[];
  tomorrowFirstEvent?: CalendarEventSummary;
  targetQuietHoursStart: { hour: number; minute: number };
}

export interface ContextualReminder {
  id: string;
  profileId: string;
  title: string;
  description?: string;
  triggerTime: Date;
  sourceMemoryId: string;
  sourceQuote: string;
  status: 'pending' | 'triggered' | 'snoozed' | 'completed' | 'cancelled';
  snoozeUntil?: Date;
  recurrence?: 'none' | 'daily' | 'weekdays' | 'weekly';
  createdAt: Date;
  updatedAt: Date;
}
