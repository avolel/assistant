import { useState, useEffect, useRef, useCallback } from "react";
import { MessageBubble } from "./components/MessageBubble";
import { ChatInput } from "./components/ChatInput";
import axios from 'axios';
import { sendMessage, getIdentity, getSessions, deleteSession, getSession, updateAssistantName, addOwner, removeOwner } from "./api/assistant";

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function SettingsModal({ identity, onClose, onIdentityChange, sessionId, onClearChat }) {
  const [nameInput, setNameInput] = useState(identity?.assistant_name ?? "");
  const [nameSaving, setNameSaving] = useState(false);
  const [nameError, setNameError] = useState("");

  const [ownerName, setOwnerName] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [ownerSaving, setOwnerSaving] = useState(false);
  const [ownerError, setOwnerError] = useState("");
  const [removingId, setRemovingId] = useState(null);

  const handleSaveName = async () => {
    if (!nameInput.trim()) return;
    setNameSaving(true);
    setNameError("");
    try {
      const updated = await updateAssistantName(nameInput.trim());
      onIdentityChange(updated);
    } catch (e) {
      setNameError(e?.response?.data?.detail ?? "Failed to update name");
    } finally {
      setNameSaving(false);
    }
  };

  const handleRemoveOwner = async (ownerId) => {
    setRemovingId(ownerId);
    setOwnerError("");
    try {
      const updated = await removeOwner(ownerId);
      onIdentityChange(updated);
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
    e.preventDefault();
    if (!ownerName.trim()) return;
    setOwnerSaving(true);
    setOwnerError("");
    try {
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
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={onClose}
    >
      <div
        className="bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6 space-y-6"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Assistant Settings</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl leading-none">×</button>
        </div>

        {/* Assistant Name */}
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

        {/* Owners */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Owners</label>
          <ul className="space-y-1 mb-3">
            {(identity?.owners ?? []).map(o => (
              <li key={o.owner_id} className="group flex items-center gap-2 text-sm text-slate-300 bg-slate-700 rounded-lg px-3 py-2">
                <span className="w-7 h-7 rounded-full bg-blue-700 flex items-center justify-center text-white font-bold text-xs shrink-0">
                  {o.name[0]?.toUpperCase()}
                </span>
                <span className="min-w-0 flex-1 truncate">{o.name}</span>
                {o.email && <span className="text-slate-500 text-xs truncate hidden group-hover:block">· {o.email}</span>}
                <button
                  onClick={() => handleRemoveOwner(o.owner_id)}
                  disabled={removingId === o.owner_id || (identity?.owners?.length ?? 0) <= 1}
                  className="ml-auto shrink-0 opacity-0 group-hover:opacity-100 text-slate-400
                             hover:text-red-400 disabled:opacity-30 disabled:cursor-not-allowed transition-opacity"
                  title={(identity?.owners?.length ?? 0) <= 1 ? "Cannot remove the last owner" : "Remove owner"}
                >
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

export default function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [identity, setIdentity] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    getIdentity().then(setIdentity);
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load sessions when sidebar opens
  const loadSessions = useCallback(async () => {
    try {
      const data = await getSessions();
      setSessions(data.sessions ?? []);
    } catch {
      setSessions([]);
    }
  }, []);

  // Load sessions when sidebar opens
  useEffect(() => {
    if (sidebarOpen) loadSessions();
  }, [sidebarOpen, loadSessions]);

  // Delete session and clear if currently loaded
  const handleDeleteSession = async (id, e) => {
    e.stopPropagation();
    setDeletingId(id);
    try {
      await deleteSession(id);
      setSessions(prev => prev.filter(s => s.session_id !== id));
      if (id === sessionId) {
        setSessionId(null);
        setMessages([]);
      }
    } finally {
      setDeletingId(null);
    }
  };

  // Send message and update conversation
  const handleSend = async (text) => {
    const userMsg = { role: "user", content: text };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    try {
      const data = await sendMessage(text, sessionId);
      setSessionId(data.session_id);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.reply,
        emotionalState: data.emotional_state,
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Sorry, I encountered an error. Is the server running?",
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleVoice = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post("http://localhost:8000/api/voice/listen",
                                         null, { params: { duration: 5 } });
      if (data.transcription) {
        await handleSend(data.transcription);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSession = async (id) => {
    try {
      const data = await getSession(id);
      setSessionId(id);
      setMessages(data.turns.map(t => ({
        role: t.role,
        content: t.content,
        ...(t.emotional_state && { emotionalState: t.emotional_state }),
      })));
      setSidebarOpen(false);
    } catch {
      // leave current state intact
    }
  };

  const handleNewChat = () => {
    setSessionId(null);
    setMessages([]);
    setSidebarOpen(false);
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      {sidebarOpen && (
        <aside className="w-72 bg-slate-900 border-r border-slate-700 flex flex-col shrink-0">
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
          <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-1">
            {sessions.length === 0 && (
              <p className="text-xs text-slate-500 px-2 mt-4">No sessions yet.</p>
            )}
            {sessions.map(s => (
              <div
                key={s.session_id}
                onClick={() => handleLoadSession(s.session_id)}
                className={`group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer
                  ${s.session_id === sessionId ? "bg-slate-600" : "hover:bg-slate-800"}`}
              >
                <div className="min-w-0">
                  <p className="text-xs text-slate-300 truncate">
                    {s.summary ?? formatTime(s.started_at)}
                  </p>
                  <p className="text-xs text-slate-500">
                    {s.turn_count} turn{s.turn_count !== 1 ? "s" : ""} · {formatTime(s.started_at)}
                  </p>
                </div>
                <button
                  onClick={(e) => handleDeleteSession(s.session_id, e)}
                  disabled={deletingId === s.session_id}
                  className="ml-2 shrink-0 opacity-0 group-hover:opacity-100 text-slate-400
                             hover:text-red-400 transition-opacity disabled:opacity-50"
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
            ))}
          </div>
        </aside>
      )}

      {/* Main chat area */}
      <div className="flex flex-col flex-1 min-w-0 max-w-3xl mx-auto w-full">
        {/* Header */}
        <header className="flex items-center gap-3 px-6 py-4 border-b border-slate-700">
          <button
            onClick={() => setSidebarOpen(v => !v)}
            style={{ fontSize: "22px", color: "#cbd5e1", background: "none", border: "none", cursor: "pointer", padding: "4px 8px", lineHeight: 1 }}
            aria-label="Toggle history"
            title="Chat history"
          >
            ☰
          </button>
          <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center
                          justify-center text-white font-bold text-lg shrink-0">
            {identity?.assistant_name?.[0] ?? "A"}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-semibold text-white truncate">
              {identity?.assistant_name ?? "Loading..."}
            </h1>
            <p className="text-xs text-slate-400">
              {identity?.configured ? "Online · Local AI" : "Not configured"}
            </p>
          </div>
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

        {/* Messages */}
        <main className="flex-1 overflow-y-auto px-4 py-6">
          {messages.length === 0 && (
            <div className="text-center text-slate-500 mt-16">
              <p className="text-4xl mb-4">🤖</p>
              <p className="text-lg">How can I help you today?</p>
            </div>
          )}
          {messages.map((m, i) => (
            <MessageBubble key={i} {...m} />
          ))}
          {loading && (
            <div className="flex justify-start mb-4">
              <div className="bg-slate-700 rounded-2xl px-4 py-3 text-slate-400 text-sm">
                Thinking...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </main>

        <ChatInput voiceEnabled={true} onVoice={handleVoice} onSend={handleSend} loading={loading} />
      </div>

      {/* Settings Modal */}
      {settingsOpen && (
        <SettingsModal
          identity={identity}
          onClose={() => setSettingsOpen(false)}
          onIdentityChange={setIdentity}
          sessionId={sessionId}
          onClearChat={() => { setSessionId(null); setMessages([]); }}
        />
      )}
    </div>
  );
}