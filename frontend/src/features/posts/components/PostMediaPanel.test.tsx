import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { PostMediaPanel } from './PostMediaPanel'

describe('PostMediaPanel', () => {
  it('renders stored media metadata without claiming it will publish', async () => {
    const fetchMock = vi.spyOn(window, 'fetch').mockResolvedValue(new Response(JSON.stringify({ items: [{
      id: 'media-1', post_id: 'post-1', media_type: 'IMAGE', mime_type: 'image/png', size_bytes: 2048,
      position: 0, metadata_json: { filename: 'diagram.png' }, created_at: '2026-09-27T00:00:00Z',
    }] }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<QueryClientProvider client={client}><PostMediaPanel editable postId="post-1"/></QueryClientProvider>)
    await waitFor(() => expect(screen.getByText('diagram.png')).toBeInTheDocument())
    expect(screen.getByText(/publishing remains text-only/i)).toBeInTheDocument()
    fetchMock.mockRestore()
  })
})
