import BookCard from './BookCard'
import { ArrowLeftIcon, ArrowRightIcon } from './Icons'

const BOOKS = [
  {
    id: 1,
    title: 'A Vida Oculta das Árvores',
    author: 'Elena Marchetti',
    price: 'R$ 78,00',
    oldPrice: 'R$ 92,00',
    tint: 'bg-forest',
    image:
      'https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 2,
    title: 'O Último Boticário',
    author: 'Sarah Penner',
    price: 'R$ 64,90',
    tint: 'bg-coffee',
    image:
      'https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 3,
    title: 'O Véu Aconchegante',
    author: 'Nora Whitfield',
    price: 'R$ 71,50',
    oldPrice: 'R$ 85,00',
    tint: 'bg-caramel-dark',
    image:
      'https://images.unsplash.com/photo-1495446815901-a7297e633e8d?auto=format&fit=crop&w=800&q=80',
  },
]

/**
 * ColecaoDestaque — vitrine "Leituras à Lareira".
 * A faixa de imagem usa o mesmo container da grade de capas, então as duas
 * se alinham nas laterais em vez de a faixa sangrar até a borda. O respiro
 * do topo é mínimo para a faixa quase encostar no hero.
 */
export default function ColecaoDestaque({ onAbrirLivro }) {
  return (
    <section id="colecao" className="bg-cream-soft">
      <div className="mx-auto max-w-[1400px] px-5 pb-10 pt-3 sm:px-8 sm:pt-4">
        {/* Faixa de imagem — estante e lareira */}
        <div className="relative h-[200px] overflow-hidden rounded-md sm:h-[240px] lg:h-[280px]">
          <img
            src="https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=2000&q=80"
            alt="Estante de madeira ao lado de uma lareira acesa"
            className="h-full w-full object-cover"
            loading="lazy"
          />
          <div className="absolute inset-0 bg-forest/25" />
        </div>

        {/* Cabeçalho da seção */}
        <div className="pt-16 text-center sm:pt-20">
          <p className="label-caps text-caramel">Coleção em destaque</p>

          <h2 className="mt-5 font-display text-[2.4rem] leading-tight font-light tracking-[-0.01em] text-forest sm:text-[3.25rem]">
            Leituras à Lareira
          </h2>

          <p className="mx-auto mt-5 max-w-[32rem] font-body text-sm font-light leading-relaxed text-coffee-soft sm:text-base">
            Histórias para as noites longas &mdash; mundos tranquilos, mistérios
            suaves e prosa que aquece.
          </p>
        </div>

        {/* Grade de capas */}
        <div className="mt-16 grid gap-10 sm:grid-cols-2 lg:grid-cols-3 lg:gap-8">
          {BOOKS.map((book) => (
            <BookCard key={book.id} {...book} onAbrir={onAbrirLivro} />
          ))}
        </div>

        {/* Navegação da vitrine */}
        <div className="mt-14 flex items-center justify-center gap-4">
          <button
            type="button"
            aria-label="Anteriores"
            className="grid h-11 w-11 place-items-center rounded-sm border border-line-strong text-coffee-soft transition-colors duration-300 hover:border-gold hover:text-gold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
          >
            <ArrowLeftIcon />
          </button>
          <span className="font-body text-[0.7rem] uppercase tracking-[0.28em] text-coffee-faint">
            01 / 04
          </span>
          <button
            type="button"
            aria-label="Próximos"
            className="grid h-11 w-11 place-items-center rounded-sm border border-line-strong text-coffee-soft transition-colors duration-300 hover:border-gold hover:text-gold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
          >
            <ArrowRightIcon />
          </button>
        </div>
      </div>
    </section>
  )
}
