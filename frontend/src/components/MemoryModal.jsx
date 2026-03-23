import { useState, useEffect } from "react";
import { getMemories, updateMemory, deleteMemory } from "../api/assistant";

const MEMORY_TYPE_STYLES = {
  user_fact:  { label: "User fact",   bg: "bg-blue-900",   text: "text-blue-300"   },
  preference: { label: "Preference", bg: "bg-purple-900", text: "text-purple-300" },
  event:      { label: "Event",      bg: "bg-amber-900",  text: "text-amber-300"  },
  summary:    { label: "Summary",    bg: "bg-green-900",  text: "text-green-300"  },
};

const ALL_TYPES = ["user_fact", "preference", "event", "summary"];

export function MemoryModal({ onClose }) {
  const [memories,    setMemories]    = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [filterType,  setFilterType]  = useState(null);
  const [editingId,   setEditingId]   = useState(null);
  const [editContent, setEditContent] = useState("");
  const [savingId,    setSavingId]    = useState(null);
  const [deletingId,  setDeletingId]  = useState(null);
  const [error,       setError]       = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    getMemories(100, 0, filterType)
      .then(d => setMemories(d.memories ?? []))
      .catch(() => setError("Failed to load memories."))
      .finally(() => setLoading(false));
  }, [filterType]);

  const startEdit = (mem) => {
    setEditingId(mem.memory_id);
    setEditContent(mem.content);
    setError("");
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditContent("");
  };

  const handleSave = async (memoryId) => {
    if (!editContent.trim()) return;
    setSavingId(memoryId);
    setError("");
    try {
      await updateMemory(memoryId, editContent.trim());
      setMemories(prev => prev.map(m =>
        m.memory_id === memoryId ? { ...m, content: editContent.trim() } : m
      ));
      setEditingId(null);
    } catch (e) {
      setError(e?.response?.data?.detail ?? "Failed to save memory.");
    } finally {
      setSavingId(null);
    }
  };

  const handleDelete = async (memoryId) => {
    setDeletingId(memoryId);
    setError("");
    try {
      await deleteMemory(memoryId);
      setMemories(prev => prev.filter(m => m.memory_id !== memoryId));
      if (editingId === memoryId) setEditingId(null);
    } catch (e) {
      setError(e?.response?.data?.detail ?? "Failed to delete memory.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={onClose}
    >
      <div
        className="bg-slate-800 rounded-2xl shadow-2xl w-full max-w-xl mx-4 flex flex-col max-h-[90vh] sm:max-h-[80vh]"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 shrink-0">
          <h2 className="text-lg font-semibold text-white">Long-Term Memories</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl leading-none">×</button>
        </div>

        {/* Type filter tabs */}
        <div className="flex gap-1.5 px-6 py-3 border-b border-slate-700 shrink-0 flex-wrap">
          <button
            onClick={() => setFilterType(null)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors
              ${filterType === null ? "bg-slate-500 text-white" : "bg-slate-700 text-slate-400 hover:text-white"}`}
          >
            All
          </button>
          {ALL_TYPES.map(t => {
            const s = MEMORY_TYPE_STYLES[t] ?? {};
            return (
              <button
                key={t}
                onClick={() => setFilterType(filterType === t ? null : t)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors
                  ${filterType === t ? `${s.bg} ${s.text}` : "bg-slate-700 text-slate-400 hover:text-white"}`}
              >
                {s.label ?? t}
              </button>
            );
          })}
        </div>

        {/* Memory list */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
          {error && <p className="text-red-400 text-xs px-2">{error}</p>}
          {loading && <p className="text-slate-500 text-sm px-2 mt-4">Loading…</p>}
          {!loading && memories.length === 0 && (
            <p className="text-slate-500 text-sm px-2 mt-6 text-center">No memories found.</p>
          )}
          {memories.map(mem => {
            const s          = MEMORY_TYPE_STYLES[mem.memory_type] ?? MEMORY_TYPE_STYLES.conversation;
            const isEditing  = editingId  === mem.memory_id;
            const isDeleting = deletingId === mem.memory_id;
            const isSaving   = savingId   === mem.memory_id;
            return (
              <div key={mem.memory_id} className="group bg-slate-750 border border-slate-700 rounded-xl p-3 space-y-2"
                   style={{ backgroundColor: "#1e293b" }}>
                {/* Type badge + actions */}
                <div className="flex items-center justify-between gap-2">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${s.bg} ${s.text}`}>
                    {s.label}
                  </span>
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    {!isEditing && (
                      <button
                        onClick={() => startEdit(mem)}
                        className="text-slate-400 hover:text-blue-400 transition-colors"
                        title="Edit"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 24 24"
                             fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(mem.memory_id)}
                      disabled={isDeleting}
                      className="text-slate-400 hover:text-red-400 transition-colors disabled:opacity-50"
                      title="Delete"
                    >
                      {isDeleting ? "…" : (
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 24 24"
                             fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="3 6 5 6 21 6"/>
                          <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                          <path d="M10 11v6M14 11v6"/>
                          <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
                        </svg>
                      )}
                    </button>
                  </div>
                </div>

                {/* Content — editable or read-only */}
                {isEditing ? (
                  <div className="space-y-2">
                    <textarea
                      value={editContent}
                      onChange={e => setEditContent(e.target.value)}
                      rows={3}
                      className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm border border-slate-600
                                 focus:outline-none focus:border-blue-500 resize-none"
                      autoFocus
                    />
                    <div className="flex gap-2 justify-end">
                      <button
                        onClick={cancelEdit}
                        className="px-3 py-1 text-xs text-slate-400 hover:text-white transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleSave(mem.memory_id)}
                        disabled={isSaving || !editContent.trim()}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs
                                   rounded-lg font-medium transition-colors"
                      >
                        {isSaving ? "Saving…" : "Save"}
                      </button>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-slate-300 leading-relaxed">{mem.content}</p>
                )}

                {/* Meta: importance + date */}
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span>importance {Math.round((mem.importance ?? 0.5) * 100)}%</span>
                  {mem.created_at && (
                    <span>{new Date(mem.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer count */}
        {!loading && (
          <div className="px-6 py-3 border-t border-slate-700 shrink-0">
            <p className="text-xs text-slate-500">{memories.length} memor{memories.length !== 1 ? "ies" : "y"}</p>
          </div>
        )}
      </div>
    </div>
  );
}