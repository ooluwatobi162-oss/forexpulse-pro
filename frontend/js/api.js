/**
 * ForexPulse Pro — API Client
 * Connects the frontend to the FastAPI backend.
 * Set API_BASE to your Render backend URL after deployment.
 */

const API_BASE = window.FOREXPULSE_API || 'http://localhost:8000/api';
const WS_BASE  = window.FOREXPULSE_WS  || 'ws://localhost:8000/ws';

// ── HTTP Helpers ──────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`API error [${path}]:`, err.message);
    return null;
  }
}

// ── Prices ────────────────────────────────────────────────────────────────────

export const Prices = {
  getAll:      () => apiFetch('/prices'),
  getPair:     (pair) => apiFetch(`/prices/${pair.replace('/', '-')}`),
  getStrength: () => apiFetch('/prices/strength'),
  getMovers:   (n = 5) => apiFetch(`/prices/movers?n=${n}`),
  getSentiment:() => apiFetch('/prices/sentiment'),
};

// ── News ──────────────────────────────────────────────────────────────────────

export const News = {
  getAll:     (currency = '', limit = 20) =>
    apiFetch(`/news?${currency ? `currency=${currency}&` : ''}limit=${limit}`),
  getBreaking:(limit = 5) => apiFetch(`/news/breaking?limit=${limit}`),
};

// ── Signals ───────────────────────────────────────────────────────────────────

export const Signals = {
  getAll:  (timeframe = 'H4') => apiFetch(`/signals?timeframe=${timeframe}`),
  getTop:  (n = 5) => apiFetch(`/signals/top?n=${n}`),
  getPair: (pair, tf = 'H4') => apiFetch(`/signals/${pair.replace('/', '-')}?timeframe=${tf}`),
};

// ── Analysis ──────────────────────────────────────────────────────────────────

export const Analysis = {
  getPair: (pair, timeframe = 'H1') =>
    apiFetch(`/analysis/${pair.replace('/', '-')}?timeframe=${timeframe}`),
};

// ── Calendar ──────────────────────────────────────────────────────────────────

export const Calendar = {
  getAll:     () => apiFetch('/calendar'),
  getUpcoming:(n = 5) => apiFetch(`/calendar/upcoming?n=${n}`),
};

// ── AI Chat ───────────────────────────────────────────────────────────────────

export const AIChat = {
  send: (message, history = []) =>
    apiFetch('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, history }),
    }),
};

// ── WebSocket: Live Prices ────────────────────────────────────────────────────

export function connectPriceStream(onMessage) {
  const ws = new WebSocket(`${WS_BASE}/prices`);
  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.type === 'prices') onMessage(data.data);
    } catch (err) {}
  };
  ws.onerror   = () => console.warn('WS price stream error');
  ws.onclose   = () => setTimeout(() => connectPriceStream(onMessage), 3000);
  return ws;
}

// ── WebSocket: News Stream ────────────────────────────────────────────────────

export function connectNewsStream(onMessage) {
  const ws = new WebSocket(`${WS_BASE}/news`);
  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.type === 'news') onMessage(data.data);
    } catch (err) {}
  };
  ws.onerror   = () => console.warn('WS news stream error');
  ws.onclose   = () => setTimeout(() => connectNewsStream(onMessage), 5000);
  return ws;
}
