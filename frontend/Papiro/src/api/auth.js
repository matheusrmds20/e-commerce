import api, { clearToken, ensureAccessToken, setToken } from './client'

/**
 * Endpoints de autenticação.
 *
 * Backend (FastAPI):
 *   POST /auth/login    -> { access_token, refresh_token } (o refresh também vai
 *                          num cookie httpOnly `papiro_refresh`)
 *   POST /auth/register -> { id, email, full_name, role, is_active, created_at }
 *   POST /auth/refresh  -> { access_token } (renova via cookie httpOnly)
 *   POST /auth/logout   -> { message } (apaga o cookie de refresh)
 *   GET  /auth/me       -> mesmo shape do register (exige Bearer access token)
 *
 * OBS: `/auth/login` usa `OAuth2PasswordRequestForm`, ou seja, espera
 * `application/x-www-form-urlencoded` com os campos `username` (o e-mail) e
 * `password` — e NÃO JSON. Enviar JSON resulta em 422.
 */
export const authService = {
  /**
   * Autentica e guarda o access token EM MEMÓRIA.
   * O refresh token fica no cookie httpOnly setado pelo backend.
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

  /**
   * Renova a sessão usando o refresh token do cookie httpOnly.
   * Chamado ao carregar a app (refresh silencioso) — permite que o usuário
   * continue logado mesmo após um F5 (o access em memória se perdeu).
   * @returns {Promise<boolean>} true se renovou com sucesso, false se não.
   */
  async restaurarSessaoViaRefresh() {
    return ensureAccessToken()
  },

  /**
   * Encerra a sessão: chama POST /auth/logout (apaga o cookie httpOnly) e
   * limpa o access token da memória.
   */
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