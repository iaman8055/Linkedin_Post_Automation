import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'

import { AuthPage } from './AuthPage'

const signIn = vi.fn(() => Promise.resolve())
vi.mock('../AuthProvider', () => ({ useAuth: () => ({ isAuthenticated: false, signIn, signUp: vi.fn(), isWorking: false, error: null }) }))

it('submits credentials through the existing authentication API boundary', async () => {
  const user = userEvent.setup()
  render(<MemoryRouter><AuthPage mode="login"/></MemoryRouter>)
  await user.type(screen.getByLabelText('Email address'), 'aman@example.com')
  await user.type(screen.getByLabelText('Password'), 'correct-password')
  await user.click(screen.getByRole('button', { name: 'Sign in' }))
  expect(signIn).toHaveBeenCalledWith({ email: 'aman@example.com', password: 'correct-password' })
})
