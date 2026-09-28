import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ApiError } from '../../../services/api/client'
import { Button, PageHeader, Skeleton } from '../../../components/ui/Primitives'
import { approvePost, assistPost, checkPostQuality, createPost, getPost, postKeys, returnPostToDraft, scorePost, updatePost, type AssistPostAction } from '../api'
import { LinkedInPreview } from '../components/LinkedInPreview'
import { AIGeneratorForm } from '../components/AIGeneratorForm'
import { PostEditorForm, type PostFormValues } from '../components/PostEditorForm'
import { QualityCheckPanel } from '../components/QualityCheckPanel'
import { PostMediaPanel } from '../components/PostMediaPanel'
import { HookGenerator } from '../components/HookGenerator'
import { PostScorePanel } from '../components/PostScorePanel'

const emptyDraft: PostFormValues = { title: '', content: '', language: 'English' }

export function PostEditorPage() {
  const { postId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [previewOverride, setPreviewOverride] = useState<string | null>(null)
  const [editorOverride, setEditorOverride] = useState<string | null>(null)
  const [suggestion, setSuggestion] = useState<string | null>(null)
  const postQuery = useQuery({ queryKey: postKeys.detail(postId ?? ''), queryFn: () => getPost(postId!), enabled: Boolean(postId) })
  const values = postQuery.data
    ? { title: postQuery.data.title ?? '', content: postQuery.data.content, language: postQuery.data.language }
    : emptyDraft

  const save = useMutation({
    mutationFn: (form: PostFormValues) => {
      const input = { ...form, title: form.title.trim() || null }
      return postId ? updatePost(postId, input) : createPost(input)
    },
    onSuccess: async (post) => {
      quality.reset()
      await queryClient.invalidateQueries({ queryKey: postKeys.all })
      navigate(`/create/${post.id}`, { replace: true })
    },
  })
  const transition = useMutation({
    mutationFn: () => postQuery.data?.status === 'APPROVED' ? returnPostToDraft(postId!) : approvePost(postId!),
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: postKeys.all }) },
  })
  const quality = useMutation({ mutationFn: () => checkPostQuality(postId!) })
  const score = useMutation({ mutationFn: () => scorePost(postId!) })
  const assist = useMutation({
    mutationFn: ({ action, tone }: { action: AssistPostAction; tone?: string }) => assistPost(postId!, action, tone),
    onSuccess: (result) => setSuggestion(result.content),
  })

  if (postQuery.isLoading) return <div className="mx-auto max-w-[1120px]"><Skeleton className="h-[500px]"/></div>
  if (postQuery.isError) return <p role="alert" className="text-red-700">This draft could not be loaded.</p>

  return (
    <div className="mx-auto max-w-[1120px]">
      <PageHeader eyebrow={postId ? 'Editor' : 'Create'} title={postId ? 'Edit post' : 'AI Content Studio'} description={postId ? 'Refine, assess, and review your draft before publishing.' : 'Create distinct LinkedIn drafts from a detailed content brief.'} action={postId && postQuery.data ? <div className="flex flex-wrap gap-2"><Button variant="secondary" onClick={() => navigator.clipboard.writeText(previewOverride ?? values.content)}>Copy</Button><Button variant="secondary" onClick={() => quality.mutate()} disabled={quality.isPending}>{quality.isPending ? 'Checking…' : 'Quality check'}</Button><Button variant="secondary" onClick={() => score.mutate()} disabled={score.isPending}>{score.isPending ? 'Scoring…' : 'AI score'}</Button>{postQuery.data.status === 'DRAFT' && <Button onClick={() => transition.mutate()} disabled={transition.isPending}>Approve</Button>}{postQuery.data.status === 'APPROVED' && <><Button variant="secondary" onClick={() => transition.mutate()} disabled={transition.isPending}>Return to draft</Button><Link className="inline-flex h-9 items-center rounded-lg bg-[#4f5ff7] px-4 text-[13px] font-semibold text-white" to="/calendar">Schedule</Link></>}</div> : undefined}/>
      {!postId && (
        <div className="mb-5 grid gap-5 xl:grid-cols-[1.25fr_0.75fr]"><AIGeneratorForm
          onGenerated={async (result) => {
            await queryClient.invalidateQueries({ queryKey: postKeys.all })
            navigate(result.posts.length === 1 ? `/create/${result.posts[0].id}` : '/posts')
          }}
        /><HookGenerator onUseHook={(hook) => { const content = `${hook}\n\n`; setEditorOverride(content); setPreviewOverride(content) }}/></div>
      )}
      {!postId && <div className="mb-4 flex items-center gap-3"><span className="h-px flex-1 bg-slate-200"/><span className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Or write manually</span><span className="h-px flex-1 bg-slate-200"/></div>}
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.72fr)]">
        <section className="app-card p-5 sm:p-6"><h2 className="mb-5 text-[14px] font-bold">{postId ? 'Post editor' : 'Manual draft'}</h2>
          {postId && postQuery.data?.status === 'DRAFT' && <div className="mb-5 rounded-xl border border-[#e6e9f5] bg-[#fafbff] p-3"><p className="mb-2 text-[10px] font-bold uppercase tracking-wide text-[#4f5ff7]">AI writing assistant</p><div className="flex flex-wrap gap-2">{assistantActions.map(([action, label]) => <Button disabled={assist.isPending} key={action} onClick={() => assist.mutate({ action })} variant="secondary">{label}</Button>)}<Button disabled={assist.isPending} onClick={() => { const tone = window.prompt('Enter the new tone, for example: bold or conversational'); if (tone?.trim()) assist.mutate({ action: 'change_tone', tone: tone.trim() }) }} variant="secondary">Change tone</Button></div>{assist.isPending && <p className="mt-3 text-[11px] text-slate-500">✨ Improving your post…</p>}{assist.isError && <p className="mt-3 text-[11px] text-red-700">{assist.error instanceof ApiError ? assist.error.message : 'The AI edit could not be generated.'}</p>}</div>}
          {suggestion && <div className="mb-5 rounded-xl border border-indigo-200 bg-indigo-50 p-4"><p className="text-[11px] font-bold text-indigo-900">AI suggestion — review before applying</p><p className="mt-2 max-h-48 overflow-y-auto whitespace-pre-wrap text-[11px] leading-5 text-indigo-900">{suggestion}</p><div className="mt-3 flex gap-2"><Button onClick={() => { setEditorOverride(suggestion); setPreviewOverride(suggestion); setSuggestion(null) }}>Use suggestion</Button><Button onClick={() => setSuggestion(null)} variant="ghost">Discard</Button></div></div>}
          <PostEditorForm
            contentOverride={editorOverride}
            defaultValues={values}
            isSaving={save.isPending}
            onContentChange={(content) => { setPreviewOverride(content); quality.reset() }}
            onSubmit={(form) => save.mutate(form)}
            serverError={save.error instanceof ApiError ? save.error.message : save.isError ? 'The draft could not be saved.' : undefined}
          />
        </section>
        <div>
          <p className="mb-3 text-[11px] font-bold uppercase tracking-wide text-slate-500">LinkedIn preview</p>
          <LinkedInPreview content={previewOverride ?? values.content} />
          {postId && postQuery.data && <PostMediaPanel postId={postId} editable={postQuery.data.status === 'DRAFT'}/>} 
          {quality.data && <QualityCheckPanel result={quality.data}/>} 
          {score.data && <PostScorePanel improving={assist.isPending} onImprove={() => assist.mutate({ action: 'improve' })} result={score.data}/>} 
          {quality.isError && <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-[11px] text-red-700" role="alert">{quality.error instanceof ApiError ? quality.error.message : 'The quality check could not be completed.'}</p>}
          {score.isError && <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-[11px] text-red-700" role="alert">{score.error instanceof ApiError ? score.error.message : 'The AI score could not be completed.'}</p>}
        </div>
      </div>
    </div>
  )
}

const assistantActions: [AssistPostAction, string][] = [
  ['improve', 'Improve'], ['rewrite', 'Rewrite'], ['shorten', 'Shorten'], ['expand', 'Expand'],
  ['improve_hook', 'Improve hook'], ['improve_cta', 'Improve CTA'], ['add_hashtags', 'Add hashtags'],
]
