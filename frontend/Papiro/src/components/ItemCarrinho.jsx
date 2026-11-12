import Quantidade from './Quantidade'
import { CloseIcon } from './Icons'
import { atributosCapa } from '../lib/imagemCapa'


export default function ItemCarrinho({
 item,
 onQuantidade,
 onRemover,
 formatarPreco,
}) {
 const subtotal = item.preco * item.quantidade

 return (
 <li
 className="group border-b border-line py-6"
 data-testid={`cart-item-${item.id}`}
 >
 <div className="grid grid-cols-[80px_1fr_auto] items-center gap-4 sm:grid-cols-[96px_1fr_auto_auto] sm:gap-6">
 {/* Capa */}
 <a
 href="#"
 onClick={(event) => event.preventDefault()}
 className="block "
 >
 <img
 src={item.imagem}
 alt={`Capa de ${item.titulo}`}
 className="h-[110px] w-full rounded-sm object-contain shadow-cover sm:h-[130px]"
 {...atributosCapa(item.imagem, { larguraExibida: 130, ajuste: 'contain' })}
 />
 </a>

 {/* Título e autor */}
 <div className="min-w-0">
 <h3 className="font-display text-xl font-medium leading-snug tracking-[0.01em] text-coffee sm:text-2xl">
 <a
 href="#"
 onClick={(event) => event.preventDefault()}
 className="transition-colors duration-150 hover:text-gold"
 >
 {item.titulo}
 </a>
 </h3>

 <p className="mt-1 font-body text-sm font-medium text-coffee-soft">
 {item.autor}
 </p>

 {/* Preço unitário — só no mobile */}
 <p className="mt-2 font-body text-sm font-normal text-coffee-faint sm:hidden">
 {formatarPreco(item.preco)} cada
 </p>

 <button
 type="button"
 data-testid="btn-remover"
 onClick={() => onRemover(item.id)}
 className="mt-2.5 inline-flex items-center gap-1.5 font-body text-2xs font-semibold uppercase tracking-[0.14em] text-coffee-faint transition-colors duration-150 hover:text-caramel-dark"
 >
 <CloseIcon className="h-3.5 w-3.5" />
 Remover
 </button>
 </div>

 {/* Quantidade */}
 <div className="justify-self-end sm:justify-self-start">
 <span className="sr-only">Quantidade de {item.titulo}</span>
 <Quantidade
 valor={item.quantidade}
 max={item.stockQty > 0 ? item.stockQty : 99}
 onChange={(valor) => onQuantidade(item.id, valor)}
 />
 </div>

 {/* Subtotal */}
 <p className="col-span-3 text-right font-body text-lg font-semibold text-coffee sm:col-span-1 sm:min-w-[92px] sm:text-xl">
 {formatarPreco(subtotal)}
 </p>
 </div>
 </li>
 )
}
