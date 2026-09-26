/**
 * ResumoPedido — coluna esquerda do checkout: itens, totais e total geral.
 * `desconto` é o valor estimado do cupom aplicado (0 quando não há cupom).
 */
export default function ResumoPedido({
  itens,
  subtotal,
  frete,
  desconto = 0,
  cupom,
  total,
  formatarPreco,
}) {
  return (
    <aside className="rounded-md border border-line bg-cream-tint/60 p-6 sm:p-7">
      <div className="flex items-baseline justify-between gap-4 border-b border-line pb-4">
        <h2 className="font-display text-[1.5rem] font-normal text-coffee">
          Resumo do pedido
        </h2>
        <span className="font-body text-[0.92rem] font-semibold text-coffee">
          Preço
        </span>
      </div>

      <ul className="divide-y divide-line">
        {itens.map((item) => (
          <li key={item.id} className="flex gap-4 py-5">
            <img
              src={item.imagem}
              alt={`Capa de ${item.titulo}`}
              className="h-[92px] w-16 shrink-0 rounded-sm object-contain shadow-sm"
              loading="lazy"
            />

            <div className="min-w-0 flex-1">
              <h3 className="font-display text-[1.18rem] font-medium leading-snug text-coffee">
                {item.titulo}
              </h3>
              <p className="mt-0.5 font-body text-[0.88rem] font-medium text-coffee-soft">
                {item.autor}
              </p>
              {item.quantidade > 1 && (
                <p className="mt-1 font-body text-[0.8rem] font-normal text-coffee-faint">
                  {item.quantidade} exemplares
                </p>
              )}
            </div>

            <span className="shrink-0 font-body text-[0.98rem] font-semibold text-coffee">
              {formatarPreco(item.preco * item.quantidade)}
            </span>
          </li>
        ))}
      </ul>

      <dl className="flex flex-col gap-3 border-t border-line pt-5">
        <div className="flex items-baseline justify-between gap-4">
          <dt className="font-body text-[0.92rem] font-medium text-coffee-soft">Subtotal</dt>
          <dd className="font-body text-[0.95rem] font-medium text-coffee">
            {formatarPreco(subtotal)}
          </dd>
        </div>

        {desconto > 0 && (
          <div className="flex items-baseline justify-between gap-4">
            <dt className="font-body text-[0.92rem] font-medium text-forest">
              Desconto {cupom?.code ? `(${cupom.code})` : ''}
            </dt>
            <dd className="font-body text-[0.95rem] font-medium text-forest">
              −{formatarPreco(desconto)}
            </dd>
          </div>
        )}

        <div className="flex items-baseline justify-between gap-4">
          <dt className="font-body text-[0.92rem] font-medium text-coffee-soft">Frete</dt>
          <dd className="font-body text-[0.95rem] font-medium text-coffee">
            {frete === 0 ? 'Grátis' : formatarPreco(frete)}
          </dd>
        </div>
      </dl>

      <div className="mt-5 flex items-baseline justify-between gap-4 border-t border-line-strong pt-5">
        <span className="font-body text-[1.1rem] font-semibold text-coffee">
          Total
        </span>
        <span className="font-display text-[1.6rem] font-semibold text-forest">
          {formatarPreco(total)}
        </span>
      </div>
    </aside>
  )
}
