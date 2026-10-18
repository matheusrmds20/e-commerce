import api from './client'


export const orderService = {

  async criar(pedido) {
    const { data } = await api.post('/orders/create', pedido)
    return data
  },


  async listar(params = {}) {
    const { data } = await api.get('/orders/list', { params })
    return data?.data ?? data
  },


  async cancelar(orderId) {
    const { data } = await api.patch(`/orders/update/${orderId}`, {
      status: 'cancelled',
    })
    return data
  },
}

export default orderService
