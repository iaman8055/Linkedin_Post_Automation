const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'
export const sessionKeys = { access: 'access_token', refresh: 'refresh_token', user: 'auth_user' }

type ApiErrorBody = {
  error?: { code?: string; message?: string }
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code = 'API_ERROR',
  ) {
    super(message)
  }
}

let refreshPromise: Promise<boolean> | null = null

function clearSession() {
  Object.values(sessionKeys).forEach((key) => window.localStorage.removeItem(key))
  window.dispatchEvent(new Event('auth:unauthorized'))
}

async function refreshSession(): Promise<boolean> {
  const refreshToken = window.localStorage.getItem(sessionKeys.refresh)
  if (!refreshToken) return false
  try {
    const response = await fetch(`${apiBaseUrl}/auth/refresh`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    if (!response.ok) { clearSession(); return false }
    const session = await response.json() as { access_token: string; refresh_token: string; user: unknown }
    window.localStorage.setItem(sessionKeys.access, session.access_token)
    window.localStorage.setItem(sessionKeys.refresh, session.refresh_token)
    window.localStorage.setItem(sessionKeys.user, JSON.stringify(session.user))
    return true
  } catch { clearSession(); return false }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = window.localStorage.getItem(sessionKeys.access)
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let response = await fetch(`${apiBaseUrl}${path}`, { ...init, headers })
  if (response.status === 401 && !path.startsWith('/auth/')) {
    refreshPromise ??= refreshSession().finally(() => { refreshPromise = null })
    if (await refreshPromise) {
      headers.set('Authorization', `Bearer ${window.localStorage.getItem(sessionKeys.access)}`)
      response = await fetch(`${apiBaseUrl}${path}`, { ...init, headers })
    }
  }
  if (!response.ok) {
    let body: ApiErrorBody = {}
    try {
      body = (await response.json()) as ApiErrorBody
    } catch {
      // The server may return an empty body for infrastructure errors.
    }
    throw new ApiError(
      body.error?.message ?? 'The request could not be completed.',
      response.status,
      body.error?.code,
    )
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
