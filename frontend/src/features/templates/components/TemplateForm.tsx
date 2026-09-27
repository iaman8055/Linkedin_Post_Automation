import { zodResolver } from '@hookform/resolvers/zod'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'

import { Button } from '../../../components/ui/Primitives'
import { ApiError } from '../../../services/api/client'
import type { ContentTemplate, TemplateInput } from '../api'

const schema = z.object({
  name: z.string().trim().min(1, 'Enter a template name.').max(160),
  description: z.string().max(2000),
  body: z.string().trim().min(1, 'Write a template body.').max(10_000),
})
type Values = z.infer<typeof schema>
const tokens = (body: string) => [...new Set([...body.matchAll(/{{\s*([A-Za-z][A-Za-z0-9_]*)\s*}}/g)].map((match) => match[1]))]

export function TemplateForm({ template, pending, error, onCancel, onSubmit }: {
  template: ContentTemplate | null
  pending: boolean
  error: unknown
  onCancel: () => void
  onSubmit: (input: TemplateInput) => void
}) {
  const form = useForm<Values>({ resolver: zodResolver(schema), values: { name: template?.name ?? '', description: template?.description ?? '', body: template?.body ?? 'HOOK: {{topic}}\n\nKEY INSIGHT:\n{{insight}}\n\nCTA:\n{{cta}}' } })
  const body = useWatch({ control: form.control, name: 'body' })
  const placeholders = tokens(body)
  return <form className="space-y-4" onSubmit={form.handleSubmit((values) => onSubmit({ name: values.name, description: values.description.trim() || null, body: values.body }))}>
    <div><label className="text-[11px] font-bold text-slate-700" htmlFor="template-name">Name</label><input className="app-input mt-1.5" id="template-name" {...form.register('name')}/>{form.formState.errors.name && <p className="mt-1 text-[11px] text-red-700">{form.formState.errors.name.message}</p>}</div>
    <div><label className="text-[11px] font-bold text-slate-700" htmlFor="template-description">Description</label><input className="app-input mt-1.5" id="template-description" placeholder="When should this structure be used?" {...form.register('description')}/></div>
    <div><div className="flex items-center justify-between"><label className="text-[11px] font-bold text-slate-700" htmlFor="template-body">Structure</label><span className="text-[10px] text-slate-400">{body.length}/10,000</span></div><textarea className="app-input mt-1.5 min-h-72 font-mono text-[12px] leading-6" id="template-body" {...form.register('body')}/>{form.formState.errors.body && <p className="mt-1 text-[11px] text-red-700">{form.formState.errors.body.message}</p>}</div>
    <div><p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Detected placeholders</p><div className="mt-2 flex flex-wrap gap-1.5">{placeholders.length ? placeholders.map((name) => <span className="rounded-md bg-[#eef1ff] px-2 py-1 text-[10px] font-bold text-[#4f5ff7]" key={name}>{`{{${name}}}`}</span>) : <span className="text-[11px] text-slate-400">No placeholders</span>}</div></div>
    {error != null && <p className="rounded-lg bg-red-50 px-3 py-2 text-[11px] text-red-700" role="alert">{error instanceof ApiError ? error.message : 'The template could not be saved.'}</p>}
    <div className="flex gap-2"><Button disabled={pending} type="submit">{template ? 'Save changes' : 'Create template'}</Button><Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button></div>
  </form>
}
