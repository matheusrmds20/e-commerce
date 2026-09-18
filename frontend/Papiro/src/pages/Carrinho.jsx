import { useEffect, useMemo, useState } from 'react'
import ItemCarrinho from '../components/ItemCarrinho'
import ResumoCarrinho from '../components/ResumoCarrinho'
import CartaoRecomendado from '../components/CartaoRecomendado'
import { useCart } from '../context/cart-context'
import { useAuth } from '../context/auth-context'
import { calcularTotais, formatarPreco } from '../api/adapters'

/**
 * Carrinho — sacola conectada à API.
 *
 * O estado vive no CartContext (a Navbar usa o mesmo para o badge).
 * Visitantes são avisados de que a sacola só persiste após o login.
 */
export default function Carrinho({ onCheckout, onIrParaLogin }) {
  const {
    itens,
    carregando,
    erro,
    alterarQuantidade,
    remover,
    adicionar,
    recomendados,
    totalItens,
  } = useCart()
  const { autenticado } = useAuth()

  const [recomendadosLista, setRecomendadosLista] = useState([])
  const [acaoErro, setAcaoErro] = useState(null)

  // Totais derivados dos itens atuais (frete grátis a partir de R$ 150).
  const { subtotal, frete, total } = useMemo(
    () => calcularTotais(itens),
    [itens],
  )

  // Busca recomendações no catálogo real.
  useEffect(() => {
    let ativo = true
    recomendados()
      .then((lista) => {
        if (ativo) setRecomendadosLista(lista)
      })
      .catch(() => {
        if (ativo) setRecomendadosLista([])
      })
    return () => {
      ativo = false
    }
  }, [recomendados])

  /** Envolve ações que falam com a API para exibir falhas sem quebrar a tela. */
  const comTratamento = (fn) => async (...args) => {
    setAcaoErro(null)
    try {
      await fn(...args)
    } catch (error) {
      setAcaoErro(error)
    }
  }

  const aoAlterarQuantidade = comTratamento(alterarQuantidade)
  const aoRemover = comTratamento(remover)
  const aoAdicionarRecomendado = comTratamento((produto) => adicionar(produto, 1))

  return (
    <main className="bg-cream-deep">
      <div className="mx-auto max-w-[1400px] px-5 py-12 sm:px-8 sm:py-16">
        <h1 className="font-display text-[2.5rem] leading-tight font-normal text-coffee sm:text-[3.25rem]">
          Sacola de compras
        </h1>

        {/* Visitante — a sacola ainda não persiste no servidor */}
        {!autenticado && itens.length > 0 && (
          <div className="mt-6 flex flex-wrap items-center gap-x-3 gap-y-2 border-y border-line py-4">
            <p className="font-body text-[0.9rem] text-coffee-soft">
              Sua sacola ainda não está salva.
            </p>
            <button
              type="button"
              onClick={onIrParaLogin}
              className="font-body text-[0.8rem] font-semibold uppercase tracking-[0.16em] text-gold transition-colors duration-300 hover:text-caramel-dark"
            >
              Entrar para salvar
            </button>
          </div>
        )}

        {(erro || acaoErro) && (
          <div
            role="alert"
            className="mt-6 rounded-sm border border-[#a4533f]/30 bg-[#a4533f]/[0.06] px-4 py-3 font-body text-[0.86rem] font-medium tracking-wide text-[#a4533f]"
          >
            {acaoErro?.message ?? erro?.message}
          </div>
        )}

        {carregando && itens.length === 0 ? (
          <p className="mt-10 border-y border-line py-16 text-center font-body text-[0.95rem] tracking-wide text-coffee-soft">
            Abrindo sua sacola…
          </p>
        ) : itens.length === 0 ? (
          <p className="mt-10 border-y border-line py-16 text-center font-display text-2xl text-coffee-soft">
            Sua sacola está vazia.
          </p>
        ) : (
          <div className="mt-10 grid gap-12 lg:grid-cols-[1fr_380px] lg:gap-14">
            {/* Lista */}
            <div>
              {/* Cabeçalho da tabela — só no desktop */}
              <div className="hidden border-b border-line pb-4 sm:grid sm:grid-cols-[96px_1fr_auto_auto] sm:gap-6">
                <span className="font-body text-[0.95rem] font-semibold text-coffee">
                  Livro
                </span>
                <span className="font-body text-[0.95rem] font-semibold text-coffee">
                  Título
                </span>
                <span className="font-body text-[0.95rem] font-semibold text-coffee">
                  Quantidade
                </span>
                <span className="min-w-[92px] text-right font-body text-[0.95rem] font-semibold text-coffee">
                  Preço
                </span>
              </div>

              <ul>
                {itens.map((item) => (
                  <ItemCarrinho
                    key={item.id}
                    item={item}
                    onQuantidade={aoAlterarQuantidade}
                    onRemover={aoRemover}
                    formatarPreco={formatarPreco}
                  />
                ))}
              </ul>

              <p className="mt-6 font-body text-[0.88rem] font-medium italic text-coffee-faint">
                {totalItens}{' '}
                {totalItens === 1 ? 'exemplar' : 'exemplares'} na sacola
              </p>
            </div>

            {/* Resumo */}
            <ResumoCarrinho
              subtotal={subtotal}
              frete={frete}
              total={total}
              formatarPreco={formatarPreco}
              onCheckout={onCheckout}
            />
          </div>
        )}

        {/* Recomendações — vindas do catálogo real */}
        {recomendadosLista.length > 0 && (
          <section className="mt-20 border-t border-line pt-14 sm:mt-24">
            <h2 className="text-center font-display text-[2rem] leading-tight font-normal text-forest sm:text-[2.6rem]">
              Você também pode gostar destes momentos tranquilos
            </h2>

            <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {recomendadosLista.map((item) => (
                <CartaoRecomendado
                  key={item.id}
                  item={item}
                  formatarPreco={formatarPreco}
                  onAdicionar={aoAdicionarRecomendado}
                />
              ))}
            </div>
          </section>
        )}
      </div>
    </main>
  )
}
