import { apiRequest } from '../../services/api/client'

export type ResearchSource = {
  id: string
  url: string
  title: string
  retrieved_at: string
  summary: string | null
  relevant_content: string | null
  source_metadata: Record<string, unknown>
}
export type ResearchStatus = { selected_provider: string | null; configured: boolean }
export type ResearchSearchInput = { query: string; topic: 'general' | 'news'; max_results: number; time_range: 'day' | 'week' | 'month' | 'year' | null }
export type ResearchSearchResult = { answer: string | null; provider: string; sources: ResearchSource[] }
export type ResearchSourceList = { items: ResearchSource[]; total: number; offset: number; limit: number }
export const researchKeys = { status: ['research', 'status'] as const, sources: ['research', 'sources'] as const }

export const getResearchStatus = () => apiRequest<ResearchStatus>('/research/status')
export const searchResearch = (input: ResearchSearchInput) => apiRequest<ResearchSearchResult>('/research/search', { method: 'POST', body: JSON.stringify(input) })
export const listResearchSources = () => apiRequest<ResearchSourceList>('/research/sources?limit=50')
export const deleteResearchSource = (id: string) => apiRequest<void>(`/research/sources/${id}`, { method: 'DELETE' })
