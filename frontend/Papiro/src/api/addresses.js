import api from './client'


export const addressService = {

  async criar(endereco) {
    const { data } = await api.post('/addresses/create', endereco)
    return data
  },


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


  async definirPadrao(addressId) {
    const { data } = await api.patch(`/addresses/default/set/${addressId}`)
    return data
  },


  async atualizar(addressId, endereco) {
    const { data } = await api.patch(`/addresses/update/${addressId}`, endereco)
    return data
  },


  async excluir(addressId) {
    const { data } = await api.delete(`/addresses/delete/${addressId}`)
    return data
  },
}

export default addressService
