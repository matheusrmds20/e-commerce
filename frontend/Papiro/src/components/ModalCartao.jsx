import { useEffect, useState } from 'react'
import CampoFormulario from './CampoFormulario'
import { CloseIcon } from './Icons'
import cardService, {
  detectarBandeira,
  formatarNumeroCartao,
} from '../api/cards'

const MESES = Array.from({ length: 12 }, (_, i) =>
  String(i + 1).padStart(2, '0'),
)
const ANOS = Array.from({ length: 12 }, (_, i) => String(2026 + i))

function ModalCartaoDialog({
  onClose,
  userId,
  cartoes = [],
  cartaoSelecionadoId = null,
  onSelecionarCartao,
  onRecarregarCartoes,
  modoInicial = 'lista',
  cartaoParaEditar = null,
}) {
  const [modo, setModo] = useState(() => {
    if (modoInicial === 'novo' || cartoes.length === 0) return 'formulario'
    if (modoInicial === 'editar' && cartaoParaEditar) return 'formulario'
    return 'lista'
  })

  const [form, setForm] = useState(() => {
    if (modoInicial === 'editar' && cartaoParaEditar) {
      return {
        id: cartaoParaEditar.id,
        numero: cartaoParaEditar.numeroMascarado || '',
        titular: cartaoParaEditar.titular || '',
        mes: cartaoParaEditar.mes || '',
        ano: cartaoParaEditar.ano || '',
        cvc: '',
        apelido: cartaoParaEditar.apelido || '',
        isDefault: Boolean(cartaoParaEditar.isDefault),
      }
    }
    return {
      id: null,
      numero: '',
      titular: '',
      mes: '',
      ano: '',
      cvc: '',
      apelido: '',
      isDefault: false,
    }
  })

  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState(null)
  const [salvando, setSalvando] = useState(false)
  const [excluindoId, setExcluindoId] = useState(null)

  // Fecha no ESC
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  const bandeiraAtual = detectarBandeira(form.numero)

  const atualizarCampo = (campo) => (e) => {
    const valor = e.target.value
    setForm((prev) => ({ ...prev, [campo]: valor }))
    if (erros[campo]) {
      setErros((prev) => ({ ...prev, [campo]: null }))
    }
  }

  const handleNumeroChange = (e) => {
    const formatado = formatarNumeroCartao(e.target.value)
    setForm((prev) => ({ ...prev, numero: formatado }))
    if (erros.numero) {
      setErros((prev) => ({ ...prev, numero: null }))
    }
  }

  const validar = () => {
    const novoserros = {}

    if (!form.id) {
      // Criação exige validação de número do cartão
      const numDigitos = form.numero.replace(/\D/g, '')
      if (!numDigitos) novoserros.numero = 'Informe o número do cartão.'
      else if (numDigitos.length < 13 || numDigitos.length > 16) {
        novoserros.numero = 'Número de cartão inválido.'
      }

      const cvcDigitos = form.cvc.replace(/\D/g, '')
      if (!cvcDigitos) novoserros.cvc = 'Informe o CVC.'
      else if (cvcDigitos.length < 3) novoserros.cvc = 'CVC inválido.'
    }

    if (!form.titular.trim()) {
      novoserros.titular = 'Informe o nome impresso no cartão.'
    }

    if (!form.mes) novoserros.mes = 'Mês obrigatório.'
    if (!form.ano) novoserros.ano = 'Ano obrigatório.'

    setErros(novoserros)
    return Object.keys(novoserros).length === 0
  }

  const handleSalvar = async (e) => {
    e.preventDefault()
    if (salvando) return

    setErroGeral(null)
    if (!validar()) return

    setSalvando(true)
    try {
      let salvo
      if (form.id) {
        salvo = cardService.atualizar(userId, form.id, {
          titular: form.titular,
          mes: form.mes,
          ano: form.ano,
          apelido: form.apelido,
          isDefault: form.isDefault,
        })
      } else {
        salvo = cardService.criar(userId, {
          numero: form.numero,
          titular: form.titular,
          mes: form.mes,
          ano: form.ano,
          apelido: form.apelido,
          isDefault: form.isDefault,
        })
      }

      onRecarregarCartoes?.()
      if (onSelecionarCartao && salvo) {
        onSelecionarCartao(salvo)
      }
      onClose()
    } catch (err) {
      setErroGeral(err.message || 'Erro ao salvar o cartão.')
    } finally {
      setSalvando(false)
    }
  }

  const handleIniciarEdicao = (cartao) => {
    setForm({
      id: cartao.id,
      numero: cartao.numeroMascarado || '',
      titular: cartao.titular || '',
      mes: cartao.mes || '',
      ano: cartao.ano || '',
      cvc: '',
      apelido: cartao.apelido || '',
      isDefault: Boolean(cartao.isDefault),
    })
    setErros({})
    setErroGeral(null)
    setModo('formulario')
  }

  const handleExcluir = (id, e) => {
    e.stopPropagation()
    if (excluindoId) return
    if (!window.confirm('Tem certeza que deseja remover este cartão?')) return

    try {
      setExcluindoId(id)
      cardService.excluir(userId, id)
      onRecarregarCartoes?.()
    } catch (err) {
      setErroGeral(err.message || 'Erro ao excluir o cartão.')
    } finally {
      setExcluindoId(null)
    }
  }

  const handleDefinirPadrao = (id, e) => {
    e.stopPropagation()
    try {
      cardService.definirPadrao(userId, id)
      onRecarregarCartoes?.()
    } catch (err) {
      setErroGeral(err.message || 'Erro ao definir cartão padrão.')
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-cartao-titulo"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-coffee/60 backdrop-blur-sm transition-all"
    >
      <div className="relative w-full max-w-xl max-h-[90vh] flex flex-col rounded-md border border-line bg-cream-soft shadow-2xl overflow-hidden">
        {/* Cabeçalho */}
        <div className="flex items-center justify-between border-b border-line px-6 py-4 bg-cream">
          <div>
            <h2
              id="modal-cartao-titulo"
              className="font-display text-2xl font-normal text-coffee"
            >
              {modo === 'formulario'
                ? form.id
                  ? 'Editar cartão'
                  : 'Cadastrar novo cartão'
                : 'Cartões de pagamento salvos'}
            </h2>
            <p className="font-body text-xs text-coffee-faint">
              {modo === 'formulario'
                ? 'Seus dados de pagamento são protegidos e salvos localmente'
                : 'Selecione, edite ou gerencie seus cartões de crédito'}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar"
            className="rounded-full p-2 text-coffee-soft hover:bg-cream-deep hover:text-coffee transition-colors"
          >
            <CloseIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Mensagem de Erro Geral */}
        {erroGeral && (
          <div
            role="alert"
            className="mx-6 mt-4 rounded-sm border border-[#a4533f]/30 bg-[#a4533f]/[0.06] px-4 py-2.5 font-body text-xs font-medium text-[#a4533f]"
          >
            {erroGeral}
          </div>
        )}

        {/* Conteúdo */}
        <div className="flex-1 overflow-y-auto p-6">
          {modo === 'lista' ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center pb-2 border-b border-line">
                <span className="font-body text-xs font-semibold uppercase tracking-wider text-coffee-soft">
                  Cartões cadastrados ({cartoes.length})
                </span>
                <button
                  type="button"
                  onClick={() => {
                    setForm({
                      id: null,
                      numero: '',
                      titular: '',
                      mes: '',
                      ano: '',
                      cvc: '',
                      apelido: '',
                      isDefault: false,
                    })
                    setErros({})
                    setModo('formulario')
                  }}
                  className="font-body text-xs font-semibold uppercase tracking-wider text-forest hover:text-forest-soft flex items-center gap-1.5 transition-colors"
                >
                  <span className="text-base leading-none font-bold">+</span>
                  Novo cartão
                </button>
              </div>

              {cartoes.length === 0 ? (
                <div className="text-center py-10">
                  <p className="font-body text-sm text-coffee-soft">
                    Nenhum cartão cadastrado até o momento.
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      setForm({
                        id: null,
                        numero: '',
                        titular: '',
                        mes: '',
                        ano: '',
                        cvc: '',
                        apelido: '',
                        isDefault: false,
                      })
                      setErros({})
                      setModo('formulario')
                    }}
                    className="mt-4 inline-flex items-center gap-2 rounded-sm bg-forest px-5 py-2.5 font-body text-xs font-semibold uppercase tracking-wider text-cream-soft hover:bg-forest-soft transition-colors"
                  >
                    + Adicionar meu primeiro cartão
                  </button>
                </div>
              ) : (
                <div className="grid gap-3">
                  {cartoes.map((card) => {
                    const isSelected = card.id === cartaoSelecionadoId
                    return (
                      <div
                        key={card.id}
                        onClick={() => {
                          onSelecionarCartao?.(card)
                          onClose()
                        }}
                        className={`group relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 rounded-md border transition-all cursor-pointer ${
                          isSelected
                            ? 'border-forest bg-forest/[0.04] ring-1 ring-forest/30'
                            : 'border-line-strong bg-cream-soft hover:border-gold/60 hover:bg-cream'
                        }`}
                      >
                        <div className="flex items-center gap-3.5">
                          <input
                            type="radio"
                            name="modal_cartao_selecao"
                            checked={isSelected}
                            onChange={() => {
                              onSelecionarCartao?.(card)
                              onClose()
                            }}
                            className="accent-forest cursor-pointer"
                          />
                          {/* Emblema do cartão */}
                          <div className="flex h-10 w-14 items-center justify-center rounded bg-coffee text-[0.7rem] font-bold tracking-wider text-cream shadow-sm">
                            {card.bandeiraNome?.toUpperCase().slice(0, 4) || 'CARD'}
                          </div>

                          <div>
                            <div className="flex items-center gap-2 flex-wrap">
                              <p className="font-body text-sm font-semibold text-coffee">
                                {card.apelido || `${card.bandeiraNome} final ${card.ultimos4}`}
                              </p>
                              {card.isDefault && (
                                <span className="rounded-full bg-gold/15 px-2.5 py-0.5 font-body text-[0.7rem] font-semibold text-gold-dark uppercase tracking-wider">
                                  Padrão
                                </span>
                              )}
                              {isSelected && (
                                <span className="rounded-full bg-forest/15 px-2.5 py-0.5 font-body text-[0.7rem] font-semibold text-forest uppercase tracking-wider">
                                  Selecionado
                                </span>
                              )}
                            </div>
                            <p className="font-body text-xs text-coffee-soft mt-0.5">
                              {card.numeroMascarado} • Venc. {card.mes}/{card.ano} • {card.titular}
                            </p>
                          </div>
                        </div>

                        {/* Ações */}
                        <div className="flex items-center gap-2 self-end sm:self-center">
                          {!card.isDefault && (
                            <button
                              type="button"
                              onClick={(e) => handleDefinirPadrao(card.id, e)}
                              className="font-body text-[0.75rem] font-medium text-coffee-faint hover:text-coffee px-2 py-1 rounded transition-colors"
                              title="Tornar cartão padrão"
                            >
                              Tornar padrão
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleIniciarEdicao(card)
                            }}
                            className="font-body text-[0.75rem] font-medium text-forest hover:text-forest-soft px-2 py-1 rounded transition-colors"
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            disabled={excluindoId === card.id}
                            onClick={(e) => handleExcluir(card.id, e)}
                            className="font-body text-[0.75rem] font-medium text-[#a4533f] hover:text-[#823d2d] px-2 py-1 rounded transition-colors disabled:opacity-50"
                          >
                            Excluir
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          ) : (
            <form onSubmit={handleSalvar} noValidate className="space-y-4">
              {/* Preview visual do Cartão */}
              <div className="mx-auto max-w-sm rounded-lg bg-gradient-to-br from-forest via-[#114030] to-coffee p-5 text-cream-soft shadow-lg border border-gold/30">
                <div className="flex items-center justify-between">
                  {/* Chip do cartão */}
                  <div className="h-7 w-9 rounded-sm bg-gradient-to-r from-amber-200 to-amber-400 opacity-90 shadow-inner flex items-center justify-center">
                    <div className="h-5 w-7 border border-amber-600/40 rounded-sm"></div>
                  </div>
                  <span className="font-body text-xs font-bold tracking-widest text-gold uppercase">
                    {bandeiraAtual.nome}
                  </span>
                </div>

                <div className="mt-5 font-mono text-lg tracking-[0.2em] text-cream">
                  {form.numero || '•••• •••• •••• ••••'}
                </div>

                <div className="mt-4 flex items-end justify-between font-body text-xs">
                  <div>
                    <span className="block text-[0.65rem] uppercase tracking-wider text-cream/60">
                      Titular do Cartão
                    </span>
                    <span className="font-medium tracking-wide uppercase">
                      {form.titular || 'SEU NOME AQUI'}
                    </span>
                  </div>
                  <div>
                    <span className="block text-[0.65rem] uppercase tracking-wider text-cream/60">
                      Validade
                    </span>
                    <span className="font-medium tracking-wider">
                      {form.mes ? String(form.mes).padStart(2, '0') : 'MM'}/
                      {form.ano ? String(form.ano).slice(-2) : 'AA'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Campos do formulário */}
              <div className="space-y-4 pt-2">
                {!form.id ? (
                  <CampoFormulario
                    id="modal_card_numero"
                    label="Número do Cartão"
                    erro={erros.numero}
                  >
                    <div className="relative">
                      <input
                        id="modal_card_numero"
                        inputMode="numeric"
                        autoComplete="cc-number"
                        value={form.numero}
                        onChange={handleNumeroChange}
                        placeholder="Número do cartão (16 dígitos)"
                        className={`w-full rounded-sm border bg-cream-soft py-3.5 pl-4 pr-16 font-body text-[0.95rem] text-coffee placeholder:text-coffee-faint transition-colors duration-300 focus:outline-none ${
                          erros.numero
                            ? 'border-caramel-dark focus:border-caramel-dark'
                            : 'border-line-strong focus:border-forest'
                        }`}
                      />
                      <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 font-body text-xs font-semibold text-gold">
                        {bandeiraAtual.nome}
                      </span>
                    </div>
                  </CampoFormulario>
                ) : (
                  <div>
                    <label className="block font-body text-xs font-semibold uppercase tracking-wider text-coffee-soft mb-1">
                      Número do Cartão
                    </label>
                    <input
                      disabled
                      value={form.numero}
                      className="w-full rounded-sm border border-line bg-cream-deep px-4 py-3 font-body text-[0.95rem] text-coffee-faint cursor-not-allowed"
                    />
                  </div>
                )}

                <CampoFormulario
                  id="modal_card_titular"
                  label="Nome impresso no cartão"
                  autoComplete="cc-name"
                  value={form.titular}
                  onChange={atualizarCampo('titular')}
                  erro={erros.titular}
                />

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label htmlFor="modal_card_mes" className="sr-only">
                        Mês
                      </label>
                      <select
                        id="modal_card_mes"
                        value={form.mes}
                        onChange={atualizarCampo('mes')}
                        className={`w-full appearance-none rounded-sm border bg-cream-soft px-4 py-3.5 font-body text-[0.95rem] text-coffee transition-colors duration-300 focus:outline-none ${
                          erros.mes
                            ? 'border-caramel-dark focus:border-caramel-dark'
                            : 'border-line-strong focus:border-forest'
                        }`}
                      >
                        <option value="">Mês</option>
                        {MESES.map((m) => (
                          <option key={m} value={m}>
                            {m}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label htmlFor="modal_card_ano" className="sr-only">
                        Ano
                      </label>
                      <select
                        id="modal_card_ano"
                        value={form.ano}
                        onChange={atualizarCampo('ano')}
                        className={`w-full appearance-none rounded-sm border bg-cream-soft px-4 py-3.5 font-body text-[0.95rem] text-coffee transition-colors duration-300 focus:outline-none ${
                          erros.ano
                            ? 'border-caramel-dark focus:border-caramel-dark'
                            : 'border-line-strong focus:border-forest'
                        }`}
                      >
                        <option value="">Ano</option>
                        {ANOS.map((a) => (
                          <option key={a} value={a}>
                            {a}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {!form.id ? (
                    <CampoFormulario
                      id="modal_card_cvc"
                      label="CVC / Código de segurança"
                      inputMode="numeric"
                      autoComplete="cc-csc"
                      maxLength={4}
                      value={form.cvc}
                      onChange={(e) =>
                        setForm((prev) => ({
                          ...prev,
                          cvc: e.target.value.replace(/\D/g, '').slice(0, 4),
                        }))
                      }
                      erro={erros.cvc}
                    />
                  ) : (
                    <div className="flex items-center text-xs text-coffee-faint italic pt-3">
                      CVC protegido
                    </div>
                  )}
                </div>

                <CampoFormulario
                  id="modal_card_apelido"
                  label="Apelido do cartão (opcional, ex: Nubank, Cartão PJ)"
                  value={form.apelido}
                  onChange={atualizarCampo('apelido')}
                />

                <div className="pt-2">
                  <label className="flex items-center gap-2.5 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={form.isDefault}
                      onChange={(e) =>
                        setForm((prev) => ({ ...prev, isDefault: e.target.checked }))
                      }
                      className="accent-forest h-4 w-4 rounded border-line-strong"
                    />
                    <span className="font-body text-xs text-coffee font-medium">
                      Definir como cartão principal
                    </span>
                  </label>
                </div>
              </div>

              {/* Botões */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-line">
                {cartoes.length > 0 && (
                  <button
                    type="button"
                    onClick={() => {
                      setModo('lista')
                      setErros({})
                    }}
                    disabled={salvando}
                    className="rounded-sm border border-line-strong px-4 py-2.5 font-body text-xs font-semibold uppercase tracking-wider text-coffee hover:bg-cream-deep transition-colors"
                  >
                    Voltar para lista
                  </button>
                )}
                <button
                  type="button"
                  onClick={onClose}
                  disabled={salvando}
                  className="rounded-sm border border-line-strong px-4 py-2.5 font-body text-xs font-semibold uppercase tracking-wider text-coffee-soft hover:bg-cream-deep transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={salvando}
                  className="rounded-sm bg-forest px-6 py-2.5 font-body text-xs font-semibold uppercase tracking-wider text-cream-soft hover:bg-forest-soft transition-colors shadow-sm disabled:opacity-60"
                >
                  {salvando ? 'Salvando…' : form.id ? 'Salvar alterações' : 'Salvar cartão'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}

export default function ModalCartao({ isOpen, ...props }) {
  if (!isOpen) return null
  return (
    <ModalCartaoDialog
      key={`${props.modoInicial}-${props.cartaoParaEditar?.id || 'novo'}`}
      {...props}
    />
  )
}
