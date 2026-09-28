import { apiRequest } from '../../services/api/client'

export type WritingProfile = {
  id: string
  name: string
  tone: string | null
  sentence_style: string | null
  language: string
  emoji_preference: string | null
  paragraph_length: string | null
  technical_depth: string | null
  cta_preference: string | null
  preferred_vocabulary: string[]
  additional_guidance: Record<string, unknown>
  is_default: boolean
}

export type WritingProfileInput = Omit<WritingProfile, 'id'>
export type WritingProfileList = { items: WritingProfile[]; total: number }
export const writingProfileKeys = { all: ['writing-profiles'] as const }

export const listWritingProfiles = () => apiRequest<WritingProfileList>('/writing-profiles')
export const createWritingProfile = (input: WritingProfileInput) => apiRequest<WritingProfile>('/writing-profiles', { method: 'POST', body: JSON.stringify(input) })
export const updateWritingProfile = (id: string, input: Partial<WritingProfileInput>) => apiRequest<WritingProfile>(`/writing-profiles/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
export const deleteWritingProfile = (id: string) => apiRequest<void>(`/writing-profiles/${id}`, { method: 'DELETE' })

export type StyleAnalysis = {
  average_sentence_length: number; paragraph_length: string; formality: string; tone: string
  emoji_frequency: string; hashtag_frequency: string; storytelling: string; technical_depth: string
  cta_style: string; opening_style: string; vocabulary_patterns: string[]
}
export type StyleAnalysisResult = {
  job_id: string; sample_size: number; disclaimer: string; analysis: StyleAnalysis
  suggested_profile: WritingProfileInput
}
export const analyzeWritingStyle = (postIds: string[] = []) => apiRequest<StyleAnalysisResult>('/writing-profiles/analyze', { method: 'POST', body: JSON.stringify({ post_ids: postIds }) })
