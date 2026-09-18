/**
 * CartaoRecomendado — cartão vertical das recomendações.
 * Capa emoldurada em creme, título, preço e botão "Adicionar à sacola".
 */
export default function CartaoRecomendado({ item, formatarPreco, onAdicionar }) {
  return (
    <article className="group flex flex-col rounded-md border border-line bg-cream-soft p-4 transition-colors duration-500 ease-[var(--ease-cozy)] hover:border-line-strong">
      <div className="flex h-[230px] items-center justify-center overflow-hidden rounded-sm bg-cream-tint/80 sm:h-[250px]">
        <img
          src={item.imagem}
          alt={`Capa de ${item.titulo}`}
          className="h-[86%] w-auto object-contain shadow-[0_10px_26px_-14px_rgba(75,54,33,0.6)] transition-transform duration-700 ease-[var(--ease-cozy)] group-hover:scale-[1.05]"
          loading="lazy"
        />
      </div>

      <h3 className="mt-5 font-display text-[1.25rem] font-normal leading-snug text-coffee">
        <a
          href="#"
          onClick={(event) => event.preventDefault()}
          className="transition-colors duration-300 hover:text-gold"
        >
          {item.titulo}
        </a>
      </h3>

      <p className="mt-2 font-body text-[1rem] font-semibold text-forest">
        {formatarPreco(item.preco)}
      </p>

      <button
        type="button"
        onClick={() => onAdicionar(item)}
        className="mt-4 w-full rounded-sm bg-cream-tint py-3 font-body text-xs font-semibold tracking-wider text-coffee transition-colors duration-300 ease-[var(--ease-cozy)] hover:bg-gold hover:text-cream-soft focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
      >
        Adicionar à sacola
      </button>
    </article>
  )
}
