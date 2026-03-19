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
 
export async function getMemories() {
  const { data } = await axios.get(`${BASE}/memory/`);
  return data;
}