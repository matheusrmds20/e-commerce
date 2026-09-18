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
}

export default productService
