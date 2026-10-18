import api from './client'


export const reviewService = {

  async listarPorProduto(productId, params = {}) {
    const { data } = await api.get(`/reviews/product/${productId}`, { params })
    return data?.data ?? data
  },


  async listarMinhas(userId, params = {}) {
    const { data } = await api.get('/reviews/list', {
      params: { ...(userId ? { user_id: userId } : {}), ...params },
    })
    return data?.data ?? data
  },


  async criar(payload) {
    const { data } = await api.post('/reviews/create', payload)
    return data
  },


  async atualizar(reviewId, payload) {
    const { data } = await api.patch(`/reviews/update/${reviewId}`, payload)
    return data
  },


  async excluir(reviewId) {
    const { data } = await api.delete(`/reviews/delete/${reviewId}`)
    return data
  },
}

export default reviewService
