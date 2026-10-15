import api from './client'


export const adminService = {

  async obterEstatisticas() {
    const { data } = await api.get('/admin/dashboard/stats')
    return data
  },


  async listarPedidos(params = {}) {
    const { data } = await api.get('/admin/orders', { params })
    return data
  },


  async atualizarStatusPedido(orderId, status) {
    const { data } = await api.patch(`/admin/orders/${orderId}/status`, { status })
    return data
  },


  async listarUsuarios() {
    const { data } = await api.get('/admin/users')
    return data
  },
}

export default adminService
