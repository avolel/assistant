import { useState, useEffect } from "react";
import { exportSession } from "../api/assistant";

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function Sidebar({ sessions, sessionId, deletingId, onClose, onNewChat, onLoadSession, onDeleteSession }) {
  const [exportMenuId, setExportMenuId] = useState(null);

  // Close export dropdown when clicking anywhere outside.
  useEffect(() => {
    if (!exportMenuId) return;
    const close = () => setExportMenuId(null);
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, [exportMenuId]);

  return (
    <aside className="fixed inset-y-0 left-0 z-40 sm:relative sm:inset-auto sm:z-auto w-72 bg-slate-900 border-r border-slate-700 flex flex-col shrink-0">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
        <span className="text-sm font-semibold text-slate-300">Chat History</span>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white text-lg leading-none"
          aria-label="Close sidebar"
        >
          ×
        </button>
      </div>
      <div className="px-3 py-2">
        <button
          onClick={onNewChat}
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
            onClick={() => onLoadSession(s.session_id)}
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
            {/* Export + Delete buttons */}
            <div className="ml-2 shrink-0 flex items-center gap-1 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity relative">
              {/* Export dropdown */}
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
              {/* Delete button */}
              <button
                onClick={(e) => onDeleteSession(s.session_id, e)}
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
  );
}