import { useNavigate } from 'react-router-dom'
import { Download, Share2, CheckCircle2, ArrowUpRight, ChevronLeft } from 'lucide-react'
import { LineChart, Line, Area, AreaChart, ResponsiveContainer } from 'recharts'
import report from '../mocks/reportData.json'

// Mini sparkline data for business impact chart
const sparklineData = [
  { v: 20 }, { v: 25 }, { v: 30 }, { v: 28 }, { v: 35 }, { v: 40 }, { v: 38 }, { v: 45 }, { v: 50 }, { v: 55 }, { v: 60 }, { v: 65 }
]

export default function ReportPage() {
  const navigate = useNavigate()

  return (
    <div className="p-6 lg:p-8 min-h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Executive Report</h1>
          <p className="text-sm text-gray-500 mt-0.5">AI generated summary and recommendations</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors">
            <Download className="w-4 h-4" />
            Download PDF
          </button>
          <button className="flex items-center gap-2 border border-gray-200 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-xl text-sm font-medium transition-colors">
            <Share2 className="w-4 h-4" />
            Share
          </button>
        </div>
      </div>

      {/* Main 3-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_1.5fr_1fr] gap-6 mb-6">

        {/* Column 1: Experiment Summary */}
        <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
          <h2 className="font-bold text-gray-900 text-lg mb-5">Experiment Summary</h2>

          <div className="space-y-4">
            <SummaryItem label="Business Goal" value={report.experiment_summary.business_goal} />
            <SummaryItem label="Hypothesis" value={report.experiment_summary.hypothesis} />
            <SummaryItem label="Feature Flag" value={report.experiment_summary.feature_flag} mono />
            <SummaryItem label="Target Audience" value={report.experiment_summary.target_audience} />
            <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
              <p className="text-[11px] text-purple-600 font-bold uppercase tracking-wider mb-1">Traffic Allocation</p>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                  <span className="text-sm font-medium text-gray-800">Control {report.experiment_summary.traffic_allocation.control}%</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
                  <span className="text-sm font-medium text-gray-800">Variant {report.experiment_summary.traffic_allocation.variant}%</span>
                </div>
              </div>
            </div>
            <SummaryItem label="Duration" value={report.experiment_summary.duration} />
            <SummaryItem label="Started At" value={report.experiment_summary.started_at} />
          </div>
        </div>

        {/* Column 2: Results */}
        <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
          <h2 className="font-bold text-gray-900 text-lg mb-5">Results</h2>

          <div className="space-y-5">
            {/* Checkout Conversion */}
            <ResultMetric
              label="Checkout Conversion"
              control={report.results.checkout_conversion.control}
              variant={report.results.checkout_conversion.variant}
              uplift={report.results.checkout_conversion.uplift}
            />

            {/* Confidence & p-value — styled as cards */}
            <div className="flex items-center gap-3 py-3">
              <div className="flex-1 bg-purple-50 border border-purple-100 rounded-xl p-3 text-center">
                <p className="text-[11px] text-purple-600 font-bold uppercase tracking-wider">Confidence</p>
                <p className="text-2xl font-black text-purple-700 mt-1">{report.results.confidence}</p>
              </div>
              <div className="flex-1 bg-blue-50 border border-blue-100 rounded-xl p-3 text-center">
                <p className="text-[11px] text-blue-600 font-bold uppercase tracking-wider">p-value</p>
                <p className="text-2xl font-black text-blue-700 mt-1">{report.results.p_value}</p>
              </div>
            </div>

            {/* Average Order Value */}
            <ResultMetric
              label="Average Order Value"
              control={report.results.average_order_value.control}
              variant={report.results.average_order_value.variant}
              uplift={report.results.average_order_value.uplift}
            />

            {/* Bounce Rate */}
            <ResultMetric
              label="Bounce Rate"
              control={report.results.bounce_rate.control}
              variant={report.results.bounce_rate.variant}
              uplift={report.results.bounce_rate.improvement}
              isImprovement
            />

            {/* Payment Failure Rate */}
            <ResultMetric
              label="Payment Failure Rate"
              control={report.results.payment_failure_rate.control}
              variant={report.results.payment_failure_rate.variant}
              uplift={report.results.payment_failure_rate.improvement}
              isImprovement
            />
          </div>
        </div>

        {/* Column 3: Business Impact + AI Recommendation */}
        <div className="space-y-6">
          {/* Business Impact */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h2 className="font-bold text-gray-900 mb-3">Business Impact</h2>
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Estimated Additional Revenue</p>
            <p className="text-3xl font-black text-green-600 mt-1">{report.business_impact.estimated_revenue}</p>
            <p className="text-sm text-gray-500">{report.business_impact.period}</p>
            <p className="text-xs text-gray-400 mt-2">{report.business_impact.description}</p>

            {/* Sparkline with gradient fill */}
            <div className="mt-4">
              <ResponsiveContainer width="100%" height={70}>
                <AreaChart data={sparklineData}>
                  <defs>
                    <linearGradient id="sparkGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#10B981" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#10B981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area type="monotone" dataKey="v" stroke="#10B981" strokeWidth={2} fill="url(#sparkGradient)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* AI Recommendation */}
          <div className="bg-white rounded-2xl border border-green-200 p-6 shadow-sm bg-gradient-to-br from-white to-green-50/50">
            <h2 className="font-bold text-gray-900 mb-3">AI Recommendation</h2>
            <div className="mb-4 bg-green-100 border border-green-200 rounded-xl p-3 text-center">
              <span className="text-4xl font-black text-green-700 uppercase tracking-wider">
                {report.ai_recommendation.action}
              </span>
            </div>
            <p className="text-sm text-gray-600 mb-4 leading-relaxed">{report.ai_recommendation.reasoning}</p>

            <div>
              <p className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Next Actions</p>
              <div className="space-y-2.5">
                {report.ai_recommendation.next_actions.map((action, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{action}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Key Takeaway */}
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-2xl border border-purple-100 p-6 mb-6">
        <h3 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
          <ArrowUpRight className="w-5 h-5 text-purple-600" />
          Key Takeaway
        </h3>
        <p className="text-sm text-gray-700 leading-relaxed">{report.key_takeaway}</p>
      </div>

      {/* Back Button */}
      <div className="flex items-center">
        <button
          onClick={() => navigate('/reports')}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 px-4 py-2 rounded-xl hover:bg-gray-50 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Reports
        </button>
      </div>
    </div>
  )
}

// ============ Sub-Components ============

function SummaryItem({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
      <p className="text-[11px] text-purple-600 font-bold uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-sm text-gray-800 font-medium leading-relaxed ${mono ? 'font-mono bg-white px-2 py-1 rounded border border-gray-200 inline-block text-purple-700' : ''}`}>{value}</p>
    </div>
  )
}

function ResultMetric({ label, control, variant, uplift, isImprovement }: {
  label: string; control: string; variant: string; uplift: string; isImprovement?: boolean
}) {
  return (
    <div className="border-t border-gray-100 pt-3">
      <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-2">{label}</p>
      <div className="flex items-end gap-6">
        <div>
          <p className="text-xl font-bold text-gray-900">{control}</p>
          <p className="text-[11px] text-gray-500">Control</p>
        </div>
        <div>
          <p className="text-xl font-bold text-gray-900">{variant}</p>
          <p className="text-[11px] text-gray-500">Variant</p>
        </div>
        <div>
          <p className="text-sm font-bold text-green-600">{uplift}</p>
          <p className="text-[11px] text-gray-500">{isImprovement ? 'Improvement' : 'Uplift'}</p>
        </div>
      </div>
    </div>
  )
}
