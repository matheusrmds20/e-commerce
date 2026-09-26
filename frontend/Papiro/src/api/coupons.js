import api from './client'
import { toApiError } from './client'

/**
 * Endpoints de cupons de desconto.
 *
 * Contrato do backend (FastAPI):
 *   POST   /coupons/create        -> cria (201). Corpo: CouponCreate.
 *   GET    /coupons/list          -> CouponResponse[]
 *   PATCH  /coupons/update/{id}   -> atualiza. Corpo: CouponUpdate.
 *   DELETE /coupons/delete/{id}   -> exclui. Retorna CouponResponse.
 *
 * Observação: `CouponService.get_all` lança ValueError quando não há cupons e
 * o handler global converte em HTTP 400. Em contexto de listagem isso é
 * "lista vazia", não erro — `listarOuVazio` encapsula essa regra (mesmo padrão
 * de `products.js`).
 *
 * `CouponCreate` aceita:
 *   { code, product_id?, discount_type, discount_value, min_purchase?,
 *     max_discount?, valid_until, max_uses?, is_active }
 * `discount_type` ∈ 'percentage' | 'fixed'. `valid_until` em ISO 8601.
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
    // 400/404 = "No coupons found" no service. 401/403/500/timeout = falha real.
    if (apiError.status === 400 || apiError.status === 404) return []
    throw apiError
  }
}

export const couponService = {
  /** Lista todos os cupons (vazio quando não há nenhum cadastrado). */
  async listar() {
    return listarOuVazio(async () => {
      const { data } = await api.get('/coupons/list')
      return data
    })
  },

  /**
   * Cria um cupom.
   * @param {object} cupom CouponCreate
   */
  async criar(cupom) {
    const { data } = await api.post('/coupons/create', cupom)
    return data
  },

  /**
   * Atualiza um cupom existente.
   * @param {number} couponId
   * @param {object} cupom CouponUpdate (campos parciais)
   */
  async atualizar(couponId, cupom) {
    const { data } = await api.patch(`/coupons/update/${couponId}`, cupom)
    return data
  },

  /**
   * Exclui um cupom.
   * @param {number} couponId
   */
  async excluir(couponId) {
    const { data } = await api.delete(`/coupons/delete/${couponId}`)
    return data
  },
}

export default couponService
