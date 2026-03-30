/**
 * src/components/decision/DecisionCard.jsx
 *
 * The prominent decision result card shown when analysis completes.
 * Shows: decision badge, score bar, confidence, rationale, risks, next steps.
 */

import clsx from 'clsx'

const DECISION_CONFIG = {
  GO: {
    icon:       '✅',
    label:      'GO',
    desc:       'Proceed with expansion',
    bg:         'bg-emerald-950/60',
    border:     'border-emerald-700',
    badge:      'bg-emerald-500 text-white',
    bar:        'bg-emerald-500',
    text:       'text-emerald-400',
  },
  GO_WITH_CONDITIONS: {
    icon:       '⚠️',
    label:      'GO WITH CONDITIONS',
    desc:       'Proceed — specific requirements must be met first',
    bg:         'bg-amber-950/40',
    border:     'border-amber-700',
    badge:      'bg-amber-500 text-white',
    bar:        'bg-amber-500',
    text:       'text-amber-400',
  },
  WAIT: {
    icon:       '⏳',
    label:      'WAIT',
    desc:       'Hold — specific blockers must be resolved',
    bg:         'bg-orange-950/40',
    border:     'border-orange-800',
    badge:      'bg-orange-600 text-white',
    bar:        'bg-orange-500',
    text:       'text-orange-400',
  },
  NO_GO: {
    icon:       '🚫',
    label:      'NO GO',
    desc:       'Do not proceed — fundamental mismatch',
    bg:         'bg-red-950/40',
    border:     'border-red-800',
    badge:      'bg-red-600 text-white',
    bar:        'bg-red-500',
    text:       'text-red-400',
  },
}

function ScoreBar({ label, value, max, color }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-400">{label}</span>
        <span className="text-gray-300 font-mono">{value?.toFixed(1) ?? '—'}/{max}</span>
      </div>
      <div className="h-1.5 bg-surface-border rounded-full overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all duration-700', color)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

function ConfidenceChip({ confidence, label }) {
  const pct = Math.round((confidence || 0) * 100)
  const cls = pct >= 80 ? 'text-emerald-400' : pct >= 60 ? 'text-amber-400' : 'text-red-400'
  return (
    <span className={clsx('text-sm font-semibold', cls)}>
      {label || (pct >= 80 ? 'High' : pct >= 60 ? 'Medium' : 'Low')} confidence ({pct}%)
    </span>
  )
}

export default function DecisionCard({ decision, confidence }) {
  if (!decision?.decision) return null

  const cfg   = DECISION_CONFIG[decision.decision] || DECISION_CONFIG.WAIT
  const score = decision.adjusted_score ?? decision.total_score ?? 0
  const mc    = decision.market_component
  const fc    = decision.financial_component
  const sc    = decision.strategic_component

  return (
    <div className={clsx(
      'border rounded-xl p-5 animate-slide-up',
      cfg.bg, cfg.border
    )}>
      {/* Header */}
      <div className="flex items-start gap-4 mb-4">
        <span className="text-3xl">{cfg.icon}</span>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <span className={clsx('badge text-sm px-3 py-1', cfg.badge)}>
              {cfg.label}
            </span>
            <ConfidenceChip
              confidence={confidence?.weighted_confidence}
              label={confidence?.label}
            />
          </div>
          <p className="text-gray-400 text-sm mt-1">{cfg.desc}</p>
        </div>
        {/* Total score */}
        <div className="text-right flex-shrink-0">
          <div className={clsx('text-4xl font-bold font-mono', cfg.text)}>
            {score.toFixed(0)}
          </div>
          <div className="text-xs text-gray-500">/ 100</div>
        </div>
      </div>

      {/* Score breakdown bars */}
      {(mc != null || fc != null || sc != null) && (
        <div className="space-y-2 mb-4 p-3 bg-black/20 rounded-lg">
          <div className="text-xs text-gray-500 font-semibold mb-2">Score Breakdown</div>
          <ScoreBar label="Market Analysis"   value={mc} max={40} color={cfg.bar} />
          <ScoreBar label="Financial Case"    value={fc} max={40} color={cfg.bar} />
          <ScoreBar label="Strategic Fit"     value={sc} max={20} color={cfg.bar} />
        </div>
      )}

      {/* Summary */}
      {decision.summary && (
        <p className="text-gray-300 text-sm mb-4 leading-relaxed border-l-2 border-surface-border pl-3">
          {decision.summary}
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Rationale */}
        {decision.rationale?.length > 0 && (
          <div>
            <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold mb-2">
              Key Evidence
            </div>
            <ul className="space-y-1.5">
              {decision.rationale.slice(0, 4).map((r, i) => (
                <li key={i} className="text-sm text-gray-300 flex gap-2">
                  <span className="text-indigo-400 mt-0.5 flex-shrink-0">▸</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Risks */}
        {decision.key_risks?.length > 0 && (
          <div>
            <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold mb-2">
              Key Risks
            </div>
            <ul className="space-y-1.5">
              {decision.key_risks.slice(0, 4).map((r, i) => (
                <li key={i} className="text-sm text-gray-300 flex gap-2">
                  <span className="text-red-400 mt-0.5 flex-shrink-0">⚠</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Conditions */}
      {decision.conditions?.length > 0 && (
        <div className="mt-4 p-3 bg-amber-900/20 border border-amber-800/50 rounded-lg">
          <div className="text-xs text-amber-400 font-semibold mb-2">
            CONDITIONS REQUIRED
          </div>
          <ul className="space-y-1">
            {decision.conditions.map((c, i) => (
              <li key={i} className="text-sm text-amber-200/80 flex gap-2">
                <span className="flex-shrink-0">{i + 1}.</span>
                <span>{c}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Blocking issues */}
      {decision.blocking_issues?.length > 0 && (
        <div className="mt-4 p-3 bg-red-900/20 border border-red-800/50 rounded-lg">
          <div className="text-xs text-red-400 font-semibold mb-2">
            BLOCKING ISSUES
          </div>
          <ul className="space-y-1">
            {decision.blocking_issues.map((b, i) => (
              <li key={i} className="text-sm text-red-200/80 flex gap-2">
                <span className="flex-shrink-0">🚫</span>
                <span>{b}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Next steps */}
      {decision.next_steps?.length > 0 && (
        <div className="mt-4">
          <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold mb-2">
            Next Steps
          </div>
          <ol className="space-y-1.5">
            {decision.next_steps.slice(0, 5).map((s, i) => (
              <li key={i} className="text-sm text-gray-300 flex gap-2">
                <span className={clsx('font-mono text-xs mt-0.5 flex-shrink-0 font-bold', cfg.text)}>
                  {i + 1}.
                </span>
                <span>{s}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}
