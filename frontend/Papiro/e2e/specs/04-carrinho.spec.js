import { test, expect } from '../fixtures/base'
import { idDoCard } from '../helpers/navegar'

/**
 * 04 — Carrinho (visitante, em memória): adicionar → badge → quantidade →
 * remover → estado consistente.
 */
test.describe('Carrinho', () => {
  test('adiciona, atualiza badge, altera quantidade e remove', async ({ page }) => {
    await page.goto('/')

    // Escolhe um livro no acervo e abre o detalhe.
    await page.getByTestId('nav-acervo').click()
    const card = page.getByTestId(/^book-card-/).first()
    await expect(card).toBeVisible({ timeout: 15_000 })
    const id = await idDoCard(card)
    await card.locator('img').click()

    // Adiciona à sacola.
    await expect(page.getByTestId('btn-add-carrinho')).toBeVisible({
      timeout: 15_000,
    })
    await page.getByTestId('btn-add-carrinho').click()

    // Badge da navbar reflete 1 exemplar.
    await expect(page.getByTestId('navbar-sacola')).toContainText('1')

    // Vai para o carrinho.
    await page.getByTestId('nav-carrinho').click()
    const item = page.getByTestId(`cart-item-${id}`)
    await expect(item).toBeVisible()

    // + quantidade → badge 2 e texto de total atualizam.
    await item.getByTestId('btn-qtd-mais').click()
    await expect(page.getByTestId('navbar-sacola')).toContainText('2')
    await expect(page.locator('body')).toContainText('2 exemplares')

    // − quantidade → volta para 1.
    await item.getByTestId('btn-qtd-menos').click()
    await expect(page.getByTestId('navbar-sacola')).toContainText('1')

    // Remove → sacola vazia e badge some.
    await item.getByTestId('btn-remover').click()
    await expect(page.getByText('Sua sacola está vazia.')).toBeVisible()
    await expect(item).toHaveCount(0)
    await expect(
      page.getByTestId('navbar-sacola').locator('span'),
    ).toHaveCount(0)
  })

  test('carrinho de usuário logado persiste no backend após reload', async ({
    page,
    registrarPelaUi,
    emailUnico,
  }) => {
    await page.goto('/')

    // Usuário novo: o primeiro add dispara o handshake "No cart found" →
    // GET /cart/me (erro) → POST /cart/create → add item.
    await registrarPelaUi({ email: emailUnico('carrinho') })

    await page.getByTestId('nav-acervo').click()
    const card = page.getByTestId(/^book-card-/).first()
    await expect(card).toBeVisible({ timeout: 15_000 })
    const titulo = (await card.locator('h3').innerText()).trim()
    await card.locator('img').click()

    await expect(page.getByTestId('btn-add-carrinho')).toBeVisible({
      timeout: 15_000,
    })
    await page.getByTestId('btn-add-carrinho').click()
    await expect(page.getByTestId('navbar-sacola')).toContainText('1')

    // Reload → carrinho recarregado do backend (persistiu via API).
    await page.reload()
    await expect(page.getByTestId('navbar-sacola')).toContainText('1', {
      timeout: 15_000,
    })
    await page.getByTestId('nav-carrinho').click()

    // Item da API: `cart-item-{id}` usa o id da LINHA (não o product_id),
    // então asseramos pelo título do livro.
    const itemLinha = page.getByTestId(/^cart-item-/)
    await expect(itemLinha.first()).toBeVisible({ timeout: 15_000 })
    await expect(itemLinha.first()).toContainText(titulo)
  })
})