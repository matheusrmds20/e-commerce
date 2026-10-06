import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import BookCard from '../components/BookCard'
import Migalhas from '../components/Migalhas'
import Paginacao from '../components/Paginacao'
import { formatarPreco } from '../api/adapters'
import { produtoParaCard } from '../api/home'
import productService from '../api/products'
import categoryService from '../api/categories'

const ITENS_POR_PAGINA = 12

/**
 * MaisVendidos — Página editorial dos livros mais vendidos e aclamados da Papiro.
 * 
 * Segue a identidade visual e editorial das páginas da livraria.
 * Se a curadoria do backend não tiver marcado bestsellers, aplica fallback
 * inteligente para exibir os títulos mais relevantes do catálogo, garantindo
 * que a página nunca fique vazia.
 */
export default function MaisVendidos({ onAbrirLivro, onExplorarAcervo, onVoltarHome }) {
  const [produtos, setProdutos] = useState([])
  const [categorias, setCategorias] = useState([])
  const [categoriaId, setCategoriaId] = useState(null)
  const [termoBusca, setTermoBusca] = useState('')
  const [pagina, setPagina] = useState(1)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState(null)

  // Carrega categorias uma única vez
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

  // Carrega mais vendidos (com fallback garantido se a lista vier vazia)
  const carregarMaisVendidos = useCallback(async () => {
    setCarregando(true)
    setErro(null)
    try {
      // 1. Tenta buscar da rota de bestsellers
      let lista = await productService.listarMaisVendidos(40).catch(() => [])

      // 2. Se vazio, busca catálogo ativo e filtra/prioriza destaques para não ficar vazio
      if (!lista || lista.length === 0) {
        const catalogo = await productService.listarPorAtivo(true).catch(() => [])
        if (catalogo && catalogo.length > 0) {
          // Filtra os que têm is_bestseller ou is_featured ou pega os primeiros
          const marcados = catalogo.filter((p) => p.is_bestseller)
          lista = marcados.length > 0 ? marcados : catalogo.slice(0, 16)
        }
      }

      setProdutos((lista ?? []).map(produtoParaCard))
    } catch (error) {
      setErro(error)
      setProdutos([])
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    carregarMaisVendidos()
  }, [carregarMaisVendidos])

  // Filtragem local por categoria e busca
  const produtosFiltrados = useMemo(() => {
    let filtrados = [...produtos]

    if (categoriaId != null) {
      filtrados = filtrados.filter((p) => p.categoriaId === categoriaId)
    }

    if (termoBusca.trim()) {
      const q = termoBusca.trim().toLowerCase()
      filtrados = filtrados.filter(
        (p) =>
          p.titulo?.toLowerCase().includes(q) ||
          p.autor?.toLowerCase().includes(q) ||
          p.descricao?.toLowerCase().includes(q),
      )
    }

    return filtrados
  }, [produtos, categoriaId, termoBusca])

  // Paginação sobre os itens filtrados
  const totalItens = produtosFiltrados.length
  const totalPaginas = Math.ceil(totalItens / ITENS_POR_PAGINA)
  const itensPaginados = useMemo(() => {
    const inicio = (pagina - 1) * ITENS_POR_PAGINA
    return produtosFiltrados.slice(inicio, inicio + ITENS_POR_PAGINA)
  }, [produtosFiltrados, pagina])

  const filtrarPor = (id) => {
    setCategoriaId(id)
    setPagina(1)
  }

  const trocarPagina = (destino) => {
    setPagina(destino)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const nomeDoFiltro =
    categorias.find((c) => c.id === categoriaId)?.name ?? ''

  return (
    <main className="bg-cream-deep">
      {/* Cabeçalho Editorial */}
      <section className="border-b border-line bg-cream-soft">
        <div className="mx-auto max-w-[1400px] px-5 py-10 sm:px-8 sm:py-14">
          <Migalhas
            itens={[
              { rotulo: 'Início', onClick: onVoltarHome },
              { rotulo: 'Mais Vendidos' },
            ]}
          />

          <p className="label-caps mt-6 text-caramel">Os preferidos dos leitores</p>
          <h1 className="mt-3 font-display text-[2.5rem] font-normal leading-tight tracking-[-0.01em] text-forest sm:text-[3.25rem]">
            Mais Vendidos
          </h1>
          <p className="mt-3 max-w-[38rem] font-body text-[0.98rem] font-normal leading-relaxed text-coffee-soft sm:text-[1.05rem]">
            As obras mais lidas, celebradas e procuradas na Papiro. Seleção de
            leituras fundamentais que conquistaram nossa comunidade de leitores.
          </p>
        </div>
      </section>

      {/* Conteúdo Principal */}
      <section className="mx-auto max-w-[1400px] px-5 py-12 sm:px-8 sm:py-16">
        {/* Barra de Busca e Filtros */}
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative w-full max-w-md">
            <input
              type="search"
              value={termoBusca}
              onChange={(e) => {
                setTermoBusca(e.target.value)
                setPagina(1)
              }}
              placeholder="Buscar entre os mais vendidos…"
              aria-label="Buscar entre os mais vendidos"
              className="w-full rounded-sm border border-line-strong bg-cream-soft px-4 py-2.5 pr-10 font-body text-[0.9rem] text-coffee placeholder:text-coffee-faint focus:border-forest focus:outline-none"
            />
            {termoBusca && (
              <button
                type="button"
                onClick={() => {
                  setTermoBusca('')
                  setPagina(1)
                }}
                aria-label="Limpar busca"
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 font-body text-xl leading-none text-coffee-soft transition-colors hover:text-forest"
              >
                ×
              </button>
            )}
          </div>

          {categorias.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => filtrarPor(null)}
                className={`rounded-sm px-4 py-2 font-body text-[0.72rem] font-semibold uppercase tracking-wider transition-all duration-300 ${
                  categoriaId === null
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

        {/* Informação de contagem */}
        <div className="mt-6 flex items-center justify-between">
          <p className="font-body text-[0.85rem] text-coffee-soft">
            {carregando
              ? 'Carregando os mais vendidos…'
              : totalItens > 0
                ? `${totalItens} ${totalItens === 1 ? 'título' : 'títulos'}${
                    categoriaId != null ? ` em ${nomeDoFiltro}` : ' em destaque'
                  }${termoBusca ? ` para “${termoBusca}”` : ''}`
                : termoBusca
                  ? `Nenhum título encontrado para “${termoBusca}”`
                  : categoriaId != null
                    ? `Nenhum título mais vendido em ${nomeDoFiltro}`
                    : 'Nenhum título encontrado'}
          </p>
        </div>

        {/* Grade de Livros */}
        <div className="mt-8 grid gap-8 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
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
            itensPaginados.map((book, idx) => {
              const posicao = (pagina - 1) * ITENS_POR_PAGINA + idx + 1
              return (
                <div key={book.id} className="relative group">
                  <BookCard
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
                    badge={`#${posicao} Mais Vendido`}
                    onAbrir={onAbrirLivro}
                  />
                </div>
              )
            })}
        </div>

        {/* Estado de Erro */}
        {erro && !carregando && (
          <div className="mt-12 rounded-md border border-dashed border-line-strong bg-cream-soft/60 px-6 py-16 text-center">
            <p className="font-display text-2xl text-coffee">
              Não conseguimos carregar a lista de mais vendidos
            </p>
            <p className="mt-2 font-body text-sm text-coffee-soft">
              {erro.message ?? 'Verifique sua conexão e tente novamente.'}
            </p>
            <button
              type="button"
              onClick={carregarMaisVendidos}
              className="mt-6 rounded-sm bg-forest px-6 py-3 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft transition-colors hover:bg-forest-soft"
            >
              Tentar novamente
            </button>
          </div>
        )}

        {/* Estado Vazio */}
        {!carregando && !erro && totalItens === 0 && (
          <div className="mt-12 rounded-md border border-dashed border-line-strong bg-cream-soft/60 px-6 py-16 text-center">
            <p className="font-display text-2xl text-coffee">
              {termoBusca
                ? `Nenhum título para “${termoBusca}”`
                : categoriaId != null
                  ? `Nenhum título em ${nomeDoFiltro}`
                  : 'Nenhum título mais vendido no momento'}
            </p>
            <p className="mt-2 font-body text-sm text-coffee-soft">
              {termoBusca
                ? 'Tente outro termo ou limpe a busca.'
                : 'Explore nosso acervo completo para descobrir outras leituras memoráveis.'}
            </p>
            {onExplorarAcervo && (
              <button
                type="button"
                onClick={onExplorarAcervo}
                className="mt-6 rounded-sm border border-forest px-6 py-3 font-body text-xs font-semibold uppercase tracking-[0.2em] text-forest transition-colors hover:bg-forest hover:text-cream-soft"
              >
                Explorar Acervo Completo
              </button>
            )}
          </div>
        )}

        {/* Paginação */}
        {totalPaginas > 1 && !carregando && (
          <Paginacao
            page={pagina}
            totalPages={totalPaginas}
            onChange={trocarPagina}
            carregando={carregando}
          />
        )}

        {/* Rodapé Editorial de Incentivo */}
        {!carregando && produtosFiltrados.length > 0 && onExplorarAcervo && (
          <div className="mt-20 rounded-sm border border-line bg-cream-soft p-8 text-center sm:p-12">
            <h2 className="font-display text-2xl text-coffee sm:text-3xl">
              À procura de outras descobertas?
            </h2>
            <p className="mx-auto mt-2.5 max-w-xl font-body text-sm text-coffee-soft">
              Nossa curadoria vai além dos best-sellers. Conheça obras raras, poesias e
              edições especiais disponíveis no acervo completo.
            </p>
            <button
              type="button"
              onClick={onExplorarAcervo}
              className="mt-6 inline-block rounded-sm bg-forest px-8 py-3.5 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft transition-colors duration-300 hover:bg-forest-soft shadow-sm"
            >
              Ver Todo o Acervo
            </button>
          </div>
        )}
      </section>
    </main>
  )
}
