import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import cartService from '../api/cart'
import productService from '../api/products'
import { itensParaView, produtoParaRecomendacao } from '../api/adapters'
import { useAuth } from './auth-context'
import CartContext from './cart-context'


export function CartProvider({ children }) {
  const { usuario, autenticado } = useAuth()

  const [itens, setItens] = useState([])
  const [cartId, setCartId] = useState(null)
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState(null)


  const userId = autenticado ? (usuario?.id ?? null) : null


  const cartStateRef = useRef({ id: null, promise: null })

  const garantirCarrinho = useCallback(async () => {

    if (cartStateRef.current.id) {
      return cartStateRef.current.id
    }

    if (cartStateRef.current.promise) {
      return cartStateRef.current.promise
    }

    const promise = (async () => {
      try {
        const carrinho = await cartService.obter()
        cartStateRef.current.id = carrinho.id
        return carrinho.id
      } catch {
 
        try {
          const criado = await cartService.criar()
          cartStateRef.current.id = criado.id
          return criado.id
        } catch {


          const existente = await cartService.obter()
          cartStateRef.current.id = existente.id
          return existente.id
        }
      }
    })()

    cartStateRef.current.promise = promise
    try {
      return await promise
    } finally {
      cartStateRef.current.promise = null
    }
  }, [])


  const recarregar = useCallback(async () => {
    if (!userId) return

    await Promise.resolve()
    setCarregando(true)
    setErro(null)
    try {
      const id = await garantirCarrinho()
      const carrinho = await cartService.obter()
      setCartId(id)
      setItens(itensParaView(carrinho.cart_items))
    } catch (error) {
      setErro(error)
      setItens([])
    } finally {
      setCarregando(false)
    }
  }, [userId, garantirCarrinho])


  const [sessaoAnterior, setSessaoAnterior] = useState(userId)
  if (sessaoAnterior !== userId) {
    setSessaoAnterior(userId)
    if (!userId && sessaoAnterior) {
      setItens([])
      setCartId(null)
    }
  }


  useEffect(() => {
    if (!userId) {
      cartStateRef.current = { id: null, promise: null }
    }
  }, [userId])


  useEffect(() => {
    if (!userId) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    recarregar()
  }, [userId, recarregar])


  const idDoCarrinho = useCallback(async () => {
    if (cartId) return cartId
    if (!userId) return null
    return garantirCarrinho()
  }, [cartId, userId, garantirCarrinho])

  const adicionar = useCallback(
    async (produto, quantidade = 1) => {
      // Visitante: apenas estado local.
      if (!userId) {
        setItens((atual) => {
          const existente = atual.find((i) => i.id === produto.id)
          if (existente) {
            return atual.map((i) =>
              i.id === produto.id
                ? { ...i, quantidade: i.quantidade + quantidade }
                : i,
            )
          }
          return [...atual, { ...produto, quantidade }]
        })
        return
      }

      const id = await idDoCarrinho()
      await cartService.adicionarItem(id, produto.id, quantidade)
      await recarregar()
    },
    [userId, idDoCarrinho, recarregar],
  )

  const alterarQuantidade = useCallback(
    async (itemId, quantidade) => {
      if (!userId) {
        setItens((atual) =>
          atual.map((i) => (i.id === itemId ? { ...i, quantidade } : i)),
        )
        return
      }

      const id = await idDoCarrinho()
      await cartService.atualizarQuantidade(id, itemId, quantidade)
      await recarregar()
    },
    [userId, idDoCarrinho, recarregar],
  )

  const remover = useCallback(
    async (itemId) => {
      if (!userId) {
        setItens((atual) => atual.filter((i) => i.id !== itemId))
        return
      }

      const id = await idDoCarrinho()
      await cartService.removerItem(id, itemId)
      await recarregar()
    },
    [userId, idDoCarrinho, recarregar],
  )

  const limpar = useCallback(async () => {
    if (!userId) {
      setItens([])
      return
    }

    const id = await idDoCarrinho()
    await cartService.limpar(id)
    await recarregar()
  }, [userId, idDoCarrinho, recarregar])


  const recomendados = useCallback(async (limite = 4) => {
    const naSacola = itens.map((i) => i.productId)
    const produtos = await productService.recomendacoes(naSacola, limite)
    return produtos.map(produtoParaRecomendacao)
  }, [itens])

  const totalItens = useMemo(
    () => itens.reduce((acc, item) => acc + item.quantidade, 0),
    [itens],
  )

  const value = useMemo(
    () => ({
      itens,
      totalItens,
      carregando,
      erro,
      recarregar,
      adicionar,
      alterarQuantidade,
      remover,
      limpar,
      recomendados,
    }),
    [
      itens,
      totalItens,
      carregando,
      erro,
      recarregar,
      adicionar,
      alterarQuantidade,
      remover,
      limpar,
      recomendados,
    ],
  )

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export default CartProvider
