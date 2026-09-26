import { useEffect, useState } from 'react'
import CampoFormulario from './CampoFormulario'
import { CloseIcon } from './Icons'
import addressService from '../api/addresses'

const ESTADOS_BRASIL = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
]

const formatarCep = (valor = '') =>
  valor
    .replace(/\D/g, '')
    .slice(0, 8)
    .replace(/(\d{5})(?=\d)/, '$1-')

function ModalEnderecoDialog({
  onClose,
  enderecos = [],
  enderecoSelecionadoId = null,
  onSelecionarEndereco,
  onRecarregarEnderecos,
  modoInicial = 'lista',
  enderecoParaEditar = null,
}) {
  const [modo, setModo] = useState(() => {
    if (modoInicial === 'novo' || enderecos.length === 0) return 'formulario'
    if (modoInicial === 'editar' && enderecoParaEditar) return 'formulario'
    return 'lista'
  })

  const [form, setForm] = useState(() => {
    if (modoInicial === 'editar' && enderecoParaEditar) {
      return {
        id: enderecoParaEditar.id,
        street: enderecoParaEditar.street || '',
        number: enderecoParaEditar.number || '',
        complement: enderecoParaEditar.complement || '',
        neighborhood: enderecoParaEditar.neighborhood || '',
        city: enderecoParaEditar.city || '',
        state: enderecoParaEditar.state || '',
        zip_code: formatarCep(enderecoParaEditar.zip_code || ''),
        is_default: Boolean(enderecoParaEditar.is_default),
      }
    }
    return {
      id: null,
      street: '',
      number: '',
      complement: '',
      neighborhood: '',
      city: '',
      state: '',
      zip_code: '',
      is_default: false,
    }
  })

  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState(null)
  const [carregandoCep, setCarregandoCep] = useState(false)
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

  const atualizarCampo = (campo) => (e) => {
    const valor = e.target.value
    setForm((prev) => ({ ...prev, [campo]: valor }))
    if (erros[campo]) {
      setErros((prev) => ({ ...prev, [campo]: null }))
    }
  }

  // Busca automática por CEP via ViaCEP
  const handleCepChange = async (e) => {
    const formatado = formatarCep(e.target.value)
    setForm((prev) => ({ ...prev, zip_code: formatado }))
    if (erros.zip_code) {
      setErros((prev) => ({ ...prev, zip_code: null }))
    }

    const cepDigitos = formatado.replace(/\D/g, '')
    if (cepDigitos.length === 8) {
      try {
        setCarregandoCep(true)
        const res = await fetch(`https://viacep.com.br/ws/${cepDigitos}/json/`)
        const data = await res.json()
        if (!data.erro) {
          setForm((prev) => ({
            ...prev,
            street: data.logradouro || prev.street,
            neighborhood: data.bairro || prev.neighborhood,
            city: data.localidade || prev.city,
            state: data.uf || prev.state,
          }))
        }
      } catch {
        // Falha silenciosa no ViaCEP
      } finally {
        setCarregandoCep(false)
      }
    }
  }

  const validar = () => {
    const novoserros = {}
    if (!form.street.trim()) novoserros.street = 'Informe o logradouro.'
    if (!form.number.trim()) novoserros.number = 'Informe o número.'
    if (!form.neighborhood.trim()) novoserros.neighborhood = 'Informe o bairro.'
    if (!form.city.trim()) novoserros.city = 'Informe a cidade.'

    const cepDigitos = form.zip_code.replace(/\D/g, '')
    if (!cepDigitos) novoserros.zip_code = 'Informe o CEP.'
    else if (cepDigitos.length !== 8) novoserros.zip_code = 'CEP deve ter 8 dígitos.'

    if (!form.state.trim()) novoserros.state = 'Selecione o estado.'

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
      const payload = {
        street: form.street.trim(),
        number: form.number.trim(),
        complement: form.complement.trim() || null,
        neighborhood: form.neighborhood.trim(),
        city: form.city.trim(),
        state: form.state.trim().toUpperCase(),
        zip_code: form.zip_code.replace(/\D/g, ''),
        is_default: form.is_default,
      }

      let salvo
      if (form.id) {
        salvo = await addressService.atualizar(form.id, payload)
      } else {
        salvo = await addressService.criar(payload)
      }

      await onRecarregarEnderecos?.()
      if (onSelecionarEndereco && salvo) {
        onSelecionarEndereco(salvo)
      }
      onClose()
    } catch (err) {
      setErroGeral(err.message || 'Erro ao salvar o endereço.')
    } finally {
      setSalvando(false)
    }
  }

  const handleIniciarEdicao = (end) => {
    setForm({
      id: end.id,
      street: end.street || '',
      number: end.number || '',
      complement: end.complement || '',
      neighborhood: end.neighborhood || '',
      city: end.city || '',
      state: end.state || '',
      zip_code: formatarCep(end.zip_code || ''),
      is_default: Boolean(end.is_default),
    })
    setErros({})
    setErroGeral(null)
    setModo('formulario')
  }

  const handleExcluir = async (id, e) => {
    e.stopPropagation()
    if (excluindoId) return
    if (!window.confirm('Tem certeza que deseja excluir este endereço?')) return

    try {
      setExcluindoId(id)
      await addressService.excluir(id)
      await onRecarregarEnderecos?.()
    } catch (err) {
      setErroGeral(err.message || 'Não foi possível excluir o endereço.')
    } finally {
      setExcluindoId(null)
    }
  }

  const handleDefinirPadrao = async (id, e) => {
    e.stopPropagation()
    try {
      await addressService.definirPadrao(id)
      await onRecarregarEnderecos?.()
    } catch (err) {
      setErroGeral(err.message || 'Erro ao definir endereço como padrão.')
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-endereco-titulo"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-coffee/60 backdrop-blur-sm transition-all"
    >
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col rounded-md border border-line bg-cream-soft shadow-2xl overflow-hidden">
        {/* Cabeçalho */}
        <div className="flex items-center justify-between border-b border-line px-6 py-4 bg-cream">
          <div>
            <h2
              id="modal-endereco-titulo"
              className="font-display text-2xl font-normal text-coffee"
            >
              {modo === 'formulario'
                ? form.id
                  ? 'Editar endereço'
                  : 'Cadastrar novo endereço'
                : 'Meus endereços de entrega'}
            </h2>
            <p className="font-body text-xs text-coffee-faint">
              {modo === 'formulario'
                ? 'Preencha os campos abaixo com os dados de envio'
                : 'Selecione, edite ou cadastre um endereço para sua entrega'}
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
                  Endereços cadastrados ({enderecos.length})
                </span>
                <button
                  type="button"
                  onClick={() => {
                    setForm({
                      id: null,
                      street: '',
                      number: '',
                      complement: '',
                      neighborhood: '',
                      city: '',
                      state: '',
                      zip_code: '',
                      is_default: false,
                    })
                    setErros({})
                    setModo('formulario')
                  }}
                  className="font-body text-xs font-semibold uppercase tracking-wider text-forest hover:text-forest-soft flex items-center gap-1.5 transition-colors"
                >
                  <span className="text-base leading-none font-bold">+</span>
                  Adicionar endereço
                </button>
              </div>

              {enderecos.length === 0 ? (
                <div className="text-center py-10">
                  <p className="font-body text-sm text-coffee-soft">
                    Você ainda não possui nenhum endereço cadastrado.
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      setForm({
                        id: null,
                        street: '',
                        number: '',
                        complement: '',
                        neighborhood: '',
                        city: '',
                        state: '',
                        zip_code: '',
                        is_default: false,
                      })
                      setErros({})
                      setModo('formulario')
                    }}
                    className="mt-4 inline-flex items-center gap-2 rounded-sm bg-forest px-5 py-2.5 font-body text-xs font-semibold uppercase tracking-wider text-cream-soft hover:bg-forest-soft transition-colors"
                  >
                    + Cadastrar primeiro endereço
                  </button>
                </div>
              ) : (
                <div className="grid gap-3">
                  {enderecos.map((end) => {
                    const isSelected = end.id === enderecoSelecionadoId
                    return (
                      <div
                        key={end.id}
                        onClick={() => {
                          onSelecionarEndereco?.(end)
                          onClose()
                        }}
                        className={`group relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 rounded-md border transition-all cursor-pointer ${
                          isSelected
                            ? 'border-forest bg-forest/[0.04] ring-1 ring-forest/30'
                            : 'border-line-strong bg-cream-soft hover:border-gold/60 hover:bg-cream'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <input
                            type="radio"
                            name="modal_endereco_selecao"
                            checked={isSelected}
                            onChange={() => {
                              onSelecionarEndereco?.(end)
                              onClose()
                            }}
                            className="mt-1 accent-forest cursor-pointer"
                          />
                          <div>
                            <div className="flex items-center gap-2 flex-wrap">
                              <p className="font-body text-sm font-semibold text-coffee">
                                {end.street}, {end.number}
                                {end.complement ? ` - ${end.complement}` : ''}
                              </p>
                              {end.is_default && (
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
                              {end.neighborhood} • {end.city} - {end.state} • CEP {formatarCep(end.zip_code)}
                            </p>
                          </div>
                        </div>

                        {/* Ações */}
                        <div className="flex items-center gap-2 self-end sm:self-center">
                          {!end.is_default && (
                            <button
                              type="button"
                              onClick={(e) => handleDefinirPadrao(end.id, e)}
                              className="font-body text-[0.75rem] font-medium text-coffee-faint hover:text-coffee px-2 py-1 rounded transition-colors"
                              title="Tornar endereço padrão"
                            >
                              Tornar padrão
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleIniciarEdicao(end)
                            }}
                            className="font-body text-[0.75rem] font-medium text-forest hover:text-forest-soft px-2 py-1 rounded transition-colors"
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            disabled={excluindoId === end.id}
                            onClick={(e) => handleExcluir(end.id, e)}
                            className="font-body text-[0.75rem] font-medium text-[#a4533f] hover:text-[#823d2d] px-2 py-1 rounded transition-colors disabled:opacity-50"
                          >
                            {excluindoId === end.id ? 'Excluindo…' : 'Excluir'}
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
              <div className="grid gap-4 sm:grid-cols-[180px_1fr]">
                <div className="relative">
                  <CampoFormulario
                    id="modal_cep"
                    label="CEP"
                    inputMode="numeric"
                    value={form.zip_code}
                    onChange={handleCepChange}
                    erro={erros.zip_code}
                  />
                  {carregandoCep && (
                    <span className="absolute right-3 top-3.5 font-body text-[0.75rem] text-coffee-faint animate-pulse">
                      Buscando…
                    </span>
                  )}
                </div>

                <CampoFormulario
                  id="modal_street"
                  label="Logradouro / Rua / Avenida"
                  value={form.street}
                  onChange={atualizarCampo('street')}
                  erro={erros.street}
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-[140px_1fr]">
                <CampoFormulario
                  id="modal_number"
                  label="Número"
                  value={form.number}
                  onChange={atualizarCampo('number')}
                  erro={erros.number}
                />
                <CampoFormulario
                  id="modal_complement"
                  label="Complemento (Apto, Bloco, etc.)"
                  value={form.complement}
                  onChange={atualizarCampo('complement')}
                />
              </div>

              <CampoFormulario
                id="modal_neighborhood"
                label="Bairro"
                value={form.neighborhood}
                onChange={atualizarCampo('neighborhood')}
                erro={erros.neighborhood}
              />

              <div className="grid gap-4 sm:grid-cols-[1fr_140px]">
                <CampoFormulario
                  id="modal_city"
                  label="Cidade"
                  value={form.city}
                  onChange={atualizarCampo('city')}
                  erro={erros.city}
                />

                <div>
                  <label htmlFor="modal_state" className="sr-only">
                    Estado (UF)
                  </label>
                  <select
                    id="modal_state"
                    name="state"
                    value={form.state}
                    onChange={atualizarCampo('state')}
                    className={`w-full appearance-none rounded-sm border bg-cream-soft px-4 py-3.5 font-body text-[0.95rem] text-coffee transition-colors duration-300 focus:outline-none ${
                      erros.state
                        ? 'border-caramel-dark focus:border-caramel-dark'
                        : 'border-line-strong focus:border-forest'
                    }`}
                  >
                    <option value="">UF</option>
                    {ESTADOS_BRASIL.map((uf) => (
                      <option key={uf} value={uf}>
                        {uf}
                      </option>
                    ))}
                  </select>
                  {erros.state && (
                    <p className="mt-1 font-body text-[0.8rem] font-medium text-caramel-dark">
                      {erros.state}
                    </p>
                  )}
                </div>
              </div>

              <div className="pt-2">
                <label className="flex items-center gap-2.5 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={form.is_default}
                    onChange={(e) =>
                      setForm((prev) => ({ ...prev, is_default: e.target.checked }))
                    }
                    className="accent-forest h-4 w-4 rounded border-line-strong"
                  />
                  <span className="font-body text-xs text-coffee font-medium">
                    Definir como endereço de entrega padrão
                  </span>
                </label>
              </div>

              {/* Botões do Formulário */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-line">
                {enderecos.length > 0 && (
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
                  {salvando ? 'Salvando…' : form.id ? 'Salvar alterações' : 'Cadastrar endereço'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}

export default function ModalEndereco({ isOpen, ...props }) {
  if (!isOpen) return null
  return (
    <ModalEnderecoDialog
      key={`${props.modoInicial}-${props.enderecoParaEditar?.id || 'novo'}`}
      {...props}
    />
  )
}
