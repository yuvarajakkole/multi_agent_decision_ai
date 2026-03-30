/**
 * src/components/timeline/AgentTimeline.jsx
 *
 * Vertical timeline showing each agent's execution state in real time.
 * Shows retries, confidence, and loop indicators.
 */

import { AGENT_ORDER, AGENT_LABELS, AGENT_ICONS } from '../../store/useAgentStore'
import clsx from 'clsx'

const STATUS_STYLES = {
  idle:     { dot: 'bg-gray-600',     label: 'text-gray-500',   badge: null },
  running:  { dot: 'bg-indigo-500 animate-pulse', label: 'text-indigo-400 font-medium', badge: 'bg-indigo-500/20 text-indigo-300' },
  complete: { dot: 'bg-emerald-500',  label: 'text-emerald-400 font-medium', badge: 'bg-emerald-500/20 text-emerald-300' },
  retrying: { dot: 'bg-amber-500 animate-pulse',  label: 'text-amber-400 font-medium', badge: 'bg-amber-500/20 text-amber-300' },
  error:    { dot: 'bg-red-500',      label: 'text-red-400',    badge: 'bg-red-500/20 text-red-300' },
}

const STATUS_LABELS = {
  idle:     'Waiting',
  running:  'Running…',
  complete: 'Complete',
  retrying: 'Retrying…',
  error:    'Error',
}

function AgentRow({ name, state, isLast }) {
  const styles     = STATUS_STYLES[state.status] || STATUS_STYLES.idle
  const isActive   = state.status === 'running' || state.status === 'retrying'
  const isComplete = state.status === 'complete'
  const hasPayload = isComplete && state.payload

  return (
    <div className="flex gap-3">
      {/* Timeline line + dot */}
      <div className="flex flex-col items-center">
        <div className={clsx(
          'w-3 h-3 rounded-full mt-1 flex-shrink-0 transition-all duration-500',
          styles.dot
        )} />
        {!isLast && (
          <div className={clsx(
            'w-px flex-1 mt-1 transition-colors duration-500',
            isComplete ? 'bg-emerald-700' : 'bg-surface-border'
          )} />
        )}
      </div>

      {/* Content */}
      <div className={clsx(
        'pb-5 flex-1 min-w-0',
        isLast ? '' : ''
      )}>
        {/* Header */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-base">{AGENT_ICONS[name]}</span>
          <span className={clsx('text-sm', styles.label)}>
            {AGENT_LABELS[name]}
          </span>
          {styles.badge && (
            <span className={clsx('badge text-xs', styles.badge)}>
              {isActive && (
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-current animate-pulse mr-1" />
              )}
              {STATUS_LABELS[state.status]}
            </span>
          )}
          {state.retries > 0 && (
            <span className="badge bg-amber-500/10 text-amber-400 text-xs">
              ↺ retry {state.retries}
            </span>
          )}
          {isComplete && state.duration && (
            <span className="text-xs text-gray-600 ml-auto">
              {state.duration}s
            </span>
          )}
        </div>

        {/* Payload summary */}
        {hasPayload && (
          <div className="mt-1.5 text-xs text-gray-500 space-y-0.5 pl-0.5">
            <PayloadSummary name={name} payload={state.payload} />
          </div>
        )}

        {/* Retry reason */}
        {state.status === 'retrying' && state.payload?.issues?.length > 0 && (
          <div className="mt-1 text-xs text-amber-500/70">
            Issues: {state.payload.issues.slice(0, 2).join(', ')}
          </div>
        )}
      </div>
    </div>
  )
}

function PayloadSummary({ name, payload }) {
  if (!payload) return null

  const items = []

  if (name === 'market_agent') {
    if (payload.score != null)     items.push(`Score: ${payload.score}/100`)
    if (payload.go_signal)         items.push(payload.go_signal)
    if (payload.confidence != null) items.push(`Conf: ${(payload.confidence * 100).toFixed(0)}%`)
  }
  if (name === 'financial_agent') {
    if (payload.roi != null)           items.push(`ROI: ${payload.roi}%`)
    if (payload.irr != null)           items.push(`IRR: ${payload.irr}%`)
    if (payload.attractiveness)        items.push(payload.attractiveness)
  }
  if (name === 'knowledge_agent') {
    if (payload.strategic_fit)         items.push(`Fit: ${payload.strategic_fit}`)
    if (payload.has_experience != null) items.push(payload.has_experience ? 'Has experience' : 'No prior experience')
  }
  if (name === 'strategy_agent') {
    if (payload.decision)              items.push(payload.decision)
    if (payload.score != null)         items.push(`${payload.score}/100`)
  }
  if (name === 'communication_agent') {
    if (payload.chars)                 items.push(`${payload.chars} chars`)
    if (payload.decision)              items.push(payload.decision)
  }
  if (name === 'supervisor') {
    if (payload.product)               items.push(payload.product?.substring(0, 30))
  }

  return items.length > 0 ? (
    <div className="flex flex-wrap gap-2">
      {items.map((item, i) => (
        <span key={i} className="text-gray-400">{item}</span>
      ))}
    </div>
  ) : null
}

export default function AgentTimeline({ agents }) {
  const hasActivity = Object.values(agents).some(a => a.status !== 'idle')

  if (!hasActivity) return null

  return (
    <div className="card p-4 animate-fade-in">
      <div className="text-xs text-gray-500 uppercase tracking-widest font-semibold mb-4">
        Agent Pipeline
      </div>
      <div className="space-y-0">
        {AGENT_ORDER.map((name, i) => (
          <AgentRow
            key={name}
            name={name}
            state={agents[name]}
            isLast={i === AGENT_ORDER.length - 1}
          />
        ))}
      </div>
    </div>
  )
}
