/**
 * src/components/ui/ConfidencePanel.jsx
 * Shows per-agent confidence scores and weighted total.
 */

import clsx from 'clsx'

const AGENT_LABELS = {
  market_agent:    '🌍 Market',
  financial_agent: '💰 Financial',
  knowledge_agent: '🏢 Knowledge',
  strategy_agent:  '⚡ Strategy',
}

function ConfBar({ value }) {
  const pct  = Math.round((value || 0) * 100)
  const color = pct >= 80 ? 'bg-emerald-500'
              : pct >= 60 ? 'bg-amber-500'
              : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-surface-border rounded-full overflow-hidden">
        <div className={clsx('h-full rounded-full', color)}
          style={{ width: `${pct}%`, transition: 'width 0.6s ease' }} />
      </div>
      <span className="text-xs font-mono text-gray-400 w-8 text-right">{pct}%</span>
    </div>
  )
}

export default function ConfidencePanel({ confidence }) {
  if (!confidence) return null
  const wc  = confidence.weighted_confidence || 0
  const pct = Math.round(wc * 100)

  return (
    <div className="card p-4 animate-fade-in">
      <div className="text-xs text-gray-500 uppercase tracking-widest font-semibold mb-3">
        Confidence Report
      </div>

      {/* Weighted total */}
      <div className="flex items-center gap-3 mb-4 p-3 bg-black/20 rounded-lg">
        <div className={clsx(
          'text-3xl font-bold font-mono',
          pct >= 80 ? 'text-emerald-400' : pct >= 60 ? 'text-amber-400' : 'text-red-400'
        )}>
          {pct}%
        </div>
        <div>
          <div className="text-sm font-semibold text-gray-200">
            {confidence.label || 'Unknown'} Confidence
          </div>
          <div className="text-xs text-gray-500">Weighted across all agents</div>
        </div>
      </div>

      {/* Per-agent breakdown */}
      {confidence.per_agent && (
        <div className="space-y-2.5">
          {Object.entries(confidence.per_agent).map(([agent, data]) => (
            data && (
              <div key={agent}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400">{AGENT_LABELS[agent] || agent}</span>
                </div>
                <ConfBar value={data.confidence} />
              </div>
            )
          ))}
        </div>
      )}

      {/* Learning adjustment */}
      {confidence.learning_adjustment !== 0 && confidence.learning_adjustment != null && (
        <div className="mt-3 pt-3 border-t border-surface-border text-xs text-gray-500 flex justify-between">
          <span>Learning adjustment</span>
          <span className={confidence.learning_adjustment > 0 ? 'text-emerald-400' : 'text-red-400'}>
            {confidence.learning_adjustment > 0 ? '+' : ''}{Math.round(confidence.learning_adjustment * 100)}%
          </span>
        </div>
      )}
    </div>
  )
}
