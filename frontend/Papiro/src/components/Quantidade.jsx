/**
 * Quantidade — controle de − / valor / + em bloco único com bordas finas.
 */
export default function Quantidade({ valor, onChange, min = 1, max = 99 }) {
  const ajustar = (delta) => {
    const proximo = Math.min(max, Math.max(min, valor + delta))
    if (proximo !== valor) onChange(proximo)
  }

  return (
    <div className="inline-flex items-stretch overflow-hidden rounded-sm border border-line-strong bg-cream-soft">
      <button
        type="button"
        onClick={() => ajustar(-1)}
        disabled={valor <= min}
        aria-label="Diminuir quantidade"
        className="grid w-9 place-items-center font-body text-base text-coffee-soft transition-colors duration-300 hover:text-gold disabled:cursor-not-allowed disabled:opacity-35 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-gold"
      >
        &minus;
      </button>

      <span
        aria-live="polite"
        className="grid w-10 place-items-center border-x border-line-strong py-2 font-body text-[0.85rem] text-coffee"
      >
        {valor}
      </span>

      <button
        type="button"
        onClick={() => ajustar(1)}
        disabled={valor >= max}
        aria-label="Aumentar quantidade"
        className="grid w-9 place-items-center font-body text-base text-coffee-soft transition-colors duration-300 hover:text-gold disabled:cursor-not-allowed disabled:opacity-35 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-gold"
      >
        +
      </button>
    </div>
  )
}
