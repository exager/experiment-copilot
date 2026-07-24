// ============ EXPERIMENT RESULTS CONSTANTS ============

// --- Button Text ---
export const BUTTON_TEXT = {
  EDIT_INPUTS: 'Edit Inputs',
  GENERATE_CONFIG: 'Generate Experiment Configuration',
} as const

// --- Panel Headings ---
export const PANEL_HEADINGS = {
  AI_UNDERSTANDING: 'AI Understanding',
  SUGGESTED_METRICS: 'Suggested Success Metrics',
  AI_STATUS: 'AI Status',
} as const

// --- Panel Descriptions ---
export const PANEL_DESCRIPTIONS = {
  AI_UNDERSTANDING: 'Based on the provided business context, the AI has interpreted the experiment objective.',
  SUGGESTED_METRICS: 'AI suggested metrics based on your experiment context.',
} as const

// --- Badges ---
export const BADGES = {
  AI_GENERATED: 'AI Generated',
} as const

// --- Metric Section Labels ---
export const METRIC_LABELS = {
  PRIMARY: 'Primary Metric',
  SECONDARY: 'Secondary Metrics',
  GUARDRAIL: 'Guardrail Metrics',
} as const

// --- AI Understanding Card Items ---
export const UNDERSTANDING_CARD_LABELS = {
  EXPERIMENT: 'Experiment Name',
  HYPOTHESIS: 'Hypothesis',
  PROBLEM: 'Problem Statement',
  TARGET_USERS: 'Target Users',
  EXPERIMENT_AREA: 'Experiment Area',
  CONFIDENCE: 'AI Confidence Score',
} as const

export const UNDERSTANDING_CARD_ICONS = {
  EXPERIMENT: '🧪',
  HYPOTHESIS: '💡',
  PROBLEM: '⚠️',
  TARGET_USERS: '👥',
  EXPERIMENT_AREA: '🎯',
  CONFIDENCE: '📊',
} as const

export const UNDERSTANDING_CARD_COLORS = {
  EXPERIMENT: 'bg-purple-50 border-purple-100',
  HYPOTHESIS: 'bg-blue-50 border-blue-100',
  PROBLEM: 'bg-red-50 border-red-100',
  TARGET_USERS: 'bg-indigo-50 border-indigo-100',
  EXPERIMENT_AREA: 'bg-green-50 border-green-100',
  CONFIDENCE: 'bg-emerald-50 border-emerald-100',
} as const

// --- AI Status Steps ---
export const AI_STATUS_STEPS = [
  { label: 'Business Goal Understood', completed: true },
  { label: 'User Flow Analysed', completed: true },
  { label: 'Pain Point Identified', completed: true },
  { label: 'Metrics Suggested', completed: true },
] as const

export const STATUS_TEXT = {
  LABEL: 'Status',
  READY: 'Ready to Generate Experiment',
} as const

// --- Default Fallback Values ---
export const DEFAULTS = {
  CONFIDENCE_UNKNOWN: 'N/A',
} as const

// --- Navigation Routes ---
export const ROUTES = {
  RUNNING: '/running',
} as const
