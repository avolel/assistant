import { useState } from "react";
import { Send, Mic } from "lucide-react"; // Using lucide-react for icons
 
// ChatInput component for sending messages and voice input
export function ChatInput({ onSend, onVoice, loading, voiceEnabled }) {
  const [text, setText] = useState("");
 
  const handleSend = () => {
    if (!text.trim() || loading) return;
    onSend(text.trim());
    setText("");
  };
 
  return (
    <div className="flex items-end gap-2 p-4 border-t border-slate-700">
      <textarea
        className="flex-1 resize-none rounded-xl bg-slate-700 text-slate-100
                   px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-blue-500
                   max-h-32"
        rows={1}
        placeholder="Message..."
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={e => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
      />
      {voiceEnabled && (
        <button onClick={onVoice}
          className="p-3 rounded-xl bg-slate-700 hover:bg-slate-600 text-slate-300">
          <Mic size={18} />
        </button>
      )}
      <button onClick={handleSend} disabled={loading || !text.trim()}
        className="p-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40
                   text-white transition-colors">
        <Send size={18} />
      </button>
    </div>
  );
}