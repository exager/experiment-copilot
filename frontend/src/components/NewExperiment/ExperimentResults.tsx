import { useState, useCallback } from 'react'
import { Rocket, CheckCircle2 } from 'lucide-react'
import type {
  ExperimentResultsProps,
  AIUnderstandingData,
  SuggestedMetricsData,
  MetricChipProps,
  MetricOption,
  ValidateExperimentRequest,
} from '../../types'
import {
  BUTTON_TEXT,
  PANEL_HEADINGS,
  PANEL_DESCRIPTIONS,
  BADGES,
  METRIC_LABELS,
  UNDERSTANDING_CARD_LABELS,
  UNDERSTANDING_CARD_ICONS,
  UNDERSTANDING_CARD_COLORS,
  AI_STATUS_STEPS,
  STATUS_TEXT,
} from '../../constants/experimentResults.constants'

// ============ UTILS ============

/**
 * Filters out metrics that are selected as primary from secondary/guardrail lists.
 */
const excludePrimaryMetrics = (
  metrics: readonly MetricOption[],
  primaryMetrics: readonly MetricOption[],
): MetricOption[] => {
  const primaryIds = new Set(primaryMetrics.filter((m) => m.selected).map((m) => m.id))
  return metrics.filter((m) => !primaryIds.has(m.id)).map((m) => ({ ...m }))
}

// ============ MAIN COMPONENT ============

export default function ExperimentResults({
  aiData,
  formData,
  onEditInputs,
  onGenerateConfig,
  isValidating,
}: Readonly<ExperimentResultsProps>) {
  const understandingData: AIUnderstandingData = {
    experiment_name: aiData.experiment_name ?? formData.business_goal,
    hypothesis: aiData.hypothesis ?? formData.pain_point,
    problem_statement: aiData.problem_statement ?? formData.pain_point,
    target_users: aiData.context_understanding?.target_users ?? 'All Users',
    experiment_area: aiData.context_understanding?.experiment_area ?? formData.feature_page,
    ai_confidence: aiData.context_understanding?.ai_confidence
      ? `${aiData.context_understanding.ai_confidence}%`
      : 'N/A',
  }

  // Primary: only show metrics where selected === true (static, not editable)
  const primarySelected = aiData.primary_metric.filter((m) => m.selected)

  // Secondary & Guardrail: exclude primary-selected, user can toggle these
  const initialSecondary = excludePrimaryMetrics(aiData.secondary_metrics, aiData.primary_metric)
  const initialGuardrail = excludePrimaryMetrics(aiData.guardrail_metrics, aiData.primary_metric)

  const [secondaryMetrics, setSecondaryMetrics] = useState<MetricOption[]>(initialSecondary)
  const [guardrailMetrics, setGuardrailMetrics] = useState<MetricOption[]>(initialGuardrail)

  const handleSecondaryToggle = useCallback((metricId: string): void => {
    setSecondaryMetrics((prev) =>
      prev.map((m) => (m.id === metricId ? { ...m, selected: !m.selected } : m)),
    )
  }, [])

  const handleGuardrailToggle = useCallback((metricId: string): void => {
    setGuardrailMetrics((prev) =>
      prev.map((m) => (m.id === metricId ? { ...m, selected: !m.selected } : m)),
    )
  }, [])

  const handleGenerateConfig = async (): Promise<void> => {
    const metricsPayload: ValidateExperimentRequest = {
      primary_metric: aiData.primary_metric.map(({ id, selected }) => ({ id, selected })),
      secondary_metrics: secondaryMetrics.map(({ id, selected }) => ({ id, selected })),
    }
    await onGenerateConfig(metricsPayload)
  }

  const metricsData: SuggestedMetricsData = {
    primary_metric: primarySelected,
    secondary_metrics: secondaryMetrics,
    guardrail_metrics: guardrailMetrics,
  }

  return (
    <>
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-[2fr_1.5fr_1fr] gap-6 animate-slide-up">
        {/* Column 1: AI Understanding */}
        <div className="animate-slide-up animate-stagger-1">
          <AIUnderstandingPanel data={understandingData} />
        </div>

        {/* Column 2: Suggested Metrics */}
        <div className="animate-slide-up animate-stagger-2">
          <SuggestedMetricsPanel
            data={metricsData}
            onSecondaryToggle={handleSecondaryToggle}
            onGuardrailToggle={handleGuardrailToggle}
          />
        </div>

        {/* Column 3: AI Status */}
        <div className="animate-slide-up animate-stagger-3">
          <AIStatusPanel />
        </div>
      </div>

      {/* Bottom Buttons */}
      <div
        className="mt-6 flex items-center justify-between animate-slide-up"
        style={{ animationDelay: '0.5s', opacity: 0, animationFillMode: 'forwards' }}
      >
        <button
          type="button"
          onClick={onEditInputs}
          disabled={isValidating}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 px-5 py-2.5 rounded-xl hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          {BUTTON_TEXT.EDIT_INPUTS}
        </button>
        <button
          type="button"
          onClick={handleGenerateConfig}
          disabled={isValidating}
          className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:opacity-60 text-white px-7 py-3 rounded-xl font-semibold text-sm transition-all transform hover:scale-[1.02] active:scale-95 shadow-lg shadow-purple-200"
        >
          {isValidating ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Validating...
            </>
          ) : (
            <>
              <Rocket className="w-4 h-4" aria-hidden="true" />
              {BUTTON_TEXT.GENERATE_CONFIG}
            </>
          )}
        </button>
      </div>
    </>
  )
}

// ============ AI UNDERSTANDING PANEL ============

function AIUnderstandingPanel({ data }: Readonly<{ data: AIUnderstandingData }>) {
  const items = [
    { icon: UNDERSTANDING_CARD_ICONS.EXPERIMENT, label: UNDERSTANDING_CARD_LABELS.EXPERIMENT, value: data.experiment_name, color: UNDERSTANDING_CARD_COLORS.EXPERIMENT },
    { icon: UNDERSTANDING_CARD_ICONS.HYPOTHESIS, label: UNDERSTANDING_CARD_LABELS.HYPOTHESIS, value: data.hypothesis, color: UNDERSTANDING_CARD_COLORS.HYPOTHESIS },
    { icon: UNDERSTANDING_CARD_ICONS.PROBLEM, label: UNDERSTANDING_CARD_LABELS.PROBLEM, value: data.problem_statement, color: UNDERSTANDING_CARD_COLORS.PROBLEM },
    { icon: UNDERSTANDING_CARD_ICONS.TARGET_USERS, label: UNDERSTANDING_CARD_LABELS.TARGET_USERS, value: data.target_users, color: UNDERSTANDING_CARD_COLORS.TARGET_USERS },
    { icon: UNDERSTANDING_CARD_ICONS.EXPERIMENT_AREA, label: UNDERSTANDING_CARD_LABELS.EXPERIMENT_AREA, value: data.experiment_area, color: UNDERSTANDING_CARD_COLORS.EXPERIMENT_AREA },
    { icon: UNDERSTANDING_CARD_ICONS.CONFIDENCE, label: UNDERSTANDING_CARD_LABELS.CONFIDENCE, value: data.ai_confidence, color: UNDERSTANDING_CARD_COLORS.CONFIDENCE },
  ] as const

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm card-hover h-full">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg" aria-hidden="true">🧠</span>
        <h3 className="font-semibold text-gray-900">{PANEL_HEADINGS.AI_UNDERSTANDING}</h3>
        <span className="text-xs bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 px-2.5 py-0.5 rounded-full font-medium border border-green-200">
          {BADGES.AI_GENERATED}
        </span>
      </div>
      <p className="text-xs text-gray-500 mb-4">
        {PANEL_DESCRIPTIONS.AI_UNDERSTANDING}
      </p>

      <div className="grid grid-cols-2 gap-3">
        {items.map((item, index) => (
          <div
            key={item.label}
            className={`p-3 rounded-xl border ${item.color} transition-all hover:shadow-sm`}
            style={{ animationDelay: `${index * 0.05}s` }}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <span className="text-sm" aria-hidden="true">{item.icon}</span>
              <span className="text-[11px] text-gray-500 font-medium uppercase tracking-wide">{item.label}</span>
            </div>
            <p className="text-sm font-semibold text-gray-800 leading-tight">{item.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============ SUGGESTED METRICS PANEL ============

interface SuggestedMetricsPanelProps {
  readonly data: SuggestedMetricsData
  readonly onSecondaryToggle: (metricId: string) => void
  readonly onGuardrailToggle: (metricId: string) => void
}

function SuggestedMetricsPanel({ data, onSecondaryToggle, onGuardrailToggle }: Readonly<SuggestedMetricsPanelProps>) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm card-hover h-full">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg" aria-hidden="true">📊</span>
        <h3 className="font-semibold text-gray-900">{PANEL_HEADINGS.SUGGESTED_METRICS}</h3>
      </div>
      <p className="text-xs text-gray-500 mb-4">
        {PANEL_DESCRIPTIONS.SUGGESTED_METRICS}
      </p>

      {/* Primary Metric - static, not toggleable */}
      <div className="mb-5">
        <span className="text-[11px] font-bold text-gray-600 uppercase tracking-wider">
          {METRIC_LABELS.PRIMARY}
        </span>
        <div className="mt-1.5 flex flex-col gap-2">
          {data.primary_metric.map((metric) => (
            <div
              key={metric.id}
              className="w-full border border-purple-200 bg-purple-50 rounded-xl px-4 py-2.5 text-sm font-semibold text-purple-800 flex items-center gap-2"
            >
              <div className="w-2 h-2 rounded-full bg-purple-500" aria-hidden="true" />
              {metric.label}
            </div>
          ))}
        </div>
      </div>

      {/* Secondary Metrics - user can toggle */}
      <div className="mb-5">
        <span className="text-[11px] font-bold text-gray-600 uppercase tracking-wider">
          {METRIC_LABELS.SECONDARY}
        </span>
        <div className="mt-2 flex flex-wrap gap-2">
          {data.secondary_metrics.map((metric) => (
            <MetricChip
              key={metric.id}
              label={metric.label}
              selected={metric.selected}
              onToggle={() => onSecondaryToggle(metric.id)}
              color="purple"
            />
          ))}
        </div>
      </div>

      {/* Guardrail Metrics - user can toggle */}
      <div>
        <span className="text-[11px] font-bold text-gray-600 uppercase tracking-wider">
          {METRIC_LABELS.GUARDRAIL}
        </span>
        <div className="mt-2 flex flex-wrap gap-2">
          {data.guardrail_metrics.map((metric) => (
            <MetricChip
              key={metric.id}
              label={metric.label}
              selected={metric.selected}
              onToggle={() => onGuardrailToggle(metric.id)}
              color="red"
            />
          ))}
        </div>
      </div>
    </div>
  )
}

// ============ METRIC CHIP ============

function MetricChip({ label, selected, onToggle, color = 'purple' }: Readonly<MetricChipProps>) {
  const selectedStyles = color === 'purple'
    ? 'bg-purple-100 border-purple-300 text-purple-800'
    : 'bg-red-50 border-red-300 text-red-800'

  const unselectedStyles = 'bg-gray-50 border-gray-200 text-gray-500 hover:border-gray-300 hover:bg-gray-100'

  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={selected}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all cursor-pointer ${selected ? selectedStyles : unselectedStyles}`}
    >
      {selected && (
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      )}
      {label}
    </button>
  )
}

// ============ AI STATUS PANEL ============

function AIStatusPanel() {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm card-hover h-full">
      <div className="flex items-center gap-2 mb-5">
        <span className="text-lg" aria-hidden="true">🤖</span>
        <h3 className="font-semibold text-gray-900">{PANEL_HEADINGS.AI_STATUS}</h3>
      </div>

      <div className="space-y-4 mb-6">
        {AI_STATUS_STEPS.map((step, index) => (
          <div key={step.label} className="flex items-center gap-3" style={{ animationDelay: `${index * 0.15}s` }}>
            <div className={`animate-check flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${step.completed ? 'bg-green-100' : 'bg-gray-100'}`}>
              <CheckCircle2
                className={`w-4 h-4 ${step.completed ? 'text-green-600' : 'text-gray-400'}`}
                aria-hidden="true"
              />
            </div>
            <span className={`text-sm font-medium ${step.completed ? 'text-gray-800' : 'text-gray-400'}`}>
              {step.label}
            </span>
          </div>
        ))}
      </div>

      <div className="text-center pt-5 border-t border-gray-100">
        <p className="text-[11px] text-gray-400 uppercase tracking-wider font-bold mb-3">{STATUS_TEXT.LABEL}</p>
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-green-100 to-emerald-100 mb-3">
          <Rocket className="w-7 h-7 text-green-600" aria-hidden="true" />
        </div>
        <p className="text-sm font-bold text-green-600">{STATUS_TEXT.READY}</p>
      </div>
    </div>
  )
}
