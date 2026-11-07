/**
 * AvatarCanvas.tsx
 * Aster Companion - Interactive Human Avatar Canvas
 *
 * Renders the photorealistic human companion avatar with:
 * - Distinctive warm amber halo glow behind the avatar head (matching PNGs a98599e6 and 56539447)
 * - Real-time procedural lip-sync (jawOpen, mouthRound, mouthSmile, mouthStretch)
 * - Dynamic blinking, breathing respiration, and eye micro-saccades via VisemeLipSyncEngine
 * - Customizable Hair (Auburn #9E4A28, Black #1A1A1A, Brown #4A2E1B, Blonde #D6BE88, Silver #9E9E9E)
 * - Customizable Eyes (Hazel #8D6E3F, Brown #3E2723, Blue #5C768D, Green #4E6B4E, Grey #78909C)
 * - Customizable Style (Natural, Casual, Professional, Creative)
 * - Interactive 3D pointer parallax tracking
 * - Low-power / Accessibility "No-Avatar Fallback" Mode
 */

import React, { useRef, useState, useEffect, useMemo } from 'react';
import { HairColor, EyeColor, CompanionStyle } from '../../types';
import { VisemeLipSyncEngine, AvatarExpressionState, sharedVisemeEngine } from './VisemeLipSyncEngine';

export interface AvatarCanvasProps {
  size?: number; // diameter in pixels (e.g. 240, 280, 160)
  hairColor?: HairColor;
  eyeColor?: EyeColor;
  style?: CompanionStyle;
  isInteractive?: boolean;
  showStatusDot?: boolean;
  avatarUrl?: string;
  glowIntensity?: 'normal' | 'high' | 'subtle';
  className?: string;
  noAvatarMode?: boolean; // Low-power / accessibility fallback
  visemeEngine?: VisemeLipSyncEngine;
  onAvatarClick?: () => void;
}

// Canonical color specifications
export const HAIR_COLOR_MAP: Record<HairColor, { hex: string; filter: string; label: string }> = {
  Auburn: {
    hex: '#9E4A28',
    filter: 'sepia(0.38) saturate(1.45) hue-rotate(-12deg) brightness(1.02)',
    label: 'Auburn',
  },
  Black: {
    hex: '#1A1A1A',
    filter: 'contrast(1.22) brightness(0.82) grayscale(0.55)',
    label: 'Black',
  },
  Brown: {
    hex: '#4A2E1B',
    filter: 'sepia(0.28) saturate(1.15) brightness(0.92) contrast(1.05)',
    label: 'Brown',
  },
  Blonde: {
    hex: '#D6BE88',
    filter: 'sepia(0.58) saturate(1.75) brightness(1.22) hue-rotate(8deg)',
    label: 'Blonde',
  },
  Silver: {
    hex: '#9E9E9E',
    filter: 'grayscale(0.92) contrast(1.18) brightness(1.28)',
    label: 'Silver',
  },
};

export const EYE_COLOR_MAP: Record<EyeColor, { hex: string; rgba: string; label: string }> = {
  Hazel: {
    hex: '#8D6E3F',
    rgba: 'rgba(141, 110, 63, 0.65)',
    label: 'Hazel',
  },
  Brown: {
    hex: '#3E2723',
    rgba: 'rgba(62, 39, 35, 0.75)',
    label: 'Brown',
  },
  Blue: {
    hex: '#5C768D',
    rgba: 'rgba(92, 118, 141, 0.70)',
    label: 'Blue',
  },
  Green: {
    hex: '#4E6B4E',
    rgba: 'rgba(78, 107, 78, 0.70)',
    label: 'Green',
  },
  Grey: {
    hex: '#78909C',
    rgba: 'rgba(120, 144, 156, 0.65)',
    label: 'Grey',
  },
};

export const AvatarCanvas: React.FC<AvatarCanvasProps> = ({
  size = 240,
  hairColor = 'Auburn',
  eyeColor = 'Hazel',
  style = 'Natural',
  isInteractive = true,
  showStatusDot = false,
  avatarUrl = '/assets/aster_avatar.png',
  glowIntensity = 'normal',
  className = '',
  noAvatarMode = false,
  visemeEngine = sharedVisemeEngine,
  onAvatarClick,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // 3D Parallax Tilt (degrees)
  const [tilt, setTilt] = useState({ x: 0, y: 0 });

  // Real-time expression state from viseme lip-sync engine
  const [expr, setExpr] = useState<AvatarExpressionState>({
    visemes: {
      jawOpen: 0,
      mouthRound: 0,
      mouthSmile: 0.18,
      mouthStretch: 0,
      lipPucker: 0,
      upperLipRaise: 0,
      lowerLipDepress: 0,
    },
    blinkLeft: 0,
    blinkRight: 0,
    breathScale: 1.0,
    headPitch: 0,
    headYaw: 0,
    headRoll: 0,
    eyeGazeX: 0,
    eyeGazeY: 0,
    audioEnergy: 0,
    isSpeaking: false,
  });

  // Subscribe to Viseme LipSync Engine
  useEffect(() => {
    const unsubscribe = visemeEngine.subscribe((newExpr) => {
      setExpr(newExpr);
    });
    return () => {
      unsubscribe();
    };
  }, [visemeEngine]);

  // Pointer tracking for interactive head turn
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isInteractive || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const nx = (e.clientX - rect.left) / rect.width - 0.5;
    const ny = (e.clientY - rect.top) / rect.height - 0.5;
    setTilt({
      x: nx * 14,
      y: -ny * 14,
    });
  };

  const handleMouseLeave = () => {
    setTilt({ x: 0, y: 0 });
  };

  // Glow classes based on intensity
  const glowConfig = useMemo(() => {
    switch (glowIntensity) {
      case 'high':
        return {
          blur: 'blur-3xl',
          opacity: 'opacity-95',
          scale: 1.18,
        };
      case 'subtle':
        return {
          blur: 'blur-xl',
          opacity: 'opacity-45',
          scale: 1.06,
        };
      case 'normal':
      default:
        return {
          blur: 'blur-2xl',
          opacity: 'opacity-80',
          scale: 1.12,
        };
    }
  }, [glowIntensity]);

  // Procedural Lip & Viseme Canvas Rendering Overlay
  useEffect(() => {
    if (noAvatarMode) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // Coordinate centers based on avatar portrait landmarks
    // Head center is approx (w * 0.5, h * 0.44)
    // Mouth center is approx (w * 0.5, h * 0.62)
    const mouthX = w * 0.5 + expr.headYaw * (w * 0.15) + (tilt.x * 0.08);
    const mouthY = h * 0.615 + expr.headPitch * (h * 0.12) - (tilt.y * 0.08);

    const jawOpen = expr.visemes.jawOpen;
    const mouthRound = expr.visemes.mouthRound;
    const mouthSmile = expr.visemes.mouthSmile;
    const mouthStretch = expr.visemes.mouthStretch;

    // Draw active lip-sync mouth morphing only when speaking or smiling noticeably
    if (jawOpen > 0.02 || mouthRound > 0.05 || mouthStretch > 0.1 || expr.isSpeaking) {
      ctx.save();

      // Mouth width & height driven by visemes
      const baseWidth = w * 0.16;
      const stretchWidth = baseWidth * (1 + mouthStretch * 0.35 + mouthSmile * 0.2 - mouthRound * 0.28);
      const openHeight = Math.max(1, jawOpen * (h * 0.10) + (expr.isSpeaking ? 2 : 0));

      // 1. Mouth Interior Cavity (Dark warm shadow)
      ctx.beginPath();
      ctx.ellipse(mouthX, mouthY + openHeight * 0.4, stretchWidth * 0.5, openHeight * 0.65, 0, 0, Math.PI * 2);
      ctx.fillStyle = '#220E0A';
      ctx.fill();

      // 2. Teeth (if open significantly)
      if (jawOpen > 0.25 || mouthStretch > 0.35) {
        ctx.beginPath();
        const teethY = mouthY + openHeight * 0.15;
        ctx.ellipse(mouthX, teethY, stretchWidth * 0.35, openHeight * 0.22, 0, 0, Math.PI);
        ctx.fillStyle = '#F3EFEA';
        ctx.fill();
      }

      // 3. Tongue hint (in lower cavity when jaw open wide)
      if (jawOpen > 0.45) {
        ctx.beginPath();
        const tongueY = mouthY + openHeight * 0.68;
        ctx.ellipse(mouthX, tongueY, stretchWidth * 0.28, openHeight * 0.28, 0, Math.PI, 0);
        ctx.fillStyle = '#A84C46';
        ctx.fill();
      }

      // 4. Upper Lip Contour
      ctx.beginPath();
      ctx.moveTo(mouthX - stretchWidth * 0.55, mouthY);
      ctx.quadraticCurveTo(
        mouthX - stretchWidth * 0.2,
        mouthY - openHeight * 0.15 - mouthSmile * 2.5,
        mouthX,
        mouthY - openHeight * 0.1
      );
      ctx.quadraticCurveTo(
        mouthX + stretchWidth * 0.2,
        mouthY - openHeight * 0.15 - mouthSmile * 2.5,
        mouthX + stretchWidth * 0.55,
        mouthY
      );
      ctx.strokeStyle = 'rgba(168, 86, 78, 0.75)';
      ctx.lineWidth = 2.2;
      ctx.lineCap = 'round';
      ctx.stroke();

      // 5. Lower Lip Contour
      ctx.beginPath();
      ctx.moveTo(mouthX - stretchWidth * 0.55, mouthY);
      ctx.quadraticCurveTo(
        mouthX,
        mouthY + openHeight * 0.95 + 3.0,
        mouthX + stretchWidth * 0.55,
        mouthY
      );
      ctx.strokeStyle = 'rgba(184, 94, 86, 0.85)';
      ctx.lineWidth = 2.4;
      ctx.stroke();

      ctx.restore();
    }

    // 6. Natural Eye Saccades & Corneal Highlight Reflection
    const leftEyeX = w * 0.435 + expr.headYaw * 4 + expr.eyeGazeX * 3.5;
    const rightEyeX = w * 0.565 + expr.headYaw * 4 + expr.eyeGazeX * 3.5;
    const eyeY = h * 0.425 + expr.headPitch * 3 + expr.eyeGazeY * 2.5;

    // Draw custom eye iris color wash
    const irisR = w * 0.024;
    const eyeColorSpec = EYE_COLOR_MAP[eyeColor] || EYE_COLOR_MAP.Hazel;

    ctx.save();
    ctx.globalAlpha = 0.55 * (1.0 - expr.blinkLeft);
    ctx.fillStyle = eyeColorSpec.rgba;
    ctx.beginPath();
    ctx.arc(leftEyeX, eyeY, irisR, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.arc(rightEyeX, eyeY, irisR, 0, Math.PI * 2);
    ctx.fill();

    // Corneal specular glint (warm amber ambient bounce)
    ctx.fillStyle = 'rgba(255, 230, 190, 0.7)';
    ctx.beginPath();
    ctx.arc(leftEyeX - 1.5, eyeY - 1.5, 1.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(rightEyeX - 1.5, eyeY - 1.5, 1.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // 7. Eyelid Blink Overlay (anatomical arc)
    if (expr.blinkLeft > 0.05) {
      ctx.save();
      const blinkAlpha = Math.min(1.0, expr.blinkLeft * 1.1);
      ctx.fillStyle = `rgba(32, 22, 19, ${blinkAlpha * 0.85})`;
      ctx.strokeStyle = `rgba(18, 12, 10, ${blinkAlpha * 0.95})`;
      ctx.lineWidth = 2;

      // Left eye lid
      ctx.beginPath();
      ctx.ellipse(w * 0.435, h * 0.425, w * 0.045, h * 0.022 * expr.blinkLeft, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      // Right eye lid
      ctx.beginPath();
      ctx.ellipse(w * 0.565, h * 0.425, w * 0.045, h * 0.022 * expr.blinkRight, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      ctx.restore();
    }
  }, [expr, eyeColor, noAvatarMode, tilt]);

  // Combined head rotation from user tilt + biometrics drift
  const combinedRotateX = tilt.y + expr.headPitch * (180 / Math.PI) * 0.4;
  const combinedRotateY = tilt.x + expr.headYaw * (180 / Math.PI) * 0.4;
  const combinedRotateZ = expr.headRoll * (180 / Math.PI) * 0.3;

  // Selected hair filter
  const hairFilter = HAIR_COLOR_MAP[hairColor]?.filter || HAIR_COLOR_MAP.Auburn.filter;

  // Style badge indicator / border accent
  const styleAccent = useMemo(() => {
    switch (style) {
      case 'Creative':
        return 'border-violet-accent/40 shadow-violet-glow';
      case 'Professional':
        return 'border-cream-muted/40 shadow-card';
      case 'Casual':
        return 'border-amber-bright/30';
      case 'Natural':
      default:
        return 'border-amber-accent/30 shadow-card';
    }
  }, [style]);

  // NO-AVATAR FALLBACK MODE (Low-power / accessibility preference)
  if (noAvatarMode) {
    return (
      <div
        ref={containerRef}
        onClick={onAvatarClick}
        className={`relative inline-flex items-center justify-center select-none ${className}`}
        style={{ width: size, height: size }}
      >
        {/* Warm amber back-glow halo */}
        <div
          className={`absolute inset-[-14%] rounded-full bg-gradient-to-tr from-amber-deep via-amber-bright to-amber-accent ${glowConfig.blur} ${glowConfig.opacity} pointer-events-none transition-all duration-700 animate-pulse-slow`}
        />

        {/* Outer orbital rings for soundwave visualizer */}
        <div className="absolute inset-0 rounded-full border border-amber-accent/20 animate-spin" style={{ animationDuration: '24s' }} />
        <div className="absolute inset-3 rounded-full border border-dashed border-amber-bright/30 animate-spin" style={{ animationDuration: '36s', animationDirection: 'reverse' }} />

        {/* Acoustic Center Core */}
        <div className="relative w-full h-full rounded-full bg-gradient-to-b from-graphite-850 via-graphite-900 to-graphite-950 border border-amber-accent/40 flex flex-col items-center justify-center overflow-hidden shadow-amber-glow">
          {/* Subtle acoustic frequency bars */}
          <div className="flex items-center justify-center gap-1.5 h-14 mb-1">
            {[0.4, 0.7, 1.0, 0.6, 0.9, 0.5, 0.8].map((mul, idx) => {
              const activeH = Math.max(12, expr.audioEnergy * 44 * mul + 10);
              return (
                <div
                  key={idx}
                  className="w-1.5 rounded-full bg-gradient-to-t from-amber-deep to-amber-bright transition-all duration-75"
                  style={{
                    height: `${activeH}px`,
                    opacity: expr.isSpeaking ? 0.95 : 0.45,
                  }}
                />
              );
            })}
          </div>

          {/* Accessible Text Tag */}
          <span className="text-xs font-semibold tracking-wider uppercase text-amber-bright/90">
            Aster Voice
          </span>
          <span className="text-[10px] text-cream-muted mt-0.5">
            {expr.isSpeaking ? 'Speaking...' : 'Listening'}
          </span>
        </div>

        {/* Status dot */}
        {showStatusDot && (
          <span
            className="absolute bottom-1 right-1 w-[18%] h-[18%] rounded-full bg-online border-[2.5px] border-graphite-950 shadow-md ring-1 ring-black/40 flex items-center justify-center z-20"
            title="Aster is online"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-white/80 animate-ping opacity-75" />
          </span>
        )}
      </div>
    );
  }

  // STANDARD HIGH-FIDELITY REALISTIC AVATAR
  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onAvatarClick}
      className={`relative inline-flex items-center justify-center select-none cursor-pointer group ${className}`}
      style={{
        width: size,
        height: size,
        perspective: 900,
      }}
      aria-label="Interactive Companion Avatar"
    >
      {/* 1. Distinctive Warm Amber Halo Glow behind Avatar Head (matching screenshots) */}
      <div
        className={`absolute inset-[-12%] rounded-full bg-gradient-to-tr from-amber-deep via-amber-bright to-amber-accent ${glowConfig.blur} ${glowConfig.opacity} pointer-events-none transition-all duration-700 animate-pulse-slow`}
        style={{
          transform: `scale(${glowConfig.scale * (expr.breathScale || 1.0)})`,
        }}
      />

      {/* 2. Soft Secondary Radial Atmosphere */}
      <div
        className="absolute inset-[-6%] rounded-full pointer-events-none transition-opacity duration-500"
        style={{
          background:
            'radial-gradient(circle, rgba(245,166,35,0.45) 0%, rgba(229,152,67,0.22) 50%, transparent 74%)',
          transform: `scale(${expr.breathScale})`,
        }}
      />

      {/* 3. Main Avatar Head Circle with 3D Parallax & Breathing Scale */}
      <div
        className={`relative w-full h-full rounded-full overflow-hidden border ${styleAccent} bg-graphite-900 shadow-card transition-transform duration-150 ease-out flex items-center justify-center`}
        style={{
          transform: `scale(${expr.breathScale}) rotateX(${combinedRotateX}deg) rotateY(${combinedRotateY}deg) rotateZ(${combinedRotateZ}deg)`,
          transformOrigin: '50% 65%',
        }}
      >
        {/* Photorealistic Portrait with Hair Tinting Filter */}
        <img
          src={avatarUrl}
          alt="Aster Companion Avatar"
          className="w-full h-full object-cover object-center transition-all duration-300 pointer-events-none"
          style={{
            filter: hairFilter,
            transform: `scale(1.02)`,
          }}
          onError={(e) => {
            // Graceful fallback if image is unreachable
            const target = e.target as HTMLElement;
            target.style.display = 'none';
          }}
        />

        {/* Live Procedural Viseme Canvas Overlay (Mouth, Teeth, Lips, Eye Color, Blinks) */}
        <canvas
          ref={canvasRef}
          width={size * 2}
          height={size * 2}
          className="absolute inset-0 w-full h-full pointer-events-none z-10"
        />

        {/* Ambient Warm Lighting Overlay (Simulates Amber Room Ambience) */}
        <div
          className="absolute inset-0 pointer-events-none mix-blend-soft-light transition-opacity duration-300"
          style={{
            background:
              'radial-gradient(circle at 50% 30%, rgba(245, 166, 35, 0.28) 0%, rgba(30, 20, 15, 0.45) 85%)',
          }}
        />

        {/* Subtle speaking pulse highlight */}
        {expr.isSpeaking && (
          <div
            className="absolute inset-0 pointer-events-none border-2 border-amber-bright/30 rounded-full animate-pulse"
          />
        )}
      </div>

      {/* 4. Online Status Dot at Bottom Right (matching screenshots 56539447 & 79ffed4b) */}
      {showStatusDot && (
        <span
          className="absolute bottom-1 right-1 w-[18%] h-[18%] rounded-full bg-online border-[2.5px] border-graphite-950 shadow-md ring-1 ring-black/40 flex items-center justify-center z-20"
          title="Aster is online"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-white/80 animate-ping opacity-75" />
        </span>
      )}
    </div>
  );
};

export default AvatarCanvas;
