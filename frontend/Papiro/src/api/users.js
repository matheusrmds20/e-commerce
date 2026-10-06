import api from './client'

/**
 * Endpoints de usuários e gestão de clientes.
 *
 * Contrato do backend (FastAPI):
 *   GET    /admin/users                               -> AdminUserResponse[]
 *   GET    /users/user_id/{id}                        -> UserResponse
 *   POST   /users/create                              -> UserResponse (AdminUserCreate | CustomerUserCreate)
 *   PATCH  /users/update/{id}                         -> UserResponse
 *   DELETE /users/delete/{id}                         -> UserResponse (desativação / soft delete)
 *   POST   /users/change_password/{id}/change-password -> { message }
 */
export const userService = {
  /** Lista todos os usuários cadastrados (via endpoint administrativo). */
  async listar() {
    const { data } = await api.get('/admin/users')
    return data
  },

  /** Busca os detalhes de um usuário por ID. */
  async obter(userId) {
    const { data } = await api.get(`/users/user_id/${userId}`)
    return data
  },

  /**
   * Cria um novo usuário (cliente ou administrador).
   * @param {{ email: string, full_name: string, password: string, role?: 'customer'|'admin' }} payload
   */
  async criar(payload) {
    const { data } = await api.post('/users/create', payload)
    return data
  },

  /**
   * Atualiza os dados de um usuário (nome, e-mail, senha opcional).
   * @param {number} userId
   * @param {{ full_name?: string, email?: string, password?: string, role?: 'customer'|'admin' }} dados
   * @returns {Promise<object>} UserResponse
   */
  async atualizar(userId, dados) {
    const { data } = await api.patch(`/users/update/${userId}`, dados)
    return data
  },

  /**
   * Desativa/exclui um usuário do sistema.
   * @param {number} userId
   */
  async excluir(userId) {
    const { data } = await api.delete(`/users/delete/${userId}`)
    return data
  },

  /**
   * Altera a senha do usuário.
   * @param {number} userId
   * @param {{ current_password: string, new_password: string }} payload
   * @returns {Promise<{ message: string }>}
   */
  async alterarSenha(userId, { current_password, new_password }) {
    const { data } = await api.post(
      `/users/change_password/${userId}/change-password`,
      { current_password, new_password },
    )
    return data
  },
}

export default userService
