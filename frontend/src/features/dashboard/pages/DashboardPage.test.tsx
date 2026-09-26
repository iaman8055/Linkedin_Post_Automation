import { render, screen } from '@testing-library/react'

import { DashboardPage } from './DashboardPage'

describe('DashboardPage', () => {
  it('shows the application workspace heading', () => {
    render(<DashboardPage />)

    expect(screen.getByRole('heading', { name: /your content workspace/i })).toBeInTheDocument()
  })
})

