import { apiRequest } from '../../services/api/client'
import type { PostList } from '../posts/api'

export type CampaignStatus = 'DRAFT' | 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'CANCELLED'
export type ApprovalMode = 'MANUAL' | 'AUTOMATIC'

export type Campaign = {
  id: string
  name: string
  topic: string
  description: string | null
  duration_days: number | null
  status: CampaignStatus
  approval_mode: ApprovalMode
  default_posting_time: string | null
  timezone: string
  writing_profile_id: string | null
  content_strategy: Record<string, unknown> | null
  post_count: number
  created_at: string
  updated_at: string
}

export type CampaignInput = {
  name: string
  topic: string
  description: string | null
  duration_days: number | null
  approval_mode: ApprovalMode
  default_posting_time: string | null
  timezone: string
}

export type CampaignList = { items: Campaign[]; total: number; offset: number; limit: number }
export const campaignKeys = {
  all: ['campaigns'] as const,
  detail: (id: string) => ['campaigns', id] as const,
  posts: (id: string) => ['campaigns', id, 'posts'] as const,
}

export const listCampaigns = (filters: { status?: CampaignStatus; limit?: number; offset?: number } = {}) => {
  const params = new URLSearchParams({ limit: String(filters.limit ?? 20), offset: String(filters.offset ?? 0) })
  if (filters.status) params.set('status', filters.status)
  return apiRequest<CampaignList>(`/campaigns?${params}`)
}
export const getCampaign = (id: string) => apiRequest<Campaign>(`/campaigns/${id}`)
export const createCampaign = (input: CampaignInput) =>
  apiRequest<Campaign>('/campaigns', { method: 'POST', body: JSON.stringify(input) })
export const updateCampaign = (id: string, input: CampaignInput) =>
  apiRequest<Campaign>(`/campaigns/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
export const deleteCampaign = (id: string) =>
  apiRequest<void>(`/campaigns/${id}`, { method: 'DELETE' })
export const transitionCampaign = (id: string, status: CampaignStatus) =>
  apiRequest<Campaign>(`/campaigns/${id}/transition`, {
    method: 'POST', body: JSON.stringify({ status }),
  })
export const listCampaignPosts = (id: string) =>
  apiRequest<PostList>(`/campaigns/${id}/posts`)
export const addCampaignPost = (campaignId: string, postId: string) =>
  apiRequest<Campaign>(`/campaigns/${campaignId}/posts/${postId}`, { method: 'POST' })
export const removeCampaignPost = (campaignId: string, postId: string) =>
  apiRequest<Campaign>(`/campaigns/${campaignId}/posts/${postId}`, { method: 'DELETE' })
