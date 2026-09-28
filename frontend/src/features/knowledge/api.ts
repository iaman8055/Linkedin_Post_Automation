import { apiRequest } from '../../services/api/client'

export type KnowledgeCategory = 'project' | 'resume' | 'skill' | 'experience' | 'article' | 'note' | 'previous_content' | 'achievement' | 'technical_knowledge'
export type KnowledgeItem = {
  id: string; category: KnowledgeCategory; title: string; content: string
  tags: string[]; is_private: boolean; created_at: string; updated_at: string
}
export type KnowledgeInput = Omit<KnowledgeItem, 'id' | 'created_at' | 'updated_at'>
export const knowledgeKeys = { all: ['knowledge'] as const }
export const listKnowledge = () => apiRequest<{ items: KnowledgeItem[]; total: number }>('/knowledge')
export const createKnowledge = (input: KnowledgeInput) => apiRequest<KnowledgeItem>('/knowledge', { method: 'POST', body: JSON.stringify(input) })
export const updateKnowledge = (id: string, input: Partial<KnowledgeInput>) => apiRequest<KnowledgeItem>(`/knowledge/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
export const deleteKnowledge = (id: string) => apiRequest<void>(`/knowledge/${id}`, { method: 'DELETE' })
