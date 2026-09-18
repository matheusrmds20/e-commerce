import { ArrowRightIcon } from './Icons'

/** Imagens de fallback quando a categoria não tem `image_url` no backend. */
const IMAGENS_FALLBACK = [
  'https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1457369804613-52c61a468e7d?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1518895949257-7621c3c786d7?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80',
]

/** Limite de coleções exibidas para manter a grade equilibrada. */
const LIMITE_COLECOES = 5

/**
 * ProximaLeitura — Seção "Encontre sua próxima leitura".
 *
 * As coleções são as categorias reais do backend (`CategoryResponse`), com a
 * contagem de livros derivada do catálogo (`total`). Categorias sem livros já
 * são filtradas em `carregarHome`, então aqui só cuidamos de imagem fallback e
 * do estado vazio.
 */
export default function ProximaLeitura({ colecoes = [], carregando = false }) {
  const visiveis = colecoes.slice(0, LIMITE_COLECOES)

  return (
    <section id="colecoes" className="bg-cream-soft py-16 sm:py-24">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
        {/* Cabeçalho */}
        <div className="text-center">
          <p className="label-caps text-caramel">Por atmosfera & humor</p>

          <h2 className="mt-3 font-display text-[2.5rem] font-normal leading-tight tracking-[-0.01em] text-forest sm:text-[3.25rem]">
            Encontre sua próxima leitura
          </h2>

          <p className="mx-auto mt-4 max-w-[36rem] font-body text-[0.98rem] font-normal leading-relaxed text-coffee-soft sm:text-[1.05rem]">
            Escolha o sentimento que você deseja cultivar hoje e descubra obras selecionadas para cada estado de espírito.
          </p>
        </div>

        {/* Grade de Coleções */}
        <div className="mt-14 grid gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
          {carregando &&
            Array.from({ length: LIMITE_COLECOES }).map((_, i) => (
              <div
                key={`skeleton-${i}`}
                className="min-h-[380px] animate-pulse rounded-md border border-line bg-line/40 sm:min-h-[420px]"
              />
            ))}

          {!carregando &&
            visiveis.map((col, index) => {
              const imagem =
                col.imagem ||
                IMAGENS_FALLBACK[index % IMAGENS_FALLBACK.length]
              return (
                <a
                  key={col.id}
                  href={`#${col.slug || col.id}`}
                  onClick={(e) => e.preventDefault()}
                  className="group relative flex min-h-[380px] flex-col justify-end overflow-hidden rounded-md border border-line bg-coffee p-6 transition-all duration-500 ease-[var(--ease-cozy)] hover:-translate-y-1 hover:border-gold hover:shadow-xl sm:min-h-[420px]"
                >
                  {/* Foto de fundo */}
                  <img
                    src={imagem}
                    alt={col.titulo}
                    className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 ease-[var(--ease-cozy)] group-hover:scale-110"
                    loading="lazy"
                  />

                  {/* Degradê escuro para legibilidade */}
                  <div className="absolute inset-0 bg-gradient-to-t from-forest/95 via-forest/60 to-forest/20 transition-opacity duration-500 group-hover:opacity-90" />

                  {/* Conteúdo do cartão */}
                  <div className="relative z-10 flex flex-col">
                    <div className="flex items-center justify-between">
                      <span className="rounded-full bg-cream-soft/25 px-3 py-0.5 font-body text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-cream-soft backdrop-blur-sm">
                        Coleção
                      </span>
                      <span className="font-body text-[0.78rem] font-medium text-cream/85">
                        {col.total}{' '}
                        {col.total === 1 ? 'livro' : 'livros'}
                      </span>
                    </div>

                    <h3 className="mt-4 font-display text-[1.95rem] font-medium leading-snug text-cream-soft transition-colors duration-300 group-hover:text-gold">
                      {col.titulo}
                    </h3>

                    {col.subtitulo && (
                      <p className="mt-2 font-body text-[0.82rem] font-normal leading-relaxed text-cream/90">
                        {col.subtitulo}
                      </p>
                    )}

                    <div className="mt-5 inline-flex items-center gap-2 font-body text-[0.75rem] font-semibold uppercase tracking-[0.2em] text-gold transition-all duration-300 group-hover:translate-x-1">
                      <span>Ver coleção</span>
                      <ArrowRightIcon className="h-3.5 w-3.5" />
                    </div>
                  </div>
                </a>
              )
            })}
        </div>

        {/* Estado vazio */}
        {!carregando && visiveis.length === 0 && (
          <div className="mt-14 rounded-md border border-dashed border-line-strong bg-cream-deep/60 px-6 py-16 text-center">
            <p className="font-display text-2xl text-coffee">
              Nenhuma coleção disponível ainda
            </p>
            <p className="mt-2 font-body text-sm text-coffee-soft">
              Nossas coleções por atmosfera aparecem aqui assim que as
              categorias forem cadastradas.
            </p>
          </div>
        )}
      </div>
    </section>
  )
}
