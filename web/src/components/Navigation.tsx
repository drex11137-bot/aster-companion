import React from 'react';
import {
  Home,
  MessageSquare,
  BookOpen,
  User,
  Monitor,
  Smartphone,
  Radio,
  Settings,
} from 'lucide-react';
import { useCompanion, NavTab } from '../context/CompanionContext';
import { AvatarCanvas } from './AvatarCanvas';

export const Navigation: React.FC = () => {
  const {
    activeTab,
    setActiveTab,
    activeProfile,
    isAwarenessActive,
    isAwarenessPaused,
    setSettingsOpen,
  } = useCompanion();

  // Mobile Bottom Navigation tabs matching the 4 screenshots
  const mobileNavItems: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    {
      id: 'today',
      label: 'Today',
      icon: <Home className="w-5 h-5" />,
    },
    {
      id: 'chat',
      label: 'Chat',
      icon: <MessageSquare className="w-5 h-5" />,
    },
    {
      id: 'memories',
      label: 'Memory',
      icon: <BookOpen className="w-5 h-5" />,
    },
    {
      id: 'studio',
      label: 'Companion',
      icon: <User className="w-5 h-5" />,
    },
  ];

  // Desktop Laptop Sidebar items (includes Awareness and Cross-Device sessions)
  const desktopNavItems: {
    id: NavTab;
    label: string;
    icon: React.ReactNode;
    badge?: string;
  }[] = [
    {
      id: 'today',
      label: 'Today',
      icon: <Home className="w-5 h-5" />,
    },
    {
      id: 'chat',
      label: 'Chat',
      icon: <MessageSquare className="w-5 h-5" />,
    },
    {
      id: 'memories',
      label: 'Memories',
      icon: <BookOpen className="w-5 h-5" />,
    },
    {
      id: 'studio',
      label: 'Companion Studio',
      icon: <User className="w-5 h-5" />,
    },
    {
      id: 'awareness',
      label: 'Awareness & Screen',
      icon: <Monitor className="w-5 h-5" />,
      badge: isAwarenessActive ? (isAwarenessPaused ? 'Paused' : 'Live') : undefined,
    },
    {
      id: 'devices',
      label: 'Cross-Device Sessions',
      icon: <Smartphone className="w-5 h-5" />,
    },
  ];

  return (
    <>
      {/* Mobile Bottom Navigation Bar matching Screenshot bottom navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-graphite-950/95 backdrop-blur border-t border-card-border/70 flex items-center justify-around px-2 z-40">
        {mobileNavItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className="flex flex-col items-center justify-center flex-1 py-1 group"
            >
              {/* Rounded capsule pill for active tab - exactly like Screenshot 1 & 2 */}
              <div
                className={`flex items-center justify-center transition-all ${
                  isActive
                    ? 'w-14 h-7 rounded-full bg-amber-deep/30 border border-amber-accent/40 text-amber-bright'
                    : 'w-10 h-7 rounded-full text-cream-muted group-hover:text-cream'
                }`}
              >
                {item.icon}
              </div>
              <span
                className={`text-[10px] mt-0.5 tracking-tight font-medium ${
                  isActive ? 'text-amber-bright font-bold' : 'text-cream-muted group-hover:text-cream'
                }`}
              >
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Desktop Laptop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 h-screen bg-graphite-900 border-r border-card-border p-4 sticky top-0 flex-shrink-0 z-30">
        {/* Brand Header */}
        <div className="flex items-center space-x-3 px-2 py-3 mb-4">
          <div className="relative">
            <AvatarCanvas
              size={42}
              hairColor={activeProfile.hair}
              eyeColor={activeProfile.eyes}
              showStatusDot={true}
              glowIntensity="subtle"
            />
          </div>
          <div>
            <h2 className="text-base font-bold text-cream leading-tight">
              Aster Companion
            </h2>
            <div className="flex items-center space-x-1.5 mt-0.5">
              <span className="w-2 h-2 rounded-full bg-online animate-pulse" />
              <p className="text-xs text-cream-muted font-medium">
                {activeProfile.name} • Active
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <div className="space-y-1.5 flex-1">
          {desktopNavItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-amber-deep/20 text-cream border border-amber-bright/40 shadow-sm font-semibold'
                    : 'text-cream-muted hover:text-cream hover:bg-graphite-800'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <span className={isActive ? 'text-amber-bright' : 'text-cream-muted'}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </div>

                {item.badge && (
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                      item.badge === 'Live'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 animate-pulse'
                        : 'bg-amber-deep/30 text-amber-bright border border-amber-accent/30'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Continuous Awareness Subtle Status Widget */}
        <div className="p-3.5 rounded-2xl bg-card-base border border-card-border mb-3 shadow-card space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Radio className="w-3.5 h-3.5 text-amber-bright" />
              <span className="text-xs font-semibold text-cream">Screen Awareness</span>
            </div>
            <span
              className={`w-2 h-2 rounded-full ${
                isAwarenessActive
                  ? isAwarenessPaused
                    ? 'bg-amber-bright'
                    : 'bg-online animate-ping'
                  : 'bg-cream-muted/50'
              }`}
            />
          </div>
          <p className="text-[11px] text-cream-muted leading-tight">
            {isAwarenessActive
              ? isAwarenessPaused
                ? 'Capture paused. Zero frame transmission.'
                : 'Capturing active laptop display context.'
              : 'Standby mode. Click to start continuous capture.'}
          </p>
          <button
            onClick={() => setActiveTab('awareness')}
            className="w-full py-1.5 rounded-lg bg-graphite-800 hover:bg-graphite-750 text-[11px] font-medium text-cream border border-card-border transition-colors"
          >
            Open Awareness HUD
          </button>
        </div>

        {/* Settings button */}
        <button
          onClick={() => setSettingsOpen(true)}
          className="flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-medium text-cream-muted hover:text-cream hover:bg-graphite-800 transition-colors"
        >
          <Settings className="w-4 h-4" />
          <span>Settings & Privacy</span>
        </button>
      </aside>
    </>
  );
};
