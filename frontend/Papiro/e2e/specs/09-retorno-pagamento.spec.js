import { test, expect } from '../fixtures/base'

/**
 * 09 — Tela de retorno do Mercado Pago (mockada): navegar para
 * /payment/{resultado} renderiza a tela independentemente de autenticação.
 *
 * Não há pedido real aqui (sem order_id e sem sessionStorage), então a tela
 * fica no tema default ("Aguardando confirmação") e oferece "Voltar para a loja".
 */
test.describe('Retorno de pagamento', () => {
  test('renderiza a tela de retorno sem exigir login', async ({ page }) => {
    await page.goto('/payment/success')

    // Header da tela de retorno (tema default para URL sem dados).
    await expect(
      page.getByRole('heading', { level: 1 }),
    ).toContainText('Aguardando confirmação')

    // Ações disponíveis.
    await expect(
      page.getByRole('button', { name: 'Voltar para a loja' }),
    ).toBeVisible()

    // Selo da tela de retorno (independência de auth: renderiza sem login).
    await expect(page.locator('body')).toContainText(
      'Pagamento processado com segurança pelo Mercado Pago.',
    )
  })
})