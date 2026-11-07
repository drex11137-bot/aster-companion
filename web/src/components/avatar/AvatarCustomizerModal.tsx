/**
 * AvatarCustomizerModal.tsx
 * Aster Companion - Avatar Studio & Customizer
 *
 * Implements the companion customization studio matching screenshot a98599e6-e707-4cb8-a85f-85293d19df71.png:
 * - Profile switcher tabs ('Aster' vs 'Nova') with complete profile isolation
 * - Centered live AvatarCanvas preview with warm amber halo glow and interactive 3D parallax
 * - Procedural lip-sync and audio speech simulation preview
 * - Editable companion name with pencil edit icon
 * - Hair color swatches (Auburn, Black, Brown, Blonde, Silver)
 * - Eye color swatches (Hazel, Brown, Blue, Green, Grey)
 * - Style chips (Natural, Casual, Professional, Creative)
 * - Voice tone chips (Warm voice, Calm, Energetic, Playful)
 * - Low-power / accessibility "No-avatar mode" toggle
 * - Full-width "Save companion" action button
 * - Canonical 4-tab bottom navigation bar
 */

import React, { useState, useEffect } from 'react';
import {
  Settings,
  Pencil,
  Check,
  Volume2,
  Sparkles,
  Home,
  MessageCircle,
  BookOpen,
  User,
  Power,
  X,
} from 'lucide-react';
import { useCompanion } from '../../context/CompanionContext';
import { HairColor, EyeColor, CompanionStyle, VoiceTone, ProfileId } from '../../types';
import { AvatarCanvas, HAIR_COLOR_MAP, EYE_COLOR_MAP } from './AvatarCanvas';
import { sharedVisemeEngine } from './VisemeLipSyncEngine';

export interface AvatarCustomizerModalProps {
  isOpen?: boolean;
  onClose?: () => void;
  isModal?: boolean; // true if overlay modal, false if main tab view
}

const HAIR_OPTIONS: HairColor[] = ['Auburn', 'Black', 'Brown', 'Blonde', 'Silver'];
const EYE_OPTIONS: EyeColor[] = ['Hazel', 'Brown', 'Blue', 'Green', 'Grey'];
const STYLE_OPTIONS: CompanionStyle[] = ['Natural', 'Casual', 'Professional', 'Creative'];
const VOICE_OPTIONS: VoiceTone[] = ['Warm voice', 'Calm', 'Energetic', 'Playful'];

export const AvatarCustomizerModal: React.FC<AvatarCustomizerModalProps> = ({
  isOpen = true,
  onClose,
  isModal = false,
}) => {
  const {
    activeProfileId,
    activeProfile,
    switchProfile,
    updateProfile,
    showToast,
    setActiveTab,
    activeTab,
  } = useCompanion();

  // Active form state initialized from current companion profile
  const [name, setName] = useState(activeProfile?.name || 'Aster');
  const [isEditingName, setIsEditingName] = useState(false);
  const [hair, setHair] = useState<HairColor>(activeProfile?.hair || 'Auburn');
  const [eyes, setEyes] = useState<EyeColor>(activeProfile?.eyes || 'Hazel');
  const [style, setStyle] = useState<CompanionStyle>(activeProfile?.style || 'Natural');
  const [voice, setVoice] = useState<VoiceTone>(activeProfile?.voice || 'Warm voice');
  const [noAvatarMode, setNoAvatarMode] = useState<boolean>(false);
  const [isTestingVoice, setIsTestingVoice] = useState<boolean>(false);
  const [isSaved, setIsSaved] = useState<boolean>(false);

  // Sync state whenever active profile changes
  useEffect(() => {
    if (activeProfile) {
      setName(activeProfile.name);
      setHair(activeProfile.hair);
      setEyes(activeProfile.eyes);
      setStyle(activeProfile.style);
      setVoice(activeProfile.voice);
    }
  }, [activeProfile, activeProfileId]);

  if (!isOpen && isModal) return null;

  // Handle switching between profile 1 ('Aster') and profile 2 ('Nova')
  const handleSelectProfileTab = (targetId: ProfileId) => {
    if (targetId !== activeProfileId) {
      switchProfile(targetId);
      setIsEditingName(false);
      showToast(`Switched to ${targetId === 'profile-1' ? 'Aster' : 'Nova'}`);
    }
  };

  // Test Voice & LipSync procedural preview
  const handleTestVoice = async () => {
    setIsTestingVoice(true);
    const phrases: Record<VoiceTone, string> = {
      'Warm voice': `Hello! I'm ${name}. I'm here to accompany your day with warmth and mindful clarity.`,
      Calm: `Take a quiet breath. I'm ${name}, ready whenever you'd like to reflect or slow down.`,
      Energetic: `Let's make today fantastic! I'm ${name}, excited to dive into your next big idea!`,
      Playful: `Hey there! Ready to explore something fun? ${name} at your service!`,
    };

    try {
      await sharedVisemeEngine.simulateSpeech(phrases[voice], 3500, voice);
    } finally {
      setTimeout(() => {
        setIsTestingVoice(false);
      }, 3600);
    }
  };

  // Save changes to companion profile
  const handleSave = () => {
    updateProfile(activeProfileId, {
      name: name.trim() || activeProfile.name,
      hair,
      eyes,
      style,
      voice,
    });
    setIsEditingName(false);
    setIsSaved(true);
    showToast(`${name} profile saved successfully`);
    setTimeout(() => setIsSaved(false), 2000);
    if (isModal && onClose) {
      setTimeout(onClose, 600);
    }
  };

  const content = (
    <div className="flex flex-col h-full bg-graphite-950 text-cream select-none overflow-y-auto no-scrollbar pb-24">
      {/* 1. Header Bar matching PNG screenshot a98599e6-e707-4cb8-a85f-85293d19df71.png */}
      <div className="flex items-center justify-between px-6 pt-5 pb-2">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Your companion</h1>
          <p className="text-sm text-cream-muted mt-0.5">Make it yours</p>
        </div>
        <div className="flex items-center gap-2">
          {isModal && onClose && (
            <button
              onClick={onClose}
              className="p-2 rounded-full hover:bg-graphite-800 text-cream-muted hover:text-white transition-colors"
              title="Close modal"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          )}
          <button
            onClick={() => showToast('Companion Settings & Isolation Guard')}
            className="p-2 rounded-full hover:bg-graphite-800 text-cream-muted hover:text-cream transition-colors"
            title="Settings"
            aria-label="Settings"
          >
            <Settings className="w-5 h-5 text-cream-soft" />
          </button>
        </div>
      </div>

      {/* 2. Avatar Canvas Preview with Warm Amber Halo */}
      <div className="flex flex-col items-center justify-center my-4 relative">
        <AvatarCanvas
          size={210}
          hairColor={hair}
          eyeColor={eyes}
          style={style}
          isInteractive={true}
          showStatusDot={true}
          noAvatarMode={noAvatarMode}
          glowIntensity="high"
          onAvatarClick={handleTestVoice}
        />

        {/* Quick Voice / Lip-Sync Preview Button */}
        <button
          onClick={handleTestVoice}
          disabled={isTestingVoice}
          className="mt-3 inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-medium bg-graphite-850 hover:bg-graphite-800 border border-amber-accent/30 text-amber-bright transition-all shadow-sm active:scale-95"
          title="Click to hear voice & watch real-time lip-sync"
        >
          <Volume2 className={`w-3.5 h-3.5 ${isTestingVoice ? 'animate-bounce text-amber-bright' : ''}`} />
          <span>{isTestingVoice ? 'Speaking & sync...' : 'Preview voice & lip-sync'}</span>
        </button>
      </div>

      <div className="px-5 space-y-6">
        {/* 3. Profile Tabs ('Aster' vs 'Nova') */}
        <div className="flex bg-graphite-900 rounded-full p-1 border border-card-border">
          <button
            onClick={() => handleSelectProfileTab('profile-1')}
            className={`flex-1 py-2 text-sm font-medium rounded-full transition-all duration-200 ${
              activeProfileId === 'profile-1'
                ? 'bg-amber-dim/40 border border-amber-accent text-amber-bright shadow-sm'
                : 'text-cream-muted hover:text-white'
            }`}
          >
            Aster
          </button>
          <button
            onClick={() => handleSelectProfileTab('profile-2')}
            className={`flex-1 py-2 text-sm font-medium rounded-full transition-all duration-200 ${
              activeProfileId === 'profile-2'
                ? 'bg-amber-dim/40 border border-amber-accent text-amber-bright shadow-sm'
                : 'text-cream-muted hover:text-white'
            }`}
          >
            Nova
          </button>
        </div>

        {/* 4. Name Field with Edit Pencil */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-cream-muted tracking-wide">Name</label>
          <div className="flex items-center justify-between px-4 py-3 rounded-xl bg-card-base border border-card-border transition-colors focus-within:border-amber-accent/60">
            {isEditingName ? (
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') setIsEditingName(false);
                }}
                autoFocus
                className="bg-transparent text-sm font-medium text-white focus:outline-none w-full"
                placeholder="Enter companion name"
              />
            ) : (
              <span className="text-sm font-medium text-white">{name}</span>
            )}

            <button
              onClick={() => setIsEditingName(!isEditingName)}
              className="p-1 rounded text-cream-muted hover:text-amber-bright transition-colors"
              title={isEditingName ? 'Save name' : 'Edit name'}
            >
              {isEditingName ? (
                <Check className="w-4 h-4 text-online" />
              ) : (
                <Pencil className="w-4 h-4 text-cream-muted hover:text-white" />
              )}
            </button>
          </div>
        </div>

        {/* 5. Appearance Section */}
        <div className="space-y-4">
          <h2 className="text-xs font-medium uppercase tracking-wider text-cream-muted">
            Appearance
          </h2>

          {/* Hair Swatches */}
          <div className="space-y-2">
            <span className="text-xs text-cream-soft font-medium">Hair</span>
            <div className="flex items-center justify-between pt-1">
              {HAIR_OPTIONS.map((colorKey) => {
                const spec = HAIR_COLOR_MAP[colorKey];
                const isSelected = hair === colorKey;
                return (
                  <button
                    key={colorKey}
                    onClick={() => setHair(colorKey)}
                    className="flex flex-col items-center gap-1.5 group focus:outline-none"
                    title={spec.label}
                  >
                    <div
                      className={`w-10 h-10 rounded-full transition-all duration-200 border border-white/10 ${
                        isSelected
                          ? 'ring-2 ring-amber-accent ring-offset-2 ring-offset-graphite-950 scale-105'
                          : 'opacity-85 hover:opacity-100'
                      }`}
                      style={{ backgroundColor: spec.hex }}
                    />
                    <span
                      className={`text-[11px] font-medium transition-colors ${
                        isSelected ? 'text-amber-bright font-semibold' : 'text-cream-muted group-hover:text-cream'
                      }`}
                    >
                      {spec.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Eyes Swatches */}
          <div className="space-y-2 pt-2">
            <span className="text-xs text-cream-soft font-medium">Eyes</span>
            <div className="flex items-center justify-between pt-1">
              {EYE_OPTIONS.map((colorKey) => {
                const spec = EYE_COLOR_MAP[colorKey];
                const isSelected = eyes === colorKey;
                return (
                  <button
                    key={colorKey}
                    onClick={() => setEyes(colorKey)}
                    className="flex flex-col items-center gap-1.5 group focus:outline-none"
                    title={spec.label}
                  >
                    <div
                      className={`w-10 h-10 rounded-full transition-all duration-200 border border-white/10 ${
                        isSelected
                          ? 'ring-2 ring-amber-accent ring-offset-2 ring-offset-graphite-950 scale-105'
                          : 'opacity-85 hover:opacity-100'
                      }`}
                      style={{ backgroundColor: spec.hex }}
                    />
                    <span
                      className={`text-[11px] font-medium transition-colors ${
                        isSelected ? 'text-amber-bright font-semibold' : 'text-cream-muted group-hover:text-cream'
                      }`}
                    >
                      {spec.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Style Chips */}
          <div className="space-y-2 pt-2">
            <span className="text-xs text-cream-soft font-medium">Style</span>
            <div className="grid grid-cols-4 gap-2">
              {STYLE_OPTIONS.map((styleKey) => {
                const isSelected = style === styleKey;
                return (
                  <button
                    key={styleKey}
                    onClick={() => setStyle(styleKey)}
                    className={`py-2 px-1 text-center rounded-xl text-xs font-medium border transition-all duration-150 ${
                      isSelected
                        ? 'border-amber-accent text-amber-bright bg-amber-dim/30 shadow-sm'
                        : 'border-card-border bg-card-base text-cream-soft hover:border-graphite-600'
                    }`}
                  >
                    {styleKey}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* 6. Voice Section */}
        <div className="space-y-2">
          <label className="text-xs font-medium uppercase tracking-wider text-cream-muted">
            Voice
          </label>
          <div className="grid grid-cols-4 gap-2">
            {VOICE_OPTIONS.map((voiceKey) => {
              const isSelected = voice === voiceKey;
              return (
                <button
                  key={voiceKey}
                  onClick={() => setVoice(voiceKey)}
                  className={`py-2 px-1 text-center rounded-xl text-xs font-medium border transition-all duration-150 ${
                    isSelected
                      ? 'border-amber-accent text-amber-bright bg-amber-dim/30 shadow-sm'
                      : 'border-card-border bg-card-base text-cream-soft hover:border-graphite-600'
                  }`}
                >
                  {voiceKey}
                </button>
              );
            })}
          </div>
        </div>

        {/* 7. Low-Power / Accessibility Preference (No-Avatar Mode) */}
        <div className="pt-1 flex items-center justify-between p-3 rounded-xl bg-graphite-900 border border-card-border">
          <div className="flex items-center gap-2.5">
            <Power className={`w-4 h-4 ${noAvatarMode ? 'text-amber-bright' : 'text-cream-muted'}`} />
            <div>
              <p className="text-xs font-medium text-cream-soft">No-avatar mode</p>
              <p className="text-[11px] text-cream-muted">Audio pulse & low battery draw</p>
            </div>
          </div>
          <button
            onClick={() => setNoAvatarMode(!noAvatarMode)}
            role="switch"
            aria-checked={noAvatarMode}
            className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors duration-200 ease-in-out ${
              noAvatarMode ? 'bg-amber-bright' : 'bg-graphite-750'
            }`}
          >
            <div
              className={`bg-graphite-950 w-4 h-4 rounded-full shadow-md transform transition-transform duration-200 ease-in-out ${
                noAvatarMode ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* 8. Save Action Button matching screenshot a98599e6 */}
        <div className="pt-2">
          <button
            onClick={handleSave}
            className="w-full py-3.5 rounded-full bg-amber-bright hover:bg-amber-accent active:scale-[0.99] text-graphite-950 font-semibold text-sm transition-all duration-200 shadow-amber-glow flex items-center justify-center gap-2"
          >
            {isSaved ? (
              <>
                <Check className="w-4 h-4 text-graphite-950" />
                <span>Companion saved</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-graphite-950/70" />
                <span>Save companion</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* 9. Canonical 4-Tab Bottom Navigation Bar */}
      {!isModal && (
        <div className="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-graphite-950/95 backdrop-blur-md border-t border-card-border px-6 py-2 flex items-center justify-between z-30">
          <button
            onClick={() => setActiveTab('today')}
            className={`flex flex-col items-center gap-1 text-[11px] font-medium transition-colors ${
              activeTab === 'today' ? 'text-amber-bright' : 'text-cream-muted hover:text-white'
            }`}
          >
            <Home className="w-5 h-5" />
            <span>Today</span>
          </button>

          <button
            onClick={() => setActiveTab('chat')}
            className={`flex flex-col items-center gap-1 text-[11px] font-medium transition-colors ${
              activeTab === 'chat' ? 'text-amber-bright' : 'text-cream-muted hover:text-white'
            }`}
          >
            <MessageCircle className="w-5 h-5" />
            <span>Chat</span>
          </button>

          <button
            onClick={() => setActiveTab('memories')}
            className={`flex flex-col items-center gap-1 text-[11px] font-medium transition-colors ${
              activeTab === 'memories' ? 'text-amber-bright' : 'text-cream-muted hover:text-white'
            }`}
          >
            <BookOpen className="w-5 h-5" />
            <span>Memory</span>
          </button>

          <button
            onClick={() => setActiveTab('studio')}
            className="flex flex-col items-center gap-1 text-[11px] font-semibold text-amber-bright"
          >
            <div className="px-4 py-1 rounded-full bg-amber-dim/50 border border-amber-accent/40 text-amber-bright">
              <User className="w-4 h-4" />
            </div>
            <span>Companion</span>
          </button>
        </div>
      )}
    </div>
  );

  if (isModal) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
        <div className="w-full max-w-md h-[90vh] bg-graphite-950 rounded-2xl overflow-hidden shadow-2xl border border-card-border flex flex-col">
          {content}
        </div>
      </div>
    );
  }

  return content;
};

export default AvatarCustomizerModal;
