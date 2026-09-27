import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { AnalyticsPage } from './AnalyticsPage'

describe('AnalyticsPage', () => {
  it('shows unavailable metrics instead of fabricated zeros', async () => {
    const fetchMock = vi.spyOn(window, 'fetch').mockImplementation((input) => {
      const url = String(input)
      const body = url.includes('/analytics/status')
        ? { connected: true, permission_granted: false, required_scope: 'r_member_postAnalytics', collection_available: false }
        : url.includes('/analytics/overview')
          ? { posts: [], total_impressions: null, total_likes: null, total_comments: null, total_shares: null, average_engagement_rate: null }
          : url.includes('/analytics/insights')
            ? { status: 'insufficient_data', analyzed_posts: 0, minimum_required: 5, disclaimer: 'Based only on your data.', insights: [] }
          : { items: [], total: 0, offset: 0, limit: 100 }
      return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    })
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<MemoryRouter><QueryClientProvider client={client}><AnalyticsPage/></QueryClientProvider></MemoryRouter>)
    await waitFor(() => expect(screen.getByText('Analytics permission required')).toBeInTheDocument())
    expect(screen.getAllByText('Unavailable').length).toBeGreaterThan(0)
    expect(screen.queryByText('12.4K')).not.toBeInTheDocument()
    expect(screen.getByText('More data is needed')).toBeInTheDocument()
    fetchMock.mockRestore()
  })
})
