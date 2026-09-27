import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { Button } from '../../../components/ui/Primitives'
import { ApiError } from '../../../services/api/client'
import { createPost, postKeys } from '../../posts/api'
import { renderTemplate, type ContentTemplate } from '../api'

export function UseTemplatePanel({ template, onClose }: { template: ContentTemplate; onClose: () => void }) {
  const navigate = useNavigate(); const client = useQueryClient()
  const [values, setValues] = useState<Record<string, string>>(() => Object.fromEntries(template.placeholders.map((name) => [name, ''])))
  const useTemplate = useMutation({
    mutationFn: async () => {
      const rendered = await renderTemplate(template.id, values)
      return createPost({ title: template.name, content: rendered.content, language: 'English' })
    },
    onSuccess: async (post) => { await client.invalidateQueries({ queryKey: postKeys.all }); navigate(`/create/${post.id}`) },
  })
  return <div><p className="text-[11px] text-slate-500">Fill each placeholder. The rendered result will be saved as a reviewable draft.</p><div className="mt-4 space-y-3">{template.placeholders.map((name) => <label className="block text-[11px] font-bold text-slate-700" key={name}>{name}<textarea className="app-input mt-1.5 min-h-20" required value={values[name]} onChange={(event) => setValues((current) => ({ ...current, [name]: event.target.value }))}/></label>)}</div>
    {!template.placeholders.length && <pre className="mt-4 whitespace-pre-wrap rounded-lg bg-slate-50 p-4 text-[11px] leading-5 text-slate-600">{template.body}</pre>}
    {useTemplate.isError && <p className="mt-3 text-[11px] text-red-700">{useTemplate.error instanceof ApiError ? useTemplate.error.message : 'The draft could not be created.'}</p>}
    <div className="mt-4 flex gap-2"><Button disabled={useTemplate.isPending || Object.values(values).some((value) => !value.trim())} onClick={() => useTemplate.mutate()}>Create draft</Button><Button variant="secondary" onClick={onClose}>Cancel</Button></div>
  </div>
}
