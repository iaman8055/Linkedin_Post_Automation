import { createBrowserRouter, Navigate } from 'react-router-dom'

import { App } from '../App'
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
import { TemplatesPage } from '../features/templates/pages/TemplatesPage'
import { WritingProfilesPage } from '../features/writing-profiles/pages/WritingProfilesPage'
import { ResearchPage } from '../features/research/pages/ResearchPage'
import { AnalyticsPage } from '../features/analytics/pages/AnalyticsPage'
import { NotificationsPage } from '../features/notifications/pages/NotificationsPage'
import { ContentStudioPage } from '../features/studio/pages/ContentStudioPage'
import { KnowledgePage } from '../features/knowledge/pages/KnowledgePage'
import { EngagementLabPage } from '../features/engagement/pages/EngagementLabPage'

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
    { path: 'templates', element: <TemplatesPage/> }, { path: 'research', element: <ResearchPage/> },
    { path: 'studio', element: <ContentStudioPage/> },
    { path: 'knowledge', element: <KnowledgePage/> },
    { path: 'engagement', element: <EngagementLabPage/> },
    { path: 'analytics', element: <AnalyticsPage/> },
    { path: 'insights', element: <AnalyticsPage/> },
    { path: 'notifications', element: <NotificationsPage/> },
    { path: 'settings', element: <SettingsPage/> }, { path: 'settings/writing-profiles', element: <WritingProfilesPage/> }, { path: 'settings/linkedin', element: <LinkedInSettingsPage/> }, { path: 'settings/linkedin/callback', element: <LinkedInCallbackPage/> },
  ]},
  { path: '*', element: <Navigate replace to="/dashboard"/> },
])
