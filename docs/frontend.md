# Frontend architecture

The frontend is a React and TypeScript application organized by feature. It uses React Router for route
boundaries, TanStack Query for server state, React Hook Form and Zod for validated forms, and a compact
Tailwind-based visual system inspired by the supplied workspace reference.

## Implemented routes

- `/login` and `/register`: public authentication screens
- `/dashboard`: real post, draft, campaign, AI, and LinkedIn connection summaries
- `/posts`: searchable, filtered, paginated content library
- `/posts/:postId`: manual editor and approximate LinkedIn preview
- `/create`: AI-assisted generation and manual creation workflow
- `/campaigns` and `/campaigns/:id`: campaign management, lifecycle, and post membership
- `/settings`: account and provider configuration overview
- `/settings/linkedin`: connection management and explicitly confirmed test publishing
- `/settings/linkedin/callback`: browser OAuth callback completion
- `/calendar`: month navigation, status-coded schedule placement, selected-day agenda, approved-post
  scheduling, open/edit navigation, rescheduling, pause/resume, safe retry, and cancellation
- `/templates`: searchable template library, create/edit workflow, archive/restore controls, placeholder
  rendering, and creation of a real draft post from rendered content
- `/settings/writing-profiles`: personal voice profiles, default selection, editing, and deletion
- `/research`: live topic/news research, freshness controls, provider summary, saved source selection,
  source deletion, and grounded draft creation
- `/posts/:postId`: includes an advisory quality panel with severity, explanation, and suggestion for
  every detected issue; editing the draft clears stale results
- `/posts/:postId`: draft editors also support validated image, MP4, and PDF attachment upload,
  metadata display, and deletion while clearly labelling LinkedIn publication as text-only
- `/analytics`: permission status, published-post collection controls, latest lifetime snapshots,
  aggregate metric cards, and post-level performance without placeholder values

All application routes are protected by the authentication boundary. Access tokens are kept in session
storage, refresh tokens in local storage, and one refresh attempt is made after an unauthorized API
response before the session is cleared.

## Design system

Shared primitives live in `src/components/ui`. They establish the page headers, buttons, cards, badges,
loading skeletons, empty states, error states, focus treatment, spacing, and color hierarchy used across
features. The application shell uses a narrow fixed desktop sidebar and a dismissible mobile navigation
drawer.

## Data policy

Screens use the real `/api/v1` contracts implemented through Phase 20. Later-phase routes render polished
unavailable states instead of mock analytics, notifications, or other invented production data.
