import { useState, useMemo, useEffect } from 'react'
import { useAuth } from '../context/auth-context'
import { CloseIcon, SearchIcon } from '../components/Icons'
import ModalCupom from '../components/ModalCupom'
import ModalCategoria from '../components/ModalCategoria'
import ModalUsuario from '../components/ModalUsuario'
import productService from '../api/products'
import categoryService from '../api/categories'
import adminService from '../api/admin'
import userService from '../api/users'
import couponService from '../api/coupons'
import newsletterService from '../api/newsletter'

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
    desconto: 0,
    estoque: 1,
    destaque: true,
    bestseller: true,
  },
  {
    id: 2,
    titulo: 'O Som e a Fúria (Ed. Luxo)',
    autor: 'William Faulkner',
    categoria: 'Ficção Internacional',
    categoryId: 1,
    preco: 165.0,
    desconto: 0,
    estoque: 2,
    destaque: false,
    bestseller: false,
  },
  {
    id: 3,
    titulo: 'A Divina Comédia (Ilustrada Doré)',
    autor: 'Dante Alighieri',
    categoria: 'Poesia Épica',
    categoryId: 2,
    preco: 290.0,
    desconto: 10,
    estoque: 3,
    destaque: true,
    bestseller: true,
  },
  {
    id: 4,
    titulo: 'Grande Sertão: Veredas',
    autor: 'Guimarães Rosa',
    categoria: 'Literatura Brasileira',
    categoryId: 1,
    preco: 189.9,
    desconto: 0,
    estoque: 14,
    destaque: true,
    bestseller: true,
  },
  {
    id: 5,
    titulo: 'Cem Anos de Solidão',
    autor: 'Gabriel García Márquez',
    categoria: 'Realismo Fantástico',
    categoryId: 1,
    preco: 120.0,
    desconto: 15,
    estoque: 8,
    destaque: false,
    bestseller: true,
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
  const { usuario } = useAuth()
  const ehAdmin = usuario?.role === 'admin'

  const [abaAtiva, setAbaAtiva] = useState('visao-geral')
  const [termoBusca, setTermoBusca] = useState('')
  const [pedidos, setPedidos] = useState(PEDIDOS_FALLBACK)
  const [livros, setLivros] = useState(LIVROS_FALLBACK)
  const [clientes, setClientes] = useState(CLIENTES_FALLBACK)
  const [categorias, setCategorias] = useState([])
  // Estados de Newsletter
  const [inscritos, setInscritos] = useState([])
  // Estados de Cupons
  const [cupons, setCupons] = useState([])
  const [cupomEditando, setCupomEditando] = useState(null)
  const [vinculosCupom, setVinculosCupom] = useState([])
  const [statsApi, setStatsApi] = useState(null)
  const [erroAviso, setErroAviso] = useState(null)
  const [modalNovoLivro, setModalNovoLivro] = useState(false)
  // Livro em edição (null = modal em modo criação)
  const [livroEditando, setLivroEditando] = useState(null)
  // Estados de Categorias
  const [categoriaEditando, setCategoriaEditando] = useState(null)
  const [modalCategoria, setModalCategoria] = useState(false)
  const [salvandoLivro, setSalvandoLivro] = useState(false)
  const [modalCupom, setModalCupom] = useState(false)
  // Estados de Usuários
  const [modalUsuario, setModalUsuario] = useState(false)
  const [usuarioEditando, setUsuarioEditando] = useState(null)
  const [filtroRoleUsuario, setFiltroRoleUsuario] = useState('todos')
  // Form novo livro
  const [novoTitulo, setNovoTitulo] = useState('')
  const [novoAutor, setNovoAutor] = useState('')
  const [novaCategoriaId, setNovaCategoriaId] = useState(1)
  const [novoDescricao, setNovoDescricao] = useState('')
  const [novoPreco, setNovoPreco] = useState('')
  const [novoDesconto, setNovoDesconto] = useState('')
  const [novoEstoque, setNovoEstoque] = useState('')
  const [novoDestaque, setNovoDestaque] = useState(false)
  const [novoBestseller, setNovoBestseller] = useState(false)

  // Carrega dados da API ao montar
  useEffect(() => {
    if (!ehAdmin) return
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
            desconto: p.discount_pct != null ? Number(p.discount_pct) : 0,
            estoque: p.stock_qty ?? 0,
            destaque: Boolean(p.is_featured),
            bestseller: Boolean(p.is_bestseller),
          }))
          setLivros(formatados)
        }

        // 3. Categorias (/categories/list)
        const categoriasApi = await categoryService.listar().catch(() => [])
        if (ativo && Array.isArray(categoriasApi) && categoriasApi.length > 0) {
          setCategorias(categoriasApi)
          setNovaCategoriaId(categoriasApi[0].id)
        }

        // 3b. Inscritos da Newsletter (/newsletter/list)
        const inscritosApi = await newsletterService.listarInscritos().catch(() => [])
        if (ativo && Array.isArray(inscritosApi)) {
          setInscritos(inscritosApi)
        }

        // 5. Todos os Pedidos (/admin/orders)
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

        // 6. Cupons de desconto (/coupons/list)
        const cuponsApi = await couponService.listar().catch(() => [])
        if (ativo && Array.isArray(cuponsApi)) {
          setCupons(cuponsApi)
        }
      } catch (err) {
        console.warn('Conectando via mock/fallback offline:', err)
      }
    }

    carregarTudo()
    return () => {
      ativo = false
    }
    // `ehAdmin` é derivado de `usuario.role`; só muda no login/logout, e a
    // busca dos dados de admin deve rodar somente na montagem (uma vez).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Fecha o modal de livro (limpa o modo edição)
  const fecharModalLivro = () => {
    setModalNovoLivro(false)
    setLivroEditando(null)
    setNovoDesconto('')
  }

  // Abre o modal em modo criação (limpa o livro em edição)
  const handleNovoLivro = () => {
    setLivroEditando(null)
    setNovoTitulo('')
    setNovoAutor('')
    setNovaCategoriaId(categorias[0]?.id ?? 1)
    setNovoDescricao('')
    setNovoPreco('')
    setNovoDesconto('')
    setNovoEstoque('')
    setNovoDestaque(false)
    setNovoBestseller(false)
    setModalNovoLivro(true)
  }

  // Abre o modal em modo edição, pré-preenchendo o formulário
  const handleEditarLivro = (livro) => {
    setLivroEditando(livro)
    setNovoTitulo(livro.titulo || '')
    setNovoAutor(livro.autor === 'Autor não informado' ? '' : livro.autor || '')
    setNovaCategoriaId(livro.categoryId || categorias[0]?.id || 1)
    setNovoDescricao('')
    setNovoPreco(livro.preco != null ? String(livro.preco) : '')
    setNovoDesconto(
      livro.desconto != null && livro.desconto > 0
        ? String(livro.desconto)
        : (livro.discount_pct != null && livro.discount_pct > 0 ? String(livro.discount_pct) : '')
    )
    setNovoEstoque(livro.estoque != null ? String(livro.estoque) : '')
    setNovoDestaque(Boolean(livro.destaque))
    setNovoBestseller(Boolean(livro.bestseller))
    setModalNovoLivro(true)
  }

  // Cria ou atualiza um livro. Em edição envia apenas os campos preenchidos
  // (o backend aceita PATCH parcial) e NÃO regera o slug.
  const handleSalvarLivro = async (e) => {
    e.preventDefault()
    if (!novoTitulo.trim() || !novoAutor.trim() || !novoPreco) return

    setSalvandoLivro(true)
    setErroAviso(null)

    const precoNum = parseFloat(novoPreco) || 0
    const estoqueNum = parseInt(novoEstoque, 10) || 1
    const catId = Number(novaCategoriaId) || 1
    const descontoNum =
      novoDesconto !== '' && novoDesconto != null
        ? Math.min(100, Math.max(0, parseInt(novoDesconto, 10) || 0))
        : null

    try {
      if (livroEditando) {
        const payload = {
          title: novoTitulo.trim(),
          author: novoAutor.trim(),
          price: precoNum,
          discount_pct: descontoNum,
          stock_qty: estoqueNum,
          category_id: catId,
          is_featured: novoDestaque,
          is_bestseller: novoBestseller,
        }
        if (novoDescricao.trim()) payload.description = novoDescricao.trim()

        const resp = await productService.atualizar(livroEditando.id, payload)
        const categoriaNome =
          categorias.find((c) => c.id === catId)?.name || livroEditando.categoria
        const atualizado = {
          ...livroEditando,
          titulo: resp?.title ?? payload.title,
          autor: resp?.author ?? payload.author,
          categoria: resp?.category_name ?? categoriaNome,
          categoryId: catId,
          preco: resp?.price != null ? Number(resp.price) : precoNum,
          desconto: resp?.discount_pct != null ? Number(resp.discount_pct) : (descontoNum ?? 0),
          estoque: resp?.stock_qty != null ? resp.stock_qty : estoqueNum,
          destaque: resp?.is_featured != null ? Boolean(resp.is_featured) : novoDestaque,
          bestseller: resp?.is_bestseller != null ? Boolean(resp.is_bestseller) : novoBestseller,
        }
        setLivros((prev) =>
          prev.map((l) => (l.id === livroEditando.id ? atualizado : l)),
        )
      } else {
        const slug = `${gerarSlug(novoTitulo)}-${Date.now().toString().slice(-4)}`
        const desc = novoDescricao.trim() || `Edição clássica de ${novoTitulo}, por ${novoAutor}.`
        const payload = {
          category_id: catId,
          title: novoTitulo.trim(),
          slug: slug,
          description: desc,
          price: precoNum,
          discount_pct: descontoNum,
          author: novoAutor.trim(),
          stock_qty: estoqueNum,
          is_active: true,
          is_featured: novoDestaque,
          is_bestseller: novoBestseller,
        }

        const resp = await productService.criar(payload)
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
          desconto: resp?.discount_pct != null ? Number(resp.discount_pct) : (descontoNum ?? 0),
          estoque: estoqueNum,
          destaque: resp?.is_featured != null ? Boolean(resp.is_featured) : novoDestaque,
          bestseller: resp?.is_bestseller != null ? Boolean(resp.is_bestseller) : novoBestseller,
        }
        setLivros((prev) => [novoLivroObj, ...prev])
      }

      setNovoTitulo('')
      setNovoAutor('')
      setNovoDescricao('')
      setNovoPreco('')
      setNovoDesconto('')
      setNovoEstoque('')
      setNovoDestaque(false)
      setNovoBestseller(false)
      setLivroEditando(null)
      setModalNovoLivro(false)
    } catch {
      setErroAviso(
        livroEditando
          ? 'Erro ao atualizar o produto.'
          : 'Erro ao cadastrar via API. Adicionado na visualização local.',
      )
    } finally {
      setSalvandoLivro(false)
    }
  }

  // Remover livro
  const handleRemoverLivro = async (id) => {
    try {
      await productService.excluir(id).catch(() => null)
      setLivros((prev) => prev.filter((l) => l.id !== id))
    } catch {
      setLivros((prev) => prev.filter((l) => l.id !== id))
    }
  }

  // Recarrega a lista de cupons do backend
  const recarregarCupons = async () => {
    const cuponsApi = await couponService.listar().catch(() => [])
    if (Array.isArray(cuponsApi)) setCupons(cuponsApi)
  }

  // Abre o modal de cupom em modo criação
  const handleNovoCupom = () => {
    setCupomEditando(null)
    setVinculosCupom([])
    setModalCupom(true)
  }

  // Abre o modal de cupom em modo edição. Carrega os vínculos ANTES de montar
  // o modal: o ModalCupom inicializa o estado de posse no primeiro render, então
  // precisa receber os vínculos já prontos (sem re-sincronização posterior).
  const handleEditarCupom = async (cupom) => {
    setCupomEditando(cupom)
    setVinculosCupom([])
    try {
      const resp = await couponService.vinculosDoCupom(cupom.id)
      setVinculosCupom(Array.isArray(resp) ? resp : [])
    } catch {
      setVinculosCupom([])
    }
    setModalCupom(true)
  }

  // Cria/atualiza um cupom e sincroniza a posse escolhida no modal.
  // O `onSalvar` do modal entrega os ids de usuários marcados; aqui é feito o
  // diff com os vínculos atuais: cria os que faltam e remove os desmarcados.
  const handleSalvarCupom = async (
    payload,
    cupomId,
    { usuariosSelecionados = [], vinculosIniciais = [] } = {},
  ) => {
    let idFinal = cupomId
    if (cupomId) {
      await couponService.atualizar(cupomId, payload)
    } else {
      const criado = await couponService.criar(payload)
      idFinal = criado?.id ?? null
    }

    if (idFinal != null) {
      const selecionados = new Set(usuariosSelecionados)
      const vinculosPorUsuario = new Map(
        vinculosIniciais.map((v) => [v.user_id, v]),
      )

      // Adiciona os novos; ignora conflito (já atribuído) para não quebrar o lote.
      await Promise.all(
        usuariosSelecionados
          .filter((uid) => !vinculosPorUsuario.has(uid))
          .map((uid) =>
            couponService.atribuir(uid, idFinal).catch(() => null),
          ),
      )

      // Remove os que foram desmarcados.
      await Promise.all(
        vinculosIniciais
          .filter((v) => !selecionados.has(v.user_id))
          .map((v) =>
            couponService.removerVinculo(v.id, v.user_id).catch(() => null),
          ),
      )
    }

    await recarregarCupons()
  }

  // Exclui um cupom
  const handleExcluirCupom = async (cupom) => {
    if (!window.confirm(`Excluir o cupom "${cupom.code}"?`)) return
    try {
      await couponService.excluir(cupom.id)
      await recarregarCupons()
    } catch (err) {
      setErroAviso(err.message || 'Erro ao excluir o cupom.')
    }
  }

  // ===================== Categorias =====================

  // Recarrega a lista de categorias do backend.
  const recarregarCategorias = async () => {
    const categoriasApi = await categoryService.listar().catch(() => [])
    if (Array.isArray(categoriasApi)) setCategorias(categoriasApi)
  }

  // Abre o modal de categoria em modo criação
  const handleNovaCategoria = () => {
    setCategoriaEditando(null)
    setModalCategoria(true)
  }

  // Abre o modal de categoria em modo edição
  const handleEditarCategoria = (categoria) => {
    setCategoriaEditando(categoria)
    setModalCategoria(true)
  }

  // Cria/atualiza uma categoria (o modal devolve payload + id)
  const handleSalvarCategoria = async (payload, categoriaId) => {
    if (categoriaId) {
      await categoryService.atualizar(categoriaId, payload)
    } else {
      await categoryService.criar(payload)
    }
    await recarregarCategorias()
    setModalCategoria(false)
  }

  // Exclui uma categoria
  const handleExcluirCategoria = async (categoria) => {
    if (!window.confirm(`Excluir a categoria "${categoria.name}"?`)) return
    try {
      await categoryService.excluir(categoria.id)
      await recarregarCategorias()
    } catch (err) {
      setErroAviso(err.message || 'Erro ao excluir a categoria.')
    }
  }

  // ===================== Usuários / Leitores =====================

  // Recarrega a lista de usuários do backend
  const recarregarUsuarios = async () => {
    const usuariosApi = await userService.listar().catch(() => [])
    if (Array.isArray(usuariosApi) && usuariosApi.length > 0) {
      setClientes(usuariosApi)
    }
  }

  // Abre o modal de usuário em modo criação
  const handleNovoUsuario = () => {
    setUsuarioEditando(null)
    setModalUsuario(true)
  }

  // Abre o modal de usuário em modo edição
  const handleEditarUsuario = (usuario) => {
    setUsuarioEditando(usuario)
    setModalUsuario(true)
  }

  // Cria ou atualiza um usuário
  const handleSalvarUsuario = async (payload, usuarioId) => {
    if (usuarioId) {
      const resp = await userService.atualizar(usuarioId, payload).catch(() => null)
      setClientes((prev) =>
        prev.map((u) =>
          u.id === usuarioId
            ? {
                ...u,
                full_name: payload.full_name,
                email: payload.email,
                role: payload.role,
                is_active: payload.is_active,
                ...(resp || {}),
              }
            : u,
        ),
      )
    } else {
      const resp = await userService.criar(payload).catch(() => null)
      const novoId = resp?.id || Date.now()
      const novoObj = {
        id: novoId,
        full_name: payload.full_name,
        email: payload.email,
        role: payload.role || 'customer',
        is_active: payload.is_active !== false,
        orders_count: 0,
        created_at: new Date().toISOString(),
      }
      setClientes((prev) => [novoObj, ...prev])
    }
    await recarregarUsuarios().catch(() => null)
  }

  // Desativa / exclui um usuário
  const handleExcluirUsuario = async (usuario) => {
    const acao = usuario.is_active === false ? 'remover' : 'desativar'
    if (!window.confirm(`Deseja realmente ${acao} o usuário "${usuario.full_name}"?`)) return
    try {
      await userService.excluir(usuario.id).catch(() => null)
      setClientes((prev) =>
        prev.map((u) => (u.id === usuario.id ? { ...u, is_active: false } : u)),
      )
      await recarregarUsuarios().catch(() => null)
    } catch (err) {
      setErroAviso(err.message || 'Erro ao desativar o usuário.')
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
    let lista = [...clientes]
    if (filtroRoleUsuario !== 'todos') {
      lista = lista.filter((c) => c.role === filtroRoleUsuario)
    }
    if (!termoBusca.trim()) return lista
    const busca = termoBusca.toLowerCase()
    return lista.filter(
      (c) =>
        String(c.id).includes(busca) ||
        c.full_name?.toLowerCase().includes(busca) ||
        c.email?.toLowerCase().includes(busca) ||
        c.role?.toLowerCase().includes(busca)
    )
  }, [clientes, termoBusca, filtroRoleUsuario])

  const cuponsFiltrados = useMemo(() => {
    if (!termoBusca.trim()) return cupons
    const busca = termoBusca.toLowerCase()
    return cupons.filter(
      (c) =>
        c.code?.toLowerCase().includes(busca) ||
        c.discount_type?.toLowerCase().includes(busca)
    )
  }, [cupons, termoBusca])

  const categoriasFiltradas = useMemo(() => {
    if (!termoBusca.trim()) return categorias
    const busca = termoBusca.toLowerCase()
    return categorias.filter(
      (c) =>
        c.name?.toLowerCase().includes(busca) ||
        c.slug?.toLowerCase().includes(busca),
    )
  }, [categorias, termoBusca])

  const inscritosFiltradas = useMemo(() => {
    if (!termoBusca.trim()) return inscritos
    const t = termoBusca.toLowerCase()
    return inscritos.filter((i) => i.email?.toLowerCase().includes(t))
  }, [inscritos, termoBusca])

  // KPIs
  const faturamento = statsApi?.total_revenue ?? pedidos.reduce((a, b) => a + (b.total || 0), 0)
  const totalPedidosCount = statsApi?.total_orders ?? pedidos.length
  const pedidosPendentesCount =
    statsApi?.pending_orders ??
    pedidos.filter((p) => p.status === 'pending' || p.status === 'processing' || p.status === 'separacao' || p.status === 'aguardando').length
  const totalObrasCount = statsApi?.total_products ?? livros.length
  const ticketMedio = statsApi?.average_ticket ?? (totalPedidosCount > 0 ? faturamento / totalPedidosCount : 0)

  // Defesa extra: só administradores veem o painel. (App.jsx já bloqueia a rota;
  // aqui garantimos que, mesmo montado por engano, nada de dados admin é exibido.)
  if (!ehAdmin) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-cream-deep px-4 text-center">
        <div>
          <p className="font-display text-xl font-medium text-coffee">
            Acesso restrito a administradores
          </p>
          <p className="mt-2 font-body text-sm text-coffee-faint">
            Você não tem permissão para visualizar o painel administrativo.
          </p>
          <button
            type="button"
            onClick={onVoltarParaLoja}
            className="mt-5 px-4 py-2 font-body text-sm text-cream bg-forest hover:bg-forest-soft"
          >
            Voltar para a loja
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-cream-deep text-coffee">
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

            <button
              type="button"
              onClick={() => setAbaAtiva('descontos')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-sm text-left transition-colors duration-200 ${
                abaAtiva === 'descontos'
                  ? 'bg-gold text-forest font-semibold shadow-sm'
                  : 'text-cream-soft hover:bg-forest-soft hover:text-cream'
              }`}
            >
              <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 14l6-6M9.5 8.5h.01M14.5 15.5h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              Descontos & Cupons
              <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-forest-soft text-gold font-medium">
                {cupons.length}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setAbaAtiva('categorias')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-sm text-left transition-colors duration-200 ${
                abaAtiva === 'categorias'
                  ? 'bg-gold text-forest font-semibold shadow-sm'
                  : 'text-cream-soft hover:bg-forest-soft hover:text-cream'
              }`}
            >
              <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
              </svg>
              Categorias
              <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-forest-soft text-gold font-medium">
                {categorias.length}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setAbaAtiva('newsletter')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-sm text-left transition-colors duration-200 ${
                abaAtiva === 'newsletter'
                  ? 'bg-gold text-forest font-semibold shadow-sm'
                  : 'text-cream-soft hover:bg-forest-soft hover:text-cream'
              }`}
            >
              <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
              Newsletter
              <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-forest-soft text-gold font-medium">
                {inscritos.length}
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
        <header className="border-b border-line bg-cream-soft/80 backdrop-blur px-6 sm:px-10 py-5 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-30">
          <div>
            <div className="flex items-center gap-2">
              <span className="label-caps text-gold">Painel Administrativo</span>
              <span className="text-coffee-faint">•</span>
              <span className="text-xs text-coffee-soft">
                {abaAtiva === 'visao-geral' && 'Visão Geral & Métricas Consolidadas'}
                {abaAtiva === 'acervo' && 'Gestão de Títulos e Estoque'}
                {abaAtiva === 'pedidos' && 'Acompanhamento de Todos os Pedidos'}
                {abaAtiva === 'clientes' && 'Gestão de Leitores'}
                {abaAtiva === 'descontos' && 'Gestão de Cupons e Descontos'}
                {abaAtiva === 'categorias' && 'Gestão de Categorias do Acervo'}
                {abaAtiva === 'newsletter' && 'Inscritos da Carta do Livreiro'}
              </span>
            </div>
            <h2 className="font-display text-2xl font-bold text-coffee mt-0.5">
              {abaAtiva === 'visao-geral' && 'Panorama Editorial'}
              {abaAtiva === 'acervo' && 'Acervo de Obras'}
              {abaAtiva === 'pedidos' && 'Controle de Pedidos'}
              {abaAtiva === 'clientes' && 'Leitores Cadastrados'}
              {abaAtiva === 'descontos' && 'Cupons de Desconto'}
              {abaAtiva === 'categorias' && 'Categorias do Acervo'}
              {abaAtiva === 'newsletter' && 'Newsletter'}
            </h2>
          </div>

          {abaAtiva !== 'visao-geral' && (
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
                onClick={() => {
                  if (abaAtiva === 'descontos') handleNovoCupom()
                  else if (abaAtiva === 'categorias') handleNovaCategoria()
                  else if (abaAtiva === 'clientes') handleNovoUsuario()
                  else handleNovoLivro()
                }}
                hidden={abaAtiva === 'newsletter' || abaAtiva === 'pedidos'}
                className="px-4 py-2 bg-forest hover:bg-forest-soft text-cream text-xs uppercase tracking-wider font-semibold rounded-sm transition-colors flex items-center gap-2 shadow-sm"
              >
                <span className="text-gold font-bold text-base leading-none">+</span>
                {abaAtiva === 'descontos'
                  ? 'Novo Cupom'
                  : abaAtiva === 'categorias'
                    ? 'Nova Categoria'
                    : abaAtiva === 'clientes'
                      ? 'Novo Usuário'
                      : 'Novo Livro'}
              </button>
            </div>
          )}
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
          <button
            onClick={() => setAbaAtiva('descontos')}
            className={`py-3 px-4 font-body text-xs uppercase tracking-wider font-semibold whitespace-nowrap border-b-2 ${
              abaAtiva === 'descontos' ? 'border-forest text-forest' : 'border-transparent text-coffee-faint'
            }`}
          >
            Cupons ({cupons.length})
          </button>
          <button
            onClick={() => setAbaAtiva('categorias')}
            className={`py-3 px-4 font-body text-xs uppercase tracking-wider font-semibold whitespace-nowrap border-b-2 ${
              abaAtiva === 'categorias' ? 'border-forest text-forest' : 'border-transparent text-coffee-faint'
            }`}
          >
            Categorias ({categorias.length})
          </button>
          <button
            onClick={() => setAbaAtiva('newsletter')}
            className={`py-3 px-4 font-body text-xs uppercase tracking-wider font-semibold whitespace-nowrap border-b-2 ${
              abaAtiva === 'newsletter' ? 'border-forest text-forest' : 'border-transparent text-coffee-faint'
            }`}
          >
            Newsletter ({inscritos.length})
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
                  onClick={handleNovoLivro}
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
                      <th className="py-3.5 px-6 font-semibold">Desconto</th>
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
                          {livro.bestseller && (
                            <span className="ml-1.5 text-[0.65rem] uppercase tracking-wider px-2 py-0.5 bg-forest-tint text-forest rounded font-body font-semibold">
                              Mais Vendido
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
                          {livro.desconto > 0 ? (
                            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-caramel/20 text-caramel-dark">
                              {livro.desconto}% OFF
                            </span>
                          ) : (
                            <span className="text-xs text-coffee-faint">—</span>
                          )}
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
                          <div className="flex justify-end gap-3">
                            <button
                              type="button"
                              onClick={() => handleEditarLivro(livro)}
                              className="text-xs text-forest hover:text-forest-soft font-medium transition-colors"
                            >
                              Editar
                            </button>
                            <button
                              type="button"
                              onClick={() => handleRemoverLivro(livro.id)}
                              className="text-xs text-red-700 hover:text-red-900 font-medium transition-colors"
                            >
                              Remover
                            </button>
                          </div>
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

          {/* ===================== ABA: GESTÃO DE USUÁRIOS (CRUD) ===================== */}
          {abaAtiva === 'clientes' && (
            <section className="bg-cream-soft rounded-sm border border-line shadow-sm overflow-hidden">
              <div className="p-6 border-b border-line flex flex-wrap justify-between items-center gap-4">
                <div>
                  <h3 className="font-display text-xl font-bold text-coffee">
                    Gestão de Leitores & Usuários
                  </h3>
                  <p className="font-body text-xs text-coffee-faint">
                    {clientesFiltrados.length} usuário(s) encontrado(s) no sistema
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  {/* Filtro por perfil */}
                  <div className="flex items-center gap-1 bg-cream-deep p-1 rounded border border-line-strong">
                    <button
                      type="button"
                      onClick={() => setFiltroRoleUsuario('todos')}
                      className={`px-3 py-1 text-xs font-semibold uppercase tracking-wider rounded transition-colors ${
                        filtroRoleUsuario === 'todos'
                          ? 'bg-forest text-cream shadow-xs'
                          : 'text-coffee-faint hover:text-coffee'
                      }`}
                    >
                      Todos ({clientes.length})
                    </button>
                    <button
                      type="button"
                      onClick={() => setFiltroRoleUsuario('customer')}
                      className={`px-3 py-1 text-xs font-semibold uppercase tracking-wider rounded transition-colors ${
                        filtroRoleUsuario === 'customer'
                          ? 'bg-forest text-cream shadow-xs'
                          : 'text-coffee-faint hover:text-coffee'
                      }`}
                    >
                      Leitores ({clientes.filter((c) => c.role === 'customer').length})
                    </button>
                    <button
                      type="button"
                      onClick={() => setFiltroRoleUsuario('admin')}
                      className={`px-3 py-1 text-xs font-semibold uppercase tracking-wider rounded transition-colors ${
                        filtroRoleUsuario === 'admin'
                          ? 'bg-forest text-cream shadow-xs'
                          : 'text-coffee-faint hover:text-coffee'
                      }`}
                    >
                      Curadores/Admin ({clientes.filter((c) => c.role === 'admin').length})
                    </button>
                  </div>

                  <button
                    type="button"
                    onClick={handleNovoUsuario}
                    className="px-4 py-2 bg-forest text-cream text-xs uppercase tracking-wider font-semibold rounded-sm hover:bg-forest-soft transition-colors flex items-center gap-1.5 shadow-sm"
                  >
                    <span className="text-gold font-bold text-base leading-none">+</span>
                    Novo Usuário
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left font-body text-sm">
                  <thead className="bg-cream-tint/60 text-[0.72rem] uppercase tracking-[0.16em] text-coffee-faint border-b border-line">
                    <tr>
                      <th className="py-3.5 px-6 font-semibold">Leitor / Usuário</th>
                      <th className="py-3.5 px-6 font-semibold">E-mail</th>
                      <th className="py-3.5 px-6 font-semibold">Perfil</th>
                      <th className="py-3.5 px-6 font-semibold">Status</th>
                      <th className="py-3.5 px-6 font-semibold">Pedidos</th>
                      <th className="py-3.5 px-6 font-semibold">Cadastro</th>
                      <th className="py-3.5 px-6 font-semibold text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line text-coffee-soft">
                    {clientesFiltrados.map((cli) => {
                      const iniciais = (cli.full_name || 'U')
                        .split(' ')
                        .filter(Boolean)
                        .map((n) => n[0])
                        .slice(0, 2)
                        .join('')
                        .toUpperCase()

                      return (
                        <tr key={cli.id} className="hover:bg-cream-deep/40 transition-colors">
                          <td className="py-4 px-6">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-forest text-gold flex items-center justify-center font-bold text-xs shrink-0 shadow-xs">
                                {iniciais}
                              </div>
                              <div>
                                <p className="font-display font-bold text-coffee text-base leading-tight">
                                  {cli.full_name}
                                </p>
                                <p className="font-mono text-[0.7rem] text-coffee-faint">
                                  ID #{cli.id}
                                </p>
                              </div>
                            </div>
                          </td>
                          <td className="py-4 px-6 text-xs text-coffee-soft">{cli.email}</td>
                          <td className="py-4 px-6">
                            <span
                              className={`text-[0.68rem] uppercase tracking-wider font-semibold px-2 py-0.5 rounded ${
                                cli.role === 'admin'
                                  ? 'bg-forest text-cream'
                                  : 'bg-gold/20 text-gold-dark'
                              }`}
                            >
                              {cli.role === 'admin' ? 'Curador (Admin)' : 'Leitor (Cliente)'}
                            </span>
                          </td>
                          <td className="py-4 px-6">
                            <span
                              className={`text-[0.68rem] uppercase tracking-wider font-semibold px-2 py-0.5 rounded ${
                                cli.is_active !== false
                                  ? 'bg-forest-tint text-forest'
                                  : 'bg-red-100 text-red-700'
                              }`}
                            >
                              {cli.is_active !== false ? 'Ativo' : 'Inativo'}
                            </span>
                          </td>
                          <td className="py-4 px-6 text-xs font-semibold text-coffee">
                            {cli.orders_count || 0} pedido(s)
                          </td>
                          <td className="py-4 px-6 text-xs text-coffee-faint">
                            {cli.created_at ? new Date(cli.created_at).toLocaleDateString('pt-BR') : '-'}
                          </td>
                          <td className="py-4 px-6 text-right">
                            <div className="flex justify-end gap-3">
                              <button
                                type="button"
                                onClick={() => handleEditarUsuario(cli)}
                                className="text-xs text-forest hover:text-forest-soft font-medium transition-colors"
                              >
                                Editar
                              </button>
                              <button
                                type="button"
                                onClick={() => handleExcluirUsuario(cli)}
                                className="text-xs text-red-700 hover:text-red-900 font-medium transition-colors"
                              >
                                {cli.is_active === false ? 'Excluir' : 'Desativar'}
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              {clientesFiltrados.length === 0 && (
                <div className="p-12 text-center">
                  <p className="font-display text-lg text-coffee">
                    Nenhum usuário encontrado
                  </p>
                  <p className="mt-1 font-body text-xs text-coffee-faint">
                    Tente ajustar o termo da busca ou o filtro de perfil.
                  </p>
                </div>
              )}
            </section>
          )}

          {/* ===================== ABA: DESCONTOS & CUPONS ===================== */}
          {abaAtiva === 'descontos' && (
            <section className="bg-cream-soft rounded-sm border border-line shadow-sm overflow-hidden">
              <div className="p-6 border-b border-line flex flex-wrap justify-between items-center gap-4">
                <div>
                  <h3 className="font-display text-xl font-bold text-coffee">
                    Cupons de Desconto
                  </h3>
                  <p className="font-body text-xs text-coffee-faint">
                    {cuponsFiltrados.length} cupom(ns) cadastrado(s)
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleNovoCupom}
                  className="px-4 py-2 bg-forest text-cream text-xs uppercase tracking-wider font-semibold rounded-sm hover:bg-forest-soft transition-colors"
                >
                  + Novo Cupom
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left font-body text-sm">
                  <thead className="bg-cream-tint/60 text-[0.72rem] uppercase tracking-[0.16em] text-coffee-faint border-b border-line">
                    <tr>
                      <th className="py-3.5 px-6 font-semibold">Código</th>
                      <th className="py-3.5 px-6 font-semibold">Desconto</th>
                      <th className="py-3.5 px-6 font-semibold">Mín. Compra</th>
                      <th className="py-3.5 px-6 font-semibold">Validade</th>
                      <th className="py-3.5 px-6 font-semibold">Usos</th>
                      <th className="py-3.5 px-6 font-semibold">Status</th>
                      <th className="py-3.5 px-6 font-semibold text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line text-coffee-soft">
                    {cuponsFiltrados.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="py-10 px-6 text-center text-xs text-coffee-faint">
                          Nenhum cupom cadastrado. Use “+ Novo Cupom” para começar.
                        </td>
                      </tr>
                    ) : (
                      cuponsFiltrados.map((cupom) => {
                        const expirado =
                          cupom.valid_until && new Date(cupom.valid_until) < new Date()
                        return (
                          <tr key={cupom.id} className="hover:bg-cream-deep/40 transition-colors">
                            <td className="py-4 px-6 font-mono text-xs font-semibold text-coffee">
                              {cupom.code}
                              {cupom.product_id && (
                                <span className="ml-2 text-[0.65rem] uppercase tracking-wider px-2 py-0.5 bg-cream-deep text-coffee-faint rounded font-body font-semibold">
                                  Produto #{cupom.product_id}
                                </span>
                              )}
                            </td>
                            <td className="py-4 px-6 font-display font-bold text-coffee">
                              {cupom.discount_type === 'fixed'
                                ? `R$ ${Number(cupom.discount_value).toFixed(2).replace('.', ',')}`
                                : `${cupom.discount_value}%`}
                              {cupom.max_discount != null && cupom.discount_type === 'percentage' && (
                                <span className="block text-[0.65rem] font-body font-normal text-coffee-faint">
                                  máx. R$ {Number(cupom.max_discount).toFixed(2).replace('.', ',')}
                                </span>
                              )}
                            </td>
                            <td className="py-4 px-6 text-xs">
                              {cupom.min_purchase != null
                                ? `R$ ${Number(cupom.min_purchase).toFixed(2).replace('.', ',')}`
                                : '—'}
                            </td>
                            <td className="py-4 px-6 text-xs text-coffee-faint">
                              {cupom.valid_until
                                ? new Date(cupom.valid_until).toLocaleDateString('pt-BR')
                                : '—'}
                            </td>
                            <td className="py-4 px-6 text-xs">
                              {cupom.max_uses != null ? `${cupom.max_uses}` : 'Ilimitado'}
                            </td>
                            <td className="py-4 px-6">
                              <span
                                className={`text-xs font-semibold px-2 py-0.5 rounded ${
                                  !cupom.is_active || expirado
                                    ? 'bg-red-100 text-red-800'
                                    : 'bg-forest-tint text-forest'
                                }`}
                              >
                                {!cupom.is_active ? 'Inativo' : expirado ? 'Expirado' : 'Ativo'}
                              </span>
                            </td>
                            <td className="py-4 px-6 text-right whitespace-nowrap">
                              <button
                                type="button"
                                onClick={() => handleEditarCupom(cupom)}
                                className="text-xs text-forest hover:text-forest-soft font-medium transition-colors mr-4"
                              >
                                Editar
                              </button>
                              <button
                                type="button"
                                onClick={() => handleExcluirCupom(cupom)}
                                className="text-xs text-red-700 hover:text-red-900 font-medium transition-colors"
                              >
                                Excluir
                              </button>
                            </td>
                          </tr>
                        )
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* ===================== ABA: CATEGORIAS ===================== */}
          {abaAtiva === 'categorias' && (
            <section className="bg-cream-soft rounded-sm border border-line shadow-sm overflow-hidden">
              <div className="p-6 border-b border-line flex flex-wrap justify-between items-center gap-4">
                <div>
                  <h3 className="font-display text-xl font-bold text-coffee">
                    Categorias do Acervo
                  </h3>
                  <p className="font-body text-xs text-coffee-faint">
                    {categoriasFiltradas.length} categoria(s) cadastrada(s)
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleNovaCategoria}
                  className="px-4 py-2 bg-forest text-cream text-xs uppercase tracking-wider font-semibold rounded-sm hover:bg-forest-soft transition-colors"
                >
                  + Nova Categoria
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left font-body text-sm">
                  <thead className="bg-cream-tint/60 text-[0.72rem] uppercase tracking-[0.16em] text-coffee-faint border-b border-line">
                    <tr>
                      <th className="py-3.5 px-6 font-semibold">ID</th>
                      <th className="py-3.5 px-6 font-semibold">Nome</th>
                      <th className="py-3.5 px-6 font-semibold">Slug</th>
                      <th className="py-3.5 px-6 font-semibold">Descrição</th>
                      <th className="py-3.5 px-6 font-semibold">Status</th>
                      <th className="py-3.5 px-6 font-semibold text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line text-coffee-soft">
                    {categoriasFiltradas.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-10 px-6 text-center text-xs text-coffee-faint">
                          Nenhuma categoria cadastrada. Use “+ Nova Categoria” para começar.
                        </td>
                      </tr>
                    ) : (
                      categoriasFiltradas.map((categoria) => (
                        <tr key={categoria.id} className="hover:bg-cream-deep/40 transition-colors">
                          <td className="py-4 px-6 font-mono text-xs text-coffee">#{categoria.id}</td>
                          <td className="py-4 px-6 font-medium text-coffee">{categoria.name}</td>
                          <td className="py-4 px-6 font-mono text-xs text-coffee-faint">{categoria.slug}</td>
                          <td className="py-4 px-6 text-xs text-coffee-faint max-w-[24rem] truncate">
                            {categoria.description || '—'}
                          </td>
                          <td className="py-4 px-6">
                            <span
                              className={`text-xs font-semibold px-2 py-0.5 rounded ${
                                categoria.is_active !== false
                                  ? 'bg-forest-tint text-forest'
                                  : 'bg-red-100 text-red-800'
                              }`}
                            >
                              {categoria.is_active !== false ? 'Ativa' : 'Inativa'}
                            </span>
                          </td>
                          <td className="py-4 px-6 text-right whitespace-nowrap">
                            <button
                              type="button"
                              onClick={() => handleEditarCategoria(categoria)}
                              className="text-xs text-forest hover:text-forest-soft font-medium transition-colors mr-4"
                            >
                              Editar
                            </button>
                            <button
                              type="button"
                              onClick={() => handleExcluirCategoria(categoria)}
                              className="text-xs text-red-700 hover:text-red-900 font-medium transition-colors"
                            >
                              Excluir
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          )}
          {abaAtiva === 'newsletter' && (
            <section className="bg-cream-soft rounded-sm border border-line shadow-sm overflow-hidden">
              <div className="p-6 border-b border-line flex flex-wrap justify-between items-center gap-4">
                <div>
                  <h3 className="font-display text-xl font-bold text-coffee">
                    Inscritos da Carta do Livreiro
                  </h3>
                  <p className="font-body text-xs text-coffee-faint">
                    {inscritosFiltradas.length} inscrito(s) na newsletter
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left font-body text-sm">
                  <thead className="bg-cream-tint/60 text-[0.72rem] uppercase tracking-[0.16em] text-coffee-faint border-b border-line">
                    <tr>
                      <th className="py-3.5 px-6 font-semibold">ID</th>
                      <th className="py-3.5 px-6 font-semibold">E-mail</th>
                      <th className="py-3.5 px-6 font-semibold">Inscrição</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line text-coffee-soft">
                    {inscritosFiltradas.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="py-10 px-6 text-center text-xs text-coffee-faint">
                          Nenhum inscrito ainda. A newsletter aceita visitantes pela Home.
                        </td>
                      </tr>
                    ) : (
                      inscritosFiltradas.map((inscrito) => (
                        <tr key={inscrito.id} className="hover:bg-cream-deep/40 transition-colors">
                          <td className="py-4 px-6 font-mono text-xs text-coffee">#{inscrito.id}</td>
                          <td className="py-4 px-6 font-medium text-coffee">{inscrito.email}</td>
                          <td className="py-4 px-6 text-xs text-coffee-faint">
                            {inscrito.subscribed_at
                              ? new Date(inscrito.subscribed_at).toLocaleDateString('pt-BR')
                              : '-'}
                          </td>
                        </tr>
                      ))
                    )}
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
                  {livroEditando ? 'Editar Obra do Acervo' : 'Cadastrar Obra no Acervo'}
                </h3>
              </div>
              <button
                type="button"
                onClick={fecharModalLivro}
                className="text-coffee-faint hover:text-coffee transition-colors"
              >
                <CloseIcon />
              </button>
            </div>

            <form onSubmit={handleSalvarLivro} className="mt-6 space-y-4 font-body">
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
                  Descrição Curta{livroEditando ? ' (em branco mantém a atual)' : ''}
                </label>
                <textarea
                  rows="2"
                  placeholder="Breve descrição editorial da obra..."
                  value={novoDescricao}
                  onChange={(e) => setNovoDescricao(e.target.value)}
                  className="w-full campo py-2 text-xs"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                    Desconto (%)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    placeholder="0"
                    value={novoDesconto}
                    onChange={(e) => setNovoDesconto(e.target.value)}
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

              {/* Flags de Curadoria */}
              <div className="flex flex-wrap gap-6 pt-4 border-t border-line/60">
                <label className="flex items-center gap-2.5 cursor-pointer text-xs uppercase tracking-wider font-semibold text-coffee-soft hover:text-coffee">
                  <input
                    type="checkbox"
                    checked={novoDestaque}
                    onChange={(e) => setNovoDestaque(e.target.checked)}
                    className="h-4 w-4 rounded border-line-strong text-forest focus:ring-forest"
                  />
                  <span>Marcar como Destaque</span>
                </label>
                <label className="flex items-center gap-2.5 cursor-pointer text-xs uppercase tracking-wider font-semibold text-coffee-soft hover:text-coffee">
                  <input
                    type="checkbox"
                    checked={novoBestseller}
                    onChange={(e) => setNovoBestseller(e.target.checked)}
                    className="h-4 w-4 rounded border-line-strong text-forest focus:ring-forest"
                  />
                  <span>Marcar como Mais Vendido (Best-Seller)</span>
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-line mt-6">
                <button
                  type="button"
                  onClick={fecharModalLivro}
                  className="px-4 py-2 border border-line-strong text-coffee-soft text-xs uppercase tracking-wider font-semibold rounded-sm hover:bg-cream-deep transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={salvandoLivro}
                  className="px-6 py-2 bg-forest hover:bg-forest-soft text-cream text-xs uppercase tracking-wider font-semibold rounded-sm transition-colors shadow-sm disabled:opacity-50"
                >
                  {salvandoLivro
                    ? 'Salvando...'
                    : livroEditando
                      ? 'Salvar Alterações'
                      : 'Adicionar ao Catálogo'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Novo/Editar Cupom */}
      {modalCupom && (
        <ModalCupom
          onClose={() => setModalCupom(false)}
          onSalvar={handleSalvarCupom}
          cupomParaEditar={cupomEditando}
          produtos={livros}
          usuarios={clientes}
          vinculosIniciais={vinculosCupom}
        />
      )}

      {/* Modal: Nova/Editar Categoria */}
      {modalCategoria && (
        <ModalCategoria
          onClose={() => setModalCategoria(false)}
          onSalvar={handleSalvarCategoria}
          categoriaParaEditar={categoriaEditando}
        />
      )}

      {/* Modal: Novo/Editar Usuário */}
      {modalUsuario && (
        <ModalUsuario
          onClose={() => setModalUsuario(false)}
          onSalvar={handleSalvarUsuario}
          usuarioParaEditar={usuarioEditando}
        />
      )}
    </div>
  )
}
