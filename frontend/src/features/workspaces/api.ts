import { apiRequest } from '../../services/api/client'

export type Workspace = {
  id: string; name: string; kind: 'personal' | 'company' | 'client' | string
  is_default: boolean; is_active: boolean; is_current: boolean
}
export const workspaceKeys = { all: ['workspaces'] as const }
export const listWorkspaces = () => apiRequest<{ items: Workspace[]; active_workspace_id: string }>('/workspaces')
export const createWorkspace = (name: string, kind: string) => apiRequest<Workspace>('/workspaces', { method: 'POST', body: JSON.stringify({ name, kind }) })
export const activateWorkspace = (id: string) => apiRequest<Workspace>(`/workspaces/${id}/activate`, { method: 'POST' })
