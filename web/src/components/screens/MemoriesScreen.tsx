import React, { useState } from 'react';
import {
  Search,
  Sun,
  User,
  PlusCircle,
  Activity,
  Pencil,
  Trash2,
  Share2,
  Plus,
  ShieldCheck,
  Check,
} from 'lucide-react';
import { useCompanion } from '../../context/CompanionContext';
import { MemoryItem, MemoryIconType } from '../../types';

interface MemoriesScreenProps {
  onOpenShareModal?: (memory: MemoryItem) => void;
  onOpenEditModal?: (memory?: MemoryItem) => void;
}

export const MemoriesScreen: React.FC<MemoriesScreenProps> = ({
  onOpenShareModal,
  onOpenEditModal,
}) => {
  const {
    activeProfile,
    memories,
    searchQuery,
    setSearchQuery,
    selectedCategory,
    setSelectedCategory,
    deleteMemory,
  } = useCompanion();

  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const categories = ['All', 'People', 'Preferences', 'Plans'];

  // Filter memories based on category and search query
  const filteredMemories = memories.filter((mem) => {
    const matchesCategory =
      selectedCategory === 'All' || mem.category === selectedCategory;
    const matchesSearch =
      !searchQuery.trim() ||
      mem.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      mem.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const renderMemoryIcon = (type: MemoryIconType) => {
    switch (type) {
      case 'sun':
        return <Sun className="w-5 h-5 text-amber-bright" />;
      case 'person':
        return <User className="w-5 h-5 text-amber-bright" />;
      case 'health':
        return <PlusCircle className="w-5 h-5 text-amber-bright" />;
      case 'running':
        return <Activity className="w-5 h-5 text-amber-bright" />;
      default:
        return <Sun className="w-5 h-5 text-amber-bright" />;
    }
  };

  const handleDeleteClick = (id: string) => {
    if (confirmDeleteId === id) {
      deleteMemory(id);
      setConfirmDeleteId(null);
    } else {
      setConfirmDeleteId(id);
      setTimeout(() => {
        setConfirmDeleteId((cur) => (cur === id ? null : cur));
      }, 3500);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto px-4 py-6 md:py-8 space-y-5">
      {/* Title & Subtitle matching Screenshot 2 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-cream">
            Memories
          </h1>
          <p className="text-xs md:text-sm text-cream-muted mt-0.5">
            The little things that matter.
          </p>
        </div>

        <button
          onClick={() => onOpenEditModal && onOpenEditModal()}
          className="inline-flex items-center space-x-1 px-3.5 py-1.5 rounded-full bg-amber-bright hover:bg-amber-accent text-graphite-950 font-semibold text-xs tracking-wide shadow-md transition-all active:scale-95"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          <span>Add memory</span>
        </button>
      </div>

      {/* Profile Memory Isolation Badge */}
      <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-graphite-900 border border-card-border text-[11px] text-cream-muted">
        <ShieldCheck className="w-3.5 h-3.5 text-amber-bright" />
        <span>
          Viewing isolated memories for <strong>{activeProfile.name}</strong>. Not shared with other profiles unless explicitly authorized.
        </span>
      </div>

      {/* Search Bar matching Screenshot 2 */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-cream-muted" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search memories"
          className="w-full bg-card-base border border-card-border rounded-full pl-11 pr-4 py-3 text-sm text-cream placeholder-cream-muted/60 focus:outline-none focus:border-amber-accent/80 transition-colors shadow-card"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-cream-muted hover:text-cream"
          >
            Clear
          </button>
        )}
      </div>

      {/* Category Filter Pills matching Screenshot 2 */}
      <div className="flex items-center space-x-2.5 overflow-x-auto pb-1 no-scrollbar">
        {categories.map((cat) => {
          const isActive = selectedCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-5 py-2 rounded-full text-xs md:text-sm font-medium tracking-wide transition-all shadow-sm ${
                isActive
                  ? 'bg-amber-bright text-graphite-950 font-semibold'
                  : 'bg-card-base border border-card-border text-cream hover:bg-graphite-800'
              }`}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {/* Memory List Cards matching Screenshot 2 */}
      <div className="space-y-3 pt-1">
        {filteredMemories.length === 0 ? (
          <div className="p-8 text-center rounded-2xl bg-card-base border border-card-border text-cream-muted text-sm space-y-2">
            <p>No memories match &quot;{searchQuery}&quot;.</p>
            <p className="text-xs text-cream-muted/70">
              Add a new memory or switch filter category.
            </p>
          </div>
        ) : (
          filteredMemories.map((mem) => (
            <div
              key={mem.id}
              className="group relative flex items-center justify-between p-4 rounded-2xl bg-card-base border border-card-border hover:border-graphite-700 transition-colors shadow-card"
            >
              <div className="flex items-center space-x-4 flex-1 pr-3">
                {/* Amber Icon in circular container */}
                <div className="w-11 h-11 rounded-full bg-amber-deep/15 border border-amber-accent/20 flex items-center justify-center flex-shrink-0">
                  {renderMemoryIcon(mem.iconType)}
                </div>

                <div className="space-y-0.5">
                  <h4 className="text-sm md:text-base font-semibold text-cream leading-snug">
                    {mem.text}
                  </h4>
                  <div className="flex items-center space-x-2 text-xs text-cream-muted">
                    <span>{mem.addedAgo}</span>
                    {mem.isSharedWithOtherProfile && (
                      <span className="text-[10px] text-amber-bright bg-amber-deep/20 px-1.5 py-0.5 rounded border border-amber-accent/30 font-medium">
                        Explicitly Shared
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons: Edit, Share, Delete */}
              <div className="flex items-center space-x-1 flex-shrink-0">
                {/* Explicit Share Modal Button */}
                <button
                  onClick={() => onOpenShareModal && onOpenShareModal(mem)}
                  className="p-2 text-cream-muted hover:text-amber-bright rounded-lg hover:bg-graphite-800 transition-colors"
                  title="Share memory between Aster and Nova"
                >
                  <Share2 className="w-4 h-4" />
                </button>

                {/* Edit Button */}
                <button
                  onClick={() => onOpenEditModal && onOpenEditModal(mem)}
                  className="p-2 text-cream-muted hover:text-cream rounded-lg hover:bg-graphite-800 transition-colors"
                  title="Edit memory"
                >
                  <Pencil className="w-4 h-4" />
                </button>

                {/* Delete Button */}
                <button
                  onClick={() => handleDeleteClick(mem.id)}
                  className={`p-2 rounded-lg transition-colors ${
                    confirmDeleteId === mem.id
                      ? 'bg-red-500/20 text-red-400 font-bold'
                      : 'text-cream-muted hover:text-red-400 hover:bg-graphite-800'
                  }`}
                  title={confirmDeleteId === mem.id ? 'Click to confirm delete' : 'Delete memory'}
                >
                  {confirmDeleteId === mem.id ? (
                    <Check className="w-4 h-4 text-red-400" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
