import api from './client'


export const wishlistService = {
  /** Adiciona um produto à wishlist do usuário autenticado. */
  async adicionar(productId) {
    const { data } = await api.post('/wishlists/create', {
      product_id: productId,
    })
    return data
  },


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


  async excluir(wishlistId) {
    const { data } = await api.delete(`/wishlists/delete/${wishlistId}`)
    return data
  },
}

export default wishlistService
