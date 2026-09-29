import { useState, type FormEvent, type PropsWithChildren } from 'react'
import { useQuery } from '@tanstack/react-query'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../../features/auth/AuthProvider'
import { Brand } from '../../features/auth/pages/AuthPage'
import { getLinkedInStatus, linkedinKeys } from '../../features/linkedin/api'
import { listWorkspaces, workspaceKeys } from '../../features/workspaces/api'
import { Icon } from '../ui/Icon'

const navigation = [
  { heading: 'Workspace', items: [
    { label: 'Dashboard', to: '/dashboard', icon: 'dashboard' },
    { label: 'Ask AI', to: '/copilot', icon: 'sparkle' },
    { label: 'Create post', to: '/create', icon: 'create' },
    { label: 'Content Studio', to: '/studio', icon: 'sparkle' },
    { label: 'Search', to: '/search', icon: 'search' },
  ] },
  { heading: 'Organize', items: [
    { label: 'Posts', to: '/posts', icon: 'posts' },
    { label: 'Calendar', to: '/calendar', icon: 'calendar' },
    { label: 'Campaigns', to: '/campaigns', icon: 'campaigns' },
    { label: 'Templates', to: '/templates', icon: 'templates' },
  ] },
  { heading: 'Grow', items: [
    { label: 'Engagement Lab', to: '/engagement', icon: 'sparkle' },
    { label: 'Research', to: '/research', icon: 'search' },
    { label: 'Analytics', to: '/analytics', icon: 'analytics' },
    { label: 'My Knowledge', to: '/knowledge', icon: 'insights' },
  ] },
]
const allNavigation = navigation.flatMap((group) => group.items)

export function AppShell({ children }: PropsWithChildren) {
  const [open, setOpen] = useState(false); const [search, setSearch] = useState(''); const auth = useAuth(); const location = useLocation(); const navigate = useNavigate()
  const linkedIn = useQuery({ queryKey: linkedinKeys.status, queryFn: getLinkedInStatus, staleTime: 60_000 })
  const workspaces = useQuery({ queryKey: workspaceKeys.all, queryFn: listWorkspaces, staleTime: 60_000 })
  const connected = linkedIn.data?.accounts.some((account) => account.is_connected) ?? false
  const title = allNavigation.find((item) => location.pathname.startsWith(item.to))?.label ?? (location.pathname.startsWith('/settings') ? 'Settings' : 'Workspace')
  const initial = auth.user?.display_name.slice(0, 1).toUpperCase() ?? 'U'
  const activeWorkspace = workspaces.data?.items.find((item) => item.is_current)
  const submitSearch = (event: FormEvent) => { event.preventDefault(); const query = search.trim(); if (query) { navigate(`/search?q=${encodeURIComponent(query)}`); setSearch('') } }
  return <div className="min-h-screen text-[#19162c] lg:pl-[242px]">
    {open && <button aria-label="Close navigation" className="fixed inset-0 z-30 bg-slate-950/25 lg:hidden" onClick={() => setOpen(false)} type="button" />}
    <aside className={`fixed inset-y-0 left-0 z-40 flex w-[242px] flex-col border-r border-[#ebe7f1] bg-[#fcfbfe]/95 px-3.5 py-5 shadow-[8px_0_30px_rgba(43,31,75,.025)] backdrop-blur transition-transform lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="px-2.5"><Brand /></div>
      <NavLink className="mx-1 mt-6 flex items-center justify-between rounded-xl border border-[#e6e1ee] bg-white px-3 py-2.5 shadow-sm" to="/settings"><div><p className="text-[9px] font-bold uppercase tracking-[0.12em] text-[#9a93a8]">Workspace</p><p className="mt-0.5 max-w-[145px] truncate text-[11px] font-bold text-[#3b3548]">{activeWorkspace?.name ?? 'Personal'}</p></div><span className="text-xs text-[#8b72fb]">⌄</span></NavLink>
      <nav aria-label="Main navigation" className="mt-5 flex-1 overflow-y-auto px-1">{navigation.map((group) => <div className="mb-5" key={group.heading}><p className="mb-1.5 px-2.5 text-[9px] font-extrabold uppercase tracking-[0.16em] text-[#aaa4b5]">{group.heading}</p><div className="space-y-0.5">{group.items.map((item) => <NavLink className={({ isActive }) => `group flex h-9 items-center gap-3 rounded-[10px] px-2.5 text-[12px] font-semibold ${isActive ? 'bg-[#eeeaff] text-[#5f42e8]' : 'text-[#696276] hover:bg-[#f5f2fa] hover:text-[#292438]'}`} key={item.to} onClick={() => setOpen(false)} to={item.to}><span className={`grid size-6 place-items-center rounded-md ${location.pathname.startsWith(item.to) ? 'bg-white text-[#6d4aff] shadow-sm' : 'text-[#8c8499] group-hover:text-[#6d4aff]'}`}><Icon className="size-[14px]" name={item.icon}/></span>{item.label}</NavLink>)}</div></div>)}</nav>
      <div className="border-t border-[#ece8f2] pt-3"><NavLink className={({ isActive }) => `flex h-9 items-center gap-3 rounded-[10px] px-3 text-[12px] font-semibold ${isActive ? 'bg-[#eeeaff] text-[#5f42e8]' : 'text-[#696276] hover:bg-[#f5f2fa]'}`} to="/settings"><Icon className="size-[15px]" name="settings"/>Settings</NavLink><div className="mt-3 flex items-center gap-2.5 rounded-xl bg-[#f4f1f8] px-2.5 py-2.5"><span className="grid size-8 shrink-0 place-items-center rounded-full bg-gradient-to-br from-[#7554ff] to-[#f1737d] text-xs font-bold text-white">{initial}</span><div className="min-w-0 flex-1"><p className="truncate text-[11px] font-bold">{auth.user?.display_name}</p><p className="text-[9px] text-[#9991a5]">Creator workspace</p></div><button aria-label="Sign out" className="text-[#aaa3b6] hover:text-[#554c64]" onClick={() => void auth.signOut()} type="button"><Icon className="size-4" name="logout"/></button></div></div>
    </aside>
    <header className="sticky top-0 z-20 flex h-[64px] items-center justify-between gap-4 border-b border-[#ebe7f1] bg-[#f9f8fc]/90 px-4 backdrop-blur-xl sm:px-6 lg:px-9"><div className="flex shrink-0 items-center gap-3"><button aria-label="Open navigation" className="grid size-9 place-items-center rounded-[10px] border border-[#e2deea] bg-white text-[#625b6e] lg:hidden" onClick={() => setOpen(true)} type="button"><Icon name="menu"/></button><p className="text-sm font-bold lg:hidden">{title}</p><p className="hidden text-xs font-semibold text-[#8a8295] lg:block">{title}</p></div><form className="mx-auto hidden w-full max-w-[380px] sm:block" onSubmit={submitSearch}><label className="relative block"><span className="sr-only">Search workspace</span><Icon className="absolute left-3 top-2.5 size-4 text-[#9a93a5]" name="search"/><input className="h-9 w-full rounded-[10px] border border-[#e4e0ea] bg-white/90 pl-9 pr-3 text-[11px] font-medium text-[#3f394b] outline-none placeholder:text-[#aaa4b4] focus:border-[#9a87ef] focus:ring-2 focus:ring-[#ede9ff]" onChange={(event) => setSearch(event.target.value)} placeholder="Search your workspace…" value={search}/></label></form><div className="ml-auto flex shrink-0 items-center gap-2.5"><NavLink aria-label="Search" className="grid size-9 place-items-center rounded-full bg-white text-[#746d80] shadow-sm ring-1 ring-[#e8e4ed] hover:text-[#6d4aff] sm:hidden" to="/search"><Icon className="size-4" name="search"/></NavLink><NavLink className="hidden items-center gap-2 rounded-full border border-[#e2deea] bg-white px-3 py-1.5 text-[9px] font-bold text-[#655e71] shadow-sm md:flex" to="/settings/linkedin"><span className={`size-1.5 rounded-full ${connected ? 'bg-emerald-500' : 'bg-[#c9c3d2]'}`}/>{connected ? 'LinkedIn connected' : 'Connect LinkedIn'}</NavLink><NavLink aria-label="Notifications" className="grid size-9 place-items-center rounded-full bg-white text-[#746d80] shadow-sm ring-1 ring-[#e8e4ed] hover:text-[#6d4aff]" to="/notifications"><Icon className="size-4" name="bell"/></NavLink><span className="grid size-9 place-items-center rounded-full bg-[#28233a] text-[11px] font-bold text-white shadow-sm">{initial}</span></div></header>
    <main className="px-4 py-7 sm:px-6 lg:px-9 lg:py-8">{children}</main>
  </div>
}
