import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'
import authService from '../api/auth'
import { toApiError } from '../api/client'
import AuthContext from './auth-context'

/**
 * AuthProvider — guarda o usuário logado e expõe as ações de autenticação.
 *
 * Ao montar, tenta restaurar a sessão: como o access token vive só em memória
 * (se perde num F5), fazemos refresh silencioso (POST /auth/refresh via cookie
 * httpOnly) e depois GET /auth/me. Enquanto isso, `carregando` fica true para
 * evitar telas piscando.
 */
export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  // Começa true para permitir o refresh silencioso no load (mesmo sem access).
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    let ativo = true

    async function restaurarSessao() {
      try {
        // 1) Garante access válido (renova via cookie se estiver fora de
        //    memória). Se não houver sessão, interrompe sem erro.
        const renovou = await authService.restaurarSessaoViaRefresh()
        if (!renovou) {
          if (ativo) {
            setUsuario(null)
            setCarregando(false)
          }
          return
        }
        // 2) Busca o perfil do usuário com o access renovado.
        const dados = await authService.me()
        if (ativo) setUsuario(dados)
      } catch {
        // Sessão inválida/expirada — interceptor já limpou a memória.
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

  const logout = useCallback(async () => {
    await authService.logout()
    setUsuario(null)
  }, [])

  const atualizarUsuario = useCallback((dados) => {
    setUsuario((atual) => ({ ...atual, ...dados }))
  }, [])

  const value = useMemo(
    () => ({
      usuario,
      autenticado: Boolean(usuario),
      carregando,
      login,
      logout,
      atualizarUsuario,
      // Reexportado para o formulário mapear erros sem importar o client.
      toApiError,
    }),
    [usuario, carregando, login, logout, atualizarUsuario],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export default AuthProvider
