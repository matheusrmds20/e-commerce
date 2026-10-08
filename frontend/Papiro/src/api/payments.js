import api from './client'

/**
 * Endpoints de pagamento (Mercado Pago).
 *
 * Contrato atual do backend (FastAPI):
 *   POST /payments/checkout/{order_id} -> cria a preferência e devolve a URL
 *                                         de checkout. Corpo/retorno:
 *                                         { id, payment_id, checkout_url } (201).
 *   GET  /payments/get/{payment_id}    -> busca um pagamento pelo ID.
 *   GET  /payments/order/{order_id}    -> lista os pagamentos de um pedido.
 *   GET  /payments/history             -> lista TODOS os pagamentos do usuário
 *                                         (1 request; usado na aba Pagamentos).
 *
 * FLUXO REAL: o cliente finaliza o pedido (`orderService.criar`), chamamos
 * `criarCheckout(order.id)` e redirecionamos o navegador para `checkout_url`.
 * O pagamento acontece no domínio do Mercado Pago — nenhum dado de cartão
 * passa por aqui.
 *
 * O status do pagamento só muda via webhook do Mercado Pago no backend; por
 * isso o front consulta (`listarPorPedido`) após o retorno, até sair de
 * `pending` (ver PollingPagamento).
 *
 * AUTENTICAÇÃO: checkout/consulta exigem Bearer token (o interceptor do
 * `client` anexa sozinho). O webhook é chamado pelo Mercado Pago, não pelo
 * front — por isso NÃO é exposto aqui.
 *
 * `POST /payments/create` também NÃO é exposto: ele permite criar um pagamento
 * arbitrário (forjável) e não faz parte do fluxo do cliente.
 */

/** Status possíveis de um pagamento no backend. */
export const STATUS_PAGAMENTO = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected',
}

/** Rótulos legíveis por status (para exibir na UI). */
export const ROTULO_STATUS = {
  pending: 'Aguardando confirmação',
  approved: 'Pagamento aprovado',
  rejected: 'Pagamento recusado',
}

export const paymentService = {
  /**
   * Cria o checkout do pedido e devolve a URL do Mercado Pago.
   * @param {number} orderId
   * @returns {Promise<{id: number, payment_id: number, checkout_url: string}>}
   */
  async criarCheckout(orderId) {
    const { data } = await api.post(`/payments/checkout/${orderId}`)
    return data
  },

  /**
   * Busca um pagamento pelo ID.
   * @param {number} paymentId
   */
  async obter(paymentId) {
    const { data } = await api.get(`/payments/get/${paymentId}`)
    return data
  },

  /**
   * Lista os pagamentos de um pedido.
   * @param {number} orderId
   */
  async listarPorPedido(orderId) {
    const { data } = await api.get(`/payments/order/${orderId}`)
    return data
  },

  /**
   * Lista TODOS os pagamentos do usuário autenticado em uma única chamada.
   * Usado pela aba "Pagamentos" da Minha Conta (evita 1 request por pedido).
   * @returns {Promise<Array>}
   */
  async historico() {
    const { data } = await api.get('/payments/history')
    return data
  },
}

export default paymentService
