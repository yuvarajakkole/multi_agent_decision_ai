/**
 * src/components/ui/Header.jsx
 */

import clsx from 'clsx'

export function Header({ wsConnected }) {
  return (
    <header className="border-b border-surface-border bg-surface-card/80 backdrop-blur-sm px-6 py-3 flex items-center justify-between flex-shrink-0">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-lg">
          ⚡
        </div>
        <div>
          <h1 className="text-sm font-bold text-white tracking-tight">
            RA Agent System
          </h1>
          <p className="text-xs text-gray-500">
            Multi-Agent Decision Intelligence
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* WS status */}
        <div className="flex items-center gap-1.5">
          <div className={clsx(
            'w-2 h-2 rounded-full',
            wsConnected ? 'bg-emerald-500 animate-pulse' : 'bg-gray-600'
          )} />
          <span className="text-xs text-gray-500">
            {wsConnected ? 'Live' : 'HTTP'}
          </span>
        </div>

        <div className="text-xs text-gray-600 border border-surface-border rounded px-2 py-0.5">
          v3.0
        </div>
      </div>
    </header>
  )
}

export function ErrorBanner({ error, onDismiss }) {
  if (!error) return null
  return (
    <div className="mx-4 mt-3 p-3 bg-red-950/60 border border-red-800 rounded-lg flex items-center justify-between animate-fade-in">
      <div className="flex items-center gap-2 text-sm text-red-300">
        <span>⚠️</span>
        <span>{error}</span>
      </div>
      <button onClick={onDismiss}
        className="text-red-400 hover:text-red-200 text-lg leading-none ml-3">
        ×
      </button>
    </div>
  )
}
