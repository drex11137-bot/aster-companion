import React, { useState } from 'react';
import { X, Share2, ShieldCheck } from 'lucide-react';
import { useCompanion } from '../../context/CompanionContext';
import { MemoryItem, ProfileId } from '../../types';

interface MemorySharingModalProps {
  memory: MemoryItem | null;
  onClose: () => void;
}

export const MemorySharingModal: React.FC<MemorySharingModalProps> = ({
  memory,
  onClose,
}) => {
  const {
    activeProfile,
    profiles,
    shareMemoryToOtherProfile,
    showToast,
  } = useCompanion();

  const [confirmed, setConfirmed] = useState(false);
  const [includeAuditLog, setIncludeAuditLog] = useState(true);

  if (!memory) return null;

  const targetProfileId: ProfileId = activeProfile.id === 'profile-1' ? 'profile-2' : 'profile-1';
  const targetProfile = profiles[targetProfileId];

  const handleExecuteShare = () => {
    const result = shareMemoryToOtherProfile(memory.id);
    if (result.success) {
      showToast(result.message);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-md rounded-2xl bg-card-elevated border border-card-border p-6 shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-deep/20 border border-amber-accent/30 flex items-center justify-center text-amber-bright">
              <Share2 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-cream">
                Explicit Memory Sharing
              </h3>
              <p className="text-xs text-cream-muted">
                PRD Section 9.4 Controlled Cross-Profile Sharing
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-cream-muted hover:text-cream hover:bg-graphite-750 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Selected Memory Box */}
        <div className="p-3.5 rounded-xl bg-card-base border border-card-border space-y-1">
          <span className="text-[10px] uppercase font-bold tracking-wider text-amber-bright">
            Memory Content
          </span>
          <p className="text-sm font-medium text-cream">{memory.text}</p>
          <div className="flex items-center justify-between text-xs text-cream-muted pt-1">
            <span>Category: {memory.category}</span>
            <span>Provenance: {memory.provenance}</span>
          </div>
        </div>

        {/* Transfer Pathway */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-graphite-900 border border-card-border text-xs">
          <div>
            <span className="text-cream-muted block">Source Profile</span>
            <span className="font-bold text-cream">{activeProfile.name}</span>
          </div>
          <div className="text-amber-bright font-bold">➔</div>
          <div>
            <span className="text-cream-muted block">Destination Profile</span>
            <span className="font-bold text-cream">{targetProfile.name}</span>
          </div>
        </div>

        {/* Security Checklist & Explicit Confirmation */}
        <div className="space-y-2 text-xs text-cream-muted">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={includeAuditLog}
              onChange={(e) => setIncludeAuditLog(e.target.checked)}
              className="rounded border-graphite-600 bg-graphite-800 text-amber-bright focus:ring-amber-accent"
            />
            <span>Create immutable audit entry with timestamp & authorization</span>
          </label>

          <label className="flex items-start space-x-2 cursor-pointer pt-1">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
              className="mt-0.5 rounded border-graphite-600 bg-graphite-800 text-amber-bright focus:ring-amber-accent"
            />
            <span className="text-cream font-medium">
              I explicitly authorize sharing this memory with {targetProfile.name}.
            </span>
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl bg-card-base hover:bg-graphite-800 border border-card-border text-xs font-semibold text-cream transition-colors"
          >
            Cancel
          </button>

          <button
            type="button"
            disabled={!confirmed}
            onClick={handleExecuteShare}
            className={`flex-1 py-2.5 rounded-xl font-bold text-xs tracking-wide shadow-md transition-all flex items-center justify-center space-x-1.5 ${
              confirmed
                ? 'bg-amber-bright hover:bg-amber-accent text-graphite-950 active:scale-95'
                : 'bg-graphite-750 text-cream-muted/40 cursor-not-allowed'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Authorize & Share</span>
          </button>
        </div>
      </div>
    </div>
  );
};
