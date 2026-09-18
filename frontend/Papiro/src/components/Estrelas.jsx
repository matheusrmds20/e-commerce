import { StarIcon } from './Icons'

/**
 * Estrelas — nota com meia estrela suportada via gradiente.
 */
export default function Estrelas({ nota = 0, total = 5, className = 'h-3.5 w-3.5' }) {
  return (
    <div
      className="flex items-center gap-0.5 text-gold"
      role="img"
      aria-label={`${nota} de ${total} estrelas`}
    >
      {Array.from({ length: total }, (_, i) => {
        const preenchimento = Math.min(1, Math.max(0, nota - i))
        return (
          <span key={i} className="relative inline-block">
            <StarIcon className={className} filled={false} />
            {preenchimento > 0 && (
              <span
                className="absolute inset-0 overflow-hidden"
                style={{ width: `${preenchimento * 100}%` }}
              >
                <StarIcon className={className} filled />
              </span>
            )}
          </span>
        )
      })}
    </div>
  )
}
