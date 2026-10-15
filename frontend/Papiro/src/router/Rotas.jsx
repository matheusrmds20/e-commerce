import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './AppLayout'

// Páginas da loja — carregadas sob demanda (code-splitting por rota).
const Home = lazy(() => import('../pages/Home'))
const Acervo = lazy(() => import('../pages/Acervo'))
const DetalheLivro = lazy(() => import('../pages/DetalheLivro'))
const MaisVendidos = lazy(() => import('../pages/MaisVendidos'))
const SobreNos = lazy(() => import('../pages/SobreNos'))
const Carrinho = lazy(() => import('../pages/Carrinho'))
const Checkout = lazy(() => import('../pages/Checkout'))
const MinhaConta = lazy(() => import('../pages/MinhaConta'))
const Login = lazy(() => import('../pages/Login'))
const Registro = lazy(() => import('../pages/Registro'))
const Admin = lazy(() => import('../pages/Admin'))
const PaginaRetornoPagamento = lazy(() =>
  import('../components/PaginaRetornoPagamento'),
)

import { useAuth } from '../context/auth-context'

/** Guard da área administrativa: só admins entram; os demais caem na loja. */
function AdminRota() {
  const { usuario } = useAuth()
  const ehAdmin = usuario?.role === 'admin'

  if (!ehAdmin) return <Navigate to="/" replace />

  return <Admin />
}

/** Fallback de carregamento do lazy. */
function Carregando() {
  return <div className="min-h-svh bg-cream-deep" aria-busy="true" />
}


export default function Rotas() {
  return (
    <Suspense fallback={<Carregando />}>
      <Routes>
        {/* Páginas da loja — dentro da moldura (Navbar + Footer). */}
        <Route element={<AppLayout />}>
          <Route index element={<Home />} />
          <Route path="acervo" element={<Acervo />} />
          <Route path="livro/:productId" element={<DetalheLivro />} />
          <Route
            path="mais-vendidos"
            element={<MaisVendidos />}
          />
          <Route path="sobre" element={<SobreNos />} />
          <Route path="carrinho" element={<Carrinho />} />
          <Route path="checkout" element={<Checkout />} />
          <Route path="minhaconta" element={<MinhaConta />} />
          <Route path="login" element={<Login />} />
          <Route path="registro" element={<Registro />} />
        </Route>

        {/* Fora da moldura */}
        <Route path="admin" element={<AdminRota />} />
        <Route path="payment/:status" element={<PaginaRetornoPagamento />} />

        {/* Rota desconhecida → loja */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}