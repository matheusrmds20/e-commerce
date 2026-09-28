import api from './client'

/**
 * Endpoints de wishlist (lista de desejos).
 *
 * Contrato atual do backend (FastAPI):
 *   POST   /wishlists/create            -> adiciona produto (201). Corpo: { product_id }
 *   GET    /wishlists/list              -> itens da wishlist do usuário autenticado
 *   GET    /wishlists/product/{id}      -> itens de um produto (comum vê só o próprio)
 *   DELETE /wishlists/delete/{id}       -> remove um item
 *
 * AUTENTICAÇÃO: o dono da wishlist vem do TOKEN (Bearer), não mais de um
 * `user_id` na query. O interceptor do client anexa o token automaticamente —
 * nenhum método recebe `userId`.
 */
export const wishlistService = {
  /** Adiciona um produto à wishlist do usuário autenticado. */
  async adicionar(productId) {
    const { data } = await api.post('/wishlists/create', {
      product_id: productId,
    })
    return data
  },

  /** Lista os itens da wishlist do usuário autenticado ([] quando vazia). */
  async listar() {
    try {
      const { data } = await api.get('/wishlists/list')
      return Array.isArray(data) ? data : []
    } catch (error) {
      if (error?.status === 404 || error?.code === 'WISHLIST_NOT_FOUND') {
        return []
      }
      throw error
    }
  },

  /**
   * Busca os itens da wishlist de um produto. Para um cliente comum, o backend
   * devolve apenas o próprio item (se existir); admin recebe todos. É o que o
   * DetalheLivro usa para saber se o produto já está nos desejos — sem baixar
   * a lista inteira do usuário.
   * @param {number|string} productId
   * @returns {Promise<Array>} WishlistResponse[]
   */
  async buscarPorProduto(productId) {
    try {
      const { data } = await api.get(`/wishlists/product/${productId}`)
      return Array.isArray(data) ? data : []
    } catch (error) {
      if (error?.status === 404 || error?.code === 'WISHLIST_NOT_FOUND') {
        return []
      }
      throw error
    }
  },

  /** Remove um item da wishlist pelo ID do item. */
  async excluir(wishlistId) {
    const { data } = await api.delete(`/wishlists/delete/${wishlistId}`)
    return data
  },
}

export default wishlistService
