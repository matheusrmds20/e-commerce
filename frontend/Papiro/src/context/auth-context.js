import { createContext, useContext } from 'react'

// Contexto e hook vivem separados do provider para não quebrar o fast refresh.
const AuthContext = createContext(null)

/** Hook de acesso ao contexto de autenticação. */
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth deve ser usado dentro de <AuthProvider>.')
  }
  return ctx
}

export default AuthContext
