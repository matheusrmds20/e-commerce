import { useState } from 'react'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import Login from './pages/Login'
import Registro from './pages/Registro'
import DetalheLivro from './pages/DetalheLivro'
import Carrinho from './pages/Carrinho'
import Checkout from './pages/Checkout'
import Acervo from './pages/Acervo'
import MaisVendidos from './pages/MaisVendidos'
import SobreNos from './pages/SobreNos'
import Admin from './pages/Admin'
import MinhaConta from './pages/MinhaConta'
import PaginaRetornoPagamento from './components/PaginaRetornoPagamento'

import { useAuth } from './context/auth-context'
import { useCart } from './context/cart-context'

const PAGINAS = [
  'home',
  'acervo',
  'mais-vendidos',
  'sobre',
  'detalhe',
  'carrinho',
  'checkout',
  'minhaconta',
  'login',
  'registro',
  'admin',
]

/**
 * App — alterna entre as páginas enquanto ainda não há roteador.
 * Quando entrarmos com react-router, isto vira <Routes>.
 */
/**
 * Detecta o retorno do Mercado Pago pela URL.
 *
 * O backend configura `back_urls` para {FRONTEND_URL}/payment/{success,failure,pending}
 * e o Mercado Pago devolve o cliente para lá (com ?payment_id=...&status=...).
 * Como ainda não há react-router, lemos o pathname na inicialização.
 * @returns {'success'|'failure'|'pending'|null}
 */
function detectarRetornoPagamento() {
  if (typeof window === 'undefined') return null
  const match = window.location.pathname.match(/\/payment\/(success|failure|pending)\b/)
  return match ? match[1] : null
}

export default function App() {
  const { usuario } = useAuth()
  const ehAdmin = usuario?.role === 'admin'

  const [pagina, setPagina] = useState('home')
  const [produtoId, setProdutoId] = useState(null)
  const [termoBuscaGlobal, setTermoBuscaGlobal] = useState('')
  // Congela o resultado do retorno na montagem: o polling não deve ser
  // reiniciado a cada re-render (e a URL pode ter a query limpa depois).
  const [retornoPagamento] = useState(detectarRetornoPagamento)

  // Badge da sacola vem do carrinho real (API quando logado, memória se não).
  const { totalItens } = useCart()

  /**
   * Volta para a loja limpando o path de retorno do Mercado Pago, para que um
   * refresh não reabra a tela de retorno.
   */
  const voltarParaLoja = () => {
    try {
      window.history.replaceState(null, '', '/')
    } catch {
      /* histórico indisponível */
    }
    setPagina('home')
  }

  /** Abre a página de detalhe; sem id, cai no primeiro produto do catálogo. */
  const abrirLivro = (id) => {
    setProdutoId(typeof id === 'number' ? id : null)
    setPagina('detalhe')
  }

  /** Dispara uma busca da Navbar e redireciona para o Acervo com o termo */
  const handleBuscar = (termo) => {
    setTermoBuscaGlobal(termo)
    setPagina('acervo')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const renderizar = () => {
    if (retornoPagamento)
      return (
        <PaginaRetornoPagamento
          resultado={retornoPagamento}
          onVoltarParaLoja={voltarParaLoja}
        />
      )
    if (pagina === 'admin') {
      // Só administradores podem abrir o painel; qualquer outro cai na loja.
      if (!ehAdmin) return <Home onAbrirLivro={abrirLivro} onExplorarAcervo={() => setPagina('acervo')} />
      return <Admin onVoltarParaLoja={() => setPagina('home')} />
    }
    if (pagina === 'login') return <Login onEntrar={() => setPagina('home')} onRegistrar={() => setPagina('registro')} />
    if (pagina === 'registro')
      return (
        <Registro
          onConcluir={() => setPagina('home')}
          onVoltarLogin={() => setPagina('login')}
        />
      )
    if (pagina === 'minhaconta')
      return <MinhaConta onIrParaLogin={() => setPagina('login')} />
    if (pagina === 'acervo')
      return (
        <Acervo
          onAbrirLivro={abrirLivro}
          termoInicial={termoBuscaGlobal}
          onLimparBuscaInicial={() => setTermoBuscaGlobal('')}
        />
      )
    if (pagina === 'mais-vendidos')
      return (
        <MaisVendidos
          onAbrirLivro={abrirLivro}
          onExplorarAcervo={() => setPagina('acervo')}
          onVoltarHome={() => setPagina('home')}
        />
      )
    if (pagina === 'sobre')
      return (
        <SobreNos
          onExplorarAcervo={() => setPagina('acervo')}
          onVoltarHome={() => setPagina('home')}
        />
      )
    if (pagina === 'detalhe')
      return <DetalheLivro productId={produtoId ?? 1} />
    if (pagina === 'carrinho')
      return (
        <Carrinho
          onCheckout={() => setPagina('checkout')}
          onIrParaLogin={() => setPagina('login')}
        />
      )
    if (pagina === 'checkout')
      return <Checkout onIrParaLogin={() => setPagina('login')} />
    return <Home onAbrirLivro={abrirLivro} onExplorarAcervo={() => setPagina('acervo')} />
  }

  return (
    <div className="flex min-h-svh flex-col">
      {pagina !== 'admin' && !retornoPagamento && (
        <Navbar
          onNavegar={(p) => {
            if (p !== 'acervo') setTermoBuscaGlobal('')
            setPagina(p)
          }}
          onBuscar={handleBuscar}
          totalItens={totalItens}
          simples={pagina === 'login' || pagina === 'registro'}
        />
      )}

      <div className="flex-1">{renderizar()}</div>

      {pagina !== 'admin' && !retornoPagamento && <Footer onNavegar={setPagina} />}

      {/* Alternador temporário — remover ao adicionar o roteador */}
      {!retornoPagamento && (
        <nav className="fixed bottom-5 right-5 z-40 flex gap-1 bg-forest p-1 shadow-lg">
          {PAGINAS.filter((nome) => !(nome === 'admin' && !ehAdmin)).map((nome) => (
            <button
              key={nome}
              type="button"
              data-testid={`nav-${nome}`}
              onClick={() => setPagina(nome)}
              className={`px-4 py-2.5 font-body text-[0.62rem] uppercase tracking-[0.18em] transition-colors duration-300 ${
                pagina === nome
                  ? 'bg-gold text-forest'
                  : 'text-cream-soft hover:bg-forest-soft'
              }`}
            >
              {nome}
            </button>
          ))}
        </nav>
      )}
    </div>
  )
}
