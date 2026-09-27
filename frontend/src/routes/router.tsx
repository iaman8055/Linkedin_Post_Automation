import { createBrowserRouter, Navigate } from 'react-router-dom'

import { App } from '../App'
import { ComingSoon } from '../components/common/ComingSoon'
import { AuthPage } from '../features/auth/pages/AuthPage'
import { CampaignDetailPage } from '../features/campaigns/pages/CampaignDetailPage'
import { CampaignsPage } from '../features/campaigns/pages/CampaignsPage'
import { DashboardPage } from '../features/dashboard/pages/DashboardPage'
import { LinkedInSettingsPage } from '../features/linkedin/pages/LinkedInSettingsPage'
import { LinkedInCallbackPage } from '../features/linkedin/pages/LinkedInCallbackPage'
import { PostEditorPage } from '../features/posts/pages/PostEditorPage'
import { PostsPage } from '../features/posts/pages/PostsPage'
import { SettingsPage } from '../features/settings/pages/SettingsPage'
import { CalendarPage } from '../features/calendar/pages/CalendarPage'

export const router = createBrowserRouter([
  { path: '/login', element: <AuthPage mode="login"/> },
  { path: '/register', element: <AuthPage mode="register"/> },
  { path: '/', element: <App/>, children: [
    { index: true, element: <Navigate replace to="/dashboard"/> },
    { path: 'dashboard', element: <DashboardPage/> },
    { path: 'create', element: <PostEditorPage/> }, { path: 'create/:postId', element: <PostEditorPage/> },
    { path: 'posts', element: <PostsPage/> }, { path: 'posts/:postId', element: <PostEditorPage/> },
    { path: 'campaigns', element: <CampaignsPage/> }, { path: 'campaigns/:campaignId', element: <CampaignDetailPage/> },
    { path: 'calendar', element: <CalendarPage/> },
    { path: 'templates', element: <ComingSoon title="Templates"/> }, { path: 'research', element: <ComingSoon title="Research"/> },
    { path: 'analytics', element: <ComingSoon description="LinkedIn analytics collection is not implemented through Phase 9." title="Analytics"/> },
    { path: 'insights', element: <ComingSoon description="Performance insights require real historical analytics from a later phase." title="AI Insights"/> },
    { path: 'notifications', element: <ComingSoon title="Notifications"/> },
    { path: 'settings', element: <SettingsPage/> }, { path: 'settings/linkedin', element: <LinkedInSettingsPage/> }, { path: 'settings/linkedin/callback', element: <LinkedInCallbackPage/> },
  ]},
  { path: '*', element: <Navigate replace to="/dashboard"/> },
])
