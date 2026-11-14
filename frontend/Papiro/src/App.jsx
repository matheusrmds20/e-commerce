import { useEffect } from 'react'
import { BrowserRouter, useLocation } from 'react-router-dom'
import Rotas from './router/Rotas'

/**
 * Garante rolagem ao topo na navegação entre páginas,
 * respeitando as preferências de acessibilidade com motion-safe.
 */
function ScrollToTop() {
  const { pathname } = useLocation()

  useEffect(() => {
    const prefereReduzido = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches
    window.scrollTo({
      top: 0,
      behavior: prefereReduzido ? 'instant' : 'smooth',
    })
  }, [pathname])

  return null
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <Rotas />
    </BrowserRouter>
  )
}
