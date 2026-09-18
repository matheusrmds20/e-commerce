import productService from './products'
import categoryService from './categories'
import reviewService from './reviews'
import { toApiError } from './client'
import { mediaAvaliacoes } from './adapters'

/**
 * Composição dos dados da Home a partir dos endpoints existentes.
 *
 * O backend não possui um endpoint dedicado de vitrine (`/home`), então a
 * página monta as seções assim:
 *
 * - **Catálogo base:** `GET /products/list` → alimenta os Livros em Destaque,
 *   as Coleções (categorias) e a Recomendação da Casa.
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
 * @property {Array} catalogo        ProductResponse[] ativos
 * @property {Array} ofertas         ProductResponse[] com desconto
 * @property {Array} categorias      CategoryResponse[]
 * @property {Object|null} recomendacao { produto, avaliacoes }
 * @property {Object|null} erro      Erro global (só quando o catálogo falha)
 */

/** Número mínimo de desconto (%) para um produto entrar no carrossel. */
const DESCONTO_MINIMO = 1

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
  const [catalogoResp, ofertasResp, categoriasResp] = await Promise.allSettled([
    productService.listarPorAtivo(true),
    productService.listarPorDesconto(DESCONTO_MINIMO),
    categoryService.listar(),
  ])

  // O catálogo é a única seção sem a qual a Home não faz sentido.
  if (catalogoResp.status === 'rejected') {
    throw toApiError(catalogoResp.reason)
  }

  const catalogo = (catalogoResp.value ?? []).map(produtoParaCard)

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

  // Recomendação da Casa: primeiro item do catálogo + nota média real.
  const recomendacao = await montarRecomendacao(catalogo)

  return { catalogo, ofertas, categorias, recomendacao }
}

/**
 * Escolhe um produto e busca as avaliações para calcular a média.
 * Nunca lança: falha de avaliações vira `avaliacoes: []` e nota 0.
 * @param {Array} catalogo
 */
async function montarRecomendacao(catalogo) {
  const produto =
    catalogo.find((p) => p.estoque > 0) ?? catalogo[0] ?? null
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
