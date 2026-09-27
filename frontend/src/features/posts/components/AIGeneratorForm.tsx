import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { ApiError } from '../../../services/api/client'
import { generatePosts, type GeneratePostsResult } from '../api'

const generationSchema = z.object({
  topic: z.string().trim().min(2, 'Enter a topic.').max(120),
  subject: z.string().trim().min(2, 'Enter a subject.').max(240),
  audience: z.string().trim().min(2, 'Describe the audience.').max(240),
  tone: z.string().trim().min(2).max(120),
  language: z.string().trim().min(2).max(32),
  length: z.enum(['short', 'medium', 'long']),
  call_to_action: z.string().max(240),
  include_hashtags: z.boolean(),
  hashtag_count: z.number().int().min(0).max(8),
  number_of_posts: z.number().int().min(1).max(10),
})

type GenerationFormValues = z.infer<typeof generationSchema>

type AIGeneratorFormProps = {
  onGenerated: (result: GeneratePostsResult) => void
}

export function AIGeneratorForm({ onGenerated }: AIGeneratorFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<GenerationFormValues>({
    resolver: zodResolver(generationSchema),
    defaultValues: {
      topic: '', subject: '', audience: '', tone: 'professional and conversational',
      language: 'English', length: 'medium', call_to_action: '', include_hashtags: true,
      hashtag_count: 3, number_of_posts: 1,
    },
  })
  const generation = useMutation({
    mutationFn: (values: GenerationFormValues) => generatePosts({
      ...values,
      call_to_action: values.call_to_action.trim() || null,
    }),
    onSuccess: (result) => onGenerated(result),
  })

  return (
    <section className="app-card p-5 sm:p-6">
      <div className="mb-5">
        <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#4f5ff7]">AI generation</p>
        <h2 className="mt-1 text-[16px] font-bold">Post details</h2>
        <p className="mt-1 text-[12px] text-slate-500">Create distinct drafts for review. Nothing is published automatically.</p>
      </div>
      <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit((values) => generation.mutate(values))}>
        <Field label="Topic" error={errors.topic?.message}><input className={inputClass} {...register('topic')} /></Field>
        <Field label="Subject" error={errors.subject?.message}><input className={inputClass} {...register('subject')} /></Field>
        <Field label="Audience" error={errors.audience?.message}><input className={inputClass} {...register('audience')} /></Field>
        <Field label="Tone" error={errors.tone?.message}><input className={inputClass} {...register('tone')} /></Field>
        <Field label="Language" error={errors.language?.message}><input className={inputClass} {...register('language')} /></Field>
        <Field label="Length" error={errors.length?.message}>
          <select className={inputClass} {...register('length')}><option value="short">Short</option><option value="medium">Medium</option><option value="long">Long</option></select>
        </Field>
        <Field label="Call to action (optional)" error={errors.call_to_action?.message}><input className={inputClass} {...register('call_to_action')} /></Field>
        <Field label="Number of posts" error={errors.number_of_posts?.message}><input className={inputClass} max="10" min="1" type="number" {...register('number_of_posts', { valueAsNumber: true })} /></Field>
        <label className="flex items-center gap-3 text-sm font-medium text-slate-700">
          <input className="size-4" type="checkbox" {...register('include_hashtags')} /> Include hashtags
        </label>
        <Field label="Hashtags per post" error={errors.hashtag_count?.message}><input className={inputClass} max="8" min="0" type="number" {...register('hashtag_count', { valueAsNumber: true })} /></Field>
        <div className="md:col-span-2">
          {generation.isError && (
            <p role="alert" className="mb-3 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-800">
              {generation.error instanceof ApiError ? generation.error.message : 'Posts could not be generated.'}
            </p>
          )}
          <button className="h-10 w-full rounded-lg bg-[#4f5ff7] px-5 text-[13px] font-bold text-white shadow-sm hover:bg-[#3f4de0] disabled:opacity-60" disabled={generation.isPending} type="submit">
            {generation.isPending ? 'Generating…' : 'Generate drafts'}
          </button>
        </div>
      </form>
    </section>
  )
}

const inputClass = 'app-input mt-1.5'

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return <label className="text-[11px] font-semibold text-slate-600">{label}{children}{error && <span className="mt-1 block font-normal text-red-700">{error}</span>}</label>
}
