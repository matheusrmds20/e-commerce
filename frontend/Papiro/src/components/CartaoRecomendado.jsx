
import { atributosCapa } from '../lib/imagemCapa'
export default function CartaoRecomendado({ item, formatarPreco, onAdicionar }) {
 return (
 <article className="group flex flex-col rounded-md border border-line bg-cream-soft p-4 transition-colors duration-500 ease-[var(--ease-cozy)] hover:border-line-strong">
 <div className="flex h-[230px] items-center justify-center overflow-hidden rounded-sm bg-cream-tint/80 sm:h-[250px]">
 <img
 src={item.imagem}
 alt={`Capa de ${item.titulo}`}
 className="h-[86%] w-auto object-contain shadow-cover transition-transform duration-700 ease-[var(--ease-cozy)] group-hover:scale-[1.05]"
 {...atributosCapa(item.imagem, { larguraExibida: 200, ajuste: 'contain' })}
 />
 </div>

 <h3 className="mt-5 font-display text-xl font-normal leading-snug text-coffee">
 <a
 href="#"
 onClick={(event) => event.preventDefault()}
 className="transition-colors duration-150 hover:text-gold"
 >
 {item.titulo}
 </a>
 </h3>

 <p className="mt-2 font-body text-base font-semibold text-forest">
 {formatarPreco(item.preco)}
 </p>

 <button
 type="button"
 onClick={() => onAdicionar(item)}
 className="mt-4 w-full rounded-sm bg-cream-tint py-3 font-body text-xs font-semibold tracking-wider text-coffee transition-colors duration-150 ease-[var(--ease-cozy)] hover:bg-gold hover:text-cream-soft "
 >
 Adicionar à sacola
 </button>
 </article>
 )
}
