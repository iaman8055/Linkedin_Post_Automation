import { useState } from 'react'

import { Button, Card } from '../../../components/ui/Primitives'
import { Icon } from '../../../components/ui/Icon'
import { ApiError } from '../../../services/api/client'
import type { Post } from '../../posts/api'
import type { CreateScheduleInput, ScheduleRecurrence } from '../api'
import { weekdayLabels } from '../calendar-utils'

const defaultTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'

export function ScheduleForm({ approvedPosts, loading, pending, error, onSubmit }: {
  approvedPosts: Post[]
  loading: boolean
  pending: boolean
  error: unknown
  onSubmit: (input: CreateScheduleInput) => void
}) {
  const [postId, setPostId] = useState(''); const [when, setWhen] = useState(''); const [timezone, setTimezone] = useState(defaultTimezone)
  const [recurrence, setRecurrence] = useState<ScheduleRecurrence>('ONCE'); const [days, setDays] = useState<number[]>([]); const [customDates, setCustomDates] = useState('')
  const submit = (event: React.FormEvent) => {
    event.preventDefault(); if (!postId || !when) return
    const input: CreateScheduleInput = { post_id: postId, scheduled_for: new Date(when).toISOString(), timezone, recurrence }
    if (recurrence === 'WEEKLY') input.weekdays = days
    if (recurrence === 'CUSTOM') input.custom_dates = customDates.split('\n').map((value) => value.trim()).filter(Boolean).map((value) => new Date(value).toISOString())
    onSubmit(input)
  }
  return <Card className="h-fit p-5"><h2 className="text-[14px] font-bold">Schedule a post</h2><p className="mt-1 text-[11px] text-slate-500">Only approved, unscheduled posts are available.</p>
    <form className="mt-5 space-y-4" onSubmit={submit}>
      <label className="block text-[11px] font-bold text-slate-700">Approved post<select className="app-input mt-1.5" required value={postId} onChange={(event) => setPostId(event.target.value)}><option value="">Select a post</option>{approvedPosts.map((post) => <option key={post.id} value={post.id}>{post.title || post.content.slice(0, 48)}</option>)}</select></label>
      <label className="block text-[11px] font-bold text-slate-700">First publish time<input className="app-input mt-1.5" type="datetime-local" required value={when} onChange={(event) => setWhen(event.target.value)}/></label>
      <label className="block text-[11px] font-bold text-slate-700">Timezone<input className="app-input mt-1.5" required value={timezone} onChange={(event) => setTimezone(event.target.value)}/></label>
      <label className="block text-[11px] font-bold text-slate-700">Repeat<select className="app-input mt-1.5" value={recurrence} onChange={(event) => setRecurrence(event.target.value as ScheduleRecurrence)}><option value="ONCE">One time</option><option value="DAILY">Daily</option><option value="WEEKDAYS">Weekdays</option><option value="WEEKLY">Specific weekdays</option><option value="CUSTOM">Custom dates</option></select></label>
      {recurrence === 'WEEKLY' && <fieldset><legend className="text-[11px] font-bold text-slate-700">Publish on</legend><div className="mt-2 flex flex-wrap gap-1.5">{weekdayLabels.map((day, index) => <button className={`rounded-md border px-2 py-1 text-[10px] font-bold ${days.includes(index) ? 'border-[#4f5ff7] bg-[#eef1ff] text-[#4f5ff7]' : 'border-slate-200'}`} type="button" key={day} onClick={() => setDays((current) => current.includes(index) ? current.filter((item) => item !== index) : [...current, index])}>{day}</button>)}</div></fieldset>}
      {recurrence === 'CUSTOM' && <label className="block text-[11px] font-bold text-slate-700">Custom dates<textarea className="app-input mt-1.5 min-h-24" placeholder="One ISO date per line" required value={customDates} onChange={(event) => setCustomDates(event.target.value)}/></label>}
      {error != null && <p className="text-[11px] text-red-700" role="alert">{error instanceof ApiError ? error.message : 'The schedule could not be created.'}</p>}
      <Button className="w-full" disabled={pending || !approvedPosts.length} type="submit"><Icon name="calendar" className="size-4"/>Create schedule</Button>
      {!loading && !approvedPosts.length && <p className="text-[11px] leading-5 text-slate-500">Approve a draft in the post editor before scheduling it.</p>}
    </form>
  </Card>
}
