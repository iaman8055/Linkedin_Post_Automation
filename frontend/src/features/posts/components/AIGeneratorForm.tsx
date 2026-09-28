import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { ApiError } from '../../../services/api/client'
import { generatePosts, type GeneratePostsResult } from '../api'
import { listWritingProfiles, writingProfileKeys } from '../../writing-profiles/api'
import { knowledgeKeys, listKnowledge } from '../../knowledge/api'

const generationSchema = z.object({
  topic: z.string().trim().min(2, 'Enter a topic.').max(120),
  subject: z.string().trim().min(2, 'Enter a subject.').max(240),
  post_type: z.enum(['educational', 'storytelling', 'personal_experience', 'technical', 'career_advice', 'industry_insight', 'case_study', 'opinion', 'promotional', 'question', 'poll']),
  audience: z.string().trim().min(2, 'Describe the audience.').max(240),
  tone: z.string().trim().min(2).max(120),
  language: z.string().trim().min(2).max(32),
  length: z.enum(['short', 'medium', 'long']),
  call_to_action: z.string().max(240),
  keywords: z.string().max(500),
  personal_experience: z.string().max(2000),
  reference_material: z.string().max(4000),
  desired_hashtags: z.string().max(500),
  include_hashtags: z.boolean(),
  hashtag_count: z.number().int().min(0).max(8),
  number_of_posts: z.number().int().min(1).max(10),
  writing_profile_id: z.string().nullable(),
  research_source_ids: z.array(z.string()),
  knowledge_item_ids: z.array(z.string()),
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
      topic: '', subject: '', post_type: 'educational', audience: '', tone: 'professional',
      language: 'English', length: 'medium', call_to_action: '', include_hashtags: true,
      keywords: '', personal_experience: '', reference_material: '', desired_hashtags: '',
      hashtag_count: 3, number_of_posts: 1, writing_profile_id: null, research_source_ids: [], knowledge_item_ids: [],
    },
  })
  const generation = useMutation({
    mutationFn: (values: GenerationFormValues) => generatePosts({
      ...values,
      call_to_action: values.call_to_action.trim() || null,
      keywords: splitList(values.keywords),
      personal_experience: values.personal_experience.trim() || null,
      reference_material: values.reference_material.trim() || null,
      desired_hashtags: splitList(values.desired_hashtags),
    }),
    onSuccess: (result) => onGenerated(result),
  })
  const profiles = useQuery({ queryKey: writingProfileKeys.all, queryFn: listWritingProfiles })
  const knowledge = useQuery({ queryKey: knowledgeKeys.all, queryFn: listKnowledge })

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
        <Field label="Post type" error={errors.post_type?.message}><select className={inputClass} {...register('post_type')}>{postTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field>
        <Field label="Audience" error={errors.audience?.message}><input className={inputClass} list="audiences" placeholder="Choose or enter a custom audience" {...register('audience')} /><datalist id="audiences">{audiences.map((item) => <option key={item} value={item}/>)}</datalist></Field>
        <Field label="Tone" error={errors.tone?.message}><select className={inputClass} {...register('tone')}>{tones.map((item) => <option key={item} value={item.toLowerCase()}>{item}</option>)}</select></Field>
        <Field label="Writing profile" error={errors.writing_profile_id?.message}><select className={inputClass} {...register('writing_profile_id', { setValueAs: (value) => value || null })}><option value="">No profile</option>{profiles.data?.items?.map((profile) => <option key={profile.id} value={profile.id}>{profile.name}{profile.is_default ? ' (default)' : ''}</option>)}</select></Field>
        <Field label="Language" error={errors.language?.message}><input className={inputClass} {...register('language')} /></Field>
        <Field label="Length" error={errors.length?.message}>
          <select className={inputClass} {...register('length')}><option value="short">Short</option><option value="medium">Medium</option><option value="long">Long</option></select>
        </Field>
        <Field label="Call to action (optional)" error={errors.call_to_action?.message}><input className={inputClass} {...register('call_to_action')} /></Field>
        <Field label="Keywords (comma separated)" error={errors.keywords?.message}><input className={inputClass} {...register('keywords')} /></Field>
        <Field label="Desired hashtags" error={errors.desired_hashtags?.message}><input className={inputClass} placeholder="#AI, #Leadership" {...register('desired_hashtags')} /></Field>
        <Field label="Personal experience (optional)" error={errors.personal_experience?.message}><textarea className={`${inputClass} min-h-24`} {...register('personal_experience')} /></Field>
        <Field label="Reference material (optional)" error={errors.reference_material?.message}><textarea className={`${inputClass} min-h-24`} {...register('reference_material')} /></Field>
        <fieldset className="rounded-lg border border-slate-200 p-3 md:col-span-2"><legend className="px-1 text-[11px] font-semibold text-slate-600">Use my knowledge (optional)</legend><p className="mb-2 text-[11px] text-slate-400">Only checked items are shared with the AI for this generation.</p><div className="grid gap-2 sm:grid-cols-2">{knowledge.data?.items?.map((item) => <label className="flex items-center gap-2 rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-700" key={item.id}><input type="checkbox" value={item.id} {...register('knowledge_item_ids')}/><span className="truncate">{item.title}</span></label>)}{!knowledge.data?.items?.length && <span className="text-xs text-slate-400">No knowledge items saved yet.</span>}</div></fieldset>
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

const postTypes = [
  ['educational', 'Educational'], ['storytelling', 'Storytelling'], ['personal_experience', 'Personal experience'],
  ['technical', 'Technical'], ['career_advice', 'Career advice'], ['industry_insight', 'Industry insight'],
  ['case_study', 'Case study'], ['opinion', 'Opinion'], ['promotional', 'Promotional'],
  ['question', 'Question'], ['poll', 'Poll'],
] as const
const tones = ['Professional', 'Casual', 'Friendly', 'Thought-provoking', 'Inspirational', 'Humorous', 'Bold', 'Conversational']
const audiences = ['Developers', 'Recruiters', 'Founders', 'Students', 'Marketing professionals', 'Designers', 'Job seekers']
function splitList(value: string) { return value.split(',').map((item) => item.trim()).filter(Boolean) }

const inputClass = 'app-input mt-1.5'

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return <label className="text-[11px] font-semibold text-slate-600">{label}{children}{error && <span className="mt-1 block font-normal text-red-700">{error}</span>}</label>
}
