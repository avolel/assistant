import { useState, useEffect, useRef } from "react";
import { MessageBubble } from "./components/MessageBubble";
import { ChatInput } from "./components/ChatInput";
import axios from 'axios';
import { sendMessage, getIdentity } from "./api/assistant"; // API functions to interact with the backend
 
export default function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [identity, setIdentity] = useState(null);
  const bottomRef = useRef(null);
 
  // Fetch assistant identity on mount
  useEffect(() => {
    getIdentity().then(setIdentity);
  }, []);
 
  useEffect(() => {
    // Scroll to bottom whenever messages change
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
 
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
    } catch (err) {
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
      // Optionally speak the reply:
      await axios.post("/api/voice/speak", null, { params: { text: reply } })
    }
  } finally {
    setLoading(false);
  }
};
 
  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto">
      {/* Header */}
      <header className="flex items-center gap-3 px-6 py-4 border-b border-slate-700">
        <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center
                        justify-center text-white font-bold text-lg">
          {identity?.assistant_name?.[0] ?? "A"}
        </div>
        <div>
          <h1 className="text-lg font-semibold text-white">
            {identity?.assistant_name ?? "Loading..."}
          </h1>
          <p className="text-xs text-slate-400">
            {identity?.configured ? "Online · Local AI" : "Not configured"}
          </p>
        </div>
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
  );
}