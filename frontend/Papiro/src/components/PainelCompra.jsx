import { HeartIcon } from './Icons'


export default function PainelCompra({
 preco,
 precoAntigo,
 desconto,
 stockQty = null,
 onAdicionar,
 feedback = null,
 onAdicionarDesejos,
 nosDesejos = false,
 feedbackDesejos = null,
}) {
 const esgotado = stockQty !== null && stockQty <= 0

 return (
 <div>
 {/* Preço */}
 <div className="flex flex-wrap items-baseline gap-3">
 <span className="font-display text-3xl leading-none font-semibold text-forest">
 {preco}
 </span>
 {precoAntigo && (
 <span className="font-body text-base font-normal text-coffee-faint line-through">
 {precoAntigo}
 </span>
 )}
 </div>
 {desconto && (
 <p className="mt-2 font-body text-xs font-medium text-caramel-dark">
 Você economiza {desconto}
 </p>
 )}

 <p className="mt-6 font-body text-sm font-normal text-coffee-soft">
 {esgotado
 ? 'Indisponível no momento.'
 : `Em estoque${stockQty !== null ? ` (${stockQty} un.)` : ''}. Enviamos em até 24 horas com embrulho artesanal.`}
 </p>

 {feedback && (
 <p
 className={`mt-4 font-body text-xs font-medium ${
 feedback.tipo === 'erro' ? 'text-caramel-dark' : 'text-forest'
 }`}
 >
 {feedback.texto}
 </p>
 )}

 {feedbackDesejos && (
 <p
 className={`mt-2 font-body text-xs font-medium ${
 feedbackDesejos.tipo === 'erro'
 ? 'text-caramel-dark'
 : 'text-forest'
 }`}
 >
 {feedbackDesejos.texto}
 </p>
 )}

 {/* Ações */}
 <button
 type="button"
 data-testid="btn-add-carrinho"
 onClick={onAdicionar}
 disabled={esgotado}
 className="anel-foco-claro mt-5 w-full rounded-sm bg-forest py-4 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft shadow-md transition-colors duration-150 ease-[var(--ease-cozy)] hover:bg-forest-soft hover:shadow-lg focus-visible:outline-gold disabled:cursor-not-allowed disabled:opacity-50"
 >
 {esgotado ? 'Esgotado' : 'Adicionar à sacola'}
 </button>

 <div className="mt-4 flex items-center justify-center">
 <button
 type="button"
 data-testid="btn-wishlist"
 onClick={onAdicionarDesejos}
 aria-pressed={nosDesejos}
 className={`inline-flex items-center gap-2 font-body text-xs font-medium transition-colors duration-150 hover:text-gold ${
 nosDesejos ? 'text-caramel-dark' : 'text-coffee-soft'
 }`}
 >
 <HeartIcon filled={nosDesejos} />{' '}
 {nosDesejos ? 'Remover dos desejos' : 'Adicionar aos desejos'}
 </button>
 </div>
 </div>
 )
}
