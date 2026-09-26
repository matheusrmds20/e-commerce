/**
 * Serviço de gerenciamento de cartões de pagamento (CRUD local por usuário).
 *
 * Em conformidade com boas práticas de segurança, não enviamos números
 * de cartão brutos ao backend (onde ainda não há gateway PCI).
 * Os cartões salvos ficam armazenados no navegador do cliente vinculados
 * ao ID do usuário autenticado.
 */

const STORAGE_PREFIX = 'papiro.cards_'

function getStorageKey(userId) {
  return `${STORAGE_PREFIX}${userId || 'guest'}`
}

/**
 * Detecta a bandeira do cartão com base nos primeiros dígitos (BIN).
 */
export function detectarBandeira(numero = '') {
  const limpo = String(numero).replace(/\D/g, '')
  if (/^4/.test(limpo)) return { id: 'visa', nome: 'Visa', cor: '#1a1f71' }
  if (/^(5[1-5]|2[2-7])/.test(limpo)) return { id: 'mastercard', nome: 'Mastercard', cor: '#eb001b' }
  if (/^3[47]/.test(limpo)) return { id: 'amex', nome: 'American Express', cor: '#007bc1' }
  if (/^(4011|4389|5041|5067|5090|6277|6362|6363|6504|6505|6516)/.test(limpo)) {
    return { id: 'elo', nome: 'Elo', cor: '#00a4e8' }
  }
  if (/^(606282|3841)/.test(limpo)) return { id: 'hipercard', nome: 'Hipercard', cor: '#b3131b' }
  return { id: 'generic', nome: 'Cartão', cor: '#4b3621' }
}

/** Formata o número do cartão em blocos de 4 dígitos */
export function formatarNumeroCartao(valor = '') {
  const limpo = String(valor).replace(/\D/g, '').slice(0, 16)
  return limpo.replace(/(\d{4})(?=\d)/g, '$1 ')
}

/** Mascara o número do cartão mostrando apenas os 4 últimos dígitos */
export function mascararCartao(numero = '') {
  const limpo = String(numero).replace(/\D/g, '')
  const ultimos4 = limpo.slice(-4) || '••••'
  return `•••• •••• •••• ${ultimos4}`
}

export const cardService = {
  /**
   * Lista os cartões cadastrados do usuário.
   */
  listar(userId) {
    try {
      const raw = localStorage.getItem(getStorageKey(userId))
      if (!raw) return []
      const cards = JSON.parse(raw)
      return Array.isArray(cards) ? cards : []
    } catch {
      return []
    }
  },

  /**
   * Salva a lista completa de cartões no storage.
   */
  salvarTodos(userId, cartoes) {
    try {
      localStorage.setItem(getStorageKey(userId), JSON.stringify(cartoes))
    } catch (e) {
      console.error('Erro ao persistir cartões no localStorage:', e)
    }
  },

  /**
   * Cria um novo cartão para o usuário.
   */
  criar(userId, { numero, titular, mes, ano, apelido, isDefault = false }) {
    const cartoes = this.listar(userId)
    const numeroLimpo = String(numero).replace(/\D/g, '')
    const bandeira = detectarBandeira(numeroLimpo)
    const ultimos4 = numeroLimpo.slice(-4)

    const novoCartao = {
      id: `card_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
      bandeira: bandeira.id,
      bandeiraNome: bandeira.nome,
      numeroMascarado: `•••• •••• •••• ${ultimos4}`,
      ultimos4,
      titular: titular.trim().toUpperCase(),
      mes: String(mes).padStart(2, '0'),
      ano: String(ano),
      apelido: apelido?.trim() || `${bandeira.nome} final ${ultimos4}`,
      isDefault: Boolean(isDefault) || cartoes.length === 0,
      createdAt: new Date().toISOString(),
    }

    let atualizados = cartoes
    if (novoCartao.isDefault) {
      atualizados = atualizados.map((c) => ({ ...c, isDefault: false }))
    }
    atualizados.push(novoCartao)

    this.salvarTodos(userId, atualizados)
    return novoCartao
  },

  /**
   * Atualiza informações de um cartão existente.
   */
  atualizar(userId, cardId, { titular, mes, ano, apelido, isDefault }) {
    const cartoes = this.listar(userId)
    const index = cartoes.findIndex((c) => c.id === cardId)
    if (index === -1) throw new Error('Cartão não encontrado.')

    let atualizados = cartoes.map((card) => {
      if (card.id === cardId) {
        return {
          ...card,
          ...(titular ? { titular: titular.trim().toUpperCase() } : {}),
          ...(mes ? { mes: String(mes).padStart(2, '0') } : {}),
          ...(ano ? { ano: String(ano) } : {}),
          ...(apelido !== undefined ? { apelido: apelido.trim() } : {}),
          ...(isDefault !== undefined ? { isDefault: Boolean(isDefault) } : {}),
          updatedAt: new Date().toISOString(),
        }
      }
      if (isDefault) {
        return { ...card, isDefault: false }
      }
      return card
    })

    this.salvarTodos(userId, atualizados)
    return atualizados.find((c) => c.id === cardId)
  },

  /**
   * Exclui um cartão. Se o cartão excluído era o padrão, define o primeiro restante como padrão.
   */
  excluir(userId, cardId) {
    const cartoes = this.listar(userId)
    const filtrados = cartoes.filter((c) => c.id !== cardId)
    const eraDefault = cartoes.find((c) => c.id === cardId)?.isDefault

    if (eraDefault && filtrados.length > 0) {
      filtrados[0].isDefault = true
    }

    this.salvarTodos(userId, filtrados)
    return true
  },

  /**
   * Define um cartão como padrão.
   */
  definirPadrao(userId, cardId) {
    const cartoes = this.listar(userId)
    const atualizados = cartoes.map((c) => ({
      ...c,
      isDefault: c.id === cardId,
    }))
    this.salvarTodos(userId, atualizados)
    return atualizados.find((c) => c.id === cardId)
  },
}

export default cardService
