import axios from "axios";
 
const BASE = "http://localhost:8000/api";
 
export async function sendMessage(message, sessionId = null) {
  const { data } = await axios.post(`${BASE}/chat/`, {
    message,
    session_id: sessionId,
  });
  return data;   // { reply, session_id, emotional_state }
}
 
export async function getIdentity() {
  const { data } = await axios.get(`${BASE}/identity/`);
  return data;   // { assistant_name, owner_name, configured }
}
 
export async function setupAssistant(payload) {
  const { data } = await axios.post(`${BASE}/identity/setup`, payload);
  return data;
}

export async function updateAssistantName(assistantName) {
  const { data } = await axios.patch(`${BASE}/identity/`, { assistant_name: assistantName });
  return data;  // full IdentityResponse
}

export async function addOwner(payload) {
  const { data } = await axios.post(`${BASE}/identity/owners`, payload);
  return data;  // full IdentityResponse
}

export async function removeOwner(ownerId) {
  const { data } = await axios.delete(`${BASE}/identity/owners/${ownerId}`);
  return data;  // full IdentityResponse
}
 
export async function getMemories() {
  const { data } = await axios.get(`${BASE}/memory/`);
  return data;
}

export async function getSessions(limit = 50) {
  const { data } = await axios.get(`${BASE}/sessions/`, { params: { limit } });
  return data; // { sessions: [...], total }
}

export async function deleteSession(sessionId) {
  const { data } = await axios.delete(`${BASE}/sessions/${sessionId}`);
  return data; // { deleted, session_id }
}

export async function getSession(sessionId) {
  const { data } = await axios.get(`${BASE}/sessions/${sessionId}`);
  return data; // { session_id, turns: [{role, content, timestamp}], ... }
}