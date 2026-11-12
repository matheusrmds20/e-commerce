import { useState } from 'react'
import { ZoomIcon } from './Icons'
import { atributosCapa } from '../lib/imagemCapa'


export default function GaleriaLivro({ imagens, titulo }) {
 const [ativa, setAtiva] = useState(0)
 const [zoom, setZoom] = useState(false)

 return (
 <div>
 {/* Palco */}
 <div
 onMouseEnter={() => setZoom(true)}
 onMouseLeave={() => setZoom(false)}
 className="relative flex aspect-square items-center justify-center overflow-hidden rounded-md bg-cream-tint/70 ring-1 ring-line"
 >
 <img
 src={imagens[ativa]}
 alt={`Capa de ${titulo}`}
 className={`h-[78%] w-auto rounded-sm object-contain shadow-cover transition-transform duration-700 ease-[var(--ease-cozy)] ${
 zoom ? 'scale-[1.06]' : 'scale-100'
 }`}
 {...atributosCapa(imagens[ativa], { larguraExibida: 520, ajuste: 'contain', prioridade: true })}
 />

 <button
 type="button"
 aria-label="Ampliar imagem"
 className="absolute bottom-4 right-4 grid h-10 w-10 place-items-center rounded-sm bg-cream-soft/90 text-coffee-soft transition-colors duration-150 hover:text-gold focus-visible:outline-offset-[-2px] "
 >
 <ZoomIcon />
 </button>
 </div>

 {/* Miniaturas */}
 <div className="mt-4 grid grid-cols-4 gap-3">
 {imagens.map((imagem, i) => (
 <button
 key={i}
 type="button"
 onClick={() => setAtiva(i)}
 aria-label={`Ver imagem ${i + 1}`}
 aria-current={ativa === i}
 className={`flex aspect-square items-center justify-center overflow-hidden rounded-sm bg-cream-tint/70 ring-1 transition-[box-shadow] duration-150 ease-[var(--ease-cozy)] focus-visible:outline-offset-[-2px] ${
 ativa === i
 ? 'ring-2 ring-gold'
 : 'ring-line hover:ring-line-strong'
 }`}
 >
 <img
 src={imagem}
 alt=""
 className="h-[80%] w-auto object-contain"
 {...atributosCapa(imagem, { larguraExibida: 120, ajuste: 'contain' })}
 />
 </button>
 ))}
 </div>
 </div>
 )
}
