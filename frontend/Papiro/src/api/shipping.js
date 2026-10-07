import api from './client'

/**
 * Endpoints de frete (Melhor Envio).
 *
 * Contrato atual do backend (FastAPI):
 *   POST /shipping/calculate/{order_id} -> cota o frete de um pedido.
 *                                         Retorno: ShippingCalculateResponse.
 *   POST /shipping/apply                -> aplica o frete escolhido no pedido
 *                                         e recalcula o total.
 *
 * AUTENTICAÇÃO: as duas rotas exigem Bearer token (o interceptor do `client`
 * anexa sozinho) e derivam o ``user_id`` do usuário autenticado.
 */
export const shippingService = {
  /**
   * Cota o frete de um pedido (deve existir no fluxo de finalização).
   * @param {number} orderId
   * @returns {Promise<{order_id:number, offers:Array, best_offer_index:number|null, is_real:boolean}>}
   */
  async calcular(orderId) {
    const { data } = await api.post(`/shipping/calculate/${orderId}`)
    return data
  },

  /**
   * Aplica o valor de frete escolhido a um pedido.
   * @param {{ order_id:number, price:number, delivery_time?:number|null }} payload
   * @returns {Promise<{order_id:number, applied:boolean, shipping_cost:number, total:number, status:string}>}
   */
  async aplicar(payload) {
    const { data } = await api.post('/shipping/apply', payload)
    return data
  },
}

export default shippingService