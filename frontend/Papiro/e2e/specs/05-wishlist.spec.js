import { test, expect } from '../fixtures/base'

/**
 * 05 — Wishlist: usuário logado adiciona um livro aos desejos pelo detalhe e
 * consulta em Minha Conta → Lista de desejos.
 */
test.describe('Wishlist', () => {
  test('adiciona pelo detalhe e consulta em Minha Conta', async ({
    page,
    registrarPelaUi,
    emailUnico,
  }) => {
    await page.goto('/')
    await registrarPelaUi({ email: emailUnico('wishlist') })

    // Abre o detalhe do primeiro livro do acervo.
    await page.getByTestId('nav-acervo').click()
    const card = page.getByTestId(/^book-card-/).first()
    await expect(card).toBeVisible({ timeout: 15_000 })
    const titulo = (await card.locator('h3').innerText()).trim()
    await card.locator('img').click()

    // Adiciona aos desejos.
    const btnWishlist = page.getByTestId('btn-wishlist')
    await expect(btnWishlist).toBeVisible({ timeout: 15_000 })
    await btnWishlist.click()
    await expect(btnWishlist).toHaveText(/Remover dos desejos/)

    // Consulta em Minha Conta → aba "Lista de desejos".
    await page.getByTestId('nav-minhaconta').click()
    await page.getByRole('button', { name: 'Lista de desejos' }).first().click()
    await expect(page.locator('body')).toContainText(titulo, {
      timeout: 15_000,
    })
  })
})