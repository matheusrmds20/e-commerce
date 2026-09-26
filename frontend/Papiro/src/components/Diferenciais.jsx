import Quill from './Quill'

/**
 * Diferenciais — Seção com forte peso visual, profundidade, cartões estruturados e estatísticas de confiança.
 */
export default function Diferenciais() {
  const diferenciais = [
    {
      numero: '01',
      titulo: 'Envio Artesanal & Seguro',
      subtitulo: 'Cada pacote é uma experiência de abertura.',
      descricao:
        'Não enviamos apenas livros; entregamos um momento. Cada exemplar é inspecionado, embalado à mão em papel kraft e protegido com cuidado impecável.',
      itens: [
        'Embrulho especial em papel kraft',
        'Marcador de página artesanal em linho',
        'Zero plástico descartável',
      ],
      destaque: 'Feito à Mão',
    },
    {
      numero: '02',
      titulo: 'Curadoria 100% Humana',
      subtitulo: 'Lido, debatido e aprovado antes de ir para a estante.',
      descricao:
        'Rejeitamos algoritmos genéricos de recomendação. Nossos livreiros leem e analisam cada título para garantir obras que verdadeiramente transformam a mente.',
      itens: [
        'Seleção independente de editoras',
        'Resenhas críticas exclusivas',
        'Edições raras e traduções consagradas',
      ],
      destaque: 'Sem Algoritmos',
    },
    {
      numero: '03',
      titulo: 'Clube & Comunidade',
      subtitulo: 'Uma jornada literária compartilhada a cada mês.',
      descricao:
        'Faça parte de uma comunidade que valoriza o tempo lento. Receba um livro surpresa todo mês, com cartas do curador e encontros virtuais ao vivo.',
      itens: [
        'Carta mensal do livreiro convidado',
        'Encontros virtuais com autores',
        'Brindes literários colecionáveis',
      ],
      destaque: 'Comunidade Viva',
    },
  ]

  const estatisticas = [
    { valor: '+18.000', rotulo: 'Livros entregues com afeto' },
    { valor: '100%', rotulo: 'Curadoria independente' },
    { valor: '4.9 ★', rotulo: 'Avaliação dos leitores' },
    { valor: '100%', rotulo: 'Embalagens sustentáveis' },
  ]

  return (
    <section
      id="diferenciais"
      className="relative isolate overflow-hidden bg-gradient-to-b from-[#012618] via-forest to-[#011e13] py-20 text-cream-soft sm:py-28"
    >
      {/* Elementos decorativos de fundo */}
      <div className="pointer-events-none absolute -left-20 -top-20 opacity-5">
        <Quill width={420} />
      </div>
      <div className="pointer-events-none absolute -bottom-24 -right-16 opacity-5">
        <Quill width={420} />
      </div>

      <div className="mx-auto max-w-[1400px] px-5 sm:px-8">
        {/* Cabeçalho */}
        <div className="text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-gold/30 bg-gold/10 px-4 py-1 text-gold">
            <span className="font-body text-[0.68rem] font-medium uppercase tracking-[0.25em]">
              O Padrão Papiro
            </span>
          </div>

          <h2 className="mt-4 font-display text-[2.4rem] font-light leading-tight tracking-[-0.01em] text-cream sm:text-[3.25rem]">
            Por que escolher a nossa livraria?
          </h2>

          <p className="mx-auto mt-4 max-w-[36rem] font-body text-sm font-light leading-relaxed text-cream/80 sm:text-base">
            Cultivamos a arte da boa leitura. Do primeiro clique até o abrir da caixa, tudo é pensado para desacelerar o seu dia.
          </p>
        </div>

        {/* Grade de Cartões de Diferenciais */}
        <div className="mt-16 grid gap-8 md:grid-cols-3">
          {diferenciais.map((item) => (
            <article
              key={item.numero}
              className="group relative flex flex-col justify-between rounded-md border border-cream/15 bg-forest-soft/60 p-8 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.5)] backdrop-blur-sm transition-all duration-500 ease-[var(--ease-cozy)] hover:-translate-y-2 hover:border-gold/60 hover:bg-forest-soft/90 hover:shadow-2xl"
            >
              {/* Marca d'água numérica de fundo */}
              <span className="pointer-events-none absolute right-6 top-4 select-none font-display text-7xl font-bold text-cream/[0.04] transition-colors duration-500 group-hover:text-gold/[0.1]">
                {item.numero}
              </span>

              <div>
                {/* Topo do Card */}
                <div className="flex items-center justify-between">
                  <span className="rounded-sm bg-gold/20 px-2.5 py-1 font-body text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-gold">
                    {item.destaque}
                  </span>
                  <span className="font-display text-sm italic text-cream/50">
                    Pilar {item.numero}
                  </span>
                </div>

                {/* Título & Subtítulo */}
                <h3 className="mt-6 font-display text-[1.65rem] font-normal leading-snug text-cream transition-colors duration-300 group-hover:text-gold">
                  {item.titulo}
                </h3>
                <p className="mt-1 font-body text-xs font-medium text-caramel">
                  {item.subtitulo}
                </p>

                {/* Descrição */}
                <p className="mt-4 font-body text-sm font-light leading-relaxed text-cream/75">
                  {item.descricao}
                </p>
              </div>

              {/* Lista de Benefícios */}
              <div className="mt-8 border-t border-cream/10 pt-5">
                <ul className="space-y-2.5">
                  {item.itens.map((subItem) => (
                    <li
                      key={subItem}
                      className="flex items-center gap-2.5 font-body text-xs font-light text-cream/90"
                    >
                      <span className="grid h-4 w-4 shrink-0 place-items-center rounded-full bg-gold/20 text-gold text-[0.65rem]">
                        ✓
                      </span>
                      <span>{subItem}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </article>
          ))}
        </div>

        {/* Faixa de Estatísticas e Confiança */}
        <div className="mt-16 rounded-md border border-cream/15 bg-cream-soft/5 p-6 sm:p-8 backdrop-blur-sm">
          <div className="grid grid-cols-2 gap-6 sm:grid-cols-4 sm:gap-8 text-center divide-y sm:divide-y-0 sm:divide-x divide-cream/10">
            {estatisticas.map((stat, idx) => (
              <div key={stat.rotulo} className={idx > 0 ? 'pt-4 sm:pt-0' : ''}>
                <p className="font-display text-3xl font-medium tracking-tight text-gold sm:text-4xl">
                  {stat.valor}
                </p>
                <p className="mt-1 font-body text-xs font-light uppercase tracking-[0.16em] text-cream/70">
                  {stat.rotulo}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
