import { CheckCircle2 } from 'lucide-react'

export interface StepConfig {
  readonly label: string
  readonly icon: string
}

interface StepperProps {
  readonly steps: readonly StepConfig[]
  readonly currentStep: number
}

// ============ STYLE HELPERS ============

const getCircleStyles = (isCompleted: boolean, isActive: boolean): string => {
  if (isCompleted) return 'bg-green-100 text-green-600 ring-2 ring-green-200'
  if (isActive) return 'bg-purple-600 text-white ring-4 ring-purple-100 shadow-md'
  return 'bg-gray-100 text-gray-400'
}

const getLabelStyles = (isCompleted: boolean, isActive: boolean): string => {
  if (isCompleted) return 'text-green-600'
  if (isActive) return 'text-purple-700 font-semibold'
  return 'text-gray-400'
}

// ============ COMPONENT ============

export default function Stepper({ steps, currentStep }: Readonly<StepperProps>) {
  return (
    <div className="flex items-center justify-center gap-0 mb-8">
      {steps.map((step, index) => {
        const isCompleted = index < currentStep
        const isActive = index === currentStep
        const isLast = index === steps.length - 1

        return (
          <div key={step.label} className="flex items-center">
            {/* Step circle + label */}
            <div className="flex flex-col items-center">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${getCircleStyles(isCompleted, isActive)}`}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-5 h-5" aria-hidden="true" />
                ) : (
                  <span>{step.icon}</span>
                )}
              </div>
              <span
                className={`mt-2 text-xs font-medium whitespace-nowrap transition-colors ${getLabelStyles(isCompleted, isActive)}`}
              >
                {step.label}
              </span>
            </div>

            {/* Connector line */}
            {!isLast && (
              <div
                className={`w-20 lg:w-32 h-0.5 mx-3 mt-[-18px] transition-colors duration-300 rounded-full ${
                  isCompleted ? 'bg-green-300' : 'bg-gray-200'
                }`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
