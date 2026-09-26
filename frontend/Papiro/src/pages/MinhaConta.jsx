import { useEffect, useState } from 'react'
import { useAuth } from '../context/auth-context'
import addressService from '../api/addresses'
import orderService from '../api/orders'
import cardService, { detectarBandeira } from '../api/cards'
import productService from '../api/products'
import wishlistService from '../api/wishlist'
import { formatarPreco, precoFinal } from '../api/adapters'
import api from '../api/client'
import Field from '../components/Field'
import ModalEndereco from '../components/ModalEndereco'
import ModalCartao from '../components/ModalCartao'
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
    </>
  )
}

/* ------------------------------------------------------------------ */
/* Aba: Dados pessoais                                                 */
/* ------------------------------------------------------------------ */

function AbaDados() {
  const { usuario, atualizarUsuario } = useAuth()
  const [form, setForm] = useState({
    full_name: usuario?.full_name ?? '',
    email: usuario?.email ?? '',
  })
  const [salvando, setSalvando] = useState(false)
  const [sucesso, setSucesso] = useState(null)
  const [erro, setErro] = useState(null)

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((atual) => ({ ...atual, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (salvando) return
    setSucesso(null)
    setErro(null)
    setSalvando(true)

    try {
      const { data } = await api.patch(`/users/update/${usuario.id}`, {
        full_name: form.full_name,
        email: form.email,
      })
      atualizarUsuario(data)
      setSucesso('Dados atualizados com sucesso.')
    } catch (e) {
      setErro(e)
    } finally {
      setSalvando(false)
    }
  }

  return (
    <>
      <h2 className="font-display text-3xl text-coffee">Dados pessoais</h2>

      {sucesso && (
        <div role="status" className="mt-6 rounded-sm border border-gold/40 bg-gold/[0.08] px-4 py-3 font-body text-[0.86rem] text-coffee">
          {sucesso}
        </div>
      )}

      {erro && (
        <div role="alert" className="mt-6 rounded-sm border border-[#a4533f]/30 bg-[#a4533f]/[0.06] px-4 py-3 font-body text-[0.86rem] text-[#a4533f]">
          {erro.message}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="mt-8 flex max-w-md flex-col gap-7">
        <Field label="Nome completo" id="full_name">
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

        <Field label="E-mail" id="email">
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

        <p className="font-body text-[0.8rem] text-coffee-faint">
          Membro desde{' '}
          {usuario?.created_at
            ? formatarData(usuario.created_at)
            : '—'}
        </p>

        <button
          type="submit"
          disabled={salvando}
          className="w-fit rounded-sm bg-gold px-10 py-3.5 font-body text-xs font-semibold uppercase tracking-[0.24em] text-cream-soft shadow-md transition-all duration-300 hover:bg-caramel disabled:opacity-60"
        >
          {salvando ? 'Salvando…' : 'Salvar alterações'}
        </button>
      </form>
    </>
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
      const lista = await wishlistService.listar(usuario?.id)
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
        const lista = await wishlistService.listar(usuario.id)
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
            await wishlistService.excluir(usuario.id, paraExcluir.id)
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

function AbaPagamentos() {
  const { usuario } = useAuth()
  // Cartões vivem no localStorage — lemos a cada render; o "versão" força
  // recarga após operações de CRUD feitas dentro do modal.
  const [, setVersao] = useState(0)
  const cartoes = cardService.listar(usuario?.id)
  const [modalAberto, setModalAberto] = useState(false)
  const [modoModal, setModoModal] = useState('lista')
  const [cartaoEdicao, setCartaoEdicao] = useState(null)
  const [paraExcluir, setParaExcluir] = useState(null)

  const abrirModal = ({ modo = 'lista', cartao = null } = {}) => {
    setModoModal(modo)
    setCartaoEdicao(cartao)
    setModalAberto(true)
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h2 className="font-display text-3xl text-coffee">Pagamentos</h2>
        <button
          type="button"
          onClick={() => abrirModal({ modo: 'novo' })}
          className="rounded-sm border border-line-strong px-5 py-2.5 font-body text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-coffee-soft transition-colors duration-300 hover:border-gold hover:text-caramel"
        >
          Novo cartão
        </button>
      </div>

      {cartoes?.length === 0 && (
        <p className="mt-10 font-display text-xl italic text-coffee-faint">
          Nenhum cartão salvo ainda.
        </p>
      )}

      <ul className="mt-8 grid gap-4 sm:grid-cols-2">
        {cartoes?.map((cartao) => {
          const bandeira = detectarBandeira(cartao.numeroMascarado ?? '')
          return (
            <li
              key={cartao.id}
              className="rounded-sm border border-line bg-cream-soft/60 px-6 py-5"
            >
              <p className="font-body text-[0.72rem] uppercase tracking-[0.18em] text-coffee-faint">
                {bandeira.nome}
              </p>
              <p className="mt-2 font-display text-lg tracking-[0.12em] text-coffee">
                {cartao.numeroMascarado ??
                  `•••• •••• •••• ${String(cartao.numero ?? '').slice(-4)}`}
              </p>
              <div className="mt-4 flex items-center justify-between">
                <p className="font-body text-[0.8rem] text-coffee-soft">
                  Valida {cartao.mes}/{cartao.ano}
                </p>
                <div className="flex items-center gap-4">
                <button
                  type="button"
                  onClick={() => setParaExcluir(cartao)}
                  className="font-body text-[0.75rem] font-medium uppercase tracking-[0.18em] text-coffee-faint transition-colors duration-300 hover:text-[#a4533f]"
                >
                  Excluir
                </button>
                <button
                  type="button"
                  onClick={() => abrirModal({ modo: 'editar', cartao })}
                  className="font-body text-[0.75rem] font-medium uppercase tracking-[0.18em] text-coffee-faint transition-colors duration-300 hover:text-caramel"
                >
                  Editar
                </button>
                </div>
              </div>
            </li>
          )
        })}
      </ul>

      <ModalCartao
        isOpen={modalAberto}
        onClose={() => setModalAberto(false)}
        userId={usuario?.id}
        cartoes={cartoes ?? []}
        onRecarregarCartoes={() => setVersao((v) => v + 1)}
        modoInicial={modoModal}
        cartaoParaEditar={cartaoEdicao}
      />

      <Confirmacao
        aberto={Boolean(paraExcluir)}
        titulo="Excluir cartão?"
        descricao={
          paraExcluir
            ? `O cartão terminado em ${String(paraExcluir.numero ?? '').slice(-4) || '????'} será removido dos seus dados salvos.`
            : ''
        }
        onCancelar={() => setParaExcluir(null)}
        onConfirmar={() => {
          cardService.excluir(usuario?.id, paraExcluir.id)
          setParaExcluir(null)
          setVersao((v) => v + 1)
        }}
      />
    </>
  )
}
