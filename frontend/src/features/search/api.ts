import { apiRequest } from '../../services/api/client'

export type SearchEntityType = 'all' | 'post' | 'idea' | 'knowledge' | 'template'
export type SearchResult = {
  id: string
  entity_type: Exclude<SearchEntityType, 'all'>
  title: string
  excerpt: string
  status: string | null
  topic: string | null
  tags: string[]
  updated_at: string
  scheduled_for: string | null
  url: string
}
export type SearchResponse = { items: SearchResult[]; total: number; query: string | null }
export type SearchFilters = {
  query?: string
  entityType?: SearchEntityType
  status?: string
  topic?: string
  tag?: string
  dateFrom?: string
  dateTo?: string
}

export const searchKeys = { results: (filters: SearchFilters) => ['search', filters] as const }

export function globalSearch(filters: SearchFilters) {
  const params = new URLSearchParams({ limit: '50' })
  if (filters.query?.trim()) params.set('q', filters.query.trim())
  if (filters.entityType && filters.entityType !== 'all') params.set('entity_type', filters.entityType)
  if (filters.status) params.set('status', filters.status)
  if (filters.topic?.trim()) params.set('topic', filters.topic.trim())
  if (filters.tag?.trim()) params.set('tag', filters.tag.trim())
  if (filters.dateFrom) params.set('date_from', filters.dateFrom)
  if (filters.dateTo) params.set('date_to', filters.dateTo)
  return apiRequest<SearchResponse>(`/search?${params}`)
}
