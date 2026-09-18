import { useState } from 'react'
import {
  GlobeIcon,
  HeartIcon,
  LockIcon,
  MedalIcon,
  ShareIcon,
} from './Icons'

const FORMATOS = [
  { id: 'capa-dura', rotulo: 'Capa dura' },
  { id: 'brochura', rotulo: 'Brochura' },
  { id: 'ebook', rotulo: 'E-book' },
]

const GARANTIAS = [
  { Icone: LockIcon, titulo: 'Compra', sub: 'Segura' },
  { Icone: GlobeIcon, titulo: 'Envio', sub: 'Mundial' },
  { Icone: MedalIcon, titulo: 'Satisfação', sub: 'Garantida' },
]

/**
 * PainelCompra — preço, seleção de formato, CTA e selos.
 *
 * `preco`/`precoAntigo` já chegam formatados em BRL. O CTA `onAdicionar`
 * adiciona o produto real à sacola; `stockQty` controla o estado esgotado.
 */
export default function PainelCompra({
  preco,
  precoAntigo,
  desconto,
  stockQty = null,
  onAdicionar,
  feedback = null,
}) {
  const [formato, setFormato] = useState('capa-dura')
  const [cep, setCep] = useState('')

  const esgotado = stockQty !== null && stockQty <= 0

  return (
    <div>
      {/* Preço */}
      <div className="flex flex-wrap items-baseline gap-3">
        <span className="font-display text-[2.75rem] leading-none font-semibold text-forest">
          {preco}
        </span>
        {precoAntigo && (
          <span className="font-body text-base font-normal text-coffee-faint line-through">
            {precoAntigo}
          </span>
        )}
      </div>
      {desconto && (
        <p className="mt-2 font-body text-[0.88rem] font-medium text-caramel-dark">
          Você economiza {desconto}
        </p>
      )}

      {/* Formato */}
      <fieldset className="mt-7">
        <legend className="font-body text-sm font-semibold text-coffee">
          Formato
        </legend>

        <div className="mt-3 flex flex-wrap gap-3">
          {FORMATOS.map((item) => (
            <label
              key={item.id}
              className={`flex cursor-pointer items-center gap-3 rounded-sm border px-4 py-3 transition-colors duration-300 ease-[var(--ease-cozy)] has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-gold ${
                formato === item.id
                  ? 'border-forest bg-cream-tint font-medium shadow-sm'
                  : 'border-line-strong hover:border-coffee-soft'
              }`}
            >
              <input
                type="radio"
                name="formato"
                value={item.id}
                checked={formato === item.id}
                onChange={() => setFormato(item.id)}
                className="sr-only"
              />
              <span className="font-body text-[0.88rem] text-coffee-soft">
                {item.rotulo}
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      <p className="mt-6 font-body text-[0.92rem] font-normal text-coffee-soft">
        {esgotado
          ? 'Indisponível no momento.'
          : `Em estoque${stockQty !== null ? ` (${stockQty} un.)` : ''}. Enviamos em até 24 horas com embrulho artesanal.`}
      </p>

      {feedback && (
        <p
          className={`mt-4 font-body text-[0.85rem] font-medium ${
            feedback.tipo === 'erro' ? 'text-caramel-dark' : 'text-forest'
          }`}
        >
          {feedback.texto}
        </p>
      )}

      {/* Ações */}
      <button
        type="button"
        onClick={onAdicionar}
        disabled={esgotado}
        className="mt-5 w-full rounded-sm bg-forest py-4 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft shadow-md transition-all duration-300 ease-[var(--ease-cozy)] hover:bg-forest-soft hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:cursor-not-allowed disabled:opacity-50"
      >
        {esgotado ? 'Esgotado' : 'Adicionar à sacola'}
      </button>

      <div className="mt-4 flex items-center justify-center gap-8">
        <button
          type="button"
          className="inline-flex items-center gap-2 font-body text-[0.88rem] font-medium text-coffee-soft transition-colors duration-300 hover:text-gold"
        >
          <HeartIcon /> Adicionar aos desejos
        </button>
        <span className="h-4 w-px bg-line" />
        <button
          type="button"
          className="inline-flex items-center gap-2 font-body text-[0.88rem] font-medium text-coffee-soft transition-colors duration-300 hover:text-gold"
        >
          <ShareIcon /> Compartilhar
        </button>
      </div>

      <hr className="mt-7 border-line" />

      {/* Frete */}
      <div className="mt-6">
        <h3 className="font-body text-sm font-semibold text-coffee">
          Envio e entrega
        </h3>

        <div className="mt-3 flex items-center gap-3">
          <label htmlFor="cep" className="font-body text-sm font-medium text-coffee-soft">
            CEP
          </label>
          <input
            id="cep"
            value={cep}
            onChange={(event) => setCep(event.target.value)}
            inputMode="numeric"
            placeholder="00000-000"
            className="min-w-0 flex-1 rounded-sm border border-line-strong bg-cream-soft px-3 py-2.5 font-body text-sm text-coffee placeholder:text-coffee-faint focus:border-forest focus:outline-none"
          />
          <button
            type="button"
            className="shrink-0 rounded-sm border border-line-strong bg-cream-tint px-5 py-2.5 font-body text-xs font-semibold uppercase tracking-wider text-coffee transition-colors duration-300 hover:border-forest hover:text-forest"
          >
            Calcular
          </button>
        </div>

        <p className="mt-3 font-body text-[0.82rem] font-normal text-coffee-soft">
          Frete padrão grátis em pedidos acima de R$ 150.
        </p>
      </div>

      {/* Selos */}
      <div className="mt-7 grid grid-cols-3 gap-3">
        {GARANTIAS.map(({ Icone, titulo, sub }) => (
          <div
            key={titulo}
            className="flex items-center gap-2.5 rounded-sm border border-line bg-cream-tint/40 px-3 py-3"
          >
            <Icone className="h-5 w-5 shrink-0 text-coffee-soft" />
            <span className="font-body text-[0.72rem] font-medium leading-tight text-coffee-soft">
              {titulo}
              <br />
              {sub}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
