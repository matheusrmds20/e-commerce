import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import BookCard from '../components/BookCard'
import Migalhas from '../components/Migalhas'
import Paginacao from '../components/Paginacao'
import { formatarPreco } from '../api/adapters'
import { produtoParaCard } from '../api/home'
import productService from '../api/products'
import categoryService from '../api/categories'


const ITENS_POR_PAGINA = 12


export default function Acervo() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()


  const termoAtivo = searchParams.get('termo') ?? ''
  const busca = termoAtivo.trim() ? termoAtivo.trim() : null
  const categoriaRaw = searchParams.get('categoria')
  const categoriaId =
    categoriaRaw && /^\d+$/.test(categoriaRaw) ? Number(categoriaRaw) : null
  const pagina = Number(searchParams.get('page')) || 1

  const [categorias, setCategorias] = useState([])

  const [termoBusca, setTermoBusca] = useState(termoAtivo)

  const [produtos, setProdutos] = useState([])
  const [meta, setMeta] = useState(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState(null)
  const timerBusca = useRef(null)


  const atualizarUrl = useCallback(
    (mudancas) => {
      const params = new URLSearchParams(searchParams)
      Object.entries(mudancas).forEach(([chave, valor]) => {
        if (valor === null || valor === undefined || valor === '') {
          params.delete(chave)
        } else {
          params.set(chave, String(valor))
        }
      })
      // Saída estável: pagina, termo, categoria.
      const ordenado = new URLSearchParams()
      ;['page', 'termo', 'categoria'].forEach((chave) => {
        if (params.has(chave)) ordenado.set(chave, params.get(chave))
      })
      setSearchParams(ordenado, { replace: true })
    },
    [searchParams, setSearchParams],
  )


  const carregarProdutos = useCallback(async (alvo, catId, buscaAtiva) => {
    setCarregando(true)
    setErro(null)
    try {
      const resp = await productService.listarPaginado({
        page: alvo,
        perPage: ITENS_POR_PAGINA,
        categoryId: catId ?? undefined,
        search: buscaAtiva ?? undefined,
      })

      const metaResp = resp?.meta ?? null


      if (metaResp && metaResp.total_pages > 0 && alvo > metaResp.total_pages) {
        const params = new URLSearchParams(searchParams)
        params.set('page', String(metaResp.total_pages))
        setSearchParams(params, { replace: true })
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
  }, [searchParams, setSearchParams])

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

  // Recarrega quando muda a página, o filtro ou o termo de busca (tudo na URL).
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    carregarProdutos(pagina, categoriaId, busca)
  }, [pagina, categoriaId, busca, carregarProdutos])

  // Mantém a caixa de busca alinhada ao termo da URL (ex.: busca vinda da Navbar).
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (termoAtivo !== termoBusca) setTermoBusca(termoAtivo)
  }, [termoAtivo, termoBusca])

  // Debounce do termo digitado: comita a busca 300ms após a última tecla.
  useEffect(() => {
    timerBusca.current = setTimeout(() => {
      if (termoBusca.trim() !== termoAtivo) atualizarUrl({ termo: termoBusca, page: null })
    }, 300)
    return () => clearTimeout(timerBusca.current)
  }, [termoBusca, termoAtivo, atualizarUrl])

  /** Comita o termo na hora (Enter) e cancela o debounce pendente. */
  const comitarBusca = () => {
    clearTimeout(timerBusca.current)
    if (termoBusca.trim() !== termoAtivo) {
      atualizarUrl({ termo: termoBusca, page: null })
    }
  }

  /** Limpa a busca: volta a exibir o catálogo inteiro. */
  const limparBusca = () => {
    clearTimeout(timerBusca.current)
    setTermoBusca('')
    atualizarUrl({ termo: null, page: null })
  }

  /** Troca de página e volta ao topo da listagem. */
  const trocarPagina = (destino) => {
    if (destino !== pagina) atualizarUrl({ page: destino })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  /**
   * Aplica um filtro de categoria. Sempre volta para a página 1, porque o
   * total de páginas muda junto com o filtro.
   */
  const filtrarPor = (id) => {
    if (id === categoriaId) return
    atualizarUrl({ categoria: id ?? null, page: null })
  }

  const totalPaginas = meta?.total_pages ?? 0
  const totalItens = meta?.total ?? 0
  const filtrando = categoriaId != null
  const buscando = busca != null
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
        {/* Busca livre: comita no debounce ou no Enter. */}
        <form
          role="search"
          onSubmit={(e) => {
            e.preventDefault()
            comitarBusca()
          }}
        >
          <div className="relative w-full max-w-md">
            <input
              type="search"
              value={termoBusca}
              onChange={(e) => setTermoBusca(e.target.value)}
              placeholder="Buscar por título, autor ou ISBN…"
              aria-label="Buscar no acervo"
              className="w-full rounded-sm border border-line-strong bg-cream-soft px-4 py-2.5 pr-10 font-body text-[0.9rem] text-coffee placeholder:text-coffee-faint focus:border-forest focus:outline-none"
            />
            {termoBusca && (
              <button
                type="button"
                onClick={limparBusca}
                aria-label="Limpar busca"
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 font-body text-xl leading-none text-coffee-soft transition-colors hover:text-forest"
              >
                ×
              </button>
            )}
          </div>
        </form>

        {/* Barra de estado + filtros */}
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-body text-[0.85rem] text-coffee-soft">
            {carregando
              ? 'Carregando títulos…'
              : totalItens > 0
                ? `${totalItens} ${totalItens === 1 ? 'título' : 'títulos'}${' '}
                    ${filtrando ? ` em ${nomeDoFiltro}` : ' no acervo'}${buscando ? ` para “${busca}”` : ''}`
                : buscando
                  ? `Nenhum título para “${busca}”`
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
                onAbrir={(id) => navigate(`/livro/${id}`)}
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
              onClick={() => carregarProdutos(pagina, categoriaId, busca)}
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
              {buscando
                ? `Nenhum título para “${busca}”`
                : filtrando
                  ? `Nenhum título em ${nomeDoFiltro}`
                  : 'O acervo ainda está vazio'}
            </p>
            <p className="mt-2 font-body text-sm text-coffee-soft">
              {buscando
                ? 'Tente outro termo ou limpe a busca para ver o acervo completo.'
                : filtrando
                  ? 'Escolha outra categoria ou veja o acervo completo.'
                  : 'Assim que a curadoria publicar títulos, eles aparecem aqui.'}
            </p>
            {buscando && (
              <button
                type="button"
                onClick={limparBusca}
                className="mt-6 rounded-sm border border-forest px-6 py-3 font-body text-xs font-semibold uppercase tracking-[0.2em] text-forest transition-colors hover:bg-forest hover:text-cream-soft"
              >
                Limpar busca
              </button>
            )}
            {filtrando && !buscando && (
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