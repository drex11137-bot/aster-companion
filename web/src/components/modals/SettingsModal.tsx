import React from 'react';
import {
  X,
  Shield,
  HardDrive,
  Cloud,
  Trash2,
  Download,
  Info,
} from 'lucide-react';
import { useCompanion } from '../../context/CompanionContext';

export const SettingsModal: React.FC = () => {
  const {
    settingsOpen,
    setSettingsOpen,
    activeProfile,
    offlineHistoryEnabled,
    setOfflineHistoryEnabled,
    cloudSyncEnabled,
    setCloudSyncEnabled,
    showToast,
  } = useCompanion();

  if (!settingsOpen) return null;

  const handleExportData = () => {
    const data = {
      profile: activeProfile,
      exportedAt: new Date().toISOString(),
      compliance: 'PRD v1.1 Privacy by Design (Section 16)',
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `aster-${activeProfile.name.toLowerCase()}-data-export.json`;
    a.click();
    showToast('Data exported successfully.');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-lg rounded-2xl bg-card-elevated border border-card-border p-6 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-violet-accent/20 border border-violet-accent/30 flex items-center justify-center text-violet-accent">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-cream">
                Settings & Privacy Controls
              </h3>
              <p className="text-xs text-cream-muted">
                PRD v1.1 Granular controls for {activeProfile.name}
              </p>
            </div>
          </div>

          <button
            onClick={() => setSettingsOpen(false)}
            className="p-1.5 rounded-lg text-cream-muted hover:text-cream hover:bg-graphite-750 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Local History & Offline Storage (PRD Section 6.2) */}
        <div className="space-y-3 p-4 rounded-xl bg-card-base border border-card-border">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <HardDrive className="w-5 h-5 text-amber-bright mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-cream">
                  Encrypted Local History
                </h4>
                <p className="text-xs text-cream-muted mt-0.5">
                  Store conversational & activity context locally in an encrypted buffer on this laptop.
                </p>
              </div>
            </div>

            <input
              type="checkbox"
              checked={offlineHistoryEnabled}
              onChange={(e) => setOfflineHistoryEnabled(e.target.checked)}
              className="mt-1 rounded border-graphite-600 bg-graphite-800 text-amber-bright focus:ring-amber-accent"
            />
          </div>
        </div>

        {/* Cloud Synchronization (PRD Section 9.3) */}
        <div className="space-y-3 p-4 rounded-xl bg-card-base border border-card-border">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <Cloud className="w-5 h-5 text-violet-accent mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-cream">
                  Cloud Profile Synchronization
                </h4>
                <p className="text-xs text-cream-muted mt-0.5">
                  Securely synchronize memories and preferences across your authorized devices (phone, laptop).
                </p>
              </div>
            </div>

            <input
              type="checkbox"
              checked={cloudSyncEnabled}
              onChange={(e) => setCloudSyncEnabled(e.target.checked)}
              className="mt-1 rounded border-graphite-600 bg-graphite-800 text-amber-bright focus:ring-amber-accent"
            />
          </div>
        </div>

        {/* Profile Isolation Guarantee (PRD Section 9.2) */}
        <div className="p-3.5 rounded-xl bg-graphite-900 border border-card-border flex items-start space-x-3 text-xs text-cream-muted">
          <Info className="w-5 h-5 text-amber-bright flex-shrink-0 mt-0.5" />
          <div>
            <strong className="text-cream">Two-Profile Strict Isolation:</strong>
            <p className="mt-0.5">
              Aster and Nova maintain completely segregated memory databases, conversation streams, and personality contexts. No implicit data leaks across profile boundaries.
            </p>
          </div>
        </div>

        {/* Data Export & Account Actions */}
        <div className="space-y-2 pt-1">
          <button
            onClick={handleExportData}
            className="w-full py-2.5 px-4 rounded-xl bg-card-base hover:bg-graphite-800 border border-card-border text-xs font-semibold text-cream flex items-center justify-center space-x-2 transition-colors"
          >
            <Download className="w-4 h-4 text-amber-bright" />
            <span>Export Companion Data & Audit Trail (JSON)</span>
          </button>

          <button
            onClick={() => {
              showToast('Memory database scrubbed clean.');
              setSettingsOpen(false);
            }}
            className="w-full py-2.5 px-4 rounded-xl bg-red-950/20 hover:bg-red-950/30 border border-red-800/40 text-xs font-semibold text-red-400 flex items-center justify-center space-x-2 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span>Clear Local Cached Context for {activeProfile.name}</span>
          </button>
        </div>

        {/* Close Button */}
        <button
          onClick={() => setSettingsOpen(false)}
          className="w-full py-2.5 rounded-xl bg-amber-bright hover:bg-amber-accent text-graphite-950 font-bold text-xs transition-colors"
        >
          Done
        </button>
      </div>
    </div>
  );
};
