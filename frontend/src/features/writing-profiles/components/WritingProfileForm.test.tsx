import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { WritingProfileForm } from './WritingProfileForm'

describe('WritingProfileForm', () => {
  it('normalizes vocabulary and submits style preferences', async () => {
    const submit = vi.fn()
    render(<WritingProfileForm profile={null} pending={false} onCancel={() => undefined} onSubmit={submit}/>)
    fireEvent.change(screen.getByLabelText('Profile name'), { target: { value: 'My voice' } })
    fireEvent.change(screen.getByLabelText('Tone'), { target: { value: 'Warm and direct' } })
    fireEvent.change(screen.getByLabelText('Preferred vocabulary (comma separated)'), { target: { value: 'practical, evidence-led' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create profile' }))
    await waitFor(() => expect(submit).toHaveBeenCalledWith(expect.objectContaining({
      name: 'My voice', tone: 'Warm and direct', preferred_vocabulary: ['practical', 'evidence-led'],
    })))
  })
})
