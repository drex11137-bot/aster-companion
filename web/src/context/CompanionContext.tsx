import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  ProfileId,
  CompanionProfile,
  MemoryItem,
  TaskItem,
  ReminderItem,
  ChatMessage,
  DeviceSession,
  AwarenessMetrics,
  PerceptionEvent,
} from '../types';
import { sound } from '../utils/audio';

export type NavTab = 'today' | 'chat' | 'memories' | 'studio' | 'awareness' | 'devices';
export type ViewMode = 'responsive-desktop' | 'mobile-frame';

interface CompanionContextType {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  viewMode: ViewMode;
  setViewMode: (mode: ViewMode) => void;

  // Active Companion Profile
  activeProfileId: ProfileId;
  activeProfile: CompanionProfile;
  profiles: Record<ProfileId, CompanionProfile>;
  switchProfile: (profileId: ProfileId) => void;
  updateProfile: (profileId: ProfileId, updates: Partial<CompanionProfile>) => void;

  // Memories (isolated per profile)
  memories: MemoryItem[];
  allProfileMemories: Record<ProfileId, MemoryItem[]>;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  selectedCategory: string;
  setSelectedCategory: (cat: string) => void;
  addMemory: (memory: Omit<MemoryItem, 'id' | 'timestamp' | 'addedAgo' | 'profileId'>) => void;
  updateMemory: (id: string, updates: Partial<MemoryItem>) => void;
  deleteMemory: (id: string) => void;
  shareMemoryToOtherProfile: (memoryId: string) => { success: boolean; message: string };

  // Tasks & Reminders
  tasks: TaskItem[];
  toggleTask: (id: string) => void;
  addTask: (title: string, dueDate: string) => void;
  deleteTask: (id: string) => void;
  nextReminder: ReminderItem | null;
  snoozeReminder: () => void;
  addReminder: (title: string, time: string, dateLabel: string) => void;

  // Chat Messages (isolated per profile)
  messages: ChatMessage[];
  sendMessage: (text: string, attachments?: { name: string; url: string; type: 'image' | 'file' }[]) => void;
  isStreaming: boolean;
  citationDrawerOpen: boolean;
  setCitationDrawerOpen: (open: boolean) => void;
  activeCitationMemories: MemoryItem[];
  inspectCitations: (memoryIds: string[]) => void;

  // Awareness & Screen Sharing
  isAwarenessActive: boolean;
  isAwarenessPaused: boolean;
  isAudioMuted: boolean;
  screenStream: MediaStream | null;
  audioStream: MediaStream | null;
  awarenessMetrics: AwarenessMetrics;
  perceptionEvents: PerceptionEvent[];
  startAwareness: () => Promise<void>;
  pauseAwareness: () => void;
  resumeAwareness: () => void;
  stopAwareness: () => void;
  toggleAudioMute: () => void;

  // Cross-Device Sessions
  deviceSessions: DeviceSession[];
  handoverSession: (targetDeviceId: string) => void;
  revokeSession: (deviceId: string) => void;

  // Settings / Modals
  settingsOpen: boolean;
  setSettingsOpen: (open: boolean) => void;
  offlineHistoryEnabled: boolean;
  setOfflineHistoryEnabled: (val: boolean) => void;
  cloudSyncEnabled: boolean;
  setCloudSyncEnabled: (val: boolean) => void;
  toastMessage: string | null;
  showToast: (msg: string) => void;
}

const CompanionContext = createContext<CompanionContextType | null>(null);

const DEFAULT_PROFILES: Record<ProfileId, CompanionProfile> = {
  'profile-1': {
    id: 'profile-1',
    name: 'Aster',
    avatarUrl: '/assets/aster_avatar.png',
    hair: 'Auburn',
    eyes: 'Hazel',
    style: 'Natural',
    voice: 'Warm voice',
    isOnline: true,
    tagline: 'A calmer, brighter you — one step at a time.',
    personalityNotes: 'Warm, thoughtful, grounded. Loves mindful mornings and balanced structure.',
    createdAt: '2026-10-15T08:00:00Z',
    updatedAt: '2026-11-01T08:24:00Z',
  },
  'profile-2': {
    id: 'profile-2',
    name: 'Nova',
    avatarUrl: '/assets/aster_avatar.png',
    hair: 'Silver',
    eyes: 'Blue',
    style: 'Creative',
    voice: 'Playful',
    isOnline: true,
    tagline: 'Sparking curiosity and deep creative flow.',
    personalityNotes: 'Analytical, energetic, direct, curious. Ideal for deep work sprints and ideation.',
    createdAt: '2026-10-20T10:00:00Z',
    updatedAt: '2026-11-01T08:24:00Z',
  },
};

const INITIAL_MEMORIES_PROFILE_1: MemoryItem[] = [
  {
    id: 'mem-1',
    profileId: 'profile-1',
    text: 'Prefers short answers in the morning',
    category: 'Preferences',
    iconType: 'sun',
    addedAgo: 'Added 3 days ago',
    timestamp: '2026-10-29T07:15:00Z',
    provenance: 'observed_pattern',
    confidence: 0.96,
  },
  {
    id: 'mem-2',
    profileId: 'profile-1',
    text: "Dad's number saved",
    category: 'People',
    iconType: 'person',
    addedAgo: 'Added 1 week ago',
    timestamp: '2026-10-24T18:30:00Z',
    provenance: 'stated_fact',
    confidence: 0.99,
  },
  {
    id: 'mem-3',
    profileId: 'profile-1',
    text: 'Allergic to peanuts',
    category: 'Preferences',
    iconType: 'health',
    addedAgo: 'Added 2 weeks ago',
    timestamp: '2026-10-17T12:00:00Z',
    provenance: 'stated_fact',
    confidence: 1.0,
  },
  {
    id: 'mem-4',
    profileId: 'profile-1',
    text: 'Running a half marathon in March',
    category: 'Plans',
    iconType: 'running',
    addedAgo: 'Added 3 weeks ago',
    timestamp: '2026-10-10T09:40:00Z',
    provenance: 'stated_fact',
    confidence: 0.98,
  },
  {
    id: 'mem-5',
    profileId: 'profile-1',
    text: 'You love oat flat whites',
    category: 'Preferences',
    iconType: 'sun',
    addedAgo: 'Noted 3 days ago',
    photoUrl: '/assets/memory_coffee.png',
    timestamp: '2026-10-29T08:00:00Z',
    provenance: 'observed_pattern',
    confidence: 0.95,
  },
  {
    id: 'mem-6',
    profileId: 'profile-1',
    text: "Sister's birthday: Nov 14",
    category: 'People',
    iconType: 'person',
    addedAgo: 'Added last week',
    photoUrl: '/assets/memory_flowers.png',
    timestamp: '2026-10-25T14:10:00Z',
    provenance: 'stated_fact',
    confidence: 1.0,
  },
];

const INITIAL_MEMORIES_PROFILE_2: MemoryItem[] = [
  {
    id: 'mem-nova-1',
    profileId: 'profile-2',
    text: 'Working on Q4 distributed systems architecture doc',
    category: 'Plans',
    iconType: 'running',
    addedAgo: 'Added 2 days ago',
    timestamp: '2026-10-30T11:00:00Z',
    provenance: 'stated_fact',
    confidence: 0.97,
  },
  {
    id: 'mem-nova-2',
    profileId: 'profile-2',
    text: 'Prefers bulleted executive summaries before deep dives',
    category: 'Preferences',
    iconType: 'sun',
    addedAgo: 'Added 4 days ago',
    timestamp: '2026-10-28T16:20:00Z',
    provenance: 'observed_pattern',
    confidence: 0.92,
  },
];

const INITIAL_TASKS: TaskItem[] = [
  { id: 'task-1', title: 'Book dentist', dueDate: 'Today', completed: false },
  { id: 'task-2', title: 'Finish budget draft', dueDate: 'Tomorrow', completed: false },
  { id: 'task-3', title: 'Pick up parcel', dueDate: 'This week', completed: false },
];

const INITIAL_MESSAGES_PROFILE_1: ChatMessage[] = [
  {
    id: 'msg-1',
    profileId: 'profile-1',
    sender: 'user',
    text: 'Can you plan my Saturday?',
    timestamp: '2026-11-01T20:20:00Z',
    timeLabel: '8:20 PM',
    status: 'read',
  },
  {
    id: 'msg-2',
    profileId: 'profile-1',
    sender: 'companion',
    text: 'Sure. You mentioned wanting a slow morning, so I kept it light.',
    timestamp: '2026-11-01T20:21:00Z',
    timeLabel: '8:21 PM',
    scheduleCard: {
      dateTitle: 'Saturday, Nov 15',
      subtitle: 'A calm and balanced day',
      events: [
        {
          time: '9:00 AM',
          title: 'Slow morning',
          description: 'Coffee, a good book, no rush',
          icon: 'coffee',
        },
        {
          time: '11:30 AM',
          title: 'Gentle workout',
          description: 'Yoga or a walk outside',
          icon: 'dumbbell',
        },
        {
          time: '1:00 PM',
          title: 'Lunch',
          description: 'Something fresh and local',
          icon: 'utensils',
        },
        {
          time: '3:00 PM',
          title: 'Personal time',
          description: 'Read, journal, or a creative project',
          icon: 'book',
        },
        {
          time: '7:00 PM',
          title: 'Wind down',
          description: 'A quiet evening',
          icon: 'moon',
        },
      ],
    },
    citations: {
      count: 2,
      memoryIds: ['mem-1', 'mem-5'],
      labels: ['Prefers short answers in the morning', 'You love oat flat whites'],
    },
  },
];

const INITIAL_MESSAGES_PROFILE_2: ChatMessage[] = [
  {
    id: 'msg-nova-1',
    profileId: 'profile-2',
    sender: 'companion',
    text: "Hey Maya! Ready to dive into the architecture doc or explore your creative projects?",
    timestamp: '2026-11-01T14:00:00Z',
    timeLabel: '2:00 PM',
  },
];

export const CompanionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<NavTab>('today');
  const [viewMode, setViewMode] = useState<ViewMode>('responsive-desktop');

  // Profiles
  const [profiles, setProfiles] = useState<Record<ProfileId, CompanionProfile>>(DEFAULT_PROFILES);
  const [activeProfileId, setActiveProfileId] = useState<ProfileId>('profile-1');

  // Memory isolation
  const [allProfileMemories, setAllProfileMemories] = useState<Record<ProfileId, MemoryItem[]>>({
    'profile-1': INITIAL_MEMORIES_PROFILE_1,
    'profile-2': INITIAL_MEMORIES_PROFILE_2,
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  // Tasks & Reminders
  const [tasks, setTasks] = useState<TaskItem[]>(INITIAL_TASKS);
  const [nextReminder, setNextReminder] = useState<ReminderItem | null>({
    id: 'rem-1',
    title: 'Call Dad at 7:30 PM',
    time: '7:30 PM',
    dateLabel: 'Today',
  });

  // Chat Isolation
  const [allProfileMessages, setAllProfileMessages] = useState<Record<ProfileId, ChatMessage[]>>({
    'profile-1': INITIAL_MESSAGES_PROFILE_1,
    'profile-2': INITIAL_MESSAGES_PROFILE_2,
  });
  const [isStreaming, setIsStreaming] = useState(false);
  const [citationDrawerOpen, setCitationDrawerOpen] = useState(false);
  const [activeCitationMemories, setActiveCitationMemories] = useState<MemoryItem[]>([]);

  // Awareness & Screen Sharing
  const [isAwarenessActive, setIsAwarenessActive] = useState(false);
  const [isAwarenessPaused, setIsAwarenessPaused] = useState(false);
  const [isAudioMuted, setIsAudioMuted] = useState(false);
  const [screenStream, setScreenStream] = useState<MediaStream | null>(null);
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null);

  const [awarenessMetrics, setAwarenessMetrics] = useState<AwarenessMetrics>({
    captureFps: 60,
    uploadFps: 58.4,
    analysisFps: 12.0,
    targetCaptureFps: 120, // PRD v1.1 ambition
    latencyMs: 142,
    frameSequence: 18420,
    gapsDetected: 0,
    checksumStatus: 'verified',
    bandwidthKbps: 4200,
    audioInputLevel: 32,
  });

  const [perceptionEvents] = useState<PerceptionEvent[]>([
    {
      id: 'evt-1',
      timestamp: '20:23:45',
      type: 'ocr',
      title: 'Text detected in Figma',
      detail: '"Aster Companion Mobile Design System v1.1"',
      confidence: 0.99,
    },
    {
      id: 'evt-2',
      timestamp: '20:23:42',
      type: 'scene',
      title: 'Active Application Switch',
      detail: 'Switched from Google Chrome to VS Code',
      confidence: 0.98,
    },
    {
      id: 'evt-3',
      timestamp: '20:23:38',
      type: 'ui',
      title: 'Interactive Schedule Card',
      detail: 'User reviewed Saturday timeline draft',
      confidence: 0.95,
    },
  ]);

  // Devices & Sessions (PRD Sections 9.5 & 10)
  const [deviceSessions, setDeviceSessions] = useState<DeviceSession[]>([
    {
      deviceId: 'dev-laptop-01',
      deviceName: 'MacBook Pro 16" (Current)',
      deviceType: 'laptop',
      activeProfileId: 'profile-1',
      isCurrentDevice: true,
      lastActive: 'Just now',
      syncState: 'synced',
      awarenessActive: false,
      ipAddress: '192.168.1.104',
    },
    {
      deviceId: 'dev-phone-02',
      deviceName: 'Pixel 9 Pro',
      deviceType: 'phone',
      activeProfileId: 'profile-1', // Allowed: same profile across devices
      isCurrentDevice: false,
      lastActive: '3 minutes ago',
      syncState: 'synced',
      awarenessActive: false,
      ipAddress: '192.168.1.182',
    },
    {
      deviceId: 'dev-tablet-03',
      deviceName: 'iPad Air',
      deviceType: 'tablet',
      activeProfileId: 'profile-2', // Allowed: different profile on separate device
      isCurrentDevice: false,
      lastActive: '2 hours ago',
      syncState: 'checkpointed',
      awarenessActive: false,
      ipAddress: '192.168.1.190',
    },
  ]);

  // Global UI state
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [offlineHistoryEnabled, setOfflineHistoryEnabled] = useState(true);
  const [cloudSyncEnabled, setCloudSyncEnabled] = useState(true);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = useCallback((msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((current) => (current === msg ? null : current));
    }, 3200);
  }, []);

  // Active Profile object
  const activeProfile = profiles[activeProfileId];

  // Switch profile with strict isolation guarantee (PRD 9.6)
  const switchProfile = (newProfileId: ProfileId) => {
    if (newProfileId === activeProfileId) return;

    // PRD rule: On profile switch, suspend active session and cleanly switch context
    sound.playChime();
    setActiveProfileId(newProfileId);

    // Update current device session
    setDeviceSessions((prev) =>
      prev.map((dev) =>
        dev.isCurrentDevice ? { ...dev, activeProfileId: newProfileId } : dev
      )
    );

    showToast(`Switched to ${profiles[newProfileId].name}. Memory and context are isolated.`);
  };

  const updateProfile = (profileId: ProfileId, updates: Partial<CompanionProfile>) => {
    setProfiles((prev) => ({
      ...prev,
      [profileId]: {
        ...prev[profileId],
        ...updates,
        updatedAt: new Date().toISOString(),
      },
    }));
    sound.playChime();
    showToast(`Saved ${updates.name || profiles[profileId].name}'s settings!`);
  };

  // Profile-isolated memories
  const memories = allProfileMemories[activeProfileId] || [];

  const addMemory = (item: Omit<MemoryItem, 'id' | 'timestamp' | 'addedAgo' | 'profileId'>) => {
    const newMem: MemoryItem = {
      ...item,
      id: `mem-${Date.now()}`,
      profileId: activeProfileId,
      addedAgo: 'Added just now',
      timestamp: new Date().toISOString(),
    };
    setAllProfileMemories((prev) => ({
      ...prev,
      [activeProfileId]: [newMem, ...prev[activeProfileId]],
    }));
    sound.playChime();
    showToast(`Added to ${activeProfile.name}'s memories`);
  };

  const updateMemory = (id: string, updates: Partial<MemoryItem>) => {
    setAllProfileMemories((prev) => ({
      ...prev,
      [activeProfileId]: prev[activeProfileId].map((m) => (m.id === id ? { ...m, ...updates } : m)),
    }));
    showToast('Memory updated');
  };

  const deleteMemory = (id: string) => {
    setAllProfileMemories((prev) => ({
      ...prev,
      [activeProfileId]: prev[activeProfileId].filter((m) => m.id !== id),
    }));
    showToast('Memory deleted');
  };

  // Explicit item-level sharing (PRD Section 9.4)
  const shareMemoryToOtherProfile = (memoryId: string) => {
    const targetProfileId: ProfileId = activeProfileId === 'profile-1' ? 'profile-2' : 'profile-1';
    const sourceMemory = (allProfileMemories[activeProfileId] || []).find((m) => m.id === memoryId);

    if (!sourceMemory) {
      return { success: false, message: 'Memory not found' };
    }

    // Clone into target profile with provenance = user_explicit
    const sharedCopy: MemoryItem = {
      ...sourceMemory,
      id: `shared-${Date.now()}`,
      profileId: targetProfileId,
      text: sourceMemory.text,
      category: sourceMemory.category,
      addedAgo: `Shared from ${activeProfile.name} just now`,
      timestamp: new Date().toISOString(),
      isSharedWithOtherProfile: true,
      sharedAt: new Date().toISOString(),
      provenance: 'user_explicit',
    };

    // Mark original as shared
    setAllProfileMemories((prev) => ({
      ...prev,
      [activeProfileId]: prev[activeProfileId].map((m) =>
        m.id === memoryId ? { ...m, isSharedWithOtherProfile: true, sharedAt: new Date().toISOString() } : m
      ),
      [targetProfileId]: [sharedCopy, ...prev[targetProfileId]],
    }));

    sound.playChime();
    return {
      success: true,
      message: `Explicitly shared "${sourceMemory.text}" to ${profiles[targetProfileId].name} with audit trail.`,
    };
  };

  // Tasks checklist
  const toggleTask = (id: string) => {
    setTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t))
    );
    sound.playChime();
  };

  const addTask = (title: string, dueDate: string) => {
    const newTask: TaskItem = {
      id: `task-${Date.now()}`,
      title,
      dueDate: dueDate || 'Today',
      completed: false,
    };
    setTasks((prev) => [newTask, ...prev]);
    showToast('Task added');
  };

  const deleteTask = (id: string) => {
    setTasks((prev) => prev.filter((t) => t.id !== id));
  };

  // Reminders
  const snoozeReminder = () => {
    if (!nextReminder) return;
    sound.playChime();
    setNextReminder((prev) =>
      prev
        ? {
            ...prev,
            isSnoozed: true,
            snoozedUntil: '8:00 PM',
          }
        : null
    );
    showToast(`Reminder snoozed until 8:00 PM`);
  };

  const addReminder = (title: string, time: string, dateLabel: string) => {
    setNextReminder({
      id: `rem-${Date.now()}`,
      title,
      time,
      dateLabel,
      isSnoozed: false,
    });
    sound.playChime();
    showToast(`Reminder set: "${title}" for ${time}`);
  };

  // Chat
  const messages = allProfileMessages[activeProfileId] || [];

  const inspectCitations = (memoryIds: string[]) => {
    const all = [...(allProfileMemories['profile-1'] || []), ...(allProfileMemories['profile-2'] || [])];
    const found = all.filter((m) => memoryIds.includes(m.id));
    setActiveCitationMemories(found);
    setCitationDrawerOpen(true);
  };

  const sendMessage = (text: string, attachments?: { name: string; url: string; type: 'image' | 'file' }[]) => {
    if (!text.trim() && (!attachments || attachments.length === 0)) return;

    sound.playSend();

    const now = new Date();
    const timeLabel = now.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      profileId: activeProfileId,
      sender: 'user',
      text,
      timestamp: now.toISOString(),
      timeLabel,
      status: 'sent',
      attachments: attachments?.map((a, i) => ({
        id: `att-${Date.now()}-${i}`,
        type: a.type,
        url: a.url,
        name: a.name,
      })),
    };

    setAllProfileMessages((prev) => ({
      ...prev,
      [activeProfileId]: [...prev[activeProfileId], userMsg],
    }));

    // Generate companion response
    setIsStreaming(true);
    setTimeout(() => {
      let companionResponse = `I noted that down, Maya. Let me know if you'd like me to align it with your upcoming schedule.`;
      let scheduleCard = undefined;
      let citations = undefined;

      const lower = text.toLowerCase();
      if (lower.includes('saturday') || lower.includes('plan') || lower.includes('schedule')) {
        companionResponse = `Sure. You mentioned wanting a slow morning, so I kept it light.`;
        scheduleCard = {
          dateTitle: 'Saturday, Nov 15',
          subtitle: 'A calm and balanced day',
          events: [
            { time: '9:00 AM', title: 'Slow morning', description: 'Coffee, a good book, no rush', icon: 'coffee' as const },
            { time: '11:30 AM', title: 'Gentle workout', description: 'Yoga or a walk outside', icon: 'dumbbell' as const },
            { time: '1:00 PM', title: 'Lunch', description: 'Something fresh and local', icon: 'utensils' as const },
            { time: '3:00 PM', title: 'Personal time', description: 'Read, journal, or a creative project', icon: 'book' as const },
            { time: '7:00 PM', title: 'Wind down', description: 'A quiet evening', icon: 'moon' as const },
          ],
        };
        citations = {
          count: 2,
          memoryIds: ['mem-1', 'mem-5'],
          labels: ['Prefers short answers in the morning', 'You love oat flat whites'],
        };
      } else if (lower.includes('coffee') || lower.includes('drink')) {
        companionResponse = `You love oat flat whites! There's a quiet cafe 3 blocks away that roasts their own beans if you want to take a break.`;
        citations = {
          count: 1,
          memoryIds: ['mem-5'],
          labels: ['You love oat flat whites'],
        };
      } else if (lower.includes('dad') || lower.includes('call')) {
        companionResponse = `I have your reminder set for Dad at 7:30 PM today. His number is safely saved in your contacts.`;
        citations = {
          count: 1,
          memoryIds: ['mem-2'],
          labels: ["Dad's number saved"],
        };
      }

      const compMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        profileId: activeProfileId,
        sender: 'companion',
        text: companionResponse,
        timestamp: new Date().toISOString(),
        timeLabel: new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
        scheduleCard,
        citations,
      };

      setAllProfileMessages((prev) => ({
        ...prev,
        [activeProfileId]: [...prev[activeProfileId], compMsg],
      }));
      setIsStreaming(false);
      sound.playChime();
    }, 1100);
  };

  // Awareness Controls
  const startAwareness = async () => {
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia) {
        const stream = await navigator.mediaDevices.getDisplayMedia({
          video: { frameRate: { ideal: 60, max: 120 } },
          audio: true,
        });
        setScreenStream(stream);

        // Track when user stops screen share from native browser UI
        stream.getVideoTracks()[0].onended = () => {
          stopAwareness();
        };
      }
      setIsAwarenessActive(true);
      setIsAwarenessPaused(false);
      sound.playChime();
      showToast('Continuous awareness session started. Subtle status active.');
    } catch {
      // Permission dismissed or not allowed; activate simulated high-fidelity screen ingestion
      setIsAwarenessActive(true);
      setIsAwarenessPaused(false);
      sound.playChime();
      showToast('Laptop screen awareness active in client mode.');
    }
  };

  const pauseAwareness = () => {
    setIsAwarenessPaused(true);
    showToast('Awareness paused. No frames transmitted.');
  };

  const resumeAwareness = () => {
    setIsAwarenessPaused(false);
    showToast('Awareness resumed.');
  };

  const stopAwareness = () => {
    if (screenStream) {
      screenStream.getTracks().forEach((track) => track.stop());
      setScreenStream(null);
    }
    if (audioStream) {
      audioStream.getTracks().forEach((track) => track.stop());
      setAudioStream(null);
    }
    setIsAwarenessActive(false);
    setIsAwarenessPaused(false);
    showToast('Awareness stopped. All captures ended.');
  };

  const toggleAudioMute = () => {
    setIsAudioMuted((prev) => !prev);
    showToast(isAudioMuted ? 'Microphone unmuted' : 'Microphone muted');
  };

  // Dynamic simulation of metrics and perception events while awareness is active
  useEffect(() => {
    if (!isAwarenessActive || isAwarenessPaused) return;

    const interval = setInterval(() => {
      setAwarenessMetrics((prev) => ({
        ...prev,
        captureFps: Math.min(120, Math.floor(58 + Math.random() * 4)),
        uploadFps: +(57 + Math.random() * 2).toFixed(1),
        analysisFps: +(11.5 + Math.random() * 1.2).toFixed(1),
        latencyMs: Math.floor(135 + Math.random() * 18),
        frameSequence: prev.frameSequence + 60,
        bandwidthKbps: Math.floor(4100 + Math.random() * 300),
        audioInputLevel: isAudioMuted ? 0 : Math.floor(20 + Math.random() * 40),
      }));
    }, 1000);

    return () => clearInterval(interval);
  }, [isAwarenessActive, isAwarenessPaused, isAudioMuted]);

  // Cross-device Handover
  const handoverSession = (targetDeviceId: string) => {
    const target = deviceSessions.find((d) => d.deviceId === targetDeviceId);
    if (!target) return;

    sound.playChime();
    setDeviceSessions((prev) =>
      prev.map((dev) =>
        dev.deviceId === targetDeviceId
          ? { ...dev, isCurrentDevice: true, syncState: 'synced' }
          : { ...dev, isCurrentDevice: false }
      )
    );
    showToast(`Active session handed over to ${target.deviceName}`);
  };

  const revokeSession = (deviceId: string) => {
    setDeviceSessions((prev) => prev.filter((d) => d.deviceId !== deviceId));
    showToast('Device session revoked.');
  };

  return (
    <CompanionContext.Provider
      value={{
        activeTab,
        setActiveTab,
        viewMode,
        setViewMode,
        activeProfileId,
        activeProfile,
        profiles,
        switchProfile,
        updateProfile,
        memories,
        allProfileMemories,
        searchQuery,
        setSearchQuery,
        selectedCategory,
        setSelectedCategory,
        addMemory,
        updateMemory,
        deleteMemory,
        shareMemoryToOtherProfile,
        tasks,
        toggleTask,
        addTask,
        deleteTask,
        nextReminder,
        snoozeReminder,
        addReminder,
        messages,
        sendMessage,
        isStreaming,
        citationDrawerOpen,
        setCitationDrawerOpen,
        activeCitationMemories,
        inspectCitations,
        isAwarenessActive,
        isAwarenessPaused,
        isAudioMuted,
        screenStream,
        audioStream,
        awarenessMetrics,
        perceptionEvents,
        startAwareness,
        pauseAwareness,
        resumeAwareness,
        stopAwareness,
        toggleAudioMute,
        deviceSessions,
        handoverSession,
        revokeSession,
        settingsOpen,
        setSettingsOpen,
        offlineHistoryEnabled,
        setOfflineHistoryEnabled,
        cloudSyncEnabled,
        setCloudSyncEnabled,
        toastMessage,
        showToast,
      }}
    >
      {children}
    </CompanionContext.Provider>
  );
};

export const useCompanion = () => {
  const context = useContext(CompanionContext);
  if (!context) {
    throw new Error('useCompanion must be used within CompanionProvider');
  }
  return context;
};
