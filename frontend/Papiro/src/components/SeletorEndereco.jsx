export default function SeletorEndereco({
  enderecos = [],
  enderecoSelecionadoId,
  onSelecionarEndereco,
  onAbrirModal,
  carregando = false,
}) {
  const formatarCep = (valor = '') =>
    valor
      .replace(/\D/g, '')
      .slice(0, 8)
      .replace(/(\d{5})(?=\d)/, '$1-')

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-body text-[1rem] font-semibold text-coffee flex items-center gap-2">
          <span>1. Endereço de Entrega</span>
        </h3>
        <button
          type="button"
          onClick={() => onAbrirModal({ modo: 'lista' })}
          className="font-body text-xs font-semibold uppercase tracking-[0.14em] text-forest hover:text-forest-soft flex items-center gap-1 transition-colors"
        >
          <span className="text-base leading-none font-bold">+</span>
          Gerenciar / Novo
        </button>
      </div>

      {carregando ? (
        <div className="rounded-md border border-line bg-cream-soft/60 p-6 text-center animate-pulse">
          <p className="font-body text-xs text-coffee-faint">
            Carregando seus endereços…
          </p>
        </div>
      ) : enderecos.length === 0 ? (
        <div className="rounded-md border border-dashed border-line-strong bg-cream-soft/40 p-6 text-center">
          <p className="font-body text-sm text-coffee-soft">
            Você ainda não possui um endereço de entrega cadastrado.
          </p>
          <button
            type="button"
            onClick={() => onAbrirModal({ modo: 'novo' })}
            className="mt-3 inline-flex items-center gap-1.5 rounded-sm bg-forest px-4 py-2 font-body text-xs font-semibold uppercase tracking-wider text-cream-soft hover:bg-forest-soft transition-colors shadow-sm"
          >
            <span>+</span> Cadastrar endereço de entrega
          </button>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-1">
          {enderecos.map((end) => {
            const isSelected = end.id === enderecoSelecionadoId
            return (
              <label
                key={end.id}
                className={`relative flex items-start justify-between gap-3 p-4 rounded-md border transition-all cursor-pointer ${
                  isSelected
                    ? 'border-forest bg-forest/[0.04] ring-1 ring-forest/30 shadow-xs'
                    : 'border-line-strong bg-cream-soft hover:border-gold/60 hover:bg-cream'
                }`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="radio"
                    name="endereco_entrega_checkout"
                    checked={isSelected}
                    onChange={() => onSelecionarEndereco(end)}
                    className="mt-1 accent-forest cursor-pointer"
                  />
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-body text-[0.95rem] font-semibold text-coffee">
                        {end.street}, {end.number}
                        {end.complement ? ` - ${end.complement}` : ''}
                      </span>
                      {end.is_default && (
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
                    <p className="font-body text-xs text-coffee-soft mt-1">
                      {end.neighborhood} • {end.city} - {end.state} • CEP {formatarCep(end.zip_code)}
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    onAbrirModal({ modo: 'editar', endereco: end })
                  }}
                  className="font-body text-xs font-semibold text-forest hover:text-forest-soft px-2 py-1 transition-colors self-center shrink-0"
                >
                  Editar
                </button>
              </label>
            )
          })}
        </div>
      )}
    </div>
  )
}
