import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'

import { Icon } from '../../../components/ui/Icon'
import { Badge, Card, EmptyState, ErrorState, PageHeader, Skeleton } from '../../../components/ui/Primitives'
import { globalSearch, searchKeys, type SearchEntityType, type SearchFilters, type SearchResult } from '../api'

const entityOptions: [SearchEntityType, string][] = [['all', 'Everything'], ['post', 'Posts'], ['idea', 'Ideas'], ['knowledge', 'Knowledge'], ['template', 'Templates']]

export function SearchPage() {
  const [params, setParams] = useSearchParams()
  const filters: SearchFilters = {
    query: params.get('q') ?? '', entityType: (params.get('entity_type') as SearchEntityType | null) ?? 'all',
    status: params.get('status') ?? '', topic: params.get('topic') ?? '', tag: params.get('tag') ?? '',
    dateFrom: params.get('date_from') ?? '', dateTo: params.get('date_to') ?? '',
  }
  const results = useQuery({ queryKey: searchKeys.results(filters), queryFn: () => globalSearch(filters) })
  const update = (key: string, value: string) => { const next = new URLSearchParams(params); if (value) next.set(key, value); else next.delete(key); setParams(next, { replace: true }) }
  return <div className="mx-auto max-w-[1120px]">
    <PageHeader eyebrow="Workspace search" title="Find your content" description="Search posts, ideas, templates, and your private knowledge from one place."/>
    <Card className="p-4 sm:p-5">
      <label className="relative block"><span className="sr-only">Search all content</span><Icon className="absolute left-3.5 top-3 size-4 text-[#8f879c]" name="search"/><input autoFocus className="app-input h-10 pl-10" onChange={(event) => update('q', event.target.value)} placeholder="Search titles, post copy, notes, ideas…" value={filters.query}/></label>
      <div className="mt-4 flex gap-2 overflow-x-auto pb-1">{entityOptions.map(([value, label]) => <button className={`shrink-0 rounded-full px-3.5 py-2 text-[11px] font-bold transition ${filters.entityType === value ? 'bg-[#2e2940] text-white' : 'bg-[#f2eff7] text-[#6d6679] hover:bg-[#e9e4f2]'}`} key={value} onClick={() => update('entity_type', value === 'all' ? '' : value)} type="button">{label}</button>)}</div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <select aria-label="Status" className="app-input" onChange={(event) => update('status', event.target.value)} value={filters.status}><option value="">Any status</option>{['DRAFT','APPROVED','SCHEDULED','PUBLISHED','FAILED','CANCELLED'].map((status) => <option key={status} value={status}>{titleCase(status)}</option>)}</select>
        <input aria-label="Topic" className="app-input" onChange={(event) => update('topic', event.target.value)} placeholder="Topic" value={filters.topic}/>
        <input aria-label="Tag" className="app-input" onChange={(event) => update('tag', event.target.value)} placeholder="Exact knowledge tag" value={filters.tag}/>
        <input aria-label="From date" className="app-input" onChange={(event) => update('date_from', event.target.value)} type="date" value={filters.dateFrom}/>
        <input aria-label="To date" className="app-input" onChange={(event) => update('date_to', event.target.value)} type="date" value={filters.dateTo}/>
      </div>
    </Card>
    <div className="mt-5 flex items-center justify-between"><p className="text-[11px] font-semibold text-[#8a8295]">{results.data ? `${results.data.total} result${results.data.total === 1 ? '' : 's'}` : 'Searching your workspace'}</p>{params.size > 0 && <button className="text-[11px] font-bold text-[#6849ed]" onClick={() => setParams({}, { replace: true })} type="button">Clear filters</button>}</div>
    <div className="mt-3">{results.isLoading ? <div className="space-y-3">{Array.from({ length: 4 }, (_, index) => <Skeleton className="h-28" key={index}/>)}</div> : results.isError ? <ErrorState message="We couldn't search your content right now." retry={() => void results.refetch()}/> : !results.data?.items.length ? <EmptyState title="No matching content" description="Try a broader phrase or remove one of the filters."/> : <div className="space-y-3">{results.data.items.map((item) => <ResultCard item={item} key={`${item.entity_type}-${item.id}`}/>)}</div>}</div>
  </div>
}

function ResultCard({ item }: { item: SearchResult }) {
  return <Link className="group block" to={item.url}><Card className="p-4 transition hover:-translate-y-px hover:border-[#d8d0ea] hover:shadow-[0_8px_24px_rgba(55,43,83,.07)] sm:p-5"><div className="flex items-start gap-4"><span className="grid size-9 shrink-0 place-items-center rounded-xl bg-[#f0edff] text-[#6849ed]"><Icon className="size-4" name={item.entity_type === 'post' ? 'posts' : item.entity_type === 'template' ? 'templates' : item.entity_type === 'idea' ? 'sparkle' : 'insights'}/></span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><Badge tone="violet">{item.entity_type}</Badge>{item.status && <Badge tone={item.status === 'PUBLISHED' ? 'green' : item.status === 'FAILED' ? 'red' : 'neutral'}>{titleCase(item.status)}</Badge>}<span className="text-[10px] text-[#9b94a5]">Updated {formatDate(item.updated_at)}</span></div><h2 className="mt-2 truncate text-sm font-extrabold text-[#282339] group-hover:text-[#6244e5]">{item.title}</h2><p className="mt-1 line-clamp-2 text-xs leading-5 text-[#716a7d]">{item.excerpt}</p>{(item.topic || item.tags.length > 0 || item.scheduled_for) && <div className="mt-3 flex flex-wrap gap-1.5">{item.topic && <span className="rounded-md bg-[#f5f2f8] px-2 py-1 text-[9px] font-semibold text-[#756e80]">{item.topic}</span>}{item.tags.slice(0, 4).map((tag) => <span className="rounded-md bg-[#f5f2f8] px-2 py-1 text-[9px] font-semibold text-[#756e80]" key={tag}>#{tag}</span>)}{item.scheduled_for && <span className="rounded-md bg-blue-50 px-2 py-1 text-[9px] font-semibold text-blue-700">Scheduled {formatDate(item.scheduled_for)}</span>}</div>}</div><Icon className="mt-2 size-4 shrink-0 text-[#b2abba] transition group-hover:translate-x-0.5 group-hover:text-[#6849ed]" name="arrow"/></div></Card></Link>
}

function titleCase(value: string) { return value.toLowerCase().replace(/(^|_)(\w)/g, (_, space: string, letter: string) => `${space ? ' ' : ''}${letter.toUpperCase()}`) }
function formatDate(value: string) { return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value)) }
