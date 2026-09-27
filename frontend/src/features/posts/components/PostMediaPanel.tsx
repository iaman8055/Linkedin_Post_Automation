import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button, Skeleton } from '../../../components/ui/Primitives'
import { ApiError } from '../../../services/api/client'
import { deletePostMedia, listPostMedia, uploadPostMedia } from '../api'

const mediaKey = (postId: string) => ['posts', postId, 'media'] as const

export function PostMediaPanel({ postId, editable }: { postId: string; editable: boolean }) {
  const client = useQueryClient()
  const media = useQuery({ queryKey: mediaKey(postId), queryFn: () => listPostMedia(postId) })
  const refresh = () => client.invalidateQueries({ queryKey: mediaKey(postId) })
  const upload = useMutation({ mutationFn: (file: File) => uploadPostMedia(postId, file), onSuccess: refresh })
  const remove = useMutation({ mutationFn: deletePostMedia, onSuccess: refresh })
  const error = upload.error instanceof ApiError ? upload.error.message : upload.isError ? 'The file could not be uploaded.' : null
  return <section className="app-card mt-5 p-5">
    <div className="flex items-start justify-between gap-4"><div><p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Media</p><h2 className="mt-1 text-[14px] font-bold">Post attachments</h2><p className="mt-1 text-[10px] text-slate-400">Images, MP4 video, or PDF documents. LinkedIn publishing remains text-only.</p></div>{editable && <label className="inline-flex h-9 cursor-pointer items-center rounded-lg bg-[#4f5ff7] px-3.5 text-[12px] font-bold text-white">{upload.isPending ? 'Uploading…' : 'Upload'}<input accept="image/jpeg,image/png,image/gif,image/webp,video/mp4,application/pdf" className="sr-only" disabled={upload.isPending} onChange={(event) => { const file = event.target.files?.[0]; if (file) upload.mutate(file); event.target.value = '' }} type="file"/></label>}</div>
    {error && <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-[11px] text-red-700" role="alert">{error}</p>}
    {media.isLoading ? <Skeleton className="mt-4 h-20"/> : media.data?.items.length ? <div className="mt-4 space-y-2">{media.data.items.map((item) => <div className="flex items-center gap-3 rounded-lg border border-slate-100 p-3" key={item.id}><span className="grid size-9 place-items-center rounded-lg bg-[#eef1ff] text-[10px] font-bold text-[#4f5ff7]">{item.media_type.slice(0, 3)}</span><div className="min-w-0 flex-1"><p className="truncate text-[11px] font-bold">{item.metadata_json.filename || 'Attachment'}</p><p className="mt-0.5 text-[9px] text-slate-400">{item.mime_type} · {formatBytes(item.size_bytes)}</p></div>{editable && <Button aria-label={`Delete ${item.metadata_json.filename || 'attachment'}`} disabled={remove.isPending} onClick={() => remove.mutate(item.id)} variant="danger">Delete</Button>}</div>)}</div> : <p className="mt-4 rounded-lg border border-dashed border-slate-200 px-4 py-6 text-center text-[11px] text-slate-400">No media attached.</p>}
  </section>
}

function formatBytes(value: number | null) {
  if (value == null) return 'Unknown size'
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 / 1024).toFixed(1)} MB`
}
