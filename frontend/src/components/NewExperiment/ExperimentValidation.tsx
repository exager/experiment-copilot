import { Rocket, CheckCircle2, XCircle, AlertTriangle, Lightbulb } from 'lucide-react'
import type { ValidationPanelProps, ValidationRule } from '../../types'
import {
  PANEL_HEADING,
  DECISION_LABELS,
  DECISION_STYLES,
  SECTION_LABELS,
  EMPTY_STATE,
  BUTTON_TEXT,
} from '../../constants/experimentValidation.constants'

// ============ MAIN COMPONENT ============

export default function ExperimentValidation({
  data,
  onLaunch,
  isLaunching,
  onBack,
}: Readonly<ValidationPanelProps>) {
  const passedCount = data.rules_matched.length
  const totalCount = data.rules_evaluated.length
  const scorePercent = Math.round(data.validation_score * 100)
  const isApproved = data.decision === 'approve'

  return (
    <div className="mt-8 animate-slide-up">
      <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
        {/* Header with decision badge */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <span className="text-lg" aria-hidden="true">🛡️</span>
            <h3 className="font-semibold text-gray-900 text-lg">{PANEL_HEADING}</h3>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold border ${DECISION_STYLES[data.decision]}`}
          >
            {isApproved ? '✅' : '❌'} {DECISION_LABELS[data.decision].toUpperCase()}
          </span>
        </div>

        {/* Score Bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Validation Score</span>
            <span className="text-sm font-bold text-gray-900">{scorePercent}%</span>
          </div>
          <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${isApproved ? 'bg-gradient-to-r from-green-400 to-emerald-500' : 'bg-gradient-to-r from-red-400 to-red-500'}`}
              style={{ width: `${scorePercent}%` }}
            />
          </div>
          <progress className="sr-only" value={scorePercent} max={100}>
            {scorePercent}%
          </progress>
        </div>

        {/* Rules Evaluated */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-sm" aria-hidden="true">📋</span>
            <span className="text-sm font-semibold text-gray-700">
              {SECTION_LABELS.RULES_EVALUATED} ({passedCount}/{totalCount} passed)
            </span>
          </div>
          <div className="border border-gray-100 rounded-xl overflow-hidden divide-y divide-gray-50">
            {data.rules_evaluated.map((rule) => (
              <RuleRow key={rule.rule_id} rule={rule} />
            ))}
          </div>
        </div>

        {/* Explanation */}
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm" aria-hidden="true">💬</span>
            <span className="text-sm font-semibold text-gray-700">{SECTION_LABELS.EXPLANATION}</span>
          </div>
          <p className="text-sm text-gray-600 bg-gray-50 rounded-xl px-4 py-3 leading-relaxed italic">
            &ldquo;{data.explanation}&rdquo;
          </p>
        </div>

        {/* Warnings */}
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-yellow-500" aria-hidden="true" />
            <span className="text-sm font-semibold text-gray-700">{SECTION_LABELS.WARNINGS}</span>
          </div>
          {data.warnings.length > 0 ? (
            <ul className="space-y-1.5">
              {data.warnings.map((warning, index) => (
                <li
                  key={`warning-${index}`} // NOSONAR - index is stable for static list
                  className="text-sm text-yellow-700 bg-yellow-50 border border-yellow-100 rounded-lg px-3 py-2"
                >
                  {warning}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-400">{EMPTY_STATE.WARNINGS}</p>
          )}
        </div>

        {/* Suggestions */}
        <div className="mb-2">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb className="w-4 h-4 text-blue-500" aria-hidden="true" />
            <span className="text-sm font-semibold text-gray-700">{SECTION_LABELS.SUGGESTIONS}</span>
          </div>
          {data.suggestions.length > 0 ? (
            <ul className="space-y-1.5">
              {data.suggestions.map((suggestion, index) => (
                <li
                  key={`suggestion-${index}`} // NOSONAR - index is stable for static list
                  className="text-sm text-blue-700 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2"
                >
                  {suggestion}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-400">{EMPTY_STATE.SUGGESTIONS}</p>
          )}
        </div>
      </div>

      {/* Bottom Buttons */}
      <div className="mt-6 flex items-center justify-between">
        {onBack && (
          <button
            type="button"
            onClick={onBack}
            disabled={isLaunching}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 px-5 py-2.5 rounded-xl hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Back to Metrics
          </button>
        )}
        <div className={onBack ? '' : 'ml-auto'}>
          <button
            type="button"
            onClick={onLaunch}
            disabled={isLaunching || !isApproved}
            className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:opacity-60 text-white px-7 py-3 rounded-xl font-semibold text-sm transition-all transform hover:scale-[1.02] active:scale-95 shadow-lg shadow-purple-200"
          >
            {isLaunching ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                {BUTTON_TEXT.LAUNCHING}
              </>
            ) : (
              <>
                <Rocket className="w-4 h-4" aria-hidden="true" />
                {BUTTON_TEXT.LAUNCH}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

// ============ RULE ROW ============

function RuleRow({ rule }: Readonly<{ rule: ValidationRule }>) {
  const isPassed = rule.decision === 'approve'

  return (
    <div className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50/50 transition-colors">
      <div className="flex-shrink-0">
        {isPassed ? (
          <CheckCircle2 className="w-4.5 h-4.5 text-green-500" aria-label="Passed" />
        ) : (
          <XCircle className="w-4.5 h-4.5 text-red-500" aria-label="Failed" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${isPassed ? 'text-gray-800' : 'text-red-700'}`}>
          {rule.name}
        </p>
      </div>
      <p className="text-xs text-gray-500 text-right max-w-[200px] truncate" title={rule.message}>
        {rule.message}
      </p>
    </div>
  )
}
