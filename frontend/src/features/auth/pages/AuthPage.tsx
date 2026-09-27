import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { Icon } from '../../../components/ui/Icon'
import { ApiError } from '../../../services/api/client'
import { useAuth } from '../AuthProvider'

const loginSchema = z.object({ email: z.email('Enter a valid email.'), password: z.string().min(1, 'Enter your password.') })
const registerSchema = loginSchema.extend({ display_name: z.string().trim().min(1, 'Enter your name.').max(120), password: z.string().min(12, 'Use at least 12 characters.').max(128) })
type Values = { display_name?: string; email: string; password: string }

export function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const auth = useAuth(); const navigate = useNavigate(); const location = useLocation()
  const schema = mode === 'login' ? loginSchema : registerSchema
  const { register: field, handleSubmit, formState: { errors } } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { display_name: '', email: '', password: '' } })
  if (auth.isAuthenticated) return <Navigate replace to="/dashboard" />
  const submit = async (values: Values) => {
    if (mode === 'login') await auth.signIn({ email: values.email, password: values.password })
    else await auth.signUp({ display_name: values.display_name ?? '', email: values.email, password: values.password })
    const target = (location.state as { from?: string } | null)?.from ?? '/dashboard'; navigate(target, { replace: true })
  }
  return <main className="min-h-screen bg-white lg:grid lg:grid-cols-[1.06fr_0.94fr]">
    <section className="relative hidden overflow-hidden bg-[#f4f6ff] px-12 py-10 lg:flex lg:flex-col lg:justify-between">
      <Brand />
      <div className="relative z-10 max-w-xl"><p className="text-[13px] font-bold uppercase tracking-[0.14em] text-[#4f5ff7]">LinkedIn content, thoughtfully automated</p><h1 className="mt-5 text-5xl font-extrabold leading-[1.08] tracking-[-0.045em] text-[#172033]">Create. Plan.<br/>Publish. <span className="text-[#4f5ff7]">Grow.</span></h1><p className="mt-6 max-w-md text-[15px] leading-7 text-slate-600">A focused workspace for creating useful LinkedIn content, organizing campaigns, and publishing with confidence.</p><ul className="mt-8 space-y-3 text-sm text-slate-700">{['Generate distinct drafts with AI','Review every post before it goes live','Keep campaigns and content organized'].map((item) => <li className="flex items-center gap-3" key={item}><span className="grid size-5 place-items-center rounded-full bg-[#4f5ff7] text-white"><Icon className="size-3" name="check" /></span>{item}</li>)}</ul></div>
      <p className="text-xs text-slate-400">Built for focused, responsible content workflows.</p><div className="absolute -right-24 top-24 size-[420px] rounded-full bg-white/70"/><div className="absolute right-16 top-52 size-64 rounded-full border border-indigo-100"/>
    </section>
    <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-10"><div className="w-full max-w-[420px]"><div className="mb-10 lg:hidden"><Brand /></div><p className="text-xs font-bold uppercase tracking-[0.12em] text-[#4f5ff7]">{mode === 'login' ? 'Welcome back' : 'Get started'}</p><h2 className="mt-2 text-3xl font-bold tracking-[-0.035em]">{mode === 'login' ? 'Sign in to your workspace' : 'Create your account'}</h2><p className="mt-2 text-sm text-slate-500">{mode === 'login' ? 'Continue planning and creating your content.' : 'Start building a consistent LinkedIn presence.'}</p>
      <form className="mt-8 space-y-4" onSubmit={handleSubmit(submit)}>{mode === 'register' && <AuthField label="Full name" error={errors.display_name?.message}><input autoComplete="name" className="app-input h-11" {...field('display_name')} /></AuthField>}<AuthField label="Email address" error={errors.email?.message}><input autoComplete="email" className="app-input h-11" type="email" {...field('email')} /></AuthField><AuthField label="Password" error={errors.password?.message}><input autoComplete={mode === 'login' ? 'current-password' : 'new-password'} className="app-input h-11" type="password" {...field('password')} /></AuthField>{auth.error && <p role="alert" className="rounded-lg bg-red-50 px-4 py-3 text-xs font-medium text-red-700">{auth.error instanceof ApiError ? auth.error.message : 'Unable to complete the request.'}</p>}<button className="mt-2 h-11 w-full rounded-lg bg-[#4f5ff7] text-sm font-bold text-white shadow-sm hover:bg-[#3f4de0] disabled:opacity-60" disabled={auth.isWorking} type="submit">{auth.isWorking ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}</button></form>
      <p className="mt-6 text-center text-sm text-slate-500">{mode === 'login' ? 'New to AI Autopilot?' : 'Already have an account?'} <Link className="font-bold text-[#4f5ff7]" to={mode === 'login' ? '/register' : '/login'}>{mode === 'login' ? 'Create an account' : 'Sign in'}</Link></p></div></section>
  </main>
}
function AuthField({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) { return <label className="block text-[13px] font-semibold text-slate-700">{label}<span className="mt-1.5 block">{children}</span>{error && <span className="mt-1 block text-xs font-normal text-red-600">{error}</span>}</label> }
export function Brand() { return <div className="flex items-center gap-2.5"><span className="grid size-8 place-items-center rounded-lg bg-[#4f5ff7] font-black text-white">A</span><span className="text-sm font-extrabold tracking-[-0.02em] text-[#172033]">LinkedIn AI Autopilot</span></div> }
