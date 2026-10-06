import { useEffect, useRef, useState } from 'react'
import {
  BagIcon,
  CloseIcon,
  SearchIcon,
  UserIcon,
} from './Icons'
import { useAuth } from '../context/auth-context'

/** Primeiro nome do usuário, para um cumprimento curto. */
function primeiroNome(nomeCompleto) {
  return nomeCompleto?.trim().split(/\s+/)[0] ?? ''
}

/**
 * Navbar — barra clara e fixa, com o logotipo centralizado em serifada.
 * Some ao descer, reaparece ao subir (mantém o hero limpo).
 */
export default function Navbar({ onNavegar, onBuscar, totalItens = 0, simples = false }) {
  const [searchOpen, setSearchOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const [contaOpen, setContaOpen] = useState(false)
  const [buscaInput, setBuscaInput] = useState('')

  const { usuario, autenticado, logout } = useAuth()
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
    onNavegar?.('home')
  }

  const handleConta = () => {
    if (autenticado) {
      setContaOpen((aberto) => !aberto)
    } else {
      onNavegar?.('login')
    }
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
      <nav className="mx-auto flex h-[74px] max-w-[1400px] items-center gap-4 px-5 sm:px-8">
        {/* Centro/Esquerda — logotipo */}
        <a
          href="#"
          onClick={(event) => {
            event.preventDefault()
            onNavegar?.('home')
          }}
          className="font-display text-[1.85rem] font-medium leading-none tracking-[-0.01em] text-coffee sm:text-[2.25rem]"
        >
          Papiro
        </a>

        {/* Direita — ações */}
        {!simples && (
        <div className="ml-auto flex items-center gap-1">
          <button
            type="button"
            onClick={() => setSearchOpen((open) => !open)}
            aria-label="Buscar"
            aria-expanded={searchOpen}
            className="grid h-10 w-10 place-items-center text-coffee transition-colors duration-300 hover:text-gold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
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
              className={`grid h-10 w-10 place-items-center transition-colors duration-300 hover:text-gold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold ${
                autenticado ? 'text-gold' : 'text-coffee'
              }`}
            >
              <UserIcon />
            </button>

            {autenticado && contaOpen && (
              <div
                role="menu"
                className="absolute right-0 top-12 w-60 rounded-sm border border-line bg-cream-soft p-1.5 shadow-[0_1px_2px_rgba(75,54,33,0.04),0_18px_40px_-18px_rgba(75,54,33,0.28)]"
              >
                <div className="border-b border-line px-3 pb-3 pt-2">
                  <p className="font-display text-[1.05rem] font-medium leading-tight text-coffee">
                    Olá, {primeiroNome(usuario?.full_name)}
                  </p>
                  <p className="mt-1 truncate font-body text-[0.75rem] tracking-wide text-coffee-faint">
                    {usuario?.email}
                  </p>
                </div>

                <button
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setContaOpen(false)
                    onNavegar?.('minhaconta')
                  }}
                  className="mt-1.5 w-full px-3 py-2.5 text-left font-body text-[0.82rem] font-medium tracking-wide text-coffee transition-colors duration-300 hover:bg-forest-soft/10 hover:text-gold"
                >
                  Minha conta
                </button>

                {usuario?.role === 'admin' && (
                  <button
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      setContaOpen(false)
                      onNavegar?.('admin')
                    }}
                    className="w-full px-3 py-2.5 text-left font-body text-[0.82rem] font-medium tracking-wide text-coffee transition-colors duration-300 hover:bg-forest-soft/10 hover:text-gold flex items-center justify-between"
                  >
                    <span>Painel Administrativo</span>
                    <span className="text-[0.65rem] uppercase tracking-wider px-1.5 py-0.5 bg-forest text-cream rounded">Curadoria</span>
                  </button>
                )}

                <button
                  type="button"
                  role="menuitem"
                  onClick={handleSair}
                  className="w-full px-3 py-2 text-left font-body text-[0.82rem] font-medium tracking-wide text-coffee-soft transition-colors duration-300 hover:bg-forest-soft/10 hover:text-gold border-t border-line mt-1"
                >
                  Sair da conta
                </button>
              </div>
            )}
          </div>

          <button
            type="button"
            data-testid="navbar-sacola"
            onClick={() => onNavegar?.('carrinho')}
            aria-label="Sacola"
            className="relative grid h-10 w-10 place-items-center text-coffee transition-colors duration-300 hover:text-gold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
          >
            <BagIcon />
            {totalItens > 0 && (
              <span className="absolute right-1.5 top-1.5 grid h-4 w-4 place-items-center rounded-full bg-gold font-body text-[0.6rem] font-medium text-cream-soft">
                {totalItens}
              </span>
            )}
          </button>
        </div>
        )}
      </nav>

      {/* Busca expansível */}
      <div
        className={`overflow-hidden border-line bg-cream-soft transition-[max-height,border-width] duration-500 ease-[var(--ease-cozy)] ${
          searchOpen ? 'max-h-28 border-t' : 'max-h-0 border-t-0'
        }`}
      >
        <form
          role="search"
          onSubmit={(e) => {
            e.preventDefault()
            const termo = buscaInput.trim()
            if (termo) {
              onBuscar?.(termo)
              setSearchOpen(false)
            }
          }}
          className="mx-auto flex max-w-[1400px] items-center gap-3 px-5 py-4 sm:px-8"
        >
          <input
            ref={searchInputRef}
            type="search"
            value={buscaInput}
            onChange={(e) => setBuscaInput(e.target.value)}
            placeholder="Busque por título, autor ou assunto…"
            aria-label="Buscar no acervo"
            className="w-full bg-transparent font-display text-lg text-coffee placeholder:text-coffee-faint focus:outline-none"
          />
          <button
            type="submit"
            className="rounded-sm bg-forest px-5 py-2 font-body text-xs font-semibold uppercase tracking-wider text-cream-soft transition-colors hover:bg-forest-soft shrink-0"
          >
            Buscar
          </button>
        </form>
      </div>
    </header>
  )
}
