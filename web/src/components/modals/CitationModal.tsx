import React from 'react';
import { X, FileText, CheckCircle2, ShieldCheck, Sun, User, PlusCircle, Activity } from 'lucide-react';
import { useCompanion } from '../../context/CompanionContext';
import { MemoryIconType } from '../../types';

export const CitationModal: React.FC = () => {
  const {
    activeProfile,
    citationDrawerOpen,
    setCitationDrawerOpen,
    activeCitationMemories,
  } = useCompanion();

  if (!citationDrawerOpen) return null;

  const renderIcon = (type: MemoryIconType) => {
    switch (type) {
      case 'sun':
        return <Sun className="w-4 h-4 text-amber-bright" />;
      case 'person':
        return <User className="w-4 h-4 text-amber-bright" />;
      case 'health':
        return <PlusCircle className="w-4 h-4 text-amber-bright" />;
      case 'running':
        return <Activity className="w-4 h-4 text-amber-bright" />;
      default:
        return <Sun className="w-4 h-4 text-amber-bright" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-md rounded-2xl bg-card-elevated border border-card-border p-6 shadow-2xl space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-amber-deep/20 border border-amber-accent/30 flex items-center justify-center text-amber-bright">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-cream">
                Referenced Memories
              </h3>
              <p className="text-xs text-cream-muted">
                Used to personalize this recommendation
              </p>
            </div>
          </div>

          <button
            onClick={() => setCitationDrawerOpen(false)}
            className="p-1.5 rounded-lg text-cream-muted hover:text-cream hover:bg-graphite-750 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content list */}
        <div className="space-y-3">
          {activeCitationMemories.length === 0 ? (
            <p className="text-xs text-cream-muted text-center py-4">
              No memory details available for this citation.
            </p>
          ) : (
            activeCitationMemories.map((mem) => (
              <div
                key={mem.id}
                className="p-3.5 rounded-xl bg-card-base border border-card-border space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-7 h-7 rounded-full bg-graphite-800 border border-card-border flex items-center justify-center">
                      {renderIcon(mem.iconType)}
                    </div>
                    <span className="text-[11px] font-semibold text-amber-bright uppercase tracking-wider">
                      {mem.category}
                    </span>
                  </div>
                  <span className="text-[10px] text-emerald-400 font-mono flex items-center space-x-1">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>{(mem.confidence * 100).toFixed(0)}% match</span>
                  </span>
                </div>

                <p className="text-sm font-medium text-cream">{mem.text}</p>
                <div className="flex items-center justify-between text-[11px] text-cream-muted pt-1">
                  <span>{mem.addedAgo}</span>
                  <span className="text-[10px] text-cream-muted/70">
                    Provenance: {mem.provenance}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* PRD Transparency Note */}
        <div className="p-3 rounded-xl bg-graphite-900 border border-card-border flex items-start space-x-2 text-[11px] text-cream-muted">
          <ShieldCheck className="w-4 h-4 text-amber-bright flex-shrink-0 mt-0.5" />
          <span>
            {activeProfile.name} strictly discloses retrieved facts and never fabricates memories.
          </span>
        </div>

        <button
          onClick={() => setCitationDrawerOpen(false)}
          className="w-full py-2.5 rounded-xl bg-amber-bright hover:bg-amber-accent text-graphite-950 font-bold text-xs transition-colors"
        >
          Got it
        </button>
      </div>
    </div>
  );
};
