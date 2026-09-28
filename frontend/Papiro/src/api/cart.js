import api from './client'

/**
 * Endpoints do carrinho.
 *
 * Contrato atual do backend (FastAPI):
 *   POST   /cart/create                        -> cria o carrinho do usuário.
 *   GET    /cart/cart/me                       -> busca o carrinho (com itens).
 *   POST   /cart/{cart_id}/items/add           -> adiciona item.
 *   PATCH  /cart/{cart_id}/items/update/{id}   -> define a quantidade (0 remove).
 *   DELETE /cart/{cart_id}/items/delete/{id}   -> remove o item.
 *   DELETE /cart/{cart_id}/items/clear         -> esvazia o carrinho.
 *
 * Endpoints removidos na Parte 5 (órfãos, sem uso no front):
 *   GET /cart/get/{id}, GET /cart/items/{id},
 *   PATCH /cart/{id}/items/decrease/{id} e DELETE /cart/delete/{id}.
 * Para decrementar, use `atualizarQuantidade` com o valor absoluto.
 *
 * AUTENTICAÇÃO: todas as rotas exigem Bearer token e derivam o `user_id` do
 * usuário autenticado (`Depends(get_current_user)`). O `user_id` NÃO vai mais
 * na query — o interceptor do client anexa o token sozinho.
 */
export const cartService = {
  /** Cria o carrinho do usuário. Falha (400/409) se já existir. */
  async criar() {
    const { data } = await api.post('/cart/create')
    return data
  },

  /** Busca o carrinho do usuário autenticado (com itens). */
  async obter() {
    const { data } = await api.get('/cart/cart/me')
    return data
  },

  /** Adiciona um produto; o backend soma se o item já existir. */
  async adicionarItem(cartId, productId, quantity = 1) {
    const { data } = await api.post(`/cart/${cartId}/items/add`, {
      product_id: productId,
      quantity,
    })
    return data
  },

  /** Define a quantidade absoluta de um item. */
  async atualizarQuantidade(cartId, itemId, quantity) {
    const { data } = await api.patch(
      `/cart/${cartId}/items/update/${itemId}`,
      null,
      { params: { quantity } },
    )
    return data
  },

  /** Remove um item. */
  async removerItem(cartId, itemId) {
    const { data } = await api.delete(`/cart/${cartId}/items/delete/${itemId}`)
    return data
  },

  /** Esvazia o carrinho (mantém o carrinho). */
  async limpar(cartId) {
    const { data } = await api.delete(`/cart/${cartId}/items/clear`)
    return data
  },
}

export default cartService
