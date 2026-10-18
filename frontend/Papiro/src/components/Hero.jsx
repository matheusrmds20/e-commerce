import { ArrowRightIcon } from './Icons'


export default function Hero() {
  return (
    <section className="bg-cream-deep">
      <div className="mx-auto grid max-w-[1400px] items-center gap-10 px-5 py-12 sm:px-8 sm:py-16 lg:grid-cols-2 lg:gap-16 lg:px-12 lg:py-20 xl:gap-24">
        <div className="max-w-[34rem] lg:py-6">
          <p className="label-caps text-caramel-dark">Livraria independente · desde 2026</p>

          <h1 className="mt-5 font-display text-[2.65rem] font-semibold leading-[1.05] tracking-[-0.04em] text-forest sm:text-[3.7rem] lg:text-[4.35rem]">
            Histórias que merecem ficar por perto.
          </h1>

          <p className="mt-6 max-w-[30rem] font-body text-[0.98rem] font-normal leading-relaxed text-coffee-soft sm:text-[1.05rem]">
            Uma curadoria atenta de livros para acompanhar suas pausas, conversas e próximas descobertas.
          </p>

          <div className="mt-8 flex flex-col items-start">
            <a
              href="#destaques"
              className="group inline-flex w-full items-center justify-center gap-2.5 rounded-sm bg-forest px-7 py-3.5 font-body text-xs font-semibold uppercase tracking-[0.18em] text-cream-soft transition-colors duration-300 ease-[var(--ease-cozy)] hover:bg-forest-soft focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
            >
              Explorar a coleção
              <ArrowRightIcon className="h-4 w-4 transition-transform duration-300 ease-[var(--ease-cozy)] group-hover:translate-x-1" />
            </a>

          </div>

          <ul className="mt-14 grid max-w-[32rem] grid-cols-1 gap-4 border-t border-line-strong/80 pt-6 sm:grid-cols-3 sm:gap-5">
            <li className="font-body text-[0.72rem] font-semibold uppercase leading-relaxed tracking-[0.12em] text-coffee-soft">
              Curadoria<br />
              <span className="text-forest">independente</span>
            </li>
            <li className="border-line-strong/80 font-body text-[0.72rem] font-semibold uppercase leading-relaxed tracking-[0.12em] text-coffee-soft sm:border-l sm:pl-5">
              Envio para<br />
              <span className="text-forest">todo o Brasil</span>
            </li>
            <li className="border-line-strong/80 font-body text-[0.72rem] font-semibold uppercase leading-relaxed tracking-[0.12em] text-coffee-soft sm:border-l sm:pl-5">
              Compra<br />
              <span className="text-forest">100% segura</span>
            </li>
          </ul>
        </div>

        <div className="mx-auto aspect-square w-full max-w-[620px] overflow-hidden rounded-md bg-forest/10">
          <img
            src="/Stack_of_old_books_on_20261009132000.jpg"
            alt="Pilha de livros antigos"
            className="h-full w-full object-cover"
          />
        </div>
      </div>
    </section>
  )
}
