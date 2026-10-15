import api from './client'
import { toApiError } from './client'


async function listarOuVazio(fn) {
  try {
    return (await fn()) ?? []
  } catch (error) {
    const apiError = toApiError(error)
    if (apiError.status === 400 || apiError.status === 404) return []
    throw apiError
  }
}

export const productService = {

  async listar(params = {}) {
    return listarOuVazio(async () => {
      const { data } = await api.get('/products/list', { params })
      return data?.data ?? data
    })
  },


  async obter(productId) {
    const { data } = await api.get(`/products/get/${productId}`)
    return data
  },


  async listarPorDesconto(discountPct) {
    return listarOuVazio(async () => {
      const { data } = await api.get(`/products/discount/${discountPct}`)
      return data
    })
  },


  async listarPorAtivo(isActive = true) {
    return listarOuVazio(async () => {
      const { data } = await api.get(`/products/active/${isActive}`)
      return data
    })
  },


  async listarDestaques(limite) {
    const { data } = await api.get('/products/featured', {
      params: limite ? { limit: limite } : undefined,
    })
    return data ?? []
  },


  async listarMaisVendidos(limite) {
    const { data } = await api.get('/products/bestsellers', {
      params: limite ? { limit: limite } : undefined,
    })
    return data ?? []
  },


  async listarPaginado({ page = 1, perPage = 20, categoryId, search } = {}) {
    const { data } = await api.get('/products/paginated', {
      params: {
        page,
        per_page: perPage,
        ...(categoryId ? { category_id: categoryId } : {}),
        ...(search && search.trim() ? { search: search.trim() } : {}),
      },
    })
    return data
  },


  async recomendacoes(excludeIds = [], limite = 4) {
    const { data } = await api.get('/products/recommendations', {
      params: {
        ...(excludeIds.length ? { exclude: excludeIds.join(',') } : {}),
        limit: limite,
      },
    })
    return data ?? []
  },


  async criar(produtoData) {
    const { data } = await api.post('/products/create', produtoData)
    return data
  },


  async atualizar(productId, produtoData) {
    const { data } = await api.patch(`/products/update/${productId}`, produtoData)
    return data
  },


  async excluir(productId) {
    const { data } = await api.delete(`/products/delete/${productId}`)
    return data
  },
}

export default productService

