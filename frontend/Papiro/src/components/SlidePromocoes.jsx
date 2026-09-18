import { useState, useEffect, useRef } from 'react'
import { ArrowLeftIcon, ArrowRightIcon, BagIcon } from './Icons'
import { formatarPreco } from '../api/adapters'

/**
 * SlidePromocoes — Slider interativo de ofertas especiais com badges de
 * desconto e navegação fluida.
 *
 * Recebe `ofertas` (produtos com desconto vindos da API, já normalizados por
 * `produtoParaCard`). Estados possíveis:
 * - `carregando`: esqueleto pulsante.
 * - vazio: mensagem "sem ofertas no momento" — a seção não some para manter o
 *   ritmo visual da Home, mas deixa claro que não há promoções ativas.
 */
export default function SlidePromocoes({ ofertas = [], carregando = false, onAbrirLivro }) {
  const scrollRef = useRef(null)
  const [podeVoltar, setPodeVoltar] = useState(false)
  const [podeAvancar, setPodeAvancar] = useState(true)

  const verificarBotoes = () => {
    if (!scrollRef.current) return
    const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current
    setPodeVoltar(scrollLeft > 10)
    setPodeAvancar(scrollLeft + clientWidth < scrollWidth - 10)
  }

  useEffect(() => {
    verificarBotoes()
    window.addEventListener('resize', verificarBotoes)
    return () => window.removeEventListener('resize', verificarBotoes)
  }, [])

  const rolar = (direcao) => {
    if (!scrollRef.current) return
    const larguraCard = scrollRef.current.clientWidth * 0.75
    scrollRef.current.scrollBy({
      left: direcao === 'dir' ? larguraCard : -larguraCard,
      behavior: 'smooth',
    })
  }

  return (
    <section id="promocoes" className="bg-cream-soft py-16 sm:py-24">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
        {/* Cabeçalho com título e controles do Slider */}
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-gold/15 px-3.5 py-1 text-gold-dark">
              <span className="h-2 w-2 rounded-full bg-gold animate-pulse" />
              <span className="font-body text-[0.72rem] font-semibold uppercase tracking-[0.2em]">
                Ofertas por Tempo Limitado
              </span>
            </div>

            <h2 className="mt-3 font-display text-[2.4rem] font-normal leading-tight tracking-[-0.01em] text-forest sm:text-[3.25rem]">
              Promoções da Semana
            </h2>

            <p className="mt-2 max-w-[34rem] font-body text-[0.95rem] font-normal leading-relaxed text-coffee-soft sm:text-[1.02rem]">
              Edições especiais, boxes e títulos selecionados com até 40% de desconto para enriquecer seu acervo.
            </p>
          </div>

          {/* Botões de navegação do carrossel */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => rolar('esq')}
              disabled={!podeVoltar}
              aria-label="Voltar slide de promoções"
              className={`grid h-11 w-11 place-items-center rounded-sm border transition-all duration-300 ${
                podeVoltar
                  ? 'border-line-strong bg-cream text-coffee hover:border-forest hover:bg-cream-tint focus-visible:outline focus-visible:outline-2 focus-visible:outline-forest'
                  : 'cursor-not-allowed border-line/60 bg-cream/40 text-coffee-faint/40'
              }`}
            >
              <ArrowLeftIcon className="h-4 w-4" />
            </button>

            <button
              type="button"
              onClick={() => rolar('dir')}
              disabled={!podeAvancar}
              aria-label="Avançar slide de promoções"
              className={`grid h-11 w-11 place-items-center rounded-sm border transition-all duration-300 ${
                podeAvancar
                  ? 'border-line-strong bg-cream text-coffee hover:border-forest hover:bg-cream-tint focus-visible:outline focus-visible:outline-2 focus-visible:outline-forest'
                  : 'cursor-not-allowed border-line/60 bg-cream/40 text-coffee-faint/40'
              }`}
            >
              <ArrowRightIcon className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Trilha do Carrossel / Slider */}
        <div
          ref={scrollRef}
          onScroll={verificarBotoes}
          className="mt-10 flex gap-6 overflow-x-auto pb-6 pt-2 scroll-smooth [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden"
        >
          {carregando &&
            Array.from({ length: 4 }).map((_, i) => (
              <div
                key={`skeleton-${i}`}
                className="flex w-[280px] shrink-0 flex-col rounded-md border border-line bg-cream-deep p-4 sm:w-[320px]"
              >
                <div className="aspect-[3/4] animate-pulse rounded-sm bg-line/60" />
                <div className="mt-4 h-5 w-4/5 animate-pulse rounded-sm bg-line/60" />
                <div className="mt-2 h-3 w-2/5 animate-pulse rounded-sm bg-line/50" />
                <div className="mt-4 h-6 w-1/2 animate-pulse rounded-sm bg-line/60" />
              </div>
            ))}

          {!carregando && ofertas.length === 0 && (
            <div className="w-full rounded-md border border-dashed border-line-strong bg-cream-deep/60 px-6 py-14 text-center">
              <p className="font-display text-xl text-coffee">
                Sem promoções ativas no momento
              </p>
              <p className="mt-2 font-body text-sm text-coffee-soft">
                Volte em breve — nossa curadoria prepara novas ofertas toda
                semana.
              </p>
            </div>
          )}

          {!carregando &&
            ofertas.map((item) => (
            <article
              key={item.id}
              className="group flex w-[280px] shrink-0 flex-col rounded-md border border-line bg-cream-deep p-4 transition-all duration-500 ease-[var(--ease-cozy)] hover:-translate-y-1 hover:border-line-strong hover:shadow-lg sm:w-[320px]"
            >
              {/* Moldura da Imagem */}
              <div className="relative aspect-[3/4] overflow-hidden rounded-sm bg-coffee">
                <img
                  src={item.imagem}
                  alt={`Capa de ${item.titulo}`}
                  className="h-full w-full object-cover transition-transform duration-700 ease-[var(--ease-cozy)] group-hover:scale-105"
                  loading="lazy"
                />

                {/* Tag de Desconto */}
                <span className="absolute left-3 top-3 rounded-sm bg-forest px-2.5 py-1 font-body text-[0.72rem] font-bold tracking-wider text-cream shadow-md">
                  {item.desconto}
                </span>

                {/* Tag do Tipo */}
                <span className="absolute right-3 top-3 rounded-sm bg-cream-soft/95 px-2.5 py-1 font-body text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-coffee shadow-sm backdrop-blur-sm">
                  {item.estoque > 0 && item.estoque <= 5
                    ? 'Últimas Unidades'
                    : 'Oferta'}
                </span>

                {/* Ação rápida hover */}
                <button
                  type="button"
                  onClick={() => onAbrirLivro?.(item.id)}
                  className="absolute inset-x-3 bottom-3 flex items-center justify-center gap-2 rounded-sm bg-cream-soft/95 py-2.5 font-body text-[0.75rem] font-semibold uppercase tracking-[0.2em] text-forest opacity-0 shadow transition-all duration-300 group-hover:opacity-100 hover:bg-forest hover:text-cream-soft"
                >
                  <BagIcon className="h-3.5 w-3.5" />
                  <span>Aproveitar Oferta</span>
                </button>
              </div>

              {/* Informações */}
              <div className="mt-4 flex flex-1 flex-col justify-between">
                <div>
                  <h3 className="font-display text-[1.35rem] font-normal leading-snug text-coffee">
                    <a
                      href="#"
                      onClick={(e) => {
                        e.preventDefault()
                        onAbrirLivro?.(item.id)
                      }}
                      className="transition-colors duration-300 hover:text-gold"
                    >
                      {item.titulo}
                    </a>
                  </h3>
                  <p className="mt-1 font-body text-[0.8rem] font-medium uppercase tracking-[0.14em] text-coffee-soft">
                    {item.autor}
                  </p>
                </div>

                <div className="mt-4 flex items-baseline justify-between border-t border-line/70 pt-3">
                  <div className="flex items-baseline gap-2">
                    <span className="font-body text-[1.2rem] font-bold text-forest">
                      {formatarPreco(item.precoFinal)}
                    </span>
                    {item.precoOriginal != null && (
                      <span className="font-body text-[0.88rem] font-normal text-coffee-faint line-through">
                        {formatarPreco(item.precoOriginal)}
                      </span>
                    )}
                  </div>

                  <span className="font-body text-[0.72rem] font-semibold text-gold-dark uppercase tracking-wider">
                    Economize
                  </span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
