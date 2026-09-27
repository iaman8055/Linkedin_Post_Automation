# Frontend architecture

The frontend is a React and TypeScript application organized by feature. It uses React Router for route
boundaries, TanStack Query for server state, React Hook Form and Zod for validated forms, and a compact
Tailwind-based visual system inspired by the supplied workspace reference.

## Phase 1-10 routes

- `/login` and `/register`: public authentication screens
- `/dashboard`: real post, draft, campaign, AI, and LinkedIn connection summaries
- `/posts`: searchable, filtered, paginated content library
- `/posts/:postId`: manual editor and approximate LinkedIn preview
- `/create`: AI-assisted generation and manual creation workflow
- `/campaigns` and `/campaigns/:id`: campaign management, lifecycle, and post membership
- `/settings`: account and provider configuration overview
- `/settings/linkedin`: connection management and explicitly confirmed test publishing
- `/settings/linkedin/callback`: browser OAuth callback completion
- `/calendar`: approved-post scheduling, publishing plan, rescheduling, pause/resume, and cancellation

All application routes are protected by the authentication boundary. Access tokens are kept in session
storage, refresh tokens in local storage, and one refresh attempt is made after an unauthorized API
response before the session is cleared.

## Design system

Shared primitives live in `src/components/ui`. They establish the page headers, buttons, cards, badges,
loading skeletons, empty states, error states, focus treatment, spacing, and color hierarchy used across
features. The application shell uses a narrow fixed desktop sidebar and a dismissible mobile navigation
drawer.

## Data policy

Screens use the real `/api/v1` contracts implemented through Phase 10. Later-phase routes render polished
unavailable states instead of mock analytics, notifications, or other invented production data.
