import { useState } from "react";
import { updateAssistantName, addOwner, removeOwner, getSession } from "../api/assistant";

export function SettingsModal({ identity, onClose, onIdentityChange, sessionId, onClearChat }) {
  const [nameInput,   setNameInput]   = useState(identity?.assistant_name ?? "");
  const [nameSaving,  setNameSaving]  = useState(false);
  const [nameError,   setNameError]   = useState("");

  const [ownerName,   setOwnerName]   = useState("");
  const [ownerEmail,  setOwnerEmail]  = useState("");
  const [ownerSaving, setOwnerSaving] = useState(false);
  const [ownerError,  setOwnerError]  = useState("");
  const [removingId,  setRemovingId]  = useState(null);

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
      onClick={onClose}>

      <div
        className="bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6 space-y-6"
        onClick={e => e.stopPropagation()}>

        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Assistant Settings</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl leading-none">×</button>
        </div>

        {/* ── Assistant Name ── */}
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

        {/* ── Owners ── */}
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