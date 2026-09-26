import { useEffect, useRef, useState } from 'react'
import {
  BagIcon,
  CloseIcon,
  MenuIcon,
  SearchIcon,
  UserIcon,
} from './Icons'
import { useAuth } from '../context/auth-context'

const LINKS = [
  { label: 'Novidades', href: '#' },
  { label: 'Ficção', href: '#' },
  { label: 'Não-ficção', href: '#' },
  { label: 'Infantil', href: '#' },
  { label: 'Clube Papiro', href: '#' },
]

/** Primeiro nome do usuário, para um cumprimento curto. */
function primeiroNome(nomeCompleto) {
  return nomeCompleto?.trim().split(/\s+/)[0] ?? ''
}

/**
 * Navbar — barra clara e fixa, com o logotipo centralizado em serifada.
 * Some ao descer, reaparece ao subir (mantém o hero limpo).
 */
export default function Navbar({ onNavegar, totalItens = 0, simples = false }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const [contaOpen, setContaOpen] = useState(false)

  const { usuario, autenticado, logout } = useAuth()
  const contaRef = useRef(null)

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
    setMenuOpen(false)
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

  // Trava o scroll do fundo quando o menu mobile está aberto
  useEffect(() => {
    document.body.style.overflow = menuOpen ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [menuOpen])

  return (
    <header
      className={`sticky top-0 z-40 border-b bg-cream-soft/95 backdrop-blur-sm transition-colors duration-500 ease-[var(--ease-cozy)] ${
        scrolled ? 'border-line' : 'border-transparent'
      }`}
    >
      <nav className="mx-auto flex h-[74px] max-w-[1400px] items-center gap-4 px-5 sm:px-8">
        {/* Esquerda — abrir menu */}
        {!simples && (
          <button
            type="button"
            onClick={() => setMenuOpen(true)}
            aria-label="Abrir menu"
            className="grid h-10 w-10 place-items-center text-coffee transition-colors duration-300 hover:text-gold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
          >
            <MenuIcon />
          </button>
        )}

        {/* Centro — logotipo */}
        <a
          href="#"
          onClick={(event) => {
            event.preventDefault()
            onNavegar?.('home')
          }}
          className="absolute left-1/2 -translate-x-1/2 font-display text-[1.85rem] font-medium leading-none tracking-[-0.01em] text-coffee sm:text-[2.25rem]"
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
          searchOpen ? 'max-h-24 border-t' : 'max-h-0 border-t-0'
        }`}
      >
        <div className="mx-auto max-w-[1400px] px-5 py-4 sm:px-8">
          <input
            type="search"
            placeholder="Busque por título, autor ou assunto…"
            className="w-full bg-transparent font-display text-lg text-coffee placeholder:text-coffee-faint focus:outline-none"
          />
        </div>
      </div>

      {/* Gaveta lateral */}
      <div
        className={`fixed inset-0 z-50 ${menuOpen ? '' : 'pointer-events-none'}`}
        aria-hidden={!menuOpen}
      >
        <div
          onClick={() => setMenuOpen(false)}
          className={`absolute inset-0 bg-forest/40 transition-opacity duration-500 ease-[var(--ease-cozy)] ${
            menuOpen ? 'opacity-100' : 'opacity-0'
          }`}
        />

        <aside
          className={`absolute inset-y-0 left-0 flex w-[85%] max-w-[360px] flex-col bg-cream-soft px-8 py-6 shadow-2xl transition-transform duration-500 ease-[var(--ease-cozy)] ${
            menuOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="label-caps text-gold">Menu</span>
            <button
              type="button"
              onClick={() => setMenuOpen(false)}
              aria-label="Fechar menu"
              className="grid h-9 w-9 place-items-center text-coffee transition-colors duration-300 hover:text-gold"
            >
              <CloseIcon />
            </button>
          </div>

          <ul className="mt-10 flex flex-col gap-6">
            {LINKS.map((link) => (
              <li key={link.label}>
                <a
                  href={link.href}
                  onClick={(event) => {
                    event.preventDefault()
                    setMenuOpen(false)
                    if (link.pagina) onNavegar?.(link.pagina)
                  }}
                  className="font-display text-2xl text-coffee transition-colors duration-300 hover:text-gold"
                >
                  {link.label}
                </a>
              </li>
            ))}
          </ul>

          <div className="mt-auto border-t border-line pt-6">
            {autenticado ? (
              <div className="flex flex-col gap-4">
                <div>
                  <p className="font-display text-[1.15rem] font-medium leading-tight text-coffee">
                    Olá, {primeiroNome(usuario?.full_name)}
                  </p>
                  <p className="mt-1 truncate font-body text-[0.75rem] tracking-wide text-coffee-faint">
                    {usuario?.email}
                  </p>
                </div>
                <div className="flex flex-col gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setMenuOpen(false)
                      onNavegar?.('minhaconta')
                    }}
                    className="self-start font-body text-[0.8rem] font-semibold uppercase tracking-[0.18em] text-forest transition-colors duration-300 hover:text-gold"
                  >
                    Minha conta
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setMenuOpen(false)
                      onNavegar?.('admin')
                    }}
                    className="self-start font-body text-[0.8rem] font-semibold uppercase tracking-[0.18em] text-forest transition-colors duration-300 hover:text-gold"
                  >
                    Painel Administrativo
                  </button>
                  <button
                    type="button"
                    onClick={handleSair}
                    className="self-start border-b border-line pb-1 font-body text-[0.8rem] font-semibold uppercase tracking-[0.18em] text-coffee-soft transition-colors duration-300 hover:border-gold hover:text-gold"
                  >
                    Sair da conta
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                <button
                  type="button"
                  onClick={() => {
                    setMenuOpen(false)
                    onNavegar?.('login')
                  }}
                  className="self-start border-b border-line pb-1 font-body text-[0.8rem] font-semibold uppercase tracking-[0.18em] text-coffee transition-colors duration-300 hover:border-gold hover:text-gold"
                >
                  Entrar
                </button>
                <p className="font-body text-xs leading-relaxed text-coffee-soft">
                  Papiro &mdash; livros para dias lentos.
                </p>
              </div>
            )}
          </div>
        </aside>
      </div>
    </header>
  )
}
