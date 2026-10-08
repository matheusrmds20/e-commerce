import { useEffect, useState } from 'react'
import { useAuth } from '../context/auth-context'
import addressService from '../api/addresses'
import orderService from '../api/orders'
import paymentService from '../api/payments'
import productService from '../api/products'
import wishlistService from '../api/wishlist'
import { formatarPreco, precoFinal } from '../api/adapters'
import userService from '../api/users'
import { toApiError } from '../api/client'
import Field from '../components/Field'
import ModalEndereco from '../components/ModalEndereco'
import Confirmacao from '../components/Confirmacao'

/* ------------------------------------------------------------------ */
/* Ícones simples da navegação lateral                                 */
/* ------------------------------------------------------------------ */

const iconeClass = 'h-[18px] w-[18px]'

function IconePedidos() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={iconeClass} aria-hidden="true">
      <path d="M6 7h12l1 13H5L6 7Z" />
      <path d="M9 7a3 3 0 0 1 6 0" />
    </svg>
  )
}

function IconePerfil() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={iconeClass} aria-hidden="true">
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5 20a7 7 0 0 1 14 0" />
    </svg>
  )
}

function IconeEnderecos() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={iconeClass} aria-hidden="true">
      <path d="M12 21s-7-5.5-7-11a7 7 0 0 1 14 0c0 5.5-7 11-7 11Z" />
      <circle cx="12" cy="10" r="2.5" />
    </svg>
  )
}

function IconeCartoes() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={iconeClass} aria-hidden="true">
      <rect x="3" y="6" width="18" height="13" rx="2" />
      <path d="M3 10.5h18" />
      <path d="M6.5 15.5h4" />
    </svg>
  )
}

/* ------------------------------------------------------------------ */
/* Utilitários                                                         */
/* ------------------------------------------------------------------ */

const ROTULOS_STATUS = {
  pending: 'Pendente',
  processing: 'Em preparação',
  shipped: 'Enviado',
  delivered: 'Entregue',
  completed: 'Concluído',
  cancelled: 'Cancelado',
  refunded: 'Reembolsado',
}

const CORES_STATUS = {
  pending: 'border-line-strong text-coffee-soft',
  processing: 'border-gold/50 text-caramel',
  shipped: 'border-forest/40 text-forest',
  delivered: 'border-forest/40 text-forest',
  completed: 'border-forest/40 text-forest',
  cancelled: 'border-[#a4533f]/40 text-[#a4533f]',
  refunded: 'border-[#a4533f]/40 text-[#a4533f]',
}

const rotuloStatus = (status) =>
  ROTULOS_STATUS[String(status).toLowerCase()] ?? String(status)

const corStatus = (status) =>
  CORES_STATUS[String(status).toLowerCase()] ?? 'border-line-strong text-coffee-soft'

const formatarData = (iso) => {
  try {
    return new Date(iso).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return iso
  }
}

/* ------------------------------------------------------------------ */
/* Página                                                              */
/* ------------------------------------------------------------------ */

const ABAS = [
  { id: 'pedidos', rotulo: 'Meus pedidos', icone: IconePedidos },
  { id: 'dados', rotulo: 'Dados pessoais', icone: IconePerfil },
  { id: 'wishlist', rotulo: 'Lista de desejos', icone: IconeWishlist },
  { id: 'enderecos', rotulo: 'Endereços', icone: IconeEnderecos },
  { id: 'pagamentos', rotulo: 'Pagamentos', icone: IconeCartoes },
]

export default function MinhaConta({ onIrParaLogin }) {
  const { usuario, autenticado } = useAuth()
  const [aba, setAba] = useState('pedidos')

  if (!autenticado) {
    return (
      <main className="flex flex-col items-center px-5 py-24 text-center">
        <p className="label-caps text-gold">Minha conta</p>
        <h1 className="mt-4 font-display text-4xl text-coffee">
          Você ainda não entrou
        </h1>
        <p className="mt-4 max-w-sm font-body text-coffee-soft">
          Entre na sua conta para ver seus pedidos, endereços e cartões.
        </p>
        <button
          type="button"
          onClick={() => onIrParaLogin?.()}
          className="mt-8 rounded-sm bg-gold px-10 py-4 font-body text-xs font-semibold uppercase tracking-[0.28em] text-cream-soft shadow-md transition-all duration-300 hover:bg-caramel"
        >
          Entrar
        </button>
      </main>
    )
  }

  return (
    <main className="mx-auto w-full max-w-6xl px-5 py-14 sm:py-20">
      <div className="flex flex-col overflow-hidden rounded-md bg-cream-soft shadow-[0_18px_50px_-20px_rgba(75,54,33,0.22)] ring-1 ring-line md:flex-row">
        {/* Coluna lateral */}
        <aside className="border-b border-line bg-cream md:w-[280px] md:border-b-0 md:border-r">
          <div className="flex items-center gap-4 px-8 py-10">
            <div className="grid h-16 w-16 shrink-0 place-items-center rounded-full bg-gold/15 ring-1 ring-gold/40">
              <span className="font-display text-2xl font-medium text-caramel">
                {usuario?.full_name?.[0]?.toUpperCase() ?? '?'}
              </span>
            </div>
            <div>
              <p className="font-body text-[0.78rem] uppercase tracking-[0.2em] text-coffee-faint">
                Bem-vindo,
              </p>
              <p className="mt-1 font-display text-xl text-coffee">
                {usuario?.full_name?.split(' ')[0] ?? 'leitor'}
              </p>
            </div>
          </div>

          <nav className="flex flex-col gap-1 px-4 pb-10 md:px-6">
            {ABAS.map(({ id, rotulo, icone: Icone }) => (
              <button
                key={id}
                type="button"
                onClick={() => setAba(id)}
                className={`flex items-center gap-3 rounded-sm px-4 py-3 text-left font-body text-[0.92rem] transition-colors duration-300 ${
                  aba === id
                    ? 'bg-gold/12 font-semibold text-caramel'
                    : 'text-coffee-soft hover:bg-gold/[0.06] hover:text-caramel'
                }`}
              >
                <Icone />
                {rotulo}
              </button>
            ))}
          </nav>
        </aside>

        {/* Conteúdo */}
        <section className="min-h-[540px] flex-1 px-6 py-10 sm:px-10">
          {aba === 'pedidos' && <AbaPedidos />}
          {aba === 'dados' && <AbaDados />}
          {aba === 'wishlist' && <AbaWishlist />}
          {aba === 'enderecos' && <AbaEnderecos />}
          {aba === 'pagamentos' && <AbaPagamentos />}
        </section>
      </div>
    </main>
  )
}

/* ------------------------------------------------------------------ */
/* Aba: Meus pedidos                                                   */
/* ------------------------------------------------------------------ */

function AbaPedidos() {
  const [pedidos, setPedidos] = useState(null)
  const [erro, setErro] = useState(null)
  const [expandido, setExpandido] = useState(null)
  const [titulos, setTitulos] = useState({}) // productId -> título
  const [paraCancelar, setParaCancelar] = useState(null)
  const [cancelando, setCancelando] = useState(false)

  /** Status em que o cliente ainda pode cancelar o próprio pedido. */
  const podeCancelar = (status) => ['pending', 'processing'].includes(status)

  /** Recarrega a lista de pedidos (usado após cancelar). */
  const carregar = async () => {
    try {
      const dados = await orderService.listar()
      setPedidos(dados)
      setErro(null)
    } catch (e) {
      setErro(e)
    }
  }

  useEffect(() => {
    let ativo = true
    orderService
      .listar()
      .then((dados) => ativo && setPedidos(dados))
      .catch((e) => ativo && setErro(e))
    return () => {
      ativo = false
    }
  }, [])

  /** Cancela o pedido selecionado e atualiza o estado local. */
  const confirmarCancelamento = async () => {
    if (!paraCancelar) return
    setCancelando(true)
    try {
      await orderService.cancelar(paraCancelar.id)
      setParaCancelar(null)
      await carregar()
    } catch (e) {
      setErro(e)
      setParaCancelar(null)
    } finally {
      setCancelando(false)
    }
  }

  /** Busca os títulos dos produtos de um pedido ao expandi-lo. */
  const carregarTitulos = async (pedido) => {
    const faltando = (pedido.order_items ?? [])
      .map((i) => i.product_id)
      .filter((id) => !titulos[id])
    await Promise.all(
      faltando.map(async (id) => {
        try {
          const p = await productService.obter(id)
          setTitulos((atual) => ({ ...atual, [id]: p.title }))
        } catch {
          setTitulos((atual) => ({ ...atual, [id]: `Livro #${id}` }))
        }
      }),
    )
  }

  const alternar = async (pedido) => {
    const novo = expandido === pedido.id ? null : pedido.id
    setExpandido(novo)
    if (novo) await carregarTitulos(pedido)
  }

  return (
    <>
      <h2 className="font-display text-3xl text-coffee">Meus pedidos</h2>

      {erro && (
        <div role="alert" className="mt-6 rounded-sm border border-[#a4533f]/30 bg-[#a4533f]/[0.06] px-4 py-3 font-body text-[0.86rem] text-[#a4533f]">
          {erro.message}
        </div>
      )}

      {pedidos === null && !erro && (
        <p className="mt-8 font-body text-coffee-faint">Carregando pedidos…</p>
      )}

      {pedidos?.length === 0 && (
        <div className="mt-10 text-center">
          <p className="font-display text-xl italic text-coffee-faint">
            Sua estante de pedidos ainda está vazia.
          </p>
          <p className="mt-2 font-body text-sm text-coffee-soft">
            Quando você fizer sua primeira compra, ela aparecerá aqui.
          </p>
        </div>
      )}

      <ul className="mt-8 flex flex-col gap-5">
        {pedidos?.map((pedido) => (
          <li
            key={pedido.id}
            className="rounded-sm border border-line bg-cream-soft/60 px-6 py-5 transition-shadow duration-300 hover:shadow-md"
          >
            <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
              <div className="min-w-[130px]">
                <p className="font-body text-[0.72rem] uppercase tracking-[0.18em] text-coffee-faint">
                  Pedido #{pedido.id}
                </p>
                <p className="mt-1 font-display text-lg text-coffee">
                  {formatarData(pedido.created_at)}
                </p>
              </div>

              <span
                className={`rounded-full border px-4 py-1 font-body text-[0.74rem] font-medium uppercase tracking-[0.14em] ${corStatus(pedido.status)}`}
              >
                {rotuloStatus(pedido.status)}
              </span>

              <p className="font-display text-lg font-medium text-coffee">
                {formatarPreco(pedido.total)}
              </p>

              <button
                type="button"
                onClick={() => alternar(pedido)}
                className="ml-auto rounded-sm bg-forest px-5 py-2.5 font-body text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-cream-soft transition-colors duration-300 hover:bg-forest-soft"
              >
                {expandido === pedido.id ? 'Ocultar' : 'Ver detalhes'}
              </button>

              {podeCancelar(pedido.status) && (
                <button
                  type="button"
                  onClick={() => setParaCancelar(pedido)}
                  className="rounded-sm border border-[#a4533f]/40 px-5 py-2.5 font-body text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-[#a4533f] transition-colors duration-300 hover:bg-[#a4533f]/[0.08]"
                >
                  Cancelar pedido
                </button>
              )}
            </div>

            {expandido === pedido.id && (
              <ul className="mt-5 flex flex-col divide-y divide-line border-t border-line pt-4">
                {(pedido.order_items ?? []).map((item) => (
                  <li
                    key={item.id}
                    className="flex items-center justify-between gap-4 py-3"
                  >
                    <div>
                      <p className="font-body text-[0.92rem] text-coffee">
                        {titulos[item.product_id] ?? `Livro #${item.product_id}`}
                      </p>
                      <p className="mt-0.5 font-body text-[0.78rem] text-coffee-faint">
                        {item.quantity} × {formatarPreco(item.price)}
                      </p>
                    </div>
                    <p className="font-body text-[0.9rem] font-medium text-coffee">
                      {formatarPreco(item.quantity * item.price)}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>

      <Confirmacao
        aberto={Boolean(paraCancelar)}
        titulo="Cancelar pedido?"
        descricao={
          paraCancelar
            ? `O pedido #${paraCancelar.id} será cancelado e os itens voltam ao estoque. Esta ação não pode ser desfeita.`
            : ''
        }
        ocupado={cancelando}
        textoConfirmar="Cancelar pedido"
        textoOcupado="Cancelando…"
        onCancelar={() => setParaCancelar(null)}
        onConfirmar={confirmarCancelamento}
      />
    </>
  )
}

/* ------------------------------------------------------------------ */
/* Aba: Dados pessoais                                                 */
/* ------------------------------------------------------------------ */

function AbaDados() {
  const { usuario, atualizarUsuario } = useAuth()
  const [editando, setEditando] = useState(false)

  return (
    <>
      <h2 className="font-display text-3xl text-coffee">Dados pessoais</h2>

      {!editando ? (
        <LeituraDados
          usuario={usuario}
          aoEditar={() => setEditando(true)}
        />
      ) : (
        <FormDados
          usuario={usuario}
          aoSalvar={atualizarUsuario}
          aoCancelar={() => setEditando(false)}
        />
      )}

      <SecaoSenha usuario={usuario} />
    </>
  )
}

/* ------------------------------------------------------------------ */
/* Dados pessoais — leitura                                            */
/* ------------------------------------------------------------------ */

function LinhaDado({ rotulo, valor }) {
  return (
    <div className="flex flex-col gap-1 border-b border-line py-4 sm:flex-row sm:items-baseline sm:justify-between sm:gap-6">
      <dt className="font-body text-[0.75rem] font-medium uppercase tracking-[0.18em] text-coffee-faint">
        {rotulo}
      </dt>
      <dd className="font-display text-[1.05rem] text-coffee">{valor}</dd>
    </div>
  )
}

function LeituraDados({ usuario, aoEditar }) {
  return (
    <div className="mt-8 max-w-md">
      <dl>
        <LinhaDado rotulo="Nome completo" valor={usuario?.full_name ?? '—'} />
        <LinhaDado rotulo="E-mail" valor={usuario?.email ?? '—'} />
        <LinhaDado
          rotulo="Membro desde"
          valor={
            usuario?.created_at ? formatarData(usuario.created_at) : '—'
          }
        />
      </dl>

      <button
        type="button"
        onClick={aoEditar}
        className="mt-8 w-fit rounded-sm bg-gold px-10 py-3.5 font-body text-xs font-semibold uppercase tracking-[0.24em] text-cream-soft shadow-md transition-all duration-300 hover:bg-caramel"
      >
        Editar dados
      </button>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Dados pessoais — edição                                             */
/* ------------------------------------------------------------------ */

function FormDados({ usuario, aoSalvar, aoCancelar }) {
  const [form, setForm] = useState({
    full_name: usuario?.full_name ?? '',
    email: usuario?.email ?? '',
  })
  const [erros, setErros] = useState({})
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState(null)

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((atual) => ({ ...atual, [name]: value }))
    setErros((atual) => (atual[name] ? { ...atual, [name]: null } : atual))
  }

  const validar = () => {
    const novos = {}
    if (!form.full_name || form.full_name.trim().length < 3) {
      novos.full_name = 'Informe ao menos 3 caracteres.'
    }
    if (!form.email || !/\S+@\S+\.\S+/.test(form.email)) {
      novos.email = 'Informe um e-mail válido.'
    }
    setErros(novos)
    return Object.keys(novos).length === 0
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (salvando) return
    setErro(null)
    if (!validar()) return
    setSalvando(true)

    try {
      const dados = await userService.atualizar(usuario.id, {
        full_name: form.full_name.trim(),
        email: form.email.trim(),
      })
      aoSalvar(dados)
      aoCancelar()
    } catch (e) {
      setErro(toApiError(e))
    } finally {
      setSalvando(false)
    }
  }

  const erroDoCampo = (campo) =>
    erro?.details?.find((d) => d.field === campo)?.message ?? erros[campo]

  return (
    <form onSubmit={handleSubmit} noValidate className="mt-8 flex max-w-md flex-col gap-7">
      {erro && !erro.details && (
        <div role="alert" className="rounded-sm border border-[#a4533f]/30 bg-[#a4533f]/[0.06] px-4 py-3 font-body text-[0.86rem] text-[#a4533f]">
          {erro.message}
        </div>
      )}

      <Field label="Nome completo" id="full_name" error={erroDoCampo('full_name')}>
        <input
          id="full_name"
          name="full_name"
          type="text"
          autoComplete="name"
          value={form.full_name}
          onChange={handleChange}
          required
          minLength={3}
          className="w-full bg-transparent pb-2 font-display text-[1.05rem] text-coffee focus:outline-none"
        />
      </Field>

      <Field label="E-mail" id="email" error={erroDoCampo('email')}>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={handleChange}
          required
          className="w-full bg-transparent pb-2 font-display text-[1.05rem] text-coffee focus:outline-none"
        />
      </Field>

      <div className="flex flex-wrap gap-4">
        <button
          type="submit"
          disabled={salvando}
          className="w-fit rounded-sm bg-gold px-10 py-3.5 font-body text-xs font-semibold uppercase tracking-[0.24em] text-cream-soft shadow-md transition-all duration-300 hover:bg-caramel disabled:opacity-60"
        >
          {salvando ? 'Salvando…' : 'Salvar alterações'}
        </button>
        <button
          type="button"
          onClick={aoCancelar}
          disabled={salvando}
          className="w-fit rounded-sm border border-line-strong px-10 py-3.5 font-body text-xs font-semibold uppercase tracking-[0.24em] text-coffee-soft transition-all duration-300 hover:border-gold hover:text-gold disabled:opacity-60"
        >
          Cancelar
        </button>
      </div>
    </form>
  )
}

/* ------------------------------------------------------------------ */
/* Dados pessoais — alterar senha                                      */
/* ------------------------------------------------------------------ */

const MSG_SENHA_INVALIDA =
  'A senha deve ter ao menos 8 caracteres, com uma letra e um número.'

function CampoSenha({ id, label, autoComplete, valor, onChange, erro, mostrar, alternarMostrar }) {
  return (
    <Field label={label} id={id} error={erro}>
      <div className="flex items-center gap-3">
        <input
          id={id}
          name={id}
          type={mostrar ? 'text' : 'password'}
          autoComplete={autoComplete}
          placeholder="••••••••"
          value={valor}
          onChange={onChange}
          required
          className="w-full bg-transparent pb-2 font-display text-[1.05rem] tracking-[0.08em] text-coffee placeholder:tracking-normal focus:outline-none"
        />
        <button
          type="button"
          onClick={alternarMostrar}
          aria-label={mostrar ? 'Ocultar senha' : 'Mostrar senha'}
          className="pb-2 font-body text-[0.75rem] font-medium uppercase tracking-[0.18em] text-coffee-faint transition-colors duration-300 hover:text-gold"
        >
          {mostrar ? 'Ocultar' : 'Mostrar'}
        </button>
      </div>
    </Field>
  )
}

function SecaoSenha({ usuario }) {
  const [form, setForm] = useState({
    current_password: '',
    new_password: '',
    confirmacao: '',
  })
  const [aberta, setAberta] = useState(false)
  const [mostrarAtual, setMostrarAtual] = useState(false)
  const [mostrarNova, setMostrarNova] = useState(false)
  const [erros, setErros] = useState({})
  const [salvando, setSalvando] = useState(false)
  const [sucesso, setSucesso] = useState(null)
  const [erro, setErro] = useState(null)

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((atual) => ({ ...atual, [name]: value }))
    setErros((atual) => (atual[name] ? { ...atual, [name]: null } : atual))
  }

  const validar = () => {
    const novos = {}
    if (!form.current_password) {
      novos.current_password = 'Informe a senha atual.'
    }
    if (
      form.new_password.length < 8 ||
      !/[a-zA-Z]/.test(form.new_password) ||
      !/\d/.test(form.new_password)
    ) {
      novos.new_password = MSG_SENHA_INVALIDA
    }
    if (form.confirmacao !== form.new_password || !form.confirmacao) {
      novos.confirmacao = 'As senhas não coincidem.'
    }
    setErros(novos)
    return Object.keys(novos).length === 0
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (salvando) return
    setSucesso(null)
    setErro(null)
    if (!validar()) return
    setSalvando(true)

    try {
      await userService.alterarSenha(usuario.id, {
        current_password: form.current_password,
        new_password: form.new_password,
      })
      setSucesso('Senha alterada com sucesso.')
      setForm({ current_password: '', new_password: '', confirmacao: '' })
    } catch (e) {
      const apiError = toApiError(e)
      if (apiError.code === 'INVALID_CURRENT_PASSWORD') {
        setErros({ current_password: apiError.message })
      } else {
        setErro(apiError)
      }
    } finally {
      setSalvando(false)
    }
  }

  const erroDoCampo = (campo) =>
    erro?.details?.find((d) => d.field === campo)?.message ?? erros[campo]

  return (
    <section aria-labelledby="titulo-senha" className="mt-14 max-w-md border-t border-line pt-10">
      <div className="flex flex-wrap items-baseline justify-between gap-4">
        <h3 id="titulo-senha" className="font-display text-2xl text-coffee">
          Alterar senha
        </h3>
        <button
          type="button"
          onClick={() => setAberta((v) => !v)}
          aria-expanded={aberta}
          className="w-fit rounded-sm border border-line-strong px-6 py-2.5 font-body text-[0.7rem] font-semibold uppercase tracking-[0.24em] text-coffee-soft transition-all duration-300 hover:border-gold hover:text-gold"
        >
          {aberta ? 'Fechar' : 'Alterar senha'}
        </button>
      </div>

      {aberta && (
        <>
          {sucesso && (
            <div role="status" className="mt-6 rounded-sm border border-gold/40 bg-gold/[0.08] px-4 py-3 font-body text-[0.86rem] text-coffee">
              {sucesso}
            </div>
          )}

          {erro && !erro.details && (
            <div role="alert" className="mt-6 rounded-sm border border-[#a4533f]/30 bg-[#a4533f]/[0.06] px-4 py-3 font-body text-[0.86rem] text-[#a4533f]">
              {erro.message}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="mt-8 flex flex-col gap-7">
        <CampoSenha
          id="current_password"
          label="Senha atual"
          autoComplete="current-password"
          valor={form.current_password}
          onChange={handleChange}
          erro={erroDoCampo('current_password')}
          mostrar={mostrarAtual}
          alternarMostrar={() => setMostrarAtual((v) => !v)}
        />

        <CampoSenha
          id="new_password"
          label="Nova senha"
          autoComplete="new-password"
          valor={form.new_password}
          onChange={handleChange}
          erro={erroDoCampo('new_password')}
          mostrar={mostrarNova}
          alternarMostrar={() => setMostrarNova((v) => !v)}
        />

        <CampoSenha
          id="confirmacao"
          label="Confirmar nova senha"
          autoComplete="new-password"
          valor={form.confirmacao}
          onChange={handleChange}
          erro={erroDoCampo('confirmacao')}
          mostrar={mostrarNova}
          alternarMostrar={() => setMostrarNova((v) => !v)}
        />

        <button
          type="submit"
          disabled={salvando}
          className="w-fit rounded-sm bg-gold px-10 py-3.5 font-body text-xs font-semibold uppercase tracking-[0.24em] text-cream-soft shadow-md transition-all duration-300 hover:bg-caramel disabled:opacity-60"
        >
          {salvando ? 'Alterando…' : 'Alterar senha'}
        </button>
        </form>
        </>
      )}
    </section>
  )
}

/* ------------------------------------------------------------------ */
/* Aba: Lista de desejos                                               */
/* ------------------------------------------------------------------ */

function IconeWishlist() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={iconeClass} aria-hidden="true">
      <path d="M12 20s-7.5-4.9-7.5-10A4.2 4.2 0 0 1 12 7.6 4.2 4.2 0 0 1 19.5 10c0 5.1-7.5 10-7.5 10Z" />
    </svg>
  )
}

function AbaWishlist() {
  const { usuario } = useAuth()
  const [itens, setItens] = useState(null)
  const [produtos, setProdutos] = useState({}) // productId -> produto
  const [erro, setErro] = useState(null)
  const [paraExcluir, setParaExcluir] = useState(null)
  const [excluindo, setExcluindo] = useState(false)

  const carregar = async () => {
    try {
      const lista = await wishlistService.listar()
      setItens(lista)
      // Busca os detalhes de cada produto ainda não carregado.
      await Promise.all(
        lista.map(async (item) => {
          if (produtos[item.product_id]) return
          try {
            const produto = await productService.obter(item.product_id)
            setProdutos((atual) => ({ ...atual, [item.product_id]: produto }))
          } catch {
            setProdutos((atual) => ({ ...atual, [item.product_id]: null }))
          }
        }),
      )
    } catch (e) {
      setErro(e)
      setItens([])
    }
  }

  useEffect(() => {
    if (!usuario?.id) return
    let ativo = true
    ;(async () => {
      try {
        const lista = await wishlistService.listar()
        if (!ativo) return
        setItens(lista)
        await Promise.all(
          lista.map(async (item) => {
            if (produtos[item.product_id]) return
            try {
              const produto = await productService.obter(item.product_id)
              if (ativo) setProdutos((atual) => ({ ...atual, [item.product_id]: produto }))
            } catch {
              if (ativo) setProdutos((atual) => ({ ...atual, [item.product_id]: null }))
            }
          }),
        )
      } catch (e) {
        if (ativo) {
          setErro(e)
          setItens([])
        }
      }
    })()
    return () => {
      ativo = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- carrega ao montar/trocar de usuário
  }, [usuario?.id])

  return (
    <>
      <h2 className="font-display text-3xl text-coffee">Lista de desejos</h2>

      {erro && (
        <div role="alert" className="mt-6 rounded-sm border border-[#a4533f]/30 bg-[#a4533f]/[0.06] px-4 py-3 font-body text-[0.86rem] text-[#a4533f]">
          {erro.message}
        </div>
      )}

      {itens === null && !erro && (
        <p className="mt-8 font-body text-coffee-faint">Carregando desejos…</p>
      )}

      {itens?.length === 0 && (
        <div className="mt-10 text-center">
          <p className="font-display text-xl italic text-coffee-faint">
            Nenhum desejo guardado ainda.
          </p>
          <p className="mt-2 font-body text-sm text-coffee-soft">\            Toque no coração de um livro para guardá-lo aqui.
          </p>
        </div>
      )}

      <ul className="mt-8 flex flex-col gap-4">
        {itens?.map((item) => {
          const produto = produtos[item.product_id]
          return (
            <li
              key={item.id}
              className="flex items-center gap-5 rounded-sm border border-line bg-cream-soft/60 px-6 py-4"
            >
              {/* Capa */}
              <div className="grid h-16 w-12 shrink-0 place-items-center overflow-hidden rounded-sm bg-coffee/10">
                {produto?.image_url ? (
                  <img
                    src={produto.image_url}
                    alt={produto?.title ?? ''}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <span className="font-display text-lg text-coffee-faint">¶</span>
                )}
              </div>

              <div className="min-w-0 flex-1">
                <p className="truncate font-display text-lg text-coffee">
                  {produto ? produto.title : `Livro #${item.product_id}`}
                </p>
                <p className="mt-0.5 truncate font-body text-[0.82rem] text-coffee-soft">
                  {produto?.author ?? ''}
                </p>
              </div>

              {produto && (
                <p className="font-display text-lg font-medium text-coffee">
                  {formatarPreco(precoFinal(produto))}
                </p>
              )}

              <button
                type="button"
                onClick={() => setParaExcluir(item)}
                aria-label="Remover da lista de desejos"
                className="shrink-0 text-coffee-faint transition-colors duration-300 hover:text-[#a4533f]"
              >
                <svg viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5" aria-hidden="true">
                  <path d="M12 20s-7.5-4.9-7.5-10A4.2 4.2 0 0 1 12 7.6 4.2 4.2 0 0 1 19.5 10c0 5.1-7.5 10-7.5 10Z" />
                </svg>
              </button>
            </li>
          )
        })}
      </ul>

      <Confirmacao
        aberto={Boolean(paraExcluir)}
        titulo="Remover da lista?"
        descricao={
          paraExcluir
            ? `"${produtos[paraExcluir.product_id]?.title ?? `Livro #${paraExcluir.product_id}`}" sairá da sua lista de desejos.`
            : ''
        }
        ocupado={excluindo}
        textoConfirmar="Remover"
        onCancelar={() => setParaExcluir(null)}
        onConfirmar={async () => {
          setExcluindo(true)
          try {
            await wishlistService.excluir(paraExcluir.id)
            setParaExcluir(null)
            await carregar()
          } catch (e) {
            setErro(e)
            setParaExcluir(null)
          } finally {
            setExcluindo(false)
          }
        }}
      />
    </>
  )
}

/* ------------------------------------------------------------------ */
/* Aba: Endereços                                                      */
/* ------------------------------------------------------------------ */

function AbaEnderecos() {
  const [enderecos, setEnderecos] = useState(null)
  const [modalAberto, setModalAberto] = useState(false)
  const [modoModal, setModoModal] = useState('lista')
  const [enderecoEdicao, setEnderecoEdicao] = useState(null)
  const [paraExcluir, setParaExcluir] = useState(null)
  const [excluindo, setExcluindo] = useState(false)
  const [erroExclusao, setErroExclusao] = useState(null)

  const carregar = () => {
    addressService.listar().then(setEnderecos).catch(() => setEnderecos([]))
  }

  useEffect(carregar, [])

  const abrirModal = ({ modo = 'lista', endereco = null } = {}) => {
    setModoModal(modo)
    setEnderecoEdicao(endereco)
    setModalAberto(true)
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h2 className="font-display text-3xl text-coffee">Endereços</h2>
        <button
          type="button"
          onClick={() => abrirModal({ modo: 'novo' })}
          className="rounded-sm border border-line-strong px-5 py-2.5 font-body text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-coffee-soft transition-colors duration-300 hover:border-gold hover:text-caramel"
        >
          Novo endereço
        </button>
      </div>

      {enderecos?.length === 0 && (
        <p className="mt-10 font-display text-xl italic text-coffee-faint">
          Nenhum endereço cadastrado ainda.
        </p>
      )}

      <ul className="mt-8 flex flex-col gap-4">
        {enderecos?.map((endereco) => (
          <li
            key={endereco.id}
            className="flex items-center justify-between gap-4 rounded-sm border border-line bg-cream-soft/60 px-6 py-5"
          >
            <div>
              <p className="font-display text-lg text-coffee">
                {endereco.street}, {endereco.number}
                {endereco.complement ? ` — ${endereco.complement}` : ''}
              </p>
              <p className="mt-1 font-body text-[0.85rem] text-coffee-soft">
                {endereco.neighborhood}, {endereco.city} — {endereco.state} · CEP{' '}
                {endereco.zip_code}
              </p>
              {endereco.is_default && (
                <span className="mt-2 inline-block rounded-full border border-gold/40 bg-gold/[0.08] px-3 py-0.5 font-body text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-caramel">
                  Padrão
                </span>
              )}
            </div>
            <div className="flex shrink-0 gap-4">
              <button
                type="button"
                onClick={() => abrirModal({ modo: 'editar', endereco })}
                className="font-body text-[0.75rem] font-medium uppercase tracking-[0.18em] text-coffee-faint transition-colors duration-300 hover:text-caramel"
              >
                Editar
              </button>
              <button
                type="button"
                onClick={() => setParaExcluir(endereco)}
                className="font-body text-[0.75rem] font-medium uppercase tracking-[0.18em] text-coffee-faint transition-colors duration-300 hover:text-[#a4533f]"
              >
                Excluir
              </button>
            </div>
          </li>
        ))}
      </ul>

      <ModalEndereco
        isOpen={modalAberto}
        onClose={() => setModalAberto(false)}
        enderecos={enderecos ?? []}
        onRecarregarEnderecos={carregar}
        modoInicial={modoModal}
        enderecoParaEditar={enderecoEdicao}
      />

      <Confirmacao
        aberto={Boolean(paraExcluir)}
        titulo="Excluir endereço?"
        descricao={
          paraExcluir
            ? `O endereço em ${paraExcluir.street}, ${paraExcluir.number} será removido permanentemente.`
            : ''
        }
        ocupado={excluindo}
        onCancelar={() => {
          setParaExcluir(null)
          setErroExclusao(null)
        }}
        onConfirmar={async () => {
          setExcluindo(true)
          setErroExclusao(null)
          try {
            await addressService.excluir(paraExcluir.id)
            setParaExcluir(null)
            carregar()
          } catch (error) {
            // Ex.: endereço vinculado a pedidos — mostra o motivo no popup.
            setErroExclusao(error)
          } finally {
            setExcluindo(false)
          }
        }}
        erro={erroExclusao}
      />
    </>
  )
}

/* ------------------------------------------------------------------ */
/* Aba: Pagamentos                                                     */
/* ------------------------------------------------------------------ */

const ROTULO_STATUS_PAGAMENTO = {
  pending: 'Aguardando confirmação',
  approved: 'Aprovado',
  rejected: 'Recusado',
}

const ESTILO_STATUS_PAGAMENTO = {
  pending: 'bg-gold/15 text-gold-dark',
  approved: 'bg-forest/15 text-forest',
  rejected: 'bg-[#a4533f]/15 text-[#a4533f]',
}

function AbaPagamentos() {
  // Os pagamentos são processados pelo Mercado Pago; aqui apenas listamos o
  // histórico (status por pedido). FASE 3: faz UMA única consulta agregada
  // via GET /payments/history — antes faria 1 request por pedido (Promise.all
  // de GET /payments/order/{id}), além de re-buscar /orders/list.
  const [pagamentos, setPagamentos] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState(null)

  useEffect(() => {
    let ativo = true

    async function carregar() {
      try {
        setCarregando(true)
        const lista = await paymentService.historico()
        if (!ativo) return
        setPagamentos(Array.isArray(lista) ? lista : [])
        setErro(null)
      } catch (err) {
        if (ativo) setErro(err?.message ?? 'Não foi possível carregar os pagamentos.')
      } finally {
        if (ativo) setCarregando(false)
      }
    }

    carregar()
    return () => {
      ativo = false
    }
  }, [])

  return (
    <>
      <div className="flex items-center justify-between">
        <h2 className="font-display text-3xl text-coffee">Pagamentos</h2>
      </div>

      <p className="mt-3 max-w-2xl font-body text-[0.88rem] leading-relaxed text-coffee-soft">
        Seus pagamentos são processados com segurança pelo Mercado Pago. Nenhum
        dado de cartão é armazenado por nós. Abaixo está o histórico por pedido.
      </p>

      {carregando && (
        <p className="mt-10 font-display text-xl italic text-coffee-faint">
          Carregando pagamentos…
        </p>
      )}

      {!carregando && erro && (
        <p
          role="alert"
          className="mt-8 rounded-sm border border-[#a4533f]/30 bg-[#a4533f]/[0.06] px-4 py-3 font-body text-[0.85rem] font-medium text-[#a4533f]"
        >
          {erro}
        </p>
      )}

      {!carregando && !erro && pagamentos.length === 0 && (
        <p className="mt-10 font-display text-xl italic text-coffee-faint">
          Nenhum pagamento registrado ainda.
        </p>
      )}

      <ul className="mt-8 grid gap-4 sm:grid-cols-2">
        {pagamentos.map((pg) => (
          <li
            key={pg.id}
            className="rounded-sm border border-line bg-cream-soft/60 px-6 py-5"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-body text-[0.72rem] uppercase tracking-[0.18em] text-coffee-faint">
                  Pedido #{pg.order_id}
                </p>
                <p className="mt-2 font-display text-lg text-coffee">
                  {formatarPreco(pg.amount)}
                </p>
              </div>
              <span
                className={`shrink-0 rounded-full px-2.5 py-1 font-body text-[0.68rem] font-bold uppercase tracking-wider ${
                  ESTILO_STATUS_PAGAMENTO[pg.status] ?? 'bg-coffee/10 text-coffee-soft'
                }`}
              >
                {ROTULO_STATUS_PAGAMENTO[pg.status] ?? pg.status}
              </span>
            </div>
            <p className="mt-4 font-body text-[0.78rem] text-coffee-faint">
              {pg.provider} • {pg.currency}
            </p>
          </li>
        ))}
      </ul>
    </>
  )
}
