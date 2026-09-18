import api from './client'

/**
 * Endpoints de avaliações.
 *
 * Contrato do backend (FastAPI):
 *   GET    /reviews/product/{product_id}       -> lista avaliações do produto (público)
 *   POST   /reviews/create?user_id={id}        -> cria avaliação (user_id na query)
 *   PATCH  /reviews/update/{review_id}?user_id -> atualiza (dono da avaliação)
 *   DELETE /reviews/delete/{review_id}?user_id -> exclui (dono da avaliação)
 *
 * Observações:
 * - `GET /reviews/product/{id}` responde 400 quando o produto não tem
 *   avaliações (o service lança ValueError). O chamador deve tratar isso como
 *   "lista vazia", e não como falha.
 * - O `user_id` NÃO vem do token nestas rotas: ele é passado explicitamente na
 *   query string. O token Bearer é anexado pelo interceptor quando existir.
 */
export const reviewService = {
  /**
   * Lista as avaliações de um produto.
   * @param {number|string} productId
   * @returns {Promise<Array>} ReviewResponse[]
   */
  async listarPorProduto(productId) {
    const { data } = await api.get(`/reviews/product/${productId}`)
    return data
  },

  /**
   * Cria uma avaliação para um produto.
   * @param {number} userId
   * @param {{ product_id: number, rating: number, comment?: string }} payload
   */
  async criar(userId, payload) {
    const { data } = await api.post('/reviews/create', payload, {
      params: { user_id: userId },
    })
    return data
  },

  /**
   * Atualiza uma avaliação existente.
   * @param {number} reviewId
   * @param {number} userId
   * @param {{ rating?: number, comment?: string }} payload
   */
  async atualizar(reviewId, userId, payload) {
    const { data } = await api.patch(`/reviews/update/${reviewId}`, payload, {
      params: { user_id: userId },
    })
    return data
  },

  /**
   * Exclui uma avaliação.
   * @param {number} reviewId
   * @param {number} userId
   */
  async excluir(reviewId, userId) {
    const { data } = await api.delete(`/reviews/delete/${reviewId}`, {
      params: { user_id: userId },
    })
    return data
  },
}

export default reviewService
