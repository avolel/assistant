// MessageBubble renders one chat message — either a user message (right-aligned, blue)
// or an assistant message (left-aligned, dark) with optional emotional state bars.
import ReactMarkdown from "react-markdown";

// Props are destructured directly in the function signature — equivalent to:
// function MessageBubble(props) { const { role, content, emotionalState } = props; ... }
export function MessageBubble({ role, content, emotionalState }) {
  const isUser = role === "user";

  return (
    // Conditional className: user messages are pushed right with justify-end.
    // Template literal strings in className let you combine static and dynamic classes.
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>

      {/* Avatar for assistant messages — shown on the left. ! negates isUser. */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center
                        justify-center text-white text-sm font-bold mr-3 shrink-0">
          AI
        </div>
      )}

      {/* Message bubble — different colours for user vs. assistant */}
      <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed
        ${isUser
          ? "bg-blue-600 text-white rounded-tr-sm"       // User: blue, sharp top-right corner
          : "bg-slate-700 text-slate-100 rounded-tl-sm"  // Assistant: dark, sharp top-left corner
        }`}
      >
        {/* ReactMarkdown renders markdown syntax (bold, code blocks, lists) in the content string. */}
        <ReactMarkdown>{content}</ReactMarkdown>

        {/* Show emotion bars only on assistant messages that include emotional state data. */}
        {!isUser && emotionalState && (
          <EmotionBar state={emotionalState} />
        )}
      </div>

      {/* Avatar for user messages — shown on the right. */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-slate-500 flex items-center
                        justify-center text-white text-sm ml-3 shrink-0">
          U
        </div>
      )}
    </div>
  );
}

// EmotionBar is a private component (lowercase first letter convention is not enforced,
// but it's not exported so it's only usable within this file).
function EmotionBar({ state }) {
  // Convert 0.0–1.0 floats to percentages for CSS width styling.
  const mood       = Math.round(state.mood       * 100);
  const trust      = Math.round(state.trust      * 100);
  const engagement = Math.round(state.engagement * 100);
  const stress     = Math.round(state.stress     * 100);

  // Each variable gets a colour based on its value: green (good) → yellow (mid) → red (bad).
  // For stress, high is bad; for the others, high is good — but the same colour scale works
  // here because we just display the raw value, not a "health" indicator.
  const color_mood       = mood       > 60 ? "bg-green-500" : mood       > 35 ? "bg-yellow-500" : "bg-red-400";
  const color_trust      = trust      > 60 ? "bg-green-500" : trust      > 35 ? "bg-yellow-500" : "bg-red-400";
  const color_engagement = engagement > 60 ? "bg-green-500" : engagement > 35 ? "bg-yellow-500" : "bg-red-400";
  const color_stress     = stress     > 60 ? "bg-green-500" : stress     > 35 ? "bg-yellow-500" : "bg-red-400";

  return (
    <div className="mt-2 pt-2 border-t border-slate-600">
      {/* Each metric: label + a full-width grey track with a coloured fill div inside. */}
      {/* style={{width:`${mood}%`}} sets the fill width as an inline style (Tailwind can't do dynamic %). */}
      <div className="text-xs text-slate-400 mb-1">Mood</div>
      <div className="w-full h-1.5 bg-slate-600 rounded-full">
        <div className={`h-1.5 rounded-full ${color_mood}`} style={{ width: `${mood}%` }} />
      </div>
      <div className="text-xs text-slate-400 mb-1 mt-2">Trust</div>
      <div className="w-full h-1.5 bg-slate-600 rounded-full">
        <div className={`h-1.5 rounded-full ${color_trust}`} style={{ width: `${trust}%` }} />
      </div>
      <div className="text-xs text-slate-400 mb-1 mt-2">Engagement</div>
      <div className="w-full h-1.5 bg-slate-600 rounded-full">
        <div className={`h-1.5 rounded-full ${color_engagement}`} style={{ width: `${engagement}%` }} />
      </div>
      <div className="text-xs text-slate-400 mb-1 mt-2">Stress</div>
      <div className="w-full h-1.5 bg-slate-600 rounded-full">
        <div className={`h-1.5 rounded-full ${color_stress}`} style={{ width: `${stress}%` }} />
      </div>
    </div>
  );
}