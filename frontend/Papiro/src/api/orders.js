import api from './client'

/**
 * Endpoints de pedidos.
 *
 * Contrato atual do backend (FastAPI):
 *   POST   /orders/create        -> cria o pedido (201). Corpo: OrderCreate.
 *   GET    /orders/list          -> lista os pedidos do usuário autenticado.
 *   GET    /orders/get/{id}      -> busca um pedido.
 *   GET    /orders/items/{id}    -> lista os itens de um pedido.
 *   PATCH  /orders/update/{id}   -> atualiza (status, endereço, itens...).
 *   DELETE /orders/delete/{id}   -> exclui.
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

  /** Busca um pedido pelo ID. */
  async obter(orderId) {
    const { data } = await api.get(`/orders/get/${orderId}`)
    return data
  },

  /** Lista os itens de um pedido. */
  async itens(orderId) {
    const { data } = await api.get(`/orders/items/${orderId}`)
    return data
  },
}

export default orderService
