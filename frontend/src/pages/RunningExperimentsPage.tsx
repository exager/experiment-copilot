import { useNavigate } from 'react-router-dom'
import { Play, TrendingUp, Users, Clock, ChevronRight } from 'lucide-react'
import experiments from '../mocks/runningExperiments.json'

export default function RunningExperimentsPage() {
  const navigate = useNavigate()

  return (
    <div className="p-6 lg:p-8 min-h-full">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Play className="w-6 h-6 text-green-600" />
          Running Experiments
        </h1>
        <p className="text-sm text-gray-500 mt-1">Monitor your active experiments in real-time</p>
      </div>

      {/* Experiment Cards */}
      <div className="space-y-4">
        {experiments.map((exp) => {
          const progress = (exp.days_running / exp.duration_days) * 100
          const isWinning = exp.winner === 'Variant'
          const borderColor = isWinning ? 'border-l-green-500' : 'border-l-gray-300'
          const confidenceColor = exp.confidence >= 95 ? 'text-green-600' : exp.confidence >= 80 ? 'text-blue-600' : 'text-gray-600'

          return (
            <div
              key={exp.id}
              onClick={() => navigate(`/experiments/${exp.id}`)}
              className={`bg-white rounded-2xl border border-gray-100 border-l-4 ${borderColor} p-5 shadow-sm cursor-pointer transition-all hover:shadow-md hover:border-purple-200 hover:scale-[1.005] active:scale-[0.99] group`}
            >
              <div className="flex items-center justify-between">
                {/* Left: Info */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse ring-4 ring-green-100" />
                    <h3 className="font-semibold text-gray-900 text-lg group-hover:text-purple-700 transition-colors">
                      {exp.name}
                    </h3>
                  </div>

                  {/* Progress bar */}
                  <div className="ml-6 mb-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        Day {exp.days_running} of {exp.duration_days}
                      </span>
                      <span className="text-xs text-gray-500">{Math.round(progress)}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>

                  {/* Meta info */}
                  <div className="ml-6 flex items-center gap-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      {exp.total_users.toLocaleString()} users
                    </span>
                    <span>Started: {exp.started_at}</span>
                  </div>
                </div>

                {/* Right: Metrics */}
                <div className="flex items-center gap-5 ml-6">
                  {/* Lift */}
                  <div className="text-right">
                    <p className="text-[11px] text-gray-500 uppercase tracking-wide">Lift</p>
                    <p className="text-xl font-bold text-green-600 flex items-center gap-1">
                      <TrendingUp className="w-4 h-4" />
                      +{exp.lift}%
                    </p>
                  </div>

                  {/* Confidence */}
                  <div className="text-right">
                    <p className="text-[11px] text-gray-500 uppercase tracking-wide">Confidence</p>
                    <p className={`text-xl font-bold ${confidenceColor}`}>
                      {exp.confidence}%
                    </p>
                  </div>

                  {/* Winner Badge */}
                  <div className="min-w-[90px]">
                    <p className="text-[11px] text-gray-500 uppercase tracking-wide mb-1">Winner</p>
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${
                      isWinning
                        ? 'bg-green-100 text-green-700 border border-green-200'
                        : 'bg-gray-100 text-gray-500 border border-gray-200'
                    }`}>
                      {isWinning && <span className="w-1.5 h-1.5 rounded-full bg-green-500 mr-1.5" />}
                      {exp.winner}
                    </span>
                  </div>

                  {/* Arrow */}
                  <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-purple-500 transition-colors" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Empty state */}
      {experiments.length === 0 && (
        <div className="text-center py-20">
          <Play className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No running experiments</p>
          <p className="text-sm text-gray-400 mt-1">Create a new experiment to get started</p>
        </div>
      )}
    </div>
  )
}
