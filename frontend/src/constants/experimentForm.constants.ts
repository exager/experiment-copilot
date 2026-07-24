// ============ EXPERIMENT FORM CONSTANTS ============

// --- Labels ---
export const LABELS = {
  BUSINESS_GOAL: 'Business Goal',
  WEBSITE_URL: 'Website URL',
  FEATURE_PAGE: 'Feature / Page',
  USER_FLOW: 'Current User Flow',
  PAIN_POINT: 'Pain Point / Problem Statement',
} as const

// --- Placeholders ---
export const PLACEHOLDERS = {
  BUSINESS_GOAL: 'Increase checkout conversion by 15%',
  WEBSITE_URL: 'https://www.shopmax.com',
  USER_FLOW:
    'User adds items to cart → Proceeds to checkout → Enters shipping details → Enters payment details → Sees order summary → Places order',
  PAIN_POINT:
    'Users abandon checkout during payment due to unclear error messages and limited payment options.',
} as const

// --- Hints ---
export const HINTS = {
  BUSINESS_GOAL: 'Min 10 characters. E.g., Increase signup rate by 20%',
  WEBSITE_URL: 'Must start with https:// or http://',
  USER_FLOW: 'Min 20 characters. Describe step-by-step user journey',
  PAIN_POINT: 'Min 15 characters. What problem are users facing?',
} as const

// --- Validation Error Messages ---
export const VALIDATION_MESSAGES = {
  BUSINESS_GOAL_REQUIRED: 'Business Goal is required',
  BUSINESS_GOAL_MIN_LENGTH: 'Business Goal must be at least 10 characters',
  WEBSITE_URL_REQUIRED: 'Website URL is required',
  WEBSITE_URL_INVALID: 'Enter a valid URL (e.g., https://example.com)',
  USER_FLOW_REQUIRED: 'Current User Flow is required',
  USER_FLOW_MIN_LENGTH: 'Describe the user flow in at least 20 characters',
  PAIN_POINT_REQUIRED: 'Pain Point is required',
  PAIN_POINT_MIN_LENGTH: 'Describe the pain point in at least 15 characters',
  INVALID_FORMAT: 'Invalid format',
} as const

// --- Button Text ---
export const BUTTON_TEXT = {
  GENERATING: 'Generating...',
  GENERATE: 'Generate Hypothesis',
} as const

// --- Feature/Page Dropdown Options ---
export const FEATURE_OPTIONS = [
  { value: 'checkout', label: 'Checkout' },
  { value: 'cart', label: 'Cart' },
  { value: 'product_page', label: 'Product Page' },
  { value: 'signup', label: 'Signup' },
  { value: 'search', label: 'Search' },
  { value: 'homepage', label: 'Homepage' },
  { value: 'onboarding', label: 'Onboarding' },
] as const

// --- Validation Rules ---
export const URL_PATTERN = /^https?:\/\/.+\..+/

export const VALIDATION_RULES = {
  business_goal: {
    required: VALIDATION_MESSAGES.BUSINESS_GOAL_REQUIRED,
    minLength: 10,
    minLengthMsg: VALIDATION_MESSAGES.BUSINESS_GOAL_MIN_LENGTH,
  },
  website_url: {
    required: VALIDATION_MESSAGES.WEBSITE_URL_REQUIRED,
    pattern: URL_PATTERN,
    patternMsg: VALIDATION_MESSAGES.WEBSITE_URL_INVALID,
  },
  user_flow: {
    required: VALIDATION_MESSAGES.USER_FLOW_REQUIRED,
    minLength: 20,
    minLengthMsg: VALIDATION_MESSAGES.USER_FLOW_MIN_LENGTH,
  },
  pain_point: {
    required: VALIDATION_MESSAGES.PAIN_POINT_REQUIRED,
    minLength: 15,
    minLengthMsg: VALIDATION_MESSAGES.PAIN_POINT_MIN_LENGTH,
  },
} as const

// --- Default Form State ---
export const DEFAULT_FORM_DATA = {
  business_goal: '',
  website_url: '',
  feature_page: 'checkout',
  user_flow: '',
  pain_point: '',
} as const
