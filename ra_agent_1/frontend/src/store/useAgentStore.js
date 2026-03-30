/**
 * src/store/useAgentStore.js
 *
 * Central state store (Zustand).
 * All WebSocket events, agent states, messages, and results live here.
 */

import { create } from 'zustand'

const AGENT_ORDER = [
  'supervisor',
  'market_agent',
  'financial_agent',
  'knowledge_agent',
  'strategy_agent',
  'communication_agent',
]

const AGENT_LABELS = {
  supervisor:            'Supervisor',
  market_agent:          'Market Research',
  financial_agent:       'Financial Analysis',
  knowledge_agent:       'Company Intelligence',
  strategy_agent:        'Strategy Decision',
  communication_agent:   'Report Generation',
}

const AGENT_ICONS = {
  supervisor:            '🎯',
  market_agent:          '🌍',
  financial_agent:       '💰',
  knowledge_agent:       '🏢',
  strategy_agent:        '⚡',
  communication_agent:   '📝',
}

const initialAgentState = () =>
  Object.fromEntries(
    AGENT_ORDER.map(a => [a, {
      status:    'idle',    // idle | running | complete | error | retrying
      startedAt: null,
      duration:  null,
      payload:   null,
      retries:   0,
    }])
  )

export const useAgentStore = create((set, get) => ({
  // ── State ────────────────────────────────────────────────────────────────
  messages:       [],          // chat messages
  agents:         initialAgentState(),
  isProcessing:   false,
  wsConnected:    false,
  currentReqId:   null,
  result:         null,        // final result object
  loopSummary:    null,        // retry loop info
  error:          null,

  // ── Actions ──────────────────────────────────────────────────────────────

  reset() {
    set({
      agents:       initialAgentState(),
      isProcessing: false,
      result:       null,
      loopSummary:  null,
      error:        null,
    })
  },

  startProcessing(query, reqId) {
    set({
      isProcessing: true,
      currentReqId: reqId,
      result:       null,
      error:        null,
      loopSummary:  null,
      agents:       initialAgentState(),
    })
    get().addMessage({ role: 'user', content: query })
  },

  setWsConnected(v) { set({ wsConnected: v }) },

  addMessage(msg) {
    set(s => ({
      messages: [...s.messages, {
        id:        Date.now() + Math.random(),
        timestamp: new Date().toISOString(),
        ...msg,
      }],
    }))
  },

  handleWsEvent(event) {
    const { event: type, agent, payload } = event

    if (type === 'agent_start') {
      set(s => ({
        agents: {
          ...s.agents,
          [agent]: {
            ...s.agents[agent],
            status:    'running',
            startedAt: Date.now(),
            payload:   null,
          },
        },
      }))
    }

    if (type === 'agent_complete') {
      set(s => {
        const prev       = s.agents[agent] || {}
        const duration   = prev.startedAt ? ((Date.now() - prev.startedAt) / 1000).toFixed(1) : null
        const wasRetrying = prev.status === 'retrying'
        return {
          agents: {
            ...s.agents,
            [agent]: {
              ...prev,
              status:   payload?.needs_retry ? 'retrying' : 'complete',
              duration,
              payload,
              retries:  wasRetrying ? (prev.retries || 0) + 1 : prev.retries || 0,
            },
          },
        }
      })
    }

    if (type === 'final_result') {
      set({
        result:       payload,
        isProcessing: false,
      })
    }

    if (type === 'error') {
      set(s => ({
        error:        payload?.message || 'An error occurred',
        isProcessing: false,
        agents: agent ? {
          ...s.agents,
          [agent]: { ...s.agents[agent], status: 'error' },
        } : s.agents,
      }))
    }
  },

  setResult(result) {
    const decision  = result?.decision || {}
    const conf      = result?.confidence_report || {}
    const loopSummary = result?.loop_summary || {}

    set({
      result:       { ...result, decision, conf },
      loopSummary,
      isProcessing: false,
    })

    // Add assistant message
    const decisionText = decision?.decision || 'Unknown'
    const score        = decision?.adjusted_score
    const summary      = decision?.summary || ''
    const report       = result?.final_report || ''

    get().addMessage({
      role:    'assistant',
      content: report || summary,
      meta: {
        decision:    decisionText,
        score,
        confidence:  conf?.weighted_confidence,
        label:       conf?.label,
        rationale:   decision?.rationale || [],
        key_risks:   decision?.key_risks  || [],
        next_steps:  decision?.next_steps || [],
      },
    })
  },

  setError(err) {
    set({ error: err, isProcessing: false })
  },
}))

export { AGENT_ORDER, AGENT_LABELS, AGENT_ICONS }
