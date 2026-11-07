/**
 * Aster Companion Backend - Visual Frame Ingestion Types
 * Supporting Continuous Screen Awareness, Perceptual Analysis, and Temporal Graph Linking
 */

export interface FrameDimensions {
  width: number;
  height: number;
}

export interface FramePayload {
  deviceId: string;
  sessionId: string;
  profileId: string;
  sequenceNumber: number; // Monotonically increasing per device
  captureTimestamp: number; // Epoch ms when captured on client
  uploadTimestamp: number;  // Epoch ms when sent over network
  dimensions: FrameDimensions;
  orientation: 'portrait' | 'landscape';
  imageData: string | Buffer; // Base64 or raw image buffer (e.g. JPEG / WebP / PNG)
  activeApp?: {
    packageName?: string;
    windowTitle?: string;
    bundleId?: string;
  };
  clientCaptureFps?: number;
}

export type FrameProcessingStatus = 
  | 'ANALYZED'
  | 'STATIC_SKIPPED'
  | 'GAP_RECOVERED'
  | 'DUPLICATE_REJECTED'
  | 'DROPPED_BACKPRESSURE';

export interface SequenceGapInfo {
  detected: boolean;
  expectedSequence: number;
  receivedSequence: number;
  lostFramesCount: number;
  gapDurationMs: number;
  missingInterval: [number, number]; // [startSeq, endSeq]
}

export interface PerceptualDiffResult {
  isStatic: boolean;
  isSceneChange: boolean;
  differenceScore: number; // 0.0 (identical) to 1.0 (completely distinct)
  hammingDistance: number;
  hashCurrent: string;
  hashPrevious?: string;
}

export interface DetectedUiElement {
  type: 'button' | 'input' | 'text' | 'image' | 'header' | 'container';
  label?: string;
  boundingBox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  confidence: number;
}

export interface VisualUnderstandingMetadata {
  extractedText: string[];
  uiElements: DetectedUiElement[];
  sceneDescription: string;
  contextTags: string[];
  primaryCategory?: 'shopping' | 'social' | 'media' | 'productivity' | 'browsing' | 'settings' | 'other';
  detectedEntities?: Array<{
    name: string;
    type: 'product' | 'person' | 'location' | 'date' | 'url';
    confidence: number;
  }>;
}

export interface TemporalGraphNode {
  nodeId: string;
  frameId: string;
  sessionId: string;
  profileId: string;
  deviceId: string;
  sequenceNumber: number;
  timestamp: number;
  activeApp?: string;
  sceneSummary: string;
  metadata: VisualUnderstandingMetadata;
  previousNodeId?: string;
  timeDeltaFromPreviousMs?: number;
  transitionType?: 'continuity' | 'scroll' | 'tab_switch' | 'app_switch' | 'gap_resumed';
}

export interface IngestionFpsMetrics {
  deviceId: string;
  sessionId: string;
  captureFps: number;   // Rate captured on device (PRD §5.3: capture rate)
  uploadFps: number;    // Rate sent across network (upload rate)
  ingestFps: number;    // Rate received and accepted by backend (ingestion rate)
  analysisFps: number;  // Rate analyzed by AI/OCR pipeline (analysis rate)
  totalReceivedFrames: number;
  totalAnalyzedFrames: number;
  totalSkippedStaticFrames: number;
  totalGapsDetected: number;
  totalLostFrames: number;
  lastSequenceNumber: number;
  sampleWindowSeconds: number;
  continuityRatio: number; // Analyzed / (Analyzed + Lost)
}

export interface IngestionResult {
  frameId: string;
  status: FrameProcessingStatus;
  sequenceNumber: number;
  gapInfo?: SequenceGapInfo;
  diffResult: PerceptualDiffResult;
  visualMetadata?: VisualUnderstandingMetadata;
  temporalNode?: TemporalGraphNode;
  metrics: IngestionFpsMetrics;
  serverIngestLatencyMs: number;
}
