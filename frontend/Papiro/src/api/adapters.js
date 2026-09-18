/**
 * Adaptadores entre o formato do backend (snake_case, inglês) e o formato que
 * os componentes visuais do Papiro consomem (português).
 *
 * Motivo: `ProductResponse` traz `title`, `price`, `image_url`, `author`; os
 * componentes (`ItemCarrinho`, `CartaoRecomendado`) esperam `titulo`, `preco`,
 * `imagem`, `autor`. Manter a tradução aqui evita espalhar `product.title ??
 * product.titulo` por todo o JSX.
 */

/** Preço final considerando desconto percentual. */
export function precoFinal(produto) {
  const base = produto?.price ?? produto?.preco ?? 0
  const desconto = produto?.discount_pct ?? 0
  if (!desconto) return base
  return Number((base * (1 - desconto / 100)).toFixed(2))
}

/**
 * Converte um item do carrinho da API para o shape dos componentes.
 * @param {object} item CartItemResponse: { id, product_id, quantity, product }
 */
export function itemCarrinhoParaView(item) {
  const produto = item.product ?? {}

  return {
    // `id` do item é o que identifica a linha na API (não o product_id).
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

/** Converte uma lista de itens do carrinho. */
export function itensParaView(itens) {
  return (itens ?? []).map(itemCarrinhoParaView)
}

/**
 * Converte um produto do catálogo para o shape do card de recomendação.
 * @param {object} produto ProductResponse
 */
export function produtoParaRecomendacao(produto) {
  return {
    // Nas recomendações o id É o product_id (vai direto para /items/add).
    id: produto.id,
    titulo: produto.title ?? '',
    autor: produto.author ?? '',
    preco: precoFinal(produto),
    imagem: produto.image_url ?? '',
  }
}

/**
 * Converte um produto do catálogo no shape da página de detalhe.
 * @param {object} produto ProductResponse
 */
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

/**
 * Converte uma avaliação da API no shape consumido pela lista de avaliações.
 * @param {object} review ReviewResponse
 * @param {object} [usuario] Usuário autenticado (para marcar autoria própria)
 */
export function avaliacaoParaView(review, usuario = null) {
  return {
    id: review.id,
    userId: review.user_id,
    produtoId: review.product_id,
    nota: review.rating ?? 0,
    texto: review.comment ?? '',
    criadoEm: review.created_at,
    // O backend não devolve o nome do autor; usamos o usuário logado quando a
    // avaliação é dele. Avaliações de terceiros aparecem como "Leitor Papiro".
    nome:
      usuario && review.user_id === usuario.id
        ? (usuario.full_name ?? 'Você')
        : 'Leitor Papiro',
    proprio: Boolean(usuario && review.user_id === usuario.id),
  }
}

/**
 * Média das notas de uma lista de avaliações.
 * @param {Array<{rating?: number, nota?: number}>} avaliacoes
 */
export function mediaAvaliacoes(avaliacoes) {
  const notas = (avaliacoes ?? [])
    .map((a) => a.rating ?? a.nota ?? 0)
    .filter((n) => n > 0)
  if (!notas.length) return 0
  return Number(
    (notas.reduce((acc, n) => acc + n, 0) / notas.length).toFixed(1),
  )
}

/** Formata em Real brasileiro. */
export const formatarPreco = (valor) =>
  Number(valor ?? 0).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })

/**
 * Totais do carrinho.
 * Regra atual do front: frete grátis a partir de R$ 150, senão R$ 24,90.
 */
export function calcularTotais(itens) {
  const subtotal = itens.reduce(
    (acc, item) => acc + item.preco * item.quantidade,
    0,
  )
  const frete = subtotal === 0 || subtotal >= 150 ? 0 : 24.9
  return { subtotal, frete, total: subtotal + frete }
}

/**
 * Converte os itens do carrinho (view) no payload de `OrderItemCreate`.
 * @param {Array<{productId: number, quantidade: number}>} itens
 */
export function itensParaOrderPayload(itens) {
  return (itens ?? []).map((item) => ({
    product_id: item.productId,
    quantity: item.quantidade,
  }))
}

/**
 * Converte a resposta do backend (`OrderResponse`) no shape da tela.
 * @param {object} order OrderResponse
 */
export function pedidoParaView(order) {
  return {
    id: order.id,
    status: order.status,
    subtotal: order.subtotal,
    desconto: order.discount_amount,
    frete: order.shipping_cost,
    total: order.total,
    criadoEm: order.created_at,
    observacoes: order.notes ?? '',
    itens: (order.order_items ?? []).map((item) => ({
      id: item.id,
      productId: item.product_id,
      quantidade: item.quantity,
      preco: item.price,
    })),
  }
}
