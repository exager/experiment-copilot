import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { RefreshCw, Trophy, Users, BarChart3, TrendingUp, Target, StopCircle, FileText } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import detail from '../mocks/experimentDetail.json'

export default function LiveDashboardPage() {
  const navigate = useNavigate()
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(0)
  const data = detail

  // Simulate auto-refresh polling
  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(() => {
      setLastUpdated(0)
      // TODO: Replace with real API call
    }, 5000)
    const ticker = setInterval(() => {
      setLastUpdated((prev) => prev + 1)
    }, 1000)
    return () => { clearInterval(interval); clearInterval(ticker) }
  }, [autoRefresh])

  const progress = (data.days_running / data.duration_days) * 100

  return (
    <div className="p-6 lg:p-8 min-h-full">
      {/* Header Row */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Live Experiment Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">Monitor experiment performance in real-time</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Last updated */}
          <span className="text-xs text-gray-400">Updated {lastUpdated}s ago</span>
          {/* Auto-refresh toggle */}
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

      {/* Experiment Info Bar with Progress */}
      <div className="bg-white rounded-2xl border border-gray-100 p-4 mb-6 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse ring-4 ring-green-100" />
            <h2 className="font-semibold text-gray-900 text-lg">{data.name}</h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-green-100 text-green-700 border border-green-200 uppercase">
              Running
            </span>
          </div>
          <div className="text-sm text-gray-500">Started: {data.started_at}</div>
        </div>
        {/* Progress bar */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-500">Day {data.days_running} of {data.duration_days}</span>
            <span className="text-xs text-gray-500">{Math.round(progress)}% complete</span>
          </div>
          <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        <KPICard
          label="Control Conversion"
          value={`${data.stats.control_conversion}%`}
          icon={<BarChart3 className="w-5 h-5 text-blue-600" />}
          iconBg="bg-blue-100"
        />
        <KPICard
          label="Variant Conversion"
          value={`${data.stats.variant_conversion}%`}
          subValue={`↑ ${data.stats.lift}%`}
          subColor="text-green-600"
          icon={<TrendingUp className="w-5 h-5 text-green-600" />}
          iconBg="bg-green-100"
        />
        <KPICard
          label="Confidence"
          value={`${data.stats.confidence}%`}
          icon={<Target className="w-5 h-5 text-purple-600" />}
          iconBg="bg-purple-100"
          highlight={data.stats.confidence >= 95}
        />
        <KPICard
          label="Winner"
          value={data.stats.winner}
          subValue={`• ${data.stats.winner_status}`}
          subColor="text-green-600"
          icon={<Trophy className="w-5 h-5 text-amber-600" />}
          iconBg="bg-amber-100"
        />
        <KPICard
          label="Users (Total)"
          value={`${(data.stats.users_control + data.stats.users_variant).toLocaleString()}`}
          subValue={`C: ${data.stats.users_control.toLocaleString()} | V: ${data.stats.users_variant.toLocaleString()}`}
          icon={<Users className="w-5 h-5 text-indigo-600" />}
          iconBg="bg-indigo-100"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Conversion Rate Over Time */}
        <div className="col-span-1 bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
          <h3 className="font-semibold text-gray-900 text-sm mb-4">Conversion Rate Over Time (%)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={data.charts.conversion_over_time}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} domain={['dataMin - 0.5', 'dataMax + 0.5']} />
              <Line type="monotone" dataKey="control" stroke="#3B82F6" strokeWidth={2} dot={false} name="Control" />
              <Line type="monotone" dataKey="variant" stroke="#10B981" strokeWidth={2} dot={false} name="Variant" />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex items-center justify-center gap-4 mt-2">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-blue-500" />
              <span className="text-xs text-gray-600">Control</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-xs text-gray-600">Variant</span>
            </div>
          </div>
        </div>

        {/* Revenue per User */}
        <div className="col-span-1 bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
          <h3 className="font-semibold text-gray-900 text-sm mb-4">Revenue per User (₹)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={data.charts.revenue_per_user}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Line type="monotone" dataKey="control" stroke="#3B82F6" strokeWidth={2} dot={false} name="Control" />
              <Line type="monotone" dataKey="variant" stroke="#10B981" strokeWidth={2} dot={false} name="Variant" />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex items-center justify-center gap-4 mt-2">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-blue-500" />
              <span className="text-xs text-gray-600">Control</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-xs text-gray-600">Variant</span>
            </div>
          </div>
        </div>

        {/* Traffic Split Pie */}
        <div className="col-span-1 bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
          <h3 className="font-semibold text-gray-900 text-sm mb-4">Traffic Split (%)</h3>
          <div className="flex items-center justify-center gap-6">
            <ResponsiveContainer width={140} height={140}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Control', value: data.charts.traffic_split.control },
                    { name: 'Variant', value: data.charts.traffic_split.variant },
                  ]}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={65}
                  dataKey="value"
                  strokeWidth={2}
                >
                  <Cell fill="#3B82F6" />
                  <Cell fill="#10B981" />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-blue-500" />
                <span className="text-sm text-gray-700">Control</span>
                <span className="text-sm font-bold text-gray-900">{data.charts.traffic_split.control}%</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-green-500" />
                <span className="text-sm text-gray-700">Variant</span>
                <span className="text-sm font-bold text-gray-900">{data.charts.traffic_split.variant}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics Summary Table */}
      <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm mb-6">
        <h3 className="font-semibold text-gray-900 mb-4">Key Metrics Summary</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-3 px-3 text-gray-500 font-medium text-xs uppercase tracking-wider">Metric</th>
                <th className="text-left py-3 px-3 text-gray-500 font-medium text-xs uppercase tracking-wider">Control</th>
                <th className="text-left py-3 px-3 text-gray-500 font-medium text-xs uppercase tracking-wider">Variant</th>
                <th className="text-left py-3 px-3 text-gray-500 font-medium text-xs uppercase tracking-wider">Uplift</th>
                <th className="text-left py-3 px-3 text-gray-500 font-medium text-xs uppercase tracking-wider">p-value</th>
                <th className="text-left py-3 px-3 text-gray-500 font-medium text-xs uppercase tracking-wider">Significance</th>
              </tr>
            </thead>
            <tbody>
              {data.key_metrics.map((row, index) => (
                <tr key={row.metric} className={`border-b border-gray-50 hover:bg-purple-50/30 transition-colors ${index % 2 === 1 ? 'bg-gray-50/50' : ''}`}>
                  <td className="py-3.5 px-3 font-medium text-gray-900">{row.metric}</td>
                  <td className="py-3.5 px-3 text-gray-700">{row.control}</td>
                  <td className="py-3.5 px-3 text-gray-700 font-medium">{row.variant}</td>
                  <td className={`py-3.5 px-3 font-bold ${row.uplift.includes('+') || row.uplift.includes('↓') ? 'text-green-600' : 'text-red-500'}`}>
                    {row.uplift}
                  </td>
                  <td className="py-3.5 px-3 text-gray-600 font-mono text-xs">{row.p_value}</td>
                  <td className="py-3.5 px-3">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${
                      row.significance === 'Significant'
                        ? 'bg-green-100 text-green-700 border border-green-200'
                        : 'bg-gray-100 text-gray-500 border border-gray-200'
                    }`}>
                      {row.significance === 'Significant' && <span className="w-1.5 h-1.5 rounded-full bg-green-500" />}
                      {row.significance}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between bg-white rounded-2xl border border-gray-100 p-4 shadow-sm">
        <button
          onClick={() => navigate('/running')}
          className="text-sm text-gray-600 hover:text-gray-900 border border-gray-200 px-4 py-2 rounded-xl hover:bg-gray-50 transition-colors"
        >
          ← Back to Experiments
        </button>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 border border-red-200 text-red-600 hover:bg-red-50 px-4 py-2 rounded-xl text-sm font-medium transition-colors">
            <StopCircle className="w-4 h-4" />
            Stop Experiment
          </button>
          <button
            onClick={() => navigate(`/experiments/${data.id}/report`)}
            className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white px-5 py-2 rounded-xl text-sm font-medium transition-all hover:scale-[1.02]"
          >
            <FileText className="w-4 h-4" />
            View Report
          </button>
        </div>
      </div>
    </div>
  )
}

// ============ KPI Card Component ============

function KPICard({ label, value, subValue, subColor, icon, iconBg, highlight }: {
  label: string
  value: string
  subValue?: string
  subColor?: string
  icon: React.ReactNode
  iconBg: string
  highlight?: boolean
}) {
  return (
    <div className={`bg-white rounded-2xl border p-4 shadow-sm transition-shadow hover:shadow-md ${highlight ? 'border-green-200 ring-1 ring-green-100' : 'border-gray-100'}`}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-[11px] text-gray-500 uppercase tracking-wider font-medium">{label}</p>
        <div className={`w-9 h-9 rounded-lg ${iconBg} flex items-center justify-center`}>
          {icon}
        </div>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      {subValue && (
        <p className={`text-xs mt-1 font-medium ${subColor || 'text-gray-500'}`}>{subValue}</p>
      )}
    </div>
  )
}
