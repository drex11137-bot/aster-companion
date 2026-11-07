import React, { useState, useEffect } from 'react';
import { X, Sun, User, PlusCircle, Activity } from 'lucide-react';
import { useCompanion } from '../../context/CompanionContext';
import { MemoryItem, MemoryIconType } from '../../types';

interface MemoryEditModalProps {
  memory?: MemoryItem | null;
  onClose: () => void;
}

export const MemoryEditModal: React.FC<MemoryEditModalProps> = ({
  memory,
  onClose,
}) => {
  const { activeProfile, addMemory, updateMemory } = useCompanion();

  const [text, setText] = useState('');
  const [category, setCategory] = useState<'People' | 'Preferences' | 'Plans'>('Preferences');
  const [iconType, setIconType] = useState<MemoryIconType>('sun');

  useEffect(() => {
    if (memory) {
      setText(memory.text);
      setCategory(memory.category);
      setIconType(memory.iconType);
    } else {
      setText('');
      setCategory('Preferences');
      setIconType('sun');
    }
  }, [memory]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    if (memory) {
      updateMemory(memory.id, {
        text: text.trim(),
        category,
        iconType,
      });
    } else {
      addMemory({
        text: text.trim(),
        category,
        iconType,
        provenance: 'stated_fact',
        confidence: 1.0,
      });
    }
    onClose();
  };

  const iconOptions: { type: MemoryIconType; icon: React.ReactNode; label: string }[] = [
    { type: 'sun', icon: <Sun className="w-4 h-4 text-amber-bright" />, label: 'Sun / Routine' },
    { type: 'person', icon: <User className="w-4 h-4 text-amber-bright" />, label: 'Person' },
    { type: 'health', icon: <PlusCircle className="w-4 h-4 text-amber-bright" />, label: 'Health' },
    { type: 'running', icon: <Activity className="w-4 h-4 text-amber-bright" />, label: 'Plan / Sport' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-md rounded-2xl bg-card-elevated border border-card-border p-6 shadow-2xl space-y-5">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-cream">
            {memory ? 'Edit Memory' : `Add Memory for ${activeProfile.name}`}
          </h3>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-cream-muted hover:text-cream hover:bg-graphite-750 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-cream-muted">
              Memory Description
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="e.g. Prefers cold brew over espresso"
              rows={3}
              className="w-full bg-card-base border border-card-border rounded-xl p-3 text-sm text-cream placeholder-cream-muted/50 focus:outline-none focus:border-amber-accent resize-none"
              autoFocus
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-cream-muted">Category</label>
            <div className="grid grid-cols-3 gap-2">
              {(['People', 'Preferences', 'Plans'] as const).map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setCategory(cat)}
                  className={`py-2 rounded-xl text-xs font-medium transition-all ${
                    category === cat
                      ? 'bg-amber-deep/20 border border-amber-bright text-cream font-semibold'
                      : 'bg-card-base border border-card-border text-cream-muted hover:bg-graphite-800'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-cream-muted">Icon Symbol</label>
            <div className="grid grid-cols-4 gap-2">
              {iconOptions.map((opt) => (
                <button
                  key={opt.type}
                  type="button"
                  onClick={() => setIconType(opt.type)}
                  className={`p-2.5 rounded-xl border flex flex-col items-center justify-center space-y-1 transition-all ${
                    iconType === opt.type
                      ? 'bg-amber-deep/20 border-amber-bright text-cream'
                      : 'bg-card-base border-card-border text-cream-muted hover:bg-graphite-800'
                  }`}
                >
                  {opt.icon}
                  <span className="text-[10px] truncate max-w-full">{opt.type}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center space-x-3 pt-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-xl bg-card-base hover:bg-graphite-800 border border-card-border text-xs font-semibold text-cream transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!text.trim()}
              className={`flex-1 py-2.5 rounded-xl font-bold text-xs tracking-wide shadow-md transition-all ${
                text.trim()
                  ? 'bg-amber-bright hover:bg-amber-accent text-graphite-950 active:scale-95'
                  : 'bg-graphite-750 text-cream-muted/40 cursor-not-allowed'
              }`}
            >
              {memory ? 'Save Changes' : 'Add Memory'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
