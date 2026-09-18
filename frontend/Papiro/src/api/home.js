import productService from './products'
import categoryService from './categories'
import reviewService from './reviews'
import { toApiError } from './client'
import { mediaAvaliacoes } from './adapters'

/**
 * Composição dos dados da Home a partir dos endpoints existentes.
 *
 * A página monta as seções assim:
 *
 * - **Catálogo base:** `GET /products/list` (via `/products/active/true`)
 *   → alimenta as Coleções (categorias), o fallback de destaques e a
 *   Recomendação da Casa.
 * - **Destaques:** `GET /products/featured` (`is_featured = true`) → alimenta
 *   a grade "Livros em Destaque". Se a curadoria não marcou nada (200 com
 *   `[]`), cai no fallback: os primeiros itens do catálogo. Isso mantém a Home
 *   apresentável em ambiente sem curadoria, sem esconder a seção.
 * - **Mais vendidos:** `GET /products/bestsellers` (`is_bestseller = true`)
 *   → exposto em `maisVendidos` para uso futuro. Sem fallback: se vazio, é
 *   porque nada foi marcado.
 * - **Ofertas:** `GET /products/discount/{pct}` → alimenta o carrossel de
 *   Promoções. Se nenhum produto tiver desconto, o carrossel fica vazio.
 * - **Categorias:** `GET /categories/list` → alimenta as Coleções.
 * - **Recomendação:** escolhe um produto e busca `GET /reviews/product/{id}`
 *   para calcular a nota média.
 *
 * Regras de degradação (para a Home nunca quebrar por completo):
 * - Falha numa seção isolada não derruba as outras (`Promise.allSettled`).
 * - Catálogo vazio → seções caem para estado vazio explícito.
 *
 * @typedef {Object} HomeData
 * @property {Array} catalogo        ProductResponse[] ativos (normalizados)
 * @property {Array} destaques       grade de destaques (curadoria ou fallback)
 * @property {Array} maisVendidos    curadoria de mais vendidos (pode ser [])
 * @property {Array} ofertas         produtos com desconto
 * @property {Array} categorias      CategoryResponse[] enriquecidas com `total`
 * @property {Object|null} recomendacao { produto, avaliacoes, notaMedia }
 */

/** Número mínimo de desconto (%) para um produto entrar no carrossel. */
const DESCONTO_MINIMO = 1

/** Limite da grade de destaques da Home. */
const LIMITE_DESTAQUES = 8

/**
 * Normaliza um produto do catálogo para o shape dos cards da Home.
 * @param {object} p ProductResponse
 */
export function produtoParaCard(p) {
  const temDesconto = Number(p.discount_pct ?? 0) > 0
  return {
    id: p.id,
    titulo: p.title ?? '',
    autor: p.author ?? '',
    categoriaId: p.category_id,
    preco: p.price ?? 0,
    precoOriginal: temDesconto ? p.price : null,
    precoFinal: temDesconto
      ? Number(((p.price ?? 0) * (1 - p.discount_pct / 100)).toFixed(2))
      : (p.price ?? 0),
    desconto: temDesconto ? `${p.discount_pct}%` : null,
    descricao: p.description ?? '',
    sinopse: p.synopsis ?? null,
    imagem: p.image_url ?? '',
    estoque: p.stock_qty ?? 0,
    ativo: p.is_active ?? true,
    // Flags de curadoria — usadas para rotular os cards e priorizar a
    // recomendação da casa (um destaque é melhor vitrine que um item comum).
    destaque: p.is_featured ?? false,
    maisVendido: p.is_bestseller ?? false,
    criadoEm: p.created_at ?? null,
  }
}

/** Normaliza uma categoria para o shape das Coleções. */
export function categoriaParaColecao(c) {
  return {
    id: c.id,
    titulo: c.name ?? '',
    slug: c.slug ?? '',
    subtitulo: c.description ?? '',
    imagem: c.image_url ?? '',
  }
}

/**
 * Carrega tudo que a Home precisa.
 * @returns {Promise<HomeData>}
 */
export async function carregarHome() {
  const [
    catalogoResp,
    destaquesResp,
    maisVendidosResp,
    ofertasResp,
    categoriasResp,
  ] = await Promise.allSettled([
    productService.listarPorAtivo(true),
    productService.listarDestaques(LIMITE_DESTAQUES),
    productService.listarMaisVendidos(LIMITE_DESTAQUES),
    productService.listarPorDesconto(DESCONTO_MINIMO),
    categoryService.listar(),
  ])

  // O catálogo é a única seção sem a qual a Home não faz sentido.
  if (catalogoResp.status === 'rejected') {
    throw toApiError(catalogoResp.reason)
  }

  const catalogo = (catalogoResp.value ?? []).map(produtoParaCard)

  // Destaques: usa a curadoria (`is_featured`). Quando ela não cobre nada,
  // cai no fallback dos primeiros itens do catálogo para a grade não ficar
  // vazia. Falha na chamada também degrada para o fallback.
  const destaquesCuradoria =
    destaquesResp.status === 'fulfilled' && destaquesResp.value?.length
      ? destaquesResp.value.map(produtoParaCard)
      : null

  const destaques =
    destaquesCuradoria ?? catalogo.slice(0, LIMITE_DESTAQUES)

  // Mais vendidos: só curadoria, sem fallback (não há como inferir).
  const maisVendidos =
    maisVendidosResp.status === 'fulfilled'
      ? (maisVendidosResp.value ?? []).map(produtoParaCard)
      : []

  // Ordenação da grade: dentro dos destaques, os mais vendidos vêm primeiro.
  // Isso dá uso à segunda flag sem criar uma seção nova na Home.
  const idsMaisVendidos = new Set(maisVendidos.map((p) => p.id))
  const destaquesOrdenados = [...destaques].sort((a, b) => {
    const aTop = idsMaisVendidos.has(a.id) ? 0 : 1
    const bTop = idsMaisVendidos.has(b.id) ? 0 : 1
    return aTop - bTop
  })

  // Ofertas: usa o endpoint de desconto; se vazio, deriva do próprio catálogo.
  const ofertasBrutas =
    ofertasResp.status === 'fulfilled' && ofertasResp.value?.length
      ? ofertasResp.value
      : catalogo.filter((p) => p.desconto)

  const ofertas = ofertasBrutas.map(produtoParaCard)

  // Categorias: o service responde 400 quando vazio; nesse caso a lista é [].
  // O backend não expõe contagem por categoria, então derivamos do catálogo.
  const contagemPorCategoria = catalogo.reduce((acc, p) => {
    acc[p.categoriaId] = (acc[p.categoriaId] ?? 0) + 1
    return acc
  }, {})

  const categorias =
    categoriasResp.status === 'fulfilled'
      ? (categoriasResp.value ?? [])
          .map((c) => ({
            ...categoriaParaColecao(c),
            total: contagemPorCategoria[c.id] ?? 0,
          }))
          // Só mostra coleções que têm livros — evita cards vazios.
          .filter((c) => c.total > 0)
      : []

  // Recomendação da Casa: prefere um destaque com estoque — é a melhor
  // vitrine. Sem destaques marcados, cai no primeiro item com estoque.
  const recomendacao = await montarRecomendacao(destaques, catalogo)

  return {
    catalogo,
    destaques: destaquesOrdenados,
    maisVendidos,
    ofertas,
    categorias,
    recomendacao,
  }
}

/**
 * Escolhe um produto e busca as avaliações para calcular a média.
 * Nunca lança: falha de avaliações vira `avaliacoes: []` e nota 0.
 *
 * Ordem de preferência: destaque com estoque → destaque → item com estoque →
 * primeiro do catálogo.
 *
 * @param {Array} destaques
 * @param {Array} catalogo
 */
async function montarRecomendacao(destaques, catalogo) {
  // `destaques` normalmente é um subconjunto do catálogo; sem deduplicar, os
  // mesmos produtos apareceriam duas vezes na lista de candidatos.
  const vistos = new Set()
  const candidatos = [...destaques, ...catalogo].filter((p) => {
    if (vistos.has(p.id)) return false
    vistos.add(p.id)
    return true
  })

  const produto =
    candidatos.find((p) => p.destaque && p.estoque > 0) ??
    candidatos.find((p) => p.destaque) ??
    candidatos.find((p) => p.estoque > 0) ??
    candidatos[0] ??
    null
  if (!produto) return null

  let avaliacoes
  try {
    avaliacoes = (await reviewService.listarPorProduto(produto.id)) ?? []
  } catch {
    avaliacoes = []
  }

  return {
    produto,
    avaliacoes,
    notaMedia: mediaAvaliacoes(avaliacoes),
  }
}

export default { carregarHome, produtoParaCard, categoriaParaColecao }
