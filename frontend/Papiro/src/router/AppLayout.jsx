import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'


export default function AppLayout() {
  const { pathname } = useLocation()

  // Sobe ao topo a cada troca de rota.
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' })
  }, [pathname])

  const simples = pathname === '/login' || pathname === '/registro'

  return (
    <div className="flex min-h-svh flex-col">
      <Navbar simples={simples} />

      <div className="flex flex-1 flex-col">
        <Outlet />
      </div>

      <Footer />
    </div>
  )
}