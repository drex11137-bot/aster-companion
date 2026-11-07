import React, { useState } from 'react';
import { Calendar, ChevronRight, Settings, Check } from 'lucide-react';
import { useCompanion } from '../../context/CompanionContext';
import { AvatarCanvas } from '../AvatarCanvas';

export const TodayScreen: React.FC = () => {
  const {
    activeProfile,
    nextReminder,
    snoozeReminder,
    tasks,
    toggleTask,
    addTask,
    setActiveTab,
    setSettingsOpen,
  } = useCompanion();

  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [showAddTaskInput, setShowAddTaskInput] = useState(false);

  const handleCreateTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;
    addTask(newTaskTitle.trim(), 'Today');
    setNewTaskTitle('');
    setShowAddTaskInput(false);
  };

  return (
    <div className="w-full max-w-2xl mx-auto px-4 py-6 md:py-8 space-y-6">
      {/* Top Greeting Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          {/* Avatar with amber radial halo and green status dot */}
          <div
            onClick={() => setActiveTab('studio')}
            className="cursor-pointer transition-transform hover:scale-105"
            title="Configure Companion Studio"
          >
            <AvatarCanvas
              size={56}
              hairColor={activeProfile.hair}
              eyeColor={activeProfile.eyes}
              showStatusDot={true}
              glowIntensity="normal"
            />
          </div>

          <div>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-cream">
              Good evening, Maya
            </h1>
            <div className="flex items-center space-x-2 mt-0.5">
              <span className="w-2 h-2 rounded-full bg-online animate-pulse" />
              <p className="text-xs md:text-sm text-cream-muted font-medium">
                {activeProfile.name} is online
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => setSettingsOpen(true)}
          className="p-2.5 rounded-full text-cream-muted hover:text-cream hover:bg-graphite-850 transition-colors"
          title="Settings and privacy"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>

      {/* Inspirational Tagline */}
      <p className="text-xs md:text-sm text-cream-muted -mt-2">
        A calmer, brighter you — one step at a time.
      </p>

      {/* Next Reminder Card */}
      {nextReminder && (
        <div className="relative overflow-hidden rounded-2xl bg-card-base border border-card-border p-4 md:p-5 flex items-center justify-between shadow-card hover:border-graphite-700 transition-colors">
          <div className="flex items-center space-x-4">
            <div className="p-3 rounded-xl bg-amber-accent/10 border border-amber-accent/20 text-amber-bright">
              <Calendar className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs text-cream-muted font-medium tracking-wide uppercase">
                Next reminder
              </span>
              <h3 className="text-base md:text-lg font-semibold text-cream mt-0.5">
                {nextReminder.title}
              </h3>
              <p className="text-xs text-cream-muted">
                {nextReminder.dateLabel}
                {nextReminder.isSnoozed && (
                  <span className="ml-2 text-amber-bright font-medium">
                    (Snoozed until {nextReminder.snoozedUntil})
                  </span>
                )}
              </p>
            </div>
          </div>

          <button
            onClick={snoozeReminder}
            className="px-5 py-2 rounded-full bg-amber-bright hover:bg-amber-accent text-graphite-950 font-semibold text-xs md:text-sm tracking-wide shadow-md transition-all active:scale-95"
          >
            Snooze
          </button>
        </div>
      )}

      {/* Your Tasks Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base md:text-lg font-bold text-cream">Your tasks</h2>
          <button
            onClick={() => setShowAddTaskInput(!showAddTaskInput)}
            className="text-xs md:text-sm font-medium text-violet-accent hover:text-violet-dark flex items-center space-x-1"
          >
            <span>{showAddTaskInput ? 'Cancel' : 'Add task +'}</span>
          </button>
        </div>

        {showAddTaskInput && (
          <form onSubmit={handleCreateTask} className="flex items-center space-x-2">
            <input
              type="text"
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
              placeholder="What would you like to get done?"
              className="flex-1 bg-card-base border border-card-border rounded-xl px-4 py-2 text-sm text-cream placeholder-cream-muted/50 focus:outline-none focus:border-amber-accent"
              autoFocus
            />
            <button
              type="submit"
              className="px-4 py-2 bg-amber-bright text-graphite-950 text-xs font-semibold rounded-xl hover:bg-amber-accent"
            >
              Add
            </button>
          </form>
        )}

        <div className="rounded-2xl bg-card-base border border-card-border divide-y divide-card-border overflow-hidden shadow-card">
          {tasks.map((task) => (
            <div
              key={task.id}
              onClick={() => toggleTask(task.id)}
              className="group flex items-center justify-between p-4 cursor-pointer hover:bg-graphite-800/60 transition-colors"
            >
              <div className="flex items-center space-x-3.5">
                <button
                  type="button"
                  aria-label={task.completed ? "Mark incomplete" : "Mark complete"}
                  className={`w-6 h-6 rounded-lg border flex items-center justify-center transition-colors ${
                    task.completed
                      ? 'bg-amber-bright border-amber-bright text-graphite-950'
                      : 'border-graphite-600 bg-transparent group-hover:border-cream-muted'
                  }`}
                >
                  {task.completed && <Check className="w-4 h-4 stroke-[3]" />}
                </button>
                <div>
                  <p
                    className={`text-sm md:text-base font-medium transition-colors ${
                      task.completed ? 'line-through text-cream-muted' : 'text-cream'
                    }`}
                  >
                    {task.title}
                  </p>
                  <p className="text-xs text-cream-muted">{task.dueDate}</p>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-cream-muted group-hover:text-cream transition-colors" />
            </div>
          ))}
        </div>
      </div>

      {/* Recent Memories Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base md:text-lg font-bold text-cream">Recent memories</h2>
          <button
            onClick={() => setActiveTab('memories')}
            className="text-xs md:text-sm font-medium text-violet-accent hover:text-violet-dark flex items-center space-x-1"
          >
            <span>See all</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Photo cards horizontal grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3.5">
          {/* Card 1: Oat flat whites */}
          <div
            onClick={() => setActiveTab('memories')}
            className="group relative h-48 md:h-56 rounded-2xl overflow-hidden border border-card-border bg-card-base cursor-pointer shadow-card transition-transform hover:-translate-y-1"
          >
            <img
              src="/assets/memory_coffee.png"
              alt="Oat flat whites"
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
            {/* Dark gradient overlay at bottom for readability */}
            <div className="absolute inset-0 bg-gradient-to-t from-graphite-950/90 via-graphite-950/40 to-transparent" />
            <div className="absolute bottom-3 left-3 right-3">
              <h4 className="text-xs md:text-sm font-semibold text-cream leading-snug">
                You love oat flat whites
              </h4>
              <p className="text-[11px] text-cream-muted mt-0.5">Noted 3 days ago</p>
            </div>
          </div>

          {/* Card 2: Sister's birthday */}
          <div
            onClick={() => setActiveTab('memories')}
            className="group relative h-48 md:h-56 rounded-2xl overflow-hidden border border-card-border bg-card-base cursor-pointer shadow-card transition-transform hover:-translate-y-1"
          >
            <img
              src="/assets/memory_flowers.png"
              alt="Flowers for sister's birthday"
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-graphite-950/90 via-graphite-950/40 to-transparent" />
            <div className="absolute bottom-3 left-3 right-3">
              <h4 className="text-xs md:text-sm font-semibold text-cream leading-snug">
                Sister's birthday: Nov 14
              </h4>
              <p className="text-[11px] text-cream-muted mt-0.5">Added last week</p>
            </div>
          </div>

          {/* Card 3: Running goal */}
          <div
            onClick={() => setActiveTab('memories')}
            className="hidden md:flex flex-col justify-between p-4 rounded-2xl border border-card-border bg-gradient-to-br from-card-base to-graphite-900 cursor-pointer shadow-card transition-transform hover:-translate-y-1 group"
          >
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-full bg-amber-accent/15 flex items-center justify-center text-amber-bright">
                🏃‍♀️
              </div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-amber-bright px-2 py-0.5 bg-amber-accent/10 rounded-full">
                Plan
              </span>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-cream group-hover:text-amber-bright transition-colors">
                Running a half marathon in March
              </h4>
              <p className="text-xs text-cream-muted mt-1">Added 3 weeks ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
