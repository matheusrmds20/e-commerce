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
    const { data } = await api.get('/addresses/list')
    return data
  },

  /** Busca o endereço padrão. */
  async padrao() {
    const { data } = await api.get('/addresses/default')
    return data
  },

  /** Define um endereço como padrão. */
  async definirPadrao(addressId) {
    const { data } = await api.patch(`/addresses/default/set/${addressId}`)
    return data
  },
}

export default addressService
