import { apiRequest } from '../../services/api/client'

export type PostStatus =
  | 'DRAFT'
  | 'APPROVED'
  | 'SCHEDULED'
  | 'PUBLISHING'
  | 'PUBLISHED'
  | 'FAILED'
  | 'CANCELLED'

export type Post = {
  id: string
  campaign_id: string | null
  title: string | null
  content: string
  language: string
  status: PostStatus
  created_at: string
  updated_at: string
  approved_at: string | null
  published_at: string | null
}

export type PostInput = { title?: string | null; content: string; language: string }
export type PostList = { items: Post[]; total: number; offset: number; limit: number }
export type GeneratePostsInput = {
  topic: string
  subject: string
  audience: string
  tone: string
  language: string
  length: 'short' | 'medium' | 'long'
  call_to_action: string | null
  include_hashtags: boolean
  hashtag_count: number
  number_of_posts: number
  writing_profile_id: string | null
  research_source_ids: string[]
}
export type GeneratePostsResult = { job_id: string; posts: Post[] }
export type QualityIssue = { type: string; severity: 'low' | 'medium' | 'high'; message: string; suggestion: string }
export type QualityCheck = { post_id: string; status: 'pass' | 'warning' | 'fail'; issues: QualityIssue[]; ai_review_performed: boolean; job_id: string | null }
export type PostMedia = { id: string; post_id: string; media_type: 'IMAGE' | 'VIDEO' | 'DOCUMENT'; mime_type: string; size_bytes: number | null; position: number; metadata_json: { filename?: string }; created_at: string }
export type PostMediaList = { items: PostMedia[] }

export const postKeys = { all: ['posts'] as const, detail: (id: string) => ['posts', id] as const }

export type PostFilters = { search?: string; status?: PostStatus; offset?: number; limit?: number }
export function listPosts(filters: PostFilters = {}) {
  const params = new URLSearchParams({ limit: String(filters.limit ?? 20), offset: String(filters.offset ?? 0) })
  if (filters.search?.trim()) params.set('search', filters.search.trim())
  if (filters.status) params.set('status', filters.status)
  return apiRequest<PostList>(`/posts?${params}`)
}

export function getPost(id: string) {
  return apiRequest<Post>(`/posts/${id}`)
}

export function createPost(input: PostInput) {
  return apiRequest<Post>('/posts', { method: 'POST', body: JSON.stringify(input) })
}

export function updatePost(id: string, input: PostInput) {
  return apiRequest<Post>(`/posts/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
}

export function deletePost(id: string) {
  return apiRequest<void>(`/posts/${id}`, { method: 'DELETE' })
}

export function approvePost(id: string) {
  return apiRequest<Post>(`/posts/${id}/approve`, { method: 'POST' })
}

export function returnPostToDraft(id: string) {
  return apiRequest<Post>(`/posts/${id}/return-to-draft`, { method: 'POST' })
}

export function generatePosts(input: GeneratePostsInput) {
  return apiRequest<GeneratePostsResult>('/ai/posts/generate', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function checkPostQuality(id: string) {
  return apiRequest<QualityCheck>(`/posts/${id}/quality-check`, { method: 'POST' })
}

export function listPostMedia(postId: string) {
  return apiRequest<PostMediaList>(`/posts/${postId}/media`)
}

export function uploadPostMedia(postId: string, file: File) {
  const params = new URLSearchParams({ filename: file.name })
  return apiRequest<PostMedia>(`/posts/${postId}/media?${params}`, {
    method: 'POST', headers: { 'Content-Type': file.type }, body: file,
  })
}

export function deletePostMedia(mediaId: string) {
  return apiRequest<void>(`/media/${mediaId}`, { method: 'DELETE' })
}
