import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import type { CampaignInput } from '../api'

const schema = z.object({
  name: z.string().trim().min(1, 'Enter a campaign name.').max(160),
  topic: z.string().trim().min(1, 'Enter a topic.').max(160),
  description: z.string().max(5000),
  duration_days: z.number().int().min(1).max(3650).nullable(),
  approval_mode: z.enum(['MANUAL', 'AUTOMATIC']),
  default_posting_time: z.string(),
  timezone: z.string().trim().min(1).max(64),
})

type FormValues = z.infer<typeof schema>
type CampaignFormProps = {
  initial?: Partial<FormValues>
  isSaving: boolean
  submitLabel: string
  onSubmit: (input: CampaignInput) => void
}

export function CampaignForm({ initial, isSaving, submitLabel, onSubmit }: CampaignFormProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '', topic: '', description: '', duration_days: 7, approval_mode: 'MANUAL',
      default_posting_time: '', timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
      ...initial,
    },
  })
  return (
    <form className="grid gap-4 sm:grid-cols-2" onSubmit={handleSubmit((values) => onSubmit({
      ...values,
      description: values.description.trim() || null,
      default_posting_time: values.default_posting_time || null,
    }))}>
      <Field label="Campaign name" error={errors.name?.message}><input className={inputClass} {...register('name')} /></Field>
      <Field label="Topic" error={errors.topic?.message}><input className={inputClass} {...register('topic')} /></Field>
      <Field label="Duration in days" error={errors.duration_days?.message}><input className={inputClass} min="1" type="number" {...register('duration_days', { setValueAs: (value) => value === '' ? null : Number(value) })} /></Field>
      <Field label="Timezone" error={errors.timezone?.message}><input className={inputClass} {...register('timezone')} /></Field>
      <Field label="Approval mode" error={errors.approval_mode?.message}>
        <select className={inputClass} {...register('approval_mode')}><option value="MANUAL">Manual review</option><option value="AUTOMATIC">Automatic</option></select>
      </Field>
      <Field label="Default posting time" error={errors.default_posting_time?.message}><input className={inputClass} type="time" {...register('default_posting_time')} /></Field>
      <div className="sm:col-span-2"><Field label="Description" error={errors.description?.message}><textarea className={`${inputClass} min-h-24`} {...register('description')} /></Field></div>
      <div className="sm:col-span-2"><button className="h-9 rounded-lg bg-[#4f5ff7] px-5 text-[12px] font-bold text-white hover:bg-[#3f4de0] disabled:opacity-60" disabled={isSaving} type="submit">{isSaving ? 'Saving…' : submitLabel}</button></div>
    </form>
  )
}

const inputClass = 'app-input mt-1.5'
function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return <label className="text-[11px] font-semibold text-slate-600">{label}{children}{error && <span className="mt-1 block font-normal text-red-700">{error}</span>}</label>
}
