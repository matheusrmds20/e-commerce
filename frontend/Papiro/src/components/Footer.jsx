import Quill from './Quill'
import { InstagramIcon, FacebookIcon, YoutubeIcon } from './Icons'
import { useAuth } from '../context/auth-context'

const COLUMNS = [
  {
    title: 'Loja',
    links: [
      { label: 'Mais vendidos', page: 'mais-vendidos' },
      { label: 'O Acervo', page: 'acervo' },
      { label: 'Início', page: 'home' },
      { label: 'Sacola de Compras', page: 'carrinho' },
    ],
  },
  {
    title: 'Acesso',
    links: [
      { label: 'Sobre Nós', page: 'sobre' },
      { label: 'Minha Conta', page: 'minhaconta' },
      { label: 'Painel da Curadoria', page: 'admin' },
    ],
  },
]

/**
 * Footer — Rodapé compacto e elegante, com espaçamentos otimizados e estética editorial.
 */
export default function Footer({ onNavegar }) {
  const { usuario } = useAuth()
  const ehAdmin = usuario?.role === 'admin'

  return (
    <footer className="border-t border-line bg-cream-soft">
      <div className="mx-auto max-w-[1400px] px-5 py-10 sm:px-8 sm:py-12">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-[1.6fr_repeat(2,1fr)]">
          {/* Marca & Redes */}
          <div className="flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => {
                    onNavegar?.('home')
                    window.scrollTo({ top: 0, behavior: 'smooth' })
                  }}
                  className="font-display text-[1.7rem] leading-none text-coffee hover:text-forest transition-colors text-left"
                >
                  Papiro
                </button>
                <Quill className="w-[32px] text-coffee/50" />
              </div>
              <p className="mt-2.5 max-w-[22rem] font-body text-xs font-light leading-relaxed text-coffee-soft">
                Uma livraria para leitores tranquilos. Curadoria feita à mão, um
                livro de cada vez.
              </p>
            </div>

            {/* Redes Sociais */}
            <div className="mt-5 flex items-center gap-3 text-coffee-soft">
              <a
                href="#"
                aria-label="Instagram"
                className="grid h-8 w-8 place-items-center rounded-sm border border-line-strong bg-cream-tint/60 text-coffee-soft transition-colors duration-300 hover:border-gold hover:text-gold"
              >
                <InstagramIcon className="h-4 w-4" />
              </a>
              <a
                href="#"
                aria-label="Facebook"
                className="grid h-8 w-8 place-items-center rounded-sm border border-line-strong bg-cream-tint/60 text-coffee-soft transition-colors duration-300 hover:border-gold hover:text-gold"
              >
                <FacebookIcon className="h-4 w-4" />
              </a>
              <a
                href="#"
                aria-label="YouTube"
                className="grid h-8 w-8 place-items-center rounded-sm border border-line-strong bg-cream-tint/60 text-coffee-soft transition-colors duration-300 hover:border-gold hover:text-gold"
              >
                <YoutubeIcon className="h-4 w-4" />
              </a>
            </div>
          </div>

          {/* Colunas de links */}
          {COLUMNS.map((column) => (
            <div key={column.title}>
              <h3 className="label-caps text-[0.68rem] text-gold">{column.title}</h3>
              <ul className="mt-3.5 flex flex-col gap-2">
                {column.links
                  .filter((link) => !(link.page === 'admin' && !ehAdmin))
                  .map((link) => (
                  <li key={link.label}>
                    {link.page ? (
                      <button
                        type="button"
                        onClick={() => {
                          onNavegar?.(link.page)
                          window.scrollTo({ top: 0, behavior: 'smooth' })
                        }}
                        className="font-body text-xs text-coffee-soft transition-colors duration-300 hover:text-gold text-left"
                      >
                        {link.label}
                      </button>
                    ) : (
                      <span className="font-body text-xs text-coffee-soft/80 cursor-default">
                        {link.label}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Faixa Inferior / Copyright */}
        <div className="mt-8 flex flex-col gap-3 border-t border-line/80 pt-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-body text-[0.72rem] tracking-wide text-coffee-faint">
            © {new Date().getFullYear()} Papiro Livraria. Todos os direitos reservados.
          </p>
          <p className="font-display text-xs italic text-coffee-faint">
            Livros para dias lentos.
          </p>
        </div>
      </div>
    </footer>
  )
}
