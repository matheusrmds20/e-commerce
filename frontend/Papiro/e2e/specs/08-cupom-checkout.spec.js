import { test, expect } from '../fixtures/base'
import { criarEnderecoViaApi, fazerLoginViaApi } from '../helpers/setup'

/**
 * 08 — Cupom / Checkout com Mercado Pago MOCKADO.
 *
 * O backend cria a preferência via SDK do MP (gateway) — para o E2E NUNCA
 * tocar o MP real, interceptamos no navegador:
 * 1. `POST /api/v1/payments/checkout/{id}` → resposta mockada (o backend
 *    nem chega a chamar o SDK).
 * 2. `https://sandbox.mercadopago.com.br/**` → HTML mockado (o redirect
 *    `window.location.href` nunca abre o site do MP).
 *
 * O pedido em si é criado de verdade (`POST /orders/create` real).
 */
test.describe('Cupom / Checkout (MP mockado)', () => {
  test('cria o pedido e é redirecionado para o checkout do MP mockado', async ({
    page,
    request,
    registrarPelaUi,
    emailUnico,
  }) => {
    // 1) Mock do checkout do backend (o SDK do MP nunca é chamado).
    await page.route('**/api/v1/payments/checkout/**', (route) =>
      route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 9001,
          payment_id: 9001,
          checkout_url: 'https://sandbox.mercadopago.com.br/checkout?ex=1',
        }),
      }),
    )
    // 2) Mock do site do MP (redirect da preferência).
    await page.route('https://sandbox.mercadopago.com.br/**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: '<html><body>MP SANDBOX MOCKADO — nenhuma chamada real</body></html>',
      }),
    )

    await page.goto('/')
    const dados = await registrarPelaUi({ email: emailUnico('checkout') })

    // Endereço via API (o cadastro pelo modal é coberto no 07).
    // O token vem de um login via API (memória do front não é legível).
    const token = await fazerLoginViaApi(request, {
      email: dados.email,
      password: dados.password,
    })
    await criarEnderecoViaApi(request, token)

    // Item na sacola pela UI.
    await page.getByTestId('nav-acervo').click()
    const card = page.getByTestId(/^book-card-/).first()
    await expect(card).toBeVisible({ timeout: 15_000 })
    await card.locator('img').click()
    await expect(page.getByTestId('btn-add-carrinho')).toBeVisible({
      timeout: 15_000,
    })
    await page.getByTestId('btn-add-carrinho').click()

    // Checkout: endereço do setup aparece e é selecionado.
    await page.getByTestId('nav-checkout').click()
    await expect(page.getByLabel(/Rua do Teste E2E/)).toBeVisible({
      timeout: 15_000,
    })
    await page.getByLabel(/Rua do Teste E2E/).check()

    // Seção de cupons renderiza (usuário novo não tem cupom — estado vazio).
    await expect(page.getByText(/Nenhum cupom disponível/)).toBeVisible({
      timeout: 15_000,
    })

    // Finaliza: pedido real + checkout do MP mockado. Captura o id do pedido
    // pela resposta do POST /orders/create (o sessionStorage fica na origem
    // 5173, inacessível depois do redirect para o sandbox do MP).
    let orderId = null
    page.on('response', async (resp) => {
      if (resp.url().includes('/api/v1/orders/create') && resp.ok()) {
        const corpo = await resp.json()
        orderId = corpo.id
      }
    })
    await page.getByTestId('btn-finalizar').click()

    // Redirecionado para a URL do MP, mas com o conteúdo MOCKADO.
    await expect(page).toHaveURL(/sandbox\.mercadopago\.com\.br/, {
      timeout: 15_000,
    })
    await expect(page.locator('body')).toContainText('MP SANDBOX MOCKADO')

    // Pedido criado de verdade (via resposta real do backend).
    expect(orderId).toBeGreaterThan(0)
  })
})