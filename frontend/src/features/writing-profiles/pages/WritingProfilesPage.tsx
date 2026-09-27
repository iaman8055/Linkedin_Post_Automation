import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button, Card, EmptyState, PageHeader, Skeleton } from '../../../components/ui/Primitives'
import { ApiError } from '../../../services/api/client'
import { createWritingProfile, deleteWritingProfile, listWritingProfiles, updateWritingProfile, writingProfileKeys, type WritingProfile, type WritingProfileInput } from '../api'
import { WritingProfileForm } from '../components/WritingProfileForm'

export function WritingProfilesPage() {
  const [editing, setEditing] = useState<WritingProfile | null | undefined>(undefined)
  const client = useQueryClient()
  const profiles = useQuery({ queryKey: writingProfileKeys.all, queryFn: listWritingProfiles })
  const save = useMutation({ mutationFn: ({ profile, input }: { profile: WritingProfile | null; input: WritingProfileInput }) => profile ? updateWritingProfile(profile.id, input) : createWritingProfile(input), onSuccess: async () => { await client.invalidateQueries({ queryKey: writingProfileKeys.all }); setEditing(undefined) } })
  const remove = useMutation({ mutationFn: deleteWritingProfile, onSuccess: () => client.invalidateQueries({ queryKey: writingProfileKeys.all }) })
  const error = save.error instanceof ApiError ? save.error.message : save.isError ? 'The writing profile could not be saved.' : null
  return <div className="mx-auto max-w-[1120px]">
    <PageHeader title="Writing profiles" description="Keep your voice consistent across AI-generated content." action={<Button onClick={() => setEditing(null)}>Create profile</Button>}/>
    {error && <p className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-[12px] text-red-700" role="alert">{error}</p>}
    {editing !== undefined && <Card className="mb-5 p-5"><h2 className="mb-4 text-[15px] font-bold">{editing ? `Edit ${editing.name}` : 'Create writing profile'}</h2><WritingProfileForm profile={editing} pending={save.isPending} onCancel={() => setEditing(undefined)} onSubmit={(input) => save.mutate({ profile: editing, input })}/></Card>}
    {profiles.isLoading ? <div className="grid gap-4 md:grid-cols-2"><Skeleton className="h-52"/><Skeleton className="h-52"/></div> : profiles.data?.items.length ? <div className="grid gap-4 md:grid-cols-2">{profiles.data.items.map((profile) => <Card className="p-5" key={profile.id}><div className="flex items-start justify-between gap-3"><div><div className="flex items-center gap-2"><h2 className="text-[15px] font-bold">{profile.name}</h2>{profile.is_default && <span className="rounded-full bg-emerald-50 px-2 py-1 text-[9px] font-bold uppercase text-emerald-700">Default</span>}</div><p className="mt-1 text-[11px] text-slate-400">{profile.language} · {profile.tone || 'No tone specified'}</p></div></div><div className="mt-4 grid grid-cols-2 gap-3 text-[11px]"><Detail label="Sentence style" value={profile.sentence_style}/><Detail label="Technical depth" value={profile.technical_depth}/><Detail label="Emoji use" value={profile.emoji_preference}/><Detail label="Paragraphs" value={profile.paragraph_length}/></div>{profile.preferred_vocabulary.length > 0 && <div className="mt-4 flex flex-wrap gap-1.5">{profile.preferred_vocabulary.map((word) => <span className="rounded-md bg-[#eef1ff] px-2 py-1 text-[10px] font-semibold text-[#4f5ff7]" key={word}>{word}</span>)}</div>}<div className="mt-5 flex gap-2 border-t border-slate-100 pt-4"><Button variant="secondary" onClick={() => setEditing(profile)}>Edit</Button><Button variant="secondary" disabled={remove.isPending} onClick={() => remove.mutate(profile.id)}>Delete</Button>{!profile.is_default && <Button variant="secondary" onClick={() => save.mutate({ profile, input: { ...profile, is_default: true } })}>Set default</Button>}</div></Card>)}</div> : <EmptyState title="No writing profiles yet" description="Create a profile to teach generation workflows your preferred voice."/>}
  </div>
}

function Detail({ label, value }: { label: string; value: string | null }) { return <div><p className="font-bold text-slate-400">{label}</p><p className="mt-1 text-slate-700">{value || 'Not specified'}</p></div> }
