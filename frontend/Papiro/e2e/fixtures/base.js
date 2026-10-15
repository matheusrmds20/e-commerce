import { test as base, expect } from '@playwright/test'
import { navegarPara } from '../helpers/navegar'
import { registrarPelaUi, loginPelaUi, emailUnico } from '../helpers/auth'


export const test = base.extend({

  navegarPara: async ({ page }, use) => {
    await use((destino) => navegarPara(page, destino))
  },

  registrarPelaUi: async ({ page }, use) => {
    await use((opcoes = {}) => registrarPelaUi(page, opcoes))
  },

  loginPelaUi: async ({ page }, use) => {
    await use((opcoes) => loginPelaUi(page, opcoes))
  },

  // eslint-disable-next-line no-empty-pattern
  emailUnico: async ({}, use) => {
    await use(emailUnico)
  },
})

export { expect }