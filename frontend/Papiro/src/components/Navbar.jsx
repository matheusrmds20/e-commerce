import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
 BagIcon,
 CloseIcon,
 SearchIcon,
 UserIcon,
} from './Icons'
import { useAuth } from '../context/auth-context'
import { useCart } from '../context/cart-context'

/** Primeiro nome do usuário, para um cumprimento curto. */
function primeiroNome(nomeCompleto) {
 return nomeCompleto?.trim().split(/\s+/)[0] ?? ''
}


export default function Navbar({ simples = false }) {
 const navigate = useNavigate()
 const [searchOpen, setSearchOpen] = useState(false)
 const [scrolled, setScrolled] = useState(false)
 const [contaOpen, setContaOpen] = useState(false)
 const [buscaInput, setBuscaInput] = useState('')

 const { usuario, autenticado, logout } = useAuth()
 const { totalItens } = useCart()
 const contaRef = useRef(null)
 const searchInputRef = useRef(null)

 // Foca no input ao abrir a barra de busca
 useEffect(() => {
 if (searchOpen) {
 setTimeout(() => searchInputRef.current?.focus(), 100)
 }
 }, [searchOpen])

 // Fecha o menu de conta ao clicar fora ou pressionar Esc.
 useEffect(() => {
 if (!contaOpen) return

 const onClickFora = (event) => {
 if (!contaRef.current?.contains(event.target)) setContaOpen(false)
 }
 const onKeyDown = (event) => {
 if (event.key === 'Escape') setContaOpen(false)
 }

 document.addEventListener('mousedown', onClickFora)
 document.addEventListener('keydown', onKeyDown)
 return () => {
 document.removeEventListener('mousedown', onClickFora)
 document.removeEventListener('keydown', onKeyDown)
 }
 }, [contaOpen])

 const handleSair = () => {
 logout()
 setContaOpen(false)
 navigate('/')
 }

 const handleConta = () => {
 if (autenticado) {
 setContaOpen((aberto) => !aberto)
 } else {
 navigate('/login')
 }
 }

 // Sacola sempre visível. Para visitante não existe carrinho no servidor (o
 // `CartContext` exige `userId` e sai calado sem ele), então o clique leva ao
 // login com retorno para /carrinho — em vez de um ícone que promete algo que
 // não acontece.
 const irParaSacola = () => {
 if (autenticado) navigate('/carrinho')
 else navigate('/login?redirect=%2Fcarrinho')
 }

 // Busca: o mesmo submit serve ao campo do desktop e à barra do mobile.
 const enviarBusca = (evento) => {
 evento.preventDefault()
 const termo = buscaInput.trim()
 if (!termo) return
 navigate({ pathname: '/acervo', search: `?termo=${encodeURIComponent(termo)}` })
 setSearchOpen(false)
 }

 useEffect(() => {
 const onScroll = () => setScrolled(window.scrollY > 40)
 onScroll()
 window.addEventListener('scroll', onScroll, { passive: true })
 return () => window.removeEventListener('scroll', onScroll)
 }, [])

 return (
 <header
 className={`sticky top-0 z-40 border-b bg-cream-soft/95 backdrop-blur-sm transition-colors duration-500 ease-[var(--ease-cozy)] ${
 scrolled ? 'border-line' : 'border-transparent'
 }`}
 >
 <nav className="mx-auto grid h-[74px] max-w-[1400px] grid-cols-2 items-center px-5 sm:px-8 md:grid-cols-[1fr_minmax(0,680px)_1fr] md:gap-6">
        {/* Esquerda — logotipo */}
        <div className="flex items-center justify-start">
          <a
            href="/"
            onClick={(event) => {
              event.preventDefault()
              navigate('/')
            }}
            className="shrink-0 font-display text-2xl font-medium leading-none tracking-[-0.01em] text-coffee sm:text-3xl"
          >
            Papiro
          </a>
        </div>

        {/* Centro — busca desktop centralizada e ampla */}
        {!simples && (
          <form
            role="search"
            onSubmit={enviarBusca}
            className="hidden w-full items-center justify-center md:flex"
          >
            <label htmlFor="busca-topo" className="sr-only">
              Buscar no acervo
            </label>
            <div className="relative w-full max-w-[640px]">
              <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-coffee-faint" />
              <input
                id="busca-topo"
                type="search"
                value={buscaInput}
                onChange={(e) => setBuscaInput(e.target.value)}
                placeholder="Busque por título, autor ou assunto…"
                className="campo w-full py-2.5 pl-10 pr-4 text-sm shadow-sm"
              />
            </div>
          </form>
        )}

        {/* Direita — busca (mobile), conta e sacola */}
        <div className="flex items-center justify-end gap-1">
          {!simples && (
            <>
              <button
                type="button"
                onClick={() => setSearchOpen((open) => !open)}
                aria-label="Buscar"
                aria-expanded={searchOpen}
                className="grid h-10 w-10 place-items-center text-coffee transition-colors duration-150 hover:text-gold md:hidden"
              >
                {searchOpen ? <CloseIcon /> : <SearchIcon />}
              </button>

              <div className="relative" ref={contaRef}>
                <button
                  type="button"
                  data-testid="navbar-login"
                  onClick={handleConta}
                  aria-label={
                    autenticado
                      ? `Minha conta — ${usuario?.full_name}`
                      : 'Entrar na minha conta'
                  }
                  aria-haspopup={autenticado ? 'menu' : undefined}
                  aria-expanded={autenticado ? contaOpen : undefined}
                  className={`grid h-10 w-10 place-items-center transition-colors duration-150 hover:text-gold ${
                    autenticado ? 'text-gold' : 'text-coffee'
                  }`}
                >
                  <UserIcon />
                </button>

                {autenticado && contaOpen && (
                  <div
                    role="menu"
                    className="absolute right-0 top-12 w-60 rounded-sm border border-line bg-cream-soft p-1.5 shadow-float"
                  >
                    <div className="border-b border-line px-3 pb-3 pt-2">
                      <p className="font-display text-base font-medium leading-tight text-coffee">
                        Olá, {primeiroNome(usuario?.full_name)}
                      </p>
                      <p className="mt-1 truncate font-body text-2xs tracking-wide text-coffee-faint">
                        {usuario?.email}
                      </p>
                    </div>

                    <button
                      type="button"
                      role="menuitem"
                      onClick={() => {
                        setContaOpen(false)
                        navigate('/minhaconta')
                      }}
                      className="mt-1.5 w-full px-3 py-2.5 text-left font-body text-xs font-medium tracking-wide text-coffee transition-colors duration-150 hover:bg-forest-soft/10 hover:text-gold"
                    >
                      Minha conta
                    </button>

                    {usuario?.role === 'admin' && (
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => {
                          setContaOpen(false)
                          navigate('/admin')
                        }}
                        className="flex w-full items-center justify-between px-3 py-2.5 text-left font-body text-xs font-medium tracking-wide text-coffee transition-colors duration-150 hover:bg-forest-soft/10 hover:text-gold"
                      >
                        <span>Painel Administrativo</span>
                        <span className="rounded bg-forest px-1.5 py-0.5 font-body text-2xs text-cream">Curadoria</span>
                      </button>
                    )}

                    <button
                      type="button"
                      role="menuitem"
                      onClick={handleSair}
                      className="mt-1 w-full border-t border-line px-3 py-2 text-left font-body text-xs font-medium tracking-wide text-coffee-soft transition-colors duration-150 hover:bg-forest-soft/10 hover:text-gold"
                    >
                      Sair da conta
                    </button>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Sacola — sempre visível, vazia ou cheia */}
          <button
            type="button"
            data-testid="navbar-sacola"
            onClick={irParaSacola}
            aria-label={
              autenticado
                ? `Sacola — ${totalItens} ${totalItens === 1 ? 'item' : 'itens'}`
                : 'Sacola — entre para ver sua sacola'
            }
            className="relative grid h-10 w-10 place-items-center text-coffee transition-colors duration-150 hover:text-gold"
          >
            <BagIcon />
            {totalItens > 0 && (
              <span
                aria-hidden="true"
                className="absolute right-1 top-1 grid h-4 min-w-4 place-items-center rounded-full bg-gold px-1 font-body text-2xs font-medium tabular-nums text-cream-soft"
              >
                {totalItens}
              </span>
            )}
          </button>
        </div>
      </nav>

 {/* Busca expansível — só no mobile. No desktop o campo já vive no header,
 então ter os dois seria dois `role="search"` na mesma página. */}
 <div
 className={`overflow-hidden border-line bg-cream-soft transition-[max-height,border-width] duration-250 ease-[var(--ease-cozy)] md:hidden ${
 searchOpen ? 'max-h-28 border-t' : 'max-h-0 border-t-0'
 }`}
 >
 <form
 onSubmit={enviarBusca}
 className="mx-auto flex max-w-[1400px] items-center gap-3 px-5 py-4 sm:px-8"
 >
 <label htmlFor="busca-mobile" className="sr-only">
 Buscar no acervo
 </label>
 <input
 id="busca-mobile"
 ref={searchInputRef}
 type="search"
 value={buscaInput}
 onChange={(e) => setBuscaInput(e.target.value)}
 placeholder="Busque por título, autor ou assunto…"
 className="w-full bg-transparent font-display text-lg text-coffee placeholder:text-coffee-faint focus:not-focus-visible:outline-none focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-forest"
 />
 <button
 type="submit"
 className="shrink-0 rounded-sm bg-forest px-5 py-2 font-body text-xs font-semibold text-cream-soft transition-colors duration-150 hover:bg-forest-soft"
 >
 Buscar
 </button>
 </form>
 </div>
 </header>
 )
}
