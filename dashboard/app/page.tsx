'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Upload, FileText, RefreshCw, Clock, Trash2,
  AlertTriangle, CheckCircle, BarChart3, Activity,
} from 'lucide-react'

// ── Types ──────────────────────────────────────────────────────────

interface SignalData {
  score: number
  risk: string
  raw: Record<string, number>
  details?: Record<string, unknown>
}

interface AnalysisResult {
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

interface HistoryItem {
  id: string
  filename: string
  word_count: number
  composite_score: number | null
  rf_score: number | null
  risk: string
  created_at: string
}

// ── Constants ──────────────────────────────────────────────────────

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const SIGNAL_META: Record<string, { label: string; icon: string; color: string }> = {
  burstiness: { label: 'Burstiness', icon: '📏', color: '#3b82f6' },
  transition_density: { label: 'Transitions', icon: '🔗', color: '#8b5cf6' },
  lexical_diversity: { label: 'Lexical Diversity', icon: '📖', color: '#06b6d4' },
  vocabulary_fingerprint: { label: 'Vocab Fingerprint', icon: '🔤', color: '#f59e0b' },
  paragraph_uniformity: { label: 'Paragraph Uniformity', icon: '📐', color: '#10b981' },
  readability: { label: 'Readability', icon: '📊', color: '#ef4444' },
  perplexity: { label: 'Perplexity', icon: '🎲', color: '#6366f1' },
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
    default: return 'Unknown'
  }
}

// ── Score Gauge ────────────────────────────────────────────────────

function ScoreGauge({ score, label, size = 'md' }: { score: number; label: string; size?: 'sm' | 'md' | 'lg' }) {
  const radius = size === 'lg' ? 64 : size === 'sm' ? 36 : 48
  const stroke = size === 'lg' ? 10 : size === 'sm' ? 6 : 8
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = score >= 70 ? '#22c55e' : score >= 40 ? '#eab308' : '#ef4444'

  return (
    <div className="flex flex-col items-center">
      <svg width={radius * 2 + 12} height={radius * 2 + 12} className="transform -rotate-90">
        <circle cx={radius + 6} cy={radius + 6} r={radius} fill="none"
          stroke="#e5e7eb" strokeWidth={stroke} />
        <circle cx={radius + 6} cy={radius + 6} r={radius} fill="none"
          stroke={color} strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out" />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className={`font-bold ${size === 'lg' ? 'text-3xl' : size === 'sm' ? 'text-lg' : 'text-2xl'}`}>
          {score.toFixed(0)}
        </span>
        <span className="text-xs text-gray-500">/100</span>
      </div>
      <span className="mt-1 text-xs font-medium text-gray-500">{label}</span>
    </div>
  )
}

// ── Signal Bar ─────────────────────────────────────────────────────

function SignalBar({ id, score, risk }: { id: string; score: number; risk: string }) {
  const meta = SIGNAL_META[id] || { label: id, icon: '📊', color: '#6b7280' }
  const barColor = score >= 70 ? '#22c55e' : score >= 40 ? '#eab308' : '#ef4444'

  return (
    <div className="flex items-center gap-3 py-2">
      <span className="text-lg w-8 text-center">{meta.icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-baseline mb-1">
          <span className="text-sm font-medium text-gray-700 truncate">{meta.label}</span>
          <span className="text-sm font-semibold ml-2">{score.toFixed(0)}</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div className="h-full rounded-full transition-all duration-700 ease-out"
            style={{ width: `${score}%`, backgroundColor: barColor }} />
        </div>
      </div>
      <span className={`text-xs px-2 py-0.5 rounded-full border ${riskColor(risk)}`}>
        {risk}
      </span>
    </div>
  )
}

// ── Upload Zone ────────────────────────────────────────────────────

function UploadZone({ onResult }: { onResult: (r: AnalysisResult) => void }) {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback(async (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!ext || !['txt', 'md', 'docx'].includes(ext)) {
      setError('Unsupported format. Use .txt, .md, or .docx')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File too large (max 10MB)')
      return
    }

    setUploading(true)
    setError(null)

    const form = new FormData()
    form.append('file', file)

    try {
      const res = await fetch(`${API}/api/analyze`, { method: 'POST', body: form })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Server error: ${res.status}`)
      }
      const data: AnalysisResult = await res.json()
      onResult(data)
    } catch (e: any) {
      setError(e.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }, [onResult])

  return (
    <div
      className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer
        ${dragging ? 'border-primary-400 bg-primary-50 upload-active' : 'border-gray-200 hover:border-gray-300 bg-white'}
        ${uploading ? 'opacity-60 pointer-events-none' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f) }}
      onClick={() => inputRef.current?.click()}
    >
      <input ref={inputRef} type="file" accept=".txt,.md,.docx" hidden
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f) }} />

      {uploading ? (
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-10 h-10 text-primary-500 animate-spin" />
          <p className="text-gray-600 font-medium">Analyzing document...</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <Upload className="w-10 h-10 text-gray-400" />
          <div>
            <p className="text-gray-700 font-medium">Drop your document here</p>
            <p className="text-sm text-gray-400 mt-1">or click to browse — .txt, .md, .docx up to 10MB</p>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 text-sm text-red-600 bg-red-50 rounded-lg px-4 py-2 inline-flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" /> {error}
        </div>
      )}
    </div>
  )
}

// ── Results Panel ──────────────────────────────────────────────────

function ResultsPanel({ result }: { result: AnalysisResult }) {
  const [expandedSignal, setExpandedSignal] = useState<string | null>(null)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-gray-400" />
          <div>
            <h2 className="font-semibold text-lg">{result.filename}</h2>
            <p className="text-sm text-gray-500">
              {result.word_count?.toLocaleString()} words &middot;{' '}
              {new Date(result.created_at).toLocaleString()}
            </p>
          </div>
        </div>
        <span className={`text-sm font-medium px-3 py-1.5 rounded-full border ${riskColor(result.risk)}`}>
          {riskBadge(result.risk)}
        </span>
      </div>

      {/* Score Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-6 flex flex-col items-center relative">
          <ScoreGauge score={result.composite_score ?? 50} label="Weighted Score" size="lg" />
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-6 flex flex-col items-center relative">
          <ScoreGauge score={result.rf_score ?? 50} label="RF Classifier Score" size="lg" />
          <div className="mt-2 text-xs text-gray-400">
            {result.rf_class === 1 ? 'Classified: Human-like' : result.rf_class === 0 ? 'Classified: AI-like' : 'No RF model'}
          </div>
        </div>
      </div>

      {/* Signal Breakdown */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <BarChart3 className="w-4 h-4" /> Signal Breakdown
        </h3>
        <div className="divide-y divide-gray-100">
          {result.signals && Object.entries(result.signals).map(([id, sig]) => (
            <div key={id}>
              <div
                className="cursor-pointer"
                onClick={() => setExpandedSignal(expandedSignal === id ? null : id)}
              >
                <SignalBar id={id} score={sig.score} risk={sig.risk} />
              </div>
              {expandedSignal === id && (
                <div className="ml-11 mb-3 p-3 bg-gray-50 rounded-lg text-sm text-gray-600 space-y-1">
                  {sig.raw && Object.entries(sig.raw).slice(0, 5).map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-gray-500">{k.replace(/_/g, ' ')}</span>
                      <span className="font-mono font-medium">
                        {typeof v === 'number' ? v.toFixed(2) : String(v)}
                      </span>
                    </div>
                  ))}
                  {sig.details && Object.keys(sig.details).length > 0 && (
                    <p className="text-gray-400 italic mt-1">⚠️ Has flagged items — see CLI report</p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      {result.recommendations && result.recommendations.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4" /> Recommendations
          </h3>
          <ul className="space-y-2">
            {result.recommendations.map((rec, i) => (
              <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// ── History ────────────────────────────────────────────────────────

function History({ onSelect, currentId }: { onSelect: (id: string) => void; currentId?: string }) {
  const [items, setItems] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/analyses?limit=20`)
      const data = await res.json()
      setItems(data.analyses || [])
    } catch { /* ignore */ }
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  const handleDelete = async (id: string) => {
    try {
      await fetch(`${API}/api/analyze/${id}`, { method: 'DELETE' })
      setItems((prev) => prev.filter((i) => i.id !== id))
    } catch { /* ignore */ }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200">
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <h3 className="font-semibold text-sm text-gray-700 flex items-center gap-2">
          <Clock className="w-4 h-4" /> History
        </h3>
        <button onClick={load} className="text-gray-400 hover:text-gray-600 transition-colors">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>
      <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
        {items.length === 0 && !loading && (
          <p className="text-sm text-gray-400 text-center py-8">No analyses yet</p>
        )}
        {items.length === 0 && loading && (
          <p className="text-sm text-gray-400 text-center py-8">Loading...</p>
        )}
        {items.map((item) => (
          <div
            key={item.id}
            className={`px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors
              ${item.id === currentId ? 'bg-primary-50' : ''}`}
            onClick={() => onSelect(item.id)}
          >
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-gray-700 truncate">{item.filename}</p>
              <p className="text-xs text-gray-400">
                {new Date(item.created_at).toLocaleDateString()} &middot; {item.word_count} words
              </p>
            </div>
            <div className="flex items-center gap-2 ml-3">
              <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                (item.rf_score ?? 50) >= 70 ? 'text-green-700 bg-green-50' :
                (item.rf_score ?? 50) >= 40 ? 'text-yellow-700 bg-yellow-50' :
                'text-red-700 bg-red-50'
              }`}>
                {item.rf_score?.toFixed(0) ?? '—'}
              </span>
              <button
                onClick={(e) => { e.stopPropagation(); handleDelete(item.id) }}
                className="text-gray-300 hover:text-red-400 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main Dashboard Page ────────────────────────────────────────────

export default function Dashboard() {
  const [currentResult, setCurrentResult] = useState<AnalysisResult | null>(null)
  const [loadingHistory, setLoadingHistory] = useState<string | null>(null)

  const handleNewResult = (result: AnalysisResult) => {
    setCurrentResult(result)
  }

  const handleHistorySelect = async (id: string) => {
    setLoadingHistory(id)
    try {
      const res = await fetch(`${API}/api/analyze/${id}`)
      if (res.ok) {
        const data: AnalysisResult = await res.json()
        setCurrentResult(data)
      }
    } catch { /* ignore */ }
    setLoadingHistory(null)
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Main content */}
      <div className="lg:col-span-3 space-y-6">
        <UploadZone onResult={handleNewResult} />
        {currentResult && <ResultsPanel result={currentResult} />}
        {!currentResult && (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <div className="text-6xl mb-4">📄</div>
            <h2 className="text-xl font-semibold text-gray-600 mb-2">Upload a document to begin</h2>
            <p className="text-gray-400">
              Drop a .txt, .md, or .docx file above to analyze it for AI detection signals.
            </p>
          </div>
        )}
      </div>

      {/* Sidebar */}
      <div className="lg:col-span-1">
        <History onSelect={handleHistorySelect} currentId={currentResult?.id} />
      </div>
    </div>
  )
}
