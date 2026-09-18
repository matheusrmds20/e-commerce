import api from './client'
import { toApiError } from './client'

/**
 * Endpoints do catálogo (públicos).
 *
 * Contrato do backend (FastAPI):
 *   GET /products/list                     -> ProductResponse[]
 *   GET /products/get/{id}                 -> ProductResponse
 *   GET /products/category/{category_id}   -> ProductResponse[]
 *   GET /products/discount/{discount_pct}  -> ProductResponse[]
 *   GET /products/active/{is_active}       -> ProductResponse[]
 *
 * Observação importante: os services do backend lançam ValueError quando a
 * consulta não encontra nada, e o handler global converte isso em HTTP 400
 * com `code = "VALIDATION_ERROR"` (ou similar). Em contexto de listagem isso
 * significa "lista vazia", não "erro" — `listarOuVazio` encapsula essa regra.
 */

/**
 * Executa uma listagem e devolve `[]` quando o backend responde "nada
 * encontrado". Qualquer outra falha (rede, 500) é propagada.
 * @param {() => Promise<Array>} fn
 */
async function listarOuVazio(fn) {
  try {
    return (await fn()) ?? []
  } catch (error) {
    const apiError = toApiError(error)
    // 400/404 = "No products found" no service. 401/403/500/timeout = falha real.
    if (apiError.status === 400 || apiError.status === 404) return []
    throw apiError
  }
}

export const productService = {
  /** Lista todos os produtos (vazio quando o catálogo não tem itens). */
  async listar() {
    return listarOuVazio(async () => {
      const { data } = await api.get('/products/list')
      return data
    })
  },

  /** Busca um produto pelo ID. */
  async obter(productId) {
    const { data } = await api.get(`/products/get/${productId}`)
    return data
  },

  /** Lista produtos por categoria. */
  async listarPorCategoria(categoryId) {
    return listarOuVazio(async () => {
      const { data } = await api.get(`/products/category/${categoryId}`)
      return data
    })
  },

  /** Lista produtos com ao menos `discountPct` de desconto. */
  async listarPorDesconto(discountPct) {
    return listarOuVazio(async () => {
      const { data } = await api.get(`/products/discount/${discountPct}`)
      return data
    })
  },

  /** Lista produtos por status de ativação. */
  async listarPorAtivo(isActive = true) {
    return listarOuVazio(async () => {
      const { data } = await api.get(`/products/active/${isActive}`)
      return data
    })
  },

  /**
   * Lista os produtos em destaque da vitrine (`is_featured = true`).
   *
   * Diferença de contrato em relação às demais listagens: o backend responde
   * 200 com `[]` quando não há destaques marcados — lista vazia NÃO é erro.
   * Por isso, aqui não usamos `listarOuVazio`; um 200 vazio já é a resposta
   * esperada e o fallback é responsabilidade do chamador (`home.js`).
   * @param {number} [limite] 1..100
   */
  async listarDestaques(limite) {
    const { data } = await api.get('/products/featured', {
      params: limite ? { limit: limite } : undefined,
    })
    return data ?? []
  },

  /**
   * Lista os produtos mais vendidos da vitrine (`is_bestseller = true`).
   * Mesmo contrato de `listarDestaques`: vazio é 200 com `[]`.
   * @param {number} [limite] 1..100
   */
  async listarMaisVendidos(limite) {
    const { data } = await api.get('/products/bestsellers', {
      params: limite ? { limit: limite } : undefined,
    })
    return data ?? []
  },

  /**
   * Catálogo paginado — envelope `{ data, meta }`.
   *
   * `meta` traz `page`, `per_page`, `total` e `total_pages`, permitindo montar
   * a navegação sem uma segunda chamada de contagem. Quando `categoryId` é
   * informado, o backend filtra **antes** de paginar, então `meta.total`
   * reflete a categoria e não o catálogo inteiro.
   *
   * @param {{page?: number, perPage?: number, categoryId?: number}} [opcoes]
   * @returns {Promise<{data: Array, meta: object}>}
   */
  async listarPaginado({ page = 1, perPage = 20, categoryId } = {}) {
    const { data } = await api.get('/products/paginated', {
      params: {
        page,
        per_page: perPage,
        ...(categoryId ? { category_id: categoryId } : {}),
      },
    })
    return data
  },

  /**
   * Recomendações para o carrinho, já filtradas no servidor.
   *
   * Substitui o padrão de baixar o catálogo inteiro e filtrar em memória:
   * o `exclude` evita rebaixar produtos que já estão na sacola.
   *
   * @param {Array<number>} [excludeIds] ids a excluir (itens já na sacola)
   * @param {number} [limite] 1..50
   */
  async recomendacoes(excludeIds = [], limite = 4) {
    const { data } = await api.get('/products/recommendations', {
      params: {
        ...(excludeIds.length ? { exclude: excludeIds.join(',') } : {}),
        limit: limite,
      },
    })
    return data ?? []
  },
}

export default productService
