import { apiRequest } from '../../services/api/client'

export type TemplateStatus = 'ACTIVE' | 'ARCHIVED'
export type ContentTemplate = {
  id: string
  name: string
  description: string | null
  body: string
  placeholders: string[]
  settings: Record<string, unknown>
  status: TemplateStatus
  created_at: string
  updated_at: string
}
export type TemplateInput = { name: string; description: string | null; body: string; settings?: Record<string, unknown> }
export type TemplateList = { items: ContentTemplate[]; total: number; offset: number; limit: number }
export type TemplateFilters = { search?: string; status?: TemplateStatus; offset?: number; limit?: number }

export const templateKeys = { all: ['templates'] as const }
export function listTemplates(filters: TemplateFilters = {}) {
  const params = new URLSearchParams({ offset: String(filters.offset ?? 0), limit: String(filters.limit ?? 20) })
  if (filters.search?.trim()) params.set('search', filters.search.trim())
  if (filters.status) params.set('status', filters.status)
  return apiRequest<TemplateList>(`/templates?${params}`)
}
export const createTemplate = (input: TemplateInput) => apiRequest<ContentTemplate>('/templates', { method: 'POST', body: JSON.stringify(input) })
export const updateTemplate = (id: string, input: TemplateInput) => apiRequest<ContentTemplate>(`/templates/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
export const deleteTemplate = (id: string) => apiRequest<void>(`/templates/${id}`, { method: 'DELETE' })
export const templateAction = (id: string, action: 'archive' | 'restore') => apiRequest<ContentTemplate>(`/templates/${id}/${action}`, { method: 'POST' })
export const renderTemplate = (id: string, values: Record<string, string>) => apiRequest<{ content: string }>(`/templates/${id}/render`, { method: 'POST', body: JSON.stringify({ values }) })
