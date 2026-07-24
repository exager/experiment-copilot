import { create } from 'zustand'
import type { Experiment, MetricsData, Recommendation, AIInsights } from '../types'
import * as api from '../services/api'

interface ExperimentState {
  experiments: Experiment[]
  currentExperiment: Experiment | null
  metrics: MetricsData | null
  insights: AIInsights | null
  recommendation: Recommendation | null
  isLoading: boolean
  error: string | null

  fetchExperiments: () => Promise<void>
  fetchExperiment: (id: string) => Promise<void>
  fetchMetrics: (id: string) => Promise<void>
  fetchInsights: (id: string) => Promise<void>
  fetchRecommendation: (id: string) => Promise<void>
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useExperimentStore = create<ExperimentState>((set) => ({
  experiments: [],
  currentExperiment: null,
  metrics: null,
  insights: null,
  recommendation: null,
  isLoading: false,
  error: null,

  fetchExperiments: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.getExperiments()
      set({ experiments: res.data, isLoading: false })
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
    }
  },

  fetchExperiment: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.getExperiment(id)
      set({ currentExperiment: res.data, isLoading: false })
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
    }
  },

  fetchMetrics: async (id: string) => {
    try {
      const res = await api.getMetrics(id)
      set({ metrics: res.data })
    } catch (err: any) {
      set({ error: err.message })
    }
  },

  fetchInsights: async (id: string) => {
    try {
      const res = await api.analyzeExperiment(id)
      set({ insights: res.data })
    } catch (err: any) {
      set({ error: err.message })
    }
  },

  fetchRecommendation: async (id: string) => {
    try {
      const res = await api.getRecommendation(id)
      set({ recommendation: res.data })
    } catch (err: any) {
      set({ error: err.message })
    }
  },

  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}))
