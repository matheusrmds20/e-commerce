import { useEffect, useState } from 'react'
import { CloseIcon } from './Icons'

/**
 * Modal de criação/edição de cupons de desconto (Painel Admin).
 *
 * Contrato com o backend (`CouponCreate` / `CouponUpdate`):
 *   { code, product_id?, discount_type, discount_value, min_purchase?,
 *     max_discount?, valid_until, max_uses?, is_active }
 *
 * `discount_type` ∈ 'percentage' | 'fixed'. `valid_until` é enviado em ISO
 * 8601 (o input é `datetime-local` e a conversão é local → ISO).
 *
 * O modal é "burro" em relação ao estado da lista: recebe `cupomParaEditar`
 * (null = criação), salva via `onSalvar(payload, cupomId)` e deixa o Admin
 * decidir como atualizar a lista. Assim o mesmo componente serve criar/editar.
 */

/** Converte uma data ISO em valor aceito pelo input datetime-local (hora local). */
function isoParaInput(iso) {
  if (!iso) return ''
  const data = new Date(iso)
  if (Number.isNaN(data.getTime())) return ''
  const tzOffset = data.getTimezoneOffset() * 60000
  return new Date(data.getTime() - tzOffset).toISOString().slice(0, 16)
}

const FORM_VAZIO = {
  code: '',
  product_id: '',
  discount_type: 'percentage',
  discount_value: '',
  min_purchase: '',
  max_discount: '',
  valid_until: '',
  max_uses: '',
  is_active: true,
}

/**
 * Estado inicial do formulário. Em edição, preenche a partir do cupom; em
 * criação, usa o formulário vazio. Como o Admin só monta este modal quando
 * ele está aberto, um lazy initializer basta — não precisa de useEffect para
 * sincronizar o prop (evita cascading renders).
 */
function formInicial(cupom) {
  if (!cupom) return FORM_VAZIO
  return {
    code: cupom.code ?? '',
    product_id: cupom.product_id ?? '',
    discount_type: cupom.discount_type ?? 'percentage',
    discount_value: String(cupom.discount_value ?? ''),
    min_purchase: cupom.min_purchase != null ? String(cupom.min_purchase) : '',
    max_discount: cupom.max_discount != null ? String(cupom.max_discount) : '',
    valid_until: isoParaInput(cupom.valid_until),
    max_uses: cupom.max_uses != null ? String(cupom.max_uses) : '',
    is_active: Boolean(cupom.is_active),
  }
}

export default function ModalCupom({
  onClose,
  onSalvar,
  cupomParaEditar = null,
  produtos = [],
}) {
  const [form, setForm] = useState(() => formInicial(cupomParaEditar))
  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState(null)
  const [salvando, setSalvando] = useState(false)

  // Fecha no ESC
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  const editando = Boolean(cupomParaEditar)

  const atualizarCampo = (campo) => (e) => {
    const valor = e.target.value
    setForm((prev) => ({ ...prev, [campo]: valor }))
    if (erros[campo]) setErros((prev) => ({ ...prev, [campo]: null }))
  }

  /** Número opcional: '' → null; caso contrário, Number. */
  const numeroOpcional = (valor) => {
    const texto = String(valor).trim()
    if (texto === '') return null
    const n = Number(texto)
    return Number.isNaN(n) ? null : n
  }

  const validar = () => {
    const novosErros = {}

    if (!form.code.trim()) {
      novosErros.code = 'Informe o código do cupom.'
    } else if (form.code.trim().length < 3) {
      novosErros.code = 'O código deve ter ao menos 3 caracteres.'
    }

    const valor = Number(form.discount_value)
    if (form.discount_value === '' || Number.isNaN(valor)) {
      novosErros.discount_value = 'Informe o valor do desconto.'
    } else if (valor < 0) {
      novosErros.discount_value = 'O desconto deve ser positivo.'
    } else if (form.discount_type === 'percentage' && valor > 100) {
      novosErros.discount_value = 'Percentual não pode passar de 100%.'
    }

    if (!form.valid_until) {
      novosErros.valid_until = 'Informe a data de validade.'
    }

    setErros(novosErros)
    return Object.keys(novosErros).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (salvando) return

    setErroGeral(null)
    if (!validar()) return

    const payload = {
      code: form.code.trim(),
      product_id: form.product_id === '' ? null : Number(form.product_id),
      discount_type: form.discount_type,
      discount_value: Number(form.discount_value),
      min_purchase: numeroOpcional(form.min_purchase),
      max_discount: numeroOpcional(form.max_discount),
      // datetime-local entrega hora local; new Date() interpreta como local e
      // toISOString() converte para UTC (o que o backend espera).
      valid_until: new Date(form.valid_until).toISOString(),
      max_uses: numeroOpcional(form.max_uses),
      is_active: Boolean(form.is_active),
    }

    setSalvando(true)
    try {
      await onSalvar(payload, cupomParaEditar?.id ?? null)
      onClose()
    } catch (err) {
      setErroGeral(err.message || 'Não foi possível salvar o cupom.')
    } finally {
      setSalvando(false)
    }
  }

  const rotuloCampo =
    'block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1'
  const inputClasse = 'w-full campo py-2 text-sm'

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-cupom-titulo"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-forest/50 backdrop-blur-xs"
    >
      <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-cream-soft border border-line rounded-sm shadow-2xl p-6 sm:p-8">
        <div className="flex justify-between items-center pb-4 border-b border-line">
          <div>
            <span className="label-caps text-gold">Descontos</span>
            <h3
              id="modal-cupom-titulo"
              className="font-display text-2xl font-bold text-coffee mt-1"
            >
              {editando ? 'Editar Cupom' : 'Novo Cupom'}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-coffee-faint hover:text-coffee transition-colors"
            aria-label="Fechar"
          >
            <CloseIcon />
          </button>
        </div>

        {erroGeral && (
          <div className="mt-4 p-3 bg-amber-50 border border-amber-300 text-amber-900 rounded text-xs">
            {erroGeral}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-4 font-body">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className={rotuloCampo}>Código *</label>
              <input
                type="text"
                required
                placeholder="ex: PAPIRO10"
                value={form.code}
                onChange={atualizarCampo('code')}
                className={inputClasse}
              />
              {erros.code && (
                <p className="mt-1 text-[0.7rem] text-caramel-dark font-medium">
                  {erros.code}
                </p>
              )}
            </div>

            <div>
              <label className={rotuloCampo}>Produto</label>
              <select
                value={form.product_id}
                onChange={atualizarCampo('product_id')}
                className={inputClasse}
              >
                <option value="">Todos os produtos</option>
                {produtos.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.titulo || p.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className={rotuloCampo}>Tipo de Desconto</label>
              <select
                value={form.discount_type}
                onChange={atualizarCampo('discount_type')}
                className={inputClasse}
              >
                <option value="percentage">Percentual (%)</option>
                <option value="fixed">Valor Fixo (R$)</option>
              </select>
            </div>

            <div>
              <label className={rotuloCampo}>
                {form.discount_type === 'percentage'
                  ? 'Desconto (%) *'
                  : 'Desconto (R$) *'}
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                placeholder={form.discount_type === 'percentage' ? '10' : '20.00'}
                value={form.discount_value}
                onChange={atualizarCampo('discount_value')}
                className={inputClasse}
              />
              {erros.discount_value && (
                <p className="mt-1 text-[0.7rem] text-caramel-dark font-medium">
                  {erros.discount_value}
                </p>
              )}
            </div>

            <div>
              <label className={rotuloCampo}>Validade *</label>
              <input
                type="datetime-local"
                required
                value={form.valid_until}
                onChange={atualizarCampo('valid_until')}
                className={inputClasse}
              />
              {erros.valid_until && (
                <p className="mt-1 text-[0.7rem] text-caramel-dark font-medium">
                  {erros.valid_until}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className={rotuloCampo}>Compra Mínima (R$)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                placeholder="Opcional"
                value={form.min_purchase}
                onChange={atualizarCampo('min_purchase')}
                className={inputClasse}
              />
            </div>

            <div>
              <label className={rotuloCampo}>Desconto Máximo (R$)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                placeholder="Opcional"
                value={form.max_discount}
                onChange={atualizarCampo('max_discount')}
                className={inputClasse}
              />
            </div>

            <div>
              <label className={rotuloCampo}>Máx. de Usos</label>
              <input
                type="number"
                min="1"
                placeholder="Ilimitado"
                value={form.max_uses}
                onChange={atualizarCampo('max_uses')}
                className={inputClasse}
              />
            </div>
          </div>

          <label className="flex items-center gap-3 pt-1 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, is_active: e.target.checked }))
              }
              className="h-4 w-4 accent-forest"
            />
            <span className="text-sm text-coffee-soft">
              Cupom ativo (disponível para uso no checkout)
            </span>
          </label>

          <div className="flex justify-end gap-3 pt-4 border-t border-line mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-line-strong text-coffee-soft text-xs uppercase tracking-wider font-semibold rounded-sm hover:bg-cream-deep transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={salvando}
              className="px-6 py-2 bg-forest hover:bg-forest-soft text-cream text-xs uppercase tracking-wider font-semibold rounded-sm transition-colors shadow-sm disabled:opacity-50"
            >
              {salvando
                ? 'Salvando...'
                : editando
                  ? 'Salvar Alterações'
                  : 'Criar Cupom'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
