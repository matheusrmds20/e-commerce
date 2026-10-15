import { test, expect } from '../fixtures/base'

/**
 * 04 — Carrinho: adicionar → badge → quantidade → remover → estado consistente.
 * A sacola só aparece para usuários autenticados, então os testes logam.
 */
test.describe('Carrinho', () => {
  test('adiciona, atualiza badge, altera quantidade e remove', async ({
    page,
    registrarPelaUi,
    emailUnico,
  }) => {
    await page.goto('/')
    // Sacola visível apenas para autenticados.
    await registrarPelaUi({ email: emailUnico('carrinho') })

    // Escolhe um livro no acervo e abre o detalhe.
    await page.goto('/acervo')
    const card = page.getByTestId(/^book-card-/).first()
    await expect(card).toBeVisible({ timeout: 15_000 })
    const titulo = (await card.locator('h3').innerText()).trim()
    await card.locator('img').click()

    // Adiciona à sacola.
    await expect(page.getByTestId('btn-add-carrinho')).toBeVisible({
      timeout: 15_000,
    })
    await page.getByTestId('btn-add-carrinho').click()

    // Badge da navbar reflete 1 exemplar.
    await expect(page.getByTestId('navbar-sacola')).toContainText('1')

    // Vai para o carrinho (navegação client-side pela sacola).
    // `cart-item-{id}` usa o id da LINHA (não o product_id — ver 2º teste),
    // então localizamos pelo prefixo e asseramos pelo título do livro.
    await page.getByTestId('navbar-sacola').click()
    const item = page.getByTestId(/^cart-item-/).first()
    await expect(item).toBeVisible()
    await expect(item).toContainText(titulo)

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

    await page.goto('/acervo')
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
    await page.getByTestId('navbar-sacola').click()

    // Item da API: `cart-item-{id}` usa o id da LINHA (não o product_id),
    // então asseramos pelo título do livro.
    const itemLinha = page.getByTestId(/^cart-item-/)
    await expect(itemLinha.first()).toBeVisible({ timeout: 15_000 })
    await expect(itemLinha.first()).toContainText(titulo)
  })
})