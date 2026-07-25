import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Download, Share2, CheckCircle2, ArrowUpRight, ChevronLeft, AlertTriangle } from 'lucide-react'
import { Area, AreaChart, ResponsiveContainer } from 'recharts'
import { generateReport } from '../services/api'

// Sparkline for visual
const sparklineData = [
  { v: 20 }, { v: 25 }, { v: 30 }, { v: 28 }, { v: 35 }, { v: 40 }, { v: 38 }, { v: 45 }, { v: 50 }, { v: 55 }, { v: 60 }, { v: 65 },
]

// ============ HELPERS ============

const formatDate = (dateStr: string | null | undefined): string => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const getRecommendationColor = (rec: string) => {
  switch (rec) {
    case 'scale': return { bg: 'bg-green-100 border-green-200', text: 'text-green-700', wrapper: 'border-green-200 from-white to-green-50/50' }
    case 'continue': return { bg: 'bg-yellow-100 border-yellow-200', text: 'text-yellow-700', wrapper: 'border-yellow-200 from-white to-yellow-50/50' }
    case 'stop': return { bg: 'bg-red-100 border-red-200', text: 'text-red-700', wrapper: 'border-red-200 from-white to-red-50/50' }
    case 'rollback': return { bg: 'bg-red-100 border-red-200', text: 'text-red-700', wrapper: 'border-red-200 from-white to-red-50/50' }
    default: return { bg: 'bg-gray-100 border-gray-200', text: 'text-gray-700', wrapper: 'border-gray-200 from-white to-gray-50/50' }
  }
}

const getWinnerColor = (winner: string) => {
  if (winner === 'variant') return 'text-green-700 bg-green-50 border-green-200'
  if (winner === 'control') return 'text-blue-700 bg-blue-50 border-blue-200'
  return 'text-yellow-700 bg-yellow-50 border-yellow-200'
}

// ============ MAIN PAGE ============

export default function ReportPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [reportData, setReportData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    generateReport(id)
      .then((res) => {
        setReportData(res.data)
        setError(null)
      })
      .catch((err) => {
        setError(err?.response?.data?.detail ?? err?.message ?? 'Failed to generate report')
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="p-6 lg:p-8 min-h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-6 h-6 border-2 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-600">Generating report...</p>
          <p className="text-xs text-gray-400 mt-1">AI is analyzing your experiment results</p>
        </div>
      </div>
    )
  }

  if (error || !reportData) {
    return (
      <div className="p-6 lg:p-8 min-h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 text-lg mb-4">{error ?? 'No report data available.'}</p>
          <button onClick={() => navigate(-1)} className="text-purple-600 hover:underline text-sm">← Go Back</button>
        </div>
      </div>
    )
  }

  const data = reportData
  const stats = data.details?.statistics ?? {}
  const sampleRatio = data.details?.sample_ratio ?? null
  const guardrailRegressed = data.details?.guardrail_regressed ?? false
  const recColors = getRecommendationColor(data.recommendation)

  const handleDownloadPDF = (): void => {
    window.print()
  }

  return (
    <div className="p-6 lg:p-8 min-h-full" id="report-content">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 print:hidden">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Executive Report</h1>
          <p className="text-sm text-gray-500 mt-0.5">AI-generated summary and recommendations</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleDownloadPDF}
            className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors"
          >
            <Download className="w-4 h-4" />
            Download PDF
          </button>
          <button className="flex items-center gap-2 border border-gray-200 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-xl text-sm font-medium transition-colors">
            <Share2 className="w-4 h-4" />
            Share
          </button>
        </div>
      </div>

      {/* Print Header (visible only in print) */}
      <div className="hidden print:block mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Executive Report — Experiment #{id}</h1>
        <p className="text-sm text-gray-500 mt-1">Generated: {formatDate(data.generated_at)}</p>
      </div>

      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.5fr_1fr] gap-6 mb-6">

        {/* Left: Statistics & Results */}
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h2 className="font-bold text-gray-900 text-lg mb-4">Summary</h2>
            <p className="text-sm text-gray-700 leading-relaxed">{data.summary}</p>
            <p className="text-xs text-gray-400 mt-3">Generated: {formatDate(data.generated_at)}</p>
          </div>

          {/* Statistics Grid */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h2 className="font-bold text-gray-900 text-lg mb-4">Statistical Results</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <StatCard label="Confidence" value={`${(stats.confidence * 100).toFixed(1)}%`} highlight={stats.is_significant} />
              <StatCard label="P-Value" value={stats.p_value?.toFixed(4)} highlight={stats.p_value < 0.05} />
              <StatCard label="Z-Score" value={stats.z_score?.toFixed(3)} />
              <StatCard label="Conversion Lift" value={`${(stats.conversion_lift * 100).toFixed(2)}%`} highlight={stats.conversion_lift > 0} />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <StatCard label="Control Rate" value={`${(stats.control_conversion_rate * 100).toFixed(2)}%`} />
              <StatCard label="Variant Rate" value={`${(stats.variant_conversion_rate * 100).toFixed(2)}%`} />
              <div className={`rounded-xl border p-3 text-center ${getWinnerColor(stats.winner)}`}>
                <p className="text-[10px] font-bold uppercase tracking-wider opacity-70">Winner</p>
                <p className="text-xl font-black mt-1 capitalize">{stats.winner}</p>
              </div>
            </div>

            {/* Significance indicator */}
            <div className={`mt-4 rounded-xl border p-3 flex items-center gap-2 ${stats.is_significant ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
              {stats.is_significant ? (
                <CheckCircle2 className="w-4 h-4 text-green-600" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-yellow-600" />
              )}
              <span className={`text-sm font-medium ${stats.is_significant ? 'text-green-700' : 'text-yellow-700'}`}>
                {stats.is_significant ? 'Results are statistically significant' : 'Results are NOT yet statistically significant'}
              </span>
            </div>
          </div>

          {/* Health Checks */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h2 className="font-bold text-gray-900 text-lg mb-4">Experiment Health</h2>
            <div className="grid grid-cols-2 gap-3">
              <div className={`rounded-xl border p-3 ${sampleRatio && sampleRatio > 0.9 ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Sample Ratio</p>
                <p className="text-lg font-bold text-gray-900 mt-1">{sampleRatio ? sampleRatio.toFixed(4) : 'N/A'}</p>
                <p className="text-[11px] text-gray-500 mt-0.5">{sampleRatio && sampleRatio > 0.9 ? 'Healthy (close to 1.0)' : 'Check for bias'}</p>
              </div>
              <div className={`rounded-xl border p-3 ${guardrailRegressed ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Guardrail Status</p>
                <p className={`text-lg font-bold mt-1 ${guardrailRegressed ? 'text-red-700' : 'text-green-700'}`}>
                  {guardrailRegressed ? 'Regressed ⚠️' : 'No Regression ✓'}
                </p>
                <p className="text-[11px] text-gray-500 mt-0.5">{guardrailRegressed ? 'Guardrail metrics degraded' : 'All guardrails healthy'}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Recommendation + Business Impact + Next Steps */}
        <div className="space-y-6">
          {/* AI Recommendation */}
          <div className={`bg-white rounded-2xl border p-6 shadow-sm bg-gradient-to-br ${recColors.wrapper}`}>
            <h2 className="font-bold text-gray-900 mb-4">AI Recommendation</h2>
            <div className={`mb-4 ${recColors.bg} border rounded-xl p-4 text-center`}>
              <span className={`text-3xl font-black uppercase tracking-wider ${recColors.text}`}>
                {data.recommendation}
              </span>
            </div>

            {/* Sparkline */}
            <div className="mt-2 mb-4">
              <ResponsiveContainer width="100%" height={60}>
                <AreaChart data={sparklineData}>
                  <defs>
                    <linearGradient id="sparkGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#8B5CF6" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#8B5CF6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area type="monotone" dataKey="v" stroke="#8B5CF6" strokeWidth={2} fill="url(#sparkGradient)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Business Impact */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h2 className="font-bold text-gray-900 mb-3">Business Impact</h2>
            {data.business_impact ? (
              <p className="text-sm text-gray-700 leading-relaxed">{data.business_impact}</p>
            ) : (
              <div className="bg-gray-50 rounded-xl p-4 border border-gray-100 text-center">
                <p className="text-sm text-gray-400 italic">Not yet determined — experiment needs more data</p>
              </div>
            )}
          </div>

          {/* Next Steps */}
          {data.next_steps && data.next_steps.length > 0 && (
            <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
              <h2 className="font-bold text-gray-900 mb-4">Next Steps</h2>
              <div className="space-y-3">
                {data.next_steps.map((step: string, i: number) => (
                  <div key={`step-${i}`} className="flex items-start gap-2.5">
                    <div className="w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-purple-700">{i + 1}</span>
                    </div>
                    <span className="text-sm text-gray-700 leading-relaxed">{step}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Key Takeaway */}
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-2xl border border-purple-100 p-6 mb-6">
        <h3 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
          <ArrowUpRight className="w-5 h-5 text-purple-600" />
          Key Takeaway
        </h3>
        <p className="text-sm text-gray-700 leading-relaxed">{data.summary}</p>
      </div>

      {/* Back Button */}
      <div className="flex items-center print:hidden">
        <button
          onClick={() => navigate(`/experiments/${id}`)}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 px-4 py-2 rounded-xl hover:bg-gray-50 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Experiment
        </button>
      </div>
    </div>
  )
}

// ============ STAT CARD ============

function StatCard({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={`rounded-xl border p-3 text-center ${highlight ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-100'}`}>
      <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">{label}</p>
      <p className={`text-lg font-bold mt-1 ${highlight ? 'text-green-700' : 'text-gray-900'}`}>{value}</p>
    </div>
  )
}
