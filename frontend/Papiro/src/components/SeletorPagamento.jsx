export default function SeletorPagamento({
  tipoPagamento = 'cartao', // 'cartao' | 'pix' | 'boleto'
  onMudarTipoPagamento,
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
        <div className="rounded-md border border-forest/30 bg-forest/[0.04] p-5">
          <div className="flex items-start gap-3.5">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-forest text-cream-soft font-bold text-lg shadow-sm">
              💳
            </div>
            <div>
              <h4 className="font-body text-sm font-semibold text-forest">
                Cartão de Crédito via Mercado Pago
              </h4>
              <p className="font-body text-xs text-coffee-soft mt-1 leading-relaxed">
                Ao clicar em <strong>Concluir compra</strong> você será redirecionado ao
                ambiente seguro do Mercado Pago para informar os dados do cartão. Nenhum
                dado de cartão é armazenado por nós.
              </p>
              <div className="mt-3 inline-flex items-center gap-1.5 rounded-sm bg-forest/10 px-2.5 py-1 text-[0.75rem] font-medium text-forest">
                ✓ Parcelamento e aprovação em tempo real
              </div>
            </div>
          </div>
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
