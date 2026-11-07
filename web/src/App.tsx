import React, { useState } from 'react';
import {
  CompanionProvider,
  useCompanion,
} from './context/CompanionContext';
import { Header } from './components/Header';
import { Navigation } from './components/Navigation';
import { TodayScreen } from './components/screens/TodayScreen';
import { ChatScreen } from './components/screens/ChatScreen';
import { MemoriesScreen } from './components/screens/MemoriesScreen';
import { CompanionStudioScreen } from './components/screens/CompanionStudioScreen';
import { AwarenessScreen } from './components/screens/AwarenessScreen';
import { DeviceSessionManager } from './components/screens/DeviceSessionManager';
import { MemorySharingModal } from './components/modals/MemorySharingModal';
import { MemoryEditModal } from './components/modals/MemoryEditModal';
import { CitationModal } from './components/modals/CitationModal';
import { SettingsModal } from './components/modals/SettingsModal';
import { MemoryItem } from './types';
import { Wifi, Battery, Signal } from 'lucide-react';

const AppContent: React.FC = () => {
  const { activeTab, viewMode, toastMessage } = useCompanion();

  // Modal states
  const [sharingMemory, setSharingMemory] = useState<MemoryItem | null>(null);
  const [editingMemory, setEditingMemory] = useState<MemoryItem | null | undefined>(undefined);
  const [showEditModal, setShowEditModal] = useState(false);

  const renderActiveScreen = () => {
    switch (activeTab) {
      case 'today':
        return <TodayScreen />;
      case 'chat':
        return <ChatScreen />;
      case 'memories':
        return (
          <MemoriesScreen
            onOpenShareModal={(mem) => setSharingMemory(mem)}
            onOpenEditModal={(mem) => {
              setEditingMemory(mem || null);
              setShowEditModal(true);
            }}
          />
        );
      case 'studio':
        return <CompanionStudioScreen />;
      case 'awareness':
        return <AwarenessScreen />;
      case 'devices':
        return <DeviceSessionManager />;
      default:
        return <TodayScreen />;
    }
  };

  return (
    <div className="min-h-screen bg-graphite-950 text-cream flex flex-col font-sans">
      <Header />

      {viewMode === 'responsive-desktop' ? (
        /* Full Desktop Laptop Experience with Sidebar */
        <div className="flex-1 flex overflow-hidden">
          <Navigation />
          <main className="flex-1 overflow-y-auto pb-20 md:pb-8">
            {renderActiveScreen()}
          </main>
        </div>
      ) : (
        /* Mobile Device Frame Mode matching 100% Fidelity Screenshots */
        <div className="flex-1 flex items-center justify-center p-4 md:p-8 bg-graphite-900/60 overflow-y-auto">
          <div className="relative w-full max-w-[420px] h-[860px] bg-graphite-950 rounded-[44px] border-[8px] border-graphite-800 shadow-2xl overflow-hidden flex flex-col ring-1 ring-white/10">
            {/* Mobile Top Status Bar matching Screenshot headers ("8:24", battery 76%) */}
            <div className="h-10 px-6 flex items-center justify-between text-xs text-cream font-medium select-none bg-graphite-950/90 z-20">
              <span>8:24</span>
              {/* Notch */}
              <div className="w-20 h-4 bg-graphite-900 rounded-full" />
              <div className="flex items-center space-x-1.5 text-cream">
                <Signal className="w-3.5 h-3.5" />
                <Wifi className="w-3.5 h-3.5" />
                <span className="text-[11px] font-bold">76%</span>
                <Battery className="w-4 h-4" />
              </div>
            </div>

            {/* Screen Content Container */}
            <div className="flex-1 overflow-y-auto pb-16">
              {renderActiveScreen()}
            </div>

            {/* Mobile Bottom Bar Inside Frame */}
            <Navigation />

            {/* Bottom Home Indicator Bar (White pill as in Android/iOS) */}
            <div className="absolute bottom-1 left-1/2 -translate-x-1/2 w-32 h-1 bg-cream/70 rounded-full z-50 pointer-events-none" />
          </div>
        </div>
      )}

      {/* Modals */}
      <MemorySharingModal
        memory={sharingMemory}
        onClose={() => setSharingMemory(null)}
      />

      {showEditModal && (
        <MemoryEditModal
          memory={editingMemory}
          onClose={() => {
            setShowEditModal(false);
            setEditingMemory(undefined);
          }}
        />
      )}

      <CitationModal />
      <SettingsModal />

      {/* Global Toast Alert */}
      {toastMessage && (
        <div className="fixed bottom-20 md:bottom-8 left-1/2 -translate-x-1/2 px-4 py-2.5 rounded-full bg-graphite-850 border border-card-border text-xs md:text-sm text-cream shadow-2xl z-50 animate-bounce flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-amber-bright" />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <CompanionProvider>
      <AppContent />
    </CompanionProvider>
  );
};

export default App;
