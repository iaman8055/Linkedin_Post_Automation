import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, Skeleton } from '../../../components/ui/Primitives'
import { Icon } from '../../../components/ui/Icon'
import { ApiError } from '../../../services/api/client'
import { listPosts, postKeys } from '../../posts/api'
import { createSchedule, listSchedules, scheduleAction, scheduleKeys, updateSchedule, type CreateScheduleInput, type ScheduleRecurrence } from '../api'

const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const defaultTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
const toLocalInput = (iso: string) => {
  const date = new Date(iso); const shifted = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return shifted.toISOString().slice(0, 16)
}

export function CalendarPage() {
  const client = useQueryClient()
  const schedules = useQuery({ queryKey: scheduleKeys.all, queryFn: listSchedules, refetchInterval: 30_000 })
  const approved = useQuery({ queryKey: [...postKeys.all, 'approved'], queryFn: () => listPosts({ status: 'APPROVED', limit: 100 }) })
  const allPosts = useQuery({ queryKey: [...postKeys.all, 'calendar'], queryFn: () => listPosts({ limit: 100 }) })
  const [postId, setPostId] = useState(''); const [when, setWhen] = useState(''); const [timezone, setTimezone] = useState(defaultTimezone)
  const [recurrence, setRecurrence] = useState<ScheduleRecurrence>('ONCE'); const [days, setDays] = useState<number[]>([]); const [customDates, setCustomDates] = useState('')
  const postMap = useMemo(() => new Map(allPosts.data?.items.map((post) => [post.id, post])), [allPosts.data])
  const refresh = async () => { await client.invalidateQueries({ queryKey: scheduleKeys.all }); await client.invalidateQueries({ queryKey: postKeys.all }) }
  const create = useMutation({ mutationFn: createSchedule, onSuccess: async () => { setPostId(''); setWhen(''); setDays([]); setCustomDates(''); await refresh() } })
  const action = useMutation({ mutationFn: ({ id, value }: { id: string; value: 'cancel'|'pause'|'resume'|'retry' }) => scheduleAction(id, value), onSuccess: refresh })
  const reschedule = useMutation({ mutationFn: ({ id, scheduled_for, timezone: zone }: { id: string; scheduled_for: string; timezone: string }) => updateSchedule(id, { scheduled_for, timezone: zone }), onSuccess: refresh })

  const submit = (event: React.FormEvent) => {
    event.preventDefault(); if (!postId || !when) return
    const input: CreateScheduleInput = { post_id: postId, scheduled_for: new Date(when).toISOString(), timezone, recurrence }
    if (recurrence === 'WEEKLY') input.weekdays = days
    if (recurrence === 'CUSTOM') input.custom_dates = customDates.split('\n').map((value) => value.trim()).filter(Boolean).map((value) => new Date(value).toISOString())
    create.mutate(input)
  }

  return <div className="mx-auto max-w-[1120px]">
    <PageHeader title="Content calendar" description="Plan approved posts. PostgreSQL stores schedule times in UTC; publishing workers arrive in Phase 11." />
    <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
      <Card className="h-fit p-5"><h2 className="text-[14px] font-bold">Schedule a post</h2><p className="mt-1 text-[11px] text-slate-500">Only approved, unscheduled posts are available.</p>
        <form className="mt-5 space-y-4" onSubmit={submit}>
          <label className="block text-[11px] font-bold text-slate-700">Approved post<select className="app-input mt-1.5" required value={postId} onChange={(e) => setPostId(e.target.value)}><option value="">Select a post</option>{approved.data?.items.map((post) => <option key={post.id} value={post.id}>{post.title || post.content.slice(0, 48)}</option>)}</select></label>
          <label className="block text-[11px] font-bold text-slate-700">First publish time<input className="app-input mt-1.5" type="datetime-local" required value={when} onChange={(e) => setWhen(e.target.value)}/></label>
          <label className="block text-[11px] font-bold text-slate-700">Timezone<input className="app-input mt-1.5" required value={timezone} onChange={(e) => setTimezone(e.target.value)}/></label>
          <label className="block text-[11px] font-bold text-slate-700">Repeat<select className="app-input mt-1.5" value={recurrence} onChange={(e) => setRecurrence(e.target.value as ScheduleRecurrence)}><option value="ONCE">One time</option><option value="DAILY">Daily</option><option value="WEEKDAYS">Weekdays</option><option value="WEEKLY">Specific weekdays</option><option value="CUSTOM">Custom dates</option></select></label>
          {recurrence === 'WEEKLY' && <fieldset><legend className="text-[11px] font-bold text-slate-700">Publish on</legend><div className="mt-2 flex flex-wrap gap-1.5">{weekdays.map((day, index) => <button className={`rounded-md border px-2 py-1 text-[10px] font-bold ${days.includes(index) ? 'border-[#4f5ff7] bg-[#eef1ff] text-[#4f5ff7]' : 'border-slate-200'}`} type="button" key={day} onClick={() => setDays((current) => current.includes(index) ? current.filter((item) => item !== index) : [...current, index])}>{day}</button>)}</div></fieldset>}
          {recurrence === 'CUSTOM' && <label className="block text-[11px] font-bold text-slate-700">Custom dates<textarea className="app-input mt-1.5 min-h-24" placeholder="One ISO date per line" required value={customDates} onChange={(e) => setCustomDates(e.target.value)}/></label>}
          {create.isError && <p className="text-[11px] text-red-700" role="alert">{create.error instanceof ApiError ? create.error.message : 'The schedule could not be created.'}</p>}
          <Button className="w-full" disabled={create.isPending || !approved.data?.items.length} type="submit"><Icon name="calendar" className="size-4"/>Create schedule</Button>
          {!approved.isLoading && !approved.data?.items.length && <p className="text-[11px] leading-5 text-slate-500">Approve a draft in the post editor before scheduling it.</p>}
        </form>
      </Card>
      <Card className="overflow-hidden"><div className="border-b border-slate-100 p-5"><h2 className="text-[14px] font-bold">Publishing plan</h2><p className="mt-1 text-[11px] text-slate-500">Times are displayed in your browser’s timezone.</p></div>
        {schedules.isLoading ? <div className="space-y-3 p-5"><Skeleton className="h-20"/><Skeleton className="h-20"/></div> : schedules.isError ? <div className="p-5"><ErrorState message="The publishing plan could not be loaded." retry={() => schedules.refetch()}/></div> : !schedules.data?.items.length ? <div className="p-5"><EmptyState title="No scheduled posts" description="Approve a draft, then choose its publishing time."/></div> : <div className="divide-y divide-slate-100">{schedules.data.items.map((schedule) => { const post = postMap.get(schedule.post_id); return <article className="p-4 sm:p-5" key={schedule.id}><div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between"><div><div className="flex items-center gap-2"><Badge tone={post?.status === 'FAILED' ? 'red' : schedule.status === 'ACTIVE' ? 'blue' : schedule.status === 'CANCELLED' ? 'neutral' : 'amber'}>{post?.status === 'FAILED' ? 'FAILED' : schedule.status}</Badge><span className="text-[10px] font-bold text-slate-400">{schedule.recurrence}</span></div><Link className="mt-2 block text-[13px] font-bold hover:text-[#4f5ff7]" to={`/posts/${schedule.post_id}`}>{post?.title || post?.content.slice(0, 70) || 'Scheduled post'}</Link><p className="mt-1 text-[11px] text-slate-500">{new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(schedule.scheduled_for))} · {schedule.timezone}</p></div><div className="flex flex-wrap gap-2">{schedule.status === 'ACTIVE' && <Button variant="secondary" onClick={() => action.mutate({ id: schedule.id, value: 'pause' })}>Pause</Button>}{schedule.status === 'PAUSED' && <Button variant="secondary" onClick={() => action.mutate({ id: schedule.id, value: 'resume' })}>Resume</Button>}{schedule.retryable && post?.status === 'FAILED' && <Button onClick={() => action.mutate({ id: schedule.id, value: 'retry' })}>Retry safely</Button>}{schedule.outcome_uncertain && <span className="self-center text-[10px] font-semibold text-amber-700">Outcome uncertain · review LinkedIn</span>}{['ACTIVE','PAUSED'].includes(schedule.status) && <><Button variant="secondary" onClick={() => { const value = window.prompt('New local date and time', toLocalInput(schedule.scheduled_for)); if (value) reschedule.mutate({ id: schedule.id, scheduled_for: new Date(value).toISOString(), timezone: schedule.timezone }) }}>Reschedule</Button><Button variant="danger" onClick={() => action.mutate({ id: schedule.id, value: 'cancel' })}>Cancel</Button></>}</div></div>{action.isError && <p className="mt-2 text-[11px] text-red-700">{action.error instanceof ApiError ? action.error.message : 'The schedule action failed.'}</p>}</article>})}</div>}
      </Card>
    </div>
  </div>
}
