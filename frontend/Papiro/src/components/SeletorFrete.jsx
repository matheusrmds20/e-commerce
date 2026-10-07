/**
 * SeletorFrete — opções de frete (Melhor Envio) no checkout.
 *
 * Recebe as ofertas cotadas pelo backend (`POST /shipping/calculate`) e deixa
 * o usuário escolher a transportadora/prazo/valor desejados.
 *
 * Estados:
 * - `carregando`: mostra placeholder de carregamento.
 * - `ofertaSelecionadaId`: id da oferta escolhida (radio).
 * - `isReal=false`: o backend caiu no fallback (frete não calculado de verdade);
 *   exibe aviso e não mostra ofertas.
 * - sem ofertas: não exibe o seletor (frete tratado como 0/por conta do admin).
 */
export default function SeletorFrete({
  ofertas = [],
  ofertaSelecionadaId,
  onSelecionarOferta,
  carregando = false,
  isReal = true,
  fallbackMotivo = '',
  formatarPreco,
}) {
  if (carregando) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-body text-[1rem] font-semibold text-coffee">
            Frete
          </h3>
        </div>
        <div className="rounded-md border border-line bg-cream-soft/60 p-5 text-center animate-pulse">
          <p className="font-body text-xs text-coffee-faint">
            Calculando fretes disponíveis…
          </p>
        </div>
      </div>
    )
  }

  if (!isReal || ofertas.length === 0) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-body text-[1rem] font-semibold text-coffee">
            Frete
          </h3>
        </div>
        <div className="rounded-md border border-dashed border-line-strong bg-cream-soft/40 p-5">
          <p className="font-body text-xs text-coffee-soft">
            {fallbackMotivo
              ? `Frete não calculado automaticamente (${fallbackMotivo}). O valor será confirmado após o pedido.`
              : 'Nenhuma opção de frete disponível no momento.'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-body text-[1rem] font-semibold text-coffee">
          Frete
        </h3>
        <span className="font-body text-[0.72rem] uppercase tracking-[0.14em] text-coffee-faint">
          {ofertas.length} opção(oes)
        </span>
      </div>

      <div className="grid gap-3">
        {ofertas.map((oferta, index) => {
          const isSelected = ofertaSelecionadaId === index
          return (
            <label
              key={`${oferta.service_id}-${index}`}
              className={`relative flex items-center justify-between gap-3 p-4 rounded-md border transition-all cursor-pointer ${
                isSelected
                  ? 'border-forest bg-forest/[0.04] ring-1 ring-forest/30 shadow-xs'
                  : 'border-line-strong bg-cream-soft hover:border-gold/60 hover:bg-cream'
              }`}
            >
              <div className="flex items-start gap-3">
                <input
                  type="radio"
                  name="frete_checkout"
                  checked={isSelected}
                  onChange={() => onSelecionarOferta(index)}
                  className="mt-1 accent-forest cursor-pointer"
                />
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-body text-[0.95rem] font-semibold text-coffee">
                      {oferta.name || oferta.company_name || `Opção ${index + 1}`}
                    </span>
                    {isSelected && (
                      <span className="rounded-full bg-forest/15 px-2 py-0.5 font-body text-[0.68rem] font-bold text-forest uppercase tracking-wider">
                        Selecionado
                      </span>
                    )}
                  </div>
                  {oferta.delivery_time != null && (
                    <p className="font-body text-xs text-coffee-soft mt-0.5">
                      Prazo estimado: {oferta.delivery_time}{' '}
                      {oferta.delivery_time === 1 ? 'dia útil' : 'dias úteis'}
                    </p>
                  )}
                </div>
              </div>

              <span className="font-display font-semibold text-forest shrink-0">
                {formatarPreco(oferta.price)}
              </span>
            </label>
          )
        })}
      </div>
    </div>
  )
}