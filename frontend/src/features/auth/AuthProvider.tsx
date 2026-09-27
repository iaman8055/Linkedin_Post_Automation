import { createContext, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { sessionKeys } from '../../services/api/client'
import { getCurrentUser, login, logout, register, type AuthSession, type User } from './api'

type AuthContextValue = {
  user: User | null
  isAuthenticated: boolean
  signIn: (input: { email: string; password: string }) => Promise<void>
  signUp: (input: { display_name: string; email: string; password: string }) => Promise<void>
  signOut: () => Promise<void>
  isWorking: boolean
  error: Error | null
}
const AuthContext = createContext<AuthContextValue | null>(null)

function storedUser(): User | null {
  const value = window.localStorage.getItem(sessionKeys.user)
  if (!value) return null
  try { return JSON.parse(value) as User } catch { return null }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(storedUser)
  const queryClient = useQueryClient()
  const persist = (session: AuthSession) => {
    window.localStorage.setItem(sessionKeys.access, session.access_token)
    window.localStorage.setItem(sessionKeys.refresh, session.refresh_token)
    window.localStorage.setItem(sessionKeys.user, JSON.stringify(session.user))
    setUser(session.user)
  }
  const loginMutation = useMutation({ mutationFn: login, onSuccess: persist })
  const registerMutation = useMutation({ mutationFn: register, onSuccess: persist })
  useEffect(() => {
    const unauthorized = () => setUser(null)
    window.addEventListener('auth:unauthorized', unauthorized)
    return () => window.removeEventListener('auth:unauthorized', unauthorized)
  }, [])
  useEffect(() => {
    if (!window.localStorage.getItem(sessionKeys.access)) return
    void getCurrentUser().then((currentUser) => {
      window.localStorage.setItem(sessionKeys.user, JSON.stringify(currentUser))
      setUser(currentUser)
    }).catch(() => {
      Object.values(sessionKeys).forEach((key) => window.localStorage.removeItem(key))
      setUser(null)
    })
  }, [])
  const value = useMemo<AuthContextValue>(() => ({
    user,
    isAuthenticated: Boolean(user && window.localStorage.getItem(sessionKeys.access)),
    signIn: async (input) => { await loginMutation.mutateAsync(input) },
    signUp: async (input) => { await registerMutation.mutateAsync(input) },
    signOut: async () => {
      const refreshToken = window.localStorage.getItem(sessionKeys.refresh)
      try { if (refreshToken) await logout(refreshToken) } finally {
        Object.values(sessionKeys).forEach((key) => window.localStorage.removeItem(key))
        queryClient.clear(); setUser(null)
      }
    },
    isWorking: loginMutation.isPending || registerMutation.isPending,
    error: loginMutation.error ?? registerMutation.error,
  }), [user, loginMutation, registerMutation, queryClient])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// Context hooks intentionally live beside their provider to keep the session boundary cohesive.
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside AuthProvider')
  return value
}
