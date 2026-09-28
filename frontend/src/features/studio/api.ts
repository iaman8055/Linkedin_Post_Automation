import { apiRequest } from '../../services/api/client'

export type GeneratedIdea = {
  title: string; topic: string; category: string; angle: string
  description: string; suggested_hook: string; suggested_format: string
}
export type SavedIdea = GeneratedIdea & { id: string; status: 'NEW' | 'USED' | 'ARCHIVED'; created_at: string }
export type DraftPost = { id: string; title: string | null; content: string; status: string }
export type PlanItem = {
  id: string; position: number; topic: string; post_type: string; title: string
  content: string; scheduled_for: string; post_id: string | null
}
export type ContentPlan = {
  id: string; name: string; audience: string; timezone: string
  status: 'DRAFT' | 'APPROVED'; items: PlanItem[]; created_at: string
}

export const studioKeys = { ideas: ['studio', 'ideas'] as const, plans: ['studio', 'plans'] as const }

export async function generateIdeas(payload: { topics: string[]; audience?: string; count: number }) {
  return apiRequest<{ job_id: string; ideas: GeneratedIdea[] }>('/ideas/generate', {
    method: 'POST', body: JSON.stringify({ ...payload, use_personal_context: false }),
  })
}
export async function saveIdea(payload: GeneratedIdea) {
  return apiRequest<SavedIdea>('/ideas', { method: 'POST', body: JSON.stringify(payload) })
}
export async function listIdeas() {
  return apiRequest<{ items: SavedIdea[]; total: number }>('/ideas')
}
export async function createPostFromIdea(id: string) {
  return apiRequest<DraftPost>(`/ideas/${id}/create-post`, { method: 'POST' })
}
export async function repurposeContent(payload: {
  source_type: string; source_content: string; output_format: string; count: number; tone: string
}) {
  return apiRequest<{ job_id: string; posts: DraftPost[] }>('/ai/repurpose', {
    method: 'POST', body: JSON.stringify(payload),
  })
}
export async function generatePlan(payload: {
  name: string; frequency: string; duration_days: number; topics: string[]; audience: string
  start_date: string; posting_time: string; timezone: string
}) {
  return apiRequest<ContentPlan>('/content-plans/generate', {
    method: 'POST', body: JSON.stringify(payload),
  })
}
export async function listPlans() {
  return apiRequest<{ items: ContentPlan[] }>('/content-plans')
}
export async function approvePlan(id: string, scheduleForAutoPublish: boolean) {
  return apiRequest<{ plan: ContentPlan; created_post_ids: string[]; scheduled_count: number }>(
    `/content-plans/${id}/approve`, {
      method: 'POST', body: JSON.stringify({ schedule_for_auto_publish: scheduleForAutoPublish }),
    },
  )
}
