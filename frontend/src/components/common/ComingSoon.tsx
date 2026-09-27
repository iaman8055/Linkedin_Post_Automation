import { Icon } from '../ui/Icon'
import { Card, PageHeader } from '../ui/Primitives'

export function ComingSoon({ title, description }: { title: string; description?: string }) {
  return <div className="mx-auto max-w-[1120px]"><PageHeader description={description ?? `${title} is planned for a later backend milestone.`} title={title}/><Card className="grid min-h-[390px] place-items-center p-8"><div className="max-w-md text-center"><span className="mx-auto grid size-12 place-items-center rounded-xl bg-[#eef1ff] text-[#4f5ff7]"><Icon name="calendar"/></span><h2 className="mt-4 text-lg font-bold">The workspace is ready</h2><p className="mt-2 text-[13px] leading-6 text-slate-500">There is no production API for this feature yet, so this screen intentionally contains no sample records or invented metrics. It will become interactive when its backend phase is implemented.</p><span className="mt-5 inline-flex rounded-full bg-slate-100 px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-slate-500">Not connected yet</span></div></Card></div>
}
