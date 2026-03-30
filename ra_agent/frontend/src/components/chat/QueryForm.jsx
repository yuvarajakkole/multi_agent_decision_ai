/**
 * src/components/chat/QueryForm.jsx
 *
 * FIXED:
 * - Market field is optional — supervisor extracts it from query text
 * - Budget shows currency hint when non-USD detected
 * - Examples include advisory queries
 * - Enter submits even without market (supervisor handles extraction)
 */

import { useState, useEffect } from 'react'
import clsx from 'clsx'

const EXAMPLES = [
  { q: 'Should RA Groups expand SME lending into UAE?',                market: 'UAE',    budget: '2000000', timeline: '18' },
  { q: 'Can we launch an AI lending platform in Nigeria?',             market: 'Nigeria', budget: '500000', timeline: '12' },
  { q: 'Is India a good market for invoice financing in 2025?',        market: 'India',   budget: '1500000',timeline: '24' },
  { q: 'Should we expand semiconductor manufacturing in India?',       market: 'India',   budget: '5000000',timeline: '36' },
  { q: 'Opening a new branch in Kenya — viable or not?',               market: 'Kenya',   budget: '200000', timeline: '12' },
  { q: 'Which field should I open a startup in India?',                market: 'India',   budget: '1000000',timeline: '18' },
  { q: 'Give me ideas for investment in the UAE with $500k',           market: 'UAE',     budget: '500000', timeline: '12' },
]

// Detect currency in query text for display hint
const CURRENCY_HINTS = {
  rupee: '≈ $12 USD per ₹1000', rupees: '≈ $12 USD per ₹1000',
  rupes: '≈ $12 USD per ₹1000', inr: '₹ — will convert to USD',
  dirham: 'AED — will convert', aed: 'AED — will convert',
  riyal: 'SAR — will convert', sar: 'SAR — will convert',
}

function detectCurrencyHint(query, budget) {
  const q = query.toLowerCase()
  for (const [kw, hint] of Object.entries(CURRENCY_HINTS)) {
    if (q.includes(kw)) return hint
  }
  return null
}

function InputField({ label, id, value, onChange, hint, ...props }) {
  return (
    <div>
      <label htmlFor={id} className="block text-xs text-gray-500 mb-1 font-medium">
        {label}
      </label>
      <input
        id={id} value={value} onChange={e => onChange(e.target.value)}
        className="w-full bg-surface-card border border-surface-border rounded-lg px-3 py-2
                   text-gray-100 text-sm placeholder:text-gray-600
                   focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500
                   transition-colors"
        {...props}
      />
      {hint && <p className="text-xs text-amber-400 mt-1">{hint}</p>}
    </div>
  )
}

export default function QueryForm({ onSubmit, isProcessing }) {
  const [query,    setQuery]    = useState('')
  const [market,   setMarket]   = useState('')
  const [budget,   setBudget]   = useState('1000000')
  const [timeline, setTimeline] = useState('12')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [currencyHint, setCurrencyHint] = useState(null)

  // Detect currency and auto-extract market from query as user types
  useEffect(() => {
    setCurrencyHint(detectCurrencyHint(query, budget))
  }, [query])

  const fillExample = (ex) => {
    setQuery(ex.q); setMarket(ex.market)
    setBudget(ex.budget); setTimeline(ex.timeline)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!query.trim() || isProcessing) return
    // market is optional — supervisor extracts it from the query
    onSubmit({ query, market: market.trim(), budget, timeline })
  }

  const canSubmit = query.trim().length > 5 && !isProcessing

  return (
    <div className="border-t border-surface-border bg-surface/80 backdrop-blur-sm p-4">

      {/* Example queries */}
      {!isProcessing && (
        <div className="mb-3">
          <div className="text-xs text-gray-600 mb-2">Examples — click to use:</div>
          <div className="flex flex-wrap gap-1.5">
            {EXAMPLES.map((ex, i) => (
              <button key={i} onClick={() => fillExample(ex)}
                className="text-xs text-indigo-400 hover:text-indigo-300
                           border border-indigo-900/60 hover:border-indigo-700
                           rounded-full px-2.5 py-0.5 transition-colors truncate max-w-[220px]"
                title={ex.q}>
                {ex.q.length > 38 ? ex.q.slice(0, 38) + '…' : ex.q}
              </button>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-2">
        {/* Main query */}
        <textarea
          value={query} onChange={e => setQuery(e.target.value)}
          placeholder="Ask any business question… e.g. Should we expand lending into Nigeria? Or: Which startup field works best in India?"
          rows={2}
          className="w-full bg-surface-card border border-surface-border rounded-xl px-4 py-3
                     text-gray-100 text-sm placeholder:text-gray-600 resize-none
                     focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500
                     transition-colors"
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (canSubmit) handleSubmit(e) }}}
        />

        <div className="flex gap-2 items-start">
          {/* Market — optional */}
          <div className="flex-1">
            <input
              value={market} onChange={e => setMarket(e.target.value)}
              placeholder="Market / Country (optional — auto-detected from query)"
              className="w-full bg-surface-card border border-surface-border rounded-lg px-3 py-2
                         text-gray-100 text-sm placeholder:text-gray-500
                         focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
            />
          </div>

          <button type="button" onClick={() => setShowAdvanced(v => !v)}
            className="px-3 py-2 text-gray-500 hover:text-gray-300 border border-surface-border
                       rounded-lg text-xs transition-colors flex-shrink-0" title="Budget & timeline">
            ⚙
          </button>

          <button type="submit" disabled={!canSubmit}
            className={clsx('btn-primary flex items-center gap-2 px-5 flex-shrink-0',
              isProcessing && 'cursor-wait')}>
            {isProcessing ? (
              <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /><span>Working…</span></>
            ) : (
              <><span>Analyse</span><span>→</span></>
            )}
          </button>
        </div>

        {/* Advanced */}
        {showAdvanced && (
          <div className="grid grid-cols-2 gap-2 pt-1 animate-fade-in">
            <InputField
              label="Budget (any currency)" id="budget"
              value={budget} onChange={setBudget}
              type="number" placeholder="1000000" min="0"
              hint={currencyHint}
            />
            <InputField
              label="Timeline (months)" id="timeline"
              value={timeline} onChange={setTimeline}
              type="number" placeholder="12" min="1" max="60"
            />
          </div>
        )}
      </form>

      <p className="text-xs text-gray-600 text-center mt-2">
        Enter to submit · Market optional — extracted from query · Budget in any currency
      </p>
    </div>
  )
}
