/**
 * Aster Companion Web Screen Awareness
 * 
 * Provides continuous display awareness with perceptual deduplication:
 * - navigator.mediaDevices.getDisplayMedia capture with system audio
 * - Adaptive rate controller (1 - 15 FPS dynamically tuned to screen motion)
 * - Perceptual difference hashing (dHash) & identical frame dropping
 * - Accurate Capture FPS vs Upload FPS telemetry measurement
 * - Lifecycle hooks (start, pause, resume, stop) with native revocation detection
 */

import {
  ScreenAwarenessState,
  CapturedFrame,
  AwarenessMetrics,
  ScreenAwarenessOptions,
  AwarenessStopDetail,
  ScreenAwarenessEventMap,
} from './types';

const DEFAULT_OPTIONS: ScreenAwarenessOptions = {
  minFps: 1,
  maxFps: 15,
  changeThreshold: 0.035, // 3.5% normalized luminance delta
  keyframeIntervalMs: 12000, // Force sync keyframe every 12 seconds
  captureWidth: 1280,
  captureHeight: 720,
  hashResolution: 16, // 16x16 luminance grid
  imageMimeType: 'image/webp',
  imageQuality: 0.82,
  includeAudio: true,
};

export class WebScreenAwareness {
  private options: ScreenAwarenessOptions;
  private state: ScreenAwarenessState = 'idle';

  // Stream & DOM elements
  private mediaStream: MediaStream | null = null;
  private videoTrack: MediaStreamTrack | null = null;
  private audioTrack: MediaStreamTrack | null = null;
  private hiddenVideo: HTMLVideoElement | null = null;
  private captureCanvas: HTMLCanvasElement | null = null;
  private captureCtx: CanvasRenderingContext2D | null = null;
  private hashCanvas: HTMLCanvasElement | null = null;
  private hashCtx: CanvasRenderingContext2D | null = null;

  // Adaptive scheduling loop
  private loopTimer: ReturnType<typeof setTimeout> | null = null;
  private metricsTimer: ReturnType<typeof setInterval> | null = null;
  private isLoopRunning = false;
  private currentIntervalMs = 1000;
  private currentAdaptiveFps = 1;

  // Perceptual hashing state
  private previousLuminanceGrid: Float32Array | null = null;
  private lastKeyframeTime = 0;
  private sequenceCounter = 0;

  // Telemetry sliding window
  private capturedTimestamps: number[] = [];
  private uploadedTimestamps: number[] = [];
  private totalCaptured = 0;
  private totalUploaded = 0;
  private totalDropped = 0;
  private lastDiffScore = 0;
  private lastLatencyMs = 0;

  // Event subscribers
  private listeners: { [K in keyof ScreenAwarenessEventMap]?: Array<ScreenAwarenessEventMap[K]> } = {};

  constructor(customOptions?: Partial<ScreenAwarenessOptions>) {
    this.options = { ...DEFAULT_OPTIONS, ...customOptions };
  }

  // ==========================================
  // Public Lifecycle API
  // ==========================================

  public async start(): Promise<void> {
    if (this.state === 'active' || this.state === 'requesting') {
      return;
    }

    this.transitionState('requesting');

    try {
      // 1. Request user screen share via getDisplayMedia
      const displayMediaConstraints: DisplayMediaStreamOptions = {
        video: {
          displaySurface: 'monitor',
          frameRate: { max: this.options.maxFps },
        },
        audio: this.options.includeAudio,
      };

      this.mediaStream = await navigator.mediaDevices.getDisplayMedia(displayMediaConstraints);

      // Extract tracks
      const videoTracks = this.mediaStream.getVideoTracks();
      if (videoTracks.length === 0) {
        throw new Error('No video track available in display media stream');
      }

      this.videoTrack = videoTracks[0];
      const audioTracks = this.mediaStream.getAudioTracks();
      this.audioTrack = audioTracks.length > 0 ? audioTracks[0] : null;

      // Detect native browser "Stop sharing" bar click or system revocation
      this.videoTrack.onended = () => {
        this.handleRevocation('system_revocation');
      };

      // 2. Setup hidden video player to decode incoming stream frames
      await this.setupVideoPipeline(this.mediaStream);

      // 3. Setup rendering and hashing canvases
      this.setupCanvases();

      // 4. Reset counters & timestamps
      this.sequenceCounter = 0;
      this.totalCaptured = 0;
      this.totalUploaded = 0;
      this.totalDropped = 0;
      this.capturedTimestamps = [];
      this.uploadedTimestamps = [];
      this.previousLuminanceGrid = null;
      this.lastKeyframeTime = Date.now();
      this.currentIntervalMs = 1000 / this.options.minFps;
      this.currentAdaptiveFps = this.options.minFps;

      // 5. Start metrics and frame loops
      this.transitionState('active');
      this.startMetricsTimer();
      this.startAdaptiveLoop();
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      this.transitionState('error');
      this.emit('error', error, 'DISPLAY_MEDIA_FAILED');
      this.cleanup();
      throw error;
    }
  }

  public pause(): void {
    if (this.state !== 'active') return;
    this.transitionState('paused');
    if (this.loopTimer) {
      clearTimeout(this.loopTimer);
      this.loopTimer = null;
    }
  }

  public resume(): void {
    if (this.state !== 'paused') return;
    this.transitionState('active');
    this.startAdaptiveLoop();
  }

  public stop(): void {
    if (this.state === 'stopped' || this.state === 'idle') return;
    this.handleRevocation('user_action');
  }

  public getState(): ScreenAwarenessState {
    return this.state;
  }

  public getMetrics(): AwarenessMetrics {
    return this.calculateMetrics();
  }

  public getStream(): MediaStream | null {
    return this.mediaStream;
  }

  public getVideoTrack(): MediaStreamTrack | null {
    return this.videoTrack;
  }

  public getAudioTrack(): MediaStreamTrack | null {
    return this.audioTrack;
  }

  // ==========================================
  // Event Emitter Support
  // ==========================================

  public on<K extends keyof ScreenAwarenessEventMap>(event: K, listener: ScreenAwarenessEventMap[K]): void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event]?.push(listener);
  }

  public off<K extends keyof ScreenAwarenessEventMap>(event: K, listener: ScreenAwarenessEventMap[K]): void {
    const list = this.listeners[event];
    if (!list) return;
    this.listeners[event] = list.filter((l) => l !== listener) as typeof list;
  }

  private emit<K extends keyof ScreenAwarenessEventMap>(event: K, ...args: Parameters<ScreenAwarenessEventMap[K]>): void {
    const list = this.listeners[event];
    if (list) {
      for (const fn of list) {
        try {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (fn as any)(...args);
        } catch (e) {
          console.error(`[WebScreenAwareness] Listener error on event "${String(event)}":`, e);
        }
      }
    }
  }

  // ==========================================
  // Video & Canvas Pipelines
  // ==========================================

  private async setupVideoPipeline(stream: MediaStream): Promise<void> {
    this.hiddenVideo = document.createElement('video');
    this.hiddenVideo.autoplay = true;
    this.hiddenVideo.muted = true;
    this.hiddenVideo.playsInline = true;
    this.hiddenVideo.srcObject = stream;

    await new Promise<void>((resolve, reject) => {
      if (!this.hiddenVideo) return reject(new Error('Video element destroyed'));

      const onPlaying = () => {
        this.hiddenVideo?.removeEventListener('playing', onPlaying);
        resolve();
      };

      this.hiddenVideo.addEventListener('playing', onPlaying);
      this.hiddenVideo.play().catch(reject);
    });
  }

  private setupCanvases(): void {
    // 1. High-res capture canvas
    this.captureCanvas = document.createElement('canvas');
    this.captureCanvas.width = this.options.captureWidth;
    this.captureCanvas.height = this.options.captureHeight;
    this.captureCtx = this.captureCanvas.getContext('2d', { willReadFrequently: true });

    // 2. Low-res perceptual difference hash canvas
    this.hashCanvas = document.createElement('canvas');
    this.hashCanvas.width = this.options.hashResolution;
    this.hashCanvas.height = this.options.hashResolution;
    this.hashCtx = this.hashCanvas.getContext('2d', { willReadFrequently: true });
  }

  // ==========================================
  // Adaptive Loop & Perceptual Hashing
  // ==========================================

  private startAdaptiveLoop(): void {
    this.isLoopRunning = true;

    const executeCycle = async () => {
      if (!this.isLoopRunning || this.state !== 'active') return;

      const startTime = performance.now();

      try {
        await this.processNextFrame();
      } catch (err) {
        console.warn('[WebScreenAwareness] Frame capture cycle error:', err);
      }

      this.lastLatencyMs = performance.now() - startTime;

      // Schedule next tick based on adaptively calculated interval
      if (this.isLoopRunning && this.state === 'active') {
        this.loopTimer = setTimeout(executeCycle, Math.max(15, this.currentIntervalMs));
      }
    };

    executeCycle();
  }

  private async processNextFrame(): Promise<void> {
    if (!this.hiddenVideo || !this.captureCanvas || !this.captureCtx || !this.hashCanvas || !this.hashCtx) {
      return;
    }

    const minReadyState = typeof HTMLMediaElement !== 'undefined' ? HTMLMediaElement.HAVE_CURRENT_DATA : 2;
    if (this.hiddenVideo.readyState < minReadyState) {
      return;
    }

    const now = Date.now();
    this.totalCaptured++;
    this.capturedTimestamps.push(now);

    const sourceW = this.hiddenVideo.videoWidth || this.options.captureWidth;
    const sourceH = this.hiddenVideo.videoHeight || this.options.captureHeight;

    // Draw frame to low-res hashing canvas
    const hashRes = this.options.hashResolution;
    this.hashCtx.drawImage(this.hiddenVideo, 0, 0, hashRes, hashRes);
    const hashImageData = this.hashCtx.getImageData(0, 0, hashRes, hashRes);

    // Compute perceptual difference hash & normalized luminance delta
    const { dHash, changeRatio, luminanceGrid } = this.computePerceptualDelta(hashImageData.data, hashRes);
    this.lastDiffScore = changeRatio;

    // Determine if frame is identical and should be dropped
    const isBelowThreshold = changeRatio < this.options.changeThreshold;
    const isKeyframeDue = (now - this.lastKeyframeTime) >= this.options.keyframeIntervalMs;
    const shouldDrop = isBelowThreshold && !isKeyframeDue && this.previousLuminanceGrid !== null;

    if (shouldDrop) {
      this.totalDropped++;
      this.emit('frameDropped', {
        sequence: this.sequenceCounter + 1,
        reason: 'below_change_threshold',
        diffScore: changeRatio,
        timestampMs: now,
      });

      // Adaptive throttle: smooth step-down towards minFps (1 FPS / 1000ms)
      this.currentIntervalMs = Math.min(
        1000 / this.options.minFps,
        this.currentIntervalMs * 1.35
      );
      this.currentAdaptiveFps = Math.round(1000 / this.currentIntervalMs);
      return;
    }

    // Keep frame! Screen has changed or keyframe interval was reached
    this.previousLuminanceGrid = luminanceGrid;
    if (isKeyframeDue) {
      this.lastKeyframeTime = now;
    }

    // Adaptive acceleration: scale up to maxFps (15 FPS / ~66ms) based on magnitude of change
    if (changeRatio > 0.15) {
      // Substantial screen change / high motion
      this.currentIntervalMs = 1000 / this.options.maxFps;
    } else {
      // Proportional interpolation between minFps and maxFps
      const normalizedRatio = (changeRatio - this.options.changeThreshold) / (0.15 - this.options.changeThreshold);
      const targetFps = this.options.minFps + Math.max(0, Math.min(1, normalizedRatio)) * (this.options.maxFps - this.options.minFps);
      this.currentIntervalMs = 1000 / targetFps;
    }
    this.currentAdaptiveFps = Math.max(
      this.options.minFps,
      Math.min(this.options.maxFps, Math.round(1000 / this.currentIntervalMs))
    );

    // Draw full resolution frame to capture canvas
    this.captureCanvas.width = this.options.captureWidth;
    this.captureCanvas.height = this.options.captureHeight;
    this.captureCtx.drawImage(this.hiddenVideo, 0, 0, this.options.captureWidth, this.options.captureHeight);

    // Compress to WebP / JPEG Blob
    const blob = await new Promise<Blob | null>((resolve) => {
      this.captureCanvas?.toBlob(
        (b) => resolve(b),
        this.options.imageMimeType,
        this.options.imageQuality
      );
    });

    this.sequenceCounter++;
    this.totalUploaded++;
    this.uploadedTimestamps.push(now);

    const frameId = `frame_${String(this.sequenceCounter).padStart(6, '0')}_${now}`;
    const capturedFrame: CapturedFrame = {
      id: frameId,
      sequence: this.sequenceCounter,
      timestamp: new Date(now).toISOString(),
      timestampMs: now,
      width: sourceW,
      height: sourceH,
      dHash,
      changeRatio,
      isKeyframe: isKeyframeDue || this.sequenceCounter === 1,
      blob,
      mimeType: this.options.imageMimeType,
    };

    this.emit('frameCaptured', capturedFrame);

    // Optional upload to backend ingestion endpoint
    if (this.options.uploadEndpoint && blob) {
      this.dispatchUpload(capturedFrame, blob).catch((err) => {
        console.warn('[WebScreenAwareness] Frame upload dispatch failed:', err);
      });
    }
  }

  /**
   * Fast Perceptual Gradient Hash & Normalized Luminance Delta
   */
  private computePerceptualDelta(
    rgbaData: Uint8ClampedArray,
    gridSize: number
  ): { dHash: string; changeRatio: number; luminanceGrid: Float32Array } {
    const totalPixels = gridSize * gridSize;
    const luminanceGrid = new Float32Array(totalPixels);

    // 1. Compute grayscale luminance vector: Y = 0.299R + 0.587G + 0.114B
    for (let i = 0; i < totalPixels; i++) {
      const idx = i * 4;
      const r = rgbaData[idx];
      const g = rgbaData[idx + 1];
      const b = rgbaData[idx + 2];
      luminanceGrid[i] = 0.299 * r + 0.587 * g + 0.114 * b;
    }

    // 2. Compute Mean Absolute Difference against previous frame
    let changeRatio = 1.0;
    if (this.previousLuminanceGrid && this.previousLuminanceGrid.length === totalPixels) {
      let absoluteSum = 0;
      for (let i = 0; i < totalPixels; i++) {
        absoluteSum += Math.abs(luminanceGrid[i] - this.previousLuminanceGrid[i]);
      }
      changeRatio = absoluteSum / (totalPixels * 255);
    }

    // 3. Compute difference hash string (dHash): compares adjacent horizontal pixels
    let hashHex = '';
    let currentByte = 0;
    let bitIndex = 0;

    for (let y = 0; y < gridSize; y++) {
      for (let x = 0; x < gridSize - 1; x++) {
        const left = luminanceGrid[y * gridSize + x];
        const right = luminanceGrid[y * gridSize + (x + 1)];
        if (left > right) {
          currentByte |= 1 << (7 - bitIndex);
        }
        bitIndex++;
        if (bitIndex === 8) {
          hashHex += currentByte.toString(16).padStart(2, '0');
          currentByte = 0;
          bitIndex = 0;
        }
      }
    }

    if (bitIndex > 0) {
      hashHex += currentByte.toString(16).padStart(2, '0');
    }

    return {
      dHash: hashHex,
      changeRatio,
      luminanceGrid,
    };
  }

  private async dispatchUpload(frame: CapturedFrame, blob: Blob): Promise<void> {
    if (!this.options.uploadEndpoint) return;

    const formData = new FormData();
    formData.append('frame', blob, `${frame.id}.webp`);
    formData.append(
      'metadata',
      JSON.stringify({
        id: frame.id,
        sequence: frame.sequence,
        timestamp: frame.timestamp,
        dHash: frame.dHash,
        changeRatio: frame.changeRatio,
        isKeyframe: frame.isKeyframe,
        profileId: this.options.profileId,
        deviceId: this.options.deviceId,
      })
    );

    await fetch(this.options.uploadEndpoint, {
      method: 'POST',
      body: formData,
    });
  }

  // ==========================================
  // Metrics & Revocation
  // ==========================================

  private calculateMetrics(): AwarenessMetrics {
    const now = Date.now();
    const oneSecAgo = now - 1000;

    // Prune timestamps older than 1 second
    this.capturedTimestamps = this.capturedTimestamps.filter((t) => t >= oneSecAgo);
    this.uploadedTimestamps = this.uploadedTimestamps.filter((t) => t >= oneSecAgo);

    const captureFps = this.capturedTimestamps.length;
    const uploadFps = this.uploadedTimestamps.length;
    const dropRate = captureFps > 0 ? (captureFps - uploadFps) / captureFps : 0;

    const settings = this.videoTrack?.getSettings();
    const displaySurface = (settings as unknown as { displaySurface?: string })?.displaySurface;

    return {
      captureFps,
      uploadFps,
      dropRate: Math.max(0, Math.min(1, Math.round(dropRate * 100) / 100)),
      totalFramesCaptured: this.totalCaptured,
      totalFramesUploaded: this.totalUploaded,
      totalFramesDropped: this.totalDropped,
      lastDiffScore: Math.round(this.lastDiffScore * 1000) / 1000,
      currentAdaptiveFps: this.currentAdaptiveFps,
      currentIntervalMs: Math.round(this.currentIntervalMs),
      sourceResolution: {
        width: settings?.width || this.options.captureWidth,
        height: settings?.height || this.options.captureHeight,
      },
      displaySurface,
      hasAudio: this.audioTrack !== null && this.audioTrack.readyState === 'live',
      processingLatencyMs: Math.round(this.lastLatencyMs * 10) / 10,
    };
  }

  private startMetricsTimer(): void {
    if (this.metricsTimer) clearInterval(this.metricsTimer);

    this.metricsTimer = setInterval(() => {
      if (this.state === 'active') {
        const metrics = this.calculateMetrics();
        this.emit('metrics', metrics);
      }
    }, 1000);
  }

  private handleRevocation(reason: 'user_action' | 'system_revocation' | 'error'): void {
    if (this.videoTrack) {
      this.videoTrack.onended = null;
    }

    const captured = this.totalCaptured;
    const uploaded = this.totalUploaded;

    this.transitionState('stopped');

    const stopDetail: AwarenessStopDetail = {
      reason,
      totalFramesCaptured: captured,
      totalFramesUploaded: uploaded,
    };

    this.emit('stopped', stopDetail);
    this.cleanup();
  }

  private transitionState(newState: ScreenAwarenessState): void {
    if (this.state === newState) return;
    const prevState = this.state;
    this.state = newState;
    this.emit('stateChange', newState, prevState);
  }

  private cleanup(): void {
    this.isLoopRunning = false;

    if (this.loopTimer) {
      clearTimeout(this.loopTimer);
      this.loopTimer = null;
    }

    if (this.metricsTimer) {
      clearInterval(this.metricsTimer);
      this.metricsTimer = null;
    }

    if (this.videoTrack) {
      this.videoTrack.onended = null;
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    if (this.hiddenVideo) {
      this.hiddenVideo.pause();
      this.hiddenVideo.srcObject = null;
      this.hiddenVideo = null;
    }

    this.videoTrack = null;
    this.audioTrack = null;
    this.captureCanvas = null;
    this.captureCtx = null;
    this.hashCanvas = null;
    this.hashCtx = null;
    this.previousLuminanceGrid = null;
  }
}
