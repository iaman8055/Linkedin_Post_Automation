import { apiRequest } from '../../services/api/client'

export type ScheduleStatus = 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'CANCELLED'
export type ScheduleRecurrence = 'ONCE' | 'DAILY' | 'WEEKDAYS' | 'WEEKLY' | 'CUSTOM'

export type Schedule = {
  id: string
  post_id: string
  post: {
    id: string
    campaign_id: string | null
    title: string | null
    content: string
    status: 'DRAFT' | 'APPROVED' | 'SCHEDULED' | 'PUBLISHING' | 'PUBLISHED' | 'FAILED' | 'CANCELLED'
  }
  recurrence: ScheduleRecurrence
  status: ScheduleStatus
  timezone: string
  scheduled_for: string
  next_run_at: string | null
  recurrence_rule: { weekdays?: number[]; custom_dates?: string[] } | null
  attempt_count: number
  last_attempt_at: string | null
  retryable: boolean
  outcome_uncertain: boolean
  created_at: string
  updated_at: string
}

export type ScheduleList = { items: Schedule[]; total: number; offset: number; limit: number }
export type CreateScheduleInput = {
  post_id: string
  scheduled_for: string
  timezone: string
  recurrence: ScheduleRecurrence
  weekdays?: number[]
  custom_dates?: string[]
}

export type ScheduleFilters = { start?: string; end?: string; limit?: number; offset?: number }
export const scheduleKeys = { all: ['schedules'] as const, month: (start: string) => ['schedules', 'month', start] as const }
export const listSchedules = (filters: ScheduleFilters = {}) => {
  const params = new URLSearchParams({ limit: String(filters.limit ?? 100), offset: String(filters.offset ?? 0) })
  if (filters.start) params.set('start', filters.start)
  if (filters.end) params.set('end', filters.end)
  return apiRequest<ScheduleList>(`/schedules?${params}`)
}
export const createSchedule = (input: CreateScheduleInput) => apiRequest<Schedule>('/schedules', { method: 'POST', body: JSON.stringify(input) })
export const updateSchedule = (id: string, input: { scheduled_for: string; timezone: string }) => apiRequest<Schedule>(`/schedules/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
export const scheduleAction = (id: string, action: 'cancel' | 'pause' | 'resume' | 'retry') => apiRequest<Schedule>(`/schedules/${id}/${action}`, { method: 'POST' })
