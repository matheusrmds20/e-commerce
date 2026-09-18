import { useCallback, useEffect, useState } from 'react'
import BookCard from '../components/BookCard'
import Migalhas from '../components/Migalhas'
import Paginacao from '../components/Paginacao'
import { formatarPreco } from '../api/adapters'
import { produtoParaCard } from '../api/home'
import productService from '../api/products'
import categoryService from '../api/categories'

/** Itens por página. Casa com o `le=100` do backend e mantém a grade 4-col. */
const ITENS_POR_PAGINA = 12

/**
 * Acervo — catálogo completo com paginação e filtro por categoria.
 *
 * Fluxo:
 * 1. `GET /products/paginated?page&per_page&category_id` devolve
 *    `{ data, meta }`. A paginação **e** o filtro acontecem no banco, então
 *    `meta.total` reflete a categoria selecionada — não o catálogo inteiro.
 * 2. As categorias vêm de `GET /categories/list` e alimentam o filtro.
 * 3. Trocar de categoria reseta para a página 1: manter a página atual ao
 *    filtrar poderia cair em um intervalo vazio (ex.: estava na página 3, a
 *    categoria só tem 1 página).
 *
 * O catálogo é buscado no servidor a cada mudança de página **ou** de filtro;
 * as categorias ficam em cache no estado (buscadas uma única vez).
 */
export default function Acervo({ onAbrirLivro }) {
  const [produtos, setProdutos] = useState([])
  const [meta, setMeta] = useState(null)
  const [categorias, setCategorias] = useState([])
  // `null` = "Todas as categorias". Guardamos o id, não o nome.
  const [categoriaId, setCategoriaId] = useState(null)

  const [pagina, setPagina] = useState(1)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState(null)

  /** Busca uma página do catálogo, opcionalmente filtrada por categoria. */
  const carregarProdutos = useCallback(async (alvo, catId) => {
    setCarregando(true)
    setErro(null)
    try {
      const resp = await productService.listarPaginado({
        page: alvo,
        perPage: ITENS_POR_PAGINA,
        categoryId: catId ?? undefined,
      })

      const metaResp = resp?.meta ?? null

      // Guarda contra página fora do intervalo: se o filtro reduzir o total
      // (ou o usuário chegar por link antigo), o backend responde 200 com
      // `data: []` e um `page` maior que `total_pages`. Voltamos para a última
      // página válida em vez de exibir "página 9 de 3".
      if (metaResp && metaResp.total_pages > 0 && alvo > metaResp.total_pages) {
        setPagina(metaResp.total_pages)
        return
      }

      setProdutos((resp?.data ?? []).map(produtoParaCard))
      setMeta(metaResp)
    } catch (error) {
      setErro(error)
      setProdutos([])
      setMeta(null)
    } finally {
      setCarregando(false)
    }
  }, [])

  // Categorias: buscadas uma vez. Falha aqui não derruba a listagem.
  useEffect(() => {
    let ativo = true
    categoryService
      .listar()
      .then((lista) => {
        if (ativo) setCategorias(lista ?? [])
      })
      .catch(() => {
        if (ativo) setCategorias([])
      })
    return () => {
      ativo = false
    }
  }, [])

  // Recarrega quando muda a página ou o filtro.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    carregarProdutos(pagina, categoriaId)
  }, [pagina, categoriaId, carregarProdutos])

  /** Troca de página e volta ao topo da listagem. */
  const trocarPagina = (destino) => {
    setPagina(destino)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  /**
   * Aplica um filtro de categoria. Sempre volta para a página 1, porque o
   * total de páginas muda junto com o filtro.
   */
  const filtrarPor = (id) => {
    if (id === categoriaId) return
    setCategoriaId(id)
    setPagina(1)
  }

  const totalPaginas = meta?.total_pages ?? 0
  const totalItens = meta?.total ?? 0
  const filtrando = categoriaId != null
  const nomeDoFiltro =
    categorias.find((c) => c.id === categoriaId)?.name ?? ''

  return (
    <main className="bg-cream-deep">
      {/* Cabeçalho editorial */}
      <section className="border-b border-line bg-cream-soft">
        <div className="mx-auto max-w-[1400px] px-5 py-10 sm:px-8 sm:py-14">
          <Migalhas
            itens={[{ rotulo: 'Início' }, { rotulo: 'Acervo' }]}
          />

          <p className="label-caps mt-6 text-caramel">Catálogo completo</p>
          <h1 className="mt-3 font-display text-[2.5rem] font-normal leading-tight tracking-[-0.01em] text-forest sm:text-[3.25rem]">
            O Acervo
          </h1>
          <p className="mt-3 max-w-[38rem] font-body text-[0.98rem] font-normal leading-relaxed text-coffee-soft sm:text-[1.05rem]">
            Todos os títulos disponíveis na livraria. Percorra com calma — aqui
            nada tem pressa.
          </p>
        </div>
      </section>

      <section className="mx-auto max-w-[1400px] px-5 py-12 sm:px-8 sm:py-16">
        {/* Barra de estado + filtros */}
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-body text-[0.85rem] text-coffee-soft">
            {carregando
              ? 'Carregando títulos…'
              : totalItens > 0
                ? `${totalItens} ${totalItens === 1 ? 'título' : 'títulos'}${
                    filtrando ? ` em ${nomeDoFiltro}` : ' no acervo'
                  }`
                : filtrando
                  ? `Nenhum título em ${nomeDoFiltro}`
                  : 'Nenhum título no acervo'}
            {meta && totalPaginas > 1 && !carregando && (
              <span className="text-coffee-faint">
                {' '}
                — página {meta.page} de {totalPaginas}
              </span>
            )}
          </p>

          {categorias.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => filtrarPor(null)}
                className={`rounded-sm px-4 py-2 font-body text-[0.72rem] font-semibold uppercase tracking-wider transition-all duration-300 ${
                  !filtrando
                    ? 'bg-forest text-cream-soft shadow-sm'
                    : 'border border-line-strong bg-cream-soft text-coffee-soft hover:border-forest hover:text-forest'
                }`}
              >
                Todas
              </button>

              {categorias.map((cat) => {
                const ativo = categoriaId === cat.id
                return (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() => filtrarPor(cat.id)}
                    className={`rounded-sm px-4 py-2 font-body text-[0.72rem] font-semibold uppercase tracking-wider transition-all duration-300 ${
                      ativo
                        ? 'bg-forest text-cream-soft shadow-sm'
                        : 'border border-line-strong bg-cream-soft text-coffee-soft hover:border-forest hover:text-forest'
                    }`}
                  >
                    {cat.name}
                  </button>
                )
              })}
            </div>
          )}
        </div>

        {/* Grade */}
        <div className="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {carregando &&
            Array.from({ length: ITENS_POR_PAGINA }).map((_, i) => (
              <div key={`skeleton-${i}`} className="flex flex-col">
                <div className="aspect-[3/4] animate-pulse rounded-md bg-line/60" />
                <div className="mt-5 h-6 w-4/5 animate-pulse rounded-sm bg-line/60" />
                <div className="mt-2 h-3 w-2/5 animate-pulse rounded-sm bg-line/50" />
                <div className="mt-4 h-5 w-1/3 animate-pulse rounded-sm bg-line/60" />
              </div>
            ))}

          {!carregando &&
            produtos.map((book) => (
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
                badge={book.destaque ? 'Curadoria' : null}
                onAbrir={onAbrirLivro}
              />
            ))}
        </div>

        {/* Erro */}
        {erro && !carregando && (
          <div className="mt-12 rounded-md border border-dashed border-line-strong bg-cream-soft/60 px-6 py-16 text-center">
            <p className="font-display text-2xl text-coffee">
              Não conseguimos carregar o acervo
            </p>
            <p className="mt-2 font-body text-sm text-coffee-soft">
              {erro.message ?? 'Verifique sua conexão e tente novamente.'}
            </p>
            <button
              type="button"
              onClick={() => carregarProdutos(pagina, categoriaId)}
              className="mt-6 rounded-sm bg-forest px-6 py-3 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft transition-colors hover:bg-forest-soft"
            >
              Tentar de novo
            </button>
          </div>
        )}

        {/* Vazio */}
        {!carregando && !erro && produtos.length === 0 && (
          <div className="mt-12 rounded-md border border-dashed border-line-strong bg-cream-soft/60 px-6 py-16 text-center">
            <p className="font-display text-2xl text-coffee">
              {filtrando
                ? `Nenhum título em ${nomeDoFiltro}`
                : 'O acervo ainda está vazio'}
            </p>
            <p className="mt-2 font-body text-sm text-coffee-soft">
              {filtrando
                ? 'Escolha outra categoria ou veja o acervo completo.'
                : 'Assim que a curadoria publicar títulos, eles aparecem aqui.'}
            </p>
            {filtrando && (
              <button
                type="button"
                onClick={() => filtrarPor(null)}
                className="mt-6 rounded-sm border border-forest px-6 py-3 font-body text-xs font-semibold uppercase tracking-[0.2em] text-forest transition-colors hover:bg-forest hover:text-cream-soft"
              >
                Ver acervo completo
              </button>
            )}
          </div>
        )}

        <Paginacao
          page={meta?.page ?? pagina}
          totalPages={totalPaginas}
          onChange={trocarPagina}
          carregando={carregando}
        />
      </section>
    </main>
  )
}
