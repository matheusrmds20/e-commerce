import Migalhas from '../components/Migalhas'
import Quill from '../components/Quill'

/**
 * SobreNos — Página editorial com a história, manifesto e propósito da Papiro.
 *
 * Filosofia: "Conforto alinhado à personalidade".
 */
export default function SobreNos({ onExplorarAcervo, onVoltarHome }) {
  const pilares = [
    {
      numero: '01',
      titulo: 'Conforto que Acolhe',
      subtitulo: 'A leitura como refúgio diário.',
      descricao:
        'Acreditamos que abrir um livro deve ser uma pausa restauradora no ritmo acelerado do cotidiano. Cada detalhe da nossa livraria — da tipografia das edições ao papel kraft dos nossos pacotes — é pensado para proporcionar calma, aconchego e bem-estar.',
    },
    {
      numero: '02',
      titulo: 'Personalidade & Identidade',
      subtitulo: 'Estantes que contam quem você é.',
      descricao:
        'Rejeitamos listas genéricas e recomendações puramente algorítmicas. Cultivamos uma curadoria humana com clássicos atemporais, vozes singulares e ensaios profundos para que a sua biblioteca particular seja um espelho genuíno da sua essência.',
    },
    {
      numero: '03',
      titulo: 'O Ritual do Tempo Lento',
      subtitulo: 'Páginas que merecem atenção plena.',
      descricao:
        'Num mundo de estímulos rápidos e efêmeros, defendemos a desaceleração. Livros para dias lentos, lidos sem pressa, acompanhados de uma xícara quente e da certeza de que o tempo dedicado à leitura é um tempo reconquistado.',
    },
  ]

  return (
    <main className="bg-cream-deep">
      {/* Cabeçalho Editorial */}
      <section className="border-b border-line bg-cream-soft">
        <div className="mx-auto max-w-[1400px] px-5 py-10 sm:px-8 sm:py-14">
          <Migalhas
            itens={[
              { rotulo: 'Início', onClick: onVoltarHome },
              { rotulo: 'Sobre Nós' },
            ]}
          />

          <p className="label-caps mt-6 text-caramel">Nossa Filosofia & Origem</p>
          <h1 className="mt-3 font-display text-[2.5rem] font-normal leading-tight tracking-[-0.01em] text-forest sm:text-[3.5rem]">
            Conforto alinhado à personalidade.
          </h1>
          <p className="mt-3 max-w-[42rem] font-body text-[0.98rem] font-normal leading-relaxed text-coffee-soft sm:text-[1.1rem]">
            A Papiro nasceu do desejo de criar um refúgio para leitores que buscam
            mais do que comprar livros: buscam momentos de tranquilidade, estética
            cuidada e obras com alma.
          </p>
        </div>
      </section>

      {/* Seção Manifesto */}
      <section className="mx-auto max-w-[1400px] px-5 py-14 sm:px-8 sm:py-20">
        <div className="grid gap-12 lg:grid-cols-12 lg:items-center">
          <div className="lg:col-span-7">
            <span className="label-caps text-gold">O Manifesto Papiro</span>
            <h2 className="mt-3 font-display text-[2rem] leading-snug text-coffee sm:text-[2.6rem]">
              Uma livraria feita à mão, para mentes que apreciam a pausa.
            </h2>
            <div className="mt-6 space-y-4 font-body text-[0.95rem] font-light leading-relaxed text-coffee-soft">
              <p>
                Vivemos em uma época que exige velocidade constante. Na contramão
                da pressa, a Papiro propõe uma volta ao essencial: o prazer tátil do
                livro impresso, o silêncio da tarde, a prosa bem talhada e a poesia
                que reverbera devagar.
              </p>
              <p>
                Para nós, cada leitor possui uma assinatura única. Por isso,
                nossa seleção reúne desde a literatura brasileira e clássicos
                universais até a não-ficção humanista e versos delicados. Cada
                título é escolhido com critério rigoroso para somar beleza e
                profundidade à sua rotina.
              </p>
            </div>

            <div className="mt-8 border-l-2 border-gold pl-5 py-1">
              <p className="font-display text-lg italic text-forest sm:text-xl">
                “Ler é inventar um lugar calmo no meio do mundo.”
              </p>
              <p className="mt-1 font-body text-xs uppercase tracking-widest text-coffee-faint">
                — Filosofia Editorial Papiro
              </p>
            </div>
          </div>

          <div className="lg:col-span-5 flex justify-center">
            <div className="relative w-full max-w-md rounded-lg border border-line bg-cream-soft p-8 sm:p-10 shadow-sm text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-forest text-gold shadow-md">
                <Quill width={32} />
              </div>
              <h3 className="mt-6 font-display text-2xl text-forest">
                Livraria Papiro
              </h3>
              <p className="mt-1 font-body text-xs uppercase tracking-[0.2em] text-caramel">
                Fundada para Dias Lentos
              </p>
              <p className="mt-4 font-body text-sm font-light leading-relaxed text-coffee-soft">
                Curadoria independente, respeito ao tempo de cada obra e carinho
                artesanal em cada entrega realizada.
              </p>
              <div className="mt-6 grid grid-cols-2 gap-4 border-t border-line/60 pt-5 text-center">
                <div>
                  <p className="font-display text-2xl font-medium text-coffee">100%</p>
                  <p className="text-[0.7rem] uppercase tracking-wider text-coffee-faint">
                    Humana & Independente
                  </p>
                </div>
                <div>
                  <p className="font-display text-2xl font-medium text-coffee">Zero</p>
                  <p className="text-[0.7rem] uppercase tracking-wider text-coffee-faint">
                    Pressa ou Algoritmos
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Pilares da Marca */}
        <div className="mt-20">
          <div className="text-center">
            <span className="label-caps text-gold">Nossos Princípios</span>
            <h2 className="mt-2 font-display text-[2rem] text-forest sm:text-[2.5rem]">
              O que nos move a cada página
            </h2>
          </div>

          <div className="mt-12 grid gap-8 md:grid-cols-3">
            {pilares.map((pilar) => (
              <div
                key={pilar.numero}
                className="relative rounded-sm border border-line bg-cream-soft p-8 transition-all duration-300 hover:-translate-y-1 hover:border-gold/60 hover:shadow-md"
              >
                <span className="font-display text-5xl font-light text-coffee/10">
                  {pilar.numero}
                </span>
                <h3 className="mt-3 font-display text-xl text-coffee">
                  {pilar.titulo}
                </h3>
                <p className="mt-1 font-body text-xs font-semibold uppercase tracking-wider text-caramel">
                  {pilar.subtitulo}
                </p>
                <p className="mt-4 font-body text-sm font-light leading-relaxed text-coffee-soft">
                  {pilar.descricao}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Banner CTA */}
        {onExplorarAcervo && (
          <div className="mt-20 rounded-sm border border-line bg-forest p-8 text-center text-cream-soft sm:p-14">
            <h2 className="font-display text-2xl text-cream sm:text-3xl">
              Pronto para encontrar sua próxima leitura?
            </h2>
            <p className="mx-auto mt-3 max-w-xl font-body text-sm font-light text-cream/80 sm:text-base">
              Explore nossos livros selecionados a dedo e monte uma biblioteca
              que reflita verdadeiramente o seu aconchego e personalidade.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-4">
              <button
                type="button"
                onClick={onExplorarAcervo}
                className="rounded-sm bg-gold px-8 py-3.5 font-body text-xs font-semibold uppercase tracking-[0.2em] text-forest transition-colors duration-300 hover:bg-gold-light shadow-sm"
              >
                Explorar o Acervo
              </button>
            </div>
          </div>
        )}
      </section>
    </main>
  )
}
