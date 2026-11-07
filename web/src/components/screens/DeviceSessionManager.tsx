import React from 'react';
import {
  Laptop,
  Smartphone,
  Tablet,
  ArrowRightLeft,
  ShieldCheck,
  CheckCircle2,
  Lock,
  RefreshCw,
} from 'lucide-react';
import { useCompanion } from '../../context/CompanionContext';
import { DeviceSession } from '../../types';

export const DeviceSessionManager: React.FC = () => {
  const {
    profiles,
    deviceSessions,
    handoverSession,
    revokeSession,
    showToast,
  } = useCompanion();

  const renderDeviceIcon = (type: DeviceSession['deviceType']) => {
    switch (type) {
      case 'laptop':
        return <Laptop className="w-5 h-5 text-amber-bright" />;
      case 'phone':
        return <Smartphone className="w-5 h-5 text-violet-accent" />;
      case 'tablet':
        return <Tablet className="w-5 h-5 text-cream-muted" />;
      default:
        return <Laptop className="w-5 h-5 text-amber-bright" />;
    }
  };

  const getSyncBadge = (state: DeviceSession['syncState']) => {
    switch (state) {
      case 'synced':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3" />
            <span>Synced</span>
          </span>
        );
      case 'checkpointed':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-deep/20 text-amber-bright border border-amber-accent/30">
            <RefreshCw className="w-3 h-3" />
            <span>Checkpointed</span>
          </span>
        );
      case 'buffering':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30">
            <RefreshCw className="w-3 h-3 animate-spin" />
            <span>Buffering</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-graphite-800 text-cream-muted border border-card-border">
            <span>Offline</span>
          </span>
        );
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-4 py-6 md:py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-cream">
          Cross-Device Sessions & Continuity
        </h1>
        <p className="text-xs md:text-sm text-cream-muted mt-0.5">
          Manage companion profiles and handover across your authorized devices.
        </p>
      </div>

      {/* PRD Architectural Rules Notice */}
      <div className="p-4 rounded-2xl bg-card-base border border-card-border space-y-2 text-xs text-cream-muted shadow-card">
        <div className="flex items-center space-x-2 text-amber-bright font-semibold">
          <ShieldCheck className="w-4 h-4" />
          <span>PRD v1.1 Profile Activation & Cross-Device Rules</span>
        </div>
        <ul className="list-disc list-inside space-y-1 text-cream-muted/90 pl-1">
          <li>
            <strong>Single Profile Per Device:</strong> Two different companion profiles cannot operate simultaneously on the same device.
          </li>
          <li>
            <strong>Cross-Device Freedom:</strong> Different profiles may operate simultaneously on different devices (e.g. Phone running Aster, Laptop running Nova).
          </li>
          <li>
            <strong>Session Handover:</strong> Hand over active awareness and conversational continuity seamlessly between laptop and phone.
          </li>
        </ul>
      </div>

      {/* Active Device Sessions List */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-cream">Authorized Devices</h3>

        <div className="rounded-2xl bg-card-base border border-card-border divide-y divide-card-border overflow-hidden shadow-card">
          {deviceSessions.map((dev) => {
            const activeCompanion = profiles[dev.activeProfileId];

            return (
              <div
                key={dev.deviceId}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-graphite-850/50 transition-colors"
              >
                {/* Device Info */}
                <div className="flex items-start space-x-3.5">
                  <div className="w-10 h-10 rounded-xl bg-graphite-900 border border-card-border flex items-center justify-center flex-shrink-0">
                    {renderDeviceIcon(dev.deviceType)}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="text-sm md:text-base font-semibold text-cream">
                        {dev.deviceName}
                      </h4>
                      {dev.isCurrentDevice && (
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-bright text-graphite-950">
                          This Device
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-3 text-xs text-cream-muted mt-1">
                      <span>IP: {dev.ipAddress}</span>
                      <span>•</span>
                      <span>Last active: {dev.lastActive}</span>
                    </div>
                  </div>
                </div>

                {/* Profile on Device & Actions */}
                <div className="flex items-center justify-between sm:justify-end space-x-3">
                  <div className="text-left sm:text-right">
                    <div className="text-xs text-cream-muted">Active Profile:</div>
                    <div className="text-xs md:text-sm font-bold text-cream flex items-center sm:justify-end space-x-1.5 mt-0.5">
                      <span className="w-2 h-2 rounded-full bg-amber-bright" />
                      <span>{activeCompanion.name}</span>
                    </div>
                    <div className="mt-1">{getSyncBadge(dev.syncState)}</div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-1.5">
                    {!dev.isCurrentDevice && (
                      <button
                        onClick={() => handoverSession(dev.deviceId)}
                        className="px-3 py-1.5 rounded-lg bg-graphite-800 hover:bg-graphite-750 border border-card-border text-xs text-cream flex items-center space-x-1.5 transition-colors"
                        title="Hand over active work to this device"
                      >
                        <ArrowRightLeft className="w-3.5 h-3.5 text-amber-bright" />
                        <span>Handover</span>
                      </button>
                    )}

                    {!dev.isCurrentDevice && (
                      <button
                        onClick={() => revokeSession(dev.deviceId)}
                        className="p-1.5 rounded-lg text-cream-muted hover:text-red-400 hover:bg-graphite-800 transition-colors"
                        title="Revoke session on this device"
                      >
                        <Lock className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Force Sync Action */}
      <div className="flex justify-end">
        <button
          onClick={() => showToast('All registered devices synchronized successfully.')}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-card-base hover:bg-graphite-800 border border-card-border text-xs font-semibold text-cream shadow-sm transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5 text-amber-bright" />
          <span>Synchronize Across Devices</span>
        </button>
      </div>
    </div>
  );
};
