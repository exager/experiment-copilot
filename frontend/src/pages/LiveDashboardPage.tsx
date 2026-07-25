import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useLocation, useParams } from 'react-router-dom'
import { RefreshCw, Trophy, Users, BarChart3, TrendingUp, Target, StopCircle, FileText, ChevronDown, ChevronUp } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { getExperimentDetail, getExperimentMetrics } from '../services/api'

// ============ HELPERS ============

const formatMetric = (id: string): string =>
  id.replaceAll('_', ' ').replaceAll(/\b\w/g, (c) => c.toUpperCase())

const formatDate = (dateStr: string | null | undefined): string => {
  if (!dateStr) return 'N/A'
  const d = new Date(dateStr)
  return d.toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// ============ MAIN PAGE ============

export default function LiveDashboardPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { id } = useParams()
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(0)

  // Experiment data — from navigation state OR fetched from API
  const [experimentData, setExperimentData] = useState<any>(
    (location.state as { launchData?: any })?.launchData ?? null,
  )
  const [loading, setLoading] = useState(!experimentData)
  const [error, setError] = useState<string | null>(null)

  // Metrics collapsible section
  const [metricsExpanded, setMetricsExpanded] = useState(false)
  const [metricsData, setMetricsData] = useState<any>(null)
  const [metricsLoading, setMetricsLoading] = useState(false)

  // Fetch experiment detail on mount (or refresh)
  useEffect(() => {
    if (!id) return
    if (experimentData) {
      setLoading(false)
      return
    }
    setLoading(true)
    getExperimentDetail(id)
      .then((res) => {
        setExperimentData(res.data)
        setError(null)
      })
      .catch((err) => {
        setError(err?.message ?? 'Failed to load experiment')
      })
      .finally(() => setLoading(false))
  }, [id]) // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch metrics when user expands the section
  const handleMetricsToggle = useCallback(() => {
    const newExpanded = !metricsExpanded
    setMetricsExpanded(newExpanded)

    if (newExpanded && !metricsData && id) {
      setMetricsLoading(true)
      getExperimentMetrics(id, 100)
        .then((res) => setMetricsData(res.data))
        .catch(() => {}) // NOSONAR - metrics are optional
        .finally(() => setMetricsLoading(false))
    }
  }, [metricsExpanded, metricsData, id])

  // Auto-refresh ticker
  useEffect(() => {
    if (!autoRefresh) return
    const ticker = setInterval(() => {
      setLastUpdated((prev) => prev + 1)
    }, 1000)
    return () => clearInterval(ticker)
  }, [autoRefresh])

  // Loading state
  if (loading) {
    return (
      <div className="p-6 lg:p-8 min-h-full flex items-center justify-center">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-600">Loading experiment...</span>
        </div>
      </div>
    )
  }

  // Error state
  if (error || !experimentData) {
    return (
      <div className="p-6 lg:p-8 min-h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 text-lg mb-4">{error ?? 'No experiment data available.'}</p>
          <button onClick={() => navigate('/create')} className="text-purple-600 hover:underline text-sm">
            ← Go to New Experiment
          </button>
        </div>
      </div>
    )
  }

  // Map experiment data
  const data = experimentData
  const experimentName = data?.hypothesis?.experiment_name ?? 'Experiment'
  const hypothesis = data?.hypothesis?.hypothesis ?? ''
  const experimentStatus = data?.status ?? 'running'
  const startedAt = formatDate(data?.started_at)
  const completedAt = data?.completed_at ? formatDate(data.completed_at) : null
  const durationDays = data?.configuration?.duration_days ?? 14
  const featureFlag = data?.configuration?.feature_flag ?? 'N/A'
  const audience = data?.configuration?.audience ?? 'all_users'
  const trafficSplit = data?.configuration?.traffic_split ?? { control: 0.5, variant: 0.5 }
  const controlPct = Math.round((trafficSplit.control ?? 0.5) * 100)
  const variantPct = Math.round((trafficSplit.variant ?? 0.5) * 100)
  const confidenceLevel = data?.configuration?.confidence_level
    ? `${Math.round(data.configuration.confidence_level * 100)}%`
    : 'N/A'
  const sampleSize = data?.configuration?.sample_size ?? 0
  const baselineRate = data?.configuration?.baseline_conversion_rate
    ? `${(data.configuration.baseline_conversion_rate * 100).toFixed(1)}%`
    : 'N/A'
  const expectedLift = data?.configuration?.expected_lift
    ? `${(data.configuration.expected_lift * 100).toFixed(1)}%`
    : 'N/A'
  const primaryMetric = data?.hypothesis?.primary_metric ?? 'N/A'
  const secondaryMetrics: string[] = data?.hypothesis?.secondary_metrics ?? []
  const guardrailMetrics: string[] = data?.hypothesis?.guardrail_metrics ?? []
  const trafficSplitOption = data?.configuration?.traffic_split_option ?? 'N/A'

  const daysRunning = data?.started_at
    ? Math.max(1, Math.ceil((Date.now() - new Date(data.started_at).getTime()) / (1000 * 60 * 60 * 24)))
    : 1
  const progress = Math.min((daysRunning / durationDays) * 100, 100)

  return (
    <div className="p-6 lg:p-8 min-h-full">
      {/* Header Row */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Live Experiment Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">Monitor experiment performance in real-time</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">Updated {lastUpdated}s ago</span>
          <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-xl px-3 py-2">
            <RefreshCw className={`w-3.5 h-3.5 text-gray-500 ${autoRefresh ? 'animate-spin' : ''}`} style={{ animationDuration: '3s' }} />
            <span className="text-xs text-gray-600">Auto-refresh</span>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`relative w-9 h-5 rounded-full transition-colors ${autoRefresh ? 'bg-green-500' : 'bg-gray-300'}`}
            >
              <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${autoRefresh ? 'translate-x-4' : 'translate-x-0.5'}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Experiment Info Bar */}
      <div className="bg-white rounded-2xl border border-gray-100 p-4 mb-6 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${experimentStatus === 'completed' ? 'bg-blue-500' : 'bg-green-500 animate-pulse'} ring-4 ${experimentStatus === 'completed' ? 'ring-blue-100' : 'ring-green-100'}`} />
            <h2 className="font-semibold text-gray-900 text-lg">{experimentName}</h2>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase border ${
              experimentStatus === 'completed'
                ? 'bg-blue-100 text-blue-700 border-blue-200'
                : 'bg-green-100 text-green-700 border-green-200'
            }`}>
              {experimentStatus}
            </span>
          </div>
          <div className="text-sm text-gray-500">Started: {startedAt}</div>
        </div>
        {hypothesis && (
          <p className="text-xs text-gray-500 italic mb-3 line-clamp-2">&ldquo;{hypothesis}&rdquo;</p>
        )}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-500">Day {daysRunning} of {durationDays}</span>
            <span className="text-xs text-gray-500">{Math.round(progress)}% complete</span>
          </div>
          <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full transition-all" style={{ width: `${progress}%` }} />
          </div>
        </div>
        {completedAt && <p className="text-xs text-gray-400 mt-2">Completed: {completedAt}</p>}
      </div>

      {/* Configuration KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <KPICard label="Feature Flag" value={featureFlag} icon={<BarChart3 className="w-5 h-5 text-blue-600" />} iconBg="bg-blue-100" />
        <KPICard label="Audience" value={formatMetric(audience)} icon={<Users className="w-5 h-5 text-indigo-600" />} iconBg="bg-indigo-100" />
        <KPICard label="Traffic Split" value={trafficSplitOption} icon={<TrendingUp className="w-5 h-5 text-green-600" />} iconBg="bg-green-100" />
        <KPICard label="Duration" value={`${durationDays} days`} icon={<Target className="w-5 h-5 text-purple-600" />} iconBg="bg-purple-100" />
        <KPICard label="Confidence" value={confidenceLevel} icon={<Trophy className="w-5 h-5 text-amber-600" />} iconBg="bg-amber-100" highlight />
        <KPICard label="Sample Size" value={sampleSize.toLocaleString()} subValue={`per arm: ${Math.round(sampleSize / 2).toLocaleString()}`} icon={<Users className="w-5 h-5 text-teal-600" />} iconBg="bg-teal-100" />
      </div>

      {/* Baseline + Traffic Split + Metrics Config */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
          <h3 className="font-semibold text-gray-900 text-sm mb-4">Baseline & Targets</h3>
          <div className="space-y-3">
            <div className="flex justify-between"><span className="text-sm text-gray-600">Baseline Conversion</span><span className="text-sm font-bold text-gray-900">{baselineRate}</span></div>
            <div className="flex justify-between"><span className="text-sm text-gray-600">Expected Lift</span><span className="text-sm font-bold text-green-600">{expectedLift}</span></div>
            <div className="flex justify-between"><span className="text-sm text-gray-600">Primary Metric</span><span className="text-sm font-bold text-purple-700">{formatMetric(primaryMetric)}</span></div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
          <h3 className="font-semibold text-gray-900 text-sm mb-4">Traffic Split (%)</h3>
          <div className="flex items-center justify-center gap-6">
            <ResponsiveContainer width={120} height={120}>
              <PieChart>
                <Pie data={[{ name: 'Control', value: controlPct }, { name: 'Variant', value: variantPct }]} cx="50%" cy="50%" innerRadius={35} outerRadius={55} dataKey="value" strokeWidth={2}>
                  <Cell fill="#3B82F6" />
                  <Cell fill="#10B981" />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-3">
              <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-blue-500" /><span className="text-sm text-gray-700">Control</span><span className="text-sm font-bold">{controlPct}%</span></div>
              <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-green-500" /><span className="text-sm text-gray-700">Variant</span><span className="text-sm font-bold">{variantPct}%</span></div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
          <h3 className="font-semibold text-gray-900 text-sm mb-4">Metrics Configuration</h3>
          <div className="space-y-3">
            <div>
              <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Primary</span>
              <div className="mt-1"><span className="px-2.5 py-1 bg-purple-50 border border-purple-200 text-purple-800 rounded-full text-xs font-semibold">{formatMetric(primaryMetric)}</span></div>
            </div>
            <div>
              <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Secondary</span>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {secondaryMetrics.map((m) => (<span key={m} className="px-2 py-0.5 bg-blue-50 border border-blue-200 text-blue-700 rounded-full text-[11px]">{formatMetric(m)}</span>))}
              </div>
            </div>
            <div>
              <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Guardrail</span>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {guardrailMetrics.map((m) => (<span key={m} className="px-2 py-0.5 bg-red-50 border border-red-200 text-red-700 rounded-full text-[11px]">{formatMetric(m)}</span>))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Collapsible Metrics & Charts Section */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm mb-6 overflow-hidden">
        <button
          type="button"
          onClick={handleMetricsToggle}
          className="w-full flex items-center justify-between p-5 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <span className="text-lg" aria-hidden="true">📊</span>
            <h3 className="font-semibold text-gray-900">Live Metrics & Charts</h3>
          </div>
          {metricsExpanded ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
        </button>

        {metricsExpanded && (
          <div className="px-5 pb-5 border-t border-gray-100">
            {metricsLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="w-5 h-5 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
                <span className="ml-3 text-gray-500 text-sm">Loading metrics...</span>
              </div>
            ) : metricsData ? (
              <MetricsContent data={metricsData} />
            ) : (
              <p className="py-8 text-center text-gray-400 text-sm">No metrics data available yet.</p>
            )}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between bg-white rounded-2xl border border-gray-100 p-4 shadow-sm">
        <button onClick={() => navigate('/running')} className="text-sm text-gray-600 hover:text-gray-900 border border-gray-200 px-4 py-2 rounded-xl hover:bg-gray-50 transition-colors">
          ← Back to Experiments
        </button>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 border border-red-200 text-red-600 hover:bg-red-50 px-4 py-2 rounded-xl text-sm font-medium transition-colors">
            <StopCircle className="w-4 h-4" />
            Stop Experiment
          </button>
          <button onClick={() => navigate(`/experiments/${id}/report`)} className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white px-5 py-2 rounded-xl text-sm font-medium transition-all hover:scale-[1.02]">
            <FileText className="w-4 h-4" />
            View Report
          </button>
        </div>
      </div>
    </div>
  )
}

// ============ METRICS CONTENT (Charts + Table) ============

function MetricsContent({ data }: { data: any }) {
  const series = data?.series ?? []
  const stats = data?.statistics ?? {}
  const latest = data?.latest ?? {}
  const recommendation = data?.recommendation ?? {}

  // Transform series for charts — use index-based labels for clarity
  const chartData = series.map((s: any, index: number) => {
    const controlRate = Number(((s.conversion_control / (s.users_control || 1)) * 100).toFixed(2))
    const variantRate = Number(((s.conversion_variant / (s.users_variant || 1)) * 100).toFixed(2))
    return {
      label: `T${index + 1}`,
      time: new Date(s.timestamp).toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      control: controlRate,
      variant: variantRate,
    }
  })

  const revenueData = series.map((s: any, index: number) => ({
    label: `T${index + 1}`,
    time: new Date(s.timestamp).toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    control: Math.round(s.revenue_control / (s.users_control || 1)),
    variant: Math.round(s.revenue_variant / (s.users_variant || 1)),
  }))

  // Calculate Y-axis domains with padding
  const allConversionValues = chartData.flatMap((d: any) => [d.control, d.variant])
  const convMin = Math.max(0, Math.floor(Math.min(...allConversionValues) * 10 - 1) / 10)
  const convMax = Math.ceil(Math.max(...allConversionValues) * 10 + 1) / 10

  const allRevenueValues = revenueData.flatMap((d: any) => [d.control, d.variant])
  const revMin = Math.max(0, Math.min(...allRevenueValues) - 50)
  const revMax = Math.max(...allRevenueValues) + 50

  return (
    <div className="pt-4 space-y-6">
      {/* Live Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <MiniStat label="Control Rate" value={`${((latest.conversion_control / (latest.users_control || 1)) * 100).toFixed(2)}%`} />
        <MiniStat label="Variant Rate" value={`${((latest.conversion_variant / (latest.users_variant || 1)) * 100).toFixed(2)}%`} />
        <MiniStat label="Confidence" value={`${((stats.confidence ?? 0) * 100).toFixed(1)}%`} highlight={stats.is_significant} />
        <MiniStat label="Winner" value={stats.winner ?? 'N/A'} />
        <MiniStat label="Total Users" value={((latest.users_control ?? 0) + (latest.users_variant ?? 0)).toLocaleString()} />
      </div>

      {/* Charts */}
      {chartData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Conversion Rate Chart */}
          <div className="bg-gray-50 rounded-xl p-4">
            <h4 className="text-sm font-semibold text-gray-800 mb-4">Conversion Rate Over Time (%)</h4>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  axisLine={{ stroke: '#d1d5db' }}
                  tickLine={false}
                />
                <YAxis
                  domain={[convMin, convMax]}
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  axisLine={{ stroke: '#d1d5db' }}
                  tickLine={false}
                  tickFormatter={(v) => `${v}%`}
                />
                <Line
                  type="monotone"
                  dataKey="control"
                  stroke="#3B82F6"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#3B82F6', strokeWidth: 0 }}
                  activeDot={{ r: 5, stroke: '#3B82F6', strokeWidth: 2, fill: '#fff' }}
                  name="Control"
                />
                <Line
                  type="monotone"
                  dataKey="variant"
                  stroke="#10B981"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#10B981', strokeWidth: 0 }}
                  activeDot={{ r: 5, stroke: '#10B981', strokeWidth: 2, fill: '#fff' }}
                  name="Variant"
                />
              </LineChart>
            </ResponsiveContainer>
            <ChartLegend />
          </div>

          {/* Revenue per User Chart */}
          <div className="bg-gray-50 rounded-xl p-4">
            <h4 className="text-sm font-semibold text-gray-800 mb-4">Revenue per User (₹)</h4>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={revenueData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  axisLine={{ stroke: '#d1d5db' }}
                  tickLine={false}
                />
                <YAxis
                  domain={[revMin, revMax]}
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  axisLine={{ stroke: '#d1d5db' }}
                  tickLine={false}
                  tickFormatter={(v) => `₹${v}`}
                />
                <Line
                  type="monotone"
                  dataKey="control"
                  stroke="#3B82F6"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#3B82F6', strokeWidth: 0 }}
                  activeDot={{ r: 5, stroke: '#3B82F6', strokeWidth: 2, fill: '#fff' }}
                  name="Control"
                />
                <Line
                  type="monotone"
                  dataKey="variant"
                  stroke="#10B981"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#10B981', strokeWidth: 0 }}
                  activeDot={{ r: 5, stroke: '#10B981', strokeWidth: 2, fill: '#fff' }}
                  name="Variant"
                />
              </LineChart>
            </ResponsiveContainer>
            <ChartLegend />
          </div>
        </div>
      )}

      {/* Lift & P-value summary */}
      {stats.conversion_lift !== undefined && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <MiniStat label="Conversion Lift" value={`${(stats.conversion_lift * 100).toFixed(1)}%`} highlight={stats.conversion_lift > 0} />
          <MiniStat label="P-Value" value={stats.p_value?.toFixed(4) ?? 'N/A'} highlight={stats.p_value < 0.05} />
          <MiniStat label="Z-Score" value={stats.z_score?.toFixed(3) ?? 'N/A'} />
          <MiniStat label="Significant" value={stats.is_significant ? 'Yes ✓' : 'Not yet'} highlight={stats.is_significant} />
        </div>
      )}

      {/* Recommendation */}
      {recommendation.recommendation && (
        <div className="bg-purple-50 border border-purple-100 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-bold text-purple-800">Recommendation: {recommendation.recommendation.toUpperCase()}</span>
            <span className="text-xs text-purple-600">({((recommendation.confidence ?? 0) * 100).toFixed(0)}% confidence)</span>
          </div>
          <p className="text-sm text-purple-700">{recommendation.rationale}</p>
        </div>
      )}
    </div>
  )
}

// ============ MINI STAT CARD ============

function MiniStat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={`rounded-xl border p-3 ${highlight ? 'border-green-200 bg-green-50' : 'border-gray-100 bg-gray-50'}`}>
      <p className="text-[10px] text-gray-500 uppercase tracking-wider font-medium">{label}</p>
      <p className={`text-lg font-bold ${highlight ? 'text-green-700' : 'text-gray-900'}`}>{value}</p>
    </div>
  )
}

// ============ CHART LEGEND ============

function ChartLegend() {
  return (
    <div className="flex items-center justify-center gap-4 mt-2">
      <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-blue-500" /><span className="text-xs text-gray-600">Control</span></div>
      <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-green-500" /><span className="text-xs text-gray-600">Variant</span></div>
    </div>
  )
}

// ============ KPI Card ============

function KPICard({ label, value, subValue, subColor, icon, iconBg, highlight }: {
  label: string; value: string; subValue?: string; subColor?: string; icon: React.ReactNode; iconBg: string; highlight?: boolean
}) {
  return (
    <div className={`bg-white rounded-2xl border p-4 shadow-sm transition-shadow hover:shadow-md ${highlight ? 'border-green-200 ring-1 ring-green-100' : 'border-gray-100'}`}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-[11px] text-gray-500 uppercase tracking-wider font-medium">{label}</p>
        <div className={`w-9 h-9 rounded-lg ${iconBg} flex items-center justify-center`}>{icon}</div>
      </div>
      <p className="text-lg font-bold text-gray-900 truncate" title={value}>{value}</p>
      {subValue && <p className={`text-xs mt-1 font-medium ${subColor ?? 'text-gray-500'}`}>{subValue}</p>}
    </div>
  )
}
