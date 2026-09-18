import Quill from './Quill'
import { InstagramIcon, FacebookIcon, YoutubeIcon } from './Icons'

const COLUMNS = [
  {
    title: 'Loja',
    links: ['Novidades', 'Mais vendidos', 'Promoções', 'Vale-presente'],
  },
  {
    title: 'Ajuda',
    links: ['Entregas', 'Trocas e devoluções', 'Fale conosco', 'Perguntas frequentes'],
  },
  {
    title: 'Papiro',
    links: ['Nossa história', 'Clube Papiro', 'Eventos', 'Trabalhe conosco'],
  },
]

/**
 * Footer — Rodapé compacto e elegante, com espaçamentos otimizados e estética editorial.
 */
export default function Footer() {
  return (
    <footer className="border-t border-line bg-cream-soft">
      <div className="mx-auto max-w-[1400px] px-5 py-10 sm:px-8 sm:py-12">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-[1.3fr_repeat(3,1fr)]">
          {/* Marca & Redes */}
          <div className="flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3">
                <span className="font-display text-[1.7rem] leading-none text-coffee">
                  Papiro
                </span>
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
                {column.links.map((link) => (
                  <li key={link}>
                    <a
                      href="#"
                      className="font-body text-xs text-coffee-soft transition-colors duration-300 hover:text-gold"
                    >
                      {link}
                    </a>
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
