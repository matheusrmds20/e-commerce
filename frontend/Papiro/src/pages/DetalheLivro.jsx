import { useCallback, useEffect, useState } from 'react'
import Estrelas from '../components/Estrelas'
import GaleriaLivro from '../components/GaleriaLivro'
import PainelCompra from '../components/PainelCompra'
import DetalhesLivro from '../components/DetalhesLivro'
import { PdfIcon } from '../components/Icons'
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

/**
 * DetalheLivro — página de produto ligada à API.
 *
 * Fluxo:
 * 1. Busca `GET /products/get/{productId}` e `GET /reviews/product/{productId}`
 *    em paralelo.
 * 2. Normaliza o produto com `produtoParaDetalhe` e as avaliações com
 *    `avaliacaoParaView`.
 * 3. Monta o painel de compra real e as seções retráteis (descrição, ficha,
 *    avaliações) com os dados do backend.
 *
 * Fallbacks:
 * - Sem `productId`, usa o produto 1 (primeiro do catálogo) para manter a
 *   página navegável enquanto o roteador não existe.
 * - Produto sem avaliações: a API responde 200 com lista vazia; qualquer
 *   outra falha nessa chamada também degrada para lista vazia.
 * - Falha de rede/produto inexistente: mostra estado de erro com "tentar de novo".
 */
export default function DetalheLivro({ productId = 1 }) {
  const { usuario, autenticado } = useAuth()
  const { adicionar } = useCart()

  const [produto, setProduto] = useState(null)
  const [avaliacoes, setAvaliacoes] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const [feedback, setFeedback] = useState(null)
  const [nosDesejos, setNosDesejos] = useState(false)
  const [feedbackDesejos, setFeedbackDesejos] = useState(null)

  /** Carrega produto + avaliações. As avaliações nunca derrubam a página. */
  const carregar = useCallback(async () => {
    setCarregando(true)
    setErro(null)
    try {
      const [produtoResp, avaliacoesResp] = await Promise.all([
        productService.obter(productId),
        // Lista de avaliações nunca derruba a página: se a chamada falhar por
        // qualquer motivo, degrada para lista vazia.
        reviewService.listarPorProduto(productId).catch(() => []),
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
  }, [productId, usuario])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    carregar()
  }, [carregar])

  // Verifica se o produto já está na wishlist do usuário logado.
  useEffect(() => {
    if (!autenticado || !produto) return
    let ativo = true
    wishlistService
      .listar(usuario.id)
      .then((lista) => {
        if (ativo) {
          setNosDesejos(lista.some((item) => item.product_id === produto.id))
        }
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

  /** Adiciona (ou confirma) o produto na wishlist do usuário logado. */
  const adicionarAosDesejos = useCallback(async () => {
    if (!produto) return
    if (!autenticado) {
      setFeedbackDesejos({
        tipo: 'erro',
        texto: 'Entre na sua conta para guardar desejos.',
      })
      return
    }
    if (nosDesejos) return

    setFeedbackDesejos(null)
    try {
      await wishlistService.adicionar(usuario.id, produto.id)
      setNosDesejos(true)
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
  }, [autenticado, usuario, produto, nosDesejos])

  /** Publica uma nova avaliação do usuário logado. */
  const enviarAvaliacao = useCallback(
    async ({ rating, comment }) => {
      if (!autenticado || !produto) return
      setEnviando(true)
      setFeedback(null)
      try {
        await reviewService.criar(usuario.id, {
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
    [autenticado, usuario, produto, carregar],
  )

  /** Remove uma avaliação do próprio usuário. */
  const excluirAvaliacao = useCallback(
    async (reviewId) => {
      if (!autenticado || !usuario) return
      setFeedback(null)
      try {
        await reviewService.excluir(reviewId, usuario.id)
        await carregar()
        setFeedback({ tipo: 'sucesso', texto: 'Avaliação removida.' })
      } catch (error) {
        setFeedback({
          tipo: 'erro',
          texto: error?.message ?? 'Não foi possível remover a avaliação.',
        })
      }
    },
    [autenticado, usuario, carregar],
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
                onAdicionarDesejos={adicionarAosDesejos}
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
            enviando={enviando}
            feedback={feedback}
            onAvaliar={enviarAvaliacao}
            onExcluirAvaliacao={excluirAvaliacao}
          />
        </div>

        {/* Rodapé da página */}
        <div className="flex flex-col items-center gap-6 py-14 sm:flex-row sm:justify-between">
          <div className="flex items-center gap-4">
            <PdfIcon className="h-6 w-6 text-coffee-soft" />
            <div>
              <p className="font-body text-[0.75rem] font-semibold uppercase tracking-[0.2em] text-coffee-faint">
                Ficha técnica
              </p>
              <p className="font-body text-[0.92rem] font-medium text-coffee-soft">
                Baixe a ficha completa em PDF
              </p>
            </div>
          </div>

          <nav className="flex flex-wrap items-center justify-center gap-6">
            {['Sobre nós', 'Contato', 'Envio e devoluções', 'Privacidade'].map(
              (item) => (
                <a
                  key={item}
                  href="#"
                  className="font-body text-[0.88rem] font-medium text-coffee-soft transition-colors duration-300 hover:text-gold"
                >
                  {item}
                </a>
              ),
            )}
          </nav>
        </div>
      </div>
    </main>
  )
}
