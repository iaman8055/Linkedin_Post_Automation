import { apiRequest } from '../../services/api/client'

export type CommentSuggestion = { style: string; response: string }
export type ExperimentPost = { id: string; title: string | null; content: string; status: string }
export type Experiment = {
  id: string; name: string; hypothesis: string | null; comparison_axis: string
  version_a: ExperimentPost; version_b: ExperimentPost; created_at: string
}
export type ExperimentComparison = {
  experiment_id: string; status: 'awaiting_publication' | 'awaiting_analytics' | 'ready'
  version_a: { impressions: number | null; reactions: number | null; comments: number | null; shares: number | null; engagement_rate: number | null } | null
  version_b: { impressions: number | null; reactions: number | null; comments: number | null; shares: number | null; engagement_rate: number | null } | null
  better_version: 'A' | 'B' | null; explanation: string
}

export const engagementKeys = { experiments: ['engagement', 'experiments'] as const }
export const generateCommentResponses = (comment: string, postContext?: string) => apiRequest<{ job_id: string; suggestions: CommentSuggestion[]; disclaimer: string }>('/comments/generate-response', { method: 'POST', body: JSON.stringify({ comment, post_context: postContext || null }) })
export const listExperiments = () => apiRequest<Experiment[]>('/experiments')
export const createExperiment = (input: { source_post_id: string; name: string; hypothesis?: string; comparison_axis: string }) => apiRequest<Experiment>('/experiments', { method: 'POST', body: JSON.stringify(input) })
export const compareExperiment = (id: string) => apiRequest<ExperimentComparison>(`/experiments/${id}/comparison`)
