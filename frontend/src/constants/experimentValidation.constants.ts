// ============ EXPERIMENT VALIDATION CONSTANTS ============

export const PANEL_HEADING = 'Experiment Validation' as const

export const DECISION_LABELS = {
  approve: 'Approved',
  reject: 'Rejected',
} as const

export const DECISION_STYLES = {
  approve: 'bg-green-100 text-green-700 border-green-200',
  reject: 'bg-red-100 text-red-700 border-red-200',
} as const

export const SECTION_LABELS = {
  RULES_EVALUATED: 'Rules Evaluated',
  EXPLANATION: 'Explanation',
  WARNINGS: 'Warnings',
  SUGGESTIONS: 'Suggestions',
} as const

export const EMPTY_STATE = {
  WARNINGS: 'None',
  SUGGESTIONS: 'None',
} as const

export const BUTTON_TEXT = {
  LAUNCH: 'Launch Experiment',
  LAUNCHING: 'Launching...',
} as const
