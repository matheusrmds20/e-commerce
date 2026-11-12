import { useNavigate } from 'react-router-dom'


export default function ResumoCarrinho({ subtotal, total, formatarPreco }) {
 const navigate = useNavigate()

 return (
 <aside className="rounded-md border border-line bg-cream-soft p-7 lg:sticky lg:top-24">
 <h2 className="font-display text-2xl font-normal text-coffee">
 Resumo da sacola
 </h2>

 <dl className="mt-7 flex flex-col gap-4">
 <div className="border-t border-line pt-4">
 <div className="flex items-baseline justify-between gap-4">
 <dt className="font-body text-base font-semibold text-coffee">
 Total
 </dt>
 <dd className="font-display text-2xl font-semibold text-forest">
 {formatarPreco(total)}
 </dd>
 </div>
 </div>
 </dl>

 <button
 type="button"
 onClick={() => navigate('/checkout')}
 className="anel-foco-claro mt-7 w-full rounded-sm bg-forest py-4 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft shadow-md transition-colors duration-150 ease-[var(--ease-cozy)] hover:bg-forest-soft hover:shadow-lg "
 >
 Finalizar compra
 </button>

 <p className="mt-4 text-center font-body text-2xs font-normal text-coffee-faint">
 Subtotal de {formatarPreco(subtotal)}.
 </p>
 </aside>
 )
}
