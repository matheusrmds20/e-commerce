import { ArrowLeftIcon, ArrowRightIcon } from './Icons'

/**
 * Paginacao — controle de páginas do acervo.
 *
 * Recebe os metadados do envelope `PageMeta` do backend
 * (`page`, `per_page`, `total`, `total_pages`) e emite a página escolhida.
 *
 * Por que a lista de páginas é calculada aqui e não pedida ao backend: o
 * envelope já traz `total_pages`, então a navegação inteira é derivada de uma
 * única resposta — sem chamada extra de contagem.
 *
 * A janela de páginas é deslizante (até 5 números) com elipses nas pontas,
 * para o controle não estourar a largura quando o catálogo crescer.
 */

/** Quantos números de página mostrar na janela, no máximo. */
const TAMANHO_JANELA = 5

/**
 * Monta a janela de páginas: 1 … [4 5 6 7 8] … 20
 * @param {number} atual
 * @param {number} total
 * @returns {Array<number|'…'>}
 */
function janelaDePaginas(atual, total) {
  if (total <= TAMANHO_JANELA + 2) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  const metade = Math.floor(TAMANHO_JANELA / 2)
  let inicio = Math.max(2, atual - metade)
  let fim = Math.min(total - 1, atual + metade)

  // Encosta na borda quando a página atual está perto do começo ou do fim.
  if (atual - metade <= 2) fim = TAMANHO_JANELA + 1
  if (atual + metade >= total - 1) inicio = total - TAMANHO_JANELA

  const paginas = [1]
  if (inicio > 2) paginas.push('…')
  for (let i = inicio; i <= fim; i += 1) paginas.push(i)
  if (fim < total - 1) paginas.push('…')
  paginas.push(total)

  return paginas
}

export default function Paginacao({
  page = 1,
  totalPages = 1,
  onChange,
  carregando = false,
}) {
  if (totalPages <= 1) return null

  const paginas = janelaDePaginas(page, totalPages)
  const podeVoltar = page > 1 && !carregando
  const podeAvancar = page < totalPages && !carregando

  const irPara = (destino) => {
    if (carregando || destino < 1 || destino > totalPages || destino === page)
      return
    onChange?.(destino)
  }

  const baseBotao =
    'grid h-10 min-w-10 place-items-center rounded-sm border px-2 font-body text-[0.8rem] font-semibold transition-all duration-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest'

  return (
    <nav
      aria-label="Paginação do acervo"
      className="mt-14 flex flex-wrap items-center justify-center gap-2"
    >
      <button
        type="button"
        onClick={() => irPara(page - 1)}
        disabled={!podeVoltar}
        aria-label="Página anterior"
        className={`${baseBotao} ${
          podeVoltar
            ? 'border-line-strong bg-cream-soft text-coffee hover:border-forest hover:text-forest'
            : 'cursor-not-allowed border-line/60 bg-cream-soft/40 text-coffee-faint/40'
        }`}
      >
        <ArrowLeftIcon className="h-4 w-4" />
      </button>

      {paginas.map((item, i) =>
        item === '…' ? (
          <span
            key={`gap-${i}`}
            aria-hidden="true"
            className="grid h-10 min-w-10 place-items-center font-body text-sm text-coffee-faint"
          >
            …
          </span>
        ) : (
          <button
            key={item}
            type="button"
            onClick={() => irPara(item)}
            disabled={carregando}
            aria-label={`Página ${item}`}
            aria-current={item === page ? 'page' : undefined}
            className={`${baseBotao} ${
              item === page
                ? 'border-forest bg-forest text-cream-soft shadow-sm'
                : 'border-line-strong bg-cream-soft text-coffee-soft hover:border-forest hover:text-forest'
            } ${carregando ? 'cursor-not-allowed opacity-60' : ''}`}
          >
            {item}
          </button>
        ),
      )}

      <button
        type="button"
        onClick={() => irPara(page + 1)}
        disabled={!podeAvancar}
        aria-label="Próxima página"
        className={`${baseBotao} ${
          podeAvancar
            ? 'border-line-strong bg-cream-soft text-coffee hover:border-forest hover:text-forest'
            : 'cursor-not-allowed border-line/60 bg-cream-soft/40 text-coffee-faint/40'
        }`}
      >
        <ArrowRightIcon className="h-4 w-4" />
      </button>
    </nav>
  )
}
