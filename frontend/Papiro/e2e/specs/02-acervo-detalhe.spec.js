import { test, expect } from '../fixtures/base'
import { idDoCard } from '../helpers/navegar'

/**
 * 02 — Acervo → clique no card → detalhe do livro com título e preço.
 * Navegação por cliques na nav (não há roteador no front).
 */
test.describe('Acervo → Detalhe', () => {
  test('abre o detalhe do livro clicado com título e preço', async ({ page }) => {
    await page.goto('/')
    await page.getByTestId('nav-acervo').click()

    // Primeiro card do catálogo (dados da API de teste).
    const card = page.getByTestId(/^book-card-/).first()
    await expect(card).toBeVisible({ timeout: 15_000 })

    const id = await idDoCard(card)
    const titulo = (await card.locator('h3').innerText()).trim()
    const preco = (await card.getByText(/R\$/).first().innerText()).trim()

    // Abre o detalhe (o clique na capa dispara onAbrir(id)).
    await card.locator('img').click()

    // Detalhe renderizado: título como H1 + painel de compra com preço.
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(titulo, {
      timeout: 15_000,
    })
    await expect(page.getByTestId('btn-add-carrinho')).toBeVisible()
    await expect(page.locator('body')).toContainText(preco)
    expect(id).toBeGreaterThan(0)
  })
})