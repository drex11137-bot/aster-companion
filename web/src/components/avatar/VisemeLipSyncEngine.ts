/**
 * VisemeLipSyncEngine.ts
 * Aster Companion - Procedural Viseme & Lip-Sync Animation Engine
 *
 * Implements real-time frequency-band decomposition (FFT) to drive realistic
 * mouth morph targets (jawOpen, mouthRound, mouthSmile, mouthStretch, lipPucker)
 * combined with natural idle biometrics (blinking, breathing, micro-saccades, head drift).
 */

import { VoiceTone } from '../../types';

export interface VisemeWeights {
  jawOpen: number;       // 0.0 to 1.0 (vertical mouth opening)
  mouthRound: number;    // 0.0 to 1.0 (lip rounding for 'O', 'U')
  mouthSmile: number;    // 0.0 to 1.0 (lip corners pulled wide and up)
  mouthStretch: number;  // 0.0 to 1.0 (horizontal spread for 'E', 'I', fricatives)
  lipPucker: number;     // 0.0 to 1.0 (protruding lips)
  upperLipRaise: number; // 0.0 to 1.0
  lowerLipDepress: number; // 0.0 to 1.0
}

export interface AvatarExpressionState {
  visemes: VisemeWeights;
  blinkLeft: number;      // 0.0 (open) to 1.0 (fully closed)
  blinkRight: number;     // 0.0 to 1.0
  breathScale: number;    // ~0.985 to 1.015
  headPitch: number;      // Radians (-0.05 to +0.05)
  headYaw: number;        // Radians (-0.08 to +0.08)
  headRoll: number;       // Radians (-0.03 to +0.03)
  eyeGazeX: number;       // Normalized (-1.0 to +1.0)
  eyeGazeY: number;       // Normalized (-1.0 to +1.0)
  audioEnergy: number;    // 0.0 to 1.0
  isSpeaking: boolean;
}

export type VisemeListener = (state: AvatarExpressionState) => void;

export class VisemeLipSyncEngine {
  private audioContext: AudioContext | null = null;
  private analyserNode: AnalyserNode | null = null;
  private sourceNode: MediaStreamAudioSourceNode | MediaElementAudioSourceNode | null = null;
  private freqData: Uint8Array<ArrayBuffer> | null = null;

  // Smoothing states (Exponential moving average)
  private currentJawOpen = 0;
  private currentMouthRound = 0;
  private currentMouthSmile = 0.15; // default gentle natural smile
  private currentMouthStretch = 0;
  private currentEnergy = 0;

  // Biometrics & Idle state
  private lastBlinkTime = performance.now();
  private nextBlinkInterval = 3500 + Math.random() * 2500;
  private isBlinking = false;
  private blinkProgress = 0; // 0 to 1
  private currentBlinkWeight = 0;

  private lastSaccadeTime = performance.now();
  private nextSaccadeInterval = 2000 + Math.random() * 2000;
  private targetGazeX = 0;
  private targetGazeY = 0;
  private currentGazeX = 0;
  private currentGazeY = 0;

  private respirationPhase = 0;
  private headWanderPhase = Math.random() * 100;

  // Animation Loop
  private animFrameId: number | null = null;
  private listeners: Set<VisemeListener> = new Set();
  private isRunning = false;

  // Synthetic speech simulation
  private isSimulatingSpeech = false;
  private speechTimeout: number | null = null;
  private synthGainNode: GainNode | null = null;
  private synthOscillators: OscillatorNode[] = [];

  constructor() {
    // Initial state initialized
  }

  /**
   * Initializes or returns the shared AudioContext
   */
  public async ensureAudioContext(): Promise<AudioContext> {
    if (!this.audioContext) {
      const AudioCtxClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.audioContext = new AudioCtxClass();
    }
    if (this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }
    return this.audioContext;
  }

  /**
   * Attach an existing WebAudio AnalyserNode (e.g. from WebRTC client)
   */
  public attachAnalyser(analyser: AnalyserNode): void {
    this.analyserNode = analyser;
    this.analyserNode.fftSize = 512;
    this.analyserNode.smoothingTimeConstant = 0.6;
    this.freqData = new Uint8Array(new ArrayBuffer(this.analyserNode.frequencyBinCount));
    if (!this.isRunning) {
      this.start();
    }
  }

  /**
   * Connect an incoming microphone or audio MediaStream
   */
  public async connectAudioStream(stream: MediaStream): Promise<void> {
    const ctx = await this.ensureAudioContext();
    if (this.sourceNode) {
      try {
        this.sourceNode.disconnect();
      } catch {
        // Ignored
      }
    }
    this.sourceNode = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 512;
    analyser.smoothingTimeConstant = 0.6;
    this.sourceNode.connect(analyser);
    this.attachAnalyser(analyser);
  }

  /**
   * Connect an HTMLAudioElement (e.g. TTS player or audio file)
   */
  public async connectAudioElement(audioEl: HTMLAudioElement): Promise<void> {
    const ctx = await this.ensureAudioContext();
    if (this.sourceNode) {
      try {
        this.sourceNode.disconnect();
      } catch {
        // Ignored
      }
    }
    this.sourceNode = ctx.createMediaElementSource(audioEl);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 512;
    analyser.smoothingTimeConstant = 0.6;
    this.sourceNode.connect(analyser);
    analyser.connect(ctx.destination);
    this.attachAnalyser(analyser);
  }

  /**
   * Subscribe to expression updates (60fps)
   */
  public subscribe(listener: VisemeListener): () => void {
    this.listeners.add(listener);
    if (!this.isRunning) {
      this.start();
    }
    return () => {
      this.listeners.delete(listener);
      if (this.listeners.size === 0) {
        this.stop();
      }
    };
  }

  /**
   * Start animation and processing loop
   */
  public start(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    this.lastBlinkTime = performance.now();
    this.lastSaccadeTime = performance.now();

    const loop = (timestamp: number) => {
      if (!this.isRunning) return;
      this.update(timestamp);
      this.animFrameId = requestAnimationFrame(loop);
    };

    this.animFrameId = requestAnimationFrame(loop);
  }

  /**
   * Stop processing loop
   */
  public stop(): void {
    this.isRunning = false;
    if (this.animFrameId !== null) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
    this.stopSpeechSimulation();
  }

  /**
   * Play procedural synthetic speech phrase for studio preview
   */
  public async simulateSpeech(
    phrase: string = 'Hello! I am Aster, your companion. It is wonderful to meet you.',
    durationMs: number = 3200,
    voiceTone: VoiceTone = 'Warm voice'
  ): Promise<void> {
    this.stopSpeechSimulation();
    this.isSimulatingSpeech = true;

    // Use Web Speech API if supported in browser
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(phrase);
      
      // Match voice parameters
      switch (voiceTone) {
        case 'Warm voice':
          utterance.pitch = 1.05;
          utterance.rate = 0.95;
          break;
        case 'Calm':
          utterance.pitch = 0.92;
          utterance.rate = 0.88;
          break;
        case 'Energetic':
          utterance.pitch = 1.15;
          utterance.rate = 1.1;
          break;
        case 'Playful':
          utterance.pitch = 1.25;
          utterance.rate = 1.05;
          break;
      }

      // Try selecting a natural sounding female voice if available
      const voices = window.speechSynthesis.getVoices();
      const naturalVoice = voices.find(
        (v) =>
          v.lang.startsWith('en') &&
          (v.name.includes('Natural') ||
            v.name.includes('Samantha') ||
            v.name.includes('Google') ||
            v.name.includes('Victoria') ||
            v.name.includes('Zira'))
      );
      if (naturalVoice) utterance.voice = naturalVoice;

      utterance.onend = () => {
        this.isSimulatingSpeech = false;
      };
      utterance.onerror = () => {
        this.isSimulatingSpeech = false;
      };

      window.speechSynthesis.speak(utterance);
    }

    // Also spin up a procedural harmonic audio waveform through WebAudio
    // so frequency analysis produces real physical mouth movements
    try {
      const ctx = await this.ensureAudioContext();
      if (!this.analyserNode) {
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 512;
        analyser.smoothingTimeConstant = 0.6;
        this.attachAnalyser(analyser);
      }

      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.001, ctx.currentTime);
      gain.connect(this.analyserNode!);

      // Formant frequency carrier oscillators
      const baseFreq = voiceTone === 'Calm' ? 180 : voiceTone === 'Energetic' ? 260 : 220;
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const osc3 = ctx.createOscillator();

      osc1.type = 'triangle';
      osc1.frequency.setValueAtTime(baseFreq, ctx.currentTime);

      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(baseFreq * 2.2, ctx.currentTime);

      osc3.type = 'sawtooth';
      osc3.frequency.setValueAtTime(baseFreq * 3.4, ctx.currentTime);

      // Modulation for syllable rhythm
      const now = ctx.currentTime;
      const dur = durationMs / 1000;
      const numSyllables = Math.floor(dur * 4.5);
      
      gain.gain.setValueAtTime(0, now);
      for (let i = 0; i < numSyllables; i++) {
        const syllableStart = now + (i / numSyllables) * dur;
        const syllableMid = syllableStart + (dur / numSyllables) * 0.45;
        const syllableEnd = syllableStart + (dur / numSyllables) * 0.85;
        
        const vol = 0.25 + Math.random() * 0.35;
        gain.gain.setValueAtTime(0.01, syllableStart);
        gain.gain.exponentialRampToValueAtTime(vol, syllableMid);
        gain.gain.exponentialRampToValueAtTime(0.02, syllableEnd);
      }
      gain.gain.exponentialRampToValueAtTime(0.001, now + dur);

      osc1.connect(gain);
      osc2.connect(gain);
      osc3.connect(gain);

      osc1.start(now);
      osc2.start(now);
      osc3.start(now);

      osc1.stop(now + dur);
      osc2.stop(now + dur);
      osc3.stop(now + dur);

      this.synthGainNode = gain;
      this.synthOscillators = [osc1, osc2, osc3];
    } catch {
      // Audio synthesis fallback (e.g. browser security policy)
    }

    this.speechTimeout = window.setTimeout(() => {
      this.stopSpeechSimulation();
    }, durationMs + 200);
  }

  /**
   * Stop speech simulation
   */
  public stopSpeechSimulation(): void {
    this.isSimulatingSpeech = false;
    if (this.speechTimeout !== null) {
      clearTimeout(this.speechTimeout);
      this.speechTimeout = null;
    }
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    for (const osc of this.synthOscillators) {
      try {
        osc.stop();
        osc.disconnect();
      } catch {
        // ignored
      }
    }
    this.synthOscillators = [];
    if (this.synthGainNode) {
      try {
        this.synthGainNode.disconnect();
      } catch {
        // ignored
      }
      this.synthGainNode = null;
    }
  }

  /**
   * Main per-frame update loop (evaluates audio FFT & physiological biometrics)
   */
  private update(timestamp: number): void {
    let targetJawOpen = 0;
    let targetMouthRound = 0;
    let targetMouthSmile = 0.18; // base resting pleasant expression
    let targetMouthStretch = 0;
    let audioEnergy = 0;
    let isSpeaking = false;

    // 1. Audio Analysis via FFT
    if (this.analyserNode && this.freqData) {
      this.analyserNode.getByteFrequencyData(this.freqData);

      // Band 1: Low fundamental (approx 80 - 320 Hz, bins 1 to 4)
      let lowSum = 0;
      const lowBins = Math.min(4, this.freqData.length);
      for (let i = 1; i < lowBins; i++) {
        lowSum += this.freqData[i];
      }
      const lowEnergy = lowSum / ((lowBins - 1) * 255);

      // Band 2: Mid formants (approx 320 - 1200 Hz, bins 4 to 14)
      let midSum = 0;
      const midMax = Math.min(14, this.freqData.length);
      for (let i = 4; i < midMax; i++) {
        midSum += this.freqData[i];
      }
      const midEnergy = midSum / ((midMax - 4) * 255);

      // Band 3: High formants (approx 1200 - 3200 Hz, bins 14 to 38)
      let highMidSum = 0;
      const highMidMax = Math.min(38, this.freqData.length);
      for (let i = 14; i < highMidMax; i++) {
        highMidSum += this.freqData[i];
      }
      const highMidEnergy = highMidSum / ((highMidMax - 14) * 255);

      // Band 4: Sibilants / fricatives (approx 3200 - 8000 Hz, bins 38 to 90)
      let highSum = 0;
      const highMax = Math.min(90, this.freqData.length);
      for (let i = 38; i < highMax; i++) {
        highSum += this.freqData[i];
      }
      const highEnergy = highSum / ((highMax - 38) * 255);

      audioEnergy = (lowEnergy * 0.35 + midEnergy * 0.45 + highMidEnergy * 0.2);

      // Speech detection threshold
      if (audioEnergy > 0.05 || this.isSimulatingSpeech) {
        isSpeaking = true;

        // Vowel phoneme mapping:
        // High mid energy (F1) opens the jaw
        targetJawOpen = Math.min(1.0, midEnergy * 1.6 + lowEnergy * 0.5);

        // Low mid balance drives rounding (e.g. /o/, /u/)
        targetMouthRound = Math.min(1.0, Math.max(0, (lowEnergy - highMidEnergy) * 1.8));

        // High frequency energy drives stretch & smile (e.g. /ee/, /s/)
        targetMouthStretch = Math.min(1.0, highMidEnergy * 1.4 + highEnergy * 0.8);
        targetMouthSmile = 0.22 + targetMouthStretch * 0.35;
      }
    } else if (this.isSimulatingSpeech) {
      // Procedural synthetic modulation if no WebAudio analyser
      const t = timestamp * 0.008;
      targetJawOpen = Math.max(0, Math.sin(t * 1.8) * 0.6 + Math.cos(t * 3.2) * 0.3);
      targetMouthRound = Math.max(0, Math.sin(t * 1.2) * 0.5);
      targetMouthStretch = Math.max(0, Math.cos(t * 2.1) * 0.5);
      targetMouthSmile = 0.3 + targetMouthStretch * 0.2;
      audioEnergy = targetJawOpen * 0.7;
      isSpeaking = targetJawOpen > 0.1;
    }

    // 2. Smooth Interpolation (attack 0.35, decay 0.18 for organic muscle feel)
    const attackLerp = 0.32;
    const decayLerp = 0.16;

    const lerpJaw = targetJawOpen > this.currentJawOpen ? attackLerp : decayLerp;
    this.currentJawOpen += (targetJawOpen - this.currentJawOpen) * lerpJaw;

    const lerpRound = targetMouthRound > this.currentMouthRound ? attackLerp : decayLerp;
    this.currentMouthRound += (targetMouthRound - this.currentMouthRound) * lerpRound;

    const lerpSmile = targetMouthSmile > this.currentMouthSmile ? attackLerp : decayLerp;
    this.currentMouthSmile += (targetMouthSmile - this.currentMouthSmile) * lerpSmile;

    const lerpStretch = targetMouthStretch > this.currentMouthStretch ? attackLerp : decayLerp;
    this.currentMouthStretch += (targetMouthStretch - this.currentMouthStretch) * lerpStretch;

    this.currentEnergy += (audioEnergy - this.currentEnergy) * 0.25;

    // 3. Physiological Blinking (asymmetric curve: close 60ms, open 120ms)
    const timeSinceBlink = timestamp - this.lastBlinkTime;
    if (!this.isBlinking && timeSinceBlink > this.nextBlinkInterval) {
      this.isBlinking = true;
      this.blinkProgress = 0;
      this.lastBlinkTime = timestamp;
      this.nextBlinkInterval = 3200 + Math.random() * 3000;
    }

    if (this.isBlinking) {
      this.blinkProgress += 0.09; // takes ~11 frames (180ms total)
      if (this.blinkProgress < 0.35) {
        // Fast close
        this.currentBlinkWeight = this.blinkProgress / 0.35;
      } else if (this.blinkProgress <= 1.0) {
        // Slower open
        this.currentBlinkWeight = 1.0 - (this.blinkProgress - 0.35) / 0.65;
      } else {
        this.isBlinking = false;
        this.currentBlinkWeight = 0;
      }
    } else {
      this.currentBlinkWeight = 0;
    }

    // 4. Natural Eye Micro-Saccades (every 2-4 seconds)
    const timeSinceSaccade = timestamp - this.lastSaccadeTime;
    if (timeSinceSaccade > this.nextSaccadeInterval) {
      this.lastSaccadeTime = timestamp;
      this.nextSaccadeInterval = 1800 + Math.random() * 2500;
      // Slight darting gaze within realistic foveal zone
      this.targetGazeX = (Math.random() - 0.5) * 0.45;
      this.targetGazeY = (Math.random() - 0.5) * 0.25;
    }
    this.currentGazeX += (this.targetGazeX - this.currentGazeX) * 0.12;
    this.currentGazeY += (this.targetGazeY - this.currentGazeY) * 0.12;

    // 5. Idle Respiration (14 cycles / min -> ~4.3s period)
    this.respirationPhase += 0.024;
    const breathNorm = Math.sin(this.respirationPhase);
    const breathScale = 1.0 + breathNorm * 0.012;

    // 6. Natural Head Micro-Wander (gentle yaw, pitch, roll)
    this.headWanderPhase += 0.012;
    const headYaw = Math.sin(this.headWanderPhase * 0.6) * 0.035 + (isSpeaking ? Math.sin(this.headWanderPhase * 2.2) * 0.025 : 0);
    const headPitch = Math.cos(this.headWanderPhase * 0.8) * 0.025 + (breathNorm * 0.01) + (isSpeaking ? this.currentJawOpen * 0.03 : 0);
    const headRoll = Math.sin(this.headWanderPhase * 0.4) * 0.015;

    // Build comprehensive expression state
    const state: AvatarExpressionState = {
      visemes: {
        jawOpen: Math.max(0, Math.min(1, this.currentJawOpen)),
        mouthRound: Math.max(0, Math.min(1, this.currentMouthRound)),
        mouthSmile: Math.max(0, Math.min(1, this.currentMouthSmile)),
        mouthStretch: Math.max(0, Math.min(1, this.currentMouthStretch)),
        lipPucker: Math.max(0, Math.min(1, this.currentMouthRound * 0.85)),
        upperLipRaise: Math.max(0, Math.min(1, this.currentJawOpen * 0.35 + this.currentMouthSmile * 0.2)),
        lowerLipDepress: Math.max(0, Math.min(1, this.currentJawOpen * 0.8)),
      },
      blinkLeft: this.currentBlinkWeight,
      blinkRight: this.currentBlinkWeight,
      breathScale,
      headPitch,
      headYaw,
      headRoll,
      eyeGazeX: this.currentGazeX,
      eyeGazeY: this.currentGazeY,
      audioEnergy: this.currentEnergy,
      isSpeaking,
    };

    // Dispatch to all subscribers
    for (const listener of this.listeners) {
      listener(state);
    }
  }
}

// Export singleton instance for app-wide avatar coordination
export const sharedVisemeEngine = new VisemeLipSyncEngine();
