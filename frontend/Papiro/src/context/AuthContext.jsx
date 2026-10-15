import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'
import authService from '../api/auth'
import { toApiError } from '../api/client'
import AuthContext from './auth-context'


export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  // Começa true para permitir o refresh silencioso no load (mesmo sem access).
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    let ativo = true

    async function restaurarSessao() {
      try {

        const renovou = await authService.restaurarSessaoViaRefresh()
        if (!renovou) {
          if (ativo) {
            setUsuario(null)
            setCarregando(false)
          }
          return
        }

        const dados = await authService.me()
        if (ativo) setUsuario(dados)
      } catch {
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
      toApiError,
    }),
    [usuario, carregando, login, logout, atualizarUsuario],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export default AuthProvider
