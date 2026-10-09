import api from './client'

/**
 * Endpoints de avaliações.
 *
 * Contrato do backend (FastAPI) — o dono vem do TOKEN, não de `user_id`:
 *   GET    /reviews/list                -> avaliações do usuário autenticado
 *                                           (admin pode alvejar ?user_id=)
 *   GET    /reviews/product/{id}        -> lista avaliações do produto (público)
 *   POST   /reviews/create              -> cria avaliação para o usuário do token
 *   PATCH  /reviews/update/{review_id}  -> atualiza (autor ou admin)
 *   DELETE /reviews/delete/{review_id}  -> exclui (autor ou admin)
 *
 * Observações:
 * - `GET /reviews/product/{id}` responde 404 quando o produto não existe e
 *   200 com a lista (possivelmente vazia) quando existe. Chamadores tratam
 *   falha como "lista vazia".
 * - Avaliação de outro usuário em update/delete → 403 `REVIEW_FORBIDDEN`.
 * - Avaliação duplicada (mesmo usuário/produto) → 409 `DUPLICATE_REVIEW`.
 * - Rotas removidas do backend: `GET /get/{id}` e `GET /rating/{rating}`.
 */
export const reviewService = {
  /**
   * Lista as avaliações de um produto (paginado no backend).
   * Desembrulha `.data` do envelope `{ data, meta }`.
   * @param {number|string} productId
   * @param {{ page?: number, per_page?: number }} [params]
   * @returns {Promise<Array>} ReviewResponse[]
   */
  async listarPorProduto(productId, params = {}) {
    const { data } = await api.get(`/reviews/product/${productId}`, { params })
    return data?.data ?? data
  },

  /**
   * Lista as avaliações do usuário autenticado ("minhas avaliações").
   * @param {number} [userId] alvo alternativo — apenas administradores.
   * @param {{ page?: number, per_page?: number }} [params]
   * @returns {Promise<Array>} ReviewResponse[]
   */
  async listarMinhas(userId, params = {}) {
    const { data } = await api.get('/reviews/list', {
      params: { ...(userId ? { user_id: userId } : {}), ...params },
    })
    return data?.data ?? data
  },

  /**
   * Cria uma avaliação para o produto (o autor vem do token).
   * @param {{ product_id: number, rating: number, comment?: string }} payload
   */
  async criar(payload) {
    const { data } = await api.post('/reviews/create', payload)
    return data
  },

  /**
   * Atualiza uma avaliação própria (ou qualquer uma, se admin).
   * @param {number} reviewId
   * @param {{ rating?: number, comment?: string }} payload
   */
  async atualizar(reviewId, payload) {
    const { data } = await api.patch(`/reviews/update/${reviewId}`, payload)
    return data
  },

  /**
   * Exclui uma avaliação própria (ou qualquer uma, se admin).
   * @param {number} reviewId
   */
  async excluir(reviewId) {
    const { data } = await api.delete(`/reviews/delete/${reviewId}`)
    return data
  },
}

export default reviewService
