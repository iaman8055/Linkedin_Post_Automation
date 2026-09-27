import { apiRequest } from '../../services/api/client'

export type LinkedInAccount = { id: string; linkedin_member_id: string; display_name: string | null; profile_image_url: string | null; token_expires_at: string | null; scopes: string; is_connected: boolean }
export type LinkedInStatus = { accounts: LinkedInAccount[] }
export const linkedinKeys = { status: ['linkedin', 'status'] as const }
export const getLinkedInStatus = () => apiRequest<LinkedInStatus>('/linkedin/status')
export const getLinkedInConnectUrl = () => apiRequest<{ authorization_url: string }>('/linkedin/connect')
export const completeLinkedInConnection = (code: string, state: string) => apiRequest<LinkedInAccount>(`/linkedin/callback?${new URLSearchParams({ code, state })}`)
export const disconnectLinkedIn = (id: string) => apiRequest<void>(`/linkedin/${id}`, { method: 'DELETE' })
export const publishLinkedInTestPost = (id: string, commentary: string, key: string) => apiRequest<{ id: string; linkedin_post_id: string; status: string; published_at: string }>(`/linkedin/${id}/test-post`, { method: 'POST', headers: { 'Idempotency-Key': key }, body: JSON.stringify({ commentary }) })
