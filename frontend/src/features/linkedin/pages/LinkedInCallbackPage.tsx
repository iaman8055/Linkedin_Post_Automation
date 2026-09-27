import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { Card, ErrorState, Skeleton } from '../../../components/ui/Primitives'
import { completeLinkedInConnection } from '../api'

export function LinkedInCallbackPage() {
  const [params] = useSearchParams(); const navigate = useNavigate(); const started = useRef(false)
  const [error, setError] = useState(false)
  const code = params.get('code'); const state = params.get('state'); const missingParameters = !code || !state
  useEffect(() => {
    if (started.current || !code || !state) return
    started.current = true
    void completeLinkedInConnection(code, state).then(() => navigate('/settings/linkedin', { replace: true })).catch(() => setError(true))
  }, [code, navigate, state])
  return <div className="mx-auto max-w-xl"><Card className="p-6">{error || missingParameters ? <ErrorState message="LinkedIn connection could not be completed." retry={() => navigate('/settings/linkedin')}/> : <><p className="text-sm font-bold">Completing LinkedIn connection…</p><Skeleton className="mt-4 h-12"/></>}</Card></div>
}
