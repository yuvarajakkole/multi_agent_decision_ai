/**
 * src/components/ui/WelcomeScreen.jsx
 */

export default function WelcomeScreen() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center text-center px-6 py-12">
      <div className="text-6xl mb-4">⚡</div>
      <h2 className="text-2xl font-bold text-white mb-3">
        RA Agent System
      </h2>
      <p className="text-gray-400 max-w-lg mb-8 leading-relaxed">
        A multi-agent AI system that analyses business expansion decisions.
        Five specialised agents work in parallel — researching markets,
        modelling financials, assessing company fit — then synthesise an
        honest, evidence-based recommendation.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-2xl w-full mb-8">
        {[
          { icon: '🌍', title: 'Market Research',    desc: 'Live GDP, inflation, competition data' },
          { icon: '💰', title: 'Financial Modelling', desc: 'Real ROI/IRR from World Bank rates' },
          { icon: '🏢', title: 'Company Intelligence', desc: 'Matches RA Groups internal policy' },
          { icon: '⚡', title: 'Strategy Decision',   desc: 'Strict rubric — GO/WAIT/NO_GO' },
          { icon: '↺',  title: 'Quality Loops',       desc: 'Agents retry if data is poor' },
          { icon: '📝', title: 'Natural Language',    desc: 'Plain English executive report' },
        ].map(f => (
          <div key={f.title}
            className="card p-4 text-left">
            <div className="text-2xl mb-2">{f.icon}</div>
            <div className="text-sm font-semibold text-gray-200 mb-1">{f.title}</div>
            <div className="text-xs text-gray-500">{f.desc}</div>
          </div>
        ))}
      </div>

      <p className="text-xs text-gray-600">
        Type a question below — or click an example query to get started
      </p>
    </div>
  )
}
