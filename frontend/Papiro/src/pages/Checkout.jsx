import { useMemo, useState } from 'react'
import CampoFormulario from '../components/CampoFormulario'
import ResumoPedido from '../components/ResumoPedido'
import { LockIcon } from '../components/Icons'
import { useCart } from '../context/cart-context'
import { useAuth } from '../context/auth-context'
import { calcularTotais, formatarPreco } from '../api/adapters'
import addressService from '../api/addresses'
import orderService from '../api/orders'

// Meses de validade gerados sem Date — lista fixa e previsível
const MESES = Array.from({ length: 12 }, (_, i) =>
  String(i + 1).padStart(2, '0'),
)
const ANOS = Array.from({ length: 10 }, (_, i) => String(2026 + i))

const FORM_INICIAL = {
  nome: '',
  sobrenome: '',
  cep: '',
  endereco: '',
  numero: '',
  complemento: '',
  bairro: '',
  cidade: '',
  estado: '',
  cartao: '',
  mes: '',
  ano: '',
  cvc: '',
}

/** Agrupa os dígitos do cartão em blocos de 4. */
const formatarCartao = (valor) =>
  valor
    .replace(/\D/g, '')
    .slice(0, 16)
    .replace(/(\d{4})(?=\d)/g, '$1 ')

/** CEP no formato 00000-000. */
const formatarCep = (valor) =>
  valor
    .replace(/\D/g, '')
    .slice(0, 8)
    .replace(/(\d{5})(?=\d)/, '$1-')

/**
 * Valida os campos antes de bater na API (espelha as regras do backend).
 * @returns {Record<string, string>} erros por campo (vazio = ok)
 */
function validar(dados) {
  const erros = {}
  const obrigatorio = (campo, msg) => {
    if (!dados[campo].trim()) erros[campo] = msg
  }

  obrigatorio('nome', 'Informe seu nome.')
  obrigatorio('sobrenome', 'Informe seu sobrenome.')
  obrigatorio('endereco', 'Informe o logradouro.')
  obrigatorio('numero', 'Informe o número.')
  obrigatorio('bairro', 'Informe o bairro.')
  obrigatorio('cidade', 'Informe a cidade.')

  const cepDigitos = dados.cep.replace(/\D/g, '')
  if (!cepDigitos) erros.cep = 'Informe o CEP.'
  else if (cepDigitos.length !== 8) erros.cep = 'CEP deve ter 8 dígitos.'

  if (!dados.estado.trim()) erros.estado = 'UF obrigatória.'
  else if (dados.estado.trim().length !== 2) erros.estado = 'Use a sigla (2 letras).'

  const cartaoDigitos = dados.cartao.replace(/\D/g, '')
  if (!cartaoDigitos) erros.cartao = 'Informe o número do cartão.'
  else if (cartaoDigitos.length !== 16) erros.cartao = 'O cartão deve ter 16 dígitos.'

  if (!dados.mes) erros.mes = 'Mês obrigatório.'
  if (!dados.ano) erros.ano = 'Ano obrigatório.'
  if (!dados.cvc.trim()) erros.cvc = 'Informe o CVC.'
  else if (dados.cvc.length < 3) erros.cvc = 'CVC inválido.'

  return erros
}

/**
 * Checkout — resumo do pedido à esquerda, formulário de pagamento à direita.
 *
 * A compra é gravada no backend em duas etapas:
 *   1. `POST /addresses/create` — grava o endereço de entrega do usuário;
 *   2. `POST /orders/create`    — grava o pedido com os itens da sacola.
 *
 * Os dados do cartão NÃO são enviados (não há gateway de pagamento no
 * backend ainda); só os dados de entrega e os itens.
 */
export default function Checkout({ onIrParaLogin }) {
  const { itens, carregando: carrinhoCarregando, recarregar } = useCart()
  const { autenticado } = useAuth()

  const [dados, setDados] = useState(FORM_INICIAL)
  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const [pedido, setPedido] = useState(null)

  const atualizar = (campo) => (event) =>
    setDados((atual) => ({ ...atual, [campo]: event.target.value }))

  const { subtotal, frete, total } = useMemo(
    () => calcularTotais(itens),
    [itens],
  )

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (enviando || pedido) return

    setErroGeral(null)

    if (!autenticado) {
      setErroGeral({
        message: 'Entre na sua conta para finalizar a compra.',
        code: 'NOT_AUTHENTICATED',
      })
      return
    }

    if (itens.length === 0) {
      setErroGeral({
        message: 'Sua sacola está vazia.',
        code: 'EMPTY_CART',
      })
      return
    }

    const validacao = validar(dados)
    setErros(validacao)
    if (Object.keys(validacao).length > 0) {
      setErroGeral({
        message: 'Revise os campos destacados antes de continuar.',
        code: 'VALIDATION_ERROR',
      })
      return
    }

    setEnviando(true)

    try {
      // 1. Endereço de entrega (dono = usuário do token).
      const endereco = await addressService.criar({
        street: dados.endereco.trim(),
        number: dados.numero.trim(),
        complement: dados.complemento.trim() || null,
        neighborhood: dados.bairro.trim(),
        city: dados.cidade.trim(),
        state: dados.estado.trim().toUpperCase(),
        zip_code: dados.cep.replace(/\D/g, ''),
        is_default: true,
      })

      // 2. Pedido com os itens reais da sacola.
      const criado = await orderService.criar({
        address_id: endereco.id,
        notes: null,
        items: itens.map((item) => ({
          product_id: item.productId ?? item.id,
          quantity: item.quantidade,
        })),
      })

      setPedido(criado)
      // O backend esvazia o carrinho no checkout; sincroniza o badge/estado.
      await recarregar()
    } catch (error) {
      setErroGeral(error)
    } finally {
      setEnviando(false)
    }
  }

  const erroDoCampo = (campo) => erros[campo]

  return (
    <main className="bg-cream-deep">
      <div className="mx-auto max-w-[1400px] px-5 py-12 sm:px-8 sm:py-16">
        <h1 className="font-display text-[2.5rem] leading-tight font-normal text-coffee sm:text-[3.25rem]">
          Finalizar compra
        </h1>

        <div className="mt-10 grid gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)] lg:gap-16">
          <ResumoPedido
            itens={itens}
            subtotal={subtotal}
            frete={frete}
            total={total}
            formatarPreco={formatarPreco}
          />

          {/* Formulário */}
          <section className="rounded-md border border-line bg-cream-soft p-6 sm:p-9 shadow-sm">
            <h2 className="font-display text-[1.75rem] font-normal text-coffee">
              Formulário de pagamento seguro
            </h2>

            {/* Visitante precisa entrar — o backend exige um usuário dono */}
            {!autenticado && (
              <div className="mt-6 flex flex-wrap items-center gap-x-3 gap-y-2 border-y border-line py-4">
                <p className="font-body text-[0.9rem] text-coffee-soft">
                  Você precisa estar logado para finalizar a compra.
                </p>
                <button
                  type="button"
                  onClick={onIrParaLogin}
                  className="font-body text-[0.8rem] font-semibold uppercase tracking-[0.16em] text-gold transition-colors duration-300 hover:text-caramel-dark"
                >
                  Entrar
                </button>
              </div>
            )}

            {erroGeral && (
              <div
                role="alert"
                className="mt-6 rounded-sm border border-[#a4533f]/30 bg-[#a4533f]/[0.06] px-4 py-3 font-body text-[0.86rem] font-medium tracking-wide text-[#a4533f]"
              >
                {erroGeral.message}
              </div>
            )}

            {pedido && (
              <p
                role="status"
                className="mt-6 rounded-sm border border-forest/30 bg-forest-tint px-4 py-3 text-center font-body text-[0.88rem] font-medium text-forest"
              >
                Pedido #{pedido.id} confirmado! Total de{' '}
                {formatarPreco(pedido.total)}.
              </p>
            )}

            <form onSubmit={handleSubmit} noValidate className="mt-8">
              {/* Entrega */}
              <fieldset disabled={enviando || Boolean(pedido)}>
                <legend className="font-body text-[1rem] font-semibold text-coffee">
                  Dados de Entrega
                </legend>

                <div className="mt-4 flex flex-col gap-4">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <CampoFormulario
                      id="nome"
                      label="Nome"
                      autoComplete="given-name"
                      value={dados.nome}
                      onChange={atualizar('nome')}
                      erro={erroDoCampo('nome')}
                    />
                    <CampoFormulario
                      id="sobrenome"
                      label="Sobrenome"
                      autoComplete="family-name"
                      value={dados.sobrenome}
                      onChange={atualizar('sobrenome')}
                      erro={erroDoCampo('sobrenome')}
                    />
                  </div>

                  <div className="grid gap-4 sm:grid-cols-[180px_1fr]">
                    <CampoFormulario
                      id="cep"
                      label="CEP"
                      inputMode="numeric"
                      autoComplete="postal-code"
                      value={dados.cep}
                      onChange={(event) =>
                        setDados((atual) => ({
                          ...atual,
                          cep: formatarCep(event.target.value),
                        }))
                      }
                      erro={erroDoCampo('cep')}
                    />
                    <CampoFormulario
                      id="endereco"
                      label="Endereço"
                      autoComplete="street-address"
                      value={dados.endereco}
                      onChange={atualizar('endereco')}
                      erro={erroDoCampo('endereco')}
                    />
                  </div>

                  <div className="grid gap-4 sm:grid-cols-[180px_1fr]">
                    <CampoFormulario
                      id="numero"
                      label="Número"
                      inputMode="numeric"
                      value={dados.numero}
                      onChange={atualizar('numero')}
                      erro={erroDoCampo('numero')}
                    />
                    <CampoFormulario
                      id="complemento"
                      label="Complemento (opcional)"
                      autoComplete="address-line2"
                      value={dados.complemento}
                      onChange={atualizar('complemento')}
                    />
                  </div>

                  <CampoFormulario
                    id="bairro"
                    label="Bairro"
                    autoComplete="address-line3"
                    value={dados.bairro}
                    onChange={atualizar('bairro')}
                    erro={erroDoCampo('bairro')}
                  />

                  <div className="grid gap-4 sm:grid-cols-2">
                    <CampoFormulario
                      id="cidade"
                      label="Cidade"
                      autoComplete="address-level2"
                      value={dados.cidade}
                      onChange={atualizar('cidade')}
                      erro={erroDoCampo('cidade')}
                    />
                    <CampoFormulario
                      id="estado"
                      label="Estado (UF)"
                      autoComplete="address-level1"
                      maxLength={2}
                      value={dados.estado}
                      onChange={(event) =>
                        setDados((atual) => ({
                          ...atual,
                          estado: event.target.value
                            .replace(/[^a-zA-Z]/g, '')
                            .toUpperCase(),
                        }))
                      }
                      erro={erroDoCampo('estado')}
                    />
                  </div>
                </div>
              </fieldset>

              {/* Cartão */}
              <fieldset className="mt-10" disabled={enviando || Boolean(pedido)}>
                <legend className="font-body text-[1rem] font-semibold text-coffee">
                  Dados do cartão de crédito
                </legend>

                <div className="mt-4 flex flex-col gap-4">
                  {/* Campo com ícone interno — o input é passado como children */}
                  <CampoFormulario
                    id="cartao"
                    label="Número do cartão"
                    erro={erroDoCampo('cartao')}
                  >
                    <div className="relative">
                      <input
                        id="cartao"
                        name="cartao"
                        inputMode="numeric"
                        autoComplete="cc-number"
                        value={dados.cartao}
                        onChange={(event) =>
                          setDados((atual) => ({
                            ...atual,
                            cartao: formatarCartao(event.target.value),
                          }))
                        }
                        placeholder="Número do cartão"
                        aria-invalid={Boolean(erroDoCampo('cartao'))}
                        className={`w-full rounded-sm border bg-cream-soft py-3.5 pl-4 pr-12 font-body text-[0.95rem] text-coffee placeholder:text-coffee-faint transition-colors duration-300 focus:outline-none ${
                          erroDoCampo('cartao')
                            ? 'border-caramel-dark focus:border-caramel-dark'
                            : 'border-line-strong focus:border-forest'
                        }`}
                      />
                      {/* Ícone de cartão dentro do campo, como na referência */}
                      <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-coffee-faint">
                        <svg
                          viewBox="0 0 24 24"
                          className="h-5 w-5"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.3"
                          strokeLinecap="round"
                          aria-hidden="true"
                        >
                          <rect x="3" y="5.5" width="18" height="13" rx="1.5" />
                          <path d="M3 10h18" />
                          <path d="M6.5 14.5h4" />
                        </svg>
                      </span>
                    </div>
                  </CampoFormulario>

                  <div className="grid gap-4 sm:grid-cols-2">
                    {/* Validade em dois selects */}
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label htmlFor="mes" className="sr-only">
                          Mês de validade
                        </label>
                        <select
                          id="mes"
                          name="mes"
                          autoComplete="cc-exp-month"
                          value={dados.mes}
                          onChange={atualizar('mes')}
                          aria-invalid={Boolean(erroDoCampo('mes'))}
                          className={`w-full appearance-none rounded-sm border bg-cream-soft px-4 py-3.5 font-body text-[0.95rem] text-coffee transition-colors duration-300 focus:outline-none ${
                            erroDoCampo('mes')
                              ? 'border-caramel-dark focus:border-caramel-dark'
                              : 'border-line-strong focus:border-forest'
                          }`}
                        >
                          <option value="">Mês</option>
                          {MESES.map((mes) => (
                            <option key={mes} value={mes}>
                              {mes}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label htmlFor="ano" className="sr-only">
                          Ano de validade
                        </label>
                        <select
                          id="ano"
                          name="ano"
                          autoComplete="cc-exp-year"
                          value={dados.ano}
                          onChange={atualizar('ano')}
                          aria-invalid={Boolean(erroDoCampo('ano'))}
                          className={`w-full appearance-none rounded-sm border bg-cream-soft px-4 py-3.5 font-body text-[0.95rem] text-coffee transition-colors duration-300 focus:outline-none ${
                            erroDoCampo('ano')
                              ? 'border-caramel-dark focus:border-caramel-dark'
                              : 'border-line-strong focus:border-forest'
                          }`}
                        >
                          <option value="">Ano</option>
                          {ANOS.map((ano) => (
                            <option key={ano} value={ano}>
                              {ano}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <CampoFormulario
                      id="cvc"
                      label="CVC"
                      inputMode="numeric"
                      autoComplete="cc-csc"
                      maxLength={4}
                      value={dados.cvc}
                      onChange={(event) =>
                        setDados((atual) => ({
                          ...atual,
                          cvc: event.target.value.replace(/\D/g, '').slice(0, 4),
                        }))
                      }
                      erro={erroDoCampo('cvc')}
                    />
                  </div>
                </div>
              </fieldset>

              <button
                type="submit"
                disabled={enviando || Boolean(pedido) || carrinhoCarregando}
                className="mt-9 w-full rounded-sm bg-forest py-4 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft shadow-md transition-all duration-300 ease-[var(--ease-cozy)] hover:bg-forest-soft hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:cursor-not-allowed disabled:opacity-60"
              >
                {pedido
                  ? 'Compra concluída'
                  : enviando
                    ? 'Processando…'
                    : 'Concluir compra'}
              </button>

              <p className="mt-4 flex items-center justify-center gap-2 font-body text-[0.8rem] font-medium text-coffee-faint">
                <LockIcon className="h-4 w-4" />
                Pagamento 100% criptografado. Não guardamos os dados do cartão.
              </p>
            </form>
          </section>
        </div>
      </div>
    </main>
  )
}
