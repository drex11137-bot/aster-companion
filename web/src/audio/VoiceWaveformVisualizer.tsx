/**
 * Aster Companion Voice Waveform Visualizer
 * 
 * Production ambient canvas waveform matching the Aster design system:
 * - Dark graphite matte background (#121110)
 * - Multi-layer warm glowing amber sinusoidal bezier waves (#E59843, #F5A623, #FFB347)
 * - Ambient radial backlight glow & subtle floating energy filaments
 * - Driven in real-time by Float32Array time/frequency buffers from WebRTCVoiceClient
 * - Fluid state animations: Idle breathing, Listening ripple, Speaking undulation, Barge-In dip
 * - High-DPI Retina canvas rendering with smooth lerp interpolation
 */

import React, { useEffect, useRef, useState, useMemo } from 'react';
import { WebRTCVoiceClient } from './WebRTCVoiceClient';
import { VoiceClientState, VisualizerData, AudioEnergyData } from './types';

export interface VoiceWaveformVisualizerProps {
  /** Optional WebRTCVoiceClient instance to automatically bind to */
  voiceClient?: WebRTCVoiceClient | null;
  /** Direct audio data feed (normalized -1.0 to 1.0 or frequency magnitude 0.0 to 1.0) */
  audioData?: Float32Array | null;
  /** Active voice state override */
  state?: VoiceClientState;
  /** Live audio energy override */
  energy?: AudioEnergyData | null;
  /** Desired canvas width (default: 100% responsive) */
  width?: number;
  /** Desired canvas height in pixels (default: 180) */
  height?: number;
  /** Display state chip and live telemetry */
  showTelemetry?: boolean;
  /** CSS class overrides */
  className?: string;
  /** Glow intensity multiplier (default: 1.0) */
  glowIntensity?: number;
  /** Base background fill color (default: '#121110') */
  backgroundColor?: string;
  /** Primary glowing amber color (default: '#F5A623') */
  primaryAmberColor?: string;
  /** Secondary warm amber color (default: '#E59843') */
  secondaryAmberColor?: string;
}

interface ParticleFilament {
  x: number;
  y: number;
  radius: number;
  vx: number;
  vy: number;
  alpha: number;
  phase: number;
}

export const VoiceWaveformVisualizer: React.FC<VoiceWaveformVisualizerProps> = ({
  voiceClient,
  audioData,
  state: stateProp,
  energy: energyProp,
  width: customWidth,
  height = 180,
  showTelemetry = true,
  className = '',
  glowIntensity = 1.0,
  backgroundColor = '#121110',
  primaryAmberColor = '#F5A623',
  secondaryAmberColor = '#E59843',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Local state tracking
  const [internalState, setInternalState] = useState<VoiceClientState>('idle');
  const [internalEnergy, setInternalEnergy] = useState<AudioEnergyData>({
    rms: 0,
    decibels: -100,
    peak: 0,
    isSpeech: false,
    noiseFloorDb: -65,
  });

  // Effective state and energy
  const activeState = stateProp || internalState;
  const activeEnergy = energyProp || internalEnergy;

  // Real-time animation references
  const animFrameId = useRef<number | null>(null);
  const audioDataRef = useRef<Float32Array | null>(null);
  const smoothedAmplitudeRef = useRef<number>(0.1);
  const smoothedEnergyRef = useRef<number>(0.0);
  const phaseRef = useRef<number>(0);
  const bargeInDipRef = useRef<number>(0);

  // Initialize particle filaments for subtle ambient dust
  const particles = useMemo<ParticleFilament[]>(() => {
    const list: ParticleFilament[] = [];
    for (let i = 0; i < 28; i++) {
      list.push({
        x: Math.random() * 400,
        y: Math.random() * height,
        radius: 0.8 + Math.random() * 1.6,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.25,
        alpha: 0.15 + Math.random() * 0.45,
        phase: Math.random() * Math.PI * 2,
      });
    }
    return list;
  }, [height]);

  // Bind to WebRTCVoiceClient events
  useEffect(() => {
    if (!voiceClient) return;

    const handleVisualizerData = (data: VisualizerData) => {
      audioDataRef.current = data.waveform;
      setInternalEnergy(data.energy);
    };

    const handleStateChange = (newState: VoiceClientState) => {
      setInternalState(newState);
    };

    const handleBargeIn = () => {
      bargeInDipRef.current = 1.0;
    };

    setInternalState(voiceClient.getState());
    setInternalEnergy(voiceClient.getEnergy());

    voiceClient.on('visualizerData', handleVisualizerData);
    voiceClient.on('stateChange', handleStateChange);
    voiceClient.on('bargeIn', handleBargeIn);

    return () => {
      voiceClient.off('visualizerData', handleVisualizerData);
      voiceClient.off('stateChange', handleStateChange);
      voiceClient.off('bargeIn', handleBargeIn);
    };
  }, [voiceClient]);

  // Update audioDataRef when direct prop changes
  useEffect(() => {
    if (audioData) {
      audioDataRef.current = audioData;
    }
  }, [audioData]);

  // Main Canvas Rendering Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let isRunning = true;

    const render = () => {
      if (!isRunning) return;

      const container = containerRef.current;
      const displayWidth = customWidth || container?.clientWidth || 360;
      const displayHeight = height;

      // Handle High-DPI screens
      const dpr = window.devicePixelRatio || 1;
      const targetWidth = Math.round(displayWidth * dpr);
      const targetHeight = Math.round(displayHeight * dpr);

      if (canvas.width !== targetWidth || canvas.height !== targetHeight) {
        canvas.width = targetWidth;
        canvas.height = targetHeight;
      }

      ctx.save();
      ctx.scale(dpr, dpr);

      // 1. Draw graphite background
      ctx.fillStyle = backgroundColor;
      ctx.fillRect(0, 0, displayWidth, displayHeight);

      // 2. Draw ambient radial glow centered on the waveform
      const centerX = displayWidth / 2;
      const centerY = displayHeight / 2;
      const maxRadius = Math.max(displayWidth, displayHeight) * 0.65;

      const baseGlowAlpha = activeState === 'speaking'
        ? 0.38
        : activeState === 'listening'
        ? 0.24
        : 0.16;

      const radialGlow = ctx.createRadialGradient(
        centerX,
        centerY,
        10,
        centerX,
        centerY,
        maxRadius
      );
      radialGlow.addColorStop(0, `rgba(229, 152, 67, ${(baseGlowAlpha * glowIntensity).toFixed(3)})`);
      radialGlow.addColorStop(0.45, `rgba(196, 120, 40, ${(baseGlowAlpha * 0.4 * glowIntensity).toFixed(3)})`);
      radialGlow.addColorStop(1, 'rgba(18, 17, 16, 0)');

      ctx.fillStyle = radialGlow;
      ctx.fillRect(0, 0, displayWidth, displayHeight);

      // 3. Compute dynamic amplitude & phase modulation
      const buffer = audioDataRef.current;
      let instantRms = 0;

      if (buffer && buffer.length > 0) {
        let sum = 0;
        const step = Math.max(1, Math.floor(buffer.length / 128));
        let count = 0;
        for (let i = 0; i < buffer.length; i += step) {
          sum += buffer[i] * buffer[i];
          count++;
        }
        instantRms = Math.sqrt(sum / count);
      }

      // Smooth amplitude lerp (prevents abrupt jumping)
      const targetAmp = activeState === 'speaking'
        ? Math.max(0.35, instantRms * 2.8)
        : activeState === 'listening'
        ? Math.max(0.18, instantRms * 1.5)
        : 0.12;

      smoothedAmplitudeRef.current += (targetAmp - smoothedAmplitudeRef.current) * 0.14;
      smoothedEnergyRef.current += (activeEnergy.rms - smoothedEnergyRef.current) * 0.12;

      // Handle barge-in dip recovery
      if (bargeInDipRef.current > 0.01) {
        bargeInDipRef.current *= 0.82;
      } else {
        bargeInDipRef.current = 0;
      }

      const effectiveAmp = Math.max(0.04, smoothedAmplitudeRef.current * (1 - bargeInDipRef.current * 0.85));

      // Phase progression speed (faster when speaking or listening)
      const phaseSpeed = activeState === 'speaking'
        ? 0.052
        : activeState === 'listening'
        ? 0.034
        : 0.018;

      phaseRef.current += phaseSpeed;
      const currentPhase = phaseRef.current;

      // 4. Render Ambient Floating Dust Filaments
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.phase += 0.02;

        if (p.x < 0) p.x = displayWidth;
        if (p.x > displayWidth) p.x = 0;
        if (p.y < 0) p.y = displayHeight;
        if (p.y > displayHeight) p.y = 0;

        const dynamicAlpha = p.alpha * (0.6 + 0.4 * Math.sin(p.phase)) * (activeState === 'speaking' ? 1.4 : 1.0);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(245, 166, 35, ${Math.min(1, dynamicAlpha).toFixed(3)})`;
        ctx.shadowColor = primaryAmberColor;
        ctx.shadowBlur = 4;
        ctx.fill();
      }

      // 5. Draw Layered Harmonic Glowing Waves
      // Wave 3: Deep subtle background wave
      drawWaveLayer({
        ctx,
        width: displayWidth,
        height: displayHeight,
        amplitude: displayHeight * 0.16 * effectiveAmp,
        frequency: 0.008,
        phase: currentPhase * 0.7,
        color: 'rgba(196, 120, 40, 0.32)',
        shadowColor: secondaryAmberColor,
        shadowBlur: 8 * glowIntensity,
        lineWidth: 1.5,
        offsetY: centerY,
        buffer,
      });

      // Wave 2: Middle warm amber wave
      drawWaveLayer({
        ctx,
        width: displayWidth,
        height: displayHeight,
        amplitude: displayHeight * 0.24 * effectiveAmp,
        frequency: 0.014,
        phase: currentPhase * 1.15 + 1.2,
        color: secondaryAmberColor,
        shadowColor: secondaryAmberColor,
        shadowBlur: 14 * glowIntensity,
        lineWidth: 2.2,
        offsetY: centerY,
        buffer,
      });

      // Wave 1: Primary glowing bright amber foreground wave
      drawWaveLayer({
        ctx,
        width: displayWidth,
        height: displayHeight,
        amplitude: displayHeight * 0.32 * effectiveAmp,
        frequency: 0.019,
        phase: currentPhase * 1.6 + 2.8,
        color: primaryAmberColor,
        shadowColor: primaryAmberColor,
        shadowBlur: 20 * glowIntensity,
        lineWidth: 2.8,
        offsetY: centerY,
        buffer,
      });

      ctx.restore();
      animFrameId.current = requestAnimationFrame(render);
    };

    animFrameId.current = requestAnimationFrame(render);

    return () => {
      isRunning = false;
      if (animFrameId.current !== null) {
        cancelAnimationFrame(animFrameId.current);
      }
    };
  }, [
    customWidth,
    height,
    activeState,
    activeEnergy,
    backgroundColor,
    primaryAmberColor,
    secondaryAmberColor,
    glowIntensity,
    particles,
  ]);

  // Status Chip Visual Indicator
  const stateBadge = useMemo(() => {
    switch (activeState) {
      case 'speaking':
        return {
          label: 'Aster speaking',
          badgeClass: 'bg-amber-bright/20 border-amber-bright/40 text-amber-bright',
          dotClass: 'bg-amber-bright animate-pulse',
        };
      case 'listening':
        return {
          label: 'Listening',
          badgeClass: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400',
          dotClass: 'bg-emerald-400 animate-ping',
        };
      case 'interrupted':
        return {
          label: 'Interrupted',
          badgeClass: 'bg-rose-500/20 border-rose-500/40 text-rose-300',
          dotClass: 'bg-rose-400',
        };
      case 'connecting':
      case 'requesting_permissions':
        return {
          label: 'Connecting…',
          badgeClass: 'bg-violet-accent/20 border-violet-accent/40 text-violet-accent',
          dotClass: 'bg-violet-accent animate-pulse',
        };
      case 'disconnected':
        return {
          label: 'Offline',
          badgeClass: 'bg-graphite-700/40 border-graphite-600/40 text-cream-muted',
          dotClass: 'bg-graphite-600',
        };
      default:
        return {
          label: 'Ready',
          badgeClass: 'bg-graphite-800/80 border-graphite-700 text-cream-soft',
          dotClass: 'bg-online',
        };
    }
  }, [activeState]);

  return (
    <div
      ref={containerRef}
      className={`relative w-full rounded-2xl overflow-hidden border border-card-border bg-graphite-950 shadow-card ${className}`}
      style={{ height }}
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full block"
        style={{ width: '100%', height }}
      />

      {showTelemetry && (
        <div className="absolute top-3 left-4 right-4 flex items-center justify-between pointer-events-none select-none">
          {/* Status Indicator */}
          <div
            className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium border backdrop-blur-md transition-colors ${stateBadge.badgeClass}`}
          >
            <span className={`w-2 h-2 rounded-full ${stateBadge.dotClass}`} />
            <span>{stateBadge.label}</span>
          </div>

          {/* Audio Energy Telemetry */}
          {activeEnergy.decibels > -90 && (
            <div className="text-[11px] font-mono tracking-wider text-cream-muted/70 bg-graphite-900/80 px-2 py-0.5 rounded-md border border-graphite-800 backdrop-blur-sm">
              {Math.round(activeEnergy.decibels)} dBFS
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ==========================================
// Smooth Bezier Wave Drawing Helper
// ==========================================

interface WaveLayerProps {
  ctx: CanvasRenderingContext2D;
  width: number;
  height: number;
  amplitude: number;
  frequency: number;
  phase: number;
  color: string;
  shadowColor: string;
  shadowBlur: number;
  lineWidth: number;
  offsetY: number;
  buffer: Float32Array | null;
}

function drawWaveLayer({
  ctx,
  width,
  height,
  amplitude,
  frequency,
  phase,
  color,
  shadowColor,
  shadowBlur,
  lineWidth,
  offsetY,
  buffer,
}: WaveLayerProps): void {
  ctx.save();
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.shadowColor = shadowColor;
  ctx.shadowBlur = shadowBlur;
  ctx.lineWidth = lineWidth;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  const points: { x: number; y: number }[] = [];
  const segments = 48;
  const step = width / segments;

  for (let i = 0; i <= segments; i++) {
    const x = i * step;

    // Windowing envelope: dampens edges so wave tapers smoothly to center
    const normalizedX = x / width;
    const envelope = Math.sin(normalizedX * Math.PI);

    // Audio buffer displacement if available
    let audioOffset = 0;
    if (buffer && buffer.length > 0) {
      const bufIdx = Math.floor(normalizedX * (buffer.length - 1));
      audioOffset = buffer[bufIdx] * amplitude * 0.9;
    }

    // Composite harmonic calculation
    const sineVal = Math.sin(x * frequency + phase) * 0.7 + Math.sin(x * frequency * 1.8 + phase * 1.3) * 0.3;
    const rawY = offsetY + (sineVal * amplitude + audioOffset) * envelope;
    const y = Math.max(4, Math.min(height - 4, rawY));

    points.push({ x, y });
  }

  // Draw smooth cubic curves through points
  if (points.length > 0) {
    ctx.moveTo(points[0].x, points[0].y);

    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i];
      const p1 = points[i + 1];
      const midX = (p0.x + p1.x) / 2;
      const midY = (p0.y + p1.y) / 2;
      ctx.quadraticCurveTo(p0.x, p0.y, midX, midY);
    }

    const lastPoint = points[points.length - 1];
    ctx.lineTo(lastPoint.x, lastPoint.y);
  }

  ctx.stroke();
  ctx.restore();
}

export default VoiceWaveformVisualizer;
