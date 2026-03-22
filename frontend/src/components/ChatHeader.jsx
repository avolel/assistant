export function ChatHeader({ identity, online, onToggleSidebar, onOpenMemory, onOpenSettings }) {
  return (
    <header className="flex items-center gap-2 sm:gap-3 px-3 sm:px-6 py-3 sm:py-4 border-b border-slate-700">
      <button
        onClick={onToggleSidebar}
        style={{ fontSize: "22px", color: "#cbd5e1", background: "none", border: "none", cursor: "pointer", padding: "4px 8px", lineHeight: 1 }}
        aria-label="Toggle history"
        title="Chat history"
      >
        ☰
      </button>
      <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-lg shrink-0">
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
        onClick={onOpenMemory}
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
      {/* Settings gear button */}
      <button
        onClick={onOpenSettings}
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
  );
}