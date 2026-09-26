import { HeartIcon } from './Icons'

/**
 * PainelCompra — preço, CTA e adicionar aos desejos.
 *
 * `preco`/`precoAntigo` já chegam formatados em BRL. O CTA `onAdicionar`
 * adiciona o produto real à sacola; `stockQty` controla o estado esgotado.
 */
export default function PainelCompra({
  preco,
  precoAntigo,
  desconto,
  stockQty = null,
  onAdicionar,
  feedback = null,
  onAdicionarDesejos,
  nosDesejos = false,
  feedbackDesejos = null,
}) {
  const esgotado = stockQty !== null && stockQty <= 0

  return (
    <div>
      {/* Preço */}
      <div className="flex flex-wrap items-baseline gap-3">
        <span className="font-display text-[2.75rem] leading-none font-semibold text-forest">
          {preco}
        </span>
        {precoAntigo && (
          <span className="font-body text-base font-normal text-coffee-faint line-through">
            {precoAntigo}
          </span>
        )}
      </div>
      {desconto && (
        <p className="mt-2 font-body text-[0.88rem] font-medium text-caramel-dark">
          Você economiza {desconto}
        </p>
      )}

      <p className="mt-6 font-body text-[0.92rem] font-normal text-coffee-soft">
        {esgotado
          ? 'Indisponível no momento.'
          : `Em estoque${stockQty !== null ? ` (${stockQty} un.)` : ''}. Enviamos em até 24 horas com embrulho artesanal.`}
      </p>

      {feedback && (
        <p
          className={`mt-4 font-body text-[0.85rem] font-medium ${
            feedback.tipo === 'erro' ? 'text-caramel-dark' : 'text-forest'
          }`}
        >
          {feedback.texto}
        </p>
      )}

      {feedbackDesejos && (
        <p
          className={`mt-2 font-body text-[0.85rem] font-medium ${
            feedbackDesejos.tipo === 'erro'
              ? 'text-caramel-dark'
              : 'text-forest'
          }`}
        >
          {feedbackDesejos.texto}
        </p>
      )}

      {/* Ações */}
      <button
        type="button"
        onClick={onAdicionar}
        disabled={esgotado}
        className="mt-5 w-full rounded-sm bg-forest py-4 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft shadow-md transition-all duration-300 ease-[var(--ease-cozy)] hover:bg-forest-soft hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:cursor-not-allowed disabled:opacity-50"
      >
        {esgotado ? 'Esgotado' : 'Adicionar à sacola'}
      </button>

      <div className="mt-4 flex items-center justify-center">
        <button
          type="button"
          onClick={onAdicionarDesejos}
          aria-pressed={nosDesejos}
          className={`inline-flex items-center gap-2 font-body text-[0.88rem] font-medium transition-colors duration-300 hover:text-gold ${
            nosDesejos ? 'text-caramel' : 'text-coffee-soft'
          }`}
        >
          <HeartIcon filled={nosDesejos} />{' '}
          {nosDesejos ? 'Nos seus desejos' : 'Adicionar aos desejos'}
        </button>
      </div>
    </div>
  )
}
