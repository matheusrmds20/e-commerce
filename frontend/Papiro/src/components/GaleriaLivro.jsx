import { useState } from 'react'
import { ZoomIcon } from './Icons'

/**
 * GaleriaLivro — imagem principal sobre fundo creme + miniaturas.
 */
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
          className={`h-[78%] w-auto rounded-sm object-contain shadow-[0_18px_40px_-20px_rgba(75,54,33,0.55)] transition-transform duration-700 ease-[var(--ease-cozy)] ${
            zoom ? 'scale-[1.06]' : 'scale-100'
          }`}
        />

        <button
          type="button"
          aria-label="Ampliar imagem"
          className="absolute bottom-4 right-4 grid h-10 w-10 place-items-center rounded-sm bg-cream-soft/90 text-coffee-soft transition-colors duration-300 hover:text-gold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
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
            className={`flex aspect-square items-center justify-center overflow-hidden rounded-sm bg-cream-tint/70 ring-1 transition-all duration-300 ease-[var(--ease-cozy)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold ${
              ativa === i
                ? 'ring-2 ring-gold'
                : 'ring-line hover:ring-line-strong'
            }`}
          >
            <img
              src={imagem}
              alt=""
              className="h-[80%] w-auto object-contain"
              loading="lazy"
            />
          </button>
        ))}
      </div>
    </div>
  )
}
