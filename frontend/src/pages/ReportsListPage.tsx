import { useNavigate } from 'react-router-dom'
import { FileText, TrendingUp, ChevronRight, DollarSign, CheckCircle } from 'lucide-react'
import experiments from '../mocks/completedExperiments.json'

export default function ReportsListPage() {
  const navigate = useNavigate()

  return (
    <div className="p-6 lg:p-8 min-h-full">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <FileText className="w-6 h-6 text-purple-600" />
          Executive Reports
        </h1>
        <p className="text-sm text-gray-500 mt-1">AI generated summaries and recommendations for completed experiments</p>
      </div>

      {/* Experiment Report Cards */}
      <div className="space-y-4">
        {experiments.map((exp) => (
          <div
            key={exp.id}
            onClick={() => navigate(`/experiments/${exp.id}/report`)}
            className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm cursor-pointer transition-all hover:shadow-md hover:border-purple-200 hover:scale-[1.01] active:scale-[0.99]"
          >
            <div className="flex items-center justify-between">
              {/* Left: Info */}
              <div className="flex items-center gap-4">
                {/* Status icon */}
                <div className="w-10 h-10 rounded-xl bg-green-100 flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>

                {/* Name & details */}
                <div>
                  <h3 className="font-semibold text-gray-900 text-lg">{exp.name}</h3>
                  <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                    <span>Completed: {exp.completed_at}</span>
                    <span>Duration: {exp.duration_days} days</span>
                  </div>
                </div>
              </div>

              {/* Right: Metrics + Action */}
              <div className="flex items-center gap-6">
                {/* Lift */}
                <div className="text-right">
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Lift</p>
                  <p className="text-lg font-bold text-green-600 flex items-center gap-1">
                    <TrendingUp className="w-4 h-4" />
                    +{exp.lift}%
                  </p>
                </div>

                {/* Revenue Impact */}
                <div className="text-right">
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Impact</p>
                  <p className="text-lg font-bold text-purple-700 flex items-center gap-1">
                    <DollarSign className="w-4 h-4" />
                    {exp.revenue_impact}
                  </p>
                </div>

                {/* Recommendation badge */}
                <div>
                  <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wide ${
                    exp.recommendation === 'SCALE' ? 'bg-green-100 text-green-700' :
                    exp.recommendation === 'STOP' ? 'bg-gray-100 text-gray-600' :
                    exp.recommendation === 'ROLLBACK' ? 'bg-red-100 text-red-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                    {exp.recommendation}
                  </span>
                </div>

                {/* Arrow */}
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty state */}
      {experiments.length === 0 && (
        <div className="text-center py-20">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No completed experiments yet</p>
          <p className="text-sm text-gray-400 mt-1">Reports will appear here once experiments finish</p>
        </div>
      )}
    </div>
  )
}
