import api from './client'

/**
 * Endpoints de pedidos.
 *
 * Contrato atual do backend (FastAPI):
 *   POST  /orders/create       -> cria o pedido (201). Corpo: OrderCreate.
 *   GET   /orders/list         -> lista os pedidos do usuário autenticado.
 *   PATCH /orders/update/{id}  -> atualiza um pedido (usado para cancelar).
 *
 * AUTENTICAÇÃO: todas as rotas exigem Bearer token e derivam o `user_id` do
 * usuário autenticado (`Depends(get_current_user)`). Não se envia mais
 * `user_id` na query — o interceptor do client anexa o token sozinho.
 *
 * `OrderCreate` aceita:
 *   { address_id, coupon_id?, notes?, items: [{ product_id, quantity }] }
 */
export const orderService = {
  /**
   * Cria um pedido para o usuário autenticado.
   * @param {{ address_id: number, coupon_id?: number|null, notes?: string, items: {product_id: number, quantity: number}[] }} pedido
   */
  async criar(pedido) {
    const { data } = await api.post('/orders/create', pedido)
    return data
  },

  /** Lista todos os pedidos do usuário autenticado. */
  async listar() {
    const { data } = await api.get('/orders/list')
    return data
  },

  /**
   * Cancela um pedido do usuário autenticado.
   *
   * Usa `PATCH /orders/update/{id}` com `{ status: 'cancelled' }`. O backend
   * valida a posse (403) e recusa cancelar um pedido já cancelado (400).
   * @param {number} orderId
   */
  async cancelar(orderId) {
    const { data } = await api.patch(`/orders/update/${orderId}`, {
      status: 'cancelled',
    })
    return data
  },
}

export default orderService
