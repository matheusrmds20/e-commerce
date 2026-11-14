import { Outlet, useLocation } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'


export default function AppLayout() {
  const { pathname } = useLocation()
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