import { useState } from 'react'
import { ArrowRightIcon } from './Icons'
import Quill from './Quill'
import newsletterService from '../api/newsletter'

/**
 * Newsletter — "Carta do Livreiro" com forte peso visual, estética de papelaria fina,
 * selo postal vintage, encarte de pergaminho e captura de e-mail de alta conversão.
 *
 * O formulário chama o endpoint de inscrição (`newsletterService.inscrever`).
 * Como o backend ainda não expõe esse recurso, a resposta 404 vira uma
 * mensagem clara de indisponibilidade — sem confirmar uma inscrição inexistente.
 */
export default function Newsletter() {
  const [enviado, setEnviado] = useState(false)
  const [email, setEmail] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState(null)

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!email.trim() || enviando) return

    setEnviando(true)
    setErro(null)
    try {
      await newsletterService.inscrever(email.trim())
      setEnviado(true)
    } catch (error) {
      setErro(
        error?.message ?? 'Não foi possível completar a inscrição agora.',
      )
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section
      id="carta-do-livreiro"
      className="relative isolate overflow-hidden bg-gradient-to-b from-[#6e431d] via-[#8c5727] to-[#4e2d11] py-20 text-cream-soft sm:py-28"
    >
      {/* Elementos decorativos de fundo */}
      <div className="pointer-events-none absolute -left-16 -top-16 opacity-10">
        <Quill width={380} />
      </div>
      <div className="pointer-events-none absolute -bottom-20 -right-20 opacity-10">
        <Quill width={420} />
      </div>

      <div className="mx-auto max-w-[1100px] px-5 sm:px-8">
        {/* Card Principal — Encarte de Carta / Papelaria de Época */}
        <div className="relative overflow-hidden rounded-md border border-cream/20 bg-cream-soft p-8 text-coffee shadow-[0_25px_60px_-15px_rgba(30,15,5,0.5)] sm:p-12 lg:p-16">
          {/* Marca d'água da pena no card interno */}
          <div className="pointer-events-none absolute -right-6 -bottom-8 text-forest/[0.04]">
            <Quill width={280} />
          </div>

          <div className="grid gap-10 lg:grid-cols-12 lg:items-center lg:gap-14">
            {/* Lado Esquerdo — O Conceito da Carta */}
            <div className="lg:col-span-7">
              {/* Selo Postal e Rótulo */}
              <div className="flex items-center gap-3">
                <span className="inline-flex items-center gap-1.5 rounded-sm border border-caramel/40 bg-cream-tint px-3 py-1 font-body text-[0.68rem] font-medium uppercase tracking-[0.22em] text-caramel-dark">
                  ✉️ Correio dos Livreiros
                </span>
                <span className="font-body text-xs text-coffee-faint">
                  Edição Mensal
                </span>
              </div>

              <h2 className="mt-4 font-display text-[2.2rem] font-light leading-tight tracking-[-0.01em] text-forest sm:text-[2.9rem]">
                Carta do Livreiro
              </h2>

              <p className="mt-2 font-display text-lg italic text-coffee-soft sm:text-xl">
                “Uma carta por mês, nada mais. Para ler com calma no domingo de manhã.”
              </p>

              <p className="mt-4 font-body text-sm font-light leading-relaxed text-coffee-soft sm:text-[0.95rem]">
                Sem spam, promoções agressivas ou algoritmos. Todo início de mês enviamos uma correspondência escrita à mão pelos nossos livreiros com reflexões literárias, recomendações fora do radar e trechos de livros que nos marcaram.
              </p>

              {/* Benefícios em destaque */}
              <div className="mt-6 grid gap-2.5 sm:grid-cols-2">
                {[
                  'Crônicas e ensaios exclusivos',
                  'Indicações secretas da curadoria',
                  'Cupom de cortesia para assinantes',
                  'Zero propagandas invasivas',
                ].map((beneficio) => (
                  <div
                    key={beneficio}
                    className="flex items-center gap-2 font-body text-xs text-coffee-soft"
                  >
                    <span className="grid h-4 w-4 shrink-0 place-items-center rounded-full bg-forest/10 text-[0.65rem] text-forest font-bold">
                      ✓
                    </span>
                    <span>{beneficio}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Lado Direito — Formulário de Captura */}
            <div className="relative rounded-md border border-line bg-cream-deep/70 p-6 shadow-inner sm:p-8 lg:col-span-5">
              {/* Carimbo Vintage */}
              <div className="absolute -right-2 -top-3 rounded-sm border border-forest/20 bg-forest/5 px-2.5 py-1 text-[0.6rem] uppercase tracking-[0.2em] text-forest font-medium -rotate-2">
                Papiro Postal
              </div>

              <h3 className="font-display text-xl font-medium text-coffee">
                Receba a próxima edição
              </h3>
              <p className="mt-1 font-body text-xs font-light text-coffee-soft">
                Junte-se a mais de 6.400 leitores que apreciam o tempo lento.
              </p>

              {enviado ? (
                <div className="mt-6 rounded-sm bg-forest/10 p-5 text-center">
                  <span className="text-2xl">📬</span>
                  <p className="mt-2 font-display text-lg font-medium text-forest">
                    Seja bem-vindo à nossa correspondência!
                  </p>
                  <p className="mt-1 font-body text-xs text-coffee-soft">
                    Enviamos um e-mail de confirmação. Verifique sua caixa de entrada.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="mt-5 space-y-3">
                  <div>
                    <label htmlFor="newsletter-email" className="sr-only">
                      Seu melhor e-mail
                    </label>
                    <input
                      id="newsletter-email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="seu.email@exemplo.com"
                      className="w-full rounded-sm border border-line-strong bg-cream-soft px-4 py-3.5 font-body text-sm text-coffee placeholder:text-coffee-faint transition-colors duration-300 focus:border-forest focus:outline-none"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={enviando}
                    className="group flex w-full items-center justify-center gap-2 rounded-sm bg-forest py-3.5 font-body text-xs font-medium uppercase tracking-[0.2em] text-cream-soft shadow-md transition-all duration-300 hover:bg-forest-soft hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-70 focus-visible:outline focus-visible:outline-2 focus-visible:outline-forest"
                  >
                    <span>{enviando ? 'Enviando…' : 'Assinar a Carta'}</span>
                    <ArrowRightIcon className="h-3.5 w-3.5 transition-transform duration-300 group-hover:translate-x-1" />
                  </button>

                  {erro && (
                    <p className="rounded-sm bg-caramel-dark/10 px-3 py-2 text-center font-body text-[0.72rem] text-caramel-dark">
                      {erro}
                    </p>
                  )}

                  <p className="text-center font-body text-[0.68rem] text-coffee-faint">
                    Promessa Papiro: Cancele a assinatura quando quiser com 1 clique.
                  </p>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
