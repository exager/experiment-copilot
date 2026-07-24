import { useNavigate } from 'react-router-dom'
import { FlaskConical, Play, CheckCircle, TrendingUp, Clock, ChevronRight, PlusCircle } from 'lucide-react'
import runningExperiments from '../mocks/runningExperiments.json'
import completedExperiments from '../mocks/completedExperiments.json'

export default function DashboardPage() {
  const navigate = useNavigate()

  const totalExperiments = runningExperiments.length + completedExperiments.length
  const runningCount = runningExperiments.length
  const completedCount = completedExperiments.length
  const avgLift = [...runningExperiments, ...completedExperiments].reduce((sum, e) => sum + e.lift, 0) / totalExperiments

  return (
    <div className="p-6 lg:p-8 min-h-full">
      {/* Header + Quick Action */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <FlaskConical className="w-6 h-6 text-purple-600" />
            Dashboard
          </h1>
          <p className="text-sm text-gray-500 mt-1">Overview of all your experiments</p>
        </div>
        <button
          onClick={() => navigate('/create')}
          className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white px-5 py-2.5 rounded-xl font-medium text-sm transition-all hover:scale-[1.02] active:scale-95 shadow-lg shadow-purple-200"
        >
          <PlusCircle className="w-4 h-4" />
          New Experiment
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Total Experiments"
          value={totalExperiments}
          icon={<FlaskConical className="w-5 h-5 text-purple-600" />}
          bgColor="bg-purple-100"
          borderColor="border-purple-200"
        />
        <StatCard
          label="Running"
          value={runningCount}
          icon={<Play className="w-5 h-5 text-green-600" />}
          bgColor="bg-green-100"
          borderColor="border-green-200"
        />
        <StatCard
          label="Completed"
          value={completedCount}
          icon={<CheckCircle className="w-5 h-5 text-blue-600" />}
          bgColor="bg-blue-100"
          borderColor="border-blue-200"
        />
        <StatCard
          label="Avg Lift"
          value={`+${avgLift.toFixed(1)}%`}
          icon={<TrendingUp className="w-5 h-5 text-emerald-600" />}
          bgColor="bg-emerald-100"
          borderColor="border-emerald-200"
        />
      </div>

      {/* Running Experiments */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-900 text-lg flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse" />
            Running Experiments
          </h2>
          <button
            onClick={() => navigate('/running')}
            className="text-sm text-purple-600 hover:text-purple-700 font-semibold bg-purple-50 hover:bg-purple-100 px-3 py-1.5 rounded-lg transition-colors"
          >
            View all →
          </button>
        </div>
        <div className="space-y-3">
          {runningExperiments.map((exp) => (
            <div
              key={exp.id}
              onClick={() => navigate(`/experiments/${exp.id}`)}
              className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm cursor-pointer hover:shadow-md hover:border-purple-200 transition-all group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse ring-4 ring-green-100" />
                  <div>
                    <p className="font-semibold text-gray-900 group-hover:text-purple-700 transition-colors">{exp.name}</p>
                    <div className="flex items-center gap-3 mt-0.5 text-xs text-gray-500">
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> Day {exp.days_running}/{exp.duration_days}</span>
                      <span>{exp.total_users.toLocaleString()} users</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-5">
                  <div className="text-right">
                    <p className="text-[11px] text-gray-500 uppercase tracking-wide">Lift</p>
                    <p className="font-bold text-green-600 text-lg">+{exp.lift}%</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[11px] text-gray-500 uppercase tracking-wide">Confidence</p>
                    <p className="font-bold text-gray-900 text-lg">{exp.confidence}%</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-purple-500 transition-colors" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Completed Experiments */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-900 text-lg flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-blue-500" />
            Completed Experiments
          </h2>
          <button
            onClick={() => navigate('/reports')}
            className="text-sm text-purple-600 hover:text-purple-700 font-semibold bg-purple-50 hover:bg-purple-100 px-3 py-1.5 rounded-lg transition-colors"
          >
            View reports →
          </button>
        </div>
        <div className="space-y-3">
          {completedExperiments.map((exp) => (
            <div
              key={exp.id}
              onClick={() => navigate(`/experiments/${exp.id}/report`)}
              className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm cursor-pointer hover:shadow-md hover:border-purple-200 transition-all group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-blue-500" />
                  <div>
                    <p className="font-semibold text-gray-900 group-hover:text-purple-700 transition-colors">{exp.name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">Completed: {exp.completed_at} • {exp.duration_days} days</p>
                  </div>
                </div>
                <div className="flex items-center gap-5">
                  <div className="text-right">
                    <p className="text-[11px] text-gray-500 uppercase tracking-wide">Lift</p>
                    <p className="font-bold text-green-600 text-lg">+{exp.lift}%</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[11px] text-gray-500 uppercase tracking-wide">Impact</p>
                    <p className="font-bold text-purple-700">{exp.revenue_impact}</p>
                  </div>
                  <span className="px-3 py-1.5 rounded-full text-xs font-bold uppercase bg-green-100 text-green-700 border border-green-200">
                    {exp.recommendation}
                  </span>
                  <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-purple-500 transition-colors" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, icon, bgColor, borderColor }: {
  label: string; value: string | number; icon: React.ReactNode; bgColor: string; borderColor: string
}) {
  return (
    <div className={`bg-white rounded-2xl border ${borderColor} p-5 shadow-sm hover:shadow-md transition-shadow`}>
      <div className={`w-11 h-11 rounded-xl ${bgColor} flex items-center justify-center mb-3`}>
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1 uppercase tracking-wider font-medium">{label}</p>
    </div>
  )
}
