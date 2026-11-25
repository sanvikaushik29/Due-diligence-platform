
import axios from "axios";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const client = axios.create({ baseURL: BASE });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response && err.response.status === 401) {
      localStorage.removeItem("auth_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export async function login(username, password) {
  const res = await axios.post(`${BASE}/auth/login`, { username, password });
  localStorage.setItem("auth_token", res.data.token);
}

export function logout() {
  localStorage.removeItem("auth_token");
  window.location.href = "/login";
}

export function isAuthenticated() {
  return !!localStorage.getItem("auth_token");
}

export async function extractDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await client.post(`/documents/extract`, formData);
  return res.data;
}

export async function canonicalizeDocument(extraction) {
  const res = await client.post(`/documents/canonicalize`, extraction);
  return res.data;
}

export async function consistencyCheck(metrics, extractions) {
  const res = await client.post(`/documents/consistency-check`, { metrics, extractions });
  return res.data;
}

export async function riskAssessment(metrics, extractions) {
  const res = await client.post(`/documents/risk-assessment`, { metrics, extractions });
  return res.data;
}

export async function openingSummary(risk, consistency) {
  const res = await client.post(`/chat/opening-summary-direct`, { risk, consistency });
  return res.data.summary;
}

export async function indexSession(sessionId, extractions, metrics, consistency, risk) {
  const res = await client.post(`/chat/index`, {
    session_id: sessionId, extractions, metrics, consistency, risk,
  });
  return res.data;
}

export async function chatQuery(sessionId, message, history) {
  const res = await client.post(`/chat/query`, { session_id: sessionId, message, history });
  return res.data;
}

export async function generateReport(companyName, extractions, canonicalMetrics, consistency, risk, summary) {
  const res = await client.post(
    `/documents/generate-report`,
    { company_name: companyName, extractions, canonical_metrics: canonicalMetrics, consistency, risk, opening_summary: summary },
    { responseType: "blob" }
  );
  return res.data;
}

export async function saveSession(sessionId, companyName, extractions, canonicalMetrics, consistency, risk, summary) {
  const res = await client.post(`/sessions/save`, {
    session_id: sessionId, company_name: companyName, extractions,
    canonical_metrics: canonicalMetrics, consistency, risk, summary,
  });
  return res.data;
}

export async function listSessions() {
  const res = await client.get(`/sessions`);
  return res.data;
}

export async function getSession(sessionId) {
  const res = await client.get(`/sessions/${sessionId}`);
  return res.data;
}
