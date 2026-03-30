/**
 * src/components/chat/QueryForm.jsx
 *
 * The main input form at the bottom of the chat.
 * Collects: query text, market, budget, timeline.
 * Shows example queries to help users get started.
 */

import { useState } from 'react'
import clsx from 'clsx'

const EXAMPLES = [
  { q: 'Should RA Groups expand SME lending into UAE?',         market: 'UAE',          budget: '2000000', timeline: '18' },
  { q: 'Can we open an AI lending platform in Nigeria?',        market: 'Nigeria',      budget: '500000',  timeline: '12' },
  { q: 'Is India a good market for invoice financing in 2025?', market: 'India',        budget: '1500000', timeline: '24' },
  { q: 'Should we launch retail lending in Singapore?',         market: 'Singapore',    budget: '3000000', timeline: '18' },
  { q: 'Opening a new branch in Africa — viable or not?',       market: 'Kenya',        budget: '200000',  timeline: '12' },
]

function InputField({ label, id, value, onChange, ...props }) {
  return (
    <div>
      <label htmlFor={id} className="block text-xs text-gray-500 mb-1 font-medium">
        {label}
      </label>
      <input
        id={id}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full bg-surface-card border border-surface-border rounded-lg px-3 py-2
                   text-gray-100 text-sm placeholder:text-gray-600
                   focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500
                   transition-colors"
        {...props}
      />
    </div>
  )
}

export default function QueryForm({ onSubmit, isProcessing }) {
  const [query,    setQuery]    = useState('')
  const [market,   setMarket]   = useState('')
  const [budget,   setBudget]   = useState('1000000')
  const [timeline, setTimeline] = useState('12')
  const [showAdvanced, setShowAdvanced] = useState(false)

  const fillExample = (ex) => {
    setQuery(ex.q)
    setMarket(ex.market)
    setBudget(ex.budget)
    setTimeline(ex.timeline)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!query.trim() || !market.trim() || isProcessing) return
    onSubmit({ query, market, budget, timeline })
  }

  const canSubmit = query.trim().length > 0 && market.trim().length > 0 && !isProcessing

  return (
    <div className="border-t border-surface-border bg-surface/80 backdrop-blur-sm p-4">
      {/* Example queries */}
      {!isProcessing && (
        <div className="mb-3">
          <div className="text-xs text-gray-600 mb-2">Example queries:</div>
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex, i) => (
              <button
                key={i}
                onClick={() => fillExample(ex)}
                className="text-xs text-indigo-400 hover:text-indigo-300 border border-indigo-900
                           hover:border-indigo-700 rounded-full px-3 py-1 transition-colors truncate
                           max-w-[200px]"
                title={ex.q}
              >
                {ex.q.length > 35 ? ex.q.substring(0, 35) + '…' : ex.q}
              </button>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        {/* Main query input */}
        <div>
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Ask a business decision question… e.g. Should RA Groups expand into UAE?"
            rows={2}
            className="w-full bg-surface-card border border-surface-border rounded-xl px-4 py-3
                       text-gray-100 text-sm placeholder:text-gray-600 resize-none
                       focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500
                       transition-colors"
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                if (canSubmit) handleSubmit(e)
              }
            }}
          />
        </div>

        {/* Inline market + submit */}
        <div className="flex gap-2">
          <input
            value={market}
            onChange={e => setMarket(e.target.value)}
            placeholder="Market / Country"
            className="flex-1 bg-surface-card border border-surface-border rounded-lg px-3 py-2
                       text-gray-100 text-sm placeholder:text-gray-600
                       focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500
                       transition-colors"
          />

          {/* Advanced toggle */}
          <button
            type="button"
            onClick={() => setShowAdvanced(v => !v)}
            className="px-3 py-2 text-gray-500 hover:text-gray-300 border border-surface-border
                       rounded-lg text-xs transition-colors"
            title="Budget & timeline"
          >
            ⚙
          </button>

          {/* Submit */}
          <button
            type="submit"
            disabled={!canSubmit}
            className={clsx(
              'btn-primary flex items-center gap-2 px-5',
              isProcessing && 'cursor-wait'
            )}
          >
            {isProcessing ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Analysing…</span>
              </>
            ) : (
              <>
                <span>Analyse</span>
                <span>→</span>
              </>
            )}
          </button>
        </div>

        {/* Advanced options */}
        {showAdvanced && (
          <div className="grid grid-cols-2 gap-3 pt-1 animate-fade-in">
            <InputField
              label="Budget (USD)"
              id="budget"
              value={budget}
              onChange={setBudget}
              type="number"
              placeholder="1000000"
              min="0"
            />
            <InputField
              label="Timeline (months)"
              id="timeline"
              value={timeline}
              onChange={setTimeline}
              type="number"
              placeholder="12"
              min="1"
              max="60"
            />
          </div>
        )}
      </form>

      <p className="text-xs text-gray-600 text-center mt-2">
        Press Enter to submit · Shift+Enter for new line · ⚙ for budget/timeline
      </p>
    </div>
  )
}
