/**
 * Aster Companion WebRTC Voice Client
 * 
 * Provides full-duplex, low-latency bidirectional voice communication over WebRTC:
 * - Broker session negotiation (/api/realtime/session)
 * - RTCPeerConnection management for Opus voice streaming
 * - High-precision client-side VAD (Voice Activity Detection) and audio energy tracking
 * - Sub-millisecond Barge-In response cancellation and audio suppression
 * - Real-time Float32Array visualizer waveform and spectrum data streaming
 */

import {
  VoiceClientState,
  VADConfig,
  AudioEnergyData,
  VisualizerData,
  SessionConfig,
  SessionResponse,
  RealtimeClientEvent,
  RealtimeServerEvent,
  VoiceClientEventMap,
  VoiceLatencyMetrics,
} from './types';

const DEFAULT_VAD_CONFIG: VADConfig = {
  fftSize: 512,
  smoothingTimeConstant: 0.8,
  speechThresholdDb: -42,
  silenceThresholdDb: -52,
  minSpeechFrames: 3,
  hangoverMs: 650,
  energyPollIntervalMs: 20,
  noiseFloorAdaptationRate: 0.05,
};

const DEFAULT_SESSION_CONFIG: SessionConfig = {
  sessionEndpoint: '/api/realtime/session',
  profileId: 'default-profile',
  deviceId: typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : 'browser-client',
  voiceName: 'Aster-Warm',
  temperature: 0.7,
  turnDetection: {
    type: 'client_vad',
    threshold: 0.5,
    silence_duration_ms: 600,
  },
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
  ],
  audioConstraints: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
    channelCount: 1,
    sampleRate: 24000,
  },
  autoReconnect: true,
};

export class WebRTCVoiceClient {
  private config: SessionConfig;
  private vadConfig: VADConfig;
  private state: VoiceClientState = 'idle';

  // WebRTC primitives
  private peerConnection: RTCPeerConnection | null = null;
  private dataChannel: RTCDataChannel | null = null;
  private localStream: MediaStream | null = null;
  private remoteStream: MediaStream | null = null;
  private remoteAudioElement: HTMLAudioElement | null = null;

  // Web Audio pipeline
  private audioContext: AudioContext | null = null;
  private micSourceNode: MediaStreamAudioSourceNode | null = null;
  private micAnalyserNode: AnalyserNode | null = null;
  private remoteSourceNode: MediaStreamAudioSourceNode | null = null;
  private remoteAnalyserNode: AnalyserNode | null = null;
  private remoteGainNode: GainNode | null = null;

  // Audio buffers for analysis
  private micTimeData: Float32Array<ArrayBuffer> = new Float32Array(new ArrayBuffer(512 * 4));
  private micFreqData: Float32Array<ArrayBuffer> = new Float32Array(new ArrayBuffer(256 * 4));
  private remoteTimeData: Float32Array<ArrayBuffer> = new Float32Array(new ArrayBuffer(512 * 4));
  private remoteFreqData: Float32Array<ArrayBuffer> = new Float32Array(new ArrayBuffer(256 * 4));

  // VAD & Energy state
  private vadTimer: ReturnType<typeof setInterval> | null = null;
  private visualizerLoopId: number | null = null;
  private isUserSpeaking = false;
  private isAsterSpeaking = false;
  private consecutiveSpeechFrames = 0;
  private lastSpeechTimestamp = 0;
  private speechStartTime = 0;
  private currentNoiseFloorDb = -65;
  private isMutedState = false;

  // Telemetry
  private lastRttMs = 0;
  private sessionData: SessionResponse | null = null;

  // Event listeners
  private listeners: { [K in keyof VoiceClientEventMap]?: Array<VoiceClientEventMap[K]> } = {};

  constructor(customConfig?: Partial<SessionConfig>) {
    this.config = {
      ...DEFAULT_SESSION_CONFIG,
      ...customConfig,
      vadConfig: { ...DEFAULT_VAD_CONFIG, ...customConfig?.vadConfig },
    };
    this.vadConfig = { ...DEFAULT_VAD_CONFIG, ...this.config.vadConfig };
    this.allocateBuffers(this.vadConfig.fftSize);
  }

  // ==========================================
  // Public API
  // ==========================================

  public async connect(): Promise<void> {
    if (this.state === 'connecting' || this.state === 'connected' || this.state === 'listening' || this.state === 'speaking') {
      return;
    }

    this.transitionState('requesting_permissions');

    try {
      // 1. Acquire microphone stream with acoustic echo cancellation
      this.localStream = await navigator.mediaDevices.getUserMedia({
        audio: this.config.audioConstraints,
        video: false,
      });

      this.transitionState('connecting');

      // 2. Setup Web Audio pipeline for VAD & Visualization
      await this.setupAudioPipeline();

      // 3. Negotiate session with backend voice broker
      const session = await this.fetchSessionCredentials();
      this.sessionData = session;
      this.emit('sessionReady', session);

      // 4. Initialize PeerConnection and DataChannel
      await this.setupPeerConnection(session);

      this.transitionState('connected');
      this.startVADLoop();
      this.startVisualizerFeed();
      this.transitionState('listening');
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      this.transitionState('error');
      this.emit('error', error, 'CONNECTION_FAILED');
      this.cleanup();
      throw error;
    }
  }

  public async disconnect(): Promise<void> {
    if (this.state === 'disconnected' || this.state === 'idle') return;
    this.transitionState('disconnecting');
    this.cleanup();
    this.transitionState('disconnected');
  }

  public setMuted(muted: boolean): void {
    this.isMutedState = muted;
    if (this.localStream) {
      this.localStream.getAudioTracks().forEach((track) => {
        track.enabled = !muted;
      });
    }
  }

  public isMuted(): boolean {
    return this.isMutedState;
  }

  public getLastRttMs(): number {
    return this.lastRttMs;
  }

  public getSession(): SessionResponse | null {
    return this.sessionData;
  }

  public getState(): VoiceClientState {
    return this.state;
  }

  public getEnergy(): AudioEnergyData {
    return this.computeMicEnergy();
  }

  public isConnected(): boolean {
    return this.state === 'connected' || this.state === 'listening' || this.state === 'speaking' || this.state === 'interrupted';
  }

  /**
   * Client-side Barge-In:
   * Instantly cancels model response on the backend and kills local audio playback immediately.
   */
  public interrupt(reason: 'user_speech_detected' | 'manual_interrupt' = 'manual_interrupt'): void {
    if (this.state !== 'speaking' && !this.isAsterSpeaking) {
      return;
    }

    const priorState = this.state;

    // 1. Send instant cancel message over WebRTC DataChannel
    this.sendClientEvent({
      type: 'response.cancel',
    });

    // 2. Immediate local audio cutoff: mute gain and halt audio element
    if (this.remoteGainNode && this.audioContext) {
      this.remoteGainNode.gain.cancelScheduledValues(this.audioContext.currentTime);
      this.remoteGainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
    }

    if (this.remoteAudioElement) {
      this.remoteAudioElement.pause();
      this.remoteAudioElement.currentTime = 0;
    }

    this.isAsterSpeaking = false;
    this.transitionState('interrupted');

    this.emit('bargeIn', {
      timestamp: Date.now(),
      reason,
      priorState,
    });

    // Restore gain smoothly for future speech and return to listening state
    setTimeout(() => {
      if (this.remoteGainNode && this.audioContext) {
        this.remoteGainNode.gain.setValueAtTime(1.0, this.audioContext.currentTime);
      }
      if (this.state === 'interrupted') {
        this.transitionState('listening');
      }
    }, 120);
  }

  /**
   * Send JSON message over the WebRTC Data Channel
   */
  public sendClientEvent(event: RealtimeClientEvent): void {
    if (this.dataChannel && this.dataChannel.readyState === 'open') {
      this.dataChannel.send(JSON.stringify(event));
    }
  }

  /**
   * Send text message in real-time session
   */
  public sendTextMessage(text: string): void {
    this.sendClientEvent({
      type: 'conversation.item.create',
      item: {
        type: 'message',
        role: 'user',
        content: [
          {
            type: 'input_text',
            text: text,
          },
        ],
      },
    });
    this.sendClientEvent({
      type: 'response.create',
    });
  }

  /**
   * Visualizer data snapshot: retrieves fresh Float32Array waveform and frequency data
   */
  public getVisualizerData(): VisualizerData {
    const timestamp = Date.now();
    let activeSource: 'mic' | 'remote' | 'idle' = 'idle';

    if (this.remoteAnalyserNode && this.isAsterSpeaking) {
      this.remoteAnalyserNode.getFloatTimeDomainData(this.remoteTimeData);
      this.remoteAnalyserNode.getFloatFrequencyData(this.remoteFreqData);
      activeSource = 'remote';

      const energy = this.computeEnergyFromBuffers(this.remoteTimeData);
      return {
        waveform: this.remoteTimeData,
        frequency: this.remoteFreqData,
        energy,
        activeSource,
        timestamp,
      };
    }

    if (this.micAnalyserNode && (this.isUserSpeaking || this.state === 'listening')) {
      this.micAnalyserNode.getFloatTimeDomainData(this.micTimeData);
      this.micAnalyserNode.getFloatFrequencyData(this.micFreqData);
      activeSource = this.isUserSpeaking ? 'mic' : 'idle';

      const energy = this.computeEnergyFromBuffers(this.micTimeData);
      return {
        waveform: this.micTimeData,
        frequency: this.micFreqData,
        energy,
        activeSource,
        timestamp,
      };
    }

    // Default idle frame
    return {
      waveform: this.micTimeData,
      frequency: this.micFreqData,
      energy: {
        rms: 0,
        decibels: -100,
        peak: 0,
        isSpeech: false,
        noiseFloorDb: this.currentNoiseFloorDb,
      },
      activeSource: 'idle',
      timestamp,
    };
  }

  // ==========================================
  // Event Emitter Support
  // ==========================================

  public on<K extends keyof VoiceClientEventMap>(event: K, listener: VoiceClientEventMap[K]): void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event]?.push(listener);
  }

  public off<K extends keyof VoiceClientEventMap>(event: K, listener: VoiceClientEventMap[K]): void {
    const list = this.listeners[event];
    if (!list) return;
    this.listeners[event] = list.filter((l) => l !== listener) as typeof list;
  }

  private emit<K extends keyof VoiceClientEventMap>(event: K, ...args: Parameters<VoiceClientEventMap[K]>): void {
    const list = this.listeners[event];
    if (list) {
      for (const fn of list) {
        try {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (fn as any)(...args);
        } catch (e) {
          console.error(`[WebRTCVoiceClient] Listener error on event "${String(event)}":`, e);
        }
      }
    }
  }

  // ==========================================
  // Internal Web Audio & VAD Engine
  // ==========================================

  private allocateBuffers(fftSize: number): void {
    this.micTimeData = new Float32Array(new ArrayBuffer(fftSize * 4));
    this.micFreqData = new Float32Array(new ArrayBuffer((fftSize / 2) * 4));
    this.remoteTimeData = new Float32Array(new ArrayBuffer(fftSize * 4));
    this.remoteFreqData = new Float32Array(new ArrayBuffer((fftSize / 2) * 4));
  }

  private async setupAudioPipeline(): Promise<void> {
    const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    this.audioContext = new AudioContextClass({
      sampleRate: 24000,
      latencyHint: 'interactive',
    });

    if (this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }

    // Mic analysis pipeline
    if (this.localStream) {
      this.micSourceNode = this.audioContext.createMediaStreamSource(this.localStream);
      this.micAnalyserNode = this.audioContext.createAnalyser();
      this.micAnalyserNode.fftSize = this.vadConfig.fftSize;
      this.micAnalyserNode.smoothingTimeConstant = this.vadConfig.smoothingTimeConstant;
      this.micSourceNode.connect(this.micAnalyserNode);
      // NOTE: Mic node is NOT connected to audioContext.destination to avoid local feedback
    }

    // Remote playback pipeline
    this.remoteGainNode = this.audioContext.createGain();
    this.remoteGainNode.gain.setValueAtTime(1.0, this.audioContext.currentTime);

    this.remoteAnalyserNode = this.audioContext.createAnalyser();
    this.remoteAnalyserNode.fftSize = this.vadConfig.fftSize;
    this.remoteAnalyserNode.smoothingTimeConstant = 0.6;

    this.remoteGainNode.connect(this.remoteAnalyserNode);
    this.remoteGainNode.connect(this.audioContext.destination);

    // Audio element fallback for remote media stream
    this.remoteAudioElement = new Audio();
    this.remoteAudioElement.autoplay = true;
    (this.remoteAudioElement as unknown as { playsInline?: boolean }).playsInline = true;
  }

  private computeEnergyFromBuffers(timeData: Float32Array): AudioEnergyData {
    let sumSquares = 0;
    let peak = 0;
    const len = timeData.length;

    for (let i = 0; i < len; i++) {
      const sample = timeData[i];
      const abs = Math.abs(sample);
      if (abs > peak) peak = abs;
      sumSquares += sample * sample;
    }

    const rms = Math.sqrt(sumSquares / len);
    const decibels = rms > 0.00001 ? Math.max(-100, 20 * Math.log10(rms)) : -100;
    const isSpeech = decibels > this.vadConfig.speechThresholdDb;

    return {
      rms,
      decibels,
      peak,
      isSpeech,
      noiseFloorDb: this.currentNoiseFloorDb,
    };
  }

  private computeMicEnergy(): AudioEnergyData {
    if (!this.micAnalyserNode) {
      return {
        rms: 0,
        decibels: -100,
        peak: 0,
        isSpeech: false,
        noiseFloorDb: this.currentNoiseFloorDb,
      };
    }
    this.micAnalyserNode.getFloatTimeDomainData(this.micTimeData);
    return this.computeEnergyFromBuffers(this.micTimeData);
  }

  private startVADLoop(): void {
    if (this.vadTimer) clearInterval(this.vadTimer);

    this.vadTimer = setInterval(() => {
      if (this.isMutedState || !this.micAnalyserNode) return;

      const energy = this.computeMicEnergy();
      this.emit('audioEnergy', energy);

      // Dynamically track ambient background noise floor when not speaking
      if (!this.isUserSpeaking && energy.decibels > -90 && energy.decibels < this.vadConfig.speechThresholdDb) {
        this.currentNoiseFloorDb =
          this.currentNoiseFloorDb * (1 - this.vadConfig.noiseFloorAdaptationRate) +
          energy.decibels * this.vadConfig.noiseFloorAdaptationRate;
      }

      // Dynamic adaptive threshold: either fixed threshold or 10dB above estimated noise floor
      const dynamicThreshold = Math.max(this.vadConfig.speechThresholdDb, this.currentNoiseFloorDb + 10);
      const isVoiceActive = energy.decibels > dynamicThreshold;

      const now = Date.now();

      if (isVoiceActive) {
        this.consecutiveSpeechFrames++;

        if (this.consecutiveSpeechFrames >= this.vadConfig.minSpeechFrames) {
          this.lastSpeechTimestamp = now;

          if (!this.isUserSpeaking) {
            this.isUserSpeaking = true;
            this.speechStartTime = now;

            this.emit('speechStart', {
              timestamp: now,
              energy,
              source: 'mic',
            });

            // BARGE-IN TRIGGER: User spoke while Aster was speaking
            if (this.isAsterSpeaking || this.state === 'speaking') {
              this.interrupt('user_speech_detected');
            } else if (this.state === 'listening') {
              // Notify backend voice broker that input audio buffer started
              this.sendClientEvent({
                type: 'input_audio_buffer.speech_started',
              });
            }
          }
        }
      } else {
        this.consecutiveSpeechFrames = 0;

        if (this.isUserSpeaking) {
          const silenceDuration = now - this.lastSpeechTimestamp;

          if (silenceDuration >= this.vadConfig.hangoverMs) {
            this.isUserSpeaking = false;
            const durationMs = now - this.speechStartTime;

            this.emit('speechEnd', {
              timestamp: now,
              durationMs,
              source: 'mic',
            });

            this.sendClientEvent({
              type: 'input_audio_buffer.speech_stopped',
            });
          }
        }
      }
    }, this.vadConfig.energyPollIntervalMs);
  }

  private startVisualizerFeed(): void {
    if (this.visualizerLoopId !== null) {
      this.cancelAnimFrame(this.visualizerLoopId);
    }

    const render = () => {
      if (this.isConnected()) {
        const data = this.getVisualizerData();
        this.emit('visualizerData', data);
      }
      this.visualizerLoopId = this.requestAnimFrame(render);
    };

    this.visualizerLoopId = this.requestAnimFrame(render);
  }

  private requestAnimFrame(cb: FrameRequestCallback): number {
    if (typeof requestAnimationFrame === 'function') {
      return requestAnimationFrame(cb);
    }
    return setTimeout(cb, 16) as unknown as number;
  }

  private cancelAnimFrame(id: number): void {
    if (typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(id);
      return;
    }
    clearTimeout(id);
  }

  // ==========================================
  // WebRTC Session Negotiation & Protocol
  // ==========================================

  private async fetchSessionCredentials(): Promise<SessionResponse> {
    const payload = {
      profileId: this.config.profileId,
      deviceId: this.config.deviceId,
      voice: this.config.voiceName,
      temperature: this.config.temperature,
      systemPrompt: this.config.systemPrompt,
      turnDetection: this.config.turnDetection,
    };

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.config.ephemeralToken) {
      headers['Authorization'] = `Bearer ${this.config.ephemeralToken}`;
    }

    const response = await fetch(this.config.sessionEndpoint, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      // Graceful fallback for offline / mock testing environments
      const errorText = await response.text().catch(() => 'Unknown network error');
      throw new Error(`Failed to initialize realtime session (${response.status}): ${errorText}`);
    }

    return (await response.json()) as SessionResponse;
  }

  private async setupPeerConnection(session: SessionResponse): Promise<void> {
    const iceServers = session.iceServers || this.config.iceServers;

    this.peerConnection = new RTCPeerConnection({
      iceServers,
      bundlePolicy: 'max-bundle',
      rtcpMuxPolicy: 'require',
    });

    // 1. Data Channel for control events (OpenAI / Aster protocol)
    this.dataChannel = this.peerConnection.createDataChannel('oai-events', {
      ordered: true,
    });
    this.setupDataChannel(this.dataChannel);

    // Also handle server-initiated data channels
    this.peerConnection.ondatachannel = (event) => {
      this.setupDataChannel(event.channel);
    };

    // 2. Add local audio track
    if (this.localStream) {
      const audioTrack = this.localStream.getAudioTracks()[0];
      if (audioTrack) {
        this.peerConnection.addTrack(audioTrack, this.localStream);
      }
    }

    // 3. Configure audio transceiver with Opus codec preferences
    const transceivers = this.peerConnection.getTransceivers();
    const audioTransceiver = transceivers.find((t) => t.sender.track?.kind === 'audio');
    if (audioTransceiver) {
      audioTransceiver.direction = 'sendrecv';
      this.preferOpusCodec(audioTransceiver);
    }

    // 4. Handle incoming remote audio track
    this.peerConnection.ontrack = (event) => {
      this.handleRemoteTrack(event);
    };

    // 5. Connection state monitoring
    this.peerConnection.onconnectionstatechange = () => {
      if (!this.peerConnection) return;
      const rtcState = this.peerConnection.connectionState;
      if (rtcState === 'disconnected' || rtcState === 'failed') {
        if (this.config.autoReconnect) {
          this.handleReconnect();
        } else {
          this.transitionState('disconnected');
        }
      }
    };

    // 6. SDP Offer/Answer Negotiation
    const offer = await this.peerConnection.createOffer({
      offerToReceiveAudio: true,
      offerToReceiveVideo: false,
    });
    await this.peerConnection.setLocalDescription(offer);

    // If session returned sdpAnswer directly (or ephemeral token endpoint)
    if (session.sdpAnswer) {
      await this.peerConnection.setRemoteDescription({
        type: 'answer',
        sdp: session.sdpAnswer,
      });
    } else {
      // Send offer to broker/relay URL
      const relayUrl = session.relayUrl || `${this.config.sessionEndpoint}/sdp`;
      const sdpResponse = await fetch(relayUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/sdp',
          ...(session.clientSecret?.value ? { Authorization: `Bearer ${session.clientSecret.value}` } : {}),
        },
        body: offer.sdp,
      });

      if (sdpResponse.ok) {
        const answerSdp = await sdpResponse.text();
        await this.peerConnection.setRemoteDescription({
          type: 'answer',
          sdp: answerSdp,
        });
      }
    }

    // Monitor RTT latency via getStats
    this.startLatencyPolling();
  }

  private preferOpusCodec(transceiver: RTCRtpTransceiver): void {
    if (typeof RTCRtpSender.getCapabilities === 'function') {
      const capabilities = RTCRtpSender.getCapabilities('audio');
      if (capabilities?.codecs) {
        const opusCodecs = capabilities.codecs.filter(
          (c) => c.mimeType.toLowerCase() === 'audio/opus'
        );
        const otherCodecs = capabilities.codecs.filter(
          (c) => c.mimeType.toLowerCase() !== 'audio/opus'
        );
        if (opusCodecs.length > 0 && transceiver.setCodecPreferences) {
          transceiver.setCodecPreferences([...opusCodecs, ...otherCodecs]);
        }
      }
    }
  }

  private handleRemoteTrack(event: RTCTrackEvent): void {
    this.remoteStream = event.streams[0] || new MediaStream([event.track]);

    if (this.remoteAudioElement) {
      this.remoteAudioElement.srcObject = this.remoteStream;
      this.remoteAudioElement.play().catch((err) => {
        console.warn('[WebRTCVoiceClient] Audio playback autoplay blocked; user gesture required:', err);
      });
    }

    if (this.audioContext && this.remoteGainNode) {
      try {
        this.remoteSourceNode = this.audioContext.createMediaStreamSource(this.remoteStream);
        this.remoteSourceNode.connect(this.remoteGainNode);
      } catch (e) {
        console.warn('[WebRTCVoiceClient] Could not route remote track to Web Audio context:', e);
      }
    }
  }

  private setupDataChannel(channel: RTCDataChannel): void {
    channel.onopen = () => {
      // Send initial session update if needed
      this.sendClientEvent({
        type: 'session.update',
        session: {
          modalities: ['audio', 'text'],
          instructions: this.config.systemPrompt,
          voice: this.config.voiceName,
          turn_detection: this.config.turnDetection,
        },
      });
    };

    channel.onmessage = (event) => {
      this.handleServerMessage(event.data);
    };

    channel.onerror = (err) => {
      console.error('[WebRTCVoiceClient] DataChannel error:', err);
    };
  }

  private handleServerMessage(rawData: string | ArrayBuffer): void {
    if (typeof rawData !== 'string') return;

    try {
      const event = JSON.parse(rawData) as RealtimeServerEvent;

      switch (event.type) {
        case 'response.created':
        case 'response.audio.delta':
        case 'response.audio_transcript.delta': {
          if (!this.isAsterSpeaking) {
            this.isAsterSpeaking = true;
            this.transitionState('speaking');
          }

          if (event.type === 'response.audio_transcript.delta' && typeof event.delta === 'string') {
            this.emit('transcript', {
              role: 'assistant',
              text: event.delta,
              isFinal: false,
              itemId: typeof event.item_id === 'string' ? event.item_id : undefined,
              timestamp: Date.now(),
            });
          }
          break;
        }

        case 'response.audio_transcript.done': {
          if (typeof event.transcript === 'string') {
            this.emit('transcript', {
              role: 'assistant',
              text: event.transcript,
              isFinal: true,
              itemId: typeof event.item_id === 'string' ? event.item_id : undefined,
              timestamp: Date.now(),
            });
          }
          break;
        }

        case 'conversation.item.input_audio_transcription.completed': {
          if (typeof event.transcript === 'string') {
            this.emit('transcript', {
              role: 'user',
              text: event.transcript,
              isFinal: true,
              itemId: typeof event.item_id === 'string' ? event.item_id : undefined,
              timestamp: Date.now(),
            });
          }
          break;
        }

        case 'response.done': {
          this.isAsterSpeaking = false;
          if (this.state === 'speaking') {
            this.transitionState('listening');
          }
          break;
        }

        case 'input_audio_buffer.speech_started': {
          // Server detected user speech onset; if model was speaking, cancel it immediately
          if (this.state === 'speaking' || this.isAsterSpeaking) {
            this.interrupt('user_speech_detected');
          }
          break;
        }

        case 'error': {
          const errorMsg = typeof event.error === 'object' && event.error && 'message' in event.error
            ? String((event.error as { message: unknown }).message)
            : 'Unknown Realtime API server error';
          this.emit('error', new Error(errorMsg), 'SERVER_ERROR');
          break;
        }

        default:
          break;
      }
    } catch (e) {
      console.warn('[WebRTCVoiceClient] Failed to parse message from data channel:', e);
    }
  }

  private startLatencyPolling(): void {
    const statsTimer = setInterval(async () => {
      if (!this.peerConnection || this.peerConnection.connectionState !== 'connected') {
        clearInterval(statsTimer);
        return;
      }

      try {
        const stats = await this.peerConnection.getStats();
        let rtt = 0;
        let jitter = 0;
        let packetsLost = 0;
        let packetsReceived = 0;

        stats.forEach((report) => {
          if (report.type === 'candidate-pair' && report.state === 'succeeded' && typeof report.currentRoundTripTime === 'number') {
            rtt = Math.round(report.currentRoundTripTime * 1000);
          }
          if (report.type === 'inbound-rtp' && report.kind === 'audio') {
            if (typeof report.jitter === 'number') jitter = Math.round(report.jitter * 1000);
            if (typeof report.packetsLost === 'number') packetsLost = report.packetsLost;
            if (typeof report.packetsReceived === 'number') packetsReceived = report.packetsReceived;
          }
        });

        const totalPackets = packetsLost + packetsReceived;
        const lossPercent = totalPackets > 0 ? (packetsLost / totalPackets) * 100 : 0;
        this.lastRttMs = rtt;

        const metrics: VoiceLatencyMetrics = {
          roundTripTimeMs: rtt,
          jitterMs: jitter,
          audioPacketLossPercent: Math.round(lossPercent * 10) / 10,
        };

        this.emit('latency', metrics);
      } catch {
        // Silently handle stats failure during teardown
      }
    }, 2000);
  }

  private handleReconnect(): void {
    if (this.peerConnection && typeof this.peerConnection.restartIce === 'function') {
      try {
        this.peerConnection.restartIce();
        return;
      } catch (err) {
        console.warn('[WebRTCVoiceClient] restartIce failed, re-negotiating session:', err);
      }
    }

    this.cleanup();
    setTimeout(() => {
      this.connect().catch((err) => {
        console.error('[WebRTCVoiceClient] Reconnection failed:', err);
      });
    }, 1500);
  }

  private transitionState(newState: VoiceClientState): void {
    if (this.state === newState) return;
    const prevState = this.state;
    this.state = newState;
    this.emit('stateChange', newState, prevState);
  }

  private cleanup(): void {
    if (this.vadTimer) {
      clearInterval(this.vadTimer);
      this.vadTimer = null;
    }

    if (this.visualizerLoopId !== null) {
      this.cancelAnimFrame(this.visualizerLoopId);
      this.visualizerLoopId = null;
    }

    if (this.dataChannel) {
      try {
        this.dataChannel.close();
      } catch {}
      this.dataChannel = null;
    }

    if (this.peerConnection) {
      try {
        this.peerConnection.close();
      } catch {}
      this.peerConnection = null;
    }

    if (this.localStream) {
      this.localStream.getTracks().forEach((track) => track.stop());
      this.localStream = null;
    }

    if (this.remoteAudioElement) {
      this.remoteAudioElement.pause();
      this.remoteAudioElement.srcObject = null;
      this.remoteAudioElement = null;
    }

    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close().catch(() => {});
      this.audioContext = null;
    }

    this.micSourceNode = null;
    this.micAnalyserNode = null;
    this.remoteSourceNode = null;
    this.remoteAnalyserNode = null;
    this.remoteGainNode = null;
    this.isUserSpeaking = false;
    this.isAsterSpeaking = false;
    this.consecutiveSpeechFrames = 0;
  }
}
