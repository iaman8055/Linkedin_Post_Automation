import { apiRequest } from '../../services/api/client'

export type CopilotEvidence = { label: string; value: string; post_id: string | null }
export type CopilotAction = {
  id: string; tool_name: string; arguments: Record<string, unknown>
  status: string; expires_at: string; result: Record<string, unknown> | Record<string, unknown>[] | null
}
export type CopilotMessage = {
  id: string; role: 'user' | 'assistant'; content: string; evidence: CopilotEvidence[]
  suggested_action: string | null; created_at: string; action: CopilotAction | null
}
export type ConversationSummary = { id: string; title: string; last_message_at: string | null; created_at: string }
export type Conversation = ConversationSummary & { messages: CopilotMessage[] }
export type SendMessageInput = { content: string; use_writing_style: boolean; use_analytics: boolean; use_knowledge: boolean }

export const copilotKeys = {
  conversations: ['copilot', 'conversations'] as const,
  conversation: (id: string) => ['copilot', 'conversations', id] as const,
}

export const listConversations = () => apiRequest<{ items: ConversationSummary[] }>('/copilot/conversations')
export const getConversation = (id: string) => apiRequest<Conversation>(`/copilot/conversations/${id}`)
export const createConversation = () => apiRequest<Conversation>('/copilot/conversations', { method: 'POST', body: JSON.stringify({ title: 'New conversation' }) })
export const sendCopilotMessage = (id: string, input: SendMessageInput) => apiRequest<{ conversation: Conversation; assistant_message: CopilotMessage }>(`/copilot/conversations/${id}/messages`, { method: 'POST', body: JSON.stringify(input) })
export const confirmCopilotAction = (id: string) => apiRequest<CopilotAction>(`/copilot/actions/${id}/confirm`, { method: 'POST' })
export const cancelCopilotAction = (id: string) => apiRequest<CopilotAction>(`/copilot/actions/${id}/cancel`, { method: 'POST' })
