import api from './client'


export const categoryService = {

  async listar() {
    const { data } = await api.get('/categories/list')
    return data
  },


  async criar(categoriaData) {
    const { data } = await api.post('/categories/create', categoriaData)
    return data
  },


  async atualizar(categoriaId, categoriaData) {
    const { data } = await api.patch(
      `/categories/update/${categoriaId}`,
      categoriaData,
    )
    return data
  },


  async excluir(categoriaId) {
    const { data } = await api.delete(`/categories/delete/${categoriaId}`)
    return data
  },
}

export default categoryService
