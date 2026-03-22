// Root component — owns all top-level state and orchestrates the layout.
import { useState, useEffect, useRef, useCallback } from "react";
import { MessageBubble } from "./components/MessageBubble";
import { ChatInput } from "./components/ChatInput";
import { SettingsModal } from "./components/SettingsModal";
import { MemoryModal } from "./components/MemoryModal";
import { Sidebar } from "./components/Sidebar";
import { ChatHeader } from "./components/ChatHeader";
import axios from 'axios';
import { sendMessage, getIdentity, getSessions, deleteSession, getSession, checkHealth } from "./api/assistant";

export default function App() {
  const [messages,     setMessages]     = useState([]);
  const [loading,      setLoading]      = useState(false);
  const [sessionId,    setSessionId]    = useState(null);
  const [identity,     setIdentity]     = useState(null);
  const [sessions,     setSessions]     = useState([]);
  const [sidebarOpen,  setSidebarOpen]  = useState(false);
  const [deletingId,   setDeletingId]   = useState(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [memoryOpen,   setMemoryOpen]   = useState(false);
  const [online,       setOnline]       = useState(null);   // null=checking, true=online, false=offline

  // Voice recording state
  const [recording,        setRecording]        = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const RECORDING_DURATION = 5;
  const mediaRecorderRef = useRef(null);
  const chunksRef        = useRef([]);
  const timerRef         = useRef(null);

  const bottomRef = useRef(null);

  useEffect(() => {
    getIdentity().then(setIdentity);
  }, []);

  // Poll the health endpoint every 15 s.
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

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadSessions = useCallback(async () => {
    try {
      const data = await getSessions();
      setSessions(data.sessions ?? []);
    } catch {
      setSessions([]);
    }
  }, []);

  useEffect(() => {
    if (sidebarOpen) loadSessions();
  }, [sidebarOpen, loadSessions]);

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

  const handleSend = async (text) => {
    setMessages(prev => [...prev, { role: "user", content: text }]);
    setLoading(true);
    try {
      const data = await sendMessage(text, sessionId);
      setSessionId(data.session_id);
      setMessages(prev => [...prev, {
        role:           "assistant",
        content:        data.reply,
        emotionalState: data.emotional_state,
      }]);
      if (sidebarOpen) loadSessions();
    } catch {
      setMessages(prev => [...prev, {
        role:    "assistant",
        content: "Sorry, I encountered an error. Is the server running?",
      }]);
    } finally {
      setLoading(false);
    }
  };

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
    mediaRecorderRef.current.stop();
    setRecording(false);
    setRecordingSeconds(0);
  };

  const handleVoice = async () => {
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
      stream.getTracks().forEach(t => t.stop());
      stopAndTranscribe(chunksRef.current, mimeType);
    };

    mediaRecorderRef.current = recorder;
    recorder.start();
    setRecording(true);
    setRecordingSeconds(0);

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

      {/* Mobile backdrop for sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 sm:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {sidebarOpen && (
        <Sidebar
          sessions={sessions}
          sessionId={sessionId}
          deletingId={deletingId}
          onClose={() => setSidebarOpen(false)}
          onNewChat={handleNewChat}
          onLoadSession={handleLoadSession}
          onDeleteSession={handleDeleteSession}
        />
      )}

      {/* Main chat area */}
      <div className="flex flex-col flex-1 min-w-0 max-w-3xl mx-auto w-full">

        <ChatHeader
          identity={identity}
          online={online}
          onToggleSidebar={() => setSidebarOpen(v => !v)}
          onOpenMemory={() => setMemoryOpen(true)}
          onOpenSettings={() => setSettingsOpen(true)}
        />

        <main className="flex-1 overflow-y-auto px-3 sm:px-4 py-4 sm:py-6">
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

      {memoryOpen   && <MemoryModal onClose={() => setMemoryOpen(false)} />}
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