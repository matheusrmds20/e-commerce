import { test, expect } from '../fixtures/base'
import {
  criarEnderecoViaApi,
  criarPedidoViaApi,
  fazerLoginViaApi,
  primeiroProdutoViaApi,
} from '../helpers/setup'

/**
 * 06 — Review: usuário que comprou cria e edita uma avaliação.
 *
 * O form de review só aparece quando `comprou` (pedido não cancelado) — por
 * isso o setup cria endereço + pedido via API (a UI exige todo o checkout
 * para chegar lá; o fluxo completo de compra já é coberto no 08).
 */
test.describe('Review', () => {
  test('cria e edita a avaliação do usuário logado', async ({
    page,
    request,
    registrarPelaUi,
    emailUnico,
  }) => {
    await page.goto('/')
    const dados = await registrarPelaUi({ email: emailUnico('review') })

    // Setup via API: libera o form de review (usuário "comprou" o livro).
    // O token agora vem de um login via API (a memória do front não é legível).
    const token = await fazerLoginViaApi(request, {
      email: dados.email,
      password: dados.password,
    })
    const endereco = await criarEnderecoViaApi(request, token)
    const productId = await primeiroProdutoViaApi(request)
    await criarPedidoViaApi(request, token, {
      address_id: endereco.id,
      items: [{ product_id: productId, quantity: 1 }],
    })

    // Abre o detalhe do produto.
    await page.getByTestId('nav-acervo').click()
    const card = page.getByTestId(`book-card-${productId}`)
    await expect(card).toBeVisible({ timeout: 15_000 })
    await card.locator('img').click()

    // Seção retrátil "Avaliações" (fecha por padrão a descrição).
    // O `carregar()` da página desmonta/remonta o DetalhesLivro após publicar,
    // resetando a seção para fechada — por isso abrimos condicionalmente aqui e
    // de novo antes de editar.
    const abrirSecaoAvaliacoes = async () => {
      const botaoSecao = page.getByRole('button', { name: /Avaliações/ }).first()
      if ((await botaoSecao.getAttribute('aria-expanded')) !== 'true') {
        await botaoSecao.click()
      }
    }
    await abrirSecaoAvaliacoes()

    // Cria a avaliação (nota 4 + comentário).
    await page.getByRole('button', { name: '4 estrelas' }).click()
    await page
      .getByPlaceholder('Conte o que você achou da leitura…')
      .fill('Leitura excelente e envolvente!')
    await page.getByTestId('btn-criar-review').click()

    await expect(page.locator('body')).toContainText('Avaliação publicada.', {
      timeout: 15_000,
    })
    await expect(page.locator('body')).toContainText(
      'Leitura excelente e envolvente!',
    )

    // Edita (a seção voltou a fechar após o remount — reabre).
    await abrirSecaoAvaliacoes()
    await page.getByRole('button', { name: 'Editar' }).click()
    await page.getByRole('button', { name: '3 estrelas' }).click()
    await page
      .locator('textarea')
      .last()
      .fill('Atualizei minha opinião — ficou ainda melhor!')
    await page.getByRole('button', { name: 'Salvar' }).click()

    await expect(page.locator('body')).toContainText('Avaliação atualizada.', {
      timeout: 15_000,
    })
    await expect(page.locator('body')).toContainText(
      'Atualizei minha opinião — ficou ainda melhor!',
    )
  })
})