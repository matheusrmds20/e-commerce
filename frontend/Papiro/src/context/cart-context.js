import { createContext, useContext } from 'react'

const CartContext = createContext(null)

export function useCart() {
  const ctx = useContext(CartContext)
  if (!ctx) {
    throw new Error('useCart deve ser usado dentro de <CartProvider>.')
  }
  return ctx
}

export default CartContext
