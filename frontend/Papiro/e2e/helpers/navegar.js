

/** Mapeia o destino (nome legado da antiga nav) para a rota. */
const ROTA_DO_DESTINO = {
  home: '/',
  acervo: '/acervo',
  detalhe: '/livro',
  'mais-vendidos': '/mais-vendidos',
  sobre: '/sobre',
  carrinho: '/carrinho',
  checkout: '/checkout',
  minhaconta: '/minhaconta',
  login: '/login',
  registro: '/registro',
  admin: '/admin',
}


export async function navegarPara(page, destino) {
  await page.goto(ROTA_DO_DESTINO[destino] ?? '/')
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