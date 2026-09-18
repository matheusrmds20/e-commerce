import { useState } from 'react'
import { ArrowRightIcon } from './Icons'

/**
 * Hero — faixa panorâmica full-bleed (borda a borda).
 *
 * A foto é 16:9; numa faixa larga o `object-cover` precisa cortar, e o corte
 * é ancorado no topo (`object-top`) porque é ali que estão o arco da janela e
 * a árvore de outono — os elementos que sustentam a cena. Em telas estreitas,
 * onde a faixa fica quase na proporção da foto, nada é cortado.
 */
export default function Hero() {
  const [imagemOk, setImagemOk] = useState(true)

  return (
    <section className="bg-cream-deep">
      <div className="relative isolate flex h-[320px] w-full items-center justify-center overflow-hidden sm:h-[420px] lg:h-[500px] xl:h-[540px]">
        {/* Base — também serve de fallback */}
        <div className="absolute inset-0 -z-20 bg-gradient-to-br from-coffee via-coffee-soft to-forest" />

        {imagemOk && (
          <img
            src="/hero-janela.jpg"
            alt="Janela ampla com almofadas, livros e uma xícara ao sol da tarde"
            onError={() => setImagemOk(false)}
            className="absolute inset-0 -z-20 h-full w-full object-cover object-top"
          />
        )}

        {/* Véu leve — garante contraste do texto */}
        <div className="absolute inset-0 -z-10 bg-forest/30" />

        {/* Fade suave do hero para a próxima seção */}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 sm:h-32 lg:h-40 -z-10 bg-gradient-to-b from-transparent via-cream-soft/50 to-cream-soft" />

        {/* Conteúdo */}
        <div className="w-full max-w-[720px] px-6 text-center">
          <p className="label-caps text-cream">Livraria Papiro</p>

          <h1 className="mt-3.5 font-display text-[2.1rem] leading-[1.12] font-normal tracking-[-0.01em] text-cream-soft sm:text-[2.8rem] lg:text-[3.3rem]">
            Descubra seu próximo capítulo
          </h1>

          <p className="mx-auto mt-4 hidden max-w-[34rem] font-body text-[0.98rem] font-normal leading-relaxed text-cream sm:block">
            Uma seleção cuidadosa de livros para quem gosta de ler devagar.
          </p>

          <div className="mt-7 flex flex-col items-center justify-center gap-3.5 sm:flex-row">
            <a
              href="#destaques"
              className="group inline-flex w-full items-center justify-center gap-2.5 rounded-sm bg-gold px-7 py-3.5 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft transition-colors duration-300 ease-[var(--ease-cozy)] hover:bg-caramel focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cream-soft sm:w-auto"
            >
              Explorar a coleção
              <ArrowRightIcon className="h-4 w-4 transition-transform duration-300 ease-[var(--ease-cozy)] group-hover:translate-x-1" />
            </a>

            <a
              href="#"
              className="inline-flex w-full items-center justify-center rounded-sm border border-cream/70 px-7 py-3.5 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft transition-colors duration-300 ease-[var(--ease-cozy)] hover:border-cream hover:bg-cream-soft/15 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cream-soft sm:w-auto"
            >
              Conhecer o clube
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}
