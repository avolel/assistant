// API client module — all HTTP calls to the backend are centralised here.
// Each function is async and returns the `data` field from the axios response,
// so callers receive the parsed JSON directly without unwrapping `.data` themselves.
import axios from "axios";

// Use a relative path so the same build works whether the browser accesses the
// server via localhost, 127.0.0.1, 0.0.0.0, or any other hostname.
// In dev, Vite proxies /api → http://localhost:8000 (see vite.config.js).
const BASE = "/api";

// POST /api/chat/ — send a user message and receive the assistant's reply.
// sessionId=null starts a new session; passing an existing ID continues it.
export async function sendMessage(message, sessionId = null) {
  const { data } = await axios.post(`${BASE}/chat/`, {
    message,
    session_id: sessionId,
  });
  return data;   // { reply: string, session_id: string, emotional_state: object }
}

// GET /api/identity/ — fetch the assistant's name, owner list, and configured status.
export async function getIdentity() {
  const { data } = await axios.get(`${BASE}/identity/`);
  return data;   // { assistant_name, owner_name, owners: [...], configured: bool }
}

// POST /api/identity/setup — first-time setup with assistant name, owner name/email/timezone.
export async function setupAssistant(payload) {
  const { data } = await axios.post(`${BASE}/identity/setup`, payload);
  return data;
}

// PATCH /api/identity/ — rename the assistant. Returns the full updated IdentityResponse.
export async function updateAssistantName(assistantName) {
  const { data } = await axios.patch(`${BASE}/identity/`, { assistant_name: assistantName });
  return data;
}

// POST /api/identity/owners — add a new owner profile. Returns the full IdentityResponse.
export async function addOwner(payload) {
  const { data } = await axios.post(`${BASE}/identity/owners`, payload);
  return data;
}

// DELETE /api/identity/owners/:id — remove an owner. Returns the full IdentityResponse.
export async function removeOwner(ownerId) {
  const { data } = await axios.delete(`${BASE}/identity/owners/${ownerId}`);
  return data;
}

// GET /api/memory/ — fetch all long-term memories (not currently wired in the UI).
export async function getMemories() {
  const { data } = await axios.get(`${BASE}/memory/`);
  return data;
}

// GET /api/sessions/?limit=N — fetch the most recent sessions for the sidebar.
export async function getSessions(limit = 50) {
  const { data } = await axios.get(`${BASE}/sessions/`, { params: { limit } });
  return data;   // { sessions: [...], total: number }
}

// DELETE /api/sessions/:id — delete a session and all its turns.
export async function deleteSession(sessionId) {
  const { data } = await axios.delete(`${BASE}/sessions/${sessionId}`);
  return data;   // { deleted: true, session_id: string }
}

// GET /api/sessions/:id — load a session with its full turn history (for resuming a past chat).
export async function getSession(sessionId) {
  const { data } = await axios.get(`${BASE}/sessions/${sessionId}`);
  return data;   // { session_id, turns: [{role, content, timestamp, emotional_state?}], ... }
}