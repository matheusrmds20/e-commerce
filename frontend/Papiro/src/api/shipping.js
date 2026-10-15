import api from './client'


export const shippingService = {

  async quotar({ postal_code }) {
    const { data } = await api.post('/shipping/quote', { postal_code })
    return data
  },


  async calcular(orderId) {
    const { data } = await api.post(`/shipping/calculate/${orderId}`)
    return data
  },


  async aplicar(payload) {
    const { data } = await api.post('/shipping/apply', payload)
    return data
  },
}

export default shippingService