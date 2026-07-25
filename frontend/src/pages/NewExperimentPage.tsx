import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Zap } from 'lucide-react'
import { createExperimentContext, generateHypothesis, getCatalog, validateExperiment, launchExperiment } from '../services/api'
import { ExperimentForm, ExperimentResults, ExperimentValidation, Stepper } from '../components/NewExperiment'
import type { StepConfig } from '../components/NewExperiment'
import type { ExperimentFormData, HypothesisResponse, ValidateExperimentRequest, ValidateResponse, CatalogData } from '../types'

// ============ CONSTANTS ============

const ERROR_FALLBACK = 'Failed to generate experiment. Please try again.'

const STEPS: readonly StepConfig[] = [
  { label: 'Define Context', icon: '1' },
  { label: 'Review Hypothesis', icon: '2' },
  { label: 'Validate & Launch', icon: '3' },
] as const

// ============ MAIN PAGE ============

export default function NewExperimentPage() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [isValidating, setIsValidating] = useState(false)
  const [isLaunching, setIsLaunching] = useState(false)
  const [aiData, setAiData] = useState<HypothesisResponse | null>(null)
  const [validationData, setValidationData] = useState<ValidateResponse | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const [lastFormData, setLastFormData] = useState<ExperimentFormData | null>(null)

  // Cache catalog on page load
  const catalogRef = useRef<CatalogData | null>(null)

  useEffect(() => {
    if (!catalogRef.current) {
      getCatalog()
        .then((res) => { catalogRef.current = res.data })
        .catch(() => {}) // NOSONAR - catalog is optional, silent fail is intentional
    }
  }, [])

  // Step 1 → Step 2: Generate hypothesis
  const handleGenerate = async (formData: ExperimentFormData): Promise<void> => {
    setIsLoading(true)
    setApiError(null)
    try {
      const contextRes = await createExperimentContext({
        business_goal: formData.business_goal,
        website: formData.website_url,
        current_flow: formData.user_flow,
        feature: formData.feature_page,
        pain_point: formData.pain_point,
      })

      const contextId = contextRes.data.id
      const hypothesisRes = await generateHypothesis(contextId)

      setAiData(hypothesisRes.data)
      setLastFormData(formData)
      setCurrentStep(1)
    } catch (err: unknown) {
      setApiError(extractErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  // Step 2 → Step 3: Validate experiment
  const handleGenerateConfig = async (metrics: ValidateExperimentRequest): Promise<void> => {
    if (!aiData) return

    setIsValidating(true)
    setApiError(null)
    try {
      const res = await validateExperiment(aiData.experiment_id, {
        primary_metric: [...metrics.primary_metric],
        secondary_metrics: [...metrics.secondary_metrics],
        guardrail_metrics: [...metrics.guardrail_metrics],
      })

      setValidationData(res.data)
      setCurrentStep(2)
    } catch (err: unknown) {
      setApiError(extractErrorMessage(err))
    } finally {
      setIsValidating(false)
    }
  }

  // Step 3: Launch experiment
  const handleLaunch = async (): Promise<void> => {
    if (!aiData) return

    setIsLaunching(true)
    try {
      const res = await launchExperiment(aiData.experiment_id)
      const expId = res.data.id
      navigate(`/experiments/${expId}`)
    } catch (err: unknown) {
      setApiError(extractErrorMessage(err))
    } finally {
      setIsLaunching(false)
    }
  }

  // Back navigation
  const handleBackToStep1 = (): void => {
    setCurrentStep(0)
    setValidationData(null)
  }

  const handleBackToStep2 = (): void => {
    setCurrentStep(1)
    setValidationData(null)
  }

  return (
    <div className="p-6 lg:p-8 min-h-full flex flex-col">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Zap className="w-6 h-6 text-purple-600" aria-hidden="true" />
          New Experiment
        </h1>
        <p className="text-sm text-gray-500 mt-1">Define your business context and let AI design your experiment</p>
      </div>

      {/* Stepper */}
      <Stepper steps={STEPS} currentStep={currentStep} />

      {/* Step 1: Define Context */}
      {currentStep === 0 && (
        <ExperimentForm
          onGenerate={handleGenerate}
          isLoading={isLoading}
          apiError={apiError}
          onApiErrorClear={() => setApiError(null)}
        />
      )}

      {/* Step 2: Review Hypothesis & Metrics */}
      {currentStep === 1 && aiData && lastFormData && (
        <ExperimentResults
          aiData={aiData}
          formData={lastFormData}
          onEditInputs={handleBackToStep1}
          onGenerateConfig={handleGenerateConfig}
          isValidating={isValidating}
        />
      )}

      {/* Step 3: Validate & Launch */}
      {currentStep === 2 && validationData && (
        <ExperimentValidation
          data={validationData}
          onLaunch={handleLaunch}
          isLaunching={isLaunching}
          onBack={handleBackToStep2}
        />
      )}
    </div>
  )
}

// ============ ERROR EXTRACTION HELPER ============

function extractErrorMessage(err: unknown): string {
  const axiosError = err as {
    response?: { data?: { detail?: string | Array<{ msg?: string; message?: string }> } }
    message?: string
  }
  const detail = axiosError?.response?.data?.detail

  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((e) => e.msg ?? e.message ?? JSON.stringify(e)).join(', ')
  }
  return axiosError?.message ?? ERROR_FALLBACK
}
