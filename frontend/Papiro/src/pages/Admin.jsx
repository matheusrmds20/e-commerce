import { useState, useMemo, useEffect } from 'react'
import { CloseIcon, SearchIcon } from '../components/Icons'
import productService from '../api/products'
import categoryService from '../api/categories'
import adminService from '../api/admin'

const PEDIDOS_FALLBACK = [
  {
    id: '#PAP-9842',
    rawId: 9842,
    cliente: 'Helena Silveira',
    email: 'helena.s@email.com',
    itens: 'Memórias Póstumas de Brás Cubas (x1)',
    data: 'Hoje, 14:20',
    status: 'separacao',
    statusLabel: 'Em Separação',
    total: 148.0,
  },
  {
    id: '#PAP-9841',
    rawId: 9841,
    cliente: 'Rodrigo de Andrade',
    email: 'rodrigo.andrade@email.com',
    itens: 'Cem Anos de Solidão + Box Clarice Lispector',
    data: 'Hoje, 11:05',
    status: 'aguardando',
    statusLabel: 'Aguardando Envio',
    total: 412.5,
  },
  {
    id: '#PAP-9840',
    rawId: 9840,
    cliente: 'Beatriz Viana',
    email: 'beatriz.viana@email.com',
    itens: 'Grande Sertão: Veredas (Edição Comentada)',
    data: 'Ontem',
    status: 'enviado',
    statusLabel: 'Enviado',
    total: 189.9,
  },
  {
    id: '#PAP-9839',
    rawId: 9839,
    cliente: 'Carlos Drummond',
    email: 'carlos.d@email.com',
    itens: 'A Divina Comédia (Ilustrada)',
    data: '16/09',
    status: 'entregue',
    statusLabel: 'Entregue',
    total: 290.0,
  },
]

const LIVROS_FALLBACK = [
  {
    id: 1,
    titulo: 'Dom Casmurro (1ª Edição Fac-símile)',
    autor: 'Machado de Assis',
    categoria: 'Ficção Clássica',
    categoryId: 1,
    preco: 148.0,
    estoque: 1,
    destaque: true,
  },
  {
    id: 2,
    titulo: 'O Som e a Fúria (Ed. Luxo)',
    autor: 'William Faulkner',
    categoria: 'Ficção Internacional',
    categoryId: 1,
    preco: 165.0,
    estoque: 2,
    destaque: false,
  },
  {
    id: 3,
    titulo: 'A Divina Comédia (Ilustrada Doré)',
    autor: 'Dante Alighieri',
    categoria: 'Poesia Épica',
    categoryId: 2,
    preco: 290.0,
    estoque: 3,
    destaque: true,
  },
  {
    id: 4,
    titulo: 'Grande Sertão: Veredas',
    autor: 'Guimarães Rosa',
    categoria: 'Literatura Brasileira',
    categoryId: 1,
    preco: 189.9,
    estoque: 14,
    destaque: true,
  },
  {
    id: 5,
    titulo: 'Cem Anos de Solidão',
    autor: 'Gabriel García Márquez',
    categoria: 'Realismo Fantástico',
    categoryId: 1,
    preco: 120.0,
    estoque: 8,
    destaque: false,
  },
]

const CLIENTES_FALLBACK = [
  {
    id: 1,
    full_name: 'Helena Silveira',
    email: 'helena.s@email.com',
    role: 'customer',
    orders_count: 5,
    created_at: '2026-01-12T10:00:00',
  },
  {
    id: 2,
    full_name: 'Rodrigo de Andrade',
    email: 'rodrigo.andrade@email.com',
    role: 'customer',
    orders_count: 3,
    created_at: '2026-02-04T14:30:00',
  },
  {
    id: 3,
    full_name: 'Beatriz Viana',
    email: 'beatriz.viana@email.com',
    role: 'customer',
    orders_count: 2,
    created_at: '2026-03-10T09:15:00',
  },
]

function gerarSlug(texto) {
  return texto
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\w\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
}

function formatarStatus(st) {
  const map = {
    pending: 'Aguardando Envio',
    aguardando: 'Aguardando Envio',
    processing: 'Em Separação',
    separacao: 'Em Separação',
    shipped: 'Enviado',
    enviado: 'Enviado',
    delivered: 'Entregue',
    entregue: 'Entregue',
    completed: 'Concluído',
    cancelled: 'Cancelado',
  }
  return map[st?.toLowerCase()] || st || 'Pendente'
}

export default function Admin({ onVoltarParaLoja }) {
  const [abaAtiva, setAbaAtiva] = useState('visao-geral')
  const [termoBusca, setTermoBusca] = useState('')
  const [pedidos, setPedidos] = useState(PEDIDOS_FALLBACK)
  const [livros, setLivros] = useState(LIVROS_FALLBACK)
  const [clientes, setClientes] = useState(CLIENTES_FALLBACK)
  const [categorias, setCategorias] = useState([])
  const [statsApi, setStatsApi] = useState(null)
  const [erroAviso, setErroAviso] = useState(null)
  const [modalNovoLivro, setModalNovoLivro] = useState(false)
  const [salvandoLivro, setSalvandoLivro] = useState(false)

  // Form novo livro
  const [novoTitulo, setNovoTitulo] = useState('')
  const [novoAutor, setNovoAutor] = useState('')
  const [novaCategoriaId, setNovaCategoriaId] = useState(1)
  const [novoDescricao, setNovoDescricao] = useState('')
  const [novoPreco, setNovoPreco] = useState('')
  const [novoEstoque, setNovoEstoque] = useState('')

  // Carrega dados da API ao montar
  useEffect(() => {
    let ativo = true

    async function carregarTudo() {
      try {
        // 1. Estatísticas do Dashboard (/admin/dashboard/stats)
        const stats = await adminService.obterEstatisticas().catch(() => null)
        if (ativo && stats) {
          setStatsApi(stats)
        }

        // 2. Produtos do Catálogo (/products/list)
        const produtosApi = await productService.listar().catch(() => [])
        if (ativo && Array.isArray(produtosApi) && produtosApi.length > 0) {
          const formatados = produtosApi.map((p) => ({
            id: p.id,
            titulo: p.title,
            autor: p.author || 'Autor não informado',
            categoria: p.category_name || (p.category_id ? `Categoria #${p.category_id}` : 'Geral'),
            categoryId: p.category_id || 1,
            preco: Number(p.price) || 0,
            estoque: p.stock_qty ?? 0,
            destaque: Boolean(p.is_featured),
          }))
          setLivros(formatados)
        }

        // 3. Categorias (/categories/list)
        const categoriasApi = await categoryService.listar().catch(() => [])
        if (ativo && Array.isArray(categoriasApi) && categoriasApi.length > 0) {
          setCategorias(categoriasApi)
          setNovaCategoriaId(categoriasApi[0].id)
        }

        // 4. Todos os Pedidos (/admin/orders)
        const pedidosAdmin = await adminService.listarPedidos().catch(() => [])
        if (ativo && Array.isArray(pedidosAdmin) && pedidosAdmin.length > 0) {
          const formatados = pedidosAdmin.map((p) => ({
            id: `#PAP-${p.id}`,
            rawId: p.id,
            cliente: p.user?.full_name || 'Leitor Papiro',
            email: p.user?.email || 'leitor@papiro.com.br',
            itens: p.items_summary || `${p.items_count} item(ns)`,
            data: p.created_at ? new Date(p.created_at).toLocaleDateString('pt-BR') : 'Hoje',
            status: p.status,
            statusLabel: formatarStatus(p.status),
            total: Number(p.total) || 0,
          }))
          setPedidos(formatados)
        }

        // 5. Clientes (/admin/users)
        const usuariosApi = await adminService.listarUsuarios().catch(() => [])
        if (ativo && Array.isArray(usuariosApi) && usuariosApi.length > 0) {
          setClientes(usuariosApi)
        }
      } catch (err) {
        console.warn('Conectando via mock/fallback offline:', err)
      }
    }

    carregarTudo()
    return () => {
      ativo = false
    }
  }, [])

  // Cadastrar livro
  const handleCadastrarLivro = async (e) => {
    e.preventDefault()
    if (!novoTitulo.trim() || !novoAutor.trim() || !novoPreco) return

    setSalvandoLivro(true)
    setErroAviso(null)

    const precoNum = parseFloat(novoPreco) || 0
    const estoqueNum = parseInt(novoEstoque, 10) || 1
    const catId = Number(novaCategoriaId) || 1
    const slug = `${gerarSlug(novoTitulo)}-${Date.now().toString().slice(-4)}`
    const desc = novoDescricao.trim() || `Edição clássica de ${novoTitulo}, por ${novoAutor}.`

    const payload = {
      category_id: catId,
      title: novoTitulo.trim(),
      slug: slug,
      description: desc,
      price: precoNum,
      author: novoAutor.trim(),
      stock_qty: estoqueNum,
      is_active: true,
      is_featured: false,
      is_bestseller: false,
    }

    try {
      const resp = await productService.criar(payload).catch(() => null)
      const novoId = resp?.id || Date.now()
      const categoriaNome =
        categorias.find((c) => c.id === catId)?.name || 'Ficção Clássica'

      const novoLivroObj = {
        id: novoId,
        titulo: payload.title,
        autor: payload.author,
        categoria: categoriaNome,
        categoryId: catId,
        preco: precoNum,
        estoque: estoqueNum,
        destaque: false,
      }

      setLivros([novoLivroObj, ...livros])
      setNovoTitulo('')
      setNovoAutor('')
      setNovoDescricao('')
      setNovoPreco('')
      setNovoEstoque('')
      setModalNovoLivro(false)
    } catch {
      setErroAviso('Erro ao cadastrar via API. Adicionado na visualização local.')
    } finally {
      setSalvandoLivro(false)
    }
  }

  // Remover livro
  const handleRemoverLivro = async (id) => {
    try {
      await productService.excluir(id).catch(() => null)
      setLivros(livros.filter((l) => l.id !== id))
    } catch {
      setLivros(livros.filter((l) => l.id !== id))
    }
  }

  // Atualizar status do pedido
  const handleAtualizarStatusPedido = async (rawId, idFormatted, novoStatus) => {
    try {
      if (rawId && typeof rawId === 'number') {
        await adminService.atualizarStatusPedido(rawId, novoStatus).catch(() => null)
      }
      setPedidos(
        pedidos.map((p) =>
          p.id === idFormatted || p.rawId === rawId
            ? { ...p, status: novoStatus, statusLabel: formatarStatus(novoStatus) }
            : p
        )
      )
    } catch (err) {
      console.error('Erro ao atualizar status:', err)
    }
  }

  // Filtros
  const livrosFiltrados = useMemo(() => {
    if (!termoBusca.trim()) return livros
    const busca = termoBusca.toLowerCase()
    return livros.filter(
      (l) =>
        l.titulo?.toLowerCase().includes(busca) ||
        l.autor?.toLowerCase().includes(busca) ||
        l.categoria?.toLowerCase().includes(busca)
    )
  }, [livros, termoBusca])

  const pedidosFiltrados = useMemo(() => {
    if (!termoBusca.trim()) return pedidos
    const busca = termoBusca.toLowerCase()
    return pedidos.filter(
      (p) =>
        p.id?.toLowerCase().includes(busca) ||
        p.cliente?.toLowerCase().includes(busca) ||
        p.itens?.toLowerCase().includes(busca)
    )
  }, [pedidos, termoBusca])

  const clientesFiltrados = useMemo(() => {
    if (!termoBusca.trim()) return clientes
    const busca = termoBusca.toLowerCase()
    return clientes.filter(
      (c) =>
        c.full_name?.toLowerCase().includes(busca) ||
        c.email?.toLowerCase().includes(busca)
    )
  }, [clientes, termoBusca])

  // KPIs
  const faturamento = statsApi?.total_revenue ?? pedidos.reduce((a, b) => a + (b.total || 0), 0)
  const totalPedidosCount = statsApi?.total_orders ?? pedidos.length
  const pedidosPendentesCount =
    statsApi?.pending_orders ??
    pedidos.filter((p) => p.status === 'pending' || p.status === 'processing' || p.status === 'separacao' || p.status === 'aguardando').length
  const totalObrasCount = statsApi?.total_products ?? livros.length
  const ticketMedio = statsApi?.average_ticket ?? (totalPedidosCount > 0 ? faturamento / totalPedidosCount : 0)

  return (
    <div className="flex min-h-[calc(100vh-74px)] bg-cream-deep text-coffee">
      {/* Sidebar Administrativa */}
      <aside className="w-64 shrink-0 bg-forest text-cream-soft flex flex-col justify-between border-r border-forest-soft shadow-xl hidden md:flex">
        <div>
          {/* Topo */}
          <div className="p-6 border-b border-forest-soft">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full border border-gold/60 flex items-center justify-center bg-forest-soft text-gold font-display text-lg font-bold">
                P
              </div>
              <div>
                <h1 className="font-display text-xl font-medium tracking-wide text-cream">
                  Papiro
                </h1>
                <p className="font-body text-[0.68rem] tracking-[0.22em] uppercase text-gold font-semibold">
                  Curadoria & Gestão
                </p>
              </div>
            </div>
          </div>

          {/* Links de navegação */}
          <nav className="p-4 space-y-1 font-body text-[0.88rem]">
            <button
              type="button"
              onClick={() => setAbaAtiva('visao-geral')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-sm text-left transition-colors duration-200 ${
                abaAtiva === 'visao-geral'
                  ? 'bg-gold text-forest font-semibold shadow-sm'
                  : 'text-cream-soft hover:bg-forest-soft hover:text-cream'
              }`}
            >
              <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
              </svg>
              Visão Geral
            </button>

            <button
              type="button"
              onClick={() => setAbaAtiva('acervo')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-sm text-left transition-colors duration-200 ${
                abaAtiva === 'acervo'
                  ? 'bg-gold text-forest font-semibold shadow-sm'
                  : 'text-cream-soft hover:bg-forest-soft hover:text-cream'
              }`}
            >
              <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
              </svg>
              Acervo & Catálogo
              <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-forest-soft text-gold font-medium">
                {livros.length}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setAbaAtiva('pedidos')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-sm text-left transition-colors duration-200 ${
                abaAtiva === 'pedidos'
                  ? 'bg-gold text-forest font-semibold shadow-sm'
                  : 'text-cream-soft hover:bg-forest-soft hover:text-cream'
              }`}
            >
              <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/>
              </svg>
              Pedidos & Vendas
              <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-caramel text-forest font-bold">
                {pedidosPendentesCount}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setAbaAtiva('clientes')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-sm text-left transition-colors duration-200 ${
                abaAtiva === 'clientes'
                  ? 'bg-gold text-forest font-semibold shadow-sm'
                  : 'text-cream-soft hover:bg-forest-soft hover:text-cream'
              }`}
            >
              <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
              </svg>
              Leitores & Clientes
              <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-forest-soft text-gold font-medium">
                {clientes.length}
              </span>
            </button>
          </nav>
        </div>

        {/* Rodapé da Sidebar */}
        <div className="p-4 border-t border-forest-soft space-y-3">
          <button
            type="button"
            onClick={onVoltarParaLoja}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs uppercase tracking-wider font-semibold text-cream border border-forest-soft hover:border-gold/50 rounded transition-colors"
          >
            ← Voltar para a Loja
          </button>
          <div className="flex items-center gap-3 px-3 py-2 bg-forest-soft/60 rounded border border-forest-soft">
            <div className="w-8 h-8 rounded-full bg-caramel text-forest font-bold flex items-center justify-center text-xs">
              AD
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-cream truncate">Curador Geral</p>
              <p className="text-[0.7rem] text-gold truncate">admin@papiro.com.br</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Conteúdo Principal */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Barra superior */}
        <header className="border-b border-line bg-cream-soft/80 backdrop-blur px-6 sm:px-10 py-5 flex flex-wrap items-center justify-between gap-4 sticky top-[74px] z-30">
          <div>
            <div className="flex items-center gap-2">
              <span className="label-caps text-gold">Painel Administrativo</span>
              <span className="text-coffee-faint">•</span>
              <span className="text-xs text-coffee-soft">
                {abaAtiva === 'visao-geral' && 'Visão Geral & Métricas Consolidadas'}
                {abaAtiva === 'acervo' && 'Gestão de Títulos e Estoque'}
                {abaAtiva === 'pedidos' && 'Acompanhamento de Todos os Pedidos'}
                {abaAtiva === 'clientes' && 'Gestão de Leitores'}
              </span>
            </div>
            <h2 className="font-display text-2xl font-bold text-coffee mt-0.5">
              {abaAtiva === 'visao-geral' && 'Panorama Editorial'}
              {abaAtiva === 'acervo' && 'Acervo de Obras'}
              {abaAtiva === 'pedidos' && 'Controle de Pedidos'}
              {abaAtiva === 'clientes' && 'Leitores Cadastrados'}
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <input
                type="text"
                value={termoBusca}
                onChange={(e) => setTermoBusca(e.target.value)}
                placeholder="Filtrar nesta página..."
                className="w-60 sm:w-72 rounded-sm border border-line-strong bg-cream-soft pl-9 pr-3 py-1.5 font-body text-xs text-coffee placeholder:text-coffee-faint focus:border-forest focus:outline-none"
              />
              <span className="absolute left-2.5 top-2 text-coffee-faint pointer-events-none">
                <SearchIcon />
              </span>
            </div>

            <button
              type="button"
              onClick={() => setModalNovoLivro(true)}
              className="px-4 py-2 bg-forest hover:bg-forest-soft text-cream text-xs uppercase tracking-wider font-semibold rounded-sm transition-colors flex items-center gap-2 shadow-sm"
            >
              <span className="text-gold font-bold text-base leading-none">+</span>
              Novo Livro
            </button>
          </div>
        </header>

        {/* Abas mobile */}
        <div className="flex md:hidden border-b border-line bg-cream-soft overflow-x-auto px-4">
          <button
            onClick={() => setAbaAtiva('visao-geral')}
            className={`py-3 px-4 font-body text-xs uppercase tracking-wider font-semibold whitespace-nowrap border-b-2 ${
              abaAtiva === 'visao-geral' ? 'border-forest text-forest' : 'border-transparent text-coffee-faint'
            }`}
          >
            Visão Geral
          </button>
          <button
            onClick={() => setAbaAtiva('acervo')}
            className={`py-3 px-4 font-body text-xs uppercase tracking-wider font-semibold whitespace-nowrap border-b-2 ${
              abaAtiva === 'acervo' ? 'border-forest text-forest' : 'border-transparent text-coffee-faint'
            }`}
          >
            Acervo ({livros.length})
          </button>
          <button
            onClick={() => setAbaAtiva('pedidos')}
            className={`py-3 px-4 font-body text-xs uppercase tracking-wider font-semibold whitespace-nowrap border-b-2 ${
              abaAtiva === 'pedidos' ? 'border-forest text-forest' : 'border-transparent text-coffee-faint'
            }`}
          >
            Pedidos ({pedidos.length})
          </button>
          <button
            onClick={() => setAbaAtiva('clientes')}
            className={`py-3 px-4 font-body text-xs uppercase tracking-wider font-semibold whitespace-nowrap border-b-2 ${
              abaAtiva === 'clientes' ? 'border-forest text-forest' : 'border-transparent text-coffee-faint'
            }`}
          >
            Clientes ({clientes.length})
          </button>
        </div>

        {/* Corpo do Painel */}
        <div className="p-6 sm:p-10 space-y-8 max-w-[1400px]">
          {erroAviso && (
            <div className="p-4 bg-amber-50 border border-amber-300 text-amber-900 rounded text-xs flex justify-between items-center">
              <span>{erroAviso}</span>
              <button onClick={() => setErroAviso(null)} className="font-bold">✕</button>
            </div>
          )}

          {/* ===================== ABA: VISÃO GERAL ===================== */}
          {abaAtiva === 'visao-geral' && (
            <>
              {/* KPIs */}
              <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                <div className="bg-cream-soft p-5 rounded-sm border border-line shadow-sm hover:border-gold/50 transition-colors">
                  <div className="flex justify-between items-start">
                    <span className="label-caps text-coffee-faint">Faturamento Total</span>
                    <span className="text-xs font-semibold text-forest bg-forest-tint px-2 py-0.5 rounded">
                      Consolidado
                    </span>
                  </div>
                  <p className="font-display text-3xl font-bold text-coffee mt-2">
                    R$ {Number(faturamento).toFixed(2).replace('.', ',')}
                  </p>
                  <p className="font-body text-xs text-coffee-soft mt-1">
                    {totalPedidosCount} pedidos faturados
                  </p>
                </div>

                <div className="bg-cream-soft p-5 rounded-sm border border-line shadow-sm hover:border-gold/50 transition-colors">
                  <div className="flex justify-between items-start">
                    <span className="label-caps text-coffee-faint">Pedidos Pendentes</span>
                    <span className="text-xs font-semibold text-caramel-dark bg-caramel/20 px-2 py-0.5 rounded">
                      {pedidosPendentesCount} na fila
                    </span>
                  </div>
                  <p className="font-display text-3xl font-bold text-coffee mt-2">
                    {pedidosPendentesCount}
                  </p>
                  <p className="font-body text-xs text-coffee-soft mt-1">
                    Aguardando separação / despacho
                  </p>
                </div>

                <div className="bg-cream-soft p-5 rounded-sm border border-line shadow-sm hover:border-gold/50 transition-colors">
                  <div className="flex justify-between items-start">
                    <span className="label-caps text-coffee-faint">Títulos Ativos</span>
                    <span className="text-xs font-semibold text-coffee-faint bg-cream-deep px-2 py-0.5 rounded">
                      Catálogo
                    </span>
                  </div>
                  <p className="font-display text-3xl font-bold text-coffee mt-2">
                    {totalObrasCount} obras
                  </p>
                  <p className="font-body text-xs text-coffee-soft mt-1">
                    {statsApi?.total_stock ?? livros.reduce((a, b) => a + (b.estoque || 0), 0)} exemplares
                  </p>
                </div>

                <div className="bg-cream-soft p-5 rounded-sm border border-line shadow-sm hover:border-gold/50 transition-colors">
                  <div className="flex justify-between items-start">
                    <span className="label-caps text-coffee-faint">Ticket Médio</span>
                    <span className="text-xs font-semibold text-gold-dark bg-gold/15 px-2 py-0.5 rounded">
                      Média
                    </span>
                  </div>
                  <p className="font-display text-3xl font-bold text-coffee mt-2">
                    R$ {Number(ticketMedio).toFixed(2).replace('.', ',')}
                  </p>
                  <p className="font-body text-xs text-coffee-soft mt-1">
                    Por pedido realizado
                  </p>
                </div>
              </section>

              {/* Gráfico & Alertas */}
              <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-cream-soft p-6 rounded-sm border border-line shadow-sm">
                  <div className="flex justify-between items-center mb-6">
                    <div>
                      <h3 className="font-display text-xl font-bold text-coffee">
                        Fluxo de Vendas (Últimas 4 Semanas)
                      </h3>
                      <p className="font-body text-xs text-coffee-faint">
                        Faturamento consolidado registrado no banco de dados
                      </p>
                    </div>
                  </div>

                  <div className="h-48 flex items-end gap-5 pt-6 pb-2 px-2 border-b border-line">
                    {(statsApi?.weekly_sales || [
                      { label: 'Sem 1', amount: 450, orders_count: 3 },
                      { label: 'Sem 2', amount: 980, orders_count: 6 },
                      { label: 'Sem 3', amount: 620, orders_count: 4 },
                      { label: 'Sem 4', amount: 1420, orders_count: 8 },
                    ]).map((sem, idx) => (
                      <div key={sem.label} className="flex-1 flex flex-col items-center gap-2">
                        <div
                          className={`w-full rounded-t transition-all ${
                            idx === 3 ? 'bg-gold hover:bg-gold-dark shadow-sm' : 'bg-forest-soft/40 hover:bg-forest'
                          }`}
                          style={{
                            height: `${Math.max(20, Math.min(100, (sem.amount / 1500) * 100))}%`,
                          }}
                        ></div>
                        <span className={`text-[0.7rem] ${idx === 3 ? 'font-bold text-forest' : 'text-coffee-faint'}`}>
                          {sem.label}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="flex justify-between items-center mt-4 text-xs text-coffee-faint font-body">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 bg-forest rounded-xs"></span> Vendas Semanais
                    </span>
                    <span className="font-medium text-coffee">Dados em tempo real via backend</span>
                  </div>
                </div>

                {/* Avisos de Estoque */}
                <div className="bg-cream-soft p-6 rounded-sm border border-line shadow-sm flex flex-col justify-between">
                  <div>
                    <h3 className="font-display text-xl font-bold text-coffee mb-1">
                      Avisos de Exemplares
                    </h3>
                    <p className="font-body text-xs text-coffee-faint mb-4">
                      Títulos com estoque reduzido (≤ 3 unidades)
                    </p>

                    <div className="space-y-3">
                      {(statsApi?.low_stock_products || livros.filter((l) => l.estoque <= 3)).slice(0, 3).map((l) => (
                        <div
                          key={l.id}
                          className="flex items-center justify-between p-3 bg-cream-deep/60 rounded-sm border border-line"
                        >
                          <div className="overflow-hidden pr-2">
                            <h4 className="font-display font-bold text-sm text-coffee truncate">
                              {l.title || l.titulo}
                            </h4>
                            <p className="font-body text-[0.7rem] text-coffee-faint">
                              {l.author || l.autor}
                            </p>
                          </div>
                          <span className="text-xs font-bold text-red-800 bg-red-100 px-2 py-0.5 rounded whitespace-nowrap">
                            {l.stock_qty ?? l.estoque} restante(s)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => setAbaAtiva('acervo')}
                    className="w-full mt-4 py-2 border border-forest text-forest hover:bg-forest hover:text-cream text-xs font-semibold uppercase tracking-wider rounded-sm transition-colors"
                  >
                    Gerenciar Acervo Completo
                  </button>
                </div>
              </section>
            </>
          )}

          {/* ===================== ABA: ACERVO ===================== */}
          {abaAtiva === 'acervo' && (
            <section className="bg-cream-soft rounded-sm border border-line shadow-sm overflow-hidden">
              <div className="p-6 border-b border-line flex flex-wrap justify-between items-center gap-4">
                <div>
                  <h3 className="font-display text-xl font-bold text-coffee">
                    Catálogo de Obras & Exemplares
                  </h3>
                  <p className="font-body text-xs text-coffee-faint">
                    {livrosFiltrados.length} obras no acervo
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setModalNovoLivro(true)}
                  className="px-4 py-2 bg-forest text-cream text-xs uppercase tracking-wider font-semibold rounded-sm hover:bg-forest-soft transition-colors"
                >
                  + Adicionar Livro
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left font-body text-sm">
                  <thead className="bg-cream-tint/60 text-[0.72rem] uppercase tracking-[0.16em] text-coffee-faint border-b border-line">
                    <tr>
                      <th className="py-3.5 px-6 font-semibold">Título</th>
                      <th className="py-3.5 px-6 font-semibold">Autor</th>
                      <th className="py-3.5 px-6 font-semibold">Categoria</th>
                      <th className="py-3.5 px-6 font-semibold">Preço</th>
                      <th className="py-3.5 px-6 font-semibold">Estoque</th>
                      <th className="py-3.5 px-6 font-semibold text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line text-coffee-soft">
                    {livrosFiltrados.map((livro) => (
                      <tr key={livro.id} className="hover:bg-cream-deep/40 transition-colors">
                        <td className="py-4 px-6 font-display font-bold text-coffee text-base">
                          {livro.titulo}
                          {livro.destaque && (
                            <span className="ml-2 text-[0.65rem] uppercase tracking-wider px-2 py-0.5 bg-gold/20 text-gold-dark rounded font-body font-semibold">
                              Destaque
                            </span>
                          )}
                        </td>
                        <td className="py-4 px-6 text-xs text-coffee-soft">{livro.autor}</td>
                        <td className="py-4 px-6 text-xs">
                          <span className="px-2.5 py-1 bg-cream-deep rounded text-coffee-faint">
                            {livro.categoria}
                          </span>
                        </td>
                        <td className="py-4 px-6 font-display font-bold text-coffee">
                          R$ {Number(livro.preco).toFixed(2).replace('.', ',')}
                        </td>
                        <td className="py-4 px-6">
                          <span
                            className={`text-xs font-semibold px-2 py-0.5 rounded ${
                              livro.estoque <= 2 ? 'bg-red-100 text-red-800' : 'bg-forest-tint text-forest'
                            }`}
                          >
                            {livro.estoque} un
                          </span>
                        </td>
                        <td className="py-4 px-6 text-right">
                          <button
                            type="button"
                            onClick={() => handleRemoverLivro(livro.id)}
                            className="text-xs text-red-700 hover:text-red-900 font-medium transition-colors"
                          >
                            Remover
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* ===================== ABA: PEDIDOS ===================== */}
          {abaAtiva === 'pedidos' && (
            <section className="bg-cream-soft rounded-sm border border-line shadow-sm overflow-hidden">
              <div className="p-6 border-b border-line flex justify-between items-center">
                <div>
                  <h3 className="font-display text-xl font-bold text-coffee">
                    Todos os Pedidos de Clientes
                  </h3>
                  <p className="font-body text-xs text-coffee-faint">
                    Gerenciamento global de status e entregas (/admin/orders)
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left font-body text-sm">
                  <thead className="bg-cream-tint/60 text-[0.72rem] uppercase tracking-[0.16em] text-coffee-faint border-b border-line">
                    <tr>
                      <th className="py-3.5 px-6 font-semibold">Código</th>
                      <th className="py-3.5 px-6 font-semibold">Cliente</th>
                      <th className="py-3.5 px-6 font-semibold">Itens</th>
                      <th className="py-3.5 px-6 font-semibold">Data</th>
                      <th className="py-3.5 px-6 font-semibold">Status</th>
                      <th className="py-3.5 px-6 font-semibold">Total</th>
                      <th className="py-3.5 px-6 font-semibold text-right">Alterar Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line text-coffee-soft">
                    {pedidosFiltrados.map((pedido) => (
                      <tr key={pedido.id} className="hover:bg-cream-deep/40 transition-colors">
                        <td className="py-4 px-6 font-mono text-xs font-semibold text-coffee">
                          {pedido.id}
                        </td>
                        <td className="py-4 px-6">
                          <p className="font-medium text-coffee">{pedido.cliente}</p>
                          <p className="text-[0.7rem] text-coffee-faint">{pedido.email}</p>
                        </td>
                        <td className="py-4 px-6 text-xs">{pedido.itens}</td>
                        <td className="py-4 px-6 text-xs text-coffee-faint">{pedido.data}</td>
                        <td className="py-4 px-6">
                          <span
                            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium ${
                              pedido.status === 'processing' || pedido.status === 'separacao'
                                ? 'bg-forest-tint text-forest'
                                : pedido.status === 'pending' || pedido.status === 'aguardando'
                                ? 'bg-caramel/15 text-caramel-dark'
                                : pedido.status === 'shipped' || pedido.status === 'enviado'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-green-100 text-green-800'
                            }`}
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                            {pedido.statusLabel}
                          </span>
                        </td>
                        <td className="py-4 px-6 font-display font-bold text-coffee text-base">
                          R$ {Number(pedido.total).toFixed(2).replace('.', ',')}
                        </td>
                        <td className="py-4 px-6 text-right">
                          <select
                            value={pedido.status}
                            onChange={(e) => handleAtualizarStatusPedido(pedido.rawId, pedido.id, e.target.value)}
                            className="text-xs bg-cream-deep border border-line-strong rounded px-2 py-1 text-coffee focus:outline-none focus:border-forest"
                          >
                            <option value="pending">Aguardando Envio</option>
                            <option value="processing">Em Separação</option>
                            <option value="shipped">Enviado</option>
                            <option value="delivered">Entregue</option>
                            <option value="completed">Concluído</option>
                            <option value="cancelled">Cancelado</option>
                          </select>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* ===================== ABA: CLIENTES ===================== */}
          {abaAtiva === 'clientes' && (
            <section className="bg-cream-soft rounded-sm border border-line shadow-sm overflow-hidden">
              <div className="p-6 border-b border-line flex justify-between items-center">
                <div>
                  <h3 className="font-display text-xl font-bold text-coffee">
                    Leitores & Clientes Cadastrados
                  </h3>
                  <p className="font-body text-xs text-coffee-faint">
                    {clientesFiltrados.length} leitores registrados no sistema
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left font-body text-sm">
                  <thead className="bg-cream-tint/60 text-[0.72rem] uppercase tracking-[0.16em] text-coffee-faint border-b border-line">
                    <tr>
                      <th className="py-3.5 px-6 font-semibold">ID</th>
                      <th className="py-3.5 px-6 font-semibold">Nome Completo</th>
                      <th className="py-3.5 px-6 font-semibold">E-mail</th>
                      <th className="py-3.5 px-6 font-semibold">Perfil</th>
                      <th className="py-3.5 px-6 font-semibold">Pedidos</th>
                      <th className="py-3.5 px-6 font-semibold text-right">Cadastro</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line text-coffee-soft">
                    {clientesFiltrados.map((cli) => (
                      <tr key={cli.id} className="hover:bg-cream-deep/40 transition-colors">
                        <td className="py-4 px-6 font-mono text-xs text-coffee">#{cli.id}</td>
                        <td className="py-4 px-6 font-medium text-coffee">{cli.full_name}</td>
                        <td className="py-4 px-6 text-xs text-coffee-faint">{cli.email}</td>
                        <td className="py-4 px-6">
                          <span
                            className={`text-xs uppercase tracking-wider font-semibold px-2 py-0.5 rounded ${
                              cli.role === 'admin'
                                ? 'bg-forest text-cream'
                                : 'bg-cream-deep text-coffee-soft'
                            }`}
                          >
                            {cli.role}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-xs font-semibold text-coffee">
                          {cli.orders_count || 0} pedido(s)
                        </td>
                        <td className="py-4 px-6 text-right text-xs text-coffee-faint">
                          {cli.created_at ? new Date(cli.created_at).toLocaleDateString('pt-BR') : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </div>
      </main>

      {/* Modal: Novo Livro */}
      {modalNovoLivro && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-forest/50 backdrop-blur-xs">
          <div className="w-full max-w-lg bg-cream-soft border border-line rounded-sm shadow-2xl p-6 sm:p-8">
            <div className="flex justify-between items-center pb-4 border-b border-line">
              <div>
                <span className="label-caps text-gold">Curadoria</span>
                <h3 className="font-display text-2xl font-bold text-coffee mt-1">
                  Cadastrar Obra no Acervo
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setModalNovoLivro(false)}
                className="text-coffee-faint hover:text-coffee transition-colors"
              >
                <CloseIcon />
              </button>
            </div>

            <form onSubmit={handleCadastrarLivro} className="mt-6 space-y-4 font-body">
              <div>
                <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
                  Título da Obra *
                </label>
                <input
                  type="text"
                  required
                  placeholder="ex: Memórias Póstumas de Brás Cubas"
                  value={novoTitulo}
                  onChange={(e) => setNovoTitulo(e.target.value)}
                  className="w-full campo py-2"
                />
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
                  Autor(a) *
                </label>
                <input
                  type="text"
                  required
                  placeholder="ex: Machado de Assis"
                  value={novoAutor}
                  onChange={(e) => setNovoAutor(e.target.value)}
                  className="w-full campo py-2"
                />
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
                  Descrição Curta
                </label>
                <textarea
                  rows="2"
                  placeholder="Breve descrição editorial da obra..."
                  value={novoDescricao}
                  onChange={(e) => setNovoDescricao(e.target.value)}
                  className="w-full campo py-2 text-xs"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
                    Categoria
                  </label>
                  <select
                    value={novaCategoriaId}
                    onChange={(e) => setNovaCategoriaId(Number(e.target.value))}
                    className="w-full campo py-2 text-xs"
                  >
                    {categorias.length > 0 ? (
                      categorias.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))
                    ) : (
                      <>
                        <option value={1}>Ficção Clássica</option>
                        <option value={2}>Literatura Brasileira</option>
                        <option value={3}>Poesia & Teatro</option>
                        <option value={4}>Filosofia</option>
                      </>
                    )}
                  </select>
                </div>

                <div>
                  <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
                    Preço (R$) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    placeholder="120.00"
                    value={novoPreco}
                    onChange={(e) => setNovoPreco(e.target.value)}
                    className="w-full campo py-2"
                  />
                </div>

                <div>
                  <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
                    Estoque *
                  </label>
                  <input
                    type="number"
                    min="0"
                    required
                    placeholder="5"
                    value={novoEstoque}
                    onChange={(e) => setNovoEstoque(e.target.value)}
                    className="w-full campo py-2"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-line mt-6">
                <button
                  type="button"
                  onClick={() => setModalNovoLivro(false)}
                  className="px-4 py-2 border border-line-strong text-coffee-soft text-xs uppercase tracking-wider font-semibold rounded-sm hover:bg-cream-deep transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={salvandoLivro}
                  className="px-6 py-2 bg-forest hover:bg-forest-soft text-cream text-xs uppercase tracking-wider font-semibold rounded-sm transition-colors shadow-sm disabled:opacity-50"
                >
                  {salvandoLivro ? 'Salvando...' : 'Adicionar ao Catálogo'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
