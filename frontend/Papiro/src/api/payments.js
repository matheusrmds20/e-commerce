import api from './client'


export const STATUS_PAGAMENTO = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected',
}


export const ROTULO_STATUS = {
  pending: 'Aguardando confirmação',
  approved: 'Pagamento aprovado',
  rejected: 'Pagamento recusado',
}

export const paymentService = {

  async criarCheckout(orderId) {
    const { data } = await api.post(`/payments/checkout/${orderId}`)
    return data
  },


  async obter(paymentId) {
    const { data } = await api.get(`/payments/get/${paymentId}`)
    return data
  },


  async listarPorPedido(orderId) {
    const { data } = await api.get(`/payments/order/${orderId}`)
    return data
  },


  async historico(params = {}) {
    const { data } = await api.get('/payments/history', { params })
    return data?.data ?? data
  },
}

export default paymentService
