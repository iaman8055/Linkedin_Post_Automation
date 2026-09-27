import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

import { AIGeneratorForm } from './AIGeneratorForm'

it('submits generation requirements and returns drafts for review', async () => {
  const user = userEvent.setup()
  const onGenerated = vi.fn()
  const response = {
    job_id: 'job-1',
    posts: [{ id: 'post-1', title: 'Generated', content: 'Draft', status: 'DRAFT' }],
  }
  const fetchMock = vi.spyOn(window, 'fetch').mockImplementation((input) => {
    const body = String(input).includes('/writing-profiles') ? { items: [], total: 0 } : response
    return Promise.resolve(
      new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } }),
    )
  })
  const queryClient = new QueryClient({ defaultOptions: { mutations: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <AIGeneratorForm onGenerated={onGenerated} />
    </QueryClientProvider>,
  )

  await user.type(screen.getByLabelText('Topic'), 'Artificial intelligence')
  await user.type(screen.getByLabelText('Subject'), 'AI agents')
  await user.type(screen.getByLabelText('Audience'), 'Software leaders')
  await user.click(screen.getByRole('button', { name: 'Generate drafts' }))

  await waitFor(() => expect(onGenerated).toHaveBeenCalledWith(response))
  expect(fetchMock).toHaveBeenCalledWith(
    expect.stringContaining('/ai/posts/generate'),
    expect.objectContaining({ method: 'POST' }),
  )
  fetchMock.mockRestore()
})
