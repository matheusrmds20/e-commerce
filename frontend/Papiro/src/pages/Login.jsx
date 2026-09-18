import { useEffect, useRef, useState } from 'react'
import Field from '../components/Field'
import TextLink from '../components/TextLink'
import Quill from '../components/Quill'
import { useAuth } from '../context/auth-context'

export default function Login({ onEntrar }) {
  const [mostrarSenha, setMostrarSenha] = useState(false)
  const [form, setForm] = useState({ email: '', password: '' })
  const [erro, setErro] = useState(null) // { message, code, details }
  const [enviando, setEnviando] = useState(false)
  const [sucesso, setSucesso] = useState(false)

  const { login } = useAuth()
  const timerRef = useRef(null)

  // Evita que o timer de redirecionamento dispare após sair da tela.
  useEffect(() => () => clearTimeout(timerRef.current), [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((atual) => ({ ...atual, [name]: value }))
  }

  /** Erro de validação (422) por campo, para exibir sob o input certo. */
  const erroDoCampo = (campo) =>
    erro?.details?.find((d) => d.field === campo)?.message

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (enviando || sucesso) return

    setErro(null)
    setEnviando(true)

    try {
      await login({ email: form.email, password: form.password })
      // Pequena pausa para o leitor ver a confirmação antes de sair da tela.
      setSucesso(true)
      timerRef.current = setTimeout(() => onEntrar?.(), 900)
    } catch (error) {
      setErro(error)
      setEnviando(false)
    }
  }

  return (
    <main className="flex flex-col items-center px-5 py-14 sm:py-20">
      {/* Folha de papel */}
      <section className="relative w-full max-w-[560px] rounded-md bg-cream-soft shadow-[0_1px_2px_rgba(75,54,33,0.04),0_18px_50px_-20px_rgba(75,54,33,0.22)] ring-1 ring-line">
        <div className="px-8 pb-14 pt-16 sm:px-20 sm:pb-16 sm:pt-20">
          <header className="text-center">
            <p className="label-caps text-gold">Entrar</p>

            <h1 className="mt-4 font-display text-[2.75rem] leading-[1.1] font-normal tracking-[-0.01em] text-coffee sm:text-[3.35rem]">
              Um convite silencioso
            </h1>

            <p className="mx-auto mt-5 max-w-[21rem] font-body text-[0.98rem] font-normal leading-relaxed text-coffee-soft">
              Sua estante está esperando. Entre para continuar de onde parou.
            </p>
          </header>

          {erro && !erro.details && (
            <div
              role="alert"
              className="mt-8 rounded-sm border border-[#a4533f]/30 bg-[#a4533f]/[0.06] px-4 py-3 text-center font-body text-[0.86rem] font-medium tracking-wide text-[#a4533f]"
            >
              {erro.message}
            </div>
          )}

          {sucesso && (
            <div
              role="status"
              className="mt-8 rounded-sm border border-gold/40 bg-gold/[0.08] px-4 py-3 text-center font-body text-[0.86rem] font-medium tracking-wide text-coffee"
            >
              Bem-vindo de volta. Abrindo sua estante…
            </div>
          )}

          <form
            onSubmit={handleSubmit}
            noValidate
            className="mt-12 flex flex-col gap-7 sm:mt-14"
          >
            <Field label="E-mail" id="email" error={erroDoCampo('email')}>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                placeholder="voce@exemplo.com"
                value={form.email}
                onChange={handleChange}
                required
                className="w-full bg-transparent pb-2 font-display text-[1.15rem] text-coffee placeholder:text-coffee-faint/70 focus:outline-none"
              />
            </Field>

            <Field label="Senha" id="password" error={erroDoCampo('password')}>
              <div className="flex items-center gap-3">
                <input
                  id="password"
                  name="password"
                  type={mostrarSenha ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={handleChange}
                  required
                  className="w-full bg-transparent pb-2 font-display text-[1.15rem] tracking-[0.08em] text-coffee placeholder:tracking-normal placeholder:text-coffee-faint/70 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setMostrarSenha((v) => !v)}
                  aria-label={mostrarSenha ? 'Ocultar senha' : 'Mostrar senha'}
                  className="pb-2 font-body text-[0.75rem] font-medium uppercase tracking-[0.18em] text-coffee-faint transition-colors duration-300 hover:text-gold"
                >
                  {mostrarSenha ? 'Ocultar' : 'Mostrar'}
                </button>
              </div>
            </Field>

            <div className="flex items-center justify-between">
              <label className="flex cursor-pointer select-none items-center gap-3">
                <input type="checkbox" name="remember" className="peer sr-only" />
                <span className="relative grid h-[16px] w-[16px] place-items-center rounded-sm border border-line-strong bg-cream-soft transition-colors duration-300 peer-checked:border-gold peer-focus-visible:outline peer-focus-visible:outline-1 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-gold">
                  <svg
                    viewBox="0 0 12 12"
                    className="h-2.5 w-2.5 text-gold"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d="M2 6.5 4.6 9 10 3" />
                  </svg>
                </span>
                <span className="font-body text-[0.88rem] font-medium tracking-wide text-coffee-soft">
                  Lembrar de mim
                </span>
              </label>

              <TextLink href="#">Esqueci a senha</TextLink>
            </div>

            <button
              type="submit"
              disabled={enviando || sucesso}
              className="mt-2 w-full rounded-sm bg-gold py-4 font-body text-xs font-semibold uppercase tracking-[0.28em] text-cream-soft shadow-md transition-all duration-300 ease-[var(--ease-cozy)] hover:bg-caramel hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold disabled:cursor-not-allowed disabled:opacity-60"
            >
              {sucesso ? 'Conectado' : enviando ? 'Entrando…' : 'Entrar'}
            </button>
          </form>

          <div className="mt-8 flex items-center gap-4">
            <div className="h-px flex-1 bg-line" />
            <span className="font-body text-[0.72rem] font-semibold uppercase tracking-[0.3em] text-coffee-faint">
              ou
            </span>
            <div className="h-px flex-1 bg-line" />
          </div>

          <button
            type="button"
            className="mt-6 w-full rounded-sm border border-line-strong py-4 font-body text-xs font-semibold uppercase tracking-[0.24em] text-coffee-soft transition-all duration-300 ease-[var(--ease-cozy)] hover:border-forest hover:text-forest focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
          >
            Continuar como visitante
          </button>

          <p className="mt-10 text-center font-body text-[0.88rem] font-normal tracking-wide text-coffee-soft">
            Novo por aqui?{' '}
            <TextLink href="#" className="ml-1 font-semibold">
              Criar uma conta
            </TextLink>
          </p>
        </div>

        {/* Floreio da pena */}
        <div className="flex justify-center pb-14 text-coffee/60 sm:pb-16">
          <Quill className="w-[86px] sm:w-[100px]" />
        </div>
      </section>

      <footer className="mt-10 text-center">
        <p className="font-display text-base font-medium italic text-coffee-faint">
          Papiro &mdash; livros para dias lentos
        </p>
      </footer>
    </main>
  )
}
