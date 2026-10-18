import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import Estrelas from '../components/Estrelas'
import GaleriaLivro from '../components/GaleriaLivro'
import PainelCompra from '../components/PainelCompra'
import DetalhesLivro from '../components/DetalhesLivro'
import productService from '../api/products'
import reviewService from '../api/reviews'
import {
  avaliacaoParaView,
  formatarPreco,
  mediaAvaliacoes,
  produtoParaDetalhe,
} from '../api/adapters'
import { useAuth } from '../context/auth-context'
import { useCart } from '../context/cart-context'
import wishlistService from '../api/wishlist'
import orderService from '../api/orders'


export default function DetalheLivro() {
  const { productId } = useParams()
  const id = Number(productId)
  // Fallback para o primeiro produto quando não há id ou ele é inválido.
  const idProduto = Number.isInteger(id) && id > 0 ? id : 1

  const { usuario, autenticado } = useAuth()
  const { adicionar } = useCart()

  const [produto, setProduto] = useState(null)
  const [avaliacoes, setAvaliacoes] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const [feedback, setFeedback] = useState(null)
  const [nosDesejos, setNosDesejos] = useState(false)
  const [wishlistItemId, setWishlistItemId] = useState(null)
  const [feedbackDesejos, setFeedbackDesejos] = useState(null)
  const [comprou, setComprou] = useState(false)

  /** Carrega produto + avaliações. As avaliações nunca derrubam a página. */
  const carregar = useCallback(async () => {
    setCarregando(true)
    setErro(null)
    try {
      const [produtoResp, avaliacoesResp] = await Promise.all([
        productService.obter(idProduto),
        // Lista de avaliações nunca derruba a página: se a chamada falhar por
        // qualquer motivo, degrada para lista vazia.
        reviewService.listarPorProduto(idProduto).catch(() => []),
      ])

      const view = produtoParaDetalhe(produtoResp)
      const lista = (avaliacoesResp ?? []).map((r) =>
        avaliacaoParaView(r, usuario),
      )

      setProduto({
        ...view,
        nota: mediaAvaliacoes(lista),
        totalAvaliacoes: lista.length,
      })
      setAvaliacoes(lista)
    } catch (error) {
      setErro(error)
      setProduto(null)
      setAvaliacoes([])
    } finally {
      setCarregando(false)
    }
  }, [idProduto, usuario])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    carregar()
  }, [carregar])

  // Verifica se o usuário autenticado já comprou este livro.
  useEffect(() => {
    if (!autenticado || !produto?.id) return
    let ativo = true
    orderService
      .listar()
      .then((pedidos) => {
        if (!ativo) return
        const comprouLivro = (pedidos ?? []).some(
          (p) =>
            p.status !== 'cancelled' &&
            p.order_items?.some((item) => item.product_id === produto.id),
        )
        setComprou(comprouLivro)
      })
      .catch(() => {
        if (ativo) setComprou(false)
      })
    return () => {
      ativo = false
    }
  }, [autenticado, produto?.id])


  useEffect(() => {
    if (!autenticado || !produto) return
    let ativo = true
    wishlistService
      .buscarPorProduto(produto.id)
      .then((itens) => {
        if (!ativo) return
        const item = (itens ?? []).find(
          (i) => i.user_id === usuario?.id,
        )
        setNosDesejos(Boolean(item))
        setWishlistItemId(item?.id ?? null)
      })
      .catch(() => {})
    return () => {
      ativo = false
    }
  }, [autenticado, usuario, produto])

  /** Adiciona o produto atual à sacola (visitante: memória; logado: API). */
  const adicionarASacola = useCallback(async () => {
    if (!produto) return
    try {
      await adicionar({
        id: produto.id,
        titulo: produto.titulo,
        autor: produto.autor,
        preco: produto.preco,
        imagem: produto.imagens[0] ?? '',
        stockQty: produto.stockQty,
      })
      setFeedback({ tipo: 'sucesso', texto: 'Adicionado à sacola.' })
    } catch {
      setFeedback({
        tipo: 'erro',
        texto: 'Não foi possível adicionar à sacola.',
      })
    }
  }, [adicionar, produto])

  /** Adiciona ou remove o produto da wishlist (toggle). */
  const alternarDesejo = useCallback(async () => {
    if (!produto) return
    if (!autenticado) {
      setFeedbackDesejos({
        tipo: 'erro',
        texto: 'Entre na sua conta para guardar desejos.',
      })
      return
    }

    setFeedbackDesejos(null)

    // Remoção: já está nos desejos. Se por algum motivo não temos o id do item
    // (ex.: vindo de um 409), resolvemos via `buscarPorProduto` antes de remover.
    if (nosDesejos) {
      let itemId = wishlistItemId
      if (itemId == null) {
        try {
          const itens = await wishlistService.buscarPorProduto(produto.id)
          itemId = (itens ?? []).find((i) => i.user_id === usuario?.id)?.id ?? null
        } catch {
          itemId = null
        }
      }

      if (itemId == null) {
        setFeedbackDesejos({
          tipo: 'erro',
          texto: 'Não foi possível localizar o item para remover.',
        })
        return
      }

      try {
        await wishlistService.excluir(itemId)
        setNosDesejos(false)
        setWishlistItemId(null)
        setFeedbackDesejos({
          tipo: 'sucesso',
          texto: 'Removido da sua lista de desejos.',
        })
      } catch (error) {
        setFeedbackDesejos({
          tipo: 'erro',
          texto: error?.message ?? 'Não foi possível remover o desejo.',
        })
      }
      return
    }

    // Adição.
    try {
      const criado = await wishlistService.adicionar(produto.id)
      setNosDesejos(true)
      setWishlistItemId(criado?.id ?? null)
      setFeedbackDesejos({
        tipo: 'sucesso',
        texto: 'Guardado na sua lista de desejos.',
      })
    } catch (error) {
      // 409 = já estava na wishlist — tratamos como sucesso visual.
      if (error?.code === 'WISHLIST_DUPLICATE' || error?.status === 409) {
        setNosDesejos(true)
        setFeedbackDesejos(null)
        return
      }
      setFeedbackDesejos({
        tipo: 'erro',
        texto: error?.message ?? 'Não foi possível guardar o desejo.',
      })
    }
  }, [autenticado, usuario, produto, nosDesejos, wishlistItemId])

  /** Publica uma nova avaliação do usuário logado. */
  const enviarAvaliacao = useCallback(
    async ({ rating, comment }) => {
      if (!autenticado || !produto) return
      setEnviando(true)
      setFeedback(null)
      try {
        await reviewService.criar({
          product_id: produto.id,
          rating,
          comment,
        })
        await carregar()
        setFeedback({ tipo: 'sucesso', texto: 'Avaliação publicada.' })
      } catch (error) {
        setFeedback({
          tipo: 'erro',
          texto: error?.message ?? 'Não foi possível publicar a avaliação.',
        })
      } finally {
        setEnviando(false)
      }
    },
    [autenticado, produto, carregar],
  )

  /** Salva a edição de uma avaliação do próprio usuário. */
  const salvarEdicaoAvaliacao = useCallback(
    async (reviewId, { rating, comment }) => {
      if (!autenticado || !produto) return
      setFeedback(null)
      try {
        await reviewService.atualizar(reviewId, { rating, comment })
        await carregar()
        setFeedback({ tipo: 'sucesso', texto: 'Avaliação atualizada.' })
      } catch (error) {
        setFeedback({
          tipo: 'erro',
          texto: error?.message ?? 'Não foi possível atualizar a avaliação.',
        })
      }
    },
    [autenticado, produto, carregar],
  )

  /** Remove uma avaliação do próprio usuário. */
  const excluirAvaliacao = useCallback(
    async (reviewId) => {
      if (!autenticado) return
      setFeedback(null)
      try {
        await reviewService.excluir(reviewId)
        await carregar()
        setFeedback({ tipo: 'sucesso', texto: 'Avaliação removida.' })
      } catch (error) {
        setFeedback({
          tipo: 'erro',
          texto: error?.message ?? 'Não foi possível remover a avaliação.',
        })
      }
    },
    [autenticado, carregar],
  )

  if (carregando) {
    return (
      <main className="bg-cream-deep">
        <div className="mx-auto max-w-[1400px] px-5 pt-7 sm:px-8">
          <p className="py-24 text-center font-body text-coffee-soft">
            Carregando livro…
          </p>
        </div>
      </main>
    )
  }

  if (erro || !produto) {
    return (
      <main className="bg-cream-deep">
        <div className="mx-auto max-w-[1400px] px-5 pt-7 sm:px-8">
          <div className="py-24 text-center">
            <p className="font-display text-[1.8rem] text-coffee">
              Não encontramos este livro.
            </p>
            <p className="mt-3 font-body text-[0.95rem] text-coffee-soft">
              {erro?.message ?? 'Tente novamente em instantes.'}
            </p>
            <button
              type="button"
              onClick={carregar}
              className="mt-6 rounded-sm bg-forest px-6 py-3 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft transition-colors duration-300 hover:bg-forest-soft"
            >
              Tentar de novo
            </button>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="bg-cream-deep">
      <div className="mx-auto max-w-[1400px] px-5 pt-7 sm:px-8">
        {/* Topo: galeria + informações */}
        <div className="grid items-start gap-10 lg:grid-cols-2 lg:gap-14">
          <GaleriaLivro imagens={produto.imagens} titulo={produto.titulo} />

          <div>
            <h1 className="font-display text-[2.5rem] leading-[1.1] font-normal tracking-[-0.01em] text-coffee sm:text-[3.2rem]">
              {produto.titulo}
            </h1>

            <p className="mt-3 font-body text-[1rem] font-medium text-coffee-soft">
              por{' '}
              <span className="text-coffee font-semibold">{produto.autor}</span>{' '}
              (Autor)
            </p>

            <div className="mt-3.5 flex flex-wrap items-center gap-3">
              <Estrelas nota={produto.nota} />
              <span className="font-body text-[0.88rem] font-medium text-coffee-soft">
                {produto.nota} ({produto.totalAvaliacoes.toLocaleString('pt-BR')}{' '}
                avaliações)
              </span>
              <a
                href="#avaliacoes"
                className="font-body text-[0.88rem] font-medium text-coffee transition-colors duration-300 hover:text-gold"
              >
                Ler avaliações
              </a>
            </div>

            <p className="mt-6 max-w-[38rem] font-body text-[0.98rem] font-normal leading-relaxed text-coffee-soft">
              {produto.subtitulo}
            </p>

            <div className="mt-8 rounded-md border border-line bg-cream-soft p-6 sm:p-7">
              <PainelCompra
                preco={formatarPreco(produto.preco)}
                precoAntigo={
                  produto.precoAntigo ? formatarPreco(produto.precoAntigo) : null
                }
                desconto={produto.desconto}
                stockQty={produto.stockQty}
                onAdicionar={adicionarASacola}
                feedback={feedback}
                onAdicionarDesejos={alternarDesejo}
                nosDesejos={nosDesejos}
                feedbackDesejos={feedbackDesejos}
              />
            </div>
          </div>
        </div>

        {/* Seções retráteis */}
        <div id="avaliacoes" className="mt-16 border-b border-line">
          <DetalhesLivro
            descricao={produto.descricao}
            ficha={produto}
            avaliacoes={avaliacoes}
            autenticado={autenticado}
            comprou={comprou}
            enviando={enviando}
            feedback={feedback}
            onAvaliar={enviarAvaliacao}
            onEditarAvaliacao={salvarEdicaoAvaliacao}
            onExcluirAvaliacao={excluirAvaliacao}
          />
        </div>
      </div>
    </main>
  )
}
