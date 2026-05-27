'use client'

// ── Shared Components ──────────────────────────────────────────────

export function ScoreGauge({ score, label, size = 'md' }: { score: number; label: string; size?: 'sm' | 'md' | 'lg' }) {
  const radius = size === 'lg' ? 64 : size === 'sm' ? 36 : 48
  const stroke = size === 'lg' ? 10 : size === 'sm' ? 6 : 8
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = score >= 70 ? '#22c55e' : score >= 40 ? '#eab308' : '#ef4444'

  return (
    <div className="flex flex-col items-center relative">
      <svg width={radius * 2 + 12} height={radius * 2 + 12} className="transform -rotate-90">
        <circle cx={radius + 6} cy={radius + 6} r={radius} fill="none" stroke="#e5e7eb" strokeWidth={stroke} />
        <circle cx={radius + 6} cy={radius + 6} r={radius} fill="none"
          stroke={color} strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          className="transition-all duration-700 ease-out" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`font-bold ${size === 'lg' ? 'text-3xl' : size === 'sm' ? 'text-lg' : 'text-2xl'}`}>
          {score.toFixed(0)}
        </span>
        <span className="text-xs text-gray-400">/100</span>
      </div>
      <span className="mt-1 text-xs font-medium text-gray-500">{label}</span>
    </div>
  )
}

const SIGNAL_META: Record<string, { label: string; icon: string }> = {
  burstiness: { label: 'Burstiness', icon: '📏' },
  transition_density: { label: 'Transitions', icon: '🔗' },
  lexical_diversity: { label: 'Lexical Diversity', icon: '📖' },
  vocabulary_fingerprint: { label: 'Vocab Fingerprint', icon: '🔤' },
  paragraph_uniformity: { label: 'Paragraph Uniformity', icon: '📐' },
  readability: { label: 'Readability', icon: '📊' },
  perplexity: { label: 'Perplexity', icon: '🎲' },
}

function riskColor(risk: string): string {
  switch (risk) {
    case 'low': return 'text-green-600 bg-green-50 border-green-200'
    case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    case 'high': return 'text-red-600 bg-red-50 border-red-200'
    default: return 'text-gray-600 bg-gray-50 border-gray-200'
  }
}

export function SignalBar({ id, score, risk }: { id: string; score: number; risk: string }) {
  const meta = SIGNAL_META[id] || { label: id, icon: '📊' }
  const barColor = score >= 70 ? '#22c55e' : score >= 40 ? '#eab308' : '#ef4444'

  return (
    <div className="flex items-center gap-3 py-2.5">
      <span className="text-lg w-8 text-center">{meta.icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-baseline mb-1">
          <span className="text-sm font-medium text-gray-700 truncate">{meta.label}</span>
          <span className="text-sm font-semibold ml-2">{score.toFixed(0)}</span>
        </div>
        <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
          <div className="h-full rounded-full transition-all duration-700 ease-out"
            style={{ width: `${score}%`, backgroundColor: barColor }} />
        </div>
      </div>
      <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${riskColor(risk)}`}>
        {risk}
      </span>
    </div>
  )
}
