import { Link } from 'react-router-dom'

import { Badge, Button, Card, EmptyState } from '../../../components/ui/Primitives'
import type { Schedule } from '../api'
import { dateKey, scheduleTone, toLocalInput } from '../calendar-utils'

export function CalendarAgenda({ selected, schedules, busy, onAction, onReschedule }: {
  selected: Date
  schedules: Schedule[]
  busy: boolean
  onAction: (id: string, action: 'cancel' | 'pause' | 'resume' | 'retry') => void
  onReschedule: (id: string, value: string, timezone: string) => void
}) {
  const items = schedules.filter((schedule) => dateKey(schedule.scheduled_for) === dateKey(selected))
  return <Card className="overflow-hidden">
    <div className="border-b border-slate-100 px-5 py-4"><h2 className="text-[14px] font-bold">{new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'long', day: 'numeric' }).format(selected)}</h2><p className="mt-0.5 text-[10px] text-slate-400">{items.length} planned {items.length === 1 ? 'post' : 'posts'}</p></div>
    {!items.length ? <div className="p-5"><EmptyState title="Nothing planned" description="Select another day or schedule an approved post."/></div> : <div className="divide-y divide-slate-100">{items.map((schedule) => <article className="p-4" key={schedule.id}>
      <div className="flex items-start gap-3"><span className={`mt-1.5 size-2 shrink-0 rounded-full ${scheduleTone(schedule)}`}/><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><p className="text-[12px] font-bold">{new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' }).format(new Date(schedule.scheduled_for))}</p><Badge tone={schedule.post.status === 'FAILED' ? 'red' : schedule.post.status === 'PUBLISHED' ? 'green' : schedule.status === 'PAUSED' ? 'amber' : 'blue'}>{schedule.post.status}</Badge></div><Link className="mt-1 block truncate text-[12px] font-semibold text-slate-700 hover:text-[#4f5ff7]" to={`/posts/${schedule.post_id}`}>{schedule.post.title || schedule.post.content}</Link><p className="mt-1 text-[10px] text-slate-400">{schedule.recurrence} · {schedule.timezone}</p></div></div>
      <div className="mt-3 flex flex-wrap gap-1.5 pl-5"><Link className="inline-flex h-8 items-center rounded-lg border border-slate-200 px-3 text-[11px] font-semibold text-slate-600 hover:bg-slate-50" to={`/posts/${schedule.post_id}`}>Open</Link>{schedule.status === 'ACTIVE' && <Button disabled={busy} variant="secondary" onClick={() => onAction(schedule.id, 'pause')}>Pause</Button>}{schedule.status === 'PAUSED' && <Button disabled={busy} variant="secondary" onClick={() => onAction(schedule.id, 'resume')}>Resume</Button>}{schedule.retryable && <Button disabled={busy} onClick={() => onAction(schedule.id, 'retry')}>Retry safely</Button>}{schedule.outcome_uncertain && <span className="self-center text-[10px] font-semibold text-amber-700">Check LinkedIn before taking action</span>}{['ACTIVE','PAUSED'].includes(schedule.status) && <><Button disabled={busy} variant="secondary" onClick={() => { const value = window.prompt('New local date and time', toLocalInput(schedule.scheduled_for)); if (value) onReschedule(schedule.id, value, schedule.timezone) }}>Reschedule</Button><Button disabled={busy} variant="danger" onClick={() => onAction(schedule.id, 'cancel')}>Cancel</Button></>}</div>
    </article>)}</div>}
  </Card>
}
