import api from './client'
import { ApiError, toApiError } from './client'

/**
 * Newsletter / "Carta do Livreiro".
 *
 * - `inscrever(email)` — público; inscreve um e-mail na carta mensal.
 *   409 => e-mail já inscrito (mensagem amigável).
 * - `listarInscritos()` — restrito a administradores; base da aba
 *   Newsletter do painel admin.
 */
export const newsletterService = {
  /**
   * Inscreve um e-mail na carta mensal.
   * @param {string} email
   * @returns {Promise<{ id: number, email: string, subscribed_at: string }>}
   */
  async inscrever(email) {
    try {
      const { data } = await api.post('/newsletter/subscribe', { email })
      return data
    } catch (error) {
      const apiError = toApiError(error)
      if (apiError.status === 409) {
        throw new ApiError({
          message: 'Este e-mail já está inscrito na Carta do Livreiro.',
          code: 'NEWSLETTER_ALREADY_SUBSCRIBED',
          status: 409,
        })
      }
      throw apiError
    }
  },

  /**
   * Lista todos os inscritos da newsletter (admin).
   * @returns {Promise<Array<{ id: number, email: string, subscribed_at: string }>>}
   */
  async listarInscritos() {
    const { data } = await api.get('/newsletter/list')
    return data
  },
}

export default newsletterService
