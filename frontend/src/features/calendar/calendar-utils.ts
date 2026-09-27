import type { Schedule } from './api'

export const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export function dateKey(value: Date | string) {
  const date = typeof value === 'string' ? new Date(value) : value
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function monthGrid(month: Date) {
  const first = new Date(month.getFullYear(), month.getMonth(), 1)
  const mondayOffset = (first.getDay() + 6) % 7
  const start = new Date(first)
  start.setDate(first.getDate() - mondayOffset)
  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(start)
    date.setDate(start.getDate() + index)
    return date
  })
}

export function scheduleTone(schedule: Schedule) {
  if (schedule.post.status === 'FAILED') return 'bg-red-500'
  if (schedule.post.status === 'PUBLISHED') return 'bg-emerald-500'
  if (schedule.status === 'CANCELLED') return 'bg-slate-400'
  if (schedule.status === 'PAUSED') return 'bg-amber-500'
  if (schedule.post.status === 'PUBLISHING') return 'bg-violet-500'
  return 'bg-[#5666f5]'
}

export function toLocalInput(iso: string) {
  const date = new Date(iso)
  const shifted = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return shifted.toISOString().slice(0, 16)
}
