import { apiRequest } from '../../services/api/client'

export type User = { id: string; email: string; display_name: string; is_active: boolean; is_verified: boolean; created_at: string }
export type AuthSession = { user: User; access_token: string; refresh_token: string; token_type: string; expires_in: number }
export const login = (input: { email: string; password: string }) => apiRequest<AuthSession>('/auth/login', { method: 'POST', body: JSON.stringify(input) })
export const register = (input: { display_name: string; email: string; password: string }) => apiRequest<AuthSession>('/auth/register', { method: 'POST', body: JSON.stringify(input) })
export const getCurrentUser = () => apiRequest<User>('/auth/me')
export const logout = (refreshToken: string) => apiRequest<void>('/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: refreshToken }) })
