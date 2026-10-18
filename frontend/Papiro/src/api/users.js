import api from './client'


export const userService = {

  async listar() {
    const { data } = await api.get('/admin/users')
    return data
  },


  async obter(userId) {
    const { data } = await api.get(`/users/user_id/${userId}`)
    return data
  },


  async criar(payload) {
    const { data } = await api.post('/users/create', payload)
    return data
  },


  async atualizar(userId, dados) {
    const { data } = await api.patch(`/users/update/${userId}`, dados)
    return data
  },


  async excluir(userId) {
    const { data } = await api.delete(`/users/delete/${userId}`)
    return data
  },


  async alterarSenha(userId, { current_password, new_password }) {
    const { data } = await api.post(
      `/users/change_password/${userId}/change-password`,
      { current_password, new_password },
    )
    return data
  },
}

export default userService
