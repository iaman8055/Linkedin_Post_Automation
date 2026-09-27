import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { Badge, Button, Card, EmptyState, PageHeader, Skeleton } from '../../../components/ui/Primitives'
import { ApiError } from '../../../services/api/client'
import { generatePosts } from '../../posts/api'
import { deleteResearchSource, getResearchStatus, listResearchSources, researchKeys, searchResearch, type ResearchSearchInput, type ResearchSource } from '../api'

export function ResearchPage() {
  const [query, setQuery] = useState('')
  const [topic, setTopic] = useState<'general' | 'news'>('general')
  const [timeRange, setTimeRange] = useState<ResearchSearchInput['time_range']>(null)
  const [selected, setSelected] = useState<string[]>([])
  const [answer, setAnswer] = useState<string | null>(null)
  const navigate = useNavigate(); const client = useQueryClient()
  const status = useQuery({ queryKey: researchKeys.status, queryFn: getResearchStatus })
  const sources = useQuery({ queryKey: researchKeys.sources, queryFn: listResearchSources })
  const search = useMutation({ mutationFn: searchResearch, onSuccess: async (result) => { setAnswer(result.answer); setSelected(result.sources.map((source) => source.id)); await client.invalidateQueries({ queryKey: researchKeys.sources }) } })
  const remove = useMutation({ mutationFn: deleteResearchSource, onSuccess: async (_, id) => { setSelected((items) => items.filter((item) => item !== id)); await client.invalidateQueries({ queryKey: researchKeys.sources }) } })
  const createDraft = useMutation({ mutationFn: () => generatePosts({ topic: topic === 'news' ? 'Current events' : 'Research', subject: query || 'Researched topic', audience: 'LinkedIn professionals', tone: 'professional and conversational', language: 'English', length: 'medium', call_to_action: null, include_hashtags: true, hashtag_count: 3, number_of_posts: 1, writing_profile_id: null, research_source_ids: selected }), onSuccess: (result) => navigate(`/posts/${result.posts[0].id}`) })
  const failure = search.error instanceof ApiError ? search.error.message : createDraft.error instanceof ApiError ? createDraft.error.message : null
  const toggle = (id: string) => setSelected((items) => items.includes(id) ? items.filter((item) => item !== id) : [...items, id])
  return <div className="mx-auto max-w-[1120px]">
    <PageHeader title="Research" description="Find current sources before creating evidence-aware content."/>
    {!status.isLoading && !status.data?.configured && <Card className="mb-5 border-amber-200 bg-amber-50 p-4"><p className="text-[12px] font-bold text-amber-900">Research provider configuration required</p><p className="mt-1 text-[11px] text-amber-700">Configure Tavily on the server before running live searches. No sample sources are shown.</p></Card>}
    <Card className="mb-5 p-5"><form className="grid gap-3 md:grid-cols-[1fr_140px_140px_auto]" onSubmit={(event) => { event.preventDefault(); search.mutate({ query, topic, max_results: 5, time_range: timeRange }) }}><label className="text-[11px] font-semibold text-slate-600">Research topic<input className="app-input mt-1.5" minLength={2} onChange={(event) => setQuery(event.target.value)} placeholder="AI agents in software development" required value={query}/></label><label className="text-[11px] font-semibold text-slate-600">Source type<select className="app-input mt-1.5" onChange={(event) => setTopic(event.target.value as 'general' | 'news')} value={topic}><option value="general">General</option><option value="news">News</option></select></label><label className="text-[11px] font-semibold text-slate-600">Freshness<select className="app-input mt-1.5" onChange={(event) => setTimeRange(event.target.value ? event.target.value as ResearchSearchInput['time_range'] : null)} value={timeRange ?? ''}><option value="">Any time</option><option value="day">Past day</option><option value="week">Past week</option><option value="month">Past month</option><option value="year">Past year</option></select></label><Button className="self-end" disabled={!status.data?.configured || search.isPending} type="submit">{search.isPending ? 'Researching…' : 'Research topic'}</Button></form>{failure && <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-[11px] text-red-700" role="alert">{failure}</p>}</Card>
    {answer && <Card className="mb-5 p-5"><div className="flex items-center gap-2"><Badge tone="blue">Provider summary</Badge><span className="text-[10px] text-slate-400">Verify important claims against the sources.</span></div><p className="mt-3 text-[12px] leading-6 text-slate-700">{answer}</p></Card>}
    <div className="mb-3 flex items-center justify-between"><div><h2 className="text-[15px] font-bold">Saved sources</h2><p className="mt-1 text-[11px] text-slate-500">Select sources to ground a new AI draft.</p></div><Button disabled={!selected.length || createDraft.isPending || query.trim().length < 2} onClick={() => createDraft.mutate()}>{createDraft.isPending ? 'Creating…' : `Create draft (${selected.length})`}</Button></div>
    {sources.isLoading ? <Skeleton className="h-64"/> : sources.data?.items.length ? <div className="space-y-3">{sources.data.items.map((source) => <SourceCard key={source.id} source={source} checked={selected.includes(source.id)} onToggle={() => toggle(source.id)} onDelete={() => remove.mutate(source.id)}/>)}</div> : <Card className="p-5"><EmptyState title="No research sources" description="Run a live search to collect attributable sources."/></Card>}
  </div>
}

function SourceCard({ source, checked, onToggle, onDelete }: { source: ResearchSource; checked: boolean; onToggle: () => void; onDelete: () => void }) {
  let hostname = source.url
  try { hostname = new URL(source.url).hostname } catch { /* Keep the source URL as the label. */ }
  return <Card className="p-4"><div className="flex items-start gap-3"><input aria-label={`Select ${source.title}`} checked={checked} className="mt-1 size-4" onChange={onToggle} type="checkbox"/><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><a className="text-[13px] font-bold text-slate-800 hover:text-[#4f5ff7]" href={source.url} rel="noreferrer" target="_blank">{source.title}</a><span className="text-[10px] text-slate-400">{hostname}</span></div><p className="mt-2 line-clamp-3 text-[11px] leading-5 text-slate-500">{source.relevant_content || 'No content snippet was returned.'}</p></div><button className="text-[10px] font-bold text-slate-400 hover:text-red-600" onClick={onDelete} type="button">Delete</button></div></Card>
}
