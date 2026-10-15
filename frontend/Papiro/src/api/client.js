import axios from 'axios'


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


const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'https://api-e-commerce.matheuslab.xyz/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,

  withCredentials: true,
})


api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

export class ApiError extends Error {
  constructor({ message, code = 'UNKNOWN', status = 0, details = null }) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.details = details
  }
}


export function toApiError(error) {
  if (error instanceof ApiError) return error


  const payload = error?.response?.data?.error
  if (payload) {
    return new ApiError({
      message: payload.message ?? 'Não foi possível concluir a operação.',
      code: payload.code ?? 'API_ERROR',
      status: error.response.status,
      details: payload.details ?? null,
    })
  }


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


let isRefreshing = false

let waitingQueue = []

function flushWaiting(newToken) {
  waitingQueue.forEach((resolve) => resolve(newToken))
  waitingQueue = []
}

function failWaiting(error) {
  waitingQueue.forEach((reject) => reject(error))
  waitingQueue = []
}


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

    accessToken = null
    return false
  }
}


export async function ensureAccessToken() {
  if (accessToken) return true
  if (isRefreshing) {

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


api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error


    if (!response || response.status !== 401) {
      return Promise.reject(toApiError(error))
    }


    const url = config?.url ?? ''
    if (url.includes('/auth/login') || url.includes('/auth/refresh')) {
      clearToken()
      return Promise.reject(toApiError(error))
    }


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


    config._retried = true
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${accessToken}`
    return api(config)
  },
)

export default api