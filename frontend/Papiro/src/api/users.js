import api from './client'

/**
 * Endpoints de usuários (dados da conta).
 *
 * Contrato do backend (FastAPI):
 *   PATCH /users/update/{id}                          -> UserResponse
 *   POST  /users/change_password/{id}/change-password -> { message }
 *
 * AUTENTICAÇÃO: todas as rotas exigem Bearer token e só aceitam o próprio
 * usuário (ou admin). O `user_id` do token é usado pelo backend — o ID na
 * URL precisa ser o do usuário autenticado.
 *
 * Erros relevantes:
 *   - `atualizar`: 409 `EMAIL_ALREADY_EXISTS` (e-mail em uso), 422 (validação).
 *   - `alterarSenha`: 400 `INVALID_CURRENT_PASSWORD` (senha atual incorreta),
 *     422 (nova senha: mín. 8 caracteres, ao menos uma letra e um dígito).
 */
export const userService = {
  /**
   * Atualiza os dados do usuário autenticado.
   * @param {number} userId
   * @param {{ full_name?: string, email?: string }} dados
   * @returns {Promise<object>} UserResponse
   */
  async atualizar(userId, dados) {
    const { data } = await api.patch(`/users/update/${userId}`, dados)
    return data
  },

  /**
   * Altera a senha do usuário autenticado.
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
