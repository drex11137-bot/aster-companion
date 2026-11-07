/**
 * Aster Companion - Proactive Intelligence Engine
 * Scheduled Triggers Subsystem
 *
 * Implements:
 * 1. Morning Briefing Generator: synthesizes weather, today's schedule, and key reminders.
 * 2. Evening Wind-down Check-in: reviews accomplishments, unfinished priorities, and tomorrow's start.
 * 3. Contextual Reminder Trigger: manages temporal and context-aware reminders (e.g. "Call Dad at 7:30 PM"),
 *    complete with citation linkage, snoozing, and recurrence.
 */

import * as crypto from 'node:crypto';
import {
  ContextualReminder,
  EveningWindDownPayload,
  MorningBriefingPayload,
  NotificationAction,
  PendingReminderItem,
  ProfileProactiveSettings,
  ProactiveCandidate,
  ScoringDecision,
  UserContext,
} from './types.js';
import { ProactiveScoringEngine } from './scoring_engine.js';

/**
 * Morning Briefing Generator
 */
export class MorningBriefingGenerator {
  /**
   * Synthesizes a structured morning briefing proactive candidate.
   */
  public generateBriefing(payload: MorningBriefingPayload, warmth = 0.8): ProactiveCandidate {
    const greeting = this.createGreeting(payload.userName, payload.companionName, warmth);
    const weatherSummary = this.summarizeWeather(payload.weather);
    const scheduleSummary = this.summarizeSchedule(payload.schedule);
    const remindersSummary = this.summarizeReminders(payload.reminders);

    const bodySections: string[] = [weatherSummary];
    if (scheduleSummary) bodySections.push(scheduleSummary);
    if (remindersSummary) bodySections.push(remindersSummary);

    const body = bodySections.join('\n\n');
    const firstMeeting = payload.schedule.find((s) => !s.isAllDay);

    const actions: NotificationAction[] = [
      {
        id: 'view_schedule',
        title: 'View Schedule',
        type: 'navigate',
        payload: { screen: 'calendar', date: payload.date.toISOString() },
      },
      {
        id: 'snooze_30m',
        title: 'Snooze 30m',
        type: 'snooze',
        payload: { durationMinutes: 30 },
      },
      {
        id: 'dismiss',
        title: 'Dismiss',
        type: 'dismiss',
      },
    ];

    const sourceIds: string[] = [];
    payload.schedule.forEach((s) => sourceIds.push(`cal:${s.id}`));
    payload.reminders.forEach((r) => {
      if (r.sourceMemoryId) sourceIds.push(`mem:${r.sourceMemoryId}`);
    });

    return {
      id: `briefing_morning_${payload.profileId}_${this.formatDateKey(payload.date)}`,
      profileId: payload.profileId,
      category: 'briefing',
      title: `${greeting} - Your Morning Briefing`,
      subtitle: firstMeeting ? `First up: ${firstMeeting.title} at ${this.formatTime(firstMeeting.startTime)}` : undefined,
      body,
      relevance: 0.90,
      confidence: 0.95,
      urgency: 0.65,
      priorityLevel: 'medium',
      citation: {
        sourceType: 'calendar',
        snippet: `Synthesized from ${payload.schedule.length} calendar events and ${payload.reminders.length} reminders.`,
        metadata: {
          calendarEventCount: payload.schedule.length,
          reminderCount: payload.reminders.length,
          sourceIds,
        },
      },
      actions,
      createdAt: payload.date,
      overrideQuietHours: false,
    };
  }

  private createGreeting(userName?: string, companionName = 'Aster', warmth = 0.8): string {
    const name = userName ? `, ${userName}` : '';
    if (warmth > 0.7) {
      return `Good morning${name}! ${companionName} here`;
    }
    return `Good morning${name}`;
  }

  private summarizeWeather(weather: MorningBriefingPayload['weather']): string {
    const alertPrefix = weather.isSevereAlert && weather.severeAlertTitle
      ? `⚠️ Alert: ${weather.severeAlertTitle}. `
      : '';
    const precipText = weather.precipitationProbability > 0.2
      ? ` (${Math.round(weather.precipitationProbability * 100)}% chance of rain)`
      : '';
    return `${alertPrefix}Weather: ${weather.temperatureF}°F (${weather.temperatureC}°C), ${weather.conditionDescription}${precipText}.`;
  }

  private summarizeSchedule(schedule: MorningBriefingPayload['schedule']): string {
    if (schedule.length === 0) {
      return 'Today is clear with no scheduled meetings.';
    }

    const timedEvents = schedule.filter((s) => !s.isAllDay);
    if (timedEvents.length === 0) {
      return `Schedule: ${schedule.length} all-day event(s) today.`;
    }

    const eventList = timedEvents.slice(0, 3).map((e) => {
      return `• ${this.formatTime(e.startTime)}: ${e.title}`;
    }).join('\n');

    const remaining = timedEvents.length - 3;
    const remainingText = remaining > 0 ? `\n• +${remaining} more event(s)` : '';
    return `Today's Schedule (${timedEvents.length} events):\n${eventList}${remainingText}`;
  }

  private summarizeReminders(reminders: PendingReminderItem[]): string {
    if (reminders.length === 0) return '';
    const topReminders = reminders.slice(0, 2).map((r) => `• ${r.title}`).join('\n');
    return `Key Reminders:\n${topReminders}`;
  }

  private formatTime(time: Date | string): string {
    const d = typeof time === 'string' ? new Date(time) : time;
    return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
  }

  private formatDateKey(d: Date): string {
    return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')}`;
  }
}

/**
 * Evening Wind-down Generator
 */
export class EveningWindDownGenerator {
  /**
   * Synthesizes an evening wind-down check-in proactive candidate.
   */
  public generateWindDown(payload: EveningWindDownPayload, warmth = 0.8): ProactiveCandidate {
    const companion = payload.companionName || 'Aster';
    const name = payload.userName ? `, ${payload.userName}` : '';
    const title = warmth > 0.7
      ? `Good evening${name} — Time to wind down`
      : `Evening Check-in${name}`;

    const sections: string[] = [];

    // 1. Accomplishments
    if (payload.completedTasksCount > 0) {
      sections.push(`✓ You accomplished ${payload.completedTasksCount} task(s) today.`);
    }

    // 2. Unresolved priorities
    if (payload.pendingPriorities.length > 0) {
      const topPending = payload.pendingPriorities.slice(0, 2).map((p) => `• ${p.title}`).join('\n');
      sections.push(`Remaining priorities for tomorrow:\n${topPending}`);
    } else {
      sections.push('All planned tasks for today have been resolved.');
    }

    // 3. Tomorrow's first event preview
    if (payload.tomorrowFirstEvent) {
      const startTime = this.formatTime(payload.tomorrowFirstEvent.startTime);
      sections.push(`Tomorrow starts with "${payload.tomorrowFirstEvent.title}" at ${startTime}.`);
    }

    // 4. Quiet hours transition
    const qhHour = payload.targetQuietHoursStart.hour % 12 || 12;
    const qhAmPm = payload.targetQuietHoursStart.hour >= 12 ? 'PM' : 'AM';
    const qhMin = String(payload.targetQuietHoursStart.minute).padStart(2, '0');
    sections.push(`Quiet hours start at ${qhHour}:${qhMin} ${qhAmPm}. Resting well tonight will help you recharge.`);

    const body = sections.join('\n\n');

    const actions: NotificationAction[] = [
      {
        id: 'review_tasks',
        title: 'Review Tasks',
        type: 'navigate',
        payload: { screen: 'tasks' },
      },
      {
        id: 'confirm_alarm',
        title: 'Check Alarms',
        type: 'confirm',
      },
      {
        id: 'dismiss',
        title: 'Dismiss',
        type: 'dismiss',
      },
    ];

    return {
      id: `winddown_evening_${payload.profileId}_${this.formatDateKey(payload.date)}`,
      profileId: payload.profileId,
      category: 'briefing',
      title,
      body,
      relevance: 0.85,
      confidence: 0.90,
      urgency: 0.50,
      priorityLevel: 'low',
      citation: {
        sourceType: 'memory',
        snippet: `${companion} evening debrief synthesizing completed tasks and tomorrow's commitments.`,
      },
      actions,
      createdAt: payload.date,
      overrideQuietHours: false,
    };
  }

  private formatTime(time: Date | string): string {
    const d = typeof time === 'string' ? new Date(time) : time;
    return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
  }

  private formatDateKey(d: Date): string {
    return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')}`;
  }
}

/**
 * Contextual Reminder Scheduler
 * Handles reminder registration, temporal checks, snooze management,
 * and contextual score evaluation.
 */
export class ContextualReminderScheduler {
  private readonly reminders = new Map<string, ContextualReminder>();

  /**
   * Registers a new contextual reminder with transparent memory citation.
   */
  public createReminder(
    data: Omit<ContextualReminder, 'id' | 'status' | 'createdAt' | 'updatedAt'>
  ): ContextualReminder {
    const id = `rem_${crypto.randomUUID()}`;
    const now = new Date();
    const reminder: ContextualReminder = {
      ...data,
      id,
      status: 'pending',
      createdAt: now,
      updatedAt: now,
    };
    this.reminders.set(id, reminder);
    return reminder;
  }

  /**
   * Evaluates all pending and snoozed reminders against current time and context.
   * Runs each candidate through the ProactiveScoringEngine.
   */
  public evaluatePendingReminders(
    currentTime: Date,
    context: UserContext,
    settings: ProfileProactiveSettings,
    scoringEngine: ProactiveScoringEngine
  ): Array<{ reminder: ContextualReminder; candidate: ProactiveCandidate; decision: ScoringDecision }> {
    const triggeredItems: Array<{
      reminder: ContextualReminder;
      candidate: ProactiveCandidate;
      decision: ScoringDecision;
    }> = [];

    const nowMs = currentTime.getTime();

    for (const reminder of this.reminders.values()) {
      if (reminder.profileId !== settings.profileId) {
        continue; // Enforce profile isolation
      }

      if (reminder.status !== 'pending' && reminder.status !== 'snoozed') {
        continue;
      }

      // Check due time
      const effectiveDueMs = reminder.snoozeUntil
        ? reminder.snoozeUntil.getTime()
        : reminder.triggerTime.getTime();

      if (effectiveDueMs <= nowMs) {
        // Build proactive candidate with transparent memory citation
        const candidate = this.buildCandidateFromReminder(reminder, currentTime);
        const decision = scoringEngine.evaluateCandidate(candidate, context, settings);

        if (decision.shouldDeliver) {
          reminder.status = 'triggered';
          reminder.updatedAt = currentTime;
          triggeredItems.push({ reminder, candidate, decision });
        } else if (decision.reason === 'quiet_hours_active' && decision.deferredUntil) {
          // Defer until quiet hours window completes
          reminder.snoozeUntil = decision.deferredUntil;
          reminder.status = 'snoozed';
          reminder.updatedAt = currentTime;
          triggeredItems.push({ reminder, candidate, decision });
        } else if (decision.reason === 'fatigue_cooldown' && decision.deferredUntil) {
          reminder.snoozeUntil = decision.deferredUntil;
          reminder.status = 'snoozed';
          reminder.updatedAt = currentTime;
          triggeredItems.push({ reminder, candidate, decision });
        }
      }
    }

    return triggeredItems;
  }

  /**
   * Snoozes a reminder for a given number of minutes.
   */
  public snoozeReminder(reminderId: string, durationMinutes = 15): ContextualReminder | null {
    const reminder = this.reminders.get(reminderId);
    if (!reminder) return null;

    const now = new Date();
    reminder.snoozeUntil = new Date(now.getTime() + durationMinutes * 60 * 1000);
    reminder.status = 'snoozed';
    reminder.updatedAt = now;
    return reminder;
  }

  /**
   * Completes a reminder. If recurring, advances to next occurrence.
   */
  public completeReminder(reminderId: string): ContextualReminder | null {
    const reminder = this.reminders.get(reminderId);
    if (!reminder) return null;

    const now = new Date();
    if (reminder.recurrence && reminder.recurrence !== 'none') {
      reminder.triggerTime = this.calculateNextRecurrence(reminder.triggerTime, reminder.recurrence);
      reminder.snoozeUntil = undefined;
      reminder.status = 'pending';
    } else {
      reminder.status = 'completed';
    }

    reminder.updatedAt = now;
    return reminder;
  }

  /**
   * Cancels a reminder.
   */
  public cancelReminder(reminderId: string): boolean {
    const reminder = this.reminders.get(reminderId);
    if (!reminder) return false;

    reminder.status = 'cancelled';
    reminder.updatedAt = new Date();
    return true;
  }

  /**
   * Retrieves all reminders registered for a specific companion profile.
   */
  public getRemindersForProfile(profileId: string): ContextualReminder[] {
    const list: ContextualReminder[] = [];
    for (const rem of this.reminders.values()) {
      if (rem.profileId === profileId) {
        list.push(rem);
      }
    }
    return list;
  }

  public getReminder(reminderId: string): ContextualReminder | undefined {
    return this.reminders.get(reminderId);
  }

  private buildCandidateFromReminder(reminder: ContextualReminder, currentTime: Date): ProactiveCandidate {
    const actions: NotificationAction[] = [
      {
        id: 'snooze_15m',
        title: 'Snooze 15m',
        type: 'snooze',
        payload: { reminderId: reminder.id, durationMinutes: 15 },
      },
      {
        id: 'view_details',
        title: 'View Details',
        type: 'navigate',
        payload: { reminderId: reminder.id, sourceMemoryId: reminder.sourceMemoryId },
      },
      {
        id: 'mark_done',
        title: 'Done',
        type: 'confirm',
        payload: { reminderId: reminder.id },
      },
    ];

    return {
      id: `cand_${reminder.id}`,
      profileId: reminder.profileId,
      category: 'reminder',
      title: reminder.title,
      body: reminder.description || reminder.title,
      relevance: 0.95,
      confidence: 0.95,
      urgency: 0.85,
      priorityLevel: 'high',
      citation: {
        sourceMemoryId: reminder.sourceMemoryId,
        sourceType: 'memory',
        snippet: reminder.sourceQuote,
        confidenceScore: 0.98,
      },
      actions,
      createdAt: currentTime,
      overrideQuietHours: false,
    };
  }

  private calculateNextRecurrence(baseTime: Date, recurrence: ContextualReminder['recurrence']): Date {
    const next = new Date(baseTime.getTime());
    if (recurrence === 'daily') {
      next.setDate(next.getDate() + 1);
    } else if (recurrence === 'weekly') {
      next.setDate(next.getDate() + 7);
    } else if (recurrence === 'weekdays') {
      const day = next.getDay();
      if (day === 5) {
        // Friday -> advance to Monday (+3 days)
        next.setDate(next.getDate() + 3);
      } else if (day === 6) {
        // Saturday -> advance to Monday (+2 days)
        next.setDate(next.getDate() + 2);
      } else {
        next.setDate(next.getDate() + 1);
      }
    }
    return next;
  }
}
