import React, { useState, useRef, useEffect } from 'react';
import {
  Search,
  MoreVertical,
  Calendar,
  FileText,
  Mic,
  Send,
  Coffee,
  Dumbbell,
  Utensils,
  BookOpen,
  Moon,
  Paperclip,
  CheckCheck,
  StopCircle,
} from 'lucide-react';
import { useCompanion } from '../../context/CompanionContext';
import { AvatarCanvas } from '../AvatarCanvas';
import { ScheduleEvent } from '../../types';

export const ChatScreen: React.FC = () => {
  const {
    activeProfile,
    messages,
    sendMessage,
    isStreaming,
    inspectCitations,
    addReminder,
    setActiveTab,
  } = useCompanion();

  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [showMenu, setShowMenu] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  // Voice recording simulation with WebAudio
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isRecording) {
      timer = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } else {
      setRecordingTime(0);
    }
    return () => clearInterval(timer);
  }, [isRecording]);

  const handleSend = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim()) return;
    sendMessage(inputText.trim());
    setInputText('');
  };

  const handleToggleRecord = () => {
    if (!isRecording) {
      setIsRecording(true);
    } else {
      setIsRecording(false);
      // Simulate recognized speech after mic input
      const transcript = "Can you check my schedule for tomorrow morning?";
      setInputText(transcript);
    }
  };

  const handleQuickAddReminder = () => {
    addReminder('Review weekly goals', '9:00 AM', 'Tomorrow');
    sendMessage('Please remind me to review weekly goals tomorrow at 9:00 AM.');
  };

  const handleQuickSummarize = () => {
    sendMessage('Can you summarize my priorities and memories for this week?');
  };

  const renderScheduleIcon = (iconName: ScheduleEvent['icon']) => {
    switch (iconName) {
      case 'coffee':
        return <Coffee className="w-4 h-4 text-amber-bright" />;
      case 'dumbbell':
        return <Dumbbell className="w-4 h-4 text-amber-bright" />;
      case 'utensils':
        return <Utensils className="w-4 h-4 text-amber-bright" />;
      case 'book':
        return <BookOpen className="w-4 h-4 text-amber-bright" />;
      case 'moon':
        return <Moon className="w-4 h-4 text-amber-bright" />;
      default:
        return <Coffee className="w-4 h-4 text-amber-bright" />;
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-2xl mx-auto px-3 md:px-4">
      {/* Top Bar matching Screenshot 3 */}
      <div className="flex items-center justify-between py-3 border-b border-card-border/60 bg-graphite-950/80 backdrop-blur sticky top-0 z-20">
        <div className="flex items-center space-x-3">
          <AvatarCanvas
            size={40}
            hairColor={activeProfile.hair}
            eyeColor={activeProfile.eyes}
            showStatusDot={true}
            glowIntensity="subtle"
          />
          <div>
            <h2 className="text-base font-bold text-cream leading-tight">
              {activeProfile.name}
            </h2>
            <p className="text-xs text-cream-muted leading-tight">Online</p>
          </div>
        </div>

        <div className="relative flex items-center space-x-1">
          <button
            onClick={() => setActiveTab('memories')}
            className="p-2 text-cream-muted hover:text-cream rounded-full hover:bg-graphite-850 transition-colors"
            title="Search context"
          >
            <Search className="w-5 h-5" />
          </button>
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-2 text-cream-muted hover:text-cream rounded-full hover:bg-graphite-850 transition-colors"
            title="Options"
          >
            <MoreVertical className="w-5 h-5" />
          </button>

          {showMenu && (
            <div className="absolute right-0 top-10 w-48 rounded-xl bg-card-elevated border border-card-border py-1 shadow-card z-50">
              <button
                onClick={() => {
                  setShowMenu(false);
                  setActiveTab('studio');
                }}
                className="w-full px-4 py-2 text-left text-xs text-cream hover:bg-graphite-750 flex items-center space-x-2"
              >
                <span>Edit Companion</span>
              </button>
              <button
                onClick={() => {
                  setShowMenu(false);
                  setActiveTab('awareness');
                }}
                className="w-full px-4 py-2 text-left text-xs text-cream hover:bg-graphite-750 flex items-center space-x-2"
              >
                <span>Awareness Mode</span>
              </button>
              <button
                onClick={() => {
                  setShowMenu(false);
                  setActiveTab('devices');
                }}
                className="w-full px-4 py-2 text-left text-xs text-cream hover:bg-graphite-750 flex items-center space-x-2"
              >
                <span>Device Sessions</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Messages Thread */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4">
        {/* Date divider */}
        <div className="text-center my-2">
          <span className="text-xs text-cream-muted/70 tracking-wide font-medium">
            Today 8:20 PM
          </span>
        </div>

        {messages.map((msg) => (
          <div key={msg.id} className="space-y-1">
            {msg.sender === 'user' ? (
              /* User Bubble (Violet, right-aligned) */
              <div className="flex flex-col items-end">
                <div className="max-w-[85%] rounded-3xl rounded-br-md px-5 py-3 bg-violet-accent text-white shadow-md text-sm md:text-base leading-relaxed">
                  {msg.text}
                </div>
                <div className="flex items-center space-x-1 mt-1 mr-1 text-[11px] text-cream-muted">
                  <span>{msg.timeLabel}</span>
                  <CheckCheck className="w-3.5 h-3.5 text-violet-accent" />
                </div>
              </div>
            ) : (
              /* Aster Companion Bubble (Dark Graphite, left-aligned) */
              <div className="flex items-start space-x-2.5 max-w-[92%]">
                <div className="mt-1 flex-shrink-0">
                  <AvatarCanvas
                    size={28}
                    hairColor={activeProfile.hair}
                    eyeColor={activeProfile.eyes}
                    showStatusDot={false}
                    glowIntensity="subtle"
                  />
                </div>

                <div className="space-y-2 flex-1">
                  {/* Bubble text */}
                  <div className="rounded-2xl rounded-tl-sm px-4 py-3 bg-card-base border border-card-border text-cream text-sm md:text-base leading-relaxed shadow-card">
                    {msg.text}
                  </div>

                  {/* Saturday Schedule Card (Interactive Timeline) */}
                  {msg.scheduleCard && (
                    <div className="rounded-2xl bg-card-base border border-card-border p-4 shadow-card space-y-4">
                      <div>
                        <h4 className="text-sm md:text-base font-semibold text-cream">
                          {msg.scheduleCard.dateTitle}
                        </h4>
                        <p className="text-xs text-cream-muted">
                          {msg.scheduleCard.subtitle}
                        </p>
                      </div>

                      {/* Vertical Timeline */}
                      <div className="relative pl-6 space-y-5">
                        {/* Vertical line connecting nodes */}
                        <div className="absolute left-[13px] top-2 bottom-2 w-0.5 bg-graphite-700" />

                        {msg.scheduleCard.events.map((event, idx) => (
                          <div key={idx} className="relative flex items-start space-x-3.5">
                            {/* Circle icon node */}
                            <div className="absolute -left-6 w-7 h-7 rounded-full bg-graphite-800 border border-amber-accent/30 flex items-center justify-center shadow-sm z-10">
                              {renderScheduleIcon(event.icon)}
                            </div>

                            <div className="pl-3">
                              <span className="text-[11px] font-semibold text-amber-bright uppercase tracking-wider">
                                {event.time}
                              </span>
                              <h5 className="text-xs md:text-sm font-medium text-cream leading-snug">
                                {event.title}
                              </h5>
                              <p className="text-xs text-cream-muted leading-tight mt-0.5">
                                {event.description}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Citation Chip: 'Used 2 memories' */}
                  {msg.citations && (
                    <button
                      onClick={() => inspectCitations(msg.citations?.memoryIds || [])}
                      className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-graphite-850 hover:bg-graphite-800 border border-card-border text-xs text-cream-muted hover:text-cream transition-all shadow-sm active:scale-95"
                    >
                      <FileText className="w-3.5 h-3.5 text-cream-muted" />
                      <span>Used {msg.citations.count} memories</span>
                    </button>
                  )}

                  <div className="text-[11px] text-cream-muted ml-1">
                    {msg.timeLabel}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Streaming typing indicator */}
        {isStreaming && (
          <div className="flex items-center space-x-2 text-cream-muted text-xs pl-10 py-2">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-accent animate-bounce" />
            <span className="w-1.5 h-1.5 rounded-full bg-amber-accent animate-bounce [animation-delay:0.2s]" />
            <span className="w-1.5 h-1.5 rounded-full bg-amber-accent animate-bounce [animation-delay:0.4s]" />
            <span className="ml-1 text-[11px]">{activeProfile.name} is thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Action Pills above Input */}
      <div className="flex items-center space-x-2 py-2">
        <button
          onClick={handleQuickAddReminder}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-card-base hover:bg-graphite-800 border border-card-border text-xs font-medium text-cream shadow-sm transition-colors"
        >
          <Calendar className="w-3.5 h-3.5 text-amber-bright" />
          <span>Add reminder</span>
        </button>

        <button
          onClick={handleQuickSummarize}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-card-base hover:bg-graphite-800 border border-card-border text-xs font-medium text-cream shadow-sm transition-colors"
        >
          <FileText className="w-3.5 h-3.5 text-violet-accent" />
          <span>Summarize</span>
        </button>
      </div>

      {/* Input Field & Audio Mic / Send Button */}
      <div className="pb-3 pt-1">
        {isRecording && (
          <div className="flex items-center justify-between px-4 py-2 mb-2 rounded-2xl bg-amber-deep/20 border border-amber-accent/40 text-cream text-xs">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
              <span>Recording audio ({recordingTime}s)... Speak naturally</span>
            </div>
            <button
              onClick={handleToggleRecord}
              className="text-amber-bright hover:underline font-semibold"
            >
              Done & Transcribe
            </button>
          </div>
        )}

        <form
          onSubmit={handleSend}
          className="flex items-center bg-card-base border border-card-border rounded-full p-1.5 shadow-card focus-within:border-amber-accent/80 transition-colors"
        >
          <button
            type="button"
            className="p-2 text-cream-muted hover:text-cream rounded-full hover:bg-graphite-800 transition-colors ml-1"
            title="Attach file or screenshot"
          >
            <Paperclip className="w-4 h-4" />
          </button>

          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={`Message ${activeProfile.name}`}
            className="flex-1 bg-transparent border-none px-3 py-1.5 text-sm md:text-base text-cream placeholder-cream-muted/50 focus:outline-none"
          />

          {/* WebAudio Mic Button */}
          <button
            type="button"
            onClick={handleToggleRecord}
            className={`p-2 rounded-full transition-colors mr-1 ${
              isRecording
                ? 'bg-red-500/20 text-red-400'
                : 'text-cream-muted hover:text-cream hover:bg-graphite-800'
            }`}
            title={isRecording ? 'Stop recording' : 'Speak to Aster'}
          >
            {isRecording ? <StopCircle className="w-5 h-5 text-red-400" /> : <Mic className="w-5 h-5" />}
          </button>

          {/* Amber Send Button */}
          <button
            type="submit"
            disabled={!inputText.trim()}
            className={`w-9 h-9 rounded-full flex items-center justify-center transition-all ${
              inputText.trim()
                ? 'bg-amber-bright text-graphite-950 shadow-md hover:bg-amber-accent active:scale-95'
                : 'bg-graphite-750 text-cream-muted/40 cursor-not-allowed'
            }`}
          >
            <Send className="w-4 h-4 -ml-0.5" />
          </button>
        </form>
      </div>
    </div>
  );
};
