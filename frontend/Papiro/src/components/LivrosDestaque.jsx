import { useMemo, useState } from 'react'
import BookCard from './BookCard'
import { ArrowRightIcon } from './Icons'
import { formatarPreco } from '../api/adapters'

/**
 * LivrosDestaque — Seção de Livros em Destaque com filtros por categoria.
 *
 * Dados vêm da Home (`catalogo` = produtos ativos; `categorias` = categorias da
 * API, já normalizadas). Os filtros são montados dinamicamente a partir das
 * categorias que realmente possuem livros no catálogo, precedidos por "Todos".
 * Isso evita botões de filtro que não retornam resultado.
 *
 * O backend não expõe um conceito de "destaque"; a seção mostra os primeiros
 * itens do catálogo ativo (a ordem de `GET /products/list`).
 */
const LIMITE_DESTAQUES = 8

export default function LivrosDestaque({
  livros = [],
  categorias = [],
  carregando = false,
  onAbrirLivro,
}) {
  const [categoriaAtiva, setCategoriaAtiva] = useState('Todos')

  // Só categorias com ao menos um livro no catálogo viram filtro.
  const filtros = useMemo(() => {
    const idsComLivros = new Set(livros.map((l) => l.categoriaId))
    const nomes = categorias
      .filter((c) => idsComLivros.has(c.id))
      .map((c) => c.titulo)
    return ['Todos', ...nomes]
  }, [livros, categorias])

  // Garante que um filtro selecionado que sumiu do catálogo volte para "Todos".
  const filtroAtivo = filtros.includes(categoriaAtiva)
    ? categoriaAtiva
    : 'Todos'

  const nomeDaCategoria = useMemo(() => {
    const mapa = new Map(categorias.map((c) => [c.id, c.titulo]))
    return (id) => mapa.get(id) ?? ''
  }, [categorias])

  const livrosFiltrados = useMemo(() => {
    const base =
      filtroAtivo === 'Todos'
        ? livros
        : livros.filter((l) => nomeDaCategoria(l.categoriaId) === filtroAtivo)
    return base.slice(0, LIMITE_DESTAQUES)
  }, [livros, filtroAtivo, nomeDaCategoria])

  return (
    <section id="destaques" className="bg-cream-deep py-16 sm:py-24">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
        {/* Cabeçalho da seção */}
        <div className="flex flex-col items-center text-center">
          <p className="label-caps text-caramel">Seleção da Editora</p>

          <h2 className="mt-3 font-display text-[2.5rem] font-normal leading-tight tracking-[-0.01em] text-forest sm:text-[3.25rem]">
            Livros em Destaque
          </h2>

          <p className="mt-4 max-w-[36rem] font-body text-[0.98rem] font-normal leading-relaxed text-coffee-soft sm:text-[1.05rem]">
            Obras cuidadosamente selecionadas pela nossa curadoria para inspirar, encantar e transformar seus momentos de leitura.
          </p>

          {/* Filtros de categoria (dinâmicos) */}
          {filtros.length > 1 && (
            <div className="mt-8 flex flex-wrap items-center justify-center gap-2 sm:gap-3">
              {filtros.map((cat) => {
                const ativo = filtroAtivo === cat
                return (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setCategoriaAtiva(cat)}
                    className={`rounded-sm px-5 py-2.5 font-body text-xs font-semibold tracking-wider uppercase transition-all duration-300 ${
                      ativo
                        ? 'bg-forest text-cream-soft shadow-sm'
                        : 'border border-line-strong bg-cream-soft text-coffee-soft hover:border-forest hover:text-forest'
                    }`}
                  >
                    {cat}
                  </button>
                )
              })}
            </div>
          )}
        </div>

        {/* Grade de Livros */}
        <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {carregando &&
            Array.from({ length: 4 }).map((_, i) => (
              <div key={`skeleton-${i}`} className="flex flex-col">
                <div className="aspect-[3/4] animate-pulse rounded-md bg-line/60" />
                <div className="mt-5 h-6 w-4/5 animate-pulse rounded-sm bg-line/60" />
                <div className="mt-2 h-3 w-2/5 animate-pulse rounded-sm bg-line/50" />
                <div className="mt-4 h-5 w-1/3 animate-pulse rounded-sm bg-line/60" />
              </div>
            ))}

          {!carregando &&
            livrosFiltrados.map((book) => (
              <BookCard
                key={book.id}
                id={book.id}
                title={book.titulo}
                author={book.autor}
                price={formatarPreco(book.precoFinal)}
                oldPrice={
                  book.precoOriginal != null
                    ? formatarPreco(book.precoOriginal)
                    : null
                }
                image={book.imagem}
                tint="bg-coffee"
                onAbrir={onAbrirLivro}
              />
            ))}
        </div>

        {/* Estado vazio */}
        {!carregando && livrosFiltrados.length === 0 && (
          <div className="mt-12 rounded-md border border-dashed border-line-strong bg-cream-soft/60 px-6 py-16 text-center">
            <p className="font-display text-2xl text-coffee">
              {filtroAtivo === 'Todos'
                ? 'Ainda não há livros no catálogo'
                : 'Nenhum livro nesta categoria'}
            </p>
            <p className="mt-2 font-body text-sm text-coffee-soft">
              {filtroAtivo === 'Todos'
                ? 'Assim que a curadoria publicar novos títulos, eles aparecem aqui.'
                : 'Escolha outra categoria para continuar explorando.'}
            </p>
            {filtroAtivo !== 'Todos' && (
              <button
                type="button"
                onClick={() => setCategoriaAtiva('Todos')}
                className="mt-6 rounded-sm border border-forest px-6 py-3 font-body text-xs font-semibold uppercase tracking-[0.2em] text-forest transition-colors hover:bg-forest hover:text-cream-soft"
              >
                Ver todos
              </button>
            )}
          </div>
        )}

        {/* Rodapé da seção com botão de ação */}
        {!carregando && livros.length > 0 && (
          <div className="mt-14 text-center">
            <button
              type="button"
              onClick={() => onAbrirLivro?.(livros[0]?.id)}
              className="group inline-flex items-center gap-3 rounded-sm border border-forest bg-forest px-8 py-4 font-body text-xs font-semibold uppercase tracking-[0.22em] text-cream-soft shadow-md transition-all duration-300 hover:bg-forest-soft hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
            >
              <span>Explorar todo o acervo</span>
              <ArrowRightIcon className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
            </button>
          </div>
        )}
      </div>
    </section>
  )
}
