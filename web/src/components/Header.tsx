import React, { useState } from 'react';
import {
  Laptop,
  Smartphone,
  Pause,
  Play,
  Square,
  ChevronDown,
} from 'lucide-react';
import { useCompanion } from '../context/CompanionContext';

export const Header: React.FC = () => {
  const {
    activeProfile,
    viewMode,
    setViewMode,
    isAwarenessActive,
    isAwarenessPaused,
    pauseAwareness,
    resumeAwareness,
    stopAwareness,
    setActiveTab,
  } = useCompanion();

  const [panelOpen, setPanelOpen] = useState(false);

  return (
    <header className="h-14 border-b border-card-border/80 bg-graphite-950/90 backdrop-blur sticky top-0 z-30 px-4 md:px-6 flex items-center justify-between">
      {/* Left: Mobile Title or Desktop Status */}
      <div className="flex items-center space-x-3">
        <span className="text-xs font-bold uppercase tracking-widest text-amber-bright">
          Aster Companion
        </span>
        <span className="hidden sm:inline text-xs text-cream-muted">
          • v1.1 PRD Compliance
        </span>
      </div>

      {/* Center: Contextual Awareness Indicator (PRD Sections 13.4 & 13.5) */}
      <div className="relative">
        <button
          onClick={() => setPanelOpen(!panelOpen)}
          className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium transition-all ${
            isAwarenessActive
              ? isAwarenessPaused
                ? 'bg-amber-deep/30 text-amber-bright border border-amber-accent/40'
                : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
              : 'bg-graphite-850 text-cream-muted border border-card-border hover:bg-graphite-800'
          }`}
          title="Contextual Awareness Indicator"
        >
          <span
            className={`w-2 h-2 rounded-full ${
              isAwarenessActive
                ? isAwarenessPaused
                  ? 'bg-amber-bright'
                  : 'bg-online animate-pulse'
                : 'bg-cream-muted/60'
            }`}
          />
          <span className="hidden xs:inline">
            {isAwarenessActive
              ? isAwarenessPaused
                ? 'Awareness Paused'
                : 'Awareness Active'
              : 'Awareness Standby'}
          </span>
          <ChevronDown className="w-3 h-3 text-cream-muted" />
        </button>

        {/* Compact Contextual Control Panel matching PRD Section 13.5 */}
        {panelOpen && (
          <div className="absolute top-10 left-1/2 -translate-x-1/2 w-72 rounded-2xl bg-card-elevated border border-card-border p-4 shadow-card z-50 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-cream">
                Continuous Awareness Panel
              </span>
              <span className="text-[10px] text-cream-muted font-mono">
                {activeProfile.name}
              </span>
            </div>

            <p className="text-xs text-cream-muted leading-tight">
              {isAwarenessActive
                ? 'Monitoring screen context and active laptop application events.'
                : 'Awareness is currently stopped. Click below to start.'}
            </p>

            {isAwarenessActive ? (
              <div className="flex items-center space-x-2 pt-1">
                {isAwarenessPaused ? (
                  <button
                    onClick={() => {
                      resumeAwareness();
                      setPanelOpen(false);
                    }}
                    className="flex-1 py-1.5 rounded-lg bg-amber-bright text-graphite-950 font-semibold text-xs flex items-center justify-center space-x-1"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Resume</span>
                  </button>
                ) : (
                  <button
                    onClick={() => {
                      pauseAwareness();
                      setPanelOpen(false);
                    }}
                    className="flex-1 py-1.5 rounded-lg bg-graphite-800 border border-card-border text-cream text-xs flex items-center justify-center space-x-1"
                  >
                    <Pause className="w-3.5 h-3.5" />
                    <span>Pause</span>
                  </button>
                )}

                <button
                  onClick={() => {
                    stopAwareness();
                    setPanelOpen(false);
                  }}
                  className="p-1.5 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 text-xs"
                  title="Stop capture"
                >
                  <Square className="w-4 h-4 fill-current" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => {
                  setPanelOpen(false);
                  setActiveTab('awareness');
                }}
                className="w-full py-1.5 rounded-lg bg-amber-bright text-graphite-950 font-semibold text-xs"
              >
                Open Awareness HUD
              </button>
            )}
          </div>
        )}
      </div>

      {/* Right: View Mode Toggle (Laptop Desktop Client vs Mobile Phone Preview) */}
      <div className="flex items-center space-x-2">
        <div className="hidden sm:flex items-center p-1 rounded-xl bg-card-base border border-card-border">
          <button
            onClick={() => setViewMode('responsive-desktop')}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium flex items-center space-x-1.5 transition-colors ${
              viewMode === 'responsive-desktop'
                ? 'bg-graphite-750 text-cream shadow-sm'
                : 'text-cream-muted hover:text-cream'
            }`}
            title="Full Laptop Desktop View"
          >
            <Laptop className="w-3.5 h-3.5" />
            <span>Laptop View</span>
          </button>

          <button
            onClick={() => setViewMode('mobile-frame')}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium flex items-center space-x-1.5 transition-colors ${
              viewMode === 'mobile-frame'
                ? 'bg-amber-deep/30 text-amber-bright border border-amber-accent/40 shadow-sm'
                : 'text-cream-muted hover:text-cream'
            }`}
            title="Inspect 100% Fidelity Mobile Frame"
          >
            <Smartphone className="w-3.5 h-3.5" />
            <span>Mobile Preview</span>
          </button>
        </div>
      </div>
    </header>
  );
};
