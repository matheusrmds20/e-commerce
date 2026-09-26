import api from './client'

/**
 * Endpoints de wishlist (lista de desejos).
 *
 * Contrato atual do backend (FastAPI):
 *   POST   /wishlists/create            -> adiciona produto (201). Corpo: { product_id }
 *   GET    /wishlists/list?user_id=X    -> itens da wishlist do usuário
 *   GET    /wishlists/get/{id}          -> busca um item
 *   DELETE /wishlists/delete/{id}       -> remove um item
 *
 * OBS: ao contrário das outras rotas autenticadas, o backend da wishlist
 * ainda recebe o `user_id` via query param — o interceptor anexa o token,
 * mas o `user_id` precisa ser enviado explicitamente.
 */
export const wishlistService = {
  /** Adiciona um produto à wishlist do usuário. */
  async adicionar(userId, productId) {
    const { data } = await api.post(
      '/wishlists/create',
      { product_id: productId },
      { params: { user_id: userId } },
    )
    return data
  },

  /** Lista os itens da wishlist do usuário ([] quando vazia). */
  async listar(userId) {
    try {
      const { data } = await api.get('/wishlists/list', {
        params: { user_id: userId },
      })
      return Array.isArray(data) ? data : []
    } catch (error) {
      if (error?.status === 404 || error?.code === 'WISHLIST_NOT_FOUND') {
        return []
      }
      throw error
    }
  },

  /** Remove um item da wishlist pelo ID do item. */
  async excluir(userId, wishlistId) {
    const { data } = await api.delete(`/wishlists/delete/${wishlistId}`, {
      params: { user_id: userId },
    })
    return data
  },
}

export default wishlistService
