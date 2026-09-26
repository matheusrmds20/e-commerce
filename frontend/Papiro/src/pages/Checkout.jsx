import { useCallback, useEffect, useMemo, useState } from 'react'
import ResumoPedido from '../components/ResumoPedido'
import SeletorEndereco from '../components/SeletorEndereco'
import SeletorPagamento from '../components/SeletorPagamento'
import ModalEndereco from '../components/ModalEndereco'
import ModalCartao from '../components/ModalCartao'
import SecaoCupons from '../components/SecaoCupons'
import { LockIcon } from '../components/Icons'
import { useCart } from '../context/cart-context'
import { useAuth } from '../context/auth-context'
import { calcularTotais, formatarPreco } from '../api/adapters'
import addressService from '../api/addresses'
import orderService from '../api/orders'
import cardService from '../api/cards'
import couponService from '../api/coupons'

export default function Checkout({ onIrParaLogin }) {
  const { itens, carregando: carrinhoCarregando, recarregar } = useCart()
  const { usuario, autenticado } = useAuth()

  // Estados de Endereços
  const [enderecos, setEnderecos] = useState([])
  const [enderecoSelecionado, setEnderecoSelecionado] = useState(null)
  const [carregandoEnderecos, setCarregandoEnderecos] = useState(false)
  const [modalEnderecoAberto, setModalEnderecoAberto] = useState(false)
  const [modalEnderecoConfig, setModalEnderecoConfig] = useState({
    modo: 'lista',
    endereco: null,
  })

  // Estados de Pagamento e Cartões
  const [tipoPagamento, setTipoPagamento] = useState('cartao') // 'cartao' | 'pix' | 'boleto'
  const [cartoes, setCartoes] = useState(() =>
    cardService.listar(usuario?.id || 'guest'),
  )
  const [cartaoSelecionado, setCartaoSelecionado] = useState(() => {
    const lista = cardService.listar(usuario?.id || 'guest')
    const padrao = lista.find((c) => c.isDefault)
    return padrao || lista[0] || null
  })
  const [modalCartaoAberto, setModalCartaoAberto] = useState(false)
  const [modalCartaoConfig, setModalCartaoConfig] = useState({
    modo: 'lista',
    cartao: null,
  })

  // Estados de Observações e Envio
  const [observacoes, setObservacoes] = useState('')
  const [erroGeral, setErroGeral] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const [pedido, setPedido] = useState(null)

  // Estados de Cupons
  const [cupons, setCupons] = useState([])
  const [cupomSelecionado, setCupomSelecionado] = useState(null)

  // Totais do carrinho
  const { subtotal, frete, total: totalBase } = useMemo(
    () => calcularTotais(itens),
    [itens],
  )

  // Cupons válidos para a sacola atual: ativos, não expirados, aplicáveis a
  // algum item da sacola e com compra mínima atingida.
  const cuponsDisponiveis = useMemo(() => {
    const agora = new Date()
    const productIds = new Set(
      itens.map((item) => item.productId ?? item.id).filter((id) => id != null),
    )
    return cupons.filter((cupom) => {
      if (!cupom.is_active) return false
      if (cupom.valid_until && new Date(cupom.valid_until) < agora) return false
      if (cupom.product_id != null && !productIds.has(cupom.product_id)) return false
      if (
        cupom.min_purchase != null &&
        subtotal < Number(cupom.min_purchase)
      )
        return false
      return true
    })
  }, [cupons, itens, subtotal])

  // Cupom efetivamente aplicado: derivado dos disponíveis, o que expira/
  // deixa de valer sozinho quando a sacola muda (sem efeito nem setState).
  const cupomAplicado =
    cuponsDisponiveis.find((c) => c.id === cupomSelecionado?.id) ?? null

  // Desestimativa do desconto do cupom selecionado (mesma regra do backend:
  // percentage = % sobre o subtotal; fixed = valor absoluto; teto em
  // max_discount). O servidor recalcula e valida na criação do pedido.
  const desconto = useMemo(() => {
    if (!cupomAplicado) return 0
    if (cupomAplicado.discount_type === 'percentage') {
      return Math.min(
        subtotal * (cupomAplicado.discount_value / 100),
        cupomAplicado.max_discount ?? Infinity,
      )
    }
    return Math.min(cupomAplicado.discount_value, subtotal)
  }, [cupomAplicado, subtotal])

  const total = Math.max(0, totalBase - desconto)

  // Carrega os cupons ATRIBUÍDOS ao usuário autenticado (ownership).
  // Sem login não há vínculo: a lista simplesmente fica vazia (não busca).
  useEffect(() => {
    if (!autenticado) return
    let ativo = true
    couponService
      .meusCupons()
      .then((lista) => {
        if (ativo) setCupons(Array.isArray(lista) ? lista : [])
      })
      .catch(() => {
        if (ativo) setCupons([])
      })
    return () => {
      ativo = false
    }
  }, [autenticado])

  // Carrega os endereços do usuário
  const carregarEnderecos = useCallback(async () => {
    if (!autenticado) {
      setEnderecos([])
      setEnderecoSelecionado(null)
      return
    }

    try {
      setCarregandoEnderecos(true)
      const lista = await addressService.listar()
      const arr = Array.isArray(lista) ? lista : []
      setEnderecos(arr)

      setEnderecoSelecionado((atual) => {
        if (atual && arr.some((e) => e.id === atual.id)) {
          return arr.find((e) => e.id === atual.id)
        }
        const padrao = arr.find((e) => e.is_default)
        return padrao || arr[0] || null
      })
    } catch (err) {
      console.error('Erro ao carregar endereços:', err)
    } finally {
      setCarregandoEnderecos(false)
    }
  }, [autenticado])

  // Carrega os cartões salvos do usuário
  const carregarCartoes = useCallback(() => {
    const userId = usuario?.id || 'guest'
    const lista = cardService.listar(userId)
    setCartoes(lista)

    setCartaoSelecionado((atual) => {
      if (atual && lista.some((c) => c.id === atual.id)) {
        return lista.find((c) => c.id === atual.id)
      }
      const padrao = lista.find((c) => c.isDefault)
      return padrao || lista[0] || null
    })
  }, [usuario?.id])

  useEffect(() => {
    let ativo = true
    async function carregar() {
      if (!autenticado) {
        if (ativo) {
          setEnderecos([])
          setEnderecoSelecionado(null)
        }
        return
      }
      try {
        setCarregandoEnderecos(true)
        const lista = await addressService.listar()
        if (!ativo) return
        const arr = Array.isArray(lista) ? lista : []
        setEnderecos(arr)
        setEnderecoSelecionado((atual) => {
          if (atual && arr.some((e) => e.id === atual.id)) {
            return arr.find((e) => e.id === atual.id)
          }
          const padrao = arr.find((e) => e.is_default)
          return padrao || arr[0] || null
        })
      } catch (err) {
        console.error('Erro ao carregar endereços:', err)
      } finally {
        if (ativo) setCarregandoEnderecos(false)
      }
    }

    carregar()
    return () => {
      ativo = false
    }
  }, [autenticado])

  // Handlers para os Modais
  const abrirModalEndereco = ({ modo = 'lista', endereco = null } = {}) => {
    setModalEnderecoConfig({ modo, endereco })
    setModalEnderecoAberto(true)
  }

  const abrirModalCartao = ({ modo = 'lista', cartao = null } = {}) => {
    setModalCartaoConfig({ modo, cartao })
    setModalCartaoAberto(true)
  }

  // Finalização do Pedido
  const handleSubmit = async (event) => {
    event.preventDefault()
    if (enviando || pedido) return

    setErroGeral(null)

    if (!autenticado) {
      setErroGeral({
        message: 'Entre na sua conta para finalizar a compra.',
        code: 'NOT_AUTHENTICATED',
      })
      return
    }

    if (itens.length === 0) {
      setErroGeral({
        message: 'Sua sacola está vazia.',
        code: 'EMPTY_CART',
      })
      return
    }

    if (!enderecoSelecionado) {
      setErroGeral({
        message: 'Por favor, selecione ou cadastre um endereço de entrega.',
        code: 'MISSING_ADDRESS',
      })
      abrirModalEndereco({ modo: enderecos.length === 0 ? 'novo' : 'lista' })
      return
    }

    if (tipoPagamento === 'cartao' && !cartaoSelecionado) {
      setErroGeral({
        message: 'Por favor, selecione ou cadastre um cartão de crédito.',
        code: 'MISSING_CARD',
      })
      abrirModalCartao({ modo: cartoes.length === 0 ? 'novo' : 'lista' })
      return
    }

    setEnviando(true)

    try {
      // Monta resumo do pagamento para as notas do pedido
      let notasPagamento = `Pagamento: ${tipoPagamento.toUpperCase()}`
      if (tipoPagamento === 'cartao' && cartaoSelecionado) {
        notasPagamento += ` (${cartaoSelecionado.bandeiraNome} final ${cartaoSelecionado.ultimos4})`
      }
      if (observacoes.trim()) {
        notasPagamento += ` | Obs: ${observacoes.trim()}`
      }

      // Criação do pedido com os itens reais da sacola e endereço selecionado
      const criado = await orderService.criar({
        address_id: enderecoSelecionado.id,
        notes: notasPagamento,
        ...(cupomAplicado ? { coupon_id: cupomAplicado.id } : {}),
        items: itens.map((item) => ({
          product_id: item.productId ?? item.id,
          quantity: item.quantidade,
        })),
      })

      setPedido(criado)
      // O backend esvazia o carrinho no checkout; sincroniza o badge/estado.
      await recarregar()
    } catch (error) {
      setErroGeral(error)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="bg-cream-deep min-h-screen">
      <div className="mx-auto max-w-[1400px] px-5 py-12 sm:px-8 sm:py-16">
        <h1 className="font-display text-[2.5rem] leading-tight font-normal text-coffee sm:text-[3.25rem]">
          Finalizar compra
        </h1>

        <div className="mt-10 grid gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)] lg:gap-16">
          <ResumoPedido
            itens={itens}
            subtotal={subtotal}
            frete={frete}
            desconto={desconto}
            cupom={cupomAplicado}
            total={total}
            formatarPreco={formatarPreco}
          />

          {/* Seção de Seleção e Checkout */}
          <section className="rounded-md border border-line bg-cream-soft p-6 sm:p-9 shadow-sm flex flex-col justify-between">
            <div>
              <h2 className="font-display text-[1.75rem] font-normal text-coffee">
                Entrega e Pagamento
              </h2>

              {/* Alerta de Autenticação */}
              {!autenticado && (
                <div className="mt-6 flex flex-wrap items-center gap-x-3 gap-y-2 border-y border-line py-4">
                  <p className="font-body text-[0.9rem] text-coffee-soft">
                    Você precisa estar logado para selecionar seus endereços e finalizar a compra.
                  </p>
                  <button
                    type="button"
                    onClick={onIrParaLogin}
                    className="font-body text-[0.8rem] font-semibold uppercase tracking-[0.16em] text-gold transition-colors duration-300 hover:text-caramel-dark"
                  >
                    Entrar na conta
                  </button>
                </div>
              )}

              {/* Erros Gerais */}
              {erroGeral && (
                <div
                  role="alert"
                  className="mt-6 rounded-sm border border-[#a4533f]/30 bg-[#a4533f]/[0.06] px-4 py-3 font-body text-[0.86rem] font-medium tracking-wide text-[#a4533f]"
                >
                  {erroGeral.message}
                </div>
              )}

              {/* Sucesso / Pedido Confirmado */}
              {pedido ? (
                <div className="mt-6 rounded-md border border-forest/40 bg-forest/[0.06] p-6 text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-forest text-cream-soft font-bold text-xl shadow-sm mb-3">
                    ✓
                  </div>
                  <h3 className="font-display text-2xl font-normal text-coffee">
                    Pedido #{pedido.id} confirmado com sucesso!
                  </h3>
                  <p className="font-body text-sm text-coffee-soft mt-2">
                    Total pago:{' '}
                    <strong className="text-coffee font-semibold">
                      {formatarPreco(pedido.total)}
                    </strong>
                  </p>
                  <p className="font-body text-xs text-coffee-faint mt-1">
                    Um e-mail de confirmação foi enviado com os detalhes do envio.
                  </p>
                  {enderecoSelecionado && (
                    <div className="mt-4 rounded-sm bg-cream-soft border border-line p-3 text-left">
                      <p className="font-body text-xs font-semibold text-coffee">
                        Endereço de entrega selecionado:
                      </p>
                      <p className="font-body text-xs text-coffee-soft mt-0.5">
                        {enderecoSelecionado.street}, {enderecoSelecionado.number} • {enderecoSelecionado.city}/{enderecoSelecionado.state}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <form onSubmit={handleSubmit} noValidate className="mt-8 space-y-8">
                  {/* 1. Seletor de Endereço de Entrega */}
                  <fieldset disabled={enviando || !autenticado}>
                    <SeletorEndereco
                      enderecos={enderecos}
                      enderecoSelecionadoId={enderecoSelecionado?.id}
                      onSelecionarEndereco={(end) => setEnderecoSelecionado(end)}
                      onAbrirModal={abrirModalEndereco}
                      carregando={carregandoEnderecos}
                    />
                  </fieldset>

                  <div className="border-t border-line" />

                  {/* 2. Seletor de Cupom de Desconto */}
                  <SecaoCupons
                    cuponsDisponiveis={cuponsDisponiveis}
                    cupomSelecionado={cupomSelecionado}
                    onSelecionarCupom={setCupomSelecionado}
                    desabilitado={enviando || !autenticado}
                  />

                  <div className="border-t border-line" />

                  {/* 3. Seletor de Método de Pagamento */}
                  <fieldset disabled={enviando || !autenticado}>
                    <SeletorPagamento
                      tipoPagamento={tipoPagamento}
                      onMudarTipoPagamento={setTipoPagamento}
                      cartoes={cartoes}
                      cartaoSelecionadoId={cartaoSelecionado?.id}
                      onSelecionarCartao={(card) => setCartaoSelecionado(card)}
                      onAbrirModalCartao={abrirModalCartao}
                    />
                  </fieldset>

                  {/* Observações adicionais */}
                  <div>
                    <label
                      htmlFor="observacoes"
                      className="block font-body text-xs font-semibold uppercase tracking-wider text-coffee-soft mb-1.5"
                    >
                      Observações para entrega (opcional)
                    </label>
                    <textarea
                      id="observacoes"
                      rows={2}
                      value={observacoes}
                      onChange={(e) => setObservacoes(e.target.value)}
                      placeholder="Ex: Deixar com a portaria, ponto de referência..."
                      disabled={enviando || !autenticado}
                      className="w-full rounded-sm border border-line-strong bg-cream-soft px-4 py-2.5 font-body text-xs text-coffee placeholder:text-coffee-faint transition-colors focus:border-forest focus:outline-none"
                    />
                  </div>

                  {/* Botão de Finalização */}
                  <div>
                    <button
                      type="submit"
                      disabled={enviando || Boolean(pedido) || carrinhoCarregando || !autenticado}
                      className="w-full rounded-sm bg-forest py-4 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft shadow-md transition-all duration-300 ease-[var(--ease-cozy)] hover:bg-forest-soft hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {enviando ? 'Processando pedido…' : 'Concluir compra'}
                    </button>

                    <p className="mt-4 flex items-center justify-center gap-2 font-body text-[0.8rem] font-medium text-coffee-faint">
                      <LockIcon className="h-4 w-4" />
                      Ambiente seguro com criptografia de ponta a ponta.
                    </p>
                  </div>
                </form>
              )}
            </div>
          </section>
        </div>
      </div>

      {/* Modal de CRUD de Endereços */}
      <ModalEndereco
        isOpen={modalEnderecoAberto}
        onClose={() => setModalEnderecoAberto(false)}
        enderecos={enderecos}
        enderecoSelecionadoId={enderecoSelecionado?.id}
        onSelecionarEndereco={(end) => setEnderecoSelecionado(end)}
        onRecarregarEnderecos={carregarEnderecos}
        modoInicial={modalEnderecoConfig.modo}
        enderecoParaEditar={modalEnderecoConfig.endereco}
      />

      {/* Modal de CRUD de Cartões de Pagamento */}
      <ModalCartao
        isOpen={modalCartaoAberto}
        onClose={() => setModalCartaoAberto(false)}
        userId={usuario?.id}
        cartoes={cartoes}
        cartaoSelecionadoId={cartaoSelecionado?.id}
        onSelecionarCartao={(card) => setCartaoSelecionado(card)}
        onRecarregarCartoes={carregarCartoes}
        modoInicial={modalCartaoConfig.modo}
        cartaoParaEditar={modalCartaoConfig.cartao}
      />
    </main>
  )
}
