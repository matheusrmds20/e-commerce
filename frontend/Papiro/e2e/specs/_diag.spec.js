import { test, expect } from '../fixtures/base'

test.describe.configure({ mode: 'serial' })

test('diag cart-diag', async ({ page, registrarPelaUi, emailUnico }) => {
  page.on('console', (m) => {
    const t = m.text()
    if (t.includes('[CART-DIAG]')) console.log('[BROWSER] ' + t)
  })
  await page.goto('/')
  await registrarPelaUi({ email: emailUnico('d') })
  await page.goto('/acervo')
  const card = page.getByTestId(/^book-card-/).first()
  await expect(card).toBeVisible({ timeout: 15_000 })
  await card.locator('img').click()
  await expect(page.getByTestId('btn-add-carrinho')).toBeVisible({ timeout: 15_000 })
  await page.getByTestId('btn-add-carrinho').click()
  await page.waitForTimeout(1500)
  const badge = await page.getByTestId('navbar-sacola').innerText().catch(() => '<err>')
  console.log('[DIAG] BADGE = "' + badge + '"')
})