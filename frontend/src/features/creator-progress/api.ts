import { apiRequest } from '../../services/api/client'

export type Achievement = { code: string; title: string; description: string; unlocked_at: string }
export type CreatorProgress = {
  creator_level: number; level_points: number; next_level_points: number
  posts_published: number; drafts_created: number; ideas_generated: number
  total_impressions: number | null; current_streak: number
  monthly_post_target: number; monthly_posts_published: number; monthly_goal_percent: number
  achievements: Achievement[]
}
export const creatorProgressKeys = { all: ['creator-progress'] as const }
export const getCreatorProgress = () => apiRequest<CreatorProgress>('/creator-progress')
export const updateCreatorGoal = (monthly_post_target: number) => apiRequest<CreatorProgress>('/creator-progress/goal', { method: 'PATCH', body: JSON.stringify({ monthly_post_target }) })
