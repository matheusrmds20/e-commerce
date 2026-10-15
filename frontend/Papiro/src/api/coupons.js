import api from './client'
import { toApiError } from './client'


async function listarOuVazio(fn) {
  try {
    return (await fn()) ?? []
  } catch (error) {
    const apiError = toApiError(error)
    // 400/404 = "No coupons found" no service. 401/403/500/timeout = falha real.
    if (apiError.status === 400 || apiError.status === 404) return []
    throw apiError
  }
}

export const couponService = {

  async listar() {
    return listarOuVazio(async () => {
      const { data } = await api.get('/coupons/list')
      return data
    })
  },


  async criar(cupom) {
    const { data } = await api.post('/coupons/create', cupom)
    return data
  },

  async atualizar(couponId, cupom) {
    const { data } = await api.patch(`/coupons/update/${couponId}`, cupom)
    return data
  },


  async excluir(couponId) {
    const { data } = await api.delete(`/coupons/delete/${couponId}`)
    return data
  },

  // ---------------------------------------------------------------------
  // Vínculo usuário ↔ cupom (ownership)
  // ---------------------------------------------------------------------


  async meusCupons() {
    return listarOuVazio(async () => {
      const { data } = await api.get('/user-coupons/my')
      return data
    })
  },


  async vinculosDoCupom(couponId) {
    return listarOuVazio(async () => {
      const { data } = await api.get(`/user-coupons/coupon/${couponId}`)
      return data
    })
  },


  async atribuir(userId, couponId) {
    const { data } = await api.post('/user-coupons/admin/assign', {
      user_id: userId,
      coupon_id: couponId,
    })
    return data
  },


  async removerVinculo(vinculoId) {
    const { data } = await api.delete(`/user-coupons/delete/${vinculoId}`)
    return data
  },
}

export default couponService
