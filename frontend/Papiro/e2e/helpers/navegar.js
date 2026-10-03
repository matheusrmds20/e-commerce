/**
 * Navegação — o front ainda não tem roteador (App.jsx usa estado).
 * A forma confiável de "ir para uma página" é clicar no botão da nav
 * flutuante (testid `nav-{nome}`: home, acervo, detalhe, carrinho, checkout,
 * minhaconta, login, registro, admin).
 */
export async function navegarPara(page, destino) {
  await page.getByTestId(`nav-${destino}`).click()
}

/**
 * Lê o id do produto a partir do testid de um card.
 * `book-card-{id}` -> Number(id)
 */
export async function idDoCard(card) {
  const testid = await card.getAttribute('data-testid')
  const id = Number(testid.replace(/^book-card-/, ''))
  if (!Number.isInteger(id)) throw new Error(`testid inesperado: ${testid}`)
  return id
}