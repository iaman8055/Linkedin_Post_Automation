type LinkedInPreviewProps = {
  content: string
}

export function LinkedInPreview({ content }: LinkedInPreviewProps) {
  return (
    <section aria-label="LinkedIn-style preview" className="app-card overflow-hidden">
      <div className="flex items-center gap-3 p-5">
        <div aria-hidden="true" className="grid size-10 place-items-center rounded-full bg-[#e8ebff] text-[11px] font-bold text-[#4f5ff7]">
          You
        </div>
        <div>
          <p className="text-[12px] font-bold text-slate-900">Your LinkedIn profile</p>
          <p className="text-xs text-slate-500">Preview · Just now</p>
        </div>
      </div>
      <div className="min-h-48 whitespace-pre-wrap px-5 pb-5 text-[13px] leading-6 text-slate-700">
        {content || <span className="text-slate-400">Your post will appear here as you write.</span>}
      </div>
      <div className="border-t border-slate-100 px-5 py-3 text-xs text-slate-400">
        Like &nbsp;·&nbsp; Comment &nbsp;·&nbsp; Repost &nbsp;·&nbsp; Send
      </div>
      <p className="border-t border-slate-100 px-5 py-3 text-xs text-slate-500">
        This is an approximate preview, not an exact replica of LinkedIn.
      </p>
    </section>
  )
}
