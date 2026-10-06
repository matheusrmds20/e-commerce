import axios from 'axios'

/**
 * Instância única do axios usada por toda a aplicação.
 *
 * Segurança de tokens (PLANO 7.3):
 * - O access token (curta validade) vive APENAS em memória (variável módulo),
 *   NUNCA em localStorage — um XSS não consegue exfiltrá-lo.
 * - O refresh token (7 dias, rotativo) fica num cookie httpOnly, por isso o
 *   axios usa `withCredentials: true` (envia o cookie junto).
 * - Quando uma request devolve 401, o interceptor renova o access via
 *   POST /auth/refresh (cujo cookie vai sozinho) e REPETE a request.
 *
 * Legado/back-compat: mantemos as chaves getToken/setToken/clearToken com os
 * MESMOS nomes (AuthContext e auth.js as usam), mas agora operam em memória.
 */

// --- Access token em memória (não persiste entre reloads; normal) ---
let accessToken = null

export function getToken() {
  return accessToken
}

export function setToken(token) {
  if (token) accessToken = token
  else accessToken = null
}

export function clearToken() {
  accessToken = null
}

// --- Configuração do axios ---
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'https://api-e-commerce.matheuslab.xyz/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
  // Envia o cookie httpOnly (refresh token) nas requisições — necessário para
  // /auth/refresh e /auth/logout receberem o cookie.
  withCredentials: true,
})

// Request — injeta o Bearer access token quando existir em memória.
api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
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

// ---------------------------------------------------------------------------
// Refresh silencioso (rotação de token em segundo plano)
// ---------------------------------------------------------------------------

// Lock: evita disparar N refreshes quando N requests falham 401 em paralelo.
let isRefreshing = false
/** Fila de requests que aguardam o novo access token (promise resolvers). */
let waitingQueue = []

function flushWaiting(newToken) {
  waitingQueue.forEach((resolve) => resolve(newToken))
  waitingQueue = []
}

function failWaiting(error) {
  waitingQueue.forEach((reject) => reject(error))
  waitingQueue = []
}

/**
 * Troca o access token via POST /auth/refresh usando o cookie httpOnly.
 * Usa `axios` CRU (fora do interceptor) para não entrar em recursão.
 *
 * @returns {Promise<boolean>} true se renovou, false se o refresh falhou.
 */
async function tryRefreshToken() {
  try {
    // `request.withCredentials` não é garantido aqui; setamos explicitamente.
    const { data } = await axios.post(
      `${api.defaults.baseURL}/auth/refresh`,
      null,
      { withCredentials: true, timeout: 15000 },
    )
    if (data?.access_token) {
      accessToken = data.access_token
      return true
    }
    return false
  } catch {
    // Refresh inválido/expirado — sessão realmente encerrada.
    accessToken = null
    return false
  }
}

/**
 * Garante um access token válido. Se não houver (primeiro uso / após F5),
 * tenta renovar silenciosamente pelo cookie.
 */
export async function ensureAccessToken() {
  if (accessToken) return true
  if (isRefreshing) {
    // Já existe uma renovação em andamento — aguarda o resultado dela.
    return new Promise((resolve) => {
      waitingQueue.push((token) => resolve(Boolean(token)))
    })
  }

  isRefreshing = true
  try {
    const ok = await tryRefreshToken()
    flushWaiting(accessToken)
    return ok
  } catch (err) {
    failWaiting(err)
    return false
  } finally {
    isRefreshing = false
  }
}

// Response — 401: renova o access e repete a request original.
// Demais erros viram ApiError.
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error

    // Falha de rede/timeout ou status != 401 não dispara refresh.
    if (!response || response.status !== 401) {
      return Promise.reject(toApiError(error))
    }

    // /auth/login e /auth/refresh não devem entrar no retry (credenciais
    // inválidas já retornam 401; refresh inválido = sessão morta).
    const url = config?.url ?? ''
    if (url.includes('/auth/login') || url.includes('/auth/refresh')) {
      clearToken()
      return Promise.reject(toApiError(error))
    }

    // Já tentamos renovar uma vez nesta request — evita loop infinito.
    if (config?._retried) {
      clearToken()
      return Promise.reject(toApiError(error))
    }

    const renewed = await ensureAccessToken()
    if (!renewed) {
      // Sessão expirou de verdade.
      clearToken()
      return Promise.reject(toApiError(error))
    }

    // Repete a request original (apenas uma vez) com o novo token.
    config._retried = true
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${accessToken}`
    return api(config)
  },
)

export default api