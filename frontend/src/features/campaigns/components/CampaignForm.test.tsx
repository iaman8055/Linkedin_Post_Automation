import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

import { CampaignForm } from './CampaignForm'

it('creates campaigns with manual approval by default', async () => {
  const user = userEvent.setup()
  const submit = vi.fn()
  render(
    <CampaignForm
      isSaving={false}
      onSubmit={submit}
      submitLabel="Create campaign"
    />,
  )

  await user.type(screen.getByLabelText('Campaign name'), 'AI Week')
  await user.type(screen.getByLabelText('Topic'), 'Artificial intelligence')
  await user.click(screen.getByRole('button', { name: 'Create campaign' }))

  expect(submit).toHaveBeenCalledWith(
    expect.objectContaining({
      name: 'AI Week',
      topic: 'Artificial intelligence',
      approval_mode: 'MANUAL',
      duration_days: 7,
    }),
  )
})
