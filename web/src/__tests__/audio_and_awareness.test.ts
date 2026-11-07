/**
 * Aster Companion Voice & Screen Awareness Comprehensive Test Suite
 * 
 * Tests:
 * 1. WebRTCVoiceClient: VAD, energy calculations, barge-in cancellation, visualizer data feed.
 * 2. WebScreenAwareness: dHash perceptual hashing, adaptive rate controller, identical frame dropping, telemetry metrics.
 */

import { describe, it, beforeEach, expect } from 'vitest';
import { WebRTCVoiceClient } from '../audio/WebRTCVoiceClient';
import { WebScreenAwareness } from '../awareness/WebScreenAwareness';
import { AudioEnergyData } from '../audio/types';

// ==========================================
// Mock Environment Primitives for Headless Runner
// ==========================================

class MockMediaStreamTrack {
  public kind: string;
  public enabled = true;
  public readyState = 'live';
  public onended: (() => void) | null = null;

  constructor(kind: string) {
    this.kind = kind;
  }

  public stop(): void {
    this.readyState = 'ended';
    const handler = this.onended;
    this.onended = null;
    if (handler) handler();
  }

  public getSettings() {
    return {
      width: 1920,
      height: 1080,
      displaySurface: 'monitor',
    };
  }
}

class MockMediaStream {
  private tracks: MockMediaStreamTrack[];

  constructor(tracks?: MockMediaStreamTrack[]) {
    this.tracks = tracks || [new MockMediaStreamTrack('audio')];
  }

  public getTracks() {
    return this.tracks;
  }

  public getAudioTracks() {
    return this.tracks.filter((t) => t.kind === 'audio');
  }

  public getVideoTracks() {
    return this.tracks.filter((t) => t.kind === 'video');
  }
}

class MockRTCDataChannel {
  public readyState = 'open';
  public sentMessages: string[] = [];
  public onopen: (() => void) | null = null;
  public onmessage: ((e: { data: string }) => void) | null = null;
  public onerror: ((e: unknown) => void) | null = null;

  public send(data: string) {
    this.sentMessages.push(data);
  }

  public close() {
    this.readyState = 'closed';
  }
}

class MockRTCPeerConnection {
  public connectionState = 'connected';
  public iceConnectionState = 'connected';
  public onconnectionstatechange: (() => void) | null = null;
  public ontrack: ((e: { track: MockMediaStreamTrack; streams: MockMediaStream[] }) => void) | null = null;
  public ondatachannel: ((e: { channel: MockRTCDataChannel }) => void) | null = null;

  public createDataChannel(_name: string) {
    return new MockRTCDataChannel();
  }

  public addTrack(_track: unknown, _stream: unknown) {}

  public getTransceivers() {
    return [
      {
        sender: { track: { kind: 'audio' } },
        direction: 'sendrecv',
        setCodecPreferences: () => {},
      },
    ];
  }

  public async createOffer() {
    return { type: 'offer', sdp: 'v=0\r\nm=audio 50000 UDP/TLS/RTP/SAVPF 111\r\n' };
  }

  public async setLocalDescription(_desc: unknown) {}
  public async setRemoteDescription(_desc: unknown) {}

  public async getStats() {
    const map = new Map<string, unknown>();
    map.set('candidate-pair', {
      type: 'candidate-pair',
      state: 'succeeded',
      currentRoundTripTime: 0.035, // 35ms RTT
    });
    map.set('inbound-rtp', {
      type: 'inbound-rtp',
      kind: 'audio',
      jitter: 0.004,
      packetsLost: 2,
      packetsReceived: 98,
    });
    return map;
  }

  public restartIce() {}
  public close() {
    this.connectionState = 'closed';
  }
}

beforeEach(() => {
  // Mock HTMLMediaElement
  Object.defineProperty(globalThis, 'HTMLMediaElement', {
    value: class MockHTMLMediaElement {
      static HAVE_CURRENT_DATA = 2;
      static HAVE_ENOUGH_DATA = 4;
    },
    configurable: true,
    writable: true,
  });
  // Mock window/AudioContext
  Object.defineProperty(globalThis, 'window', {
    value: {
      AudioContext: class MockAudioContext {
        public state = 'running';
        public currentTime = 1.0;
        public destination = {};
        public createMediaStreamSource() {
          return { connect: () => {} };
        }
        public createAnalyser() {
          return {
            fftSize: 512,
            smoothingTimeConstant: 0.8,
            getFloatTimeDomainData: (arr: Float32Array) => {
              arr.fill(0.2);
            },
            getFloatFrequencyData: (arr: Float32Array) => {
              arr.fill(-30);
            },
          };
        }
        public createGain() {
          return {
            gain: {
              value: 1,
              setValueAtTime: () => {},
              cancelScheduledValues: () => {},
            },
            connect: () => {},
          };
        }
        public async resume() {}
        public async close() {}
      },
      devicePixelRatio: 2,
      requestAnimationFrame: (cb: FrameRequestCallback) => setTimeout(cb, 16) as unknown as number,
      cancelAnimationFrame: (id: number) => clearTimeout(id),
    },
    configurable: true,
    writable: true,
  });

  // Mock global Audio
  Object.defineProperty(globalThis, 'Audio', {
    value: class MockAudio {
      public autoplay = false;
      public currentTime = 0;
      public srcObject: unknown = null;
      public async play() {}
      public pause() {}
    },
    configurable: true,
    writable: true,
  });

  // Mock RTCPeerConnection
  Object.defineProperty(globalThis, 'RTCPeerConnection', {
    value: MockRTCPeerConnection,
    configurable: true,
    writable: true,
  });

  // Mock RTCRtpSender
  Object.defineProperty(globalThis, 'RTCRtpSender', {
    value: {
      getCapabilities: () => ({
        codecs: [{ mimeType: 'audio/opus' }, { mimeType: 'audio/PCMU' }],
      }),
    },
    configurable: true,
    writable: true,
  });

  // Mock navigator with mediaDevices
  Object.defineProperty(globalThis, 'navigator', {
    value: {
      mediaDevices: {
        getUserMedia: async () => new MockMediaStream([new MockMediaStreamTrack('audio')]),
        getDisplayMedia: async () =>
          new MockMediaStream([
            new MockMediaStreamTrack('video'),
            new MockMediaStreamTrack('audio'),
          ]),
      },
    },
    configurable: true,
    writable: true,
  });

  // Mock document
  Object.defineProperty(globalThis, 'document', {
    value: {
      createElement: (tag: string) => {
        if (tag === 'video') {
          return {
            autoplay: false,
            muted: false,
            playsInline: false,
            srcObject: null,
            videoWidth: 1920,
            videoHeight: 1080,
            readyState: 4,
            play: async () => {},
            pause: () => {},
            addEventListener: (evt: string, cb: () => void) => {
              if (evt === 'playing') setTimeout(cb, 5);
            },
            removeEventListener: () => {},
          };
        }
        if (tag === 'canvas') {
          return {
            width: 1280,
            height: 720,
            getContext: () => ({
              drawImage: () => {},
              getImageData: (_x: number, _y: number, w: number, h: number) => ({
                data: new Uint8ClampedArray(w * h * 4).fill(128),
              }),
            }),
            toBlob: (cb: (b: Blob | null) => void) => {
              cb(new Blob(['fake-image-bytes'], { type: 'image/webp' }));
            },
          };
        }
        return {};
      },
    },
    configurable: true,
    writable: true,
  });

  // Mock global fetch
  globalThis.fetch = async (url: RequestInfo | URL) => {
    const urlStr = String(url);
    if (urlStr.includes('/api/realtime/session')) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          sessionId: 'sess_test_123',
          model: 'gpt-4o-realtime',
          clientSecret: { value: 'ek_test_token', expiresAt: Date.now() + 3600000 },
          iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
          sdpAnswer: 'v=0\r\nm=audio 50000 UDP/TLS/RTP/SAVPF 111\r\n',
        }),
        text: async () => 'v=0\r\nm=audio 50000 UDP/TLS/RTP/SAVPF 111\r\n',
      } as Response;
    }
    return {
      ok: true,
      status: 200,
      json: async () => ({}),
      text: async () => '',
    } as Response;
  };
});

// ==========================================
// WebRTCVoiceClient Tests
// ==========================================

describe('WebRTCVoiceClient: Full-Duplex Real-Time Voice', () => {
  it('initializes with production default configurations', () => {
    const client = new WebRTCVoiceClient({
      profileId: 'test-profile-maya',
      voiceName: 'Aster-Warm',
    });

    expect(client.getState()).toBe('idle');
    expect(client.isMuted()).toBe(false);
    expect(client.isConnected()).toBe(false);
  });

  it('connects to voice broker and establishes WebRTC peer session', async () => {
    const client = new WebRTCVoiceClient({
      sessionEndpoint: '/api/realtime/session',
      profileId: 'profile-maya',
    });

    const stateChanges: string[] = [];
    client.on('stateChange', (state) => {
      stateChanges.push(state);
    });

    let sessionReceived = false;
    client.on('sessionReady', (session) => {
      sessionReceived = true;
      expect(session.sessionId).toBe('sess_test_123');
    });

    await client.connect();

    expect(sessionReceived).toBe(true);
    expect(client.getState()).toBe('listening');
    expect(client.isConnected()).toBe(true);
    expect(stateChanges).toContain('requesting_permissions');
    expect(stateChanges).toContain('connecting');
    expect(stateChanges).toContain('connected');
    expect(stateChanges).toContain('listening');

    await client.disconnect();
    expect(client.getState()).toBe('disconnected');
  });

  it('computes accurate audio energy and RMS decibels', async () => {
    const client = new WebRTCVoiceClient();
    await client.connect();

    const energy: AudioEnergyData = client.getEnergy();
    expect(energy.rms).toBeGreaterThanOrEqual(0);
    expect(energy.rms).toBeLessThanOrEqual(1.0);
    expect(energy.decibels).toBeGreaterThanOrEqual(-100);
    expect(energy.decibels).toBeLessThanOrEqual(0);
    expect(typeof energy.isSpeech).toBe('boolean');

    await client.disconnect();
  });

  it('barge-in immediately halts playback and sends response.cancel', async () => {
    const client = new WebRTCVoiceClient();
    await client.connect();

    let bargeInFired = false;
    client.on('bargeIn', (detail) => {
      bargeInFired = true;
      expect(detail.reason).toBe('manual_interrupt');
      expect(detail.timestamp).toBeGreaterThan(0);
    });

    // Manually simulate Aster speaking
    // @ts-expect-error accessing private state for unit verification
    client.isAsterSpeaking = true;
    // @ts-expect-error accessing private state
    client.transitionState('speaking');

    expect(client.getState()).toBe('speaking');

    // Trigger barge-in
    client.interrupt('manual_interrupt');

    expect(bargeInFired).toBe(true);
    expect(client.getState()).toBe('interrupted');

    // @ts-expect-error verifying private data channel sent response.cancel
    const dataChan = client.dataChannel as MockRTCDataChannel;
    expect(dataChan).toBeDefined();
    const cancelMsg = dataChan.sentMessages.find((m) => m.includes('response.cancel'));
    expect(cancelMsg).toBeDefined();

    await client.disconnect();
  });

  it('streams Float32Array visualizer waveform and frequency buffers', async () => {
    const client = new WebRTCVoiceClient();
    await client.connect();

    const visData = client.getVisualizerData();
    expect(visData.waveform).toBeInstanceOf(Float32Array);
    expect(visData.frequency).toBeInstanceOf(Float32Array);
    expect(visData.waveform.length).toBe(512);
    expect(visData.frequency.length).toBe(256);
    expect(visData.timestamp).toBeGreaterThan(0);

    await client.disconnect();
  });

  it('handles microphone mute and unmute toggling', async () => {
    const client = new WebRTCVoiceClient();
    await client.connect();

    client.setMuted(true);
    expect(client.isMuted()).toBe(true);

    client.setMuted(false);
    expect(client.isMuted()).toBe(false);

    await client.disconnect();
  });
});

// ==========================================
// WebScreenAwareness Tests
// ==========================================

describe('WebScreenAwareness: Continuous Screen Ingestion & Deduplication', () => {
  it('initializes with default options and idle state', () => {
    const awareness = new WebScreenAwareness({
      minFps: 1,
      maxFps: 15,
      changeThreshold: 0.035,
    });

    expect(awareness.getState()).toBe('idle');
    const metrics = awareness.getMetrics();
    expect(metrics.captureFps).toBe(0);
    expect(metrics.uploadFps).toBe(0);
    expect(metrics.totalFramesCaptured).toBe(0);
  });

  it('starts capture session and measures capture vs upload FPS', async () => {
    const awareness = new WebScreenAwareness({
      minFps: 1,
      maxFps: 15,
      changeThreshold: 0.035,
      keyframeIntervalMs: 5000,
    });

    const stateChanges: string[] = [];
    awareness.on('stateChange', (st) => stateChanges.push(st));

    let framesReceived = 0;
    awareness.on('frameCaptured', (frame) => {
      framesReceived++;
      expect(frame.id.startsWith('frame_')).toBe(true);
      expect(frame.sequence).toBeGreaterThan(0);
      expect(typeof frame.dHash).toBe('string');
      expect(frame.changeRatio).toBeGreaterThanOrEqual(0);
    });

    await awareness.start();
    expect(awareness.getState()).toBe('active');
    expect(stateChanges).toContain('requesting');
    expect(stateChanges).toContain('active');

    // Allow loop to capture frames
    await new Promise((r) => setTimeout(r, 60));

    expect(framesReceived).toBeGreaterThanOrEqual(1);
    const metrics = awareness.getMetrics();
    expect(metrics.totalFramesCaptured).toBeGreaterThanOrEqual(1);

    awareness.stop();
    expect(awareness.getState()).toBe('stopped');
  });

  it('computes accurate perceptual dHash and drops identical static frames', () => {
    const awareness = new WebScreenAwareness({
      changeThreshold: 0.04,
      hashResolution: 4, // 4x4 test grid
    });

    // Create synthetic pixel buffers
    const blackFrame = new Uint8ClampedArray(4 * 4 * 4).fill(0);
    const whiteFrame = new Uint8ClampedArray(4 * 4 * 4).fill(255);

    // @ts-expect-error invoking private computePerceptualDelta for unit verification
    const delta1 = awareness.computePerceptualDelta(blackFrame, 4);
    expect(delta1.changeRatio).toBe(1.0); // First frame is complete change
    expect(typeof delta1.dHash).toBe('string');

    // Set previous grid to black frame
    // @ts-expect-error setting private state
    awareness.previousLuminanceGrid = delta1.luminanceGrid;

    // Test identical black frame: difference should be exactly 0
    // @ts-expect-error invoking private computePerceptualDelta
    const delta2 = awareness.computePerceptualDelta(blackFrame, 4);
    expect(delta2.changeRatio).toBe(0.0); // Exactly identical!

    // Test white frame against black frame: difference should be 1.0 (100% change)
    // @ts-expect-error invoking private computePerceptualDelta
    const delta3 = awareness.computePerceptualDelta(whiteFrame, 4);
    expect(Math.round(delta3.changeRatio)).toBe(1);
  });

  it('handles pause and resume lifecycle transitions', async () => {
    const awareness = new WebScreenAwareness();
    await awareness.start();
    expect(awareness.getState()).toBe('active');

    awareness.pause();
    expect(awareness.getState()).toBe('paused');

    awareness.resume();
    expect(awareness.getState()).toBe('active');

    awareness.stop();
    expect(awareness.getState()).toBe('stopped');
  });

  it('detects native browser revocation when video track is ended', async () => {
    const awareness = new WebScreenAwareness();
    await awareness.start();

    let stopReason = '';
    awareness.on('stopped', (detail) => {
      stopReason = detail.reason;
    });

    const videoTrack = awareness.getVideoTrack();
    expect(videoTrack).toBeDefined();

    // Simulate user clicking "Stop sharing" in browser UI
    videoTrack?.stop();

    expect(stopReason).toBe('system_revocation');
    expect(awareness.getState()).toBe('stopped');
  });
});
