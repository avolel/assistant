import { useState } from "react";
import { updateAssistantName, updateOwner } from "../api/assistant";

export function SettingsModal({ identity, onClose, onIdentityChange }) {
  const [assistantName, setAssistantName] = useState(identity?.assistant_name ?? "");
  const [assistantSaving, setAssistantSaving] = useState(false);
  const [assistantError,  setAssistantError]  = useState("");

  const owner = identity?.owners?.[0];
  const [ownerName,    setOwnerName]    = useState(owner?.name  ?? "");
  const [ownerEmail,   setOwnerEmail]   = useState(owner?.email ?? "");
  const [ownerSaving,  setOwnerSaving]  = useState(false);
  const [ownerError,   setOwnerError]   = useState("");

  const handleSaveAssistant = async () => {
    if (!assistantName.trim()) return;
    setAssistantSaving(true);
    setAssistantError("");
    try {
      const updated = await updateAssistantName(assistantName.trim());
      onIdentityChange(updated);
    } catch (e) {
      setAssistantError(e?.response?.data?.detail ?? "Failed to update name");
    } finally {
      setAssistantSaving(false);
    }
  };

  const handleSaveOwner = async () => {
    if (!ownerName.trim()) return;
    setOwnerSaving(true);
    setOwnerError("");
    try {
      const updated = await updateOwner({
        name:  ownerName.trim(),
        email: ownerEmail.trim() || null,
      });
      onIdentityChange(updated);
    } catch (e) {
      setOwnerError(e?.response?.data?.detail ?? "Failed to update owner");
    } finally {
      setOwnerSaving(false);
    }
  };

  const assistantUnchanged = assistantName.trim() === identity?.assistant_name;
  const ownerUnchanged = ownerName.trim() === (owner?.name ?? "") &&
                         (ownerEmail.trim() || null) === (owner?.email ?? null);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={onClose}
    >
      <div
        className="bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6 space-y-6"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Settings</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl leading-none">×</button>
        </div>

        {/* ── Assistant ── */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Assistant Name</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={assistantName}
              onChange={e => setAssistantName(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSaveAssistant()}
              className="flex-1 bg-slate-700 text-white rounded-lg px-3 py-2 text-sm border border-slate-600
                         focus:outline-none focus:border-blue-500"
              placeholder="e.g. Aria"
            />
            <button
              onClick={handleSaveAssistant}
              disabled={assistantSaving || !assistantName.trim() || assistantUnchanged}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm
                         rounded-lg font-medium transition-colors"
            >
              {assistantSaving ? "Saving…" : "Save"}
            </button>
          </div>
          {assistantError && <p className="text-red-400 text-xs mt-1">{assistantError}</p>}
        </div>

        {/* ── Owner ── */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Your Profile</label>
          <div className="space-y-2">
            <input
              type="text"
              value={ownerName}
              onChange={e => setOwnerName(e.target.value)}
              className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm border border-slate-600
                         focus:outline-none focus:border-blue-500"
              placeholder="Your name"
            />
            <input
              type="email"
              value={ownerEmail}
              onChange={e => setOwnerEmail(e.target.value)}
              className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm border border-slate-600
                         focus:outline-none focus:border-blue-500"
              placeholder="Your email (optional)"
            />
            <button
              onClick={handleSaveOwner}
              disabled={ownerSaving || !ownerName.trim() || ownerUnchanged}
              className="w-full py-2 bg-slate-600 hover:bg-slate-500 disabled:opacity-50 text-white text-sm
                         rounded-lg font-medium transition-colors"
            >
              {ownerSaving ? "Saving…" : "Save Profile"}
            </button>
            {ownerError && <p className="text-red-400 text-xs">{ownerError}</p>}
          </div>
        </div>

      </div>
    </div>
  );
}