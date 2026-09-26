import api from './client'

/**
 * Endpoints de endereços.
 *
 * Contrato atual do backend (FastAPI):
 *   POST   /addresses/create            -> cria (201). Corpo: AddressCreate.
 *   GET    /addresses/list              -> lista os endereços do usuário.
 *   GET    /addresses/default           -> endereço padrão.
 *   GET    /addresses/zip/{zip_code}    -> busca por CEP.
 *   PATCH  /addresses/default/set/{id}  -> torna padrão.
 *   PATCH  /addresses/update/{id}       -> atualiza.
 *   DELETE /addresses/delete/{id}       -> exclui.
 *
 * AUTENTICAÇÃO: todas as rotas exigem Bearer token e derivam o `user_id` do
 * usuário autenticado (`Depends(get_current_user)`). O `user_id` NÃO vai mais
 * na query nem no corpo — o interceptor do client anexa o token sozinho.
 */
export const addressService = {
  /**
   * Cria um endereço de entrega para o usuário autenticado.
   * @param {{ street: string, number: string, complement?: string|null, neighborhood: string, city: string, state: string, zip_code: string, is_default?: boolean }} endereco
   */
  async criar(endereco) {
    const { data } = await api.post('/addresses/create', endereco)
    return data
  },

  /** Lista os endereços do usuário autenticado. */
  async listar() {
    try {
      const { data } = await api.get('/addresses/list')
      return Array.isArray(data) ? data : []
    } catch (error) {
      if (error?.status === 404 || error?.code === 'ADDRESS_NOT_FOUND') {
        return []
      }
      throw error
    }
  },

  /** Busca o endereço padrão. */
  async padrao() {
    try {
      const { data } = await api.get('/addresses/default')
      return data
    } catch (error) {
      if (error?.status === 404 || error?.code === 'ADDRESS_NOT_FOUND') {
        return null
      }
      throw error
    }
  },

  /** Define um endereço como padrão. */
  async definirPadrao(addressId) {
    const { data } = await api.patch(`/addresses/default/set/${addressId}`)
    return data
  },

  /** Atualiza um endereço existente. */
  async atualizar(addressId, endereco) {
    const { data } = await api.patch(`/addresses/update/${addressId}`, endereco)
    return data
  },

  /** Exclui um endereço. */
  async excluir(addressId) {
    const { data } = await api.delete(`/addresses/delete/${addressId}`)
    return data
  },
}

export default addressService
