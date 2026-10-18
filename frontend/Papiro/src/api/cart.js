import api from './client'


export const cartService = {

  async criar() {
    const { data } = await api.post('/cart/create')
    return data
  },


  async obter() {
    const { data } = await api.get('/cart/cart/me')
    return data
  },


  async adicionarItem(cartId, productId, quantity = 1) {
    const { data } = await api.post(`/cart/${cartId}/items/add`, {
      product_id: productId,
      quantity,
    })
    return data
  },


  async atualizarQuantidade(cartId, itemId, quantity) {
    const { data } = await api.patch(
      `/cart/${cartId}/items/update/${itemId}`,
      null,
      { params: { quantity } },
    )
    return data
  },


  async removerItem(cartId, itemId) {
    const { data } = await api.delete(`/cart/${cartId}/items/delete/${itemId}`)
    return data
  },


  async limpar(cartId) {
    const { data } = await api.delete(`/cart/${cartId}/items/clear`)
    return data
  },
}

export default cartService
