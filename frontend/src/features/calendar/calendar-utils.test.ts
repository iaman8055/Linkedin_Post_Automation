import { describe, expect, it } from 'vitest'

import { dateKey, monthGrid } from './calendar-utils'

describe('calendar utilities', () => {
  it('builds a six-week Monday-first month grid', () => {
    const cells = monthGrid(new Date(2026, 8, 1))

    expect(cells).toHaveLength(42)
    expect(cells[0].getDay()).toBe(1)
    expect(dateKey(cells[0])).toBe('2026-08-31')
    expect(dateKey(cells.at(-1)!)).toBe('2026-10-11')
  })

  it('creates stable local date keys', () => {
    expect(dateKey(new Date(2026, 0, 5, 23, 30))).toBe('2026-01-05')
  })
})
