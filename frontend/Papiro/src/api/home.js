import productService from './products'
import categoryService from './categories'
import reviewService from './reviews'
import { toApiError } from './client'
import { mediaAvaliacoes } from './adapters'


const DESCONTO_MINIMO = 1


const LIMITE_DESTAQUES = 8


export function produtoParaCard(p) {
  const temDesconto = Number(p.discount_pct ?? 0) > 0
  return {
    id: p.id,
    titulo: p.title ?? '',
    autor: p.author ?? '',
    categoriaId: p.category_id,
    preco: p.price ?? 0,
    precoOriginal: temDesconto ? p.price : null,
    precoFinal: temDesconto
      ? Number(((p.price ?? 0) * (1 - p.discount_pct / 100)).toFixed(2))
      : (p.price ?? 0),
    desconto: temDesconto ? `${p.discount_pct}%` : null,
    descricao: p.description ?? '',
    sinopse: p.synopsis ?? null,
    imagem: p.image_url ?? '',
    estoque: p.stock_qty ?? 0,
    ativo: p.is_active ?? true,
    // Flags de curadoria — usadas para rotular os cards e priorizar a
    // recomendação da casa (um destaque é melhor vitrine que um item comum).
    destaque: p.is_featured ?? false,
    maisVendido: p.is_bestseller ?? false,
    criadoEm: p.created_at ?? null,
  }
}


export function categoriaParaColecao(c) {
  return {
    id: c.id,
    titulo: c.name ?? '',
    slug: c.slug ?? '',
    subtitulo: c.description ?? '',
    imagem: c.image_url ?? '',
  }
}


export async function carregarHome() {
  const [
    catalogoResp,
    destaquesResp,
    maisVendidosResp,
    ofertasResp,
    categoriasResp,
  ] = await Promise.allSettled([
    productService.listarPorAtivo(true),
    productService.listarDestaques(LIMITE_DESTAQUES),
    productService.listarMaisVendidos(LIMITE_DESTAQUES),
    productService.listarPorDesconto(DESCONTO_MINIMO),
    categoryService.listar(),
  ])


  if (catalogoResp.status === 'rejected') {
    throw toApiError(catalogoResp.reason)
  }

  const catalogo = (catalogoResp.value ?? []).map(produtoParaCard)


  const destaquesCuradoria =
    destaquesResp.status === 'fulfilled' && destaquesResp.value?.length
      ? destaquesResp.value.map(produtoParaCard)
      : null

  const destaques =
    destaquesCuradoria ?? catalogo.slice(0, LIMITE_DESTAQUES)


  const maisVendidos =
    maisVendidosResp.status === 'fulfilled'
      ? (maisVendidosResp.value ?? []).map(produtoParaCard)
      : []


  const idsMaisVendidos = new Set(maisVendidos.map((p) => p.id))
  const destaquesOrdenados = [...destaques].sort((a, b) => {
    const aTop = idsMaisVendidos.has(a.id) ? 0 : 1
    const bTop = idsMaisVendidos.has(b.id) ? 0 : 1
    return aTop - bTop
  })


  const ofertasBrutas =
    ofertasResp.status === 'fulfilled' && ofertasResp.value?.length
      ? ofertasResp.value
      : catalogo.filter((p) => p.desconto)

  const ofertas = ofertasBrutas.map(produtoParaCard)


  const contagemPorCategoria = catalogo.reduce((acc, p) => {
    acc[p.categoriaId] = (acc[p.categoriaId] ?? 0) + 1
    return acc
  }, {})

  const categorias =
    categoriasResp.status === 'fulfilled'
      ? (categoriasResp.value ?? [])
          .map((c) => ({
            ...categoriaParaColecao(c),
            total: contagemPorCategoria[c.id] ?? 0,
          }))
          .filter(
            (c) =>
              c.total > 0 &&
              c.titulo.trim().toLocaleLowerCase('pt-BR') !== 'frete teste',
          )
      : []


  const recomendacao = await montarRecomendacao(destaques, catalogo)

  return {
    catalogo,
    destaques: destaquesOrdenados,
    maisVendidos,
    ofertas,
    categorias,
    recomendacao,
  }
}


async function montarRecomendacao(destaques, catalogo) {

  const vistos = new Set()
  const candidatos = [...destaques, ...catalogo].filter((p) => {
    if (vistos.has(p.id)) return false
    vistos.add(p.id)
    return true
  })

  const produto =
    candidatos.find((p) => p.destaque && p.estoque > 0) ??
    candidatos.find((p) => p.destaque) ??
    candidatos.find((p) => p.estoque > 0) ??
    candidatos[0] ??
    null
  if (!produto) return null

  let avaliacoes
  try {
    avaliacoes = (await reviewService.listarPorProduto(produto.id)) ?? []
  } catch {
    avaliacoes = []
  }

  return {
    produto,
    avaliacoes,
    notaMedia: mediaAvaliacoes(avaliacoes),
  }
}

export default { carregarHome, produtoParaCard, categoriaParaColecao }
