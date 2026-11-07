import React, { useRef, useEffect } from 'react';
import {
  Play,
  Pause,
  Square,
  Mic,
  MicOff,
  Activity,
  Layers,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Monitor,
  Eye,
} from 'lucide-react';
import { useCompanion } from '../../context/CompanionContext';

export const AwarenessScreen: React.FC = () => {
  const {
    activeProfile,
    isAwarenessActive,
    isAwarenessPaused,
    isAudioMuted,
    screenStream,
    awarenessMetrics,
    perceptionEvents,
    startAwareness,
    pauseAwareness,
    resumeAwareness,
    stopAwareness,
    toggleAudioMute,
  } = useCompanion();

  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && screenStream) {
      videoRef.current.srcObject = screenStream;
    }
  }, [screenStream]);

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6 md:py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold tracking-tight text-cream">
              Continuous Screen & Audio Awareness
            </h1>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase tracking-wider flex items-center space-x-1.5 ${
                isAwarenessActive
                  ? isAwarenessPaused
                    ? 'bg-amber-deep/30 text-amber-bright border border-amber-accent/40'
                    : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-graphite-800 text-cream-muted border border-card-border'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isAwarenessActive
                    ? isAwarenessPaused
                      ? 'bg-amber-bright'
                      : 'bg-emerald-400 animate-pulse'
                    : 'bg-cream-muted'
                }`}
              />
              <span>
                {isAwarenessActive
                  ? isAwarenessPaused
                    ? 'Paused'
                    : 'Active'
                  : 'Standby'}
              </span>
            </span>
          </div>
          <p className="text-xs md:text-sm text-cream-muted mt-1">
            Laptop screen capture & contextual perception pipeline for{' '}
            <strong>{activeProfile.name}</strong>.
          </p>
        </div>

        {/* Quick Pause / Stop / Mute Controls matching PRD Section 13.4 */}
        <div className="flex items-center space-x-2">
          {!isAwarenessActive ? (
            <button
              onClick={startAwareness}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-amber-bright hover:bg-amber-accent text-graphite-950 font-semibold text-xs tracking-wide shadow-md transition-all active:scale-95"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Start Screen Awareness</span>
            </button>
          ) : (
            <>
              {isAwarenessPaused ? (
                <button
                  onClick={resumeAwareness}
                  className="p-2.5 rounded-full bg-amber-bright text-graphite-950 hover:bg-amber-accent shadow-md transition-all"
                  title="Resume awareness"
                >
                  <Play className="w-4 h-4 fill-current" />
                </button>
              ) : (
                <button
                  onClick={pauseAwareness}
                  className="p-2.5 rounded-full bg-graphite-800 border border-card-border text-cream hover:bg-graphite-750 transition-all"
                  title="Pause awareness stream"
                >
                  <Pause className="w-4 h-4" />
                </button>
              )}

              <button
                onClick={toggleAudioMute}
                className={`p-2.5 rounded-full border transition-all ${
                  isAudioMuted
                    ? 'bg-red-500/20 border-red-500/40 text-red-400'
                    : 'bg-graphite-800 border-card-border text-cream hover:bg-graphite-750'
                }`}
                title={isAudioMuted ? 'Unmute microphone' : 'Mute microphone'}
              >
                {isAudioMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>

              <button
                onClick={stopAwareness}
                className="p-2.5 rounded-full bg-red-600/20 border border-red-500/40 text-red-400 hover:bg-red-600/30 transition-all"
                title="Stop awareness and disconnect"
              >
                <Square className="w-4 h-4 fill-current" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Screen Sharing Viewport */}
      <div className="relative rounded-2xl overflow-hidden bg-graphite-900 border border-card-border shadow-card aspect-video flex items-center justify-center">
        {screenStream ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-contain"
          />
        ) : isAwarenessActive ? (
          <div className="flex flex-col items-center justify-center p-6 text-center space-y-3">
            <div className="w-16 h-16 rounded-2xl bg-amber-deep/20 border border-amber-bright/30 flex items-center justify-center text-amber-bright animate-pulse">
              <Monitor className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-cream">
                Continuous Client Ingestion Active
              </h3>
              <p className="text-xs text-cream-muted max-w-sm mt-1">
                Processing laptop display frames through local client buffer. Visual OCR, scene changes, and window focus tracking active.
              </p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center p-6 text-center space-y-3">
            <div className="w-16 h-16 rounded-2xl bg-card-base border border-card-border flex items-center justify-center text-cream-muted">
              <Eye className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-cream">
                Awareness Inactive
              </h3>
              <p className="text-xs text-cream-muted max-w-sm mt-1">
                Click &apos;Start Screen Awareness&apos; to enable {activeProfile.name} to follow your ongoing screen activities, documents, and context.
              </p>
            </div>
          </div>
        )}

        {/* Floating subtle overlay tag */}
        {isAwarenessActive && (
          <div className="absolute top-3 left-3 flex items-center space-x-2 px-3 py-1 rounded-full bg-graphite-950/80 border border-card-border backdrop-blur text-[11px] text-cream">
            <span className="w-2 h-2 rounded-full bg-online animate-ping" />
            <span>Live Screen Stream • {activeProfile.name}</span>
          </div>
        )}
      </div>

      {/* Real-time Metrics Dashboard matching PRD Section 5.3 & Prompt */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-cream flex items-center space-x-2">
          <Activity className="w-4 h-4 text-amber-bright" />
          <span>Perception Pipeline Metrics</span>
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {/* Metric 1: Capture FPS */}
          <div className="p-3.5 rounded-2xl bg-card-base border border-card-border shadow-card">
            <span className="text-[11px] text-cream-muted font-medium block">Capture Rate</span>
            <div className="text-lg md:text-xl font-bold text-cream mt-1">
              {isAwarenessActive && !isAwarenessPaused ? `${awarenessMetrics.captureFps} FPS` : '0 FPS'}
            </div>
            <span className="text-[10px] text-amber-bright">Target: 120 FPS</span>
          </div>

          {/* Metric 2: Upload FPS */}
          <div className="p-3.5 rounded-2xl bg-card-base border border-card-border shadow-card">
            <span className="text-[11px] text-cream-muted font-medium block">Upload Rate</span>
            <div className="text-lg md:text-xl font-bold text-cream mt-1">
              {isAwarenessActive && !isAwarenessPaused ? `${awarenessMetrics.uploadFps} FPS` : '0 FPS'}
            </div>
            <span className="text-[10px] text-cream-muted">Encoded video</span>
          </div>

          {/* Metric 3: Analysis FPS */}
          <div className="p-3.5 rounded-2xl bg-card-base border border-card-border shadow-card">
            <span className="text-[11px] text-cream-muted font-medium block">Analysis Rate</span>
            <div className="text-lg md:text-xl font-bold text-cream mt-1">
              {isAwarenessActive && !isAwarenessPaused ? `${awarenessMetrics.analysisFps} FPS` : '0 FPS'}
            </div>
            <span className="text-[10px] text-cream-muted">OCR & UI models</span>
          </div>

          {/* Metric 4: Latency */}
          <div className="p-3.5 rounded-2xl bg-card-base border border-card-border shadow-card">
            <span className="text-[11px] text-cream-muted font-medium block">Latency</span>
            <div className="text-lg md:text-xl font-bold text-cream mt-1 flex items-center space-x-1">
              <Clock className="w-4 h-4 text-cream-muted" />
              <span>{isAwarenessActive && !isAwarenessPaused ? `${awarenessMetrics.latencyMs}ms` : '--'}</span>
            </div>
            <span className="text-[10px] text-cream-muted">End-to-end</span>
          </div>

          {/* Metric 5: Sequence */}
          <div className="p-3.5 rounded-2xl bg-card-base border border-card-border shadow-card">
            <span className="text-[11px] text-cream-muted font-medium block">Frame Sequence</span>
            <div className="text-lg md:text-xl font-bold text-cream mt-1">
              {isAwarenessActive ? awarenessMetrics.frameSequence.toLocaleString() : '--'}
            </div>
            <span className="text-[10px] text-cream-muted">Monotonic counter</span>
          </div>

          {/* Metric 6: Continuity & Integrity */}
          <div className="p-3.5 rounded-2xl bg-card-base border border-card-border shadow-card">
            <span className="text-[11px] text-cream-muted font-medium block">Integrity</span>
            <div className="text-sm font-bold text-cream mt-1 flex items-center space-x-1">
              {awarenessMetrics.gapsDetected === 0 ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400 text-xs">Verified</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 text-amber-bright" />
                  <span className="text-amber-bright text-xs">{awarenessMetrics.gapsDetected} gaps</span>
                </>
              )}
            </div>
            <span className="text-[10px] text-cream-muted">No missing frames</span>
          </div>
        </div>
      </div>

      {/* Real-time Perception Events Stream */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-cream flex items-center space-x-2">
          <Layers className="w-4 h-4 text-violet-accent" />
          <span>Real-time Perception Events</span>
        </h3>

        <div className="rounded-2xl bg-card-base border border-card-border divide-y divide-card-border overflow-hidden shadow-card">
          {perceptionEvents.map((evt) => (
            <div key={evt.id} className="p-3.5 flex items-start justify-between hover:bg-graphite-800/40 transition-colors">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-semibold text-cream">{evt.title}</span>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-graphite-800 text-amber-bright border border-amber-accent/20">
                    {evt.type}
                  </span>
                </div>
                <p className="text-xs text-cream-muted font-mono">{evt.detail}</p>
              </div>

              <div className="text-right flex-shrink-0">
                <span className="text-[11px] text-cream-muted font-mono">{evt.timestamp}</span>
                <p className="text-[10px] text-emerald-400 mt-0.5">
                  {(evt.confidence * 100).toFixed(0)}% conf
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
