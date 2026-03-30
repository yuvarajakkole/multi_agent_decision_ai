/**
 * src/services/wsService.js
 *
 * WebSocket connection manager.
 * Connects to the backend /ws/decision endpoint and forwards
 * all events to the Zustand store.
 */

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/decision'

let _ws     = null
let _onEvent = null

export function connectWs(onEvent) {
  _onEvent = onEvent

  if (_ws && _ws.readyState === WebSocket.OPEN) {
    return _ws
  }

  _ws = new WebSocket(WS_URL)

  _ws.onopen  = () => { console.log('[ws] connected'); onEvent({ _meta: 'connected' }) }
  _ws.onclose = () => { console.log('[ws] closed');    onEvent({ _meta: 'disconnected' }); _ws = null }
  _ws.onerror = (e) => { console.error('[ws] error', e); onEvent({ _meta: 'error', detail: e }) }

  _ws.onmessage = (msg) => {
    try {
      const data = JSON.parse(msg.data)
      onEvent(data)
    } catch (e) {
      console.warn('[ws] unparseable message', msg.data)
    }
  }

  return _ws
}

export function sendQuery(payload) {
  if (_ws && _ws.readyState === WebSocket.OPEN) {
    _ws.send(JSON.stringify(payload))
    return true
  }
  return false
}

export function closeWs() {
  if (_ws) { _ws.close(); _ws = null }
}

export function isConnected() {
  return _ws && _ws.readyState === WebSocket.OPEN
}
