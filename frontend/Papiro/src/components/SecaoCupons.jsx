import { formatarPreco } from '../api/adapters'

/**
 * SecaoCupons — seção do checkout que lista os cupons disponíveis para a
 * sacola atual e permite aplicar/remover um deles.
 *
 * Um cupom é "disponível" quando:
 *   - está ativo (`is_active`) e não expirou (`valid_until`);
 *   - é global (`product_id` null) ou se aplica a algum item da sacola;
 *   - o subtotal atinge a compra mínima (`min_purchase`), quando houver.
 *
 * O valor exibido é uma ESTIMATIVA: o backend recalcula o desconto no
 * checkout (`order_service._calculate_totals`) e rejeita cupons inválidos.
 */
export default function SecaoCupons({
  cuponsDisponiveis = [],
  cupomSelecionado,
  onSelecionarCupom,
  desabilitado = false,
}) {
  return (
    <fieldset disabled={desabilitado}>
      <div className="flex items-baseline justify-between gap-4">
        <h3 className="font-display text-[1.3rem] font-normal text-coffee">
          Cupom de desconto
        </h3>
        {cupomSelecionado && (
          <button
            type="button"
            onClick={() => onSelecionarCupom(null)}
            className="font-body text-[0.72rem] font-semibold uppercase tracking-[0.16em] text-[#a4533f] transition-colors hover:text-coffee-soft"
          >
            Remover cupom
          </button>
        )}
      </div>

      {cuponsDisponiveis.length === 0 ? (
        <p className="mt-3 font-body text-[0.82rem] text-coffee-faint">
          Nenhum cupom disponível para esta sacola no momento.
        </p>
      ) : (
        <ul className="mt-3 space-y-2">
          {cuponsDisponiveis.map((cupom) => {
            const selecionado = cupomSelecionado?.id === cupom.id
            const rotuloDesconto =
              cupom.discount_type === 'fixed'
                ? `R$ ${Number(cupom.discount_value).toFixed(2).replace('.', ',')} de desconto`
                : `${Number(cupom.discount_value).toFixed(0)}% de desconto`

            return (
              <li key={cupom.id}>
                <button
                  type="button"
                  onClick={() => onSelecionarCupom(selecionado ? null : cupom)}
                  aria-pressed={selecionado}
                  className={`w-full rounded-sm border px-4 py-3 text-left transition-colors duration-200 ${
                    selecionado
                      ? 'border-forest bg-forest/[0.06]'
                      : 'border-line-strong bg-cream-soft hover:border-gold'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-mono text-xs font-semibold tracking-wider text-coffee">
                      {cupom.code}
                    </span>
                    <span
                      className={`font-body text-[0.8rem] font-semibold ${
                        selecionado ? 'text-forest' : 'text-gold-dark'
                      }`}
                    >
                      {rotuloDesconto}
                    </span>
                  </div>
                  <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 font-body text-[0.72rem] text-coffee-faint">
                    <span>
                      Válido até{' '}
                      {new Date(cupom.valid_until).toLocaleDateString('pt-BR')}
                    </span>
                    {cupom.min_purchase != null && (
                      <span>Mínimo de {formatarPreco(cupom.min_purchase)}</span>
                    )}
                    {cupom.max_discount != null &&
                      cupom.discount_type === 'percentage' && (
                        <span>
                          Desconto máx. de {formatarPreco(cupom.max_discount)}
                        </span>
                      )}
                    {cupom.product_id != null && (
                      <span>Produto selecionado #{cupom.product_id}</span>
                    )}
                  </div>
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </fieldset>
  )
}
