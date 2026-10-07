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
   * Cota o frete do carrinho do usuário por CEP, SEM criar pedido.
   * Usado no fluxo de checkout antes do pagamento.
   * @param {{ postal_code: string }} payload
   * @returns {Promise<{postal_code:string, offers:Array, best_offer_index:number|null, is_real:boolean, fallback_reason?:string|null}>}
   */
  async quotar({ postal_code }) {
    const { data } = await api.post('/shipping/quote', { postal_code })
    return data
  },

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