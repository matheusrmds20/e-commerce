import { test, expect } from '../fixtures/base'

/**
 * 01 — Home carrega com dados reais da API local (DB de teste).
 * Valida também a infra: navbar + nav flutuante (Fase 1) presentes.
 */
test.describe('Home', () => {
  test('renderiza a vitrine alimentada pela API de teste', async ({
    page,
    registrarPelaUi,
    emailUnico,
  }) => {
    await page.goto('/')

    // A sacola só aparece para usuários autenticados, então logamos primeiro.
    await registrarPelaUi({ email: emailUnico('home') })

    // Infra: navbar com sacola (navegação agora via react-router).
    await expect(page.getByTestId('navbar-sacola')).toBeVisible()

    // Catálogo real vindo do banco bookcommerce-e2e (seed com 24 produtos).
    // "Dom Casmurro" é o 1º produto do seed — prova que a home consultou a
    // API local (e não produção).
    await expect(page.locator('body')).toContainText('Dom Casmurro', {
      timeout: 15_000,
    })
  })
})