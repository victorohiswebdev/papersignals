'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { ArrowLeft, FileText, AlertTriangle } from 'lucide-react'
import { ScoreGauge, SignalBar } from '../components'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface SignalData {
  score: number
  risk: string
  raw: Record<string, number>
}

interface AnalysisDetail {
  id: string
  filename: string
  word_count: number
  composite_score: number | null
  rf_score: number | null
  rf_class: number | null
  risk: string
  created_at: string
  signals?: Record<string, SignalData>
  recommendations?: string[]
}

function riskColor(risk: string): string {
  switch (risk) {
    case 'low': return 'text-green-600 bg-green-50 border-green-200'
    case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    case 'high': return 'text-red-600 bg-red-50 border-red-200'
    default: return 'text-gray-600 bg-gray-50 border-gray-200'
  }
}

function riskBadge(risk: string): string {
  switch (risk) {
    case 'low': return '✅ Low Risk'
    case 'medium': return '⚠️ Medium Risk'
    case 'high': return '🔴 High Risk'
    default: return 'N/A'
  }
}

export default function AnalysisDetail() {
  const params = useParams()
  const [data, setData] = useState<AnalysisDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const id = params?.id as string
    if (!id) return

    fetch(`${API}/api/analyze/${id}`)
      .then((r) => {
        if (!r.ok) throw new Error('Analysis not found')
        return r.json()
      })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [params?.id])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="text-center py-20">
        <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-600">{error || 'Not found'}</h2>
        <a href="/" className="text-primary-600 hover:underline mt-2 inline-block">&larr; Back to dashboard</a>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <a href="/" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="w-4 h-4" /> Back to dashboard
      </a>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-gray-400" />
          <div>
            <h1 className="font-semibold text-xl">{data.filename}</h1>
            <p className="text-sm text-gray-500">
              {data.word_count?.toLocaleString()} words &middot; {new Date(data.created_at).toLocaleString()}
            </p>
          </div>
        </div>
        <span className={`text-sm font-medium px-3 py-1.5 rounded-full border ${riskColor(data.risk)}`}>
          {riskBadge(data.risk)}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-6 flex flex-col items-center">
          <ScoreGauge score={data.composite_score ?? 50} label="Weighted Score" size="lg" />
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-6 flex flex-col items-center">
          <ScoreGauge score={data.rf_score ?? 50} label="RF Classifier" size="lg" />
          <span className="text-xs text-gray-400 mt-2">
            {data.rf_class === 1 ? '→ Human' : data.rf_class === 0 ? '→ AI' : ''}
          </span>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold text-gray-800 mb-4">Signal Analysis</h2>
        <div className="divide-y divide-gray-100">
          {data.signals && Object.entries(data.signals).map(([id, sig]) => (
            <SignalBar key={id} id={id} score={sig.score} risk={sig.risk} />
          ))}
        </div>
      </div>

      {data.recommendations && data.recommendations.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-800 mb-3">Recommendations</h2>
          <ul className="space-y-2">
            {data.recommendations.map((rec, i) => (
              <li key={i} className="text-sm text-gray-600">{rec}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
