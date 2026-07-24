import { type ChangeEvent, useId, useState } from 'react'
import { Sparkles, Globe, Target, GitBranch, AlertTriangle } from 'lucide-react'
import type { ExperimentFormData, ExperimentFormProps, InputFieldProps, TextAreaFieldProps } from '../../types'
import {
  LABELS,
  PLACEHOLDERS,
  HINTS,
  BUTTON_TEXT,
  FEATURE_OPTIONS,
  VALIDATION_RULES,
  VALIDATION_MESSAGES,
  DEFAULT_FORM_DATA,
} from '../../constants/experimentForm.constants'

// ============ VALIDATION ============

const validateForm = (formData: ExperimentFormData): Record<string, string> => {
  const errors: Record<string, string> = {}

  for (const [field, rules] of Object.entries(VALIDATION_RULES)) {
    const value = formData[field as keyof ExperimentFormData].trim()

    if (!value) {
      errors[field] = rules.required
    } else if ('pattern' in rules && rules.pattern && !rules.pattern.test(value)) {
      errors[field] = rules.patternMsg ?? VALIDATION_MESSAGES.INVALID_FORMAT
    } else if ('minLength' in rules && rules.minLength && value.length < rules.minLength) {
      errors[field] = rules.minLengthMsg ?? `Must be at least ${rules.minLength} characters`
    }
  }

  return errors
}

// ============ MAIN COMPONENT ============

export default function ExperimentForm({
  onGenerate,
  isLoading,
  apiError,
  onApiErrorClear,
}: Readonly<ExperimentFormProps>) {
  const [formData, setFormData] = useState<ExperimentFormData>({ ...DEFAULT_FORM_DATA })
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const featureSelectId = useId()

  const handleChange = (field: keyof ExperimentFormData, value: string): void => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    setFieldErrors((prev) => {
      const { [field]: _, ...rest } = prev // NOSONAR - destructuring to omit key
      return rest
    })
    onApiErrorClear()
  }

  const handleGenerate = async (): Promise<void> => {
    const errors = validateForm(formData)

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors)
      return
    }

    await onGenerate(formData)
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 lg:p-8">
      <div className="space-y-5">
        {/* Row 1: Business Goal, Website URL, Feature/Page */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <InputField
            label={LABELS.BUSINESS_GOAL}
            required
            icon={<Target className="w-4 h-4" />}
            value={formData.business_goal}
            onChange={(v) => handleChange('business_goal', v)}
            placeholder={PLACEHOLDERS.BUSINESS_GOAL}
            error={fieldErrors.business_goal}
            hint={HINTS.BUSINESS_GOAL}
          />
          <InputField
            label={LABELS.WEBSITE_URL}
            required
            icon={<Globe className="w-4 h-4" />}
            value={formData.website_url}
            onChange={(v) => handleChange('website_url', v)}
            placeholder={PLACEHOLDERS.WEBSITE_URL}
            error={fieldErrors.website_url}
            hint={HINTS.WEBSITE_URL}
          />
          <div>
            <label htmlFor={featureSelectId} className="text-sm font-medium text-gray-700">
              {LABELS.FEATURE_PAGE} <span className="text-red-500">*</span>
            </label>
            <div className="mt-1.5 relative group">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-purple-500 transition-colors">
                <GitBranch className="w-4 h-4" />
              </span>
              <select
                id={featureSelectId}
                value={formData.feature_page}
                onChange={(e: ChangeEvent<HTMLSelectElement>) => handleChange('feature_page', e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 border border-gray-200 rounded-xl text-[13px] bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-400 transition-all appearance-none cursor-pointer"
              >
                {FEATURE_OPTIONS.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            {fieldErrors.feature_page && (
              <p className="text-xs text-red-500 mt-1">{fieldErrors.feature_page}</p>
            )}
          </div>
        </div>

        {/* Row 2: User Flow, Pain Point */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextAreaField
            label={LABELS.USER_FLOW}
            required
            icon={<GitBranch className="w-4 h-4" />}
            value={formData.user_flow}
            onChange={(v) => handleChange('user_flow', v)}
            placeholder={PLACEHOLDERS.USER_FLOW}
            error={fieldErrors.user_flow}
            hint={HINTS.USER_FLOW}
          />
          <TextAreaField
            label={LABELS.PAIN_POINT}
            required
            icon={<AlertTriangle className="w-4 h-4" />}
            value={formData.pain_point}
            onChange={(v) => handleChange('pain_point', v)}
            placeholder={PLACEHOLDERS.PAIN_POINT}
            error={fieldErrors.pain_point}
            hint={HINTS.PAIN_POINT}
          />
        </div>

        {/* API Error */}
        {apiError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-center" role="alert">
            <p className="text-sm text-red-600">{apiError}</p>
          </div>
        )}

        {/* Generate Button */}
        <div className="flex justify-center pt-4">
          <button
            type="button"
            onClick={handleGenerate}
            disabled={isLoading}
            className="btn-glow flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:opacity-60 disabled:animate-none text-white px-8 py-3.5 rounded-xl font-semibold text-sm transition-all transform hover:scale-[1.02] active:scale-95"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                {BUTTON_TEXT.GENERATING}
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                {BUTTON_TEXT.GENERATE}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

// ============ REUSABLE INPUT COMPONENTS ============

function InputField({
  label,
  required = false,
  icon,
  value,
  onChange,
  placeholder,
  error,
  hint,
}: Readonly<InputFieldProps>) {
  const inputId = useId()
  const hintId = useId()

  return (
    <div>
      <label htmlFor={inputId} className="text-sm font-medium text-gray-700 flex items-center gap-1">
        {label} {required && <span className="text-red-500">*</span>}
        {hint && (
          <span className="relative group">
            <svg
              className="w-3.5 h-3.5 text-gray-400 cursor-help"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4M12 8h.01" />
            </svg>
            <span
              id={hintId}
              role="tooltip"
              className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-gray-800 text-white text-[11px] rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10"
            >
              {hint}
            </span>
          </span>
        )}
      </label>
      <div className={`mt-1.5 relative group ${error ? 'ring-2 ring-red-200 rounded-xl' : ''}`}>
        <span
          className={`absolute left-3 top-1/2 -translate-y-1/2 transition-colors ${error ? 'text-red-400' : 'text-gray-400 group-focus-within:text-purple-500'}`}
          aria-hidden="true"
        >
          {icon}
        </span>
        <input
          id={inputId}
          type="text"
          value={value}
          onChange={(e: ChangeEvent<HTMLInputElement>) => onChange(e.target.value)}
          placeholder={placeholder}
          aria-describedby={hint ? hintId : undefined}
          aria-invalid={Boolean(error)}
          className={`w-full pl-9 pr-3 py-2.5 border rounded-xl text-[13px] bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-400 transition-all ${error ? 'border-red-300 bg-red-50/50' : 'border-gray-200'}`}
        />
      </div>
      {error && <p className="text-xs text-red-500 mt-1" role="alert">{error}</p>}
    </div>
  )
}

function TextAreaField({
  label,
  required = false,
  icon,
  value,
  onChange,
  placeholder,
  error,
  hint,
}: Readonly<TextAreaFieldProps>) {
  const textareaId = useId()
  const hintId = useId()

  return (
    <div>
      <label htmlFor={textareaId} className="text-sm font-medium text-gray-700 flex items-center gap-1">
        {label} {required && <span className="text-red-500">*</span>}
        {hint && (
          <span className="relative group">
            <svg
              className="w-3.5 h-3.5 text-gray-400 cursor-help"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4M12 8h.01" />
            </svg>
            <span
              id={hintId}
              role="tooltip"
              className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-gray-800 text-white text-[11px] rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10"
            >
              {hint}
            </span>
          </span>
        )}
      </label>
      <div className={`mt-1.5 flex items-start gap-2 border rounded-xl px-3 py-3 transition-all group ${error ? 'border-red-300 bg-red-50/50 ring-2 ring-red-200' : 'border-gray-200 bg-gray-50 focus-within:bg-white focus-within:ring-2 focus-within:ring-purple-500/20 focus-within:border-purple-400'}`}>
        <span
          className={`mt-[6px] transition-colors flex-shrink-0 ${error ? 'text-red-400' : 'text-gray-400 group-focus-within:text-purple-500'}`}
          aria-hidden="true"
        >
          {icon}
        </span>
        <textarea
          id={textareaId}
          value={value}
          onChange={(e: ChangeEvent<HTMLTextAreaElement>) => onChange(e.target.value)}
          placeholder={placeholder}
          rows={3}
          aria-describedby={hint ? hintId : undefined}
          aria-invalid={Boolean(error)}
          className="w-full text-sm bg-transparent focus:outline-none resize-none leading-relaxed"
        />
      </div>
      {error && <p className="text-xs text-red-500 mt-1" role="alert">{error}</p>}
    </div>
  )
}
