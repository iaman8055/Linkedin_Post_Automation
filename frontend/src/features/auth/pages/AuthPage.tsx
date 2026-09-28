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
  return <main className="min-h-screen bg-[#fbfafe] lg:grid lg:grid-cols-[1.08fr_0.92fr]">
    <section className="relative hidden overflow-hidden bg-gradient-to-br from-[#f3f0ff] via-[#faf8ff] to-[#fff0ee] px-14 py-11 lg:flex lg:flex-col lg:justify-between">
      <Brand />
      <div className="relative z-10 max-w-xl"><p className="text-[12px] font-extrabold uppercase tracking-[0.16em] text-[#6d4aff]">LinkedIn content, thoughtfully automated</p><h1 className="mt-5 text-5xl font-extrabold leading-[1.06] tracking-[-0.05em] text-[#201b30]">Create. Plan.<br/>Publish. <span className="bg-gradient-to-r from-[#6d4aff] to-[#f1737d] bg-clip-text text-transparent">Grow.</span></h1><p className="mt-6 max-w-md text-[15px] leading-7 text-[#6e687a]">A focused workspace for creating useful LinkedIn content, organizing campaigns, and publishing with confidence.</p><ul className="mt-8 space-y-3 text-sm text-[#514a5e]">{['Generate distinct drafts with AI','Review every post before it goes live','Keep campaigns and content organized'].map((item) => <li className="flex items-center gap-3" key={item}><span className="grid size-5 place-items-center rounded-full bg-[#6d4aff] text-white shadow-sm"><Icon className="size-3" name="check" /></span>{item}</li>)}</ul></div>
      <p className="text-xs text-slate-400">Built for focused, responsible content workflows.</p><div className="absolute -right-24 top-24 size-[420px] rounded-full bg-white/70"/><div className="absolute right-16 top-52 size-64 rounded-full border border-indigo-100"/>
    </section>
    <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-10"><div className="w-full max-w-[420px]"><div className="mb-10 lg:hidden"><Brand /></div><p className="text-xs font-extrabold uppercase tracking-[0.14em] text-[#6d4aff]">{mode === 'login' ? 'Welcome back' : 'Get started'}</p><h2 className="mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[#201b30]">{mode === 'login' ? 'Sign in to your workspace' : 'Create your account'}</h2><p className="mt-2 text-sm text-[#7a7386]">{mode === 'login' ? 'Continue planning and creating your content.' : 'Start building a consistent LinkedIn presence.'}</p>
      <form className="mt-8 space-y-4" onSubmit={handleSubmit(submit)}>{mode === 'register' && <AuthField label="Full name" error={errors.display_name?.message}><input autoComplete="name" className="app-input h-11" {...field('display_name')} /></AuthField>}<AuthField label="Email address" error={errors.email?.message}><input autoComplete="email" className="app-input h-11" type="email" {...field('email')} /></AuthField><AuthField label="Password" error={errors.password?.message}><input autoComplete={mode === 'login' ? 'current-password' : 'new-password'} className="app-input h-11" type="password" {...field('password')} /></AuthField>{auth.error && <p role="alert" className="rounded-lg bg-red-50 px-4 py-3 text-xs font-medium text-red-700">{auth.error instanceof ApiError ? auth.error.message : 'Unable to complete the request.'}</p>}<button className="mt-2 h-11 w-full rounded-[10px] bg-gradient-to-r from-[#7252ff] to-[#5a43e8] text-sm font-bold text-white shadow-[0_8px_20px_rgba(109,74,255,.22)] hover:-translate-y-px hover:shadow-[0_10px_25px_rgba(109,74,255,.3)] disabled:opacity-60" disabled={auth.isWorking} type="submit">{auth.isWorking ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}</button></form>
      <p className="mt-6 text-center text-sm text-[#7a7386]">{mode === 'login' ? 'New to AI Autopilot?' : 'Already have an account?'} <Link className="font-bold text-[#6d4aff]" to={mode === 'login' ? '/register' : '/login'}>{mode === 'login' ? 'Create an account' : 'Sign in'}</Link></p></div></section>
  </main>
}
function AuthField({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) { return <label className="block text-[13px] font-semibold text-slate-700">{label}<span className="mt-1.5 block">{children}</span>{error && <span className="mt-1 block text-xs font-normal text-red-600">{error}</span>}</label> }
export function Brand() { return <div className="flex items-center gap-2.5"><span className="relative grid size-8 place-items-center overflow-hidden rounded-[10px] bg-gradient-to-br from-[#7655ff] via-[#6a48f2] to-[#f1737d] font-black text-white shadow-[0_6px_16px_rgba(109,74,255,.22)]"><span className="relative z-10">A</span><span className="absolute -right-1 -top-1 size-3 rounded-full bg-white/25"/></span><span className="text-sm font-extrabold tracking-[-0.025em] text-[#201b30]">LinkedIn AI Autopilot</span></div> }
