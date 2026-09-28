import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'

import { DashboardPage } from './DashboardPage'

vi.mock('../../auth/AuthProvider', () => ({ useAuth: () => ({ user: { display_name: 'Aman Chauhan' } }) }))
vi.mock('../../posts/api', () => ({
  postKeys: { all: ['posts'] },
  listPosts: vi.fn(({ status }: { status?: string }) => Promise.resolve({ items: status ? [] : [], total: status ? 2 : 5, offset: 0, limit: 5 })),
}))
vi.mock('../../campaigns/api', () => ({
  campaignKeys: { all: ['campaigns'] },
  listCampaigns: vi.fn(() => Promise.resolve({ items: [], total: 0, offset: 0, limit: 4 })),
}))
vi.mock('../../linkedin/api', () => ({
  linkedinKeys: { status: ['linkedin', 'status'] },
  getLinkedInStatus: vi.fn(() => Promise.resolve({ accounts: [] })),
}))
vi.mock('../../creator-progress/api', () => ({
  creatorProgressKeys: { all: ['creator-progress'] },
  getCreatorProgress: vi.fn(() => Promise.resolve({
    creator_level: 1, level_points: 100, next_level_points: 500,
    posts_published: 1, drafts_created: 2, ideas_generated: 0,
    total_impressions: null, current_streak: 1,
    monthly_post_target: 8, monthly_posts_published: 1,
    monthly_goal_percent: 13, achievements: [],
  })),
  updateCreatorGoal: vi.fn(),
}))

it('loads real workspace totals without fabricated analytics', async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><MemoryRouter><DashboardPage/></MemoryRouter></QueryClientProvider>)
  expect(screen.getByRole('heading', { name: /good morning, aman/i })).toBeInTheDocument()
  expect(await screen.findByText('5')).toBeInTheDocument()
  expect(screen.queryByText(/impressions/i)).not.toBeInTheDocument()
})
