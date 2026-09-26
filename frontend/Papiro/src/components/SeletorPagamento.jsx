export default function SeletorPagamento({
  tipoPagamento = 'cartao', // 'cartao' | 'pix' | 'boleto'
  onMudarTipoPagamento,
  cartoes = [],
  cartaoSelecionadoId,
  onSelecionarCartao,
  onAbrirModalCartao,
}) {
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-body text-[1rem] font-semibold text-coffee">
          2. Método de Pagamento
        </h3>
      </div>

      {/* Opções de método de pagamento (Tabs) */}
      <div className="grid grid-cols-3 gap-2.5">
        <button
          type="button"
          onClick={() => onMudarTipoPagamento('cartao')}
          className={`flex flex-col items-center justify-center p-3 rounded-md border text-center transition-all ${
            tipoPagamento === 'cartao'
              ? 'border-forest bg-forest/[0.05] ring-1 ring-forest/30 text-forest font-semibold shadow-xs'
              : 'border-line-strong bg-cream-soft text-coffee-soft hover:border-gold/60 hover:bg-cream'
          }`}
        >
          <span className="text-xl">💳</span>
          <span className="font-body text-xs mt-1">Cartão de Crédito</span>
        </button>

        <button
          type="button"
          onClick={() => onMudarTipoPagamento('pix')}
          className={`flex flex-col items-center justify-center p-3 rounded-md border text-center transition-all ${
            tipoPagamento === 'pix'
              ? 'border-forest bg-forest/[0.05] ring-1 ring-forest/30 text-forest font-semibold shadow-xs'
              : 'border-line-strong bg-cream-soft text-coffee-soft hover:border-gold/60 hover:bg-cream'
          }`}
        >
          <span className="text-xl">⚡</span>
          <span className="font-body text-xs mt-1">PIX Instantâneo</span>
        </button>

        <button
          type="button"
          onClick={() => onMudarTipoPagamento('boleto')}
          className={`flex flex-col items-center justify-center p-3 rounded-md border text-center transition-all ${
            tipoPagamento === 'boleto'
              ? 'border-forest bg-forest/[0.05] ring-1 ring-forest/30 text-forest font-semibold shadow-xs'
              : 'border-line-strong bg-cream-soft text-coffee-soft hover:border-gold/60 hover:bg-cream'
          }`}
        >
          <span className="text-xl">📄</span>
          <span className="font-body text-xs mt-1">Boleto Bancário</span>
        </button>
      </div>

      {/* Conteúdo do Método Selecionado */}
      {tipoPagamento === 'cartao' && (
        <div className="space-y-3 pt-1">
          <div className="flex items-center justify-between">
            <span className="font-body text-xs font-semibold uppercase tracking-wider text-coffee-soft">
              Seus cartões salvos
            </span>
            <button
              type="button"
              onClick={() => onAbrirModalCartao({ modo: 'lista' })}
              className="font-body text-xs font-semibold uppercase tracking-[0.14em] text-forest hover:text-forest-soft flex items-center gap-1 transition-colors"
            >
              <span className="text-base leading-none font-bold">+</span>
              Gerenciar / Novo Cartão
            </button>
          </div>

          {cartoes.length === 0 ? (
            <div className="rounded-md border border-dashed border-line-strong bg-cream-soft/40 p-6 text-center">
              <p className="font-body text-sm text-coffee-soft">
                Você ainda não possui nenhum cartão de crédito cadastrado.
              </p>
              <button
                type="button"
                onClick={() => onAbrirModalCartao({ modo: 'novo' })}
                className="mt-3 inline-flex items-center gap-1.5 rounded-sm bg-forest px-4 py-2 font-body text-xs font-semibold uppercase tracking-wider text-cream-soft hover:bg-forest-soft transition-colors shadow-sm"
              >
                <span>+</span> Cadastrar novo cartão
              </button>
            </div>
          ) : (
            <div className="grid gap-3">
              {cartoes.map((card) => {
                const isSelected = card.id === cartaoSelecionadoId
                return (
                  <label
                    key={card.id}
                    className={`relative flex items-center justify-between gap-3 p-3.5 rounded-md border transition-all cursor-pointer ${
                      isSelected
                        ? 'border-forest bg-forest/[0.04] ring-1 ring-forest/30 shadow-xs'
                        : 'border-line-strong bg-cream-soft hover:border-gold/60 hover:bg-cream'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <input
                        type="radio"
                        name="cartao_checkout_selecionado"
                        checked={isSelected}
                        onChange={() => onSelecionarCartao(card)}
                        className="accent-forest cursor-pointer"
                      />

                      {/* Ícone de bandeira */}
                      <div className="flex h-9 w-12 shrink-0 items-center justify-center rounded bg-coffee text-[0.65rem] font-bold tracking-wider text-cream shadow-2xs">
                        {card.bandeiraNome?.toUpperCase().slice(0, 4) || 'CARD'}
                      </div>

                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-body text-[0.95rem] font-semibold text-coffee">
                            {card.apelido || `${card.bandeiraNome} final ${card.ultimos4}`}
                          </span>
                          {card.isDefault && (
                            <span className="rounded-full bg-gold/15 px-2 py-0.5 font-body text-[0.68rem] font-bold text-gold-dark uppercase tracking-wider">
                              Padrão
                            </span>
                          )}
                          {isSelected && (
                            <span className="rounded-full bg-forest/15 px-2 py-0.5 font-body text-[0.68rem] font-bold text-forest uppercase tracking-wider">
                              Selecionado
                            </span>
                          )}
                        </div>
                        <p className="font-body text-xs text-coffee-soft mt-0.5">
                          {card.numeroMascarado} • Venc. {card.mes}/{card.ano} • {card.titular}
                        </p>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        onAbrirModalCartao({ modo: 'editar', cartao: card })
                      }}
                      className="font-body text-xs font-semibold text-forest hover:text-forest-soft px-2 py-1 transition-colors shrink-0"
                    >
                      Editar
                    </button>
                  </label>
                )
              })}
            </div>
          )}
        </div>
      )}

      {tipoPagamento === 'pix' && (
        <div className="rounded-md border border-forest/30 bg-forest/[0.04] p-5">
          <div className="flex items-start gap-3.5">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-forest text-cream-soft font-bold text-lg shadow-sm">
              ⚡
            </div>
            <div>
              <h4 className="font-body text-sm font-semibold text-forest">
                Pagamento Instantâneo via PIX
              </h4>
              <p className="font-body text-xs text-coffee-soft mt-1 leading-relaxed">
                O QR Code e o código Copia e Cola serão gerados imediatamente após clicar em <strong>Concluir compra</strong>. A confirmação do pagamento é instantânea.
              </p>
              <div className="mt-3 inline-flex items-center gap-1.5 rounded-sm bg-forest/10 px-2.5 py-1 text-[0.75rem] font-medium text-forest">
                ✓ Desconto especial de até 5% e aprovação imediata
              </div>
            </div>
          </div>
        </div>
      )}

      {tipoPagamento === 'boleto' && (
        <div className="rounded-md border border-line-strong bg-cream-soft p-5">
          <div className="flex items-start gap-3.5">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-coffee text-cream-soft font-bold text-lg shadow-sm">
              📄
            </div>
            <div>
              <h4 className="font-body text-sm font-semibold text-coffee">
                Boleto Bancário
              </h4>
              <p className="font-body text-xs text-coffee-soft mt-1 leading-relaxed">
                O boleto será exibido para impressão ou cópia da linha digitável após a confirmação. O prazo de compensação é de até <strong>3 dias úteis</strong>.
              </p>
              <p className="font-body text-[0.75rem] text-coffee-faint mt-2">
                * O pedido será separado para envio somente após a confirmação bancária.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
