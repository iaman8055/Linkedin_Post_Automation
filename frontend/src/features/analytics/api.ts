import { apiRequest } from '../../services/api/client'

export type AnalyticsStatus = { connected: boolean; permission_granted: boolean; required_scope: string; collection_available: boolean }
export type PostAnalytics = { id: string; post_id: string; impressions: number | null; likes: number | null; comments: number | null; shares: number | null; engagement_rate: number | null; captured_at: string }
export type AnalyticsPostItem = { post_id: string; title: string | null; content_excerpt: string; published_at: string | null; analytics: PostAnalytics }
export type AnalyticsOverview = { posts: AnalyticsPostItem[]; total_impressions: number | null; total_likes: number | null; total_comments: number | null; total_shares: number | null; average_engagement_rate: number | null }
export type PerformanceInsight = { type: string; title: string; observation: string; evidence: string; sample_size: number }
export type PerformanceInsights = { status: 'ready' | 'insufficient_data'; analyzed_posts: number; minimum_required: number; disclaimer: string; insights: PerformanceInsight[] }
export const analyticsKeys = { status: ['analytics', 'status'] as const, overview: ['analytics', 'overview'] as const, insights: ['analytics', 'insights'] as const }

export const getAnalyticsStatus = () => apiRequest<AnalyticsStatus>('/analytics/status')
export const getAnalyticsOverview = () => apiRequest<AnalyticsOverview>('/analytics/overview')
export const getPerformanceInsights = () => apiRequest<PerformanceInsights>('/analytics/insights')
export const refreshPostAnalytics = (postId: string) => apiRequest<PostAnalytics>(`/analytics/posts/${postId}/refresh`, { method: 'POST' })
