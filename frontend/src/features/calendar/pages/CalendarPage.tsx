import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { ErrorState, PageHeader, Skeleton } from '../../../components/ui/Primitives'
import { ApiError } from '../../../services/api/client'
import { listPosts, postKeys } from '../../posts/api'
import { createSchedule, listSchedules, scheduleAction, scheduleKeys, updateSchedule, type CreateScheduleInput } from '../api'
import { monthGrid } from '../calendar-utils'
import { CalendarAgenda } from '../components/CalendarAgenda'
import { CalendarMonth } from '../components/CalendarMonth'
import { ScheduleForm } from '../components/ScheduleForm'

export function CalendarPage() {
  const client = useQueryClient()
  const [month, setMonth] = useState(() => new Date(new Date().getFullYear(), new Date().getMonth(), 1))
  const [selected, setSelected] = useState(new Date())
  const range = useMemo(() => {
    const cells = monthGrid(month); const end = new Date(cells.at(-1)!)
    end.setDate(end.getDate() + 1)
    return { start: cells[0].toISOString(), end: end.toISOString() }
  }, [month])
  const schedules = useQuery({ queryKey: scheduleKeys.month(range.start), queryFn: () => listSchedules({ ...range, limit: 100 }), refetchInterval: 30_000 })
  const approved = useQuery({ queryKey: [...postKeys.all, 'approved'], queryFn: () => listPosts({ status: 'APPROVED', limit: 100 }) })
  const refresh = async () => { await client.invalidateQueries({ queryKey: scheduleKeys.all }); await client.invalidateQueries({ queryKey: postKeys.all }) }
  const create = useMutation({ mutationFn: createSchedule, onSuccess: refresh })
  const action = useMutation({ mutationFn: ({ id, value }: { id: string; value: 'cancel'|'pause'|'resume'|'retry' }) => scheduleAction(id, value), onSuccess: refresh })
  const reschedule = useMutation({ mutationFn: ({ id, scheduled_for, timezone }: { id: string; scheduled_for: string; timezone: string }) => updateSchedule(id, { scheduled_for, timezone }), onSuccess: refresh })
  const items = schedules.data?.items ?? []
  const changeMonth = (offset: number) => { const next = new Date(month.getFullYear(), month.getMonth() + offset, 1); setMonth(next); setSelected(next) }
  const selectDate = (date: Date) => { if (date.getMonth() !== month.getMonth() || date.getFullYear() !== month.getFullYear()) setMonth(new Date(date.getFullYear(), date.getMonth(), 1)); setSelected(date) }

  return <div className="mx-auto max-w-[1180px]">
    <PageHeader title="Content calendar" description="Review, schedule, and manage your publishing plan from one workspace." />
    {schedules.isError ? <ErrorState message="The calendar could not be loaded." retry={() => schedules.refetch()}/> : schedules.isLoading ? <Skeleton className="h-[620px]"/> : <>
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_300px]"><CalendarMonth month={month} selected={selected} schedules={items} onMonthChange={changeMonth} onSelect={selectDate}/><CalendarAgenda selected={selected} schedules={items} busy={action.isPending || reschedule.isPending} onAction={(id, value) => action.mutate({ id, value })} onReschedule={(id, value, timezone) => reschedule.mutate({ id, scheduled_for: new Date(value).toISOString(), timezone })}/></div>
      {schedules.data && schedules.data.total > schedules.data.items.length && <p className="mt-3 text-[11px] text-amber-700">This view contains more than 100 scheduled records. Use a narrower date range through the API for the remaining records.</p>}
    </>}
    {(action.isError || reschedule.isError) && <div className="mt-4"><ErrorState message={action.error instanceof ApiError ? action.error.message : reschedule.error instanceof ApiError ? reschedule.error.message : 'The calendar action failed.'}/></div>}
    <div className="mt-5 max-w-[420px]"><ScheduleForm approvedPosts={approved.data?.items ?? []} loading={approved.isLoading} pending={create.isPending} error={create.error} onSubmit={(input: CreateScheduleInput) => create.mutate(input)}/></div>
  </div>
}
