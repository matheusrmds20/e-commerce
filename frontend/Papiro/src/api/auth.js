import api, { clearToken, ensureAccessToken, setToken } from './client'


export const authService = {

  async login({ email, password }) {

    const body = new URLSearchParams()
    body.append('username', email)
    body.append('password', password)

    const { data } = await api.post('/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    setToken(data.access_token)
    return data
  },


  async register({ email, full_name, password }) {
    const { data } = await api.post('/auth/register', {
      email,
      full_name,
      password,
    })
    return data
  },

  /** Busca os dados do usuário autenticado. Lança 401 se o token for inválido. */  async me() {
    const { data } = await api.get('/auth/me')
    return data
  },


  async restaurarSessaoViaRefresh() {
    return ensureAccessToken()
  },


  async logout() {
    try {
      await api.post('/auth/logout')
    } catch {
      // Mesmo se o servidor falhar, limpa a sessão local.
    }
    clearToken()
  },
}

export default authService