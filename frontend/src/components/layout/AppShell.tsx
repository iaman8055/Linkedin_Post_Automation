import { useState, type PropsWithChildren } from 'react'
import { useQuery } from '@tanstack/react-query'
import { NavLink, useLocation } from 'react-router-dom'

import { useAuth } from '../../features/auth/AuthProvider'
import { Brand } from '../../features/auth/pages/AuthPage'
import { getLinkedInStatus, linkedinKeys } from '../../features/linkedin/api'
import { Icon } from '../ui/Icon'

const navigation = [
  { label: 'Dashboard', to: '/dashboard', icon: 'dashboard' }, { label: 'Create Post', to: '/create', icon: 'create' },
  { label: 'Campaigns', to: '/campaigns', icon: 'campaigns' }, { label: 'Calendar', to: '/calendar', icon: 'calendar' },
  { label: 'Posts', to: '/posts', icon: 'posts' }, { label: 'Templates', to: '/templates', icon: 'templates' },
  { label: 'Research', to: '/research', icon: 'search' }, { label: 'Analytics', to: '/analytics', icon: 'analytics' },
  { label: 'AI Insights', to: '/insights', icon: 'insights' }, { label: 'Notifications', to: '/notifications', icon: 'bell' },
]

export function AppShell({ children }: PropsWithChildren) {
  const [open, setOpen] = useState(false); const auth = useAuth(); const location = useLocation()
  const linkedIn = useQuery({ queryKey: linkedinKeys.status, queryFn: getLinkedInStatus, staleTime: 60_000 })
  const connected = linkedIn.data?.accounts.some((account) => account.is_connected) ?? false
  const title = navigation.find((item) => location.pathname.startsWith(item.to))?.label ?? (location.pathname.startsWith('/settings') ? 'Settings' : 'Workspace')
  const initial = auth.user?.display_name.slice(0, 1).toUpperCase() ?? 'U'
  return <div className="min-h-screen bg-[#f5f7fb] text-[#172033] lg:pl-[224px]">
    {open && <button aria-label="Close navigation" className="fixed inset-0 z-30 bg-slate-950/25 lg:hidden" onClick={() => setOpen(false)} type="button" />}
    <aside className={`fixed inset-y-0 left-0 z-40 flex w-[224px] flex-col border-r border-[#e4e8f0] bg-white px-3.5 py-5 transition-transform lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="px-2"><Brand /></div>
      <nav aria-label="Main navigation" className="mt-7 flex-1 space-y-0.5 overflow-y-auto">{navigation.map((item) => <NavLink className={({ isActive }) => `flex h-9 items-center gap-3 rounded-lg px-3 text-[12.5px] font-semibold ${isActive ? 'bg-[#eef1ff] text-[#4353e8]' : 'text-[#5f6c80] hover:bg-slate-50 hover:text-slate-900'}`} key={item.to} onClick={() => setOpen(false)} to={item.to}><Icon className="size-[16px]" name={item.icon}/>{item.label}</NavLink>)}</nav>
      <div className="border-t border-slate-100 pt-3"><NavLink className={({ isActive }) => `flex h-9 items-center gap-3 rounded-lg px-3 text-[12.5px] font-semibold ${isActive ? 'bg-[#eef1ff] text-[#4353e8]' : 'text-[#5f6c80] hover:bg-slate-50'}`} to="/settings"><Icon className="size-[16px]" name="settings"/>Settings</NavLink><div className="mt-3 flex items-center gap-2.5 rounded-lg bg-slate-50 px-2.5 py-2.5"><span className="grid size-8 shrink-0 place-items-center rounded-full bg-[#e6eaff] text-xs font-bold text-[#4353e8]">{initial}</span><div className="min-w-0 flex-1"><p className="truncate text-[11px] font-bold">{auth.user?.display_name}</p><p className="text-[9px] text-slate-400">Free plan</p></div><button aria-label="Sign out" className="text-slate-400 hover:text-slate-700" onClick={() => void auth.signOut()} type="button"><Icon className="size-4" name="logout"/></button></div></div>
    </aside>
    <header className="sticky top-0 z-20 flex h-[58px] items-center justify-between border-b border-[#e6eaf1] bg-white/95 px-4 backdrop-blur sm:px-6 lg:px-8"><div className="flex items-center gap-3"><button aria-label="Open navigation" className="grid size-9 place-items-center rounded-lg border border-slate-200 text-slate-600 lg:hidden" onClick={() => setOpen(true)} type="button"><Icon name="menu"/></button><p className="text-sm font-bold lg:hidden">{title}</p></div><div className="ml-auto flex items-center gap-2.5"><NavLink className="hidden items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-[10px] font-bold text-slate-600 sm:flex" to="/settings/linkedin"><span className={`size-1.5 rounded-full ${connected ? 'bg-emerald-500' : 'bg-slate-300'}`}/>{connected ? 'LinkedIn Connected' : 'Connect LinkedIn'}</NavLink><NavLink aria-label="Notifications" className="grid size-8 place-items-center rounded-full text-slate-500 hover:bg-slate-100" to="/notifications"><Icon className="size-4" name="bell"/></NavLink><span className="grid size-8 place-items-center rounded-full bg-[#172033] text-[11px] font-bold text-white">{initial}</span></div></header>
    <main className="px-4 py-6 sm:px-6 lg:px-8 lg:py-7">{children}</main>
  </div>
}
