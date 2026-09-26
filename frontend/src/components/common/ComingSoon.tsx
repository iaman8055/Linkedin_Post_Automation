interface ComingSoonProps {
  title: string
}

export function ComingSoon({ title }: ComingSoonProps) {
  return (
    <section className="mx-auto max-w-3xl rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
      <p className="text-sm font-semibold text-sky-700">Planned feature</p>
      <h1 className="mt-2 text-3xl font-bold">{title}</h1>
      <p className="mt-3 text-slate-600">This area will be implemented in its scheduled development phase.</p>
    </section>
  )
}

