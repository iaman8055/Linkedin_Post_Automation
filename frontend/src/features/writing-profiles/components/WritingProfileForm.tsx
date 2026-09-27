import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { Button } from '../../../components/ui/Primitives'
import type { WritingProfile, WritingProfileInput } from '../api'

const schema = z.object({
  name: z.string().trim().min(1, 'Enter a profile name.').max(120),
  tone: z.string().max(80), sentence_style: z.string().max(80),
  language: z.string().trim().min(2).max(32), emoji_preference: z.string().max(32),
  paragraph_length: z.string().max(32), technical_depth: z.string().max(32),
  cta_preference: z.string().max(500), preferred_vocabulary: z.string().max(240),
  guidance: z.string().max(2000), is_default: z.boolean(),
})
type Values = z.infer<typeof schema>
const optional = (value: string) => value.trim() || null

export function WritingProfileForm({ profile, pending, onCancel, onSubmit }: {
  profile: WritingProfile | null
  pending: boolean
  onCancel: () => void
  onSubmit: (input: WritingProfileInput) => void
}) {
  const form = useForm<Values>({ resolver: zodResolver(schema), values: {
    name: profile?.name ?? '', tone: profile?.tone ?? '', sentence_style: profile?.sentence_style ?? '',
    language: profile?.language ?? 'English', emoji_preference: profile?.emoji_preference ?? 'Occasional',
    paragraph_length: profile?.paragraph_length ?? 'Short', technical_depth: profile?.technical_depth ?? 'Balanced',
    cta_preference: profile?.cta_preference ?? '', preferred_vocabulary: profile?.preferred_vocabulary.join(', ') ?? '',
    guidance: typeof profile?.additional_guidance.notes === 'string' ? profile.additional_guidance.notes : '',
    is_default: profile?.is_default ?? false,
  } })
  return <form className="grid gap-4 sm:grid-cols-2" onSubmit={form.handleSubmit((values) => onSubmit({
    name: values.name, tone: optional(values.tone), sentence_style: optional(values.sentence_style),
    language: values.language, emoji_preference: optional(values.emoji_preference),
    paragraph_length: optional(values.paragraph_length), technical_depth: optional(values.technical_depth),
    cta_preference: optional(values.cta_preference),
    preferred_vocabulary: values.preferred_vocabulary.split(',').map((word) => word.trim()).filter(Boolean),
    additional_guidance: values.guidance.trim() ? { notes: values.guidance.trim() } : {}, is_default: values.is_default,
  }))}>
    <Field label="Profile name" error={form.formState.errors.name?.message}><input className="app-input mt-1.5" {...form.register('name')}/></Field>
    <Field label="Language"><input className="app-input mt-1.5" {...form.register('language')}/></Field>
    <Field label="Tone"><input className="app-input mt-1.5" placeholder="Warm, direct, thoughtful" {...form.register('tone')}/></Field>
    <Field label="Sentence style"><input className="app-input mt-1.5" placeholder="Concise with varied rhythm" {...form.register('sentence_style')}/></Field>
    <Field label="Emoji preference"><select className="app-input mt-1.5" {...form.register('emoji_preference')}><option>None</option><option>Occasional</option><option>Frequent</option></select></Field>
    <Field label="Paragraph length"><select className="app-input mt-1.5" {...form.register('paragraph_length')}><option>Short</option><option>Medium</option><option>Long</option></select></Field>
    <Field label="Technical depth"><select className="app-input mt-1.5" {...form.register('technical_depth')}><option>Accessible</option><option>Balanced</option><option>Expert</option></select></Field>
    <Field label="CTA preference"><input className="app-input mt-1.5" placeholder="End with an open question" {...form.register('cta_preference')}/></Field>
    <div className="sm:col-span-2"><Field label="Preferred vocabulary (comma separated)"><input className="app-input mt-1.5" placeholder="practical, evidence-led, systems thinking" {...form.register('preferred_vocabulary')}/></Field></div>
    <div className="sm:col-span-2"><Field label="Additional guidance"><textarea className="app-input mt-1.5 min-h-24" placeholder="Any personal writing rules the AI should follow" {...form.register('guidance')}/></Field></div>
    <label className="flex items-center gap-2 text-[12px] font-semibold text-slate-600"><input type="checkbox" {...form.register('is_default')}/>Use as my default writing profile</label>
    <div className="flex justify-end gap-2 sm:col-span-2"><Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button><Button disabled={pending} type="submit">{pending ? 'Saving…' : profile ? 'Save changes' : 'Create profile'}</Button></div>
  </form>
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return <label className="text-[11px] font-semibold text-slate-600">{label}{children}{error && <span className="mt-1 block text-red-700">{error}</span>}</label>
}
