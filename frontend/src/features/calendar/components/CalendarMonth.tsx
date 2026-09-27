import { Button, Card } from '../../../components/ui/Primitives'
import type { Schedule } from '../api'
import { dateKey, monthGrid, scheduleTone, weekdayLabels } from '../calendar-utils'

export function CalendarMonth({ month, selected, schedules, onMonthChange, onSelect }: {
  month: Date
  selected: Date
  schedules: Schedule[]
  onMonthChange: (offset: number) => void
  onSelect: (date: Date) => void
}) {
  const cells = monthGrid(month)
  const grouped = new Map<string, Schedule[]>()
  for (const schedule of schedules) {
    const key = dateKey(schedule.scheduled_for)
    grouped.set(key, [...(grouped.get(key) ?? []), schedule])
  }
  const today = dateKey(new Date())

  return <Card className="overflow-hidden">
    <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
      <div><h2 className="text-[15px] font-bold">{new Intl.DateTimeFormat(undefined, { month: 'long', year: 'numeric' }).format(month)}</h2><p className="mt-0.5 text-[10px] text-slate-400">Times shown in your browser timezone</p></div>
      <div className="flex gap-1.5"><Button aria-label="Previous month" variant="secondary" onClick={() => onMonthChange(-1)}>←</Button><Button variant="secondary" onClick={() => onSelect(new Date())}>Today</Button><Button aria-label="Next month" variant="secondary" onClick={() => onMonthChange(1)}>→</Button></div>
    </div>
    <div className="grid grid-cols-7 border-b border-slate-100 bg-slate-50/70">{weekdayLabels.map((day) => <div className="px-2 py-2 text-center text-[9px] font-bold uppercase tracking-wide text-slate-400" key={day}>{day}</div>)}</div>
    <div className="grid grid-cols-7">{cells.map((date) => {
      const key = dateKey(date); const events = grouped.get(key) ?? []; const outside = date.getMonth() !== month.getMonth(); const active = key === dateKey(selected)
      return <button aria-label={`${key}, ${events.length} posts`} className={`min-h-24 border-b border-r border-slate-100 p-2 text-left transition-colors hover:bg-slate-50 sm:min-h-28 ${outside ? 'bg-slate-50/45' : 'bg-white'} ${active ? 'ring-2 ring-inset ring-[#5666f5]' : ''}`} key={key} onClick={() => onSelect(date)} type="button">
        <span className={`grid size-6 place-items-center rounded-full text-[10px] font-bold ${key === today ? 'bg-[#4f5ff7] text-white' : outside ? 'text-slate-300' : 'text-slate-600'}`}>{date.getDate()}</span>
        <div className="mt-2 space-y-1">{events.slice(0, 3).map((schedule) => <div className="flex min-w-0 items-center gap-1.5" key={schedule.id}><span className={`size-1.5 shrink-0 rounded-full ${scheduleTone(schedule)}`}/><span className="truncate text-[9px] font-semibold text-slate-600">{schedule.post.title || schedule.post.content}</span></div>)}{events.length > 3 && <p className="text-[9px] font-bold text-[#4f5ff7]">+{events.length - 3} more</p>}</div>
      </button>
    })}</div>
  </Card>
}
