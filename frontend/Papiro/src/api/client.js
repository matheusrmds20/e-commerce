import axios from 'axios'

/**
 * Instância única do axios usada por toda a aplicação.
 *
 * - baseURL vem de VITE_API_URL (veja .env.example)
 * - o interceptor de request anexa o token JWT salvo
 * - o interceptor de response normaliza os erros da API
 */
const TOKEN_KEY = 'papiro.token'

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* localStorage indisponível (modo privado, SSR) — segue sem persistir */
  }
}

export function clearToken() {
  setToken(null)
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

// Request — injeta o Bearer token quando existir
api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/**
 * Erro normalizado da API.
 * Sempre tem `message` (legível) e `code` (ex.: INVALID_CREDENTIALS),
 * além de `status` e `details` (erros de validação por campo).
 */
export class ApiError extends Error {
  constructor({ message, code = 'UNKNOWN', status = 0, details = null }) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.details = details
  }
}

/** Converte qualquer falha do axios no nosso ApiError padronizado. */
export function toApiError(error) {
  if (error instanceof ApiError) return error

  // Resposta de erro do backend: { error: { code, message, details? } }
  const payload = error?.response?.data?.error
  if (payload) {
    return new ApiError({
      message: payload.message ?? 'Não foi possível concluir a operação.',
      code: payload.code ?? 'API_ERROR',
      status: error.response.status,
      details: payload.details ?? null,
    })
  }

  // Timeout / rede / servidor fora do ar
  if (error?.code === 'ECONNABORTED') {
    return new ApiError({
      message: 'O servidor demorou para responder. Tente novamente.',
      code: 'TIMEOUT',
    })
  }

  return new ApiError({
    message: 'Não foi possível conectar ao servidor.',
    code: 'NETWORK_ERROR',
    status: error?.response?.status ?? 0,
  })
}

// Response — sessão expirada limpa o token; demais erros viram ApiError
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      clearToken()
    }
    return Promise.reject(toApiError(error))
  },
)

export default api
