import { test, expect } from '../fixtures/base'

/**
 * 07 — Endereço: usuário logado cadastra um endereço pelo modal do checkout e
 * confere na lista (SeletorEndereco) e em Minha Conta → Endereços.
 *
 * O CEP dispararia uma chamada ao ViaCEP — mockamos via `page.route` para
 * manter o E2E offline (e ainda validamos o auto-preenchimento).
 */
test.describe('Endereço', () => {
  test('cadastra pelo modal no checkout e o endereço aparece nas listas', async ({
    page,
    registrarPelaUi,
    emailUnico,
  }) => {
    // Mock do ViaCEP (sem rede externa; simula CEP válido).
    await page.route('https://viacep.com.br/**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          logradouro: 'Rua das Flores',
          bairro: 'Jardim Botânico',
          localidade: 'São Paulo',
          uf: 'SP',
        }),
      }),
    )

    await page.goto('/')
    await registrarPelaUi({ email: emailUnico('endereco') })

    // Item na sacola para um fluxo real de checkout.
    await page.getByTestId('nav-acervo').click()
    const card = page.getByTestId(/^book-card-/).first()
    await expect(card).toBeVisible({ timeout: 15_000 })
    await card.locator('img').click()
    await expect(page.getByTestId('btn-add-carrinho')).toBeVisible({
      timeout: 15_000,
    })
    await page.getByTestId('btn-add-carrinho').click()

    // Vai ao checkout e abre o modal de novo endereço.
    await page.getByTestId('nav-checkout').click()
    await expect(page.getByTestId('btn-novo-endereco')).toBeVisible({
      timeout: 15_000,
    })
    await page.getByTestId('btn-novo-endereco').click()

    // CEP → auto-preenchimento (mock) → complemento → salvar.
    await page.getByLabel('CEP').fill('01153000')
    // Espera o ViaCEP mockado preencher rua/bairro/cidade/UF.
    await expect(page.getByLabel('Logradouro / Rua / Avenida')).toHaveValue(
      'Rua das Flores',
      { timeout: 10_000 },
    )
    await page.getByLabel('Número').fill('100')
    await page.getByLabel('Complemento (Apto, Bloco, etc.)').fill('Apto 12')
    await page
      .getByRole('button', { name: 'Cadastrar endereço', exact: true })
      .click()

    // Modal fecha e o endereço aparece no seletor do checkout.
    await expect(page.locator('body')).toContainText('Rua das Flores', {
      timeout: 15_000,
    })
    await expect(page.locator('body')).toContainText('Jardim Botânico')

    // Listagem em Minha Conta → aba Endereços.
    await page.getByTestId('nav-minhaconta').click()
    await page.getByRole('button', { name: 'Endereços' }).first().click()
    await expect(page.locator('body')).toContainText('Rua das Flores', {
      timeout: 15_000,
    })
  })
})