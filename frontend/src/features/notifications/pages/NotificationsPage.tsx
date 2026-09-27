import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge, Button, Card, EmptyState, PageHeader, Skeleton } from '../../../components/ui/Primitives'
import { listNotifications, markAllNotificationsRead, markNotificationRead, notificationKeys } from '../api'

export function NotificationsPage() {
  const client = useQueryClient()
  const query = useQuery({ queryKey: notificationKeys.all, queryFn: listNotifications })
  const refresh = async () => { await client.invalidateQueries({ queryKey: ['notifications'] }) }
  const markOne = useMutation({ mutationFn: markNotificationRead, onSuccess: refresh })
  const markAll = useMutation({ mutationFn: markAllNotificationsRead, onSuccess: refresh })
  return <div className="mx-auto max-w-[900px]"><PageHeader action={query.data?.unread_count ? <Button disabled={markAll.isPending} onClick={() => markAll.mutate()} variant="secondary">Mark all as read</Button> : undefined} description="Publishing and workflow updates from your account." title="Notifications"/>{query.isLoading ? <Skeleton className="h-80"/> : query.data?.items.length ? <Card className="divide-y divide-slate-100">{query.data.items.map((item) => <button className={`flex w-full items-start gap-3 p-4 text-left hover:bg-slate-50 ${item.read_at ? 'bg-white' : 'bg-[#f7f8ff]'}`} key={item.id} onClick={() => !item.read_at && markOne.mutate(item.id)} type="button"><span className={`mt-1 size-2 shrink-0 rounded-full ${item.read_at ? 'bg-slate-200' : 'bg-[#4f5ff7]'}`}/><span className="min-w-0 flex-1"><span className="flex flex-wrap items-center gap-2"><strong className="text-[12px]">{item.title}</strong>{!item.read_at && <Badge tone="blue">New</Badge>}</span><span className="mt-1 block text-[11px] leading-5 text-slate-500">{item.message}</span><span className="mt-2 block text-[9px] text-slate-400">{new Date(item.created_at).toLocaleString()}</span></span></button>)}</Card> : <EmptyState description="Publishing results and workflow reminders will appear here." title="No notifications yet"/>}</div>
}
