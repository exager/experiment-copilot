import type { ReactNode } from 'react'

// ============ Experiment Form Types ============

export interface ExperimentFormData {
  readonly business_goal: string
  readonly website_url: string
  readonly feature_page: string
  readonly user_flow: string
  readonly pain_point: string
}

export interface ExperimentFormProps {
  readonly onGenerate: (data: ExperimentFormData) => Promise<void>
  readonly isLoading: boolean
  readonly apiError: string | null
  readonly onApiErrorClear: () => void
}

export interface InputFieldProps {
  readonly label: string
  readonly required?: boolean
  readonly icon: ReactNode
  readonly value: string
  readonly onChange: (value: string) => void
  readonly placeholder: string
  readonly error?: string
  readonly hint?: string
}

export interface TextAreaFieldProps {
  readonly label: string
  readonly required?: boolean
  readonly icon: ReactNode
  readonly value: string
  readonly onChange: (value: string) => void
  readonly placeholder: string
  readonly error?: string
  readonly hint?: string
}

// ============ Experiment Results Types ============

export interface MetricOption {
  readonly id: string
  readonly label: string
  readonly selected: boolean
}

export interface ContextUnderstanding {
  readonly product_type: string
  readonly business_goal_summary: string
  readonly problem_identified: string
  readonly experiment_area: string
  readonly target_users: string
  readonly ai_confidence: number
}

export interface HypothesisResponse {
  readonly thread_id: string
  readonly experiment_id: number
  readonly experiment_name: string
  readonly hypothesis: string
  readonly problem_statement: string
  readonly context_understanding: ContextUnderstanding
  readonly primary_metric: readonly MetricOption[]
  readonly secondary_metrics: readonly MetricOption[]
  readonly guardrail_metrics: readonly MetricOption[]
}

export interface ValidateExperimentRequest {
  readonly primary_metric: readonly MetricOption[]
  readonly secondary_metrics: readonly MetricOption[]
  readonly guardrail_metrics: readonly MetricOption[]
}

export interface ExperimentResultsProps {
  readonly aiData: HypothesisResponse
  readonly formData: Pick<ExperimentFormData, 'business_goal' | 'feature_page' | 'pain_point'>
  readonly onEditInputs: () => void
  readonly onGenerateConfig: (metrics: ValidateExperimentRequest) => Promise<void>
  readonly isValidating: boolean
}

export interface CatalogData {
  readonly primary_metrics?: readonly string[]
  readonly secondary_metrics?: readonly string[]
  readonly guardrail_metrics?: readonly string[]
}

export interface AIUnderstandingData {
  readonly experiment_name: string
  readonly hypothesis: string
  readonly problem_statement: string
  readonly target_users: string
  readonly experiment_area: string
  readonly ai_confidence: string
}

export interface SuggestedMetricsData {
  readonly primary_metric: readonly MetricOption[]
  readonly secondary_metrics: readonly MetricOption[]
  readonly guardrail_metrics: readonly MetricOption[]
}

export interface MetricChipProps {
  readonly label: string
  readonly selected: boolean
  readonly onToggle: () => void
  readonly color?: 'purple' | 'red'
}

// ============ POST /context — Request & Response ============

export interface ContextRequest {
  business_goal: string
  website: string
  current_flow: string
  feature: string
  pain_point: string
}

export interface ContextResponse {
  experiment_id: number
  context_id: number
  hypothesis: Hypothesis
  configuration: Configuration
  status: 'draft' | 'running' | 'completed'
}

export interface Hypothesis {
  experiment_name: string
  hypothesis: string
  primary_metric: string
  secondary_metrics: string[]
  guardrail_metrics: string[]
}

export interface Configuration {
  feature_flag: string
  audience: string
  traffic_split_option: string
  traffic_split: { control: number; variant: number }
  duration_days: number
  sample_size: number
  confidence_level: number
  baseline_conversion_rate: number
  expected_lift: number
}

// ============ POST /experiments/:id/validate — Response ============

export interface ValidateResponse {
  readonly decision: 'approve' | 'reject'
  readonly explanation: string
  readonly validation_score: number
  readonly warnings: string[]
  readonly suggestions: string[]
  readonly rules_evaluated: ValidationRule[]
  readonly rules_matched: ValidationRule[]
  readonly rules_rejected: ValidationRule[]
}

export interface ValidationRule {
  readonly rule_id: string
  readonly name: string
  readonly priority: number
  readonly matched: boolean
  readonly decision: 'approve' | 'reject'
  readonly message: string
  readonly details: Record<string, unknown>
}

export interface ValidationPanelProps {
  readonly data: ValidateResponse
  readonly onLaunch: () => Promise<void>
  readonly isLaunching: boolean
  readonly onBack?: () => void
}

// ============ GET /experiment/:id/metrics — Response ============

export interface MetricsResponse {
  experiment_id: number
  latest: MetricSnapshot
  series: MetricSnapshot[]
  statistics: Statistics
  recommendation: Recommendation
}

export interface MetricSnapshot {
  id: number
  experiment_id?: number
  users_control: number
  users_variant: number
  conversion_control: number
  conversion_variant: number
  revenue_control: number
  revenue_variant: number
  confidence: number
  p_value: number
  conversion_lift: number
  timestamp: string
}

export interface Statistics {
  p_value: number
  confidence: number
  conversion_lift: number
  z_score: number
  control_conversion_rate: number
  variant_conversion_rate: number
  winner: 'variant' | 'control' | 'inconclusive'
  is_significant: boolean
}

export interface Recommendation {
  recommendation: 'scale' | 'continue' | 'stop' | 'rollback'
  rationale: string
  confidence: number
}

// ============ POST /report/:id — Response ============

export interface ReportResponse {
  id: number
  experiment_id: number
  summary: string
  recommendation: 'scale' | 'continue' | 'stop' | 'rollback'
  business_impact: string
  next_steps: string[]
  details: {
    business_goal: string
    hypothesis: {
      experiment_name: string
      hypothesis: string
      primary_metric: string
    }
    configuration: {
      feature_flag: string
      audience: string
      traffic_split: { control: number; variant: number }
    }
    statistics: {
      confidence: number
      conversion_lift: number
      winner: string
    }
  }
  generated_at: string
}

// ============ Experiment Start Response ============

export interface ExperimentStartResponse {
  id: number
  context_id: number
  hypothesis: Hypothesis
  configuration: Configuration
  validation: {
    rules_evaluated: ValidationRule[]
    rules_matched: ValidationRule[]
    rules_rejected: ValidationRule[]
    decision: 'approve' | 'reject'
    explanation: string
    validation_score: number
    warnings: string[]
    suggestions: string[]
  }
  status: string
  created_at: string
  started_at: string
  completed_at: string | null
}
