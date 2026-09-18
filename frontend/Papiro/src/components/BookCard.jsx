/**
 * BookCard — capa em fundo próprio, com sobreposição discreta ao passar o mouse.
 * `tint` dá o tom de fundo quando a imagem não preenche a área.
 */
export default function BookCard({
  id,
  title,
  author,
  price,
  oldPrice,
  image,
  tint = 'bg-coffee',
  badge = null,
  onAbrir,
}) {
  return (
    <article className="group flex flex-col">
      <a
        href="#"
        onClick={(event) => {
          event.preventDefault()
          onAbrir?.(id)
        }}
        className="block focus-visible:outline-none"
      >
        <div
          className={`relative aspect-[3/4] overflow-hidden rounded-md ${tint} shadow-[0_10px_30px_-18px_rgba(75,54,33,0.5)]`}
        >
          <img
            src={image}
            alt={`Capa de ${title}`}
            className="h-full w-full object-cover transition-transform duration-700 ease-[var(--ease-cozy)] group-hover:scale-[1.04]"
            loading="lazy"
          />

          {/* Selo de curadoria (ex.: produto marcado como destaque na API) */}
          {badge && (
            <span className="absolute left-3 top-3 z-10 rounded-sm bg-forest/95 px-2.5 py-1 font-body text-[0.65rem] font-semibold uppercase tracking-[0.16em] text-cream-soft shadow-sm backdrop-blur-sm">
              {badge}
            </span>
          )}

          {/* Véu ao passar o mouse */}
          <div className="absolute inset-0 bg-forest/0 transition-colors duration-500 group-hover:bg-forest/25" />

          {/* Ação rápida */}
          <span className="pointer-events-none absolute inset-x-4 bottom-4 translate-y-3 rounded-sm bg-cream-soft/95 py-3 text-center font-body text-[0.68rem] font-medium uppercase tracking-[0.22em] text-forest opacity-0 transition-all duration-500 ease-[var(--ease-cozy)] group-hover:translate-y-0 group-hover:opacity-100">
            Adicionar à sacola
          </span>
        </div>
      </a>

      <div className="mt-5 flex flex-1 flex-col">
        <h3 className="font-display text-[1.45rem] font-normal leading-snug text-coffee">
          <a
            href="#"
            onClick={(event) => {
              event.preventDefault()
              onAbrir?.(id)
            }}
            className="transition-colors duration-300 hover:text-gold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
          >
            {title}
          </a>
        </h3>

        <p className="mt-1.5 font-body text-[0.82rem] font-medium uppercase tracking-[0.14em] text-coffee-soft">
          {author}
        </p>

        <p className="mt-3.5 flex items-baseline gap-3">
          <span className="font-body text-[1.05rem] font-semibold text-forest">
            {price}
          </span>
          {oldPrice && (
            <span className="font-body text-[0.88rem] font-normal text-coffee-faint line-through">
              {oldPrice}
            </span>
          )}
        </p>
      </div>
    </article>
  )
}
