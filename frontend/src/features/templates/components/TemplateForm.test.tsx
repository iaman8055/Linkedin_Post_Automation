import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { TemplateForm } from './TemplateForm'

describe('TemplateForm', () => {
  it('detects placeholders and submits normalized values', async () => {
    const submit = vi.fn()
    render(<TemplateForm template={null} pending={false} error={null} onCancel={() => undefined} onSubmit={submit}/>)

    expect(screen.getByText('{{topic}}')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Insight template' } })
    fireEvent.change(screen.getByLabelText('Description'), { target: { value: '  Useful structure  ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create template' }))

    await waitFor(() => {
      expect(submit).toHaveBeenCalledWith(expect.objectContaining({
        name: 'Insight template',
        description: 'Useful structure',
      }))
    })
  })
})
