// Root component — owns all top-level state and orchestrates the layout:
// optional sidebar (chat history) + main chat area + optional settings modal.
import { useState, useEffect, useRef, useCallback } from "react";
import { MessageBubble } from "./components/MessageBubble";
import { ChatInput } from "./components/ChatInput";
import axios from 'axios';
import { sendMessage, getIdentity, getSessions, deleteSession, getSession, updateAssistantName, addOwner, removeOwner, exportSession, getMemories, updateMemory, deleteMemory, checkHealth } from "./api/assistant";

// Utility: format an ISO datetime string as a short locale string for display in the sidebar.
function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

// SettingsModal is a separate component to keep App clean.
// It receives identity data and callbacks as props — App owns the state,
// the modal just renders it and calls up when something changes.
function SettingsModal({ identity, onClose, onIdentityChange, sessionId, onClearChat }) {
  // Each piece of form state lives in its own useState call.
  // Initialise nameInput from the current identity name so the field is pre-filled.
  const [nameInput,   setNameInput]   = useState(identity?.assistant_name ?? "");
  const [nameSaving,  setNameSaving]  = useState(false);
  const [nameError,   setNameError]   = useState("");

  const [ownerName,   setOwnerName]   = useState("");
  const [ownerEmail,  setOwnerEmail]  = useState("");
  const [ownerSaving, setOwnerSaving] = useState(false);
  const [ownerError,  setOwnerError]  = useState("");
  // Track which owner is currently being removed to show a loading indicator on that row.
  const [removingId,  setRemovingId]  = useState(null);

  const handleSaveName = async () => {
    if (!nameInput.trim()) return;
    setNameSaving(true);
    setNameError("");
    try {
      const updated = await updateAssistantName(nameInput.trim());
      // Pass the updated identity back up to App so the header reflects the new name.
      onIdentityChange(updated);
    } catch (e) {
      // e?.response?.data?.detail is the FastAPI error detail string. `?.` is optional chaining —
      // if any part of the chain is undefined, it short-circuits to undefined instead of throwing.
      setNameError(e?.response?.data?.detail ?? "Failed to update name");
    } finally {
      // `finally` always runs — clears the loading state whether the call succeeded or failed.
      setNameSaving(false);
    }
  };

  const handleRemoveOwner = async (ownerId) => {
    setRemovingId(ownerId);
    setOwnerError("");
    try {
      const updated = await removeOwner(ownerId);
      onIdentityChange(updated);
      // If the removed owner's session is currently loaded, try to verify it still exists.
      // If the session is now gone, clear the chat to avoid a stale state.
      if (sessionId) {
        try { await getSession(sessionId); }
        catch { onClearChat(); }
      }
    } catch (e) {
      setOwnerError(e?.response?.data?.detail ?? "Failed to remove owner");
    } finally {
      setRemovingId(null);
    }
  };

  const handleAddOwner = async (e) => {
    // e.preventDefault() stops the default HTML form submission (page reload).
    e.preventDefault();
    if (!ownerName.trim()) return;
    setOwnerSaving(true);
    setOwnerError("");
    try {
      // `|| undefined` converts an empty string to undefined so the field is omitted from the request.
      const updated = await addOwner({ name: ownerName.trim(), email: ownerEmail.trim() || undefined });
      onIdentityChange(updated);
      setOwnerName("");
      setOwnerEmail("");
    } catch (e) {
      setOwnerError(e?.response?.data?.detail ?? "Failed to add owner");
    } finally {
      setOwnerSaving(false);
    }
  };

  return (
    // Backdrop: fixed overlay covering the whole screen.
    // Clicking the backdrop (not the modal card) triggers onClose.
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={onClose}
    >
      {/* Modal card: e.stopPropagation() stops clicks inside from bubbling to the backdrop. */}
      <div
        className="bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6 space-y-6"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Assistant Settings</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl leading-none">×</button>
        </div>

        {/* ── Assistant Name ───────────────────────────────────── */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Assistant Name</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={nameInput}
              onChange={e => setNameInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSaveName()}
              className="flex-1 bg-slate-700 text-white rounded-lg px-3 py-2 text-sm border border-slate-600
                         focus:outline-none focus:border-blue-500"
              placeholder="e.g. Aria"
            />
            {/* Disable Save if already saving, input is empty, or the name hasn't changed. */}
            <button
              onClick={handleSaveName}
              disabled={nameSaving || !nameInput.trim() || nameInput.trim() === identity?.assistant_name}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm
                         rounded-lg font-medium transition-colors"
            >
              {nameSaving ? "Saving…" : "Save"}
            </button>
          </div>
          {nameError && <p className="text-red-400 text-xs mt-1">{nameError}</p>}
        </div>

        {/* ── Owners ───────────────────────────────────────────── */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Owners</label>
          <ul className="space-y-1 mb-3">
            {/* (identity?.owners ?? []) safely handles null identity during loading. */}
            {(identity?.owners ?? []).map(o => (
              // `key` prop is required for list items — React uses it to track which items changed.
              <li key={o.owner_id} className="group flex items-center gap-2 text-sm text-slate-300 bg-slate-700 rounded-lg px-3 py-2">
                {/* Avatar: first letter of the owner's name, uppercased. */}
                <span className="w-7 h-7 rounded-full bg-blue-700 flex items-center justify-center text-white font-bold text-xs shrink-0">
                  {o.name[0]?.toUpperCase()}
                </span>
                <span className="min-w-0 flex-1 truncate">{o.name}</span>
                {/* Email only shown on hover (group-hover:block). Hidden by default. */}
                {o.email && <span className="text-slate-500 text-xs truncate hidden group-hover:block">· {o.email}</span>}
                {/* Disable remove button when only one owner remains (backend enforces this too). */}
                <button
                  onClick={() => handleRemoveOwner(o.owner_id)}
                  disabled={removingId === o.owner_id || (identity?.owners?.length ?? 0) <= 1}
                  className="ml-auto shrink-0 opacity-0 group-hover:opacity-100 text-slate-400
                             hover:text-red-400 disabled:opacity-30 disabled:cursor-not-allowed transition-opacity"
                  title={(identity?.owners?.length ?? 0) <= 1 ? "Cannot remove the last owner" : "Remove owner"}
                >
                  {/* Show ellipsis while this specific owner is being removed. */}
                  {removingId === o.owner_id ? "…" : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24"
                         fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                      <path d="M10 11v6M14 11v6" />
                      <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
                    </svg>
                  )}
                </button>
              </li>
            ))}
          </ul>
          {/* Add owner form — onSubmit calls handleAddOwner which calls e.preventDefault(). */}
          <form onSubmit={handleAddOwner} className="space-y-2">
            <input
              type="text"
              value={ownerName}
              onChange={e => setOwnerName(e.target.value)}
              className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm border border-slate-600
                         focus:outline-none focus:border-blue-500"
              placeholder="New owner name"
            />
            <input
              type="email"
              value={ownerEmail}
              onChange={e => setOwnerEmail(e.target.value)}
              className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm border border-slate-600
                         focus:outline-none focus:border-blue-500"
              placeholder="Email (optional)"
            />
            <button
              type="submit"
              disabled={ownerSaving || !ownerName.trim()}
              className="w-full py-2 bg-slate-600 hover:bg-slate-500 disabled:opacity-50 text-white text-sm
                         rounded-lg font-medium transition-colors"
            >
              {ownerSaving ? "Adding…" : "+ Add Owner"}
            </button>
            {ownerError && <p className="text-red-400 text-xs">{ownerError}</p>}
          </form>
        </div>
      </div>
    </div>
  );
}


// Type badge colours and labels for the five memory types.
const MEMORY_TYPE_STYLES = {
  user_fact:    { label: "User fact",    bg: "bg-blue-900",   text: "text-blue-300"   },
  preference:   { label: "Preference",  bg: "bg-purple-900", text: "text-purple-300" },
  conversation: { label: "Convo",       bg: "bg-slate-700",  text: "text-slate-300"  },
  event:        { label: "Event",       bg: "bg-amber-900",  text: "text-amber-300"  },
  summary:      { label: "Summary",     bg: "bg-green-900",  text: "text-green-300"  },
};

function MemoryModal({ onClose }) {
  const [memories,    setMemories]    = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [filterType,  setFilterType]  = useState(null);   // null = all
  const [editingId,   setEditingId]   = useState(null);
  const [editContent, setEditContent] = useState("");
  const [savingId,    setSavingId]    = useState(null);
  const [deletingId,  setDeletingId]  = useState(null);
  const [error,       setError]       = useState("");

  // Load memories whenever the type filter changes.
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

  const allTypes = ["user_fact", "preference", "event", "summary", "conversation"];

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
          {allTypes.map(t => {
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
            const s    = MEMORY_TYPE_STYLES[mem.memory_type] ?? MEMORY_TYPE_STYLES.conversation;
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
                        {/* Pencil icon */}
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


export default function App() {
  // Top-level state — all state that needs to be shared between child components lives here.
  const [messages,     setMessages]     = useState([]);       // All messages in the current view
  const [loading,      setLoading]      = useState(false);    // True while awaiting a backend response
  const [sessionId,    setSessionId]    = useState(null);     // Current session ID (null = new session)
  const [identity,     setIdentity]     = useState(null);     // Assistant identity (name, owners, etc.)
  const [sessions,     setSessions]     = useState([]);       // Session list shown in the sidebar
  const [sidebarOpen,  setSidebarOpen]  = useState(false);
  const [deletingId,   setDeletingId]   = useState(null);     // Session being deleted (for loading state)
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [memoryOpen,   setMemoryOpen]   = useState(false);
  const [exportMenuId, setExportMenuId] = useState(null);     // Session with export format menu open
  const [online,       setOnline]       = useState(null);     // null=checking, true=online, false=offline

  // Voice recording state
  const [recording,        setRecording]        = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const RECORDING_DURATION = 5;   // max seconds before auto-stop
  const mediaRecorderRef = useRef(null);   // MediaRecorder instance
  const chunksRef        = useRef([]);     // accumulated audio chunks
  const timerRef         = useRef(null);   // setInterval handle for countdown

  // useRef gives a mutable ref object whose .current property persists across renders.
  // Used here to get a DOM reference for auto-scrolling — not tracked by React state.
  const bottomRef = useRef(null);

  // useEffect with [] runs once after the first render (like componentDidMount).
  // Loads the identity so the header can show the assistant's name immediately.
  useEffect(() => {
    getIdentity().then(setIdentity);
  }, []);

  // Poll the health endpoint every 15 s to reflect real-time connectivity.
  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      const up = await checkHealth();
      if (!cancelled) setOnline(up);
    };
    poll();
    const id = setInterval(poll, 15_000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  // useEffect with [messages] runs after every render where `messages` changed.
  // Scrolls the invisible div at the bottom of the message list into view.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // useCallback memoises the function — it's only re-created when its dependencies change.
  // Without this, a new function reference would be created on every render, causing the
  // useEffect below to fire every time App re-renders (not just when sidebarOpen changes).
  const loadSessions = useCallback(async () => {
    try {
      const data = await getSessions();
      setSessions(data.sessions ?? []);
    } catch {
      setSessions([]);
    }
  }, []);  // Empty deps: loadSessions never changes, safe to call from any effect

  // Load sessions from the API when the sidebar is opened.
  useEffect(() => {
    if (sidebarOpen) loadSessions();
  }, [sidebarOpen, loadSessions]);

  // Close export menu when clicking outside the sidebar.
  useEffect(() => {
    if (!exportMenuId) return;
    const close = () => setExportMenuId(null);
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, [exportMenuId]);

  const handleDeleteSession = async (id, e) => {
    // stopPropagation prevents the click from bubbling to the session row's onClick (which would load it).
    e.stopPropagation();
    setDeletingId(id);
    try {
      await deleteSession(id);
      // Filter the deleted session out of local state. `prev =>` is the functional update form —
      // safer than reading sessions directly when state updates might be batched.
      setSessions(prev => prev.filter(s => s.session_id !== id));
      if (id === sessionId) {
        setSessionId(null);
        setMessages([]);
      }
    } finally {
      setDeletingId(null);
    }
  };

  const handleSend = async (text) => {
    // Optimistically add the user message to the UI before the response arrives.
    const userMsg = { role: "user", content: text };
    setMessages(prev => [...prev, userMsg]);   // Spread creates a new array — React requires immutability
    setLoading(true);
    try {
      const data = await sendMessage(text, sessionId);
      setSessionId(data.session_id);   // Update session ID in case this was the first message
      setMessages(prev => [...prev, {
        role:           "assistant",
        content:        data.reply,
        emotionalState: data.emotional_state,  // Passed to MessageBubble for the emotion bars
      }]);
      if (sidebarOpen) loadSessions();
    } catch {
      // Show a fallback error message instead of crashing.
      setMessages(prev => [...prev, {
        role:    "assistant",
        content: "Sorry, I encountered an error. Is the server running?",
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Finalise recording: send the collected audio chunks to the backend for transcription.
  const stopAndTranscribe = async (chunks, mimeType) => {
    const blob = new Blob(chunks, { type: mimeType });
    const ext  = mimeType.includes("ogg") ? ".ogg" : mimeType.includes("mp4") ? ".mp4" : ".webm";
    const form = new FormData();
    form.append("audio", blob, `recording${ext}`);
    setLoading(true);
    try {
      const { data } = await axios.post("http://localhost:8000/api/voice/transcribe", form);
      if (data.transcription) await handleSend(data.transcription);
    } finally {
      setLoading(false);
    }
  };

  const handleStopVoice = () => {
    if (!mediaRecorderRef.current) return;
    clearInterval(timerRef.current);
    mediaRecorderRef.current.stop();   // triggers the onstop handler which calls stopAndTranscribe
    setRecording(false);
    setRecordingSeconds(0);
  };

  const handleVoice = async () => {
    // Request microphone access. The browser prompts the user if permission hasn't been granted yet.
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      alert("Microphone access denied. Please allow microphone access and try again.");
      return;
    }

    chunksRef.current = [];
    const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm"
                   : MediaRecorder.isTypeSupported("audio/ogg")  ? "audio/ogg"
                   : "audio/mp4";
    const recorder = new MediaRecorder(stream, { mimeType });

    recorder.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
    recorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop());   // release mic
      stopAndTranscribe(chunksRef.current, mimeType);
    };

    mediaRecorderRef.current = recorder;
    recorder.start();
    setRecording(true);
    setRecordingSeconds(0);

    // Tick the counter every second; auto-stop at RECORDING_DURATION.
    let elapsed = 0;
    timerRef.current = setInterval(() => {
      elapsed += 1;
      setRecordingSeconds(elapsed);
      if (elapsed >= RECORDING_DURATION) handleStopVoice();
    }, 1000);
  };

  const handleLoadSession = async (id) => {
    try {
      const data = await getSession(id);
      setSessionId(id);
      // Map the turn objects from the API into the shape MessageBubble expects.
      // `...` spread plus a conditional field: emotionalState is only added if it exists on the turn.
      setMessages(data.turns.map(t => ({
        role:    t.role,
        content: t.content,
        ...(t.emotional_state && { emotionalState: t.emotional_state }),
      })));
      setSidebarOpen(false);
    } catch {
      // Leave current state intact if the session can't be loaded.
    }
  };

  const handleNewChat = () => {
    setSessionId(null);
    setMessages([]);
    setSidebarOpen(false);
  };

  return (
    <div className="flex h-screen">

      {/* ── Sidebar ────────────────────────────────────────────── */}
      {/* Mobile: fixed overlay drawer. Desktop: inline sidebar pushing content. */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 sm:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      {sidebarOpen && (
        <aside className="fixed inset-y-0 left-0 z-40 sm:relative sm:inset-auto sm:z-auto w-72 bg-slate-900 border-r border-slate-700 flex flex-col shrink-0">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
            <span className="text-sm font-semibold text-slate-300">Chat History</span>
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-slate-400 hover:text-white text-lg leading-none"
              aria-label="Close sidebar"
            >
              ×
            </button>
          </div>
          <div className="px-3 py-2">
            <button
              onClick={handleNewChat}
              className="w-full text-sm text-left px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200"
            >
              + New chat
            </button>
          </div>
          {/* overflow-y-auto makes this section scrollable when sessions overflow the sidebar height. */}
          <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-1">
            {sessions.length === 0 && (
              <p className="text-xs text-slate-500 px-2 mt-4">No sessions yet.</p>
            )}
            {/* Render a clickable row for each session. Highlight the active session. */}
            {sessions.map(s => (
              <div
                key={s.session_id}
                onClick={() => handleLoadSession(s.session_id)}
                className={`group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer
                  ${s.session_id === sessionId ? "bg-slate-600" : "hover:bg-slate-800"}`}
              >
                <div className="min-w-0">
                  <p className="text-xs text-slate-300 truncate">
                    {/* Show the LLM-generated summary if available, otherwise the timestamp. */}
                    {s.summary ?? formatTime(s.started_at)}
                  </p>
                  <p className="text-xs text-slate-500">
                    {s.turn_count} turn{s.turn_count !== 1 ? "s" : ""} · {formatTime(s.started_at)}
                  </p>
                </div>
                {/* Export + Delete buttons: always visible on mobile, hover-reveal on desktop. */}
                <div className="ml-2 shrink-0 flex items-center gap-1 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity relative">
                  {/* Export button — toggles a small format-picker dropdown */}
                  <div className="relative">
                    <button
                      onClick={(e) => { e.stopPropagation(); setExportMenuId(v => v === s.session_id ? null : s.session_id); }}
                      className="text-slate-400 hover:text-blue-400 transition-colors"
                      aria-label="Export session"
                      title="Export session"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24"
                           fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                      </svg>
                    </button>
                    {exportMenuId === s.session_id && (
                      <div
                        className="absolute right-0 top-6 z-10 bg-slate-700 border border-slate-600 rounded-lg shadow-xl py-1 w-28"
                        onClick={e => e.stopPropagation()}
                      >
                        {[["text", "Plain text"], ["markdown", "Markdown"], ["json", "JSON"]].map(([fmt, label]) => (
                          <button
                            key={fmt}
                            onClick={() => { exportSession(s.session_id, fmt); setExportMenuId(null); }}
                            className="w-full text-left px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-600 hover:text-white transition-colors"
                          >
                            {label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={(e) => handleDeleteSession(s.session_id, e)}
                    disabled={deletingId === s.session_id}
                    className="text-slate-400 hover:text-red-400 transition-colors disabled:opacity-50"
                    aria-label="Delete session"
                    title="Delete session"
                  >
                    {deletingId === s.session_id ? "…" : (
                      <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24"
                           fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                        <path d="M10 11v6M14 11v6" />
                        <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </aside>
      )}

      {/* ── Main chat area ─────────────────────────────────────── */}
      {/* max-w-3xl + mx-auto centres the chat column. flex-1 takes remaining width. */}
      <div className="flex flex-col flex-1 min-w-0 max-w-3xl mx-auto w-full">

        {/* Header */}
        <header className="flex items-center gap-2 sm:gap-3 px-3 sm:px-6 py-3 sm:py-4 border-b border-slate-700">
          {/* Toggle sidebar — `v => !v` is a functional update that flips the boolean. */}
          <button
            onClick={() => setSidebarOpen(v => !v)}
            style={{ fontSize: "22px", color: "#cbd5e1", background: "none", border: "none", cursor: "pointer", padding: "4px 8px", lineHeight: 1 }}
            aria-label="Toggle history"
            title="Chat history"
          >
            ☰
          </button>
          {/* Assistant avatar: first letter of the name, or "A" while loading. */}
          <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center
                          justify-center text-white font-bold text-lg shrink-0">
            {identity?.assistant_name?.[0] ?? "A"}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-semibold text-white truncate">
              {identity?.assistant_name ?? "Loading..."}
            </h1>
            <p className="text-xs text-slate-400 flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                online === null ? "bg-slate-500 animate-pulse" :
                online          ? "bg-green-500" :
                                  "bg-red-500"
              }`} />
              {online === null ? "Connecting…" : online ? "Online · Local AI" : "Offline"}
            </p>
          </div>
          {/* Memory brain button */}
          <button
            onClick={() => setMemoryOpen(true)}
            title="Long-term memories"
            className="text-slate-400 hover:text-white transition-colors p-1"
            aria-label="Open memory manager"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24"
                 fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-1.04-4.79A2.5 2.5 0 0 1 7 10.5a2.5 2.5 0 0 1 2.5-2.5"/>
              <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 1.04-4.79A2.5 2.5 0 0 0 17 10.5a2.5 2.5 0 0 0-2.5-2.5"/>
            </svg>
          </button>
          {/* Settings gear icon button */}
          <button
            onClick={() => setSettingsOpen(true)}
            title="Settings"
            className="text-slate-400 hover:text-white transition-colors p-1"
            aria-label="Open settings"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24"
                 fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33
                       1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33
                       l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4
                       h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0
                       9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33
                       l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4
                       h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
          </button>
        </header>

        {/* Messages list */}
        <main className="flex-1 overflow-y-auto px-3 sm:px-4 py-4 sm:py-6">
          {/* Empty state: shown when there are no messages yet. */}
          {messages.length === 0 && (
            <div className="text-center text-slate-500 mt-16">
              <p className="text-4xl mb-4">🤖</p>
              <p className="text-lg">How can I help you today?</p>
            </div>
          )}
          {/* Spread props: {...m} passes all fields of the message object as individual props to MessageBubble.
              Equivalent to: <MessageBubble role={m.role} content={m.content} emotionalState={m.emotionalState} /> */}
          {messages.map((m, i) => (
            <MessageBubble key={i} {...m} />
          ))}
          {/* Thinking indicator: shown while the API call is in flight. */}
          {loading && (
            <div className="flex justify-start mb-4">
              <div className="bg-slate-700 rounded-2xl px-4 py-3 text-slate-400 text-sm">
                Thinking...
              </div>
            </div>
          )}
          {/* Invisible anchor div — scrollIntoView() targets this to keep the latest message visible. */}
          <div ref={bottomRef} />
        </main>

        <ChatInput
          voiceEnabled={true}
          onVoice={handleVoice}
          onStopVoice={handleStopVoice}
          onSend={handleSend}
          loading={loading}
          recording={recording}
          recordingSeconds={recordingSeconds}
          recordingDuration={RECORDING_DURATION}
        />
      </div>

      {/* ── Memory Modal ───────────────────────────────────────── */}
      {memoryOpen && (
        <MemoryModal onClose={() => setMemoryOpen(false)} />
      )}

      {/* ── Settings Modal ─────────────────────────────────────── */}
      {settingsOpen && (
        <SettingsModal
          identity={identity}
          onClose={() => setSettingsOpen(false)}
          onIdentityChange={setIdentity}   // When identity changes in the modal, update App state
          sessionId={sessionId}
          onClearChat={() => { setSessionId(null); setMessages([]); }}
        />
      )}
    </div>
  );
}