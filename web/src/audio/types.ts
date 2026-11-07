/**
 * Aster Companion WebRTC Voice Client Types
 * Conforms to PRD v1.1 & Real-Time Audio Architecture
 */

export type VoiceClientState =
  | 'idle'
  | 'requesting_permissions'
  | 'connecting'
  | 'connected'
  | 'listening'
  | 'speaking'
  | 'interrupted'
  | 'disconnecting'
  | 'disconnected'
  | 'error';

export interface VADConfig {
  /** Fast Fourier Transform size for spectral analysis (power of 2: 256, 512, 1024, 2048) */
  fftSize: number;
  /** Smoothing time constant for the AnalyserNode (0.0 - 1.0) */
  smoothingTimeConstant: number;
  /** Audio energy threshold in dBFS to classify speech onset (e.g. -45 dB) */
  speechThresholdDb: number;
  /** Audio energy threshold in dBFS to classify silence (e.g. -52 dB) */
  silenceThresholdDb: number;
  /** Minimum consecutive speech frames to confirm speech onset (filters transient clicks/pops) */
  minSpeechFrames: number;
  /** Hangover duration in milliseconds before declaring speech has ended (e.g. 600ms) */
  hangoverMs: number;
  /** Polling interval for VAD calculation in milliseconds */
  energyPollIntervalMs: number;
  /** Dynamic noise floor adaptation rate (0.0 to 1.0) */
  noiseFloorAdaptationRate: number;
}

export interface AudioEnergyData {
  /** Root Mean Square amplitude normalized between 0.0 and 1.0 */
  rms: number;
  /** Decibels relative to full scale (-100 dBFS to 0 dBFS) */
  decibels: number;
  /** Peak absolute amplitude in current frame (0.0 to 1.0) */
  peak: number;
  /** Whether the frame is classified as voice activity based on VAD */
  isSpeech: boolean;
  /** Estimated ambient background noise floor in dBFS */
  noiseFloorDb: number;
}

export interface VisualizerData {
  /** Normalized time-domain waveform values (-1.0 to 1.0) */
  waveform: Float32Array;
  /** Frequency spectrum magnitude values (0.0 to 1.0) */
  frequency: Float32Array;
  /** Calculated energy telemetry */
  energy: AudioEnergyData;
  /** Which audio source is dominant: 'mic' | 'remote' | 'idle' */
  activeSource: 'mic' | 'remote' | 'idle';
  /** Timestamp in milliseconds */
  timestamp: number;
}

export interface SessionConfig {
  /** Voice session broker API endpoint */
  sessionEndpoint: string;
  /** Active companion profile ID */
  profileId: string;
  /** Unique device identifier */
  deviceId: string;
  /** Selected voice name (e.g. 'Aster-Warm', 'Nova-Calm') */
  voiceName?: string;
  /** Model generation temperature (0.0 - 2.0) */
  temperature?: number;
  /** Persona / companion instructions override */
  systemPrompt?: string;
  /** Turn detection / VAD mode */
  turnDetection?: {
    type: 'client_vad' | 'server_vad' | 'none';
    threshold?: number;
    prefix_padding_ms?: number;
    silence_duration_ms?: number;
  };
  /** Custom WebRTC ICE servers (STUN/TURN) */
  iceServers?: RTCIceServer[];
  /** Audio constraints for getUserMedia */
  audioConstraints?: MediaTrackConstraints;
  /** VAD tuning parameters */
  vadConfig?: Partial<VADConfig>;
  /** Ephemeral authentication token if already acquired */
  ephemeralToken?: string;
  /** Enable automatic reconnection on transient network drops */
  autoReconnect?: boolean;
}

export interface SessionResponse {
  sessionId: string;
  model: string;
  clientSecret?: {
    value: string;
    expiresAt: number;
  };
  iceServers?: RTCIceServer[];
  sdpAnswer?: string;
  token?: string;
  relayUrl?: string;
}

export interface RealtimeServerEvent {
  type: string;
  event_id?: string;
  [key: string]: unknown;
}

export interface RealtimeClientEvent {
  type: string;
  event_id?: string;
  [key: string]: unknown;
}

export interface SpeechStartEvent {
  timestamp: number;
  energy: AudioEnergyData;
  source: 'mic' | 'remote';
}

export interface SpeechEndEvent {
  timestamp: number;
  durationMs: number;
  source: 'mic' | 'remote';
}

export interface BargeInEvent {
  timestamp: number;
  reason: 'user_speech_detected' | 'manual_interrupt';
  priorState: VoiceClientState;
  cancelledResponseId?: string;
}

export interface TranscriptEvent {
  role: 'user' | 'assistant';
  text: string;
  isFinal: boolean;
  itemId?: string;
  timestamp: number;
}

export interface VoiceLatencyMetrics {
  roundTripTimeMs: number;
  jitterMs: number;
  audioPacketLossPercent: number;
  speechToResponseLatencyMs?: number;
}

export type VoiceClientEventMap = {
  stateChange: (state: VoiceClientState, prevState: VoiceClientState) => void;
  speechStart: (detail: SpeechStartEvent) => void;
  speechEnd: (detail: SpeechEndEvent) => void;
  bargeIn: (detail: BargeInEvent) => void;
  audioEnergy: (energy: AudioEnergyData) => void;
  visualizerData: (data: VisualizerData) => void;
  transcript: (transcript: TranscriptEvent) => void;
  latency: (metrics: VoiceLatencyMetrics) => void;
  error: (error: Error, code?: string) => void;
  sessionReady: (session: SessionResponse) => void;
};
