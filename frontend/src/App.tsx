import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { AppShell } from './components/layout/AppShell'
import { useAuth } from './features/auth/AuthProvider'

export function App() {
  const auth = useAuth()
  const location = useLocation()
  if (!auth.isAuthenticated) return <Navigate replace state={{ from: location.pathname }} to="/login" />
  return <AppShell><Outlet /></AppShell>
}
