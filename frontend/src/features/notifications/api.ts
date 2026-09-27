import { apiRequest } from '../../services/api/client'

export type Notification = { id: string; event_type: string; title: string; message: string; read_at: string | null; data: Record<string, unknown>; created_at: string }
export type NotificationList = { items: Notification[]; unread_count: number; offset: number; limit: number }
export const notificationKeys = { all: ['notifications'] as const, count: ['notifications', 'unread-count'] as const }

export const listNotifications = () => apiRequest<NotificationList>('/notifications?limit=100')
export const getUnreadCount = () => apiRequest<{ unread_count: number }>('/notifications/unread-count')
export const markNotificationRead = (id: string) => apiRequest<Notification>(`/notifications/${id}/read`, { method: 'PATCH' })
export const markAllNotificationsRead = () => apiRequest<{ unread_count: number }>('/notifications/read-all', { method: 'POST' })
