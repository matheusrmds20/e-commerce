import { ArrowRightIcon, BagIcon } from './Icons'
import Estrelas from './Estrelas'
import Quill from './Quill'
import { formatarPreco } from '../api/adapters'
import { useCart } from '../context/cart-context'
import { useState } from 'react'

/**
 * RecomendacaoDestaque — Destaque editorial com o livro recomendado da casa.
 *
 * Dados reais vindos da API (via `carregarHome`):
 * - `recomendacao.produto`: primeiro produto ativo (idealmente com estoque).
 * - `recomendacao.notaMedia`: média das avaliações do produto.
 * - `recomendacao.avaliacoes`: lista crua (contagem).
 *
 * Limitações conhecidas do backend (ver relatório de integração):
 * - Não existe campo de resenha editorial, citação ou curador no modelo de
 *   produto. Esses blocos só aparecem se o produto trouxer `description`/
 *   `synopsis`; caso contrário, são omitidos em vez de exibir texto fictício.
 * - Não há endpoint de "recomendação da casa"; a seleção é feita no front.
 */
export default function RecomendacaoDestaque({
  recomendacao = null,
  carregando = false,
  onAbrirLivro,
}) {
  const { adicionar } = useCart()
  const [feedback, setFeedback] = useState(null)

  if (carregando) {
    return (
      <section id="recomendacao" className="bg-cream-deep py-16 sm:py-24">
        <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
          <div className="mb-12 text-center sm:mb-16">
            <p className="label-caps text-caramel">Escolha do Livreiro</p>
            <h2 className="mt-3 font-display text-[2.5rem] font-normal leading-tight tracking-[-0.01em] text-forest sm:text-[3.25rem]">
              Recomendação da Casa
            </h2>
          </div>
          <div className="grid gap-10 rounded-md border border-line bg-cream-soft p-6 sm:p-10 lg:grid-cols-12 lg:p-14">
            <div className="lg:col-span-5">
              <div className="mx-auto aspect-[3/4] w-full max-w-[320px] animate-pulse rounded-md bg-line/60" />
            </div>
            <div className="space-y-4 lg:col-span-7">
              <div className="h-4 w-40 animate-pulse rounded-sm bg-line/60" />
              <div className="h-10 w-3/4 animate-pulse rounded-sm bg-line/60" />
              <div className="h-4 w-1/3 animate-pulse rounded-sm bg-line/50" />
              <div className="h-28 w-full animate-pulse rounded-md bg-line/40" />
              <div className="h-10 w-48 animate-pulse rounded-sm bg-line/60" />
            </div>
          </div>
        </div>
      </section>
    )
  }

  const produto = recomendacao?.produto

  // Sem produto nenhum no catálogo: seção some de forma limpa.
  if (!produto) {
    return (
      <section id="recomendacao" className="bg-cream-deep py-16 sm:py-24">
        <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
          <div className="rounded-md border border-dashed border-line-strong bg-cream-soft/60 px-6 py-16 text-center">
            <p className="label-caps text-caramel">Escolha do Livreiro</p>
            <p className="mt-3 font-display text-2xl text-coffee">
              Sem recomendação no momento
            </p>
            <p className="mt-2 font-body text-sm text-coffee-soft">
              Assim que houver títulos no catálogo, a escolha da casa aparece
              aqui.
            </p>
          </div>
        </div>
      </section>
    )
  }

  const nota = recomendacao?.notaMedia ?? 0
  const totalAvaliacoes = recomendacao?.avaliacoes?.length ?? 0

  /** Adiciona o livro recomendado à sacola. */
  const adicionarASacola = async () => {
    try {
      await adicionar({
        id: produto.id,
        titulo: produto.titulo,
        autor: produto.autor,
        preco: produto.precoFinal,
        imagem: produto.imagem,
        stockQty: produto.estoque,
      })
      setFeedback({ tipo: 'sucesso', texto: 'Adicionado à sacola.' })
    } catch {
      setFeedback({
        tipo: 'erro',
        texto: 'Não foi possível adicionar à sacola.',
      })
    }
  }

  return (
    <section id="recomendacao" className="bg-cream-deep py-16 sm:py-24">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
        {/* Cabeçalho da seção */}
        <div className="mb-12 text-center sm:mb-16">
          <p className="label-caps text-caramel">Escolha do Livreiro</p>
          <h2 className="mt-3 font-display text-[2.5rem] font-normal leading-tight tracking-[-0.01em] text-forest sm:text-[3.25rem]">
            Recomendação da Casa
          </h2>
          <p className="mx-auto mt-3 max-w-[34rem] font-body text-[0.98rem] font-normal leading-relaxed text-coffee-soft sm:text-[1.05rem]">
            Todo mês, nossa equipe seleciona uma obra especial que tocou nossos corações e merece ser lida com calma.
          </p>
        </div>

        {/* Card Principal da Recomendação */}
        <div className="relative overflow-hidden rounded-md border border-line bg-cream-soft shadow-[0_20px_50px_-20px_rgba(75,54,33,0.12)]">
          {/* Fundo decorativo sutil com a pena do Papiro */}
          <div className="pointer-events-none absolute -right-8 -top-8 text-forest/5 lg:text-forest/[0.04]">
            <Quill width={260} />
          </div>

          <div className="grid gap-10 p-6 sm:p-10 lg:grid-cols-12 lg:gap-14 lg:p-14">
            {/* Coluna da Capa do Livro (5 colunas no desktop) */}
            <div className="flex flex-col items-center justify-center lg:col-span-5">
              <div className="group relative w-full max-w-[320px]">
                {/* Selo de Desconto */}
                {produto.desconto && (
                  <div className="absolute -left-3 -top-3 z-20 rounded-sm bg-forest px-3.5 py-1.5 font-body text-[0.72rem] font-bold uppercase tracking-[0.2em] text-cream shadow-md">
                    {produto.desconto} OFF
                  </div>
                )}

                {/* Moldura da Capa */}
                <div
                  onClick={() => onAbrirLivro?.(produto.id)}
                  className="cursor-pointer overflow-hidden rounded-md bg-forest/10 p-3 shadow-2xl transition-transform duration-700 ease-[var(--ease-cozy)] group-hover:scale-[1.02]"
                >
                  <div className="relative aspect-[3/4] overflow-hidden rounded-sm bg-coffee">
                    {produto.imagem ? (
                      <img
                        src={produto.imagem}
                        alt={`Capa de ${produto.titulo}`}
                        className="h-full w-full object-cover transition-transform duration-700 ease-[var(--ease-cozy)] group-hover:scale-105"
                        loading="lazy"
                      />
                    ) : (
                      <div className="grid h-full w-full place-items-center font-body text-xs uppercase tracking-widest text-cream/60">
                        Sem capa
                      </div>
                    )}
                    <div className="absolute inset-0 bg-forest/10 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
                  </div>
                </div>
              </div>
            </div>

            {/* Coluna da Resenha e Detalhes (7 colunas no desktop) */}
            <div className="flex flex-col justify-between lg:col-span-7">
              <div>
                {/* Gênero e Avaliação */}
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span className="font-body text-[0.78rem] font-semibold uppercase tracking-[0.16em] text-caramel-dark">
                    {produto.autor}
                  </span>
                  <div className="flex items-center gap-2">
                    <Estrelas nota={nota} />
                    <span className="font-body text-xs font-bold text-coffee">
                      {nota > 0
                        ? `${nota} / 5.0`
                        : 'Sem avaliações'}
                    </span>
                    {totalAvaliacoes > 0 && (
                      <span className="font-body text-[0.72rem] text-coffee-faint">
                        ({totalAvaliacoes})
                      </span>
                    )}
                  </div>
                </div>

                {/* Título e Autor */}
                <h3 className="mt-3.5 font-display text-[2.2rem] font-normal leading-tight text-coffee sm:text-[2.8rem]">
                  <a
                    href="#"
                    onClick={(e) => {
                      e.preventDefault()
                      onAbrirLivro?.(produto.id)
                    }}
                    className="transition-colors duration-300 hover:text-gold"
                  >
                    {produto.titulo}
                  </a>
                </h3>

                {/* Sinopse real (quando o produto tiver) */}
                {produto.sinopse && (
                  <div className="mt-6 border-l-2 border-gold pl-4 font-display text-lg italic text-forest/90 sm:text-xl">
                    {produto.sinopse}
                  </div>
                )}

                {/* Descrição real do produto */}
                {produto.descricao && (
                  <div className="mt-6 rounded-md bg-cream-deep/60 p-5 sm:p-7">
                    <p className="font-body text-[0.75rem] font-semibold uppercase tracking-[0.24em] text-gold-dark">
                      Sobre esta edição
                    </p>
                    <p className="mt-3 font-body text-[0.95rem] font-normal leading-relaxed text-coffee sm:text-[1.02rem]">
                      {produto.descricao}
                    </p>
                  </div>
                )}
              </div>

              {/* Bloco de Preço e Ações de Compra */}
              <div className="mt-8 flex flex-col gap-4 border-t border-line pt-6 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="flex items-baseline gap-3">
                    <span className="font-display text-[2.2rem] font-semibold leading-none text-forest">
                      {formatarPreco(produto.precoFinal)}
                    </span>
                    {produto.precoOriginal != null && (
                      <span className="font-body text-sm font-normal text-coffee-faint line-through">
                        {formatarPreco(produto.precoOriginal)}
                      </span>
                    )}
                  </div>
                  <span className="mt-1 block font-body text-[0.76rem] font-normal text-coffee-faint">
                    {produto.estoque > 0
                      ? `${produto.estoque} em estoque`
                      : 'Produto esgotado'}
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={adicionarASacola}
                    disabled={produto.estoque <= 0}
                    className="inline-flex items-center justify-center gap-2.5 rounded-sm bg-forest px-7 py-4 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft shadow-md transition-all duration-300 hover:bg-forest-soft hover:shadow-lg disabled:cursor-not-allowed disabled:bg-line-strong disabled:opacity-70 focus-visible:outline focus-visible:outline-2 focus-visible:outline-forest"
                  >
                    <BagIcon className="h-4 w-4" />
                    <span>
                      {produto.estoque > 0
                        ? 'Adicionar à sacola'
                        : 'Esgotado'}
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => onAbrirLivro?.(produto.id)}
                    className="group inline-flex items-center justify-center rounded-sm border border-line-strong bg-cream-soft px-4 py-4 font-body text-xs uppercase tracking-wider text-coffee transition-colors duration-300 hover:border-gold hover:text-gold"
                    aria-label="Ver mais detalhes do livro"
                  >
                    <ArrowRightIcon className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
                  </button>
                </div>
              </div>

              {feedback && (
                <p
                  className={`mt-3 font-body text-xs ${
                    feedback.tipo === 'sucesso'
                      ? 'text-forest'
                      : 'text-caramel-dark'
                  }`}
                >
                  {feedback.texto}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
