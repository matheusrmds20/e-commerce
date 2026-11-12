/**
 * Imagens de capa — o mínimo que um produto precisa para não pesar nem pular.
 *
 * Toda capa do site é servida grande (as locais têm 1376×768 e ~650 KB cada),
 * mas aparece em caixas de 48 px a 520 px. Sem `srcset` o celular baixa o
 * arquivo do desktop; sem `width`/`height` a grade salta quando a imagem chega
 * (CLS). Os dois problemas se resolvem aqui, num lugar só, em vez de repetir
 * atributos em 12 `<img>`.
 *
 * O ponto que mais pesa na nitidez não é a compressão, é a **geometria**: as
 * capas do acervo são paisagem (1376×768) e quase todo container é retrato
 * (`aspect-[3/4]`). Com `object-cover`, preencher um retrato de 320×427 exige
 * uma imagem de ~764 px de largura — 2.4× a coluna. Declarar `sizes="320px"`
 * nesse caso faz o navegador baixar a variante de 320 e ampliá-la 2.4× (e mais
 * 2× em tela Retina), que é o borrão que aparece na grade.
 *
 * Por isso `larguraExibida` não é "o quanto a imagem ocupa", é a coluna; e
 * `ajuste` diz como a imagem é encaixada nela, para o cálculo do fator.
 *
 * Três origens, porque nem toda imagem aceita parâmetro de largura:
 *  - capa local (`/capas/x.jpg`): existe em -320/-640/-960/-1376 (geradas);
 *  - Unsplash: aceita `w=` na query, então dá para pedir cada largura;
 *  - qualquer outra URL (Supabase, CDN externa): passa intacta, só com a
 *    proporção — inventar `srcset` aí daria 404.
 */

/**
 * Larguras geradas para as capas locais, em `public/capas`.
 * 1376 é o tamanho nativo do acervo e é o teto: pedir mais só ampliaria.
 */
const LARGURAS_LOCAIS = [320, 640, 960, 1376]

/** Proporção das capas do acervo (1376×768). Serve de `width`/`height`. */
export const CAPA_LARGURA = 1376
export const CAPA_ALTURA = 768

const RAZAO_CAPA = CAPA_LARGURA / CAPA_ALTURA

/**
 * Quanto a imagem é ampliada ao ser encaixada na coluna, em relação à largura
 * da coluna. É o número que falta em todo `sizes` ingênuo.
 *
 * @param {'cover-retrato'|'cover-paisagem'|'contain'} ajuste
 * @returns {number}
 */
function fatorAjuste(ajuste) {
  switch (ajuste) {
    // Container retrato (aspect 3/4) + object-cover numa arte paisagem:
    // manda a altura, então a largura útil é altura × razão da arte.
    case 'cover-retrato':
      return (4 / 3) * RAZAO_CAPA
    // Container paisagem + cover: manda a largura, sem ampliação lateral.
    case 'cover-paisagem':
      return 1
    // contain: a imagem inteira cabe, nunca amplia por corte.
    case 'contain':
    default:
      return 1
  }
}

/** Monta um `srcset` trocando a largura na URL do Unsplash. */
function srcsetUnsplash(url) {
  try {
    const base = new URL(url)
    // Só o Unsplash aceita `w=` como redimensionamento. Qualquer outra CDN
    // (Supabase, S3) devolveria 404 em `?w=320`, então não entra aqui.
    if (base.hostname !== 'images.unsplash.com') return undefined
    return LARGURAS_LOCAIS.map((w) => {
      const alvo = new URL(base)
      alvo.searchParams.set('w', String(w))
      return `${alvo.toString()} ${w}w`
    }).join(', ')
  } catch {
    return undefined
  }
}

/** Monta um `srcset` a partir dos arquivos `-320/-640/-960/-1376`. */
function srcsetLocal(url) {
  const casou = /^(.*\/capas\/.+?)(\.(?:jpe?g|png|webp))$/i.exec(url)
  if (!casou) return undefined
  const [, raiz, extensao] = casou
  return LARGURAS_LOCAIS.map((w) => `${raiz}-${w}${extensao} ${w}w`).join(', ')
}

/**
 * Atributos de imagem responsiva para uma capa.
 *
 * @param {string|undefined|null} url  URL da capa vinda da API
 * @param {object} [opcoes]
 * @param {number} [opcoes.larguraExibida] largura da coluna (px CSS) onde a capa é desenhada
 * @param {'cover-retrato'|'cover-paisagem'|'contain'} [opcoes.ajuste] como a imagem é encaixada
 * @param {boolean} [opcoes.prioridade] capa acima da dobra (sem lazy, alta prioridade)
 * @returns {object} atributos prontos para espalhar em `<img {...}>`
 */
export function atributosCapa(
  url,
  { larguraExibida = 320, ajuste = 'contain', prioridade = false } = {},
) {
  if (!url) return {}

  const srcset = srcsetLocal(url) ?? srcsetUnsplash(url)

  // Largura em px CSS que a imagem precisa ocupar para não ser esticada.
  // O navegador multiplica pelo DPR ao escolher dentro do `srcset`.
  const larguraEfetiva = Math.round(larguraExibida * fatorAjuste(ajuste))

  return {
    width: CAPA_LARGURA,
    height: CAPA_ALTURA,
    // `decoding=async` tira a decodificação do caminho crítico da rolagem.
    decoding: 'async',
    srcSet: srcset,
    // Sem `sizes` o navegador assume `100vw`; com o valor certo ele baixa a
    // menor variante que ainda cobre a área — nem borrada, nem desperdiçada.
    sizes: srcset ? `${larguraEfetiva}px` : undefined,
    loading: prioridade ? 'eager' : 'lazy',
    fetchPriority: prioridade ? 'high' : undefined,
  }
}
