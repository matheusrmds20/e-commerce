
export function precoFinal(produto) {
  const base = produto?.price ?? produto?.preco ?? 0
  const desconto = produto?.discount_pct ?? 0
  if (!desconto) return base
  return Number((base * (1 - desconto / 100)).toFixed(2))
}


export function itemCarrinhoParaView(item) {
  const produto = item.product ?? {}

  return {

    id: item.id,
    productId: item.product_id,
    quantidade: item.quantity,
    titulo: produto.title ?? '',
    autor: produto.author ?? '',
    preco: precoFinal(produto),
    precoOriginal: produto.discount_pct > 0 ? produto.price : null,
    imagem: produto.image_url ?? '',
    stockQty: produto.stock_qty ?? 0,
  }
}


export function itensParaView(itens) {
  return (itens ?? []).map(itemCarrinhoParaView)
}



export function produtoParaRecomendacao(produto) {
  return {

    id: produto.id,
    titulo: produto.title ?? '',
    autor: produto.author ?? '',
    preco: precoFinal(produto),
    imagem: produto.image_url ?? '',
  }
}


export function produtoParaDetalhe(produto) {
  const preco = precoFinal(produto)
  const precoAntigo = produto.discount_pct > 0 ? produto.price : null

  return {
    id: produto.id,
    titulo: produto.title ?? '',
    subtitulo: produto.synopsis ?? produto.description ?? '',
    autor: produto.author ?? '',
    editora: produto.publisher ?? null,
    isbn: produto.isbn ?? null,
    anoPublicacao: produto.publication_year ?? null,
    paginas: produto.pages ?? null,
    idioma: produto.language ?? null,
    descricao: (produto.description ?? '')
      .split(/\n\n+/)
      .map((p) => p.trim())
      .filter(Boolean),
    sinopse: produto.synopsis ?? null,
    nota: 0,
    totalAvaliacoes: 0,
    preco,
    precoAntigo,
    desconto:
      produto.discount_pct > 0 ? `${produto.discount_pct}%` : null,
    imagens: produto.image_url ? [produto.image_url] : [],
    stockQty: produto.stock_qty ?? 0,
    isActive: produto.is_active ?? true,
  }
}


export function avaliacaoParaView(review, usuario = null) {
  return {
    id: review.id,
    userId: review.user_id,
    produtoId: review.product_id,
    nota: review.rating ?? 0,
    texto: review.comment ?? '',
    criadoEm: review.created_at,
    nome:
      usuario && review.user_id === usuario.id
        ? (usuario.full_name ?? 'Você')
        : 'Leitor Papiro',
    proprio: Boolean(usuario && review.user_id === usuario.id),
  }
}


export function mediaAvaliacoes(avaliacoes) {
  const notas = (avaliacoes ?? [])
    .map((a) => a.rating ?? a.nota ?? 0)
    .filter((n) => n > 0)
  if (!notas.length) return 0
  return Number(
    (notas.reduce((acc, n) => acc + n, 0) / notas.length).toFixed(1),
  )
}


export const formatarPreco = (valor) =>
  Number(valor ?? 0).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })


export function calcularTotais(itens) {
  const subtotal = itens.reduce(
    (acc, item) => acc + item.preco * item.quantidade,
    0,
  )
  return { subtotal, total: subtotal }
}

