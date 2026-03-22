// ChatInput renders the message composer at the bottom of the chat.
// It's a "controlled component" — the textarea value is driven by React state (text),
// not read directly from the DOM. Every keystroke updates state, React re-renders.
import { useState } from "react";
import { Send, Mic } from "lucide-react";

export function ChatInput({ onSend, onVoice, loading, voiceEnabled }) {
  // useState returns [currentValue, setterFunction].
  // setText("...") triggers a re-render with the new value.
  const [text, setText] = useState("");

  const handleSend = () => {
    // Guard: don't send if the trimmed text is empty, or if a request is already in flight.
    if (!text.trim() || loading) return;
    onSend(text.trim());   // Call the parent's handler (defined in App.jsx)
    setText("");           // Clear the input after sending
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
        // onChange fires on every keystroke. e.target.value is the current textarea content.
        onChange={e => setText(e.target.value)}
        onKeyDown={e => {
          // Submit on Enter (without Shift). Shift+Enter inserts a newline instead.
          // e.preventDefault() stops the default Enter behaviour (inserting a newline).
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
      />

      {/* Conditional render: only show the mic button if voice is enabled. */}
      {voiceEnabled && (
        <button onClick={onVoice}
          className="p-3 rounded-xl bg-slate-700 hover:bg-slate-600 text-slate-300">
          <Mic size={18} />
        </button>
      )}

      {/* disabled prop prevents clicking while loading or when the input is empty. */}
      <button onClick={handleSend} disabled={loading || !text.trim()}
        className="p-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40
                   text-white transition-colors">
        <Send size={18} />
      </button>
    </div>
  );
}