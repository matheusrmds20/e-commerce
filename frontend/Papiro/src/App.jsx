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
import Admin from './pages/Admin'
import MinhaConta from './pages/MinhaConta'

import { useCart } from './context/cart-context'

const PAGINAS = [
  'home',
  'acervo',
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
export default function App() {
  const [pagina, setPagina] = useState('home')
  const [produtoId, setProdutoId] = useState(null)

  // Badge da sacola vem do carrinho real (API quando logado, memória se não).
  const { totalItens } = useCart()

  /** Abre a página de detalhe; sem id, cai no primeiro produto do catálogo. */
  const abrirLivro = (id) => {
    setProdutoId(typeof id === 'number' ? id : null)
    setPagina('detalhe')
  }

  const renderizar = () => {
    if (pagina === 'admin') return <Admin onVoltarParaLoja={() => setPagina('home')} />
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
    if (pagina === 'acervo') return <Acervo onAbrirLivro={abrirLivro} />
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
      {pagina !== 'admin' && (
        <Navbar
          onNavegar={setPagina}
          totalItens={totalItens}
          simples={pagina === 'login' || pagina === 'registro'}
        />
      )}

      <div className="flex-1">{renderizar()}</div>

      {pagina !== 'admin' && <Footer />}

      {/* Alternador temporário — remover ao adicionar o roteador */}
      <nav className="fixed bottom-5 right-5 z-40 flex gap-1 bg-forest p-1 shadow-lg">
        {PAGINAS.map((nome) => (
          <button
            key={nome}
            type="button"
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
    </div>
  )
}
