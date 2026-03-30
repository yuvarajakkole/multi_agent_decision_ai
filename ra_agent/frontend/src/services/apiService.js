/**
 * src/services/apiService.js
 *
 * HTTP API calls to the backend.
 * Used as the primary method (simpler than WebSocket for the demo).
 * WebSocket is used for real-time streaming on top of this.
 */

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function submitDecision({ user_query, market, budget, timeline_months }) {
  const res = await fetch(`${BASE}/api/decision`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ user_query, market, budget, timeline_months }),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }
  return res.json()
}

export async function getHistory() {
  const res = await fetch(`${BASE}/api/history`)
  return res.json()
}

export async function recordOutcome(request_id, actual_outcome, notes = '') {
  const res = await fetch(`${BASE}/api/outcome`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ request_id, actual_outcome, notes }),
  })
  return res.json()
}

export async function healthCheck() {
  try {
    const res = await fetch(`${BASE}/api/health`, { signal: AbortSignal.timeout(3000) })
    return res.ok
  } catch {
    return false
  }
}
