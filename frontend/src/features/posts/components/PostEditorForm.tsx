import { zodResolver } from '@hookform/resolvers/zod'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'

const postSchema = z.object({
  title: z.string().max(240, 'Use 240 characters or fewer.'),
  content: z.string().trim().min(1, 'Write some content first.').max(3000, 'LinkedIn posts are limited to 3,000 characters.'),
  language: z.string().trim().min(2).max(32),
})

export type PostFormValues = z.infer<typeof postSchema>

type PostEditorFormProps = {
  defaultValues: PostFormValues
  isSaving: boolean
  serverError?: string
  onContentChange: (content: string) => void
  onSubmit: (values: PostFormValues) => void
}

export function PostEditorForm({
  defaultValues,
  isSaving,
  serverError,
  onContentChange,
  onSubmit,
}: PostEditorFormProps) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<PostFormValues>({ resolver: zodResolver(postSchema), values: defaultValues })
  const content = useWatch({ control, name: 'content' })

  return (
    <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label className="text-[11px] font-semibold text-slate-600" htmlFor="title">Internal title</label>
        <input
          className="app-input mt-1.5"
          id="title"
          placeholder="e.g. Why AI agents matter"
          {...register('title')}
        />
        {errors.title && <p className="mt-1 text-sm text-red-700">{errors.title.message}</p>}
      </div>
      <div>
        <div className="flex items-center justify-between gap-4">
          <label className="text-[11px] font-semibold text-slate-600" htmlFor="content">Post content</label>
          <span className={content.length > 3000 ? 'text-sm text-red-700' : 'text-sm text-slate-500'}>{content.length}/3000</span>
        </div>
        <textarea
          className="app-input mt-1.5 min-h-72 resize-y leading-6"
          id="content"
          placeholder="Share an insight, example, or question…"
          {...register('content', { onChange: (event) => onContentChange(event.target.value as string) })}
        />
        {errors.content && <p className="mt-1 text-sm text-red-700">{errors.content.message}</p>}
      </div>
      <div>
        <label className="text-[11px] font-semibold text-slate-600" htmlFor="language">Language</label>
        <input
          className="app-input mt-1.5"
          id="language"
          {...register('language')}
        />
        {errors.language && <p className="mt-1 text-sm text-red-700">Enter a valid language.</p>}
      </div>
      {serverError && <p role="alert" className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-800">{serverError}</p>}
      <button
        className="h-9 rounded-lg bg-[#4f5ff7] px-5 text-[12px] font-bold text-white hover:bg-[#3f4de0] disabled:cursor-not-allowed disabled:opacity-60"
        disabled={isSaving}
        type="submit"
      >
        {isSaving ? 'Saving…' : 'Save draft'}
      </button>
    </form>
  )
}
