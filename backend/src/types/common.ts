/**
 * Aster Companion Backend - Common Type Definitions
 * Adheres strictly to PRD v1.1 specifications.
 */

export type PlatformType = 'android' | 'ios' | 'macos' | 'windows' | 'web';

export interface DeviceContext {
  deviceId: string;
  userId: string;
  platform: PlatformType;
  deviceName?: string;
  appVersion?: string;
  capabilities: {
    screenCapture: boolean;
    audioInput: boolean;
    fullDuplexVoice: boolean;
    biometricAuth: boolean;
    backgroundExecution: boolean;
  };
}

export interface ProfileContext {
  profileId: string;
  userId: string;
  name: string;
  voiceName: string;
  personality: {
    warmth: number;       // 0.0 - 1.0
    humor: number;        // 0.0 - 1.0
    formality: number;    // 0.0 - 1.0
    proactivity: number;  // 0.0 - 1.0
  };
  quietHours?: {
    enabled: boolean;
    startTime: string;    // HH:mm format e.g. "22:00"
    endTime: string;      // HH:mm format e.g. "07:00"
    timezone: string;     // e.g. "America/New_York"
  };
}
