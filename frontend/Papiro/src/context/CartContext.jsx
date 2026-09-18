import { useCallback, useEffect, useMemo, useState } from 'react'
import cartService from '../api/cart'
import productService from '../api/products'
import { itensParaView, produtoParaRecomendacao } from '../api/adapters'
import { useAuth } from './auth-context'
import CartContext from './cart-context'

/**
 * CartProvider — fonte única do carrinho.
 *
 * Estratégia:
 * - **Autenticado:** lê e escreve no backend. O `cart_id` é resolvido uma vez
 *   (cria o carrinho se ainda não existir).
 * - **Visitante:** mantém os itens apenas em memória. As rotas de carrinho
 *   exigem Bearer token, então não há como persistir sem login.
 *
 * Em ambos os casos a UI consome a mesma interface.
 */
export function CartProvider({ children }) {
  const { usuario, autenticado } = useAuth()

  const [itens, setItens] = useState([])
  const [cartId, setCartId] = useState(null)
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState(null)

  // Primitivos estáveis — `usuario?.id` dentro de useCallback impede o
  // React Compiler de preservar a memoização (regra preserve-manual-memoization).
  const userId = autenticado ? (usuario?.id ?? null) : null

  /** Garante um carrinho para o usuário e devolve o cart_id. */
  const garantirCarrinho = useCallback(async () => {
    try {
      const carrinho = await cartService.obter()
      setCartId(carrinho.id)
      return carrinho.id
    } catch {
      // 404/400 → ainda não existe carrinho para este usuário.
      const criado = await cartService.criar()
      setCartId(criado.id)
      return criado.id
    }
  }, [])

  /**
   * Recarrega o carrinho do servidor. Só faz sentido com sessão ativa.
   *
   * Nota: o `setCarregando(true)` vem depois do primeiro `await` de propósito.
   * Setar estado de forma síncrona no corpo de um effect dispara cascading
   * render (react-hooks/set-state-in-effect). Assim o effect só agenda a
   * busca e o estado é atualizado quando a promise resolve.
   */
  const recarregar = useCallback(async () => {
    if (!userId) return

    await Promise.resolve()
    setCarregando(true)
    setErro(null)
    try {
      const id = await garantirCarrinho()
      const carrinho = await cartService.obter()
      setCartId(id)
      setItens(itensParaView(carrinho.items))
    } catch (error) {
      setErro(error)
      setItens([])
    } finally {
      setCarregando(false)
    }
  }, [userId, garantirCarrinho])

  // Reset síncrono durante o render quando a sessão termina.
  // É o padrão recomendado pelo React para "ajustar estado quando algo muda"
  // (evita o setState dentro de effect e o cascading render que ele gera).
  const [sessaoAnterior, setSessaoAnterior] = useState(userId)
  if (sessaoAnterior !== userId) {
    setSessaoAnterior(userId)
    if (!userId && sessaoAnterior) {
      setItens([])
      setCartId(null)
    }
  }

  // Sincroniza o carrinho ao entrar na conta.
  // `recarregar` é async e só toca estado após um await, mas a regra nova
  // `react-hooks/set-state-in-effect` ainda rastreia o setState através da
  // fronteira assíncrona. Este é um fetch de dados disparado por mudança de
  // sessão — uso legítimo de effect.
  useEffect(() => {
    if (!userId) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    recarregar()
  }, [userId, recarregar])

  /** Resolve o cart_id sob demanda. */
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

  /**
   * Recomendações do catálogo, excluindo o que já está na sacola.
   *
   * O filtro e o limite agora acontecem no servidor
   * (`GET /products/recommendations?exclude=...&limit=...`). Antes, esta função
   * baixava o catálogo INTEIRO e filtrava em memória — e como ela é recriada a
   * cada mudança de `itens`, o catálogo era rebaixado toda vez que o usuário
   * adicionava ou removia um produto.
   */
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
