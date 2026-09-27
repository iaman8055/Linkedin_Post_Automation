import type { QualityCheck } from '../api'

const styles = {
  pass: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  fail: 'border-red-200 bg-red-50 text-red-800',
}
const severity = { low: 'bg-slate-100 text-slate-600', medium: 'bg-amber-100 text-amber-700', high: 'bg-red-100 text-red-700' }

export function QualityCheckPanel({ result }: { result: QualityCheck }) {
  return <section className="app-card mt-5 p-5" aria-live="polite">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Quality check</p><h2 className="mt-1 text-[14px] font-bold">Review before publishing</h2></div><span className={`rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase ${styles[result.status]}`}>{result.status}</span></div>
    {!result.ai_review_performed && <p className="mt-3 rounded-lg bg-blue-50 px-3 py-2 text-[11px] text-blue-700">Automated structural checks completed. Configure the AI provider to add grammar and claim review.</p>}
    {result.issues.length ? <div className="mt-4 space-y-3">{result.issues.map((issue, index) => <article className="rounded-lg border border-slate-100 p-3" key={`${issue.type}-${index}`}><div className="flex items-center gap-2"><span className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase ${severity[issue.severity]}`}>{issue.severity}</span><p className="text-[11px] font-bold capitalize text-slate-700">{issue.type.replaceAll('_', ' ')}</p></div><p className="mt-2 text-[11px] leading-5 text-slate-600">{issue.message}</p><p className="mt-1 text-[10px] leading-4 text-slate-400">Suggestion: {issue.suggestion}</p></article>)}</div> : <p className="mt-4 rounded-lg bg-emerald-50 px-3 py-3 text-[11px] text-emerald-700">No issues were detected. Continue reviewing the post for context and accuracy.</p>}
    <p className="mt-4 text-[10px] leading-4 text-slate-400">Results are advisory. The checker does not modify your post.</p>
  </section>
}
