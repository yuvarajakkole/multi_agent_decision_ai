/**
 * src/pages/ChatPage.jsx
 *
 * Main page layout:
 *
 *  ┌────────────────────────────────────────┐
 *  │  Header                                │
 *  ├────────────────────┬───────────────────┤
 *  │                    │  Agent Timeline   │
 *  │  Chat / Messages   │  Confidence Panel │
 *  │                    │  Loop Summary     │
 *  ├────────────────────┴───────────────────┤
 *  │  Query Form (input)                    │
 *  └────────────────────────────────────────┘
 */

import { useEffect, useRef } from 'react'
import { useDecision } from '../hooks/useDecision'
import { useAgentStore } from '../store/useAgentStore'

import { Header, ErrorBanner }  from '../components/ui/Header'
import WelcomeScreen             from '../components/ui/WelcomeScreen'
import LoopSummary               from '../components/ui/LoopSummary'
import ConfidencePanel           from '../components/ui/ConfidencePanel'
import AgentTimeline             from '../components/timeline/AgentTimeline'
import { UserMessage, AssistantMessage, ThinkingIndicator } from '../components/chat/ChatMessage'
import QueryForm                 from '../components/chat/QueryForm'

export default function ChatPage() {
  const { submit, isProcessing, wsConnected } = useDecision()
  const store   = useAgentStore()
  const chatRef = useRef(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight
    }
  }, [store.messages, isProcessing])

  const hasMessages  = store.messages.length > 0
  const hasActivity  = Object.values(store.agents).some(a => a.status !== 'idle')
  const showSidebar  = hasActivity || store.result

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-[#0f1117]">

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <Header wsConnected={wsConnected} />

      {/* ── Error banner ───────────────────────────────────────────────── */}
      {store.error && (
        <ErrorBanner
          error={store.error}
          onDismiss={() => useAgentStore.setState({ error: null })}
        />
      )}

      {/* ── Main content ───────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden">

        {/* ── Left: Chat panel ─────────────────────────────────────────── */}
        <div className="flex-1 flex flex-col overflow-hidden">

          {/* Messages area */}
          <div
            ref={chatRef}
            className="flex-1 overflow-y-auto px-4 py-4 space-y-2"
          >
            {/* Welcome screen when no messages */}
            {!hasMessages && !isProcessing && <WelcomeScreen />}

            {/* Render messages */}
            {store.messages.map(msg => (
              msg.role === 'user'
                ? <UserMessage      key={msg.id} content={msg.content} />
                : <AssistantMessage key={msg.id} content={msg.content} meta={msg.meta} />
            ))}

            {/* Thinking indicator */}
            {isProcessing && <ThinkingIndicator />}
          </div>

          {/* Input form */}
          <QueryForm onSubmit={submit} isProcessing={isProcessing} />
        </div>

        {/* ── Right: Sidebar ───────────────────────────────────────────── */}
        {showSidebar && (
          <div className="w-80 xl:w-96 border-l border-surface-border flex flex-col overflow-y-auto flex-shrink-0">
            <div className="p-4 space-y-4">

              {/* Agent execution timeline */}
              <AgentTimeline agents={store.agents} />

              {/* Confidence report */}
              {store.result?.confidence_report && (
                <ConfidencePanel confidence={store.result.confidence_report} />
              )}

              {/* Loop summary */}
              {store.loopSummary && (
                <LoopSummary loopSummary={store.loopSummary} />
              )}

              {/* Raw data accordion (for debugging/transparency) */}
              {store.result && (
                <RawDataAccordion result={store.result} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}


/* ── Raw data accordion ─────────────────────────────────────────────────── */

import { useState } from 'react'

function DataBlock({ title, data }) {
  const [open, setOpen] = useState(false)
  if (!data || Object.keys(data).length === 0) return null
  return (
    <div className="border border-surface-border rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full px-3 py-2 text-left text-xs text-gray-400 hover:text-gray-200
                   hover:bg-surface-border/30 transition-colors flex justify-between items-center"
      >
        <span>{title}</span>
        <span className="text-gray-600">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <pre className="px-3 pb-3 text-xs text-gray-500 overflow-x-auto max-h-60 font-mono leading-relaxed">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  )
}

function RawDataAccordion({ result }) {
  return (
    <div className="card p-3 space-y-2">
      <div className="text-xs text-gray-500 uppercase tracking-widest font-semibold mb-1">
        Raw Data
      </div>
      <DataBlock title="Market Insights"    data={result.market_insights} />
      <DataBlock title="Financial Analysis" data={result.financial_analysis} />
      <DataBlock title="Company Knowledge"  data={result.knowledge_summary} />
      <DataBlock title="Strategy Decision"  data={result.decision} />
      <DataBlock title="Execution Log"      data={{ steps: result.execution_log }} />
    </div>
  )
}
