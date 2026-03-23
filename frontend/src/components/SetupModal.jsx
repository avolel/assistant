import { useState } from "react";
import { setupAssistant } from "../api/assistant";

export function SetupModal({ onSetupComplete }) {
  const [assistantName, setAssistantName] = useState("");
  const [ownerName,     setOwnerName]     = useState("");
  const [ownerEmail,    setOwnerEmail]    = useState("");
  const [saving,        setSaving]        = useState(false);
  const [error,         setError]         = useState("");

  const canSubmit = assistantName.trim() && ownerName.trim() && !saving;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    setSaving(true);
    setError("");
    try {
      const identity = await setupAssistant({
        assistant_name: assistantName.trim(),
        owner_name:     ownerName.trim(),
        owner_email:    ownerEmail.trim() || undefined,
      });
      onSetupComplete(identity);
    } catch (err) {
      setError(err?.response?.data?.detail ?? "Setup failed. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div
        className="bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md mx-4 p-8 space-y-6"
        onClick={e => e.stopPropagation()}
      >
        <div className="text-center space-y-1">
          <div className="text-4xl mb-3">🤖</div>
          <h2 className="text-xl font-semibold text-white">Welcome! Let's set things up.</h2>
          <p className="text-slate-400 text-sm">Give your assistant a name, and tell it who you are.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Assistant Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={assistantName}
              onChange={e => setAssistantName(e.target.value)}
              className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm border border-slate-600
                         focus:outline-none focus:border-blue-500"
              placeholder="e.g. Aria"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Your Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={ownerName}
              onChange={e => setOwnerName(e.target.value)}
              className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm border border-slate-600
                         focus:outline-none focus:border-blue-500"
              placeholder="e.g. Alex"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Your Email <span className="text-slate-500 text-xs">(optional)</span>
            </label>
            <input
              type="email"
              value={ownerEmail}
              onChange={e => setOwnerEmail(e.target.value)}
              className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm border border-slate-600
                         focus:outline-none focus:border-blue-500"
              placeholder="you@example.com"
            />
          </div>

          {error && <p className="text-red-400 text-xs">{error}</p>}

          <button
            type="submit"
            disabled={!canSubmit}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed
                       text-white font-medium rounded-lg transition-colors"
          >
            {saving ? "Setting up…" : "Get Started"}
          </button>
        </form>
      </div>
    </div>
  );
}