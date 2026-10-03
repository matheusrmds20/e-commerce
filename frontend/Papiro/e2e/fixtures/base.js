import { test as base, expect } from '@playwright/test'
import { navegarPara } from '../helpers/navegar'
import { registrarPelaUi, loginPelaUi, emailUnico } from '../helpers/auth'

/**
 * Fixture base do E2E — expõe helpers prontos nos testes.
 * (A estrutura prevê este arquivo; os specs da Fase 4 também o usarão.)
 */
export const test = base.extend({
  // Navega pela nav flutuante: `await navegarPara('acervo')`.
  navegarPara: async ({ page }, use) => {
    await use((destino) => navegarPara(page, destino))
  },
  // Cria um usuário novo e já logado: `await registrarPelaUi({...})`.
  registrarPelaUi: async ({ page }, use) => {
    await use((opcoes = {}) => registrarPelaUi(page, opcoes))
  },
  // Login com credenciais existentes.
  loginPelaUi: async ({ page }, use) => {
    await use((opcoes) => loginPelaUi(page, opcoes))
  },
  // Gera um email único: `const email = emailUnico()`.
  emailUnico: async ({}, use) => {
    await use(emailUnico)
  },
})

export { expect }