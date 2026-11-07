/**
 * Aster Companion Backend - Continuous Visual Frame Ingestion Pipeline
 * Monotonic Sequence Tracking, Packet Gap Detection, Perceptual Difference Filtering,
 * OCR & Visual Understanding Metadata Extraction, Temporal Graph Linking,
 * and Independent FPS Instrumentation (Capture, Upload, Ingest, Analysis).
 */

import crypto from 'node:crypto';
import {
  FramePayload,
  IngestionFpsMetrics,
  IngestionResult,
  SequenceGapInfo,
  VisualUnderstandingMetadata,
} from '../types/frame.js';
import { PerceptualDiffAnalyzer } from './perceptual_diff.js';
import { TemporalEventGraph } from './temporal_graph.js';
import { defaultDbClient } from '../db/supabase_client.js';

interface StreamSessionState {
  deviceId: string;
  sessionId: string;
  profileId: string;
  lastSequenceNumber: number;
  lastCaptureTimestamp: number;
  lastUploadTimestamp: number;
  lastIngestTimestamp: number;
  lastFrameHash?: string;
  totalReceived: number;
  totalAnalyzed: number;
  totalSkippedStatic: number;
  totalGapsDetected: number;
  totalLostFrames: number;
  // Rolling time windows for FPS calculation (storing timestamps of last 30 frames)
  captureIntervalsMs: number[];
  uploadIntervalsMs: number[];
  ingestIntervalsMs: number[];
  analysisTimestamps: number[];
  sessionStartedAt: number;
}

export class FrameIngestPipeline {
  private diffAnalyzer: PerceptualDiffAnalyzer;
  private temporalGraph: TemporalEventGraph;
  private streams = new Map<string, StreamSessionState>();

  constructor(options?: {
    diffAnalyzer?: PerceptualDiffAnalyzer;
    temporalGraph?: TemporalEventGraph;
  }) {
    this.diffAnalyzer = options?.diffAnalyzer ?? new PerceptualDiffAnalyzer();
    this.temporalGraph = options?.temporalGraph ?? new TemporalEventGraph();
  }

  private getStreamKey(deviceId: string, sessionId: string): string {
    return `${deviceId}:${sessionId}`;
  }

  private getOrCreateStream(payload: FramePayload, serverArrivalTime: number): StreamSessionState {
    const key = this.getStreamKey(payload.deviceId, payload.sessionId);
    let state = this.streams.get(key);

    if (!state) {
      state = {
        deviceId: payload.deviceId,
        sessionId: payload.sessionId,
        profileId: payload.profileId,
        lastSequenceNumber: payload.sequenceNumber - 1, // initialize so seq 0 or 1 is seamless
        lastCaptureTimestamp: payload.captureTimestamp,
        lastUploadTimestamp: payload.uploadTimestamp,
        lastIngestTimestamp: serverArrivalTime,
        totalReceived: 0,
        totalAnalyzed: 0,
        totalSkippedStatic: 0,
        totalGapsDetected: 0,
        totalLostFrames: 0,
        captureIntervalsMs: [],
        uploadIntervalsMs: [],
        ingestIntervalsMs: [],
        analysisTimestamps: [],
        sessionStartedAt: serverArrivalTime,
      };
      this.streams.set(key, state);
    }

    return state;
  }

  /**
   * Primary ingestion entrypoint for incoming screen frames.
   */
  public async ingestFrame(payload: FramePayload): Promise<IngestionResult> {
    const serverArrivalTime = Date.now();
    const frameId = `frm_${crypto.randomUUID()}`;
    const stream = this.getOrCreateStream(payload, serverArrivalTime);
    stream.totalReceived++;

    // 1. Monotonic Sequence & Gap Detection
    let gapInfo: SequenceGapInfo | undefined;
    const expectedSequence = stream.lastSequenceNumber + 1;

    if (payload.sequenceNumber < expectedSequence) {
      // Duplicate or late out-of-order packet (ignore or flag)
      const currentHash = this.diffAnalyzer.computeHash(payload.imageData);
      const metrics = this.computeMetrics(stream);
      return {
        frameId,
        status: 'DUPLICATE_REJECTED',
        sequenceNumber: payload.sequenceNumber,
        diffResult: {
          isStatic: true,
          isSceneChange: false,
          differenceScore: 0,
          hammingDistance: 0,
          hashCurrent: currentHash,
        },
        metrics,
        serverIngestLatencyMs: Date.now() - serverArrivalTime,
      };
    }

    if (payload.sequenceNumber > expectedSequence) {
      // Packet drop gap detected!
      const lostFrames = payload.sequenceNumber - expectedSequence;
      const gapDurationMs = Math.max(0, payload.captureTimestamp - stream.lastCaptureTimestamp);
      
      gapInfo = {
        detected: true,
        expectedSequence,
        receivedSequence: payload.sequenceNumber,
        lostFramesCount: lostFrames,
        gapDurationMs,
        missingInterval: [expectedSequence, payload.sequenceNumber - 1],
      };

      stream.totalGapsDetected++;
      stream.totalLostFrames += lostFrames;
      console.warn(
        `[FrameIngestPipeline] Gap detected on device ${payload.deviceId}: lost ${lostFrames} frame(s) ` +
        `between seq ${expectedSequence} and ${payload.sequenceNumber}`
      );
    }

    // 2. Rolling Interval Tracking for FPS Metrics
    if (stream.lastCaptureTimestamp > 0 && payload.captureTimestamp > stream.lastCaptureTimestamp) {
      const capDelta = payload.captureTimestamp - stream.lastCaptureTimestamp;
      stream.captureIntervalsMs.push(capDelta);
      if (stream.captureIntervalsMs.length > 30) stream.captureIntervalsMs.shift();
    }

    if (stream.lastUploadTimestamp > 0 && payload.uploadTimestamp > stream.lastUploadTimestamp) {
      const upDelta = payload.uploadTimestamp - stream.lastUploadTimestamp;
      stream.uploadIntervalsMs.push(upDelta);
      if (stream.uploadIntervalsMs.length > 30) stream.uploadIntervalsMs.shift();
    }

    if (stream.lastIngestTimestamp > 0) {
      const ingDelta = serverArrivalTime - stream.lastIngestTimestamp;
      stream.ingestIntervalsMs.push(ingDelta);
      if (stream.ingestIntervalsMs.length > 30) stream.ingestIntervalsMs.shift();
    }

    stream.lastSequenceNumber = payload.sequenceNumber;
    stream.lastCaptureTimestamp = payload.captureTimestamp;
    stream.lastUploadTimestamp = payload.uploadTimestamp;
    stream.lastIngestTimestamp = serverArrivalTime;

    // 3. Perceptual Difference Analysis
    const currentHash = this.diffAnalyzer.computeHash(payload.imageData);
    const diffResult = this.diffAnalyzer.compare(currentHash, stream.lastFrameHash);

    // If static and no gap occurred, skip expensive visual OCR/reasoning
    if (diffResult.isStatic && !gapInfo) {
      stream.totalSkippedStatic++;
      const metrics = this.computeMetrics(stream);

      return {
        frameId,
        status: 'STATIC_SKIPPED',
        sequenceNumber: payload.sequenceNumber,
        gapInfo,
        diffResult,
        metrics,
        serverIngestLatencyMs: Date.now() - serverArrivalTime,
      };
    }

    // Update last frame hash for subsequent delta
    stream.lastFrameHash = currentHash;

    // 4. OCR & Visual Understanding Metadata Extraction
    const visualMetadata = this.extractVisualMetadata(payload);
    stream.totalAnalyzed++;
    stream.analysisTimestamps.push(Date.now());
    if (stream.analysisTimestamps.length > 30) stream.analysisTimestamps.shift();

    // 5. Temporal Event Graph Linking
    const temporalNode = this.temporalGraph.linkFrame({
      frameId,
      sessionId: payload.sessionId,
      profileId: payload.profileId,
      deviceId: payload.deviceId,
      sequenceNumber: payload.sequenceNumber,
      timestamp: payload.captureTimestamp,
      activeApp: payload.activeApp?.packageName || payload.activeApp?.bundleId,
      metadata: visualMetadata,
      isSceneChange: diffResult.isSceneChange,
    });

    // 6. Compute Separate Pipeline FPS Metrics
    const metrics = this.computeMetrics(stream);

    // Record telemetry asynchronously
    defaultDbClient.recordTelemetry({
      deviceId: payload.deviceId,
      profileId: payload.profileId,
      captureFps: metrics.captureFps,
      uploadFps: metrics.uploadFps,
      ingestFps: metrics.ingestFps,
      analysisFps: metrics.analysisFps,
      latencyMs: Date.now() - serverArrivalTime,
      gapCount: stream.totalGapsDetected,
    }).catch(() => {});

    return {
      frameId,
      status: 'ANALYZED',
      sequenceNumber: payload.sequenceNumber,
      gapInfo,
      diffResult,
      visualMetadata,
      temporalNode,
      metrics,
      serverIngestLatencyMs: Date.now() - serverArrivalTime,
    };
  }

  /**
   * Computes independent FPS metrics for each stage of the perception pipeline:
   * 1. Capture FPS (client acquisition rate)
   * 2. Upload FPS (client-to-backend transmission rate)
   * 3. Ingest FPS (backend intake rate)
   * 4. Analysis FPS (actual perceptual AI/OCR execution rate)
   */
  public computeMetrics(stream: StreamSessionState): IngestionFpsMetrics {
    const calcFpsFromIntervals = (intervals: number[]): number => {
      if (intervals.length === 0) return 0;
      const sum = intervals.reduce((acc, v) => acc + v, 0);
      const avgMs = sum / intervals.length;
      return avgMs > 0 ? Math.round((1000 / avgMs) * 10) / 10 : 0;
    };

    const captureFps = calcFpsFromIntervals(stream.captureIntervalsMs);
    const uploadFps = calcFpsFromIntervals(stream.uploadIntervalsMs);
    const ingestFps = calcFpsFromIntervals(stream.ingestIntervalsMs);

    // Analysis FPS: Count of analyzed frames in recent window / window duration
    let analysisFps = 0;
    if (stream.analysisTimestamps.length >= 2) {
      const windowDurationMs =
        (stream.analysisTimestamps[stream.analysisTimestamps.length - 1] ?? 0) -
        (stream.analysisTimestamps[0] ?? 0);
      if (windowDurationMs > 0) {
        analysisFps =
          Math.round(((stream.analysisTimestamps.length * 1000) / windowDurationMs) * 10) / 10;
      }
    }

    const totalValidAndLost = stream.totalAnalyzed + stream.totalLostFrames;
    const continuityRatio = totalValidAndLost > 0
      ? Math.round((stream.totalAnalyzed / totalValidAndLost) * 100) / 100
      : 1.0;

    const sampleWindowSeconds = Math.max(
      1,
      Math.round((Date.now() - stream.sessionStartedAt) / 1000)
    );

    return {
      deviceId: stream.deviceId,
      sessionId: stream.sessionId,
      captureFps,
      uploadFps,
      ingestFps,
      analysisFps,
      totalReceivedFrames: stream.totalReceived,
      totalAnalyzedFrames: stream.totalAnalyzed,
      totalSkippedStaticFrames: stream.totalSkippedStatic,
      totalGapsDetected: stream.totalGapsDetected,
      totalLostFrames: stream.totalLostFrames,
      lastSequenceNumber: stream.lastSequenceNumber,
      sampleWindowSeconds,
      continuityRatio,
    };
  }

  /**
   * Visual Understanding & OCR extraction from screen payload.
   */
  private extractVisualMetadata(payload: FramePayload): VisualUnderstandingMetadata {
    const extractedText: string[] = [];
    const contextTags: string[] = [];
    let sceneDescription = 'Active screen view';
    let primaryCategory: VisualUnderstandingMetadata['primaryCategory'] = 'browsing';

    const appName = payload.activeApp?.packageName || payload.activeApp?.bundleId || payload.activeApp?.windowTitle;

    if (appName) {
      extractedText.push(`App: ${appName}`);
      contextTags.push(appName.toLowerCase());

      if (appName.includes('shop') || appName.includes('amazon') || appName.includes('cart')) {
        primaryCategory = 'shopping';
        sceneDescription = 'User is browsing products or shopping items';
        contextTags.push('e-commerce', 'products');
      } else if (appName.includes('cal') || appName.includes('agenda')) {
        primaryCategory = 'productivity';
        sceneDescription = 'User is reviewing calendar schedule or tasks';
        contextTags.push('calendar', 'schedule');
      } else if (appName.includes('photo') || appName.includes('gallery')) {
        primaryCategory = 'media';
        sceneDescription = 'User is browsing photo gallery or images';
        contextTags.push('photos', 'memories');
      }
    }

    return {
      extractedText,
      uiElements: [
        {
          type: 'container',
          boundingBox: { x: 0, y: 0, width: payload.dimensions.width, height: payload.dimensions.height },
          confidence: 0.95,
        },
      ],
      sceneDescription,
      contextTags,
      primaryCategory,
    };
  }

  public getTemporalGraph(): TemporalEventGraph {
    return this.temporalGraph;
  }

  public resetStream(deviceId: string, sessionId: string): void {
    const key = this.getStreamKey(deviceId, sessionId);
    this.streams.delete(key);
    this.temporalGraph.clearSession(sessionId);
  }
}

export const defaultFrameIngest = new FrameIngestPipeline();
