import axios from 'axios'
import { mockData } from '../mocks'

// ============ TOGGLE: Set to false when real backend is ready ============
const USE_MOCK = false
// ===========================================================================

const API_BASE = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Simulate network delay for mocks
const mockDelay = (ms = 1500) => new Promise(resolve => setTimeout(resolve, ms))

// ============ HEALTH ============
export const healthCheck = () => {
  if (USE_MOCK) return Promise.resolve({ data: { status: 'ok' } })
  return api.get('/health')
}

// ============ GET /catalog (Static — call once and cache) ============
export const getCatalog = async () => {
  if (USE_MOCK) {
    await mockDelay(300)
    return { data: { primary_metrics: ['checkout_conversion'], secondary_metrics: ['average_order_value'], guardrail_metrics: ['bounce_rate', 'error_rate'] } }
  }
  return api.get('/catalog')
}

// ============ POST /context (Screen 1: New Experiment) ============
export const createExperimentContext = async (data: {
  business_goal: string
  website: string
  current_flow: string
  feature: string
  pain_point: string
}) => {
  if (USE_MOCK) {
    await mockDelay(1800)
    return { data: mockData.contextResponse }
  }
  return api.post('/context', data)
}

// ============ POST /context/:context_id/hypothesis (Screen 1: Generate hypothesis after context) ============
export const generateHypothesis = async (contextId: number) => {
  if (USE_MOCK) {
    await mockDelay(1500)
    return { data: mockData.contextResponse }
  }
  return api.post(`/context/${contextId}/hypothesis`)
}

// ============ POST /experiments/:id/validate (Screen 1: Validate with selected metrics) ============
export const validateExperiment = async (
  experimentId: number,
  data: {
    primary_metric: Array<{ id: string; label: string; selected: boolean }>
    secondary_metrics: Array<{ id: string; label: string; selected: boolean }>
    guardrail_metrics: Array<{ id: string; label: string; selected: boolean }>
  },
) => {
  if (USE_MOCK) {
    await mockDelay(1000)
    return { data: mockData.validateResponse }
  }
  return api.post(`/experiments/${experimentId}/validate`, data)
}

// ============ POST /experiments/:id/launch (Launch experiment) ============
export const launchExperiment = async (experimentId: number) => {
  if (USE_MOCK) {
    await mockDelay(800)
    return { data: { experiment_id: `exp_${experimentId}`, status: 'running', started_at: new Date().toISOString() } }
  }
  return api.post(`/experiments/${experimentId}/launch`)
}

// ============ POST /experiment/start (Start running — legacy) ============
export const startExperiment = async (experimentId: number) => {
  if (USE_MOCK) {
    await mockDelay(800)
    return { data: { ...mockData.contextResponse, status: 'running', started_at: new Date().toISOString() } }
  }
  return api.post('/experiment/start', { experiment_id: experimentId })
}

// ============ GET /experiment/:id/metrics (Screen 2: Live Dashboard — poll) ============
export const getExperimentMetrics = async (experimentId: number | string) => {
  if (USE_MOCK) {
    await mockDelay(300)
    return { data: mockData.metricsResponse }
  }
  return api.get(`/experiment/${experimentId}/metrics`)
}

// ============ POST /report/:id (Screen 3: Executive Report) ============
export const generateReport = async (experimentId: number | string) => {
  if (USE_MOCK) {
    await mockDelay(1200)
    return { data: mockData.reportResponse }
  }
  return api.post(`/report/${experimentId}`)
}

export default api
