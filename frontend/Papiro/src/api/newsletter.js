import api from './client'
import { ApiError, toApiError } from './client'


export const newsletterService = {

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


  async listarInscritos() {
    const { data } = await api.get('/newsletter/list')
    return data
  },
}

export default newsletterService
