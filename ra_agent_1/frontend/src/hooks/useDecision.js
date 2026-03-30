/**
 * src/hooks/useDecision.js
 *
 * Main hook that orchestrates a decision request.
 *
 * Strategy:
 * 1. Open WebSocket for real-time agent events (streaming timeline)
 * 2. POST to HTTP API in parallel (guaranteed response)
 * 3. WebSocket events update agent timeline as they arrive
 * 4. HTTP response provides the final complete result
 */

import { useEffect, useRef, useCallback } from 'react'
import { useAgentStore } from '../store/useAgentStore'
import { submitDecision } from '../services/apiService'
import { connectWs, sendQuery, isConnected } from '../services/wsService'

export function useDecision() {
  const store = useAgentStore()
  const wsRef = useRef(null)

  // Connect WebSocket on mount
  useEffect(() => {
    wsRef.current = connectWs((event) => {
      if (event._meta === 'connected') {
        store.setWsConnected(true)
        return
      }
      if (event._meta === 'disconnected') {
        store.setWsConnected(false)
        return
      }
      if (event._meta === 'error') return

      // Forward agent events to store
      store.handleWsEvent(event)
    })

    return () => {
      // Don't close on unmount — keep connection alive across renders
    }
  }, [])

  const submit = useCallback(async ({ query, market, budget, timeline }) => {
    store.reset()
    store.startProcessing(query, `req_${Date.now()}`)

    const payload = {
      user_query:      query,
      market:          market,
      budget:          parseFloat(budget) || 1_000_000,
      timeline_months: parseInt(timeline) || 12,
    }

    // Send via WebSocket for real-time streaming (best effort)
    if (isConnected()) {
      sendQuery(payload)
    }

    // Always use HTTP for the complete result (reliable)
    try {
      const result = await submitDecision(payload)
      store.setResult(result)

      // Mark all agents as complete if WebSocket missed events
      const { agents } = useAgentStore.getState()
      // (agents already updated via WS events — HTTP just fills the gaps)

    } catch (err) {
      store.setError(err.message || 'Request failed')
    }
  }, [store])

  return {
    submit,
    isProcessing: store.isProcessing,
    wsConnected:  store.wsConnected,
    messages:     store.messages,
    agents:       store.agents,
    result:       store.result,
    loopSummary:  store.loopSummary,
    error:        store.error,
  }
}
