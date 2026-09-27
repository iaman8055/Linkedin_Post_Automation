import { apiRequest } from '../../services/api/client'

export type AIStatus = { selected_provider: string | null; selected_model: string | null; provider_installed: boolean; registered_providers: string[] }
export const getAIStatus = () => apiRequest<AIStatus>('/ai/status')
