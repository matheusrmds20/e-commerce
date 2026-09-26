import { useEffect, useRef, useState } from 'react'
import Field from '../components/Field'
import TextLink from '../components/TextLink'
import Quill from '../components/Quill'
import { useAuth } from '../context/auth-context'
import authService from '../api/auth'

/**
 * Registro — tela de criação de conta.
 * Valida os campos localmente, chama POST /auth/register e, em seguida,
 * faz login automático para o usuário já entrar com a sessão ativa.
 */
export default function Registro({ onConcluir, onVoltarLogin }) {
  const { login } = useAuth()
  const [mostrarSenha, setMostrarSenha] = useState(false)
  const [mostrarConfirmacao, setMostrarConfirmacao] = useState(false)
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    confirmacao: '',
  })
  const [erros, setErros] = useState({})
  const [erro, setErro] = useState(null) // { message, details } vindo da API
  const [enviando, setEnviando] = useState(false)
  const [sucesso, setSucesso] = useState(false)
  const timerRef = useRef(null)

  // Evita que o timer de redirecionamento dispare após sair da tela.
  useEffect(() => () => clearTimeout(timerRef.current), [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((atual) => ({ ...atual, [name]: value }))
    // Limpa o erro do campo enquanto o usuário digita.
    setErros((atual) => (atual[name] ? { ...atual, [name]: null } : atual))
  }

  /** Validação simples no cliente; retorna um mapa campo -> mensagem. */
  const validar = () => {
    const novos = {}
    if (!form.full_name.trim()) novos.full_name = 'Informe seu nome.'
    if (!form.email.trim()) novos.email = 'Informe seu e-mail.'
    else if (!/^\S+@\S+\.\S+$/.test(form.email))
      novos.email = 'E-mail inválido.'
    if (!form.password) novos.password = 'Informe uma senha.'
    else if (form.password.length < 8)
      novos.password = 'A senha deve ter ao menos 8 caracteres.'
    else if (!/[a-zA-Z]/.test(form.password) || !/\d/.test(form.password))
      novos.password = 'A senha deve conter ao menos uma letra e um número.'
    if (form.confirmacao !== form.password)
      novos.confirmacao = 'As senhas não coincidem.'
    return novos
  }

  /** Erro de validação (422) por campo, para exibir sob o input certo. */
  const erroDoCampo = (campo) =>
    erro?.details?.find((d) => d.field === campo)?.message

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (enviando || sucesso) return

    const novos = validar()
    setErros(novos)
    if (Object.values(novos).some(Boolean)) return

    setErro(null)
    setEnviando(true)

    try {
      await authService.register({
        email: form.email,
        full_name: form.full_name,
        password: form.password,
      })
      // Cadastra e já autentica, para o usuário entrar direto na loja.
      await login({ email: form.email, password: form.password })
      // Pequena pausa para o leitor ver a confirmação antes de sair da tela.
      setSucesso(true)
      timerRef.current = setTimeout(() => onConcluir?.(), 900)
    } catch (error) {
      setErro(error)
      setEnviando(false)
    }
  }

  return (
    <main className="flex flex-col items-center px-5 py-6 sm:py-8">
      {/* Folha de papel */}
      <section className="relative w-full max-w-[920px] rounded-md bg-cream-soft shadow-[0_1px_2px_rgba(75,54,33,0.04),0_18px_50px_-20px_rgba(75,54,33,0.22)] ring-1 ring-line">
        <div className="grid md:grid-cols-2">
        <div className="flex flex-col items-center justify-start px-8 pb-10 pt-10 text-center sm:px-12 sm:pt-12 md:border-r md:border-line md:pt-14">
          <header>
            <p className="label-caps text-gold">Criar conta</p>

            <h1 className="mt-4 font-display text-[2.75rem] leading-[1.1] font-normal tracking-[-0.01em] text-coffee sm:text-[3.35rem]">
              Sua primeira página
            </h1>

            <p className="mx-auto mt-5 max-w-[21rem] font-body text-[0.98rem] font-normal leading-relaxed text-coffee-soft">
              Cada estante começa com um livro. A sua começa aqui.
            </p>
          </header>
        </div>

        <div className="px-8 pb-12 pt-8 sm:px-12 sm:pb-14 sm:pt-10">
          {erro && !erro.details && (
            <div
              role="alert"
              className="mb-6 rounded-sm border border-[#a4533f]/30 bg-[#a4533f]/[0.06] px-4 py-3 text-center font-body text-[0.86rem] font-medium tracking-wide text-[#a4533f]"
            >
              {erro.message}
            </div>
          )}

          {sucesso && (
            <div
              role="status"
              className="mb-6 rounded-sm border border-gold/40 bg-gold/[0.08] px-4 py-3 text-center font-body text-[0.86rem] font-medium tracking-wide text-coffee"
            >
              Conta criada. Levando você ao login…
            </div>
          )}

          <form
            onSubmit={handleSubmit}
            noValidate
            className="flex flex-col gap-6"
          >
            <Field label="Nome completo" id="full_name" error={erros.full_name || erroDoCampo('full_name')}>
              <input
                id="full_name"
                name="full_name"
                type="text"
                autoComplete="name"
                placeholder="Maria Almeida"
                value={form.full_name}
                onChange={handleChange}
                required
                className="w-full bg-transparent pb-2 font-display text-[1.15rem] text-coffee placeholder:text-coffee-faint/70 focus:outline-none"
              />
            </Field>

            <Field label="E-mail" id="email" error={erros.email || erroDoCampo('email')}>
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

            <Field label="Senha" id="password" error={erros.password || erroDoCampo('password')}>
              <div className="flex items-center gap-3">
                <input
                  id="password"
                  name="password"
                  type={mostrarSenha ? 'text' : 'password'}
                  autoComplete="new-password"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={handleChange}
                  required
                  minLength={8}
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

            <Field
              label="Confirmar senha"
              id="confirmacao"
              error={erros.confirmacao}
            >
              <div className="flex items-center gap-3">
                <input
                  id="confirmacao"
                  name="confirmacao"
                  type={mostrarConfirmacao ? 'text' : 'password'}
                  autoComplete="new-password"
                  placeholder="••••••••"
                  value={form.confirmacao}
                  onChange={handleChange}
                  required
                  className="w-full bg-transparent pb-2 font-display text-[1.15rem] tracking-[0.08em] text-coffee placeholder:tracking-normal placeholder:text-coffee-faint/70 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setMostrarConfirmacao((v) => !v)}
                  aria-label={
                    mostrarConfirmacao ? 'Ocultar senha' : 'Mostrar senha'
                  }
                  className="pb-2 font-body text-[0.75rem] font-medium uppercase tracking-[0.18em] text-coffee-faint transition-colors duration-300 hover:text-gold"
                >
                  {mostrarConfirmacao ? 'Ocultar' : 'Mostrar'}
                </button>
              </div>
            </Field>

            <p className="font-body text-[0.8rem] font-normal leading-relaxed text-coffee-faint">
              Ao criar uma conta, você concorda com os nossos termos e com a
              política de privacidade.
            </p>

            <button
              type="submit"
              disabled={enviando || sucesso}
              className="mt-2 w-full rounded-sm bg-gold py-4 font-body text-xs font-semibold uppercase tracking-[0.28em] text-cream-soft shadow-md transition-all duration-300 ease-[var(--ease-cozy)] hover:bg-caramel hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold disabled:cursor-not-allowed disabled:opacity-60"
            >
              {sucesso ? 'Conta criada' : enviando ? 'Criando…' : 'Criar conta'}
            </button>
          </form>

          <p className="mt-10 text-center font-body text-[0.88rem] font-normal tracking-wide text-coffee-soft">
            Já tem uma conta?{' '}
            <TextLink
              href="#"
              onClick={(e) => {
                e.preventDefault()
                onVoltarLogin?.()
              }}
              className="ml-1 font-semibold"
            >
              Entrar
            </TextLink>
          </p>
          {/* Floreio da pena */}
          <div className="mt-12 flex justify-center text-coffee/60">
            <Quill className="w-[86px] sm:w-[100px]" />
          </div>
        </div>
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
