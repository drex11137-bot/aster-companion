import { test, describe } from 'vitest';
import assert from 'node:assert/strict';
import {
  MorningBriefingGenerator,
  EveningWindDownGenerator,
  ContextualReminderScheduler,
  ProactiveScoringEngine,
} from '../../dist/proactive/index.js';
import type {
  MorningBriefingPayload,
  EveningWindDownPayload,
  UserContext,
  ProfileProactiveSettings,
} from '../../dist/proactive/index.js';

function createMockSettings(overrides?: Partial<ProfileProactiveSettings>): ProfileProactiveSettings {
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
    quietHours: {
      enabled: true,
      startHour: 22, // 10 PM
      startMinute: 0,
      endHour: 7, // 7 AM
      endMinute: 0,
      timezone: 'UTC',
      allowCriticalOverride: true,
    },
    deliveryThreshold: 0.25,
    maxNotificationsPerHour: 5,
    maxNotificationsPerDay: 20,
    initiativeLevel: 'balanced',
    personalityWarmth: 0.8,
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
    currentTimestamp: new Date('2026-11-01T15:00:00Z'),
    timezone: 'UTC',
    ...overrides,
  };
}

test('MorningBriefingGenerator: synthesizes weather, schedule, reminders, and interactive actions', () => {
  const generator = new MorningBriefingGenerator();

  const payload: MorningBriefingPayload = {
    profileId: 'profile_test_1',
    userName: 'Alex',
    companionName: 'Aster',
    date: new Date('2026-11-01T08:00:00Z'),
    weather: {
      temperatureC: 18,
      temperatureF: 64,
      conditionDescription: 'Partly Cloudy',
      conditionCode: 'partly_cloudy',
      precipitationProbability: 0.45,
      isSevereAlert: false,
    },
    schedule: [
      {
        id: 'evt_1',
        title: 'Team Product Sync',
        startTime: new Date('2026-11-01T09:30:00Z'),
        endTime: new Date('2026-11-01T10:00:00Z'),
        isAllDay: false,
        meetingUrl: 'https://meet.google.com/xyz',
      },
      {
        id: 'evt_2',
        title: 'Lunch with Sarah',
        startTime: new Date('2026-11-01T12:30:00Z'),
        endTime: new Date('2026-11-01T13:30:00Z'),
        isAllDay: false,
      },
    ],
    reminders: [
      {
        id: 'rem_1',
        title: 'Submit Q4 Budget draft',
        dueTime: new Date('2026-11-01T17:00:00Z'),
        isHighPriority: true,
        sourceMemoryId: 'mem_budget_draft',
      },
    ],
  };

  const candidate = generator.generateBriefing(payload, 0.85);

  assert.equal(candidate.profileId, 'profile_test_1');
  assert.equal(candidate.category, 'briefing');
  assert.ok(candidate.title.includes('Good morning, Alex! Aster here'));
  assert.ok(candidate.subtitle?.includes('First up: Team Product Sync'));

  // Weather verification
  assert.ok(candidate.body.includes('64°F (18°C), Partly Cloudy (45% chance of rain)'));

  // Schedule verification
  assert.ok(candidate.body.includes('Today\'s Schedule (2 events):'));
  assert.ok(candidate.body.includes('Team Product Sync'));

  // Reminders verification
  assert.ok(candidate.body.includes('Submit Q4 Budget draft'));

  // Action buttons
  assert.ok(candidate.actions !== undefined);
  assert.equal(candidate.actions.length, 3);
  assert.equal(candidate.actions[0].id, 'view_schedule');
  assert.equal(candidate.actions[1].id, 'snooze_30m');
  assert.equal(candidate.actions[2].id, 'dismiss');

  // Citation metadata
  assert.equal(candidate.citation?.sourceType, 'calendar');
  assert.ok(candidate.citation?.metadata?.sourceIds !== undefined);
});

test('EveningWindDownGenerator: reviews accomplishments, unfinished tasks, and tomorrow\'s preview', () => {
  const generator = new EveningWindDownGenerator();

  const payload: EveningWindDownPayload = {
    profileId: 'profile_test_1',
    userName: 'Alex',
    companionName: 'Aster',
    date: new Date('2026-11-01T21:00:00Z'),
    completedTasksCount: 4,
    pendingPriorities: [
      {
        id: 'rem_deferred_1',
        title: 'Review PRD v1.2 updates',
        dueTime: new Date('2026-11-02T10:00:00Z'),
        isHighPriority: true,
      },
    ],
    tomorrowFirstEvent: {
      id: 'evt_tomorrow_1',
      title: 'Executive Review',
      startTime: new Date('2026-11-02T09:00:00Z'),
      endTime: new Date('2026-11-02T10:00:00Z'),
      isAllDay: false,
    },
    targetQuietHoursStart: { hour: 22, minute: 0 },
  };

  const candidate = generator.generateWindDown(payload, 0.8);

  assert.equal(candidate.profileId, 'profile_test_1');
  assert.equal(candidate.category, 'briefing');
  assert.ok(candidate.title.includes('Time to wind down'));

  // Body content
  assert.ok(candidate.body.includes('You accomplished 4 task(s) today.'));
  assert.ok(candidate.body.includes('Review PRD v1.2 updates'));
  assert.ok(candidate.body.includes('Tomorrow starts with "Executive Review"'));
  assert.ok(candidate.body.includes('Quiet hours start at 10:00 PM'));

  // Actions
  assert.ok(candidate.actions !== undefined);
  assert.equal(candidate.actions[0].id, 'review_tasks');
  assert.equal(candidate.actions[1].id, 'confirm_alarm');
  assert.equal(candidate.actions[2].id, 'dismiss');
});

test('ContextualReminderScheduler: creates reminder with citation, triggers on time, and snoozes', () => {
  const scheduler = new ContextualReminderScheduler();
  const scoringEngine = new ProactiveScoringEngine();
  const settings = createMockSettings();

  const triggerTime = new Date('2026-11-01T19:30:00Z');
  const reminder = scheduler.createReminder({
    profileId: 'profile_test_1',
    title: 'Call Dad',
    description: 'Call Dad at 7:30 PM to discuss weekend dinner.',
    triggerTime,
    sourceMemoryId: 'mem_call_dad_prompt_99',
    sourceQuote: 'User said: "Remind me to call Dad at 7:30 tonight"',
    recurrence: 'none',
  });

  assert.equal(reminder.title, 'Call Dad');
  assert.equal(reminder.status, 'pending');
  assert.equal(reminder.sourceMemoryId, 'mem_call_dad_prompt_99');

  // 1. Before trigger time (19:20): should NOT fire
  const contextBefore = createMockContext({ currentTimestamp: new Date('2026-11-01T19:20:00Z') });
  const pendingBefore = scheduler.evaluatePendingReminders(
    new Date('2026-11-01T19:20:00Z'),
    contextBefore,
    settings,
    scoringEngine
  );
  assert.equal(pendingBefore.length, 0);

  // 2. At trigger time (19:30): fires candidate with memory citation and rich actions
  const contextAtTrigger = createMockContext({ currentTimestamp: triggerTime });
  const triggered = scheduler.evaluatePendingReminders(
    triggerTime,
    contextAtTrigger,
    settings,
    scoringEngine
  );

  assert.equal(triggered.length, 1);
  const { candidate, decision } = triggered[0];
  assert.equal(candidate.title, 'Call Dad');
  assert.equal(candidate.citation?.sourceMemoryId, 'mem_call_dad_prompt_99');
  assert.equal(candidate.citation?.snippet, 'User said: "Remind me to call Dad at 7:30 tonight"');
  assert.equal(decision.shouldDeliver, true);
  assert.equal(decision.reason, 'threshold_passed');

  // 3. User taps "Snooze 15m"
  const snoozed = scheduler.snoozeReminder(reminder.id, 15);
  assert.ok(snoozed !== undefined);
  assert.equal(snoozed?.status, 'snoozed');
  assert.ok(snoozed?.snoozeUntil !== undefined);
});

test('ContextualReminderScheduler: handles recurrence and profile isolation', () => {
  const scheduler = new ContextualReminderScheduler();

  const reminderA = scheduler.createReminder({
    profileId: 'profile_A',
    title: 'Profile A Task',
    triggerTime: new Date('2026-11-01T10:00:00Z'),
    sourceMemoryId: 'mem_a',
    sourceQuote: 'Quote A',
    recurrence: 'daily',
  });

  scheduler.createReminder({
    profileId: 'profile_B',
    title: 'Profile B Task',
    triggerTime: new Date('2026-11-01T10:00:00Z'),
    sourceMemoryId: 'mem_b',
    sourceQuote: 'Quote B',
    recurrence: 'none',
  });

  // Profile A list only contains Profile A reminder
  const profileAReminders = scheduler.getRemindersForProfile('profile_A');
  assert.equal(profileAReminders.length, 1);
  assert.equal(profileAReminders[0].title, 'Profile A Task');

  // Complete Profile A recurring reminder -> advances triggerTime by 1 day
  const updatedA = scheduler.completeReminder(reminderA.id);
  assert.ok(updatedA !== undefined);
  assert.equal(updatedA?.status, 'pending'); // Recurring remains pending for next cycle
  assert.equal(updatedA?.triggerTime.toISOString(), '2026-11-02T10:00:00.000Z');
});
