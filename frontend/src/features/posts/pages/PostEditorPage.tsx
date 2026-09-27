import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ApiError } from '../../../services/api/client'
import { Button, PageHeader, Skeleton } from '../../../components/ui/Primitives'
import { approvePost, createPost, getPost, postKeys, returnPostToDraft, updatePost } from '../api'
import { LinkedInPreview } from '../components/LinkedInPreview'
import { AIGeneratorForm } from '../components/AIGeneratorForm'
import { PostEditorForm, type PostFormValues } from '../components/PostEditorForm'

const emptyDraft: PostFormValues = { title: '', content: '', language: 'English' }

export function PostEditorPage() {
  const { postId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [previewOverride, setPreviewOverride] = useState<string | null>(null)
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
      await queryClient.invalidateQueries({ queryKey: postKeys.all })
      navigate(`/create/${post.id}`, { replace: true })
    },
  })
  const transition = useMutation({
    mutationFn: () => postQuery.data?.status === 'APPROVED' ? returnPostToDraft(postId!) : approvePost(postId!),
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: postKeys.all }) },
  })

  if (postQuery.isLoading) return <div className="mx-auto max-w-[1120px]"><Skeleton className="h-[500px]"/></div>
  if (postQuery.isError) return <p role="alert" className="text-red-700">This draft could not be loaded.</p>

  return (
    <div className="mx-auto max-w-[1120px]">
      <PageHeader eyebrow={postId ? 'Editor' : 'Create'} title={postId ? 'Edit post' : 'Create a new post'} description={postId ? 'Refine your draft and review how it will appear.' : 'Let AI help you create engaging LinkedIn drafts for your audience.'} action={postId && postQuery.data ? <div className="flex gap-2">{postQuery.data.status === 'DRAFT' && <Button onClick={() => transition.mutate()} disabled={transition.isPending}>Approve</Button>}{postQuery.data.status === 'APPROVED' && <><Button variant="secondary" onClick={() => transition.mutate()} disabled={transition.isPending}>Return to draft</Button><Link className="inline-flex h-9 items-center rounded-lg bg-[#4f5ff7] px-4 text-[13px] font-semibold text-white" to="/calendar">Schedule</Link></>}</div> : undefined}/>
      {!postId && (
        <div className="mb-5 grid gap-5 xl:grid-cols-[1.25fr_0.75fr]"><AIGeneratorForm
          onGenerated={async (result) => {
            await queryClient.invalidateQueries({ queryKey: postKeys.all })
            navigate(result.posts.length === 1 ? `/create/${result.posts[0].id}` : '/posts')
          }}
        /><section className="app-card p-5"><p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#4f5ff7]">Generation workflow</p><h2 className="mt-2 text-[16px] font-bold">From idea to editable draft</h2><ol className="mt-5 space-y-4">{['Set the audience and angle','Generate distinct post options','Open, refine, and save each draft'].map((step, index) => <li className="flex gap-3" key={step}><span className="grid size-6 shrink-0 place-items-center rounded-full bg-[#eef1ff] text-[10px] font-bold text-[#4f5ff7]">{index + 1}</span><span className="pt-1 text-[12px] font-medium text-slate-600">{step}</span></li>)}</ol><div className="mt-6 rounded-lg bg-slate-50 p-4 text-[11px] leading-5 text-slate-500">Generated content is always saved as a draft. Review claims and wording before publishing.</div></section></div>
      )}
      {!postId && <div className="mb-4 flex items-center gap-3"><span className="h-px flex-1 bg-slate-200"/><span className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Or write manually</span><span className="h-px flex-1 bg-slate-200"/></div>}
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.72fr)]">
        <section className="app-card p-5 sm:p-6"><h2 className="mb-5 text-[14px] font-bold">{postId ? 'Post editor' : 'Manual draft'}</h2>
          <PostEditorForm
            defaultValues={values}
            isSaving={save.isPending}
            onContentChange={setPreviewOverride}
            onSubmit={(form) => save.mutate(form)}
            serverError={save.error instanceof ApiError ? save.error.message : save.isError ? 'The draft could not be saved.' : undefined}
          />
        </section>
        <div>
          <p className="mb-3 text-[11px] font-bold uppercase tracking-wide text-slate-500">LinkedIn preview</p>
          <LinkedInPreview content={previewOverride ?? values.content} />
        </div>
      </div>
    </div>
  )
}
