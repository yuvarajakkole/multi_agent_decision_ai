/**
 * src/components/chat/ChatMessage.jsx
 *
 * Individual chat message bubble.
 * User messages: simple text.
 * Assistant messages: full markdown report with decision summary above.
 */

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import DecisionCard from '../decision/DecisionCard'

const DECISION_ICONS = { GO: '✅', GO_WITH_CONDITIONS: '⚠️', WAIT: '⏳', NO_GO: '🚫' }

export function UserMessage({ content }) {
  return (
    <div className="flex justify-end mb-4">
      <div className="max-w-[80%] bg-brand-600/30 border border-brand-600/40 rounded-2xl rounded-tr-sm px-4 py-3">
        <p className="text-gray-100 text-sm leading-relaxed">{content}</p>
      </div>
    </div>
  )
}

export function AssistantMessage({ content, meta }) {
  const hasDecision = meta?.decision

  return (
    <div className="flex gap-3 mb-6 animate-slide-up">
      {/* Avatar */}
      <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-sm flex-shrink-0 mt-1">
        🤖
      </div>

      <div className="flex-1 min-w-0">
        {/* Decision card (if this message has a decision) */}
        {hasDecision && meta && (
          <div className="mb-4">
            <DecisionCard
              decision={{
                decision:       meta.decision,
                adjusted_score: meta.score,
                summary:        null,   // summary is in the report below
                rationale:      meta.rationale,
                key_risks:      meta.key_risks,
                next_steps:     meta.next_steps,
              }}
              confidence={{ weighted_confidence: meta.confidence, label: meta.label }}
            />
          </div>
        )}

        {/* Full markdown report */}
        {content && (
          <div className="card p-5">
            <div className="prose-dark">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export function ThinkingIndicator() {
  return (
    <div className="flex gap-3 mb-6">
      <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-sm flex-shrink-0 mt-1">
        🤖
      </div>
      <div className="card px-4 py-3">
        <div className="flex items-center gap-2 text-gray-400 text-sm">
          <div className="flex gap-1">
            {[0, 1, 2].map(i => (
              <div
                key={i}
                className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
          <span>Agents are working…</span>
        </div>
      </div>
    </div>
  )
}
