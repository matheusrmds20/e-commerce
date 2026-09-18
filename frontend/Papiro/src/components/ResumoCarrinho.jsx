/**
 * ResumoCarrinho — caixa lateral com frete estimado, total e checkout.
 */
export default function ResumoCarrinho({
  subtotal,
  frete,
  total,
  formatarPreco,
  onCheckout,
}) {
  const freteGratis = frete === 0

  return (
    <aside className="rounded-md border border-line bg-cream-soft p-7 lg:sticky lg:top-24">
      <h2 className="font-display text-[1.75rem] font-normal text-coffee">
        Resumo da sacola
      </h2>

      <dl className="mt-7 flex flex-col gap-4">
        <div className="flex items-baseline justify-between gap-4">
          <dt className="font-body text-[0.95rem] font-semibold text-coffee">
            Frete estimado:
          </dt>
          <dd className="font-body text-[0.98rem] font-medium text-coffee">
            {freteGratis ? 'Grátis' : formatarPreco(frete)}
          </dd>
        </div>

        <p className="font-body text-[0.82rem] font-medium italic text-caramel-dark">
          {freteGratis
            ? 'Frete grátis aplicado ao seu pedido.'
            : 'Cálculo médio para todo o Brasil.'}
        </p>

        <div className="border-t border-line pt-4">
          <div className="flex items-baseline justify-between gap-4">
            <dt className="font-body text-[1.05rem] font-semibold text-coffee">
              Total
            </dt>
            <dd className="font-display text-[1.6rem] font-semibold text-forest">
              {formatarPreco(total)}
            </dd>
          </div>
        </div>
      </dl>

      <button
        type="button"
        onClick={onCheckout}
        className="mt-7 w-full rounded-sm bg-forest py-4 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft shadow-md transition-all duration-300 ease-[var(--ease-cozy)] hover:bg-forest-soft hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
      >
        Finalizar compra
      </button>

      <p className="mt-4 text-center font-body text-[0.76rem] font-normal text-coffee-faint">
        Subtotal de {formatarPreco(subtotal)} antes do frete.
      </p>
    </aside>
  )
}
