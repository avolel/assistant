// ChatInput renders the message composer at the bottom of the chat.
// It's a "controlled component" — the textarea value is driven by React state (text),
// not read directly from the DOM. Every keystroke updates state, React re-renders.
import { useState } from "react";
import { Send, Mic, Square } from "lucide-react";

export function ChatInput({ onSend, onVoice, onStopVoice, loading, voiceEnabled, recording, recordingSeconds, recordingDuration = 5 }) {
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

      {/* While recording, replace the textarea with an animated pill + stop button. */}
      {recording ? (
        <button
          onClick={onStopVoice}
          className="flex-1 flex items-center justify-center gap-3 py-3 rounded-xl
                     bg-red-600 hover:bg-red-500 text-white font-medium transition-colors"
        >
          {/* Pulsing red dot indicator */}
          <span className="w-2.5 h-2.5 rounded-full bg-white animate-pulse shrink-0" />
          Recording… {recordingSeconds}s / {recordingDuration}s
          {/* Square icon signals "stop" */}
          <Square size={16} className="ml-1 shrink-0" />
        </button>
      ) : (
        <textarea
          className="flex-1 resize-none rounded-xl bg-slate-700 text-slate-100
                     px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-blue-500
                     max-h-32"
          rows={1}
          placeholder="Message Aria…"
          value={text}
          // onChange fires on every keystroke. e.target.value is the current textarea content.
          onChange={e => setText(e.target.value)}
          onKeyDown={e => {
            // Submit on Enter (without Shift). Shift+Enter inserts a newline instead.
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
      )}

      {/* Mic button: only visible when voice is enabled and not currently recording. */}
      {voiceEnabled && !recording && (
        <button
          onClick={onVoice}
          disabled={loading}
          className="p-3 rounded-xl bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-slate-300 transition-colors"
        >
          <Mic size={18} />
        </button>
      )}

      {/* Send button: hidden while recording (no text to send). */}
      {!recording && (
        <button
          onClick={handleSend}
          disabled={loading || !text.trim()}
          className="p-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40
                     text-white transition-colors"
        >
          <Send size={18} />
        </button>
      )}
    </div>
  );
}