import api from './client'

/**
 * Endpoints de categorias.
 *
 * Contrato do backend (FastAPI):
 *   GET    /categories/list          -> CategoryResponse[]   (público)
 *   GET    /categories/get/{id}      -> CategoryResponse     (público)
 *   GET    /categories/name/{name}   -> CategoryResponse     (público)
 *   GET    /categories/slug/{slug}   -> CategoryResponse     (público)
 *   POST   /categories/create        -> 201 (exige admin; 403 sem permissão)
 *   PATCH  /categories/update/{id}   -> 200 (exige admin)
 *   DELETE /categories/delete/{id}   -> 200 (exige admin)
 *
 * Observação: `CategoryService.get_all` lança ValueError quando não há
 * categorias, e o handler global converte isso em HTTP 400. O chamador deve
 * tratar esse caso como "lista vazia", não como falha.
 *
 * Erros de escrita relevantes:
 * - 401 sem token; 403 `INSUFFICIENT_PERMISSION` sem papel de admin.
 * - 409 `DUPLICATE_CATEGORY` quando nome ou slug já existem.
 * - 404 `CATEGORY_NOT_FOUND` quando o id não existe.
 */
export const categoryService = {
  /** Lista todas as categorias. */
  async listar() {
    const { data } = await api.get('/categories/list')
    return data
  },

  /** Cria uma categoria (admin). */
  async criar(categoriaData) {
    const { data } = await api.post('/categories/create', categoriaData)
    return data
  },

  /** Atualiza uma categoria (admin). */
  async atualizar(categoriaId, categoriaData) {
    const { data } = await api.patch(
      `/categories/update/${categoriaId}`,
      categoriaData,
    )
    return data
  },

  /** Exclui uma categoria (admin). */
  async excluir(categoriaId) {
    const { data } = await api.delete(`/categories/delete/${categoriaId}`)
    return data
  },
}

export default categoryService
