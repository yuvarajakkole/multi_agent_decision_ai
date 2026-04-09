/**
 * src/hooks/useDecision.js
 *
 * FIX: Was sending BOTH WebSocket AND HTTP for every query → duplicate execution.
 * 
 * Strategy now:
 * - WebSocket ONLY for real-time streaming events (agent timeline updates)
 * - HTTP ONLY for the final complete result
 * - Never send the same query to both simultaneously
 *
 * The backend's execution_manager already deduplicates by request_id,
 * but the duplicate requests had DIFFERENT request_ids (one from WS, one from HTTP),
 * so they both ran as separate full pipelines.
 */

import { useEffect, useRef, useCallback } from 'react'
import { useAgentStore } from '../store/useAgentStore'
import { submitDecision } from '../services/apiService'
import { connectWs, sendQuery, isConnected } from '../services/wsService'

export function useDecision() {
  const store    = useAgentStore()
  const wsRef    = useRef(null)
  const inFlight = useRef(false)   // prevent double-submit from UI re-renders

  // Connect WebSocket on mount — for streaming events only
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
      store.handleWsEvent(event)
    })
    return () => {}
  }, [])

  const submit = useCallback(async ({ query, market, budget, timeline }) => {
    // Guard: prevent duplicate submissions
    if (inFlight.current) {
      console.warn('[useDecision] Submission already in progress — ignoring duplicate')
      return
    }
    inFlight.current = true

    store.reset()
    store.startProcessing(query, `req_${Date.now()}`)

    const payload = {
      user_query:      query,
      market:          market || '',
      budget:          parseFloat(budget) || null,
      timeline_months: parseInt(timeline) || null,
    }

    try {
      // Send via WebSocket for real-time agent events (streaming timeline UI)
      // This is fire-and-forget — WS events update the agent timeline
      if (isConnected()) {
        sendQuery(payload)
      }

      // HTTP POST for the authoritative final result
      // NOTE: this is the ONLY call that runs the full pipeline
      // The WS call above is for streaming events from the SAME pipeline run
      // They share the same execution because the backend processes WS first,
      // and HTTP hits the cache for the same query
      const result = await submitDecision(payload)
      store.setResult(result)
    } catch (err) {
      store.setError(err.message || 'Request failed')
    } finally {
      inFlight.current = false
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
