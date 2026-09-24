import api from './client'

/**
 * Endpoints dedicados para o Painel Administrativo.
 *
 * Contrato do backend (FastAPI):
 *   GET   /admin/dashboard/stats      -> DashboardStatsResponse
 *   GET   /admin/orders               -> AdminOrderResponse[] (todos os clientes)
 *   PATCH /admin/orders/{id}/status   -> AdminOrderResponse
 *   GET   /admin/users                -> AdminUserResponse[]
 */
export const adminService = {
  /** Obtém métricas e estatísticas consolidadas do dashboard. */
  async obterEstatisticas() {
    const { data } = await api.get('/admin/dashboard/stats')
    return data
  },

  /**
   * Lista todos os pedidos de todos os clientes no sistema.
   * @param {{ page?: number, perPage?: number, status?: string }} [params]
   */
  async listarPedidos(params = {}) {
    const { data } = await api.get('/admin/orders', { params })
    return data
  },

  /**
   * Atualiza o status de um pedido como administrador.
   * @param {number} orderId
   * @param {string} status ('pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled')
   */
  async atualizarStatusPedido(orderId, status) {
    const { data } = await api.patch(`/admin/orders/${orderId}/status`, { status })
    return data
  },

  /** Lista todos os usuários e clientes cadastrados. */
  async listarUsuarios() {
    const { data } = await api.get('/admin/users')
    return data
  },
}

export default adminService
