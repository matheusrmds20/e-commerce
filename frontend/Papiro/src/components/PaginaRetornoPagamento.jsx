import { useCallback, useEffect, useRef, useState } from 'react'
import paymentService, {
  ROTULO_STATUS,
  STATUS_PAGAMENTO,
} from '../api/payments'
import { formatarPreco } from '../api/adapters'
import { LockIcon } from './Icons'

const INTERVALO_POLLING_MS = 4000
const MAX_TENTATIVAS = 15 // ~1 minuto

/**
 * PaginaRetornoPagamento — tela de retorno do Mercado Pago.
 *
 * O backend redireciona para cá com `back_urls`:
 *   /payment/success | /payment/failure | /payment/pending
 * e o Mercado Pago acrescenta `?payment_id=...&status=...` (quando disponível).
 *
 * Como o status real só é atualizado pelo WEBHOOK no backend, aqui:
 * - no retorno `pending`, consultamos `GET /payments/order/{order_id}` em
 *   intervalos até o pagamento sair de `pending` (ou estourar as tentativas);
 * - nos retornos `success`/`failure`, fazemos uma consulta única para confirmar.
 *
 * O `order_id` vem da query (`external_reference`/`order_id`) ou, em último
 * caso, do `sessionStorage` gravado pelo Checkout antes do redirect.
 */
export default function PaginaRetornoPagamento({ resultado: resultadoUrl, onVoltarParaLoja }) {
  const [carregando, setCarregando] = useState(true)
  const [pagamento, setPagamento] = useState(null)
  const [erro, setErro] = useState(null)
  const [tentativas, setTentativas] = useState(0)
  const [desistiu, setDesistiu] = useState(false)

  const timerRef = useRef(null)
  const tentativasRef = useRef(0)

  // Descobre o order_id: prioridade para a query, fallback no sessionStorage.
  const obterOrderId = useCallback(() => {
    if (typeof window === 'undefined') return null
    const params = new URLSearchParams(window.location.search)
    const daQuery =
      params.get('order_id') ??
      params.get('external_reference') ??
      params.get('pedido')
    if (daQuery && /^\d+$/.test(daQuery)) return Number(daQuery)

    try {
      const salvo = sessionStorage.getItem('papiro.ultimo_pedido')
      if (salvo && /^\d+$/.test(salvo)) return Number(salvo)
    } catch {
      /* sessionStorage indisponível */
    }
    return null
  }, [])

  const consultar = useCallback(async () => {
    const orderId = obterOrderId()

    if (!orderId) {
      setErro('Não foi possível identificar o pedido deste pagamento.')
      setCarregando(false)
      return null
    }

    try {
      const lista = await paymentService.listarPorPedido(orderId)
      const arr = Array.isArray(lista) ? lista : []
      // O pagamento mais recente do pedido representa o estado atual.
      const atual = arr[0] ?? null
      setPagamento(atual)
      setErro(null)
      return atual
    } catch (err) {
      setErro(err?.message ?? 'Não foi possível consultar o pagamento.')
      return null
    } finally {
      setCarregando(false)
    }
  }, [obterOrderId])

  // Primeira consulta ao montar (padrão async IIFE + flag `ativo` usado no
  // restante do projeto — evita setState síncrono no corpo do efeito).
  useEffect(() => {
    let ativo = true
    async function iniciar() {
      if (ativo) await consultar()
    }
    iniciar()
    return () => {
      ativo = false
    }
    // Consulta apenas na montagem; recargas são disparadas pelo polling/botão.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Polling: enquanto `pending` e no retorno pending/success, segue tentando.
  useEffect(() => {
    const devePoll =
      resultadoUrl !== 'failure' &&
      !desistiu &&
      pagamento?.status === STATUS_PAGAMENTO.PENDING

    if (!devePoll) return undefined

    if (tentativasRef.current >= MAX_TENTATIVAS) {
      setDesistiu(true)
      return undefined
    }

    timerRef.current = setTimeout(async () => {
      tentativasRef.current += 1
      setTentativas(tentativasRef.current)
      await consultar()
    }, INTERVALO_POLLING_MS)

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [pagamento, resultadoUrl, desistiu, consultar])

  const status = pagamento?.status
  const aprovado = status === STATUS_PAGAMENTO.APPROVED
  const recusado = status === STATUS_PAGAMENTO.REJECTED || resultadoUrl === 'failure'
  const pendente = status === STATUS_PAGAMENTO.PENDING || resultadoUrl === 'pending'

  const tema = aprovado
    ? {
        icone: '✓',
        circulo: 'bg-forest text-cream-soft',
        borda: 'border-forest/40 bg-forest/[0.06]',
        titulo: 'Pagamento aprovado!',
        texto: 'Seu pedido foi confirmado e já está sendo preparado para envio.',
      }
    : recusado
      ? {
          icone: '✕',
          circulo: 'bg-[#a4533f] text-cream-soft',
          borda: 'border-[#a4533f]/30 bg-[#a4533f]/[0.06]',
          titulo: 'Pagamento não concluído',
          texto:
            'O pagamento não foi aprovado. Você pode tentar novamente com outro método.',
        }
      : {
          icone: '⏳',
          circulo: 'bg-gold text-coffee',
          borda: 'border-gold/40 bg-gold/[0.08]',
          titulo: 'Aguardando confirmação',
          texto:
            'Seu pagamento está sendo processado. A confirmação pode levar alguns instantes.',
        }

  return (
    <main className="bg-cream-deep min-h-screen">
      <div className="mx-auto flex max-w-2xl flex-col items-center px-5 py-20 sm:py-28">
        <div
          className={`w-full rounded-md border p-8 text-center shadow-sm sm:p-12 ${tema.borda}`}
        >
          <div
            className={`mx-auto flex h-16 w-16 items-center justify-center rounded-full text-3xl font-bold shadow-sm ${tema.circulo}`}
          >
            {tema.icone}
          </div>

          <h1 className="mt-6 font-display text-3xl font-normal text-coffee sm:text-4xl">
            {tema.titulo}
          </h1>

          <p className="mx-auto mt-3 max-w-md font-body text-[0.95rem] leading-relaxed text-coffee-soft">
            {tema.texto}
          </p>

          {pagamento && (
            <dl className="mx-auto mt-8 max-w-xs space-y-2 rounded-sm border border-line bg-cream-soft/60 px-5 py-4 text-left">
              <div className="flex items-center justify-between gap-4">
                <dt className="font-body text-[0.78rem] uppercase tracking-wider text-coffee-faint">
                  Pedido
                </dt>
                <dd className="font-body text-sm font-semibold text-coffee">
                  #{pagamento.order_id}
                </dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="font-body text-[0.78rem] uppercase tracking-wider text-coffee-faint">
                  Valor
                </dt>
                <dd className="font-body text-sm font-semibold text-coffee">
                  {formatarPreco(pagamento.amount)}
                </dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="font-body text-[0.78rem] uppercase tracking-wider text-coffee-faint">
                  Status
                </dt>
                <dd className="font-body text-sm font-semibold text-coffee">
                  {ROTULO_STATUS[pagamento.status] ?? pagamento.status}
                </dd>
              </div>
            </dl>
          )}

          {pendente && !desistiu && (
            <p className="mt-6 flex items-center justify-center gap-2 font-body text-[0.82rem] text-coffee-faint">
              <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-coffee-faint/40 border-t-forest" />
              Verificando o status automaticamente… ({tentativas}/{MAX_TENTATIVAS})
            </p>
          )}

          {pendente && desistiu && (
            <p className="mt-6 font-body text-[0.82rem] text-coffee-faint">
              Ainda não recebemos a confirmação. Você pode verificar em Minha
              Conta mais tarde — o status é atualizado automaticamente.
            </p>
          )}

          {carregando && !pagamento && (
            <p className="mt-6 font-body text-[0.82rem] text-coffee-faint">
              Carregando detalhes do pagamento…
            </p>
          )}

          {erro && (
            <p
              role="alert"
              className="mt-6 rounded-sm border border-[#a4533f]/30 bg-[#a4533f]/[0.06] px-4 py-3 font-body text-[0.84rem] font-medium text-[#a4533f]"
            >
              {erro}
            </p>
          )}

          <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <button
              type="button"
              onClick={onVoltarParaLoja}
              className="w-full rounded-sm bg-forest px-8 py-3.5 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft shadow-md transition-colors duration-300 hover:bg-forest-soft sm:w-auto"
            >
              Voltar para a loja
            </button>
            {(pendente || erro) && (
              <button
                type="button"
                onClick={async () => {
                  tentativasRef.current = 0
                  setTentativas(0)
                  setDesistiu(false)
                  setCarregando(true)
                  await consultar()
                }}
                className="w-full rounded-sm border border-line-strong px-8 py-3.5 font-body text-xs font-semibold uppercase tracking-[0.2em] text-coffee-soft transition-colors duration-300 hover:border-gold hover:text-caramel sm:w-auto"
              >
                Verificar novamente
              </button>
            )}
          </div>
        </div>

        <p className="mt-8 flex items-center justify-center gap-2 font-body text-[0.78rem] font-medium text-coffee-faint">
          <LockIcon className="h-4 w-4" />
          Pagamento processado com segurança pelo Mercado Pago.
        </p>
      </div>
    </main>
  )
}
