import ReactMarkdown from "react-markdown"; // For rendering markdown content in messages
 
// MessageBubble component to display individual messages in the chat interface
export function MessageBubble({ role, content, emotionalState }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center
                        justify-center text-white text-sm font-bold mr-3 shrink-0">
          AI
        </div>
      )}
      <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed
        ${isUser
          ? "bg-blue-600 text-white rounded-tr-sm"
          : "bg-slate-700 text-slate-100 rounded-tl-sm"
        }`}
      >
        <ReactMarkdown>{content}</ReactMarkdown>
        {!isUser && emotionalState && (
          <EmotionBar state={emotionalState} />
        )}
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-slate-500 flex items-center
                        justify-center text-white text-sm ml-3 shrink-0">
          U
        </div>
      )}
    </div>
  );
}
 
function EmotionBar({ state }) {
  const mood = Math.round(state.mood * 100);
  const color = mood > 60 ? "bg-green-500" : mood > 35 ? "bg-yellow-500" : "bg-red-400";
  return (
    <div className="mt-2 pt-2 border-t border-slate-600">
      <div className="text-xs text-slate-400 mb-1">Mood</div>
      <div className="w-full h-1.5 bg-slate-600 rounded-full">
        <div className={`h-1.5 rounded-full ${color}`} style={{width:`${mood}%`}} />
      </div>
    </div>
  );
}