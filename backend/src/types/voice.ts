/**
 * Aster Companion Backend - Real-Time Voice Broker Types
 * Supporting OpenAI Realtime API and Gemini Live API with Provider-Neutral Abstraction
 */

export type VoiceProvider = 'openai' | 'gemini' | 'cascaded_streaming';

export type VoiceModelOpenAI = 'gpt-4o-realtime-preview' | 'gpt-4o-mini-realtime-preview';
export type VoiceModelGemini = 'models/gemini-2.0-flash-exp' | 'models/gemini-2.0-flash-realtime';

export type VoicePreset = 
  | 'alloy' | 'echo' | 'shimmer' | 'ash' | 'ballad' | 'coral' | 'sage' | 'verse' // OpenAI
  | 'Puck' | 'Charon' | 'Kore' | 'Fenrir' | 'Aoede'; // Gemini Live

export interface VadConfig {
  type: 'server_vad';
  threshold: number;         // 0.0 - 1.0 (default: 0.5)
  prefixPaddingMs: number;   // default: 300ms
  silenceDurationMs: number; // default: 500ms
}

export interface VoiceToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, unknown>; // JSON Schema
}

export interface EphemeralSessionRequest {
  userId: string;
  profileId: string;
  deviceId: string;
  preferredProvider?: VoiceProvider;
  voiceName?: VoicePreset | string;
  customInstructions?: string;
  enableTools?: boolean;
  vadConfig?: Partial<VadConfig>;
}

export interface EphemeralSessionTokenResponse {
  sessionId: string;
  provider: VoiceProvider;
  model: string;
  clientSecret: string; // Ephemeral token scoped strictly to this session; master key NEVER exposed!
  expiresAt: string;    // ISO timestamp (typically 60s expiration for token initiation)
  endpointUrl: string;  // WebRTC or WebSocket connection URL
  voiceConfig: {
    voice: string;
    inputAudioFormat: 'pcm16';
    outputAudioFormat: 'pcm16';
    sampleRate: number; // e.g. 24000 for OpenAI, 16000 or 24000 for Gemini
  };
  vadConfig: VadConfig;
  fallbackActive: boolean;
  fallbackReason?: string;
  quotaStatus: QuotaStatus;
}

export interface QuotaStatus {
  userId: string;
  profileId: string;
  usedMinutesToday: number;
  allocatedMinutesToday: number;
  remainingMinutesToday: number;
  activeConcurrentSessions: number;
  isThrottled: boolean;
  resetsAt: string; // ISO timestamp
}

export interface InterruptionSignal {
  sessionId: string;
  signalType: 'response.cancel' | 'input_audio_buffer.clear' | 'barge_in';
  timestamp: number;
  interruptedItemId?: string;
  playbackPositionMs?: number;
  reason?: string;
}

export interface InterruptionResult {
  sessionId: string;
  handled: boolean;
  timestamp: number;
  elapsedMs: number;
  cancelledResponseId?: string;
  clearedBufferBytes?: number;
}

export interface ProviderHealth {
  provider: VoiceProvider;
  healthy: boolean;
  latencyMs: number;
  lastChecked: number;
  consecutiveFailures: number;
  statusMessage?: string;
}
