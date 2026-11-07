/**
 * Aster Companion Web Screen Awareness Types
 * Conforms to PRD v1.1 Continuous Screen Awareness & Temporal Visual Ingestion
 */

export type ScreenAwarenessState =
  | 'idle'
  | 'requesting'
  | 'active'
  | 'paused'
  | 'stopped'
  | 'error';

export interface CapturedFrame {
  /** Stable monotonic frame ID (e.g. frame_000042_1730440000000) */
  id: string;
  /** Strictly increasing monotonic per-device sequence number */
  sequence: number;
  /** UTC ISO 8601 timestamp */
  timestamp: string;
  /** Epoch milliseconds timestamp */
  timestampMs: number;
  /** Captured pixel width */
  width: number;
  /** Captured pixel height */
  height: number;
  /** 64-bit or 256-bit perceptual difference hash */
  dHash: string;
  /** Normalized difference magnitude relative to previous frame (0.0 = identical, 1.0 = completely inverted) */
  changeRatio: number;
  /** True if forced periodic checkpoint or drastic scene change */
  isKeyframe: boolean;
  /** Compressed image blob (image/webp or image/jpeg) */
  blob: Blob | null;
  /** Optional Data URL representation for preview */
  dataUrl?: string;
  /** Image format mime type */
  mimeType: string;
}

export interface AwarenessMetrics {
  /** Actual rate at which video frames are grabbed from the display track */
  captureFps: number;
  /** Actual rate at which non-duplicate frames are transmitted/emitted to backend */
  uploadFps: number;
  /** Ratio of dropped identical frames (0.0 - 1.0) */
  dropRate: number;
  /** Cumulative frames captured */
  totalFramesCaptured: number;
  /** Cumulative frames emitted/uploaded */
  totalFramesUploaded: number;
  /** Cumulative identical frames dropped */
  totalFramesDropped: number;
  /** Most recent perceptual frame difference score (0.0 to 1.0) */
  lastDiffScore: number;
  /** Current adaptive target FPS (1 - 15) */
  currentAdaptiveFps: number;
  /** Current adaptive sampling interval in milliseconds (66ms - 1000ms) */
  currentIntervalMs: number;
  /** Source capture resolution */
  sourceResolution: {
    width: number;
    height: number;
  };
  /** Display surface captured ('monitor' | 'window' | 'browser') */
  displaySurface?: string;
  /** Whether system audio capture is active on this session */
  hasAudio: boolean;
  /** Latency of frame processing pipeline in ms */
  processingLatencyMs: number;
}

export interface ScreenAwarenessOptions {
  /** Minimum sampling rate when screen is static (default: 1 FPS) */
  minFps: number;
  /** Maximum sampling rate during high motion/interaction (default: 15 FPS) */
  maxFps: number;
  /** Perceptual difference threshold below which frames are dropped (default: 0.035, i.e. 3.5%) */
  changeThreshold: number;
  /** Maximum milliseconds allowed between keyframes even if screen is static (default: 12000 ms) */
  keyframeIntervalMs: number;
  /** Maximum width for captured frame ingestion (default: 1280) */
  captureWidth: number;
  /** Maximum height for captured frame ingestion (default: 720) */
  captureHeight: number;
  /** Low-resolution grid width for fast perceptual hashing (default: 16) */
  hashResolution: number;
  /** Output compression format */
  imageMimeType: 'image/webp' | 'image/jpeg';
  /** Compression quality (0.0 - 1.0) */
  imageQuality: number;
  /** Capture system audio alongside screen */
  includeAudio: boolean;
  /** Profile identifier for session correlation */
  profileId?: string;
  /** Device identifier */
  deviceId?: string;
  /** Backend visual frame ingestion endpoint */
  uploadEndpoint?: string;
}

export interface FrameDropDetail {
  sequence: number;
  reason: 'duplicate_hash' | 'below_change_threshold';
  diffScore: number;
  timestampMs: number;
}

export interface AwarenessStopDetail {
  reason: 'user_action' | 'system_revocation' | 'error';
  totalFramesCaptured: number;
  totalFramesUploaded: number;
}

export type ScreenAwarenessEventMap = {
  stateChange: (state: ScreenAwarenessState, prevState: ScreenAwarenessState) => void;
  frameCaptured: (frame: CapturedFrame) => void;
  frameDropped: (detail: FrameDropDetail) => void;
  metrics: (metrics: AwarenessMetrics) => void;
  error: (error: Error, code?: string) => void;
  stopped: (detail: AwarenessStopDetail) => void;
};
