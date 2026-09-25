import api, { clearToken, setToken } from './client'

/**
 * Endpoints de autenticação.
 *
 * Backend (FastAPI):
 *   POST /auth/login    -> { access_token, token_type }
 *   POST /auth/register -> { id, email, full_name, role, is_active, created_at }
 *   GET  /auth/me       -> mesmo shape do register (exige Bearer token)
 *
 * OBS: `/auth/login` usa `OAuth2PasswordRequestForm`, ou seja, espera
 * `application/x-www-form-urlencoded` com os campos `username` (o e-mail) e
 * `password` — e NÃO JSON. Enviar JSON resulta em 422.
 */
export const authService = {
  /**
   * Autentica e persiste o token.
   * @param {{ email: string, password: string }} credenciais
   * @returns {Promise<{ access_token: string, token_type: string }>}
   */
  async login({ email, password }) {
    // `OAuth2PasswordRequestForm` exige form-urlencoded; o campo `username`
    // carrega o e-mail (ver `AuthService.login`, que lê `data.username`).
    const body = new URLSearchParams()
    body.append('username', email)
    body.append('password', password)

    const { data } = await api.post('/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    setToken(data.access_token)
    return data
  },

  /** Cadastra um novo usuário (não faz login automático). */
  async register({ email, full_name, password }) {
    const { data } = await api.post('/auth/register', {
      email,
      full_name,
      password,
    })
    return data
  },

  /** Busca os dados do usuário autenticado. Lança 401 se o token for inválido. */
  async me() {
    const { data } = await api.get('/auth/me')
    return data
  },

  /** Encerra a sessão local (não há endpoint de logout no backend). */
  logout() {
    clearToken()
  },
}

export default authService
