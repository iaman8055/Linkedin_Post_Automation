import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

import { LinkedInPreview } from './LinkedInPreview'
import { PostEditorForm } from './PostEditorForm'

describe('post editor', () => {
  it('validates and submits a manual draft', async () => {
    const user = userEvent.setup()
    const submit = vi.fn()
    const contentChange = vi.fn()
    render(
      <PostEditorForm
        defaultValues={{ title: '', content: '', language: 'English' }}
        isSaving={false}
        onContentChange={contentChange}
        onSubmit={submit}
      />,
    )

    await user.type(screen.getByLabelText('Post content'), 'A useful LinkedIn draft.')
    expect(contentChange).toHaveBeenCalled()
    expect(screen.getByText('24/3000')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Save draft' }))

    expect(submit).toHaveBeenCalledWith(
      { title: '', content: 'A useful LinkedIn draft.', language: 'English' },
      expect.anything(),
    )
  })

  it('labels the preview as approximate', () => {
    render(<LinkedInPreview content="Preview content" />)
    expect(screen.getByText('Preview content')).toBeInTheDocument()
    expect(screen.getByText(/not an exact replica/i)).toBeInTheDocument()
  })
})
