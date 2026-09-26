import { createBrowserRouter } from 'react-router-dom'

import { App } from '../App'
import { ComingSoon } from '../components/common/ComingSoon'
import { DashboardPage } from '../features/dashboard/pages/DashboardPage'

const plannedRoutes = [
  ['create', 'Create content'],
  ['campaigns', 'Campaigns'],
  ['calendar', 'Content calendar'],
  ['posts', 'Posts'],
  ['templates', 'Templates'],
  ['research', 'Research'],
  ['analytics', 'Analytics'],
  ['notifications', 'Notifications'],
  ['settings', 'Settings'],
] as const

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <DashboardPage /> },
      ...plannedRoutes.map(([path, title]) => ({ path, element: <ComingSoon title={title} /> })),
    ],
  },
])

