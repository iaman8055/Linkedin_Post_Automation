import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { Button } from '../../../components/ui/Primitives'
import { ApiError } from '../../../services/api/client'
import { generateHooks } from '../api'

export function HookGenerator({ onUseHook }: { onUseHook: (hook: string) => void }) {
  const [topic, setTopic] = useState('')
  const hooks = useMutation({ mutationFn: () => generateHooks(topic.trim(), 7) })
  return <section className="app-card p-5"><p className="text-[10px] font-bold uppercase tracking-[0.12em] text-violet-500">Hook generator</p><h2 className="mt-2 text-[16px] font-bold">Find a stronger opening</h2><p className="mt-1 text-[11px] leading-5 text-slate-500">Generate varied openings, then insert one into the manual editor.</p><label className="mt-4 block text-[11px] font-semibold text-slate-600">Topic<input className="app-input mt-1.5" onChange={(event) => setTopic(event.target.value)} value={topic}/></label><Button className="mt-3 w-full" disabled={topic.trim().length < 2 || hooks.isPending} onClick={() => hooks.mutate()}>{hooks.isPending ? '✨ Generating hooks…' : 'Generate 7 hooks'}</Button>{hooks.isError && <p className="mt-3 text-[11px] text-red-700">{hooks.error instanceof ApiError ? hooks.error.message : 'Hooks could not be generated.'}</p>}{hooks.data && <div className="mt-4 max-h-96 space-y-2 overflow-y-auto">{hooks.data.hooks.map((hook, index) => <article className="rounded-lg border border-slate-100 p-3" key={`${hook.category}-${index}`}><p className="text-[9px] font-bold uppercase tracking-wide text-violet-500">{hook.category.replaceAll('_', ' ')}</p><p className="mt-1 text-[11px] leading-5 text-slate-700">{hook.text}</p><button className="mt-2 text-[10px] font-bold text-[#4f5ff7]" onClick={() => onUseHook(hook.text)} type="button">Use hook</button></article>)}</div>}</section>
}
