import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { Card, PageHeader, Skeleton } from '../../../components/ui/Primitives'
import { useAuth } from '../../auth/AuthProvider'
import { getAIStatus } from '../api'

export function SettingsPage() {
  const auth = useAuth()
  const ai = useQuery({ queryKey: ['ai', 'status'], queryFn: getAIStatus })
  return <div className="mx-auto max-w-[1120px]">
    <PageHeader description="Manage the integrations and preferences available in the current product." title="Settings"/>
    <div className="grid gap-5 lg:grid-cols-2">
      <Card className="p-5"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">Account</p><h2 className="mt-2 text-base font-bold">{auth.user?.display_name}</h2><p className="mt-1 text-[13px] text-slate-500">{auth.user?.email}</p><div className="mt-4 flex items-center gap-2 text-xs"><span className={`size-2 rounded-full ${auth.user?.is_verified ? 'bg-emerald-500' : 'bg-amber-400'}`}/>{auth.user?.is_verified ? 'Email verified' : 'Email verification pending'}</div></Card>
      <Card className="p-5"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">AI provider</p>{ai.isLoading ? <Skeleton className="mt-3 h-16"/> : <><h2 className="mt-2 text-base font-bold">{ai.data?.selected_provider ?? 'Not configured'}</h2><p className="mt-1 text-[13px] text-slate-500">{ai.data?.selected_model ?? 'Choose a provider and model in the server environment.'}</p><p className={`mt-4 text-xs font-semibold ${ai.data?.provider_installed ? 'text-emerald-600' : 'text-amber-600'}`}>{ai.data?.provider_installed ? 'Provider adapter available' : 'Provider configuration required'}</p></>}</Card>
      <Card className="p-5 lg:col-span-2"><div className="flex items-center justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-wide text-slate-400">LinkedIn</p><h2 className="mt-2 text-base font-bold">Connection and publishing test</h2><p className="mt-1 text-[13px] text-slate-500">Connect the real LinkedIn account used for publishing.</p></div><Link className="rounded-lg bg-[#4f5ff7] px-4 py-2.5 text-xs font-bold text-white" to="/settings/linkedin">Manage LinkedIn</Link></div></Card>
      <Card className="p-5 lg:col-span-2"><div className="flex items-center justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-wide text-slate-400">Personal voice</p><h2 className="mt-2 text-base font-bold">Writing profiles</h2><p className="mt-1 text-[13px] text-slate-500">Define the tone, rhythm, vocabulary, and depth used by AI drafts.</p></div><Link className="rounded-lg border border-slate-200 px-4 py-2.5 text-xs font-bold text-slate-700" to="/settings/writing-profiles">Manage profiles</Link></div></Card>
    </div>
  </div>
}
