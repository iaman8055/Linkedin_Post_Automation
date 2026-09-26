const cards = [
  { label: 'Scheduled posts', value: '0', detail: 'Nothing queued yet' },
  { label: 'Draft posts', value: '0', detail: 'Start with a new idea' },
  { label: 'Active campaigns', value: '0', detail: 'Campaigns arrive in Phase 9' },
]

export function DashboardPage() {
  return (
    <div className="mx-auto max-w-6xl">
      <header className="mb-8">
        <p className="text-sm font-semibold text-sky-700">Overview</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight">Your content workspace</h1>
        <p className="mt-3 max-w-2xl text-slate-600">
          The application foundation is ready. Content workflows will be introduced milestone by milestone.
        </p>
      </header>

      <section aria-label="Content summary" className="grid gap-4 md:grid-cols-3">
        {cards.map((card) => (
          <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" key={card.label}>
            <p className="text-sm font-medium text-slate-500">{card.label}</p>
            <p className="mt-3 text-3xl font-bold">{card.value}</p>
            <p className="mt-2 text-sm text-slate-500">{card.detail}</p>
          </article>
        ))}
      </section>
    </div>
  )
}

