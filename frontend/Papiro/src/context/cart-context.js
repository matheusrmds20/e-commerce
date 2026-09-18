import { createContext, useContext } from 'react'

// Contexto e hook separados do provider para não quebrar o fast refresh.
const CartContext = createContext(null)

/** Hook de acesso ao carrinho. */
export function useCart() {
  const ctx = useContext(CartContext)
  if (!ctx) {
    throw new Error('useCart deve ser usado dentro de <CartProvider>.')
  }
  return ctx
}

export default CartContext
