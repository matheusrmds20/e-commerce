import api from './client'
import { ApiError, toApiError } from './client'

/**
 * Newsletter / "Carta do Livreiro".
 *
 * ⚠️ O backend ATUAL NÃO POSSUI este endpoint (nem modelo de inscrição).
 * Este módulo existe para deixar o contrato pronto: quando a API implementar
 * `POST /newsletter/subscribe`, a Home passa a funcionar sem mudanças na UI.
 *
 * Enquanto isso, a chamada retorna 404 e o componente Newsletter trata como
 * "recurso indisponível" — sem fingir sucesso.
 */
export const newsletterService = {
  /**
   * Inscreve um e-mail na carta mensal.
   * @param {string} email
   * @returns {Promise<{ email: string }>}
   */
  async inscrever(email) {
    try {
      const { data } = await api.post('/newsletter/subscribe', { email })
      return data
    } catch (error) {
      const apiError = toApiError(error)
      // 404 => endpoint ainda não implementado no backend.
      if (apiError.status === 404) {
        throw new ApiError({
          message:
            'A assinatura da Carta ainda não está disponível. Em breve abriremos as inscrições.',
          code: 'NEWSLETTER_UNAVAILABLE',
          status: 404,
        })
      }
      throw apiError
    }
  },
}

export default newsletterService
