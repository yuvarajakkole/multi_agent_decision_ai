/**
 * src/components/ui/LoopSummary.jsx
 * Shows how many retries happened in the graph — proof the loops work.
 */

import clsx from 'clsx'

export default function LoopSummary({ loopSummary }) {
  if (!loopSummary || loopSummary.total_attempts === 0) return null

  const retries = [
    { label: 'Market',    count: loopSummary.market_retries    || 0 },
    { label: 'Financial', count: loopSummary.financial_retries || 0 },
    { label: 'Knowledge', count: loopSummary.knowledge_retries || 0 },
    { label: 'Strategy',  count: loopSummary.strategy_retries  || 0 },
  ].filter(r => r.count > 1)  // >1 means at least one retry happened

  if (retries.length === 0) return null

  return (
    <div className="card px-4 py-3 border-amber-800/40 bg-amber-950/20 animate-fade-in">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-amber-400 text-xs font-semibold uppercase tracking-wide">
          ↺ Graph Loops
        </span>
        <span className="text-xs text-gray-500">
          Agents retried to improve data quality:
        </span>
        {retries.map(r => (
          <span key={r.label}
            className="badge bg-amber-500/15 text-amber-300 text-xs">
            {r.label}: {r.count - 1} retry
          </span>
        ))}
      </div>
    </div>
  )
}
