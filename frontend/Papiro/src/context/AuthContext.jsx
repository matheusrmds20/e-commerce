import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'
import authService from '../api/auth'
import { getToken, toApiError } from '../api/client'
import AuthContext from './auth-context'

/**
 * AuthProvider — guarda o usuário logado e expõe as ações de autenticação.
 *
 * Ao montar, se houver token salvo, tenta restaurar a sessão via GET /auth/me.
 * Enquanto isso, `carregando` fica true para evitar telas piscando.
 */
export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [carregando, setCarregando] = useState(() => Boolean(getToken()))

  useEffect(() => {
    let ativo = true

    async function restaurarSessao() {
      if (!getToken()) {
        setCarregando(false)
        return
      }
      try {
        const dados = await authService.me()
        if (ativo) setUsuario(dados)
      } catch {
        // Token inválido/expirado — o interceptor já limpou o token.
        if (ativo) setUsuario(null)
      } finally {
        if (ativo) setCarregando(false)
      }
    }

    restaurarSessao()
    return () => {
      ativo = false
    }
  }, [])

  const login = useCallback(async (credenciais) => {
    await authService.login(credenciais)
    // Busca o perfil para ter o usuário completo em memória.
    const dados = await authService.me()
    setUsuario(dados)
    return dados
  }, [])

  const logout = useCallback(() => {
    authService.logout()
    setUsuario(null)
  }, [])

  const value = useMemo(
    () => ({
      usuario,
      autenticado: Boolean(usuario),
      carregando,
      login,
      logout,
      // Reexportado para o formulário mapear erros sem importar o client.
      toApiError,
    }),
    [usuario, carregando, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export default AuthProvider
