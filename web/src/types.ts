export type ProfileId = 'profile-1' | 'profile-2';

export type HairColor = 'Auburn' | 'Black' | 'Brown' | 'Blonde' | 'Silver';
export type EyeColor = 'Hazel' | 'Brown' | 'Blue' | 'Green' | 'Grey';
export type CompanionStyle = 'Natural' | 'Casual' | 'Professional' | 'Creative';
export type VoiceTone = 'Warm voice' | 'Calm' | 'Energetic' | 'Playful';

export interface CompanionProfile {
  id: ProfileId;
  name: string;
  avatarUrl: string;
  hair: HairColor;
  eyes: EyeColor;
  style: CompanionStyle;
  voice: VoiceTone;
  isOnline: boolean;
  tagline: string;
  personalityNotes: string;
  createdAt: string;
  updatedAt: string;
}

export type MemoryCategory = 'All' | 'People' | 'Preferences' | 'Plans';
export type MemoryIconType = 'sun' | 'person' | 'health' | 'running';

export interface MemoryItem {
  id: string;
  profileId: ProfileId;
  text: string;
  category: 'People' | 'Preferences' | 'Plans';
  iconType: MemoryIconType;
  addedAgo: string;
  timestamp: string;
  photoUrl?: string;
  isSharedWithOtherProfile?: boolean;
  sharedAt?: string;
  provenance: 'stated_fact' | 'observed_pattern' | 'user_explicit';
  confidence: number;
}

export interface TaskItem {
  id: string;
  title: string;
  dueDate: string;
  completed: boolean;
}

export interface ReminderItem {
  id: string;
  title: string;
  time: string;
  dateLabel: string;
  isSnoozed?: boolean;
  snoozedUntil?: string;
}

export interface ChatAttachment {
  id: string;
  type: 'image' | 'file';
  url: string;
  name: string;
  size?: string;
}

export interface ScheduleEvent {
  time: string;
  title: string;
  description: string;
  icon: 'coffee' | 'dumbbell' | 'utensils' | 'book' | 'moon';
}

export interface ChatMessage {
  id: string;
  profileId: ProfileId;
  sender: 'user' | 'companion';
  text: string;
  timestamp: string;
  timeLabel: string;
  status?: 'sent' | 'delivered' | 'read';
  attachments?: ChatAttachment[];
  scheduleCard?: {
    dateTitle: string;
    subtitle: string;
    events: ScheduleEvent[];
  };
  citations?: {
    count: number;
    memoryIds: string[];
    labels: string[];
  };
  isStreaming?: boolean;
}

export interface DeviceSession {
  deviceId: string;
  deviceName: string;
  deviceType: 'laptop' | 'phone' | 'tablet';
  activeProfileId: ProfileId;
  isCurrentDevice: boolean;
  lastActive: string;
  syncState: 'synced' | 'buffering' | 'offline' | 'checkpointed';
  awarenessActive: boolean;
  ipAddress: string;
}

export interface AwarenessMetrics {
  captureFps: number;
  uploadFps: number;
  analysisFps: number;
  targetCaptureFps: number; // e.g. 60 or 120
  latencyMs: number;
  frameSequence: number;
  gapsDetected: number;
  checksumStatus: 'verified' | 'mismatch' | 'recovering';
  bandwidthKbps: number;
  audioInputLevel: number;
}

export interface PerceptionEvent {
  id: string;
  timestamp: string;
  type: 'ocr' | 'scene' | 'ui' | 'audio';
  title: string;
  detail: string;
  confidence: number;
}
