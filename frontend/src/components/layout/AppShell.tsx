import type { PropsWithChildren } from 'react'
import { NavLink } from 'react-router-dom'

const navigation = [
  { label: 'Dashboard', to: '/' },
  { label: 'Create', to: '/create' },
  { label: 'Campaigns', to: '/campaigns' },
  { label: 'Calendar', to: '/calendar' },
  { label: 'Posts', to: '/posts' },
  { label: 'Templates', to: '/templates' },
  { label: 'Research', to: '/research' },
  { label: 'Analytics', to: '/analytics' },
  { label: 'Notifications', to: '/notifications' },
  { label: 'Settings', to: '/settings' },
]

export function AppShell({ children }: PropsWithChildren) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 lg:grid lg:grid-cols-[250px_1fr]">
      <aside className="border-b border-slate-200 bg-white px-5 py-5 lg:min-h-screen lg:border-b-0 lg:border-r">
        <div className="mb-7">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-700">LinkedIn</p>
          <p className="mt-1 text-xl font-bold">AI Autopilot</p>
        </div>
        <nav aria-label="Main navigation" className="flex gap-2 overflow-x-auto lg:flex-col">
          {navigation.map((item) => (
            <NavLink
              className={({ isActive }) =>
                `whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition ${
                  isActive ? 'bg-sky-50 text-sky-800' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`
              }
              key={item.to}
              to={item.to}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="p-5 sm:p-8 lg:p-10">{children}</main>
    </div>
  )
}

