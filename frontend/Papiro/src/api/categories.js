import api from './client'

/**
 * Endpoints de categorias (públicos).
 *
 * Contrato do backend (FastAPI):
 *   GET /categories/list -> CategoryResponse[]
 *
 * Observação: `CategoryService.get_all` lança ValueError quando não há
 * categorias, e o handler global converte isso em HTTP 400. O chamador deve
 * tratar esse caso como "lista vazia", não como falha.
 */
export const categoryService = {
  /** Lista todas as categorias. */
  async listar() {
    const { data } = await api.get('/categories/list')
    return data
  },
}

export default categoryService
