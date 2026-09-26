import { useEffect, useRef } from 'react'

/**
 * Confirmacao — diálogo de confirmação em modal, no estilo papel do projeto.
 * Usado antes de ações destrutivas (excluir endereço, cartão...).
 */
export default function Confirmacao({
  aberto,
  titulo = 'Confirmar ação',
  descricao,
  textoConfirmar = 'Excluir',
  textoCancelar = 'Cancelar',
  ocupado = false,
  erro = null,
  onConfirmar,
  onCancelar,
}) {
  const botaoCancelarRef = useRef(null)

  // Foco no botão seguro ao abrir e fecha com Esc.
  useEffect(() => {
    if (!aberto) return
    botaoCancelarRef.current?.focus()
    const aoTeclar = (event) => {
      if (event.key === 'Escape') onCancelar?.()
    }
    window.addEventListener('keydown', aoTeclar)
    return () => window.removeEventListener('keydown', aoTeclar)
  }, [aberto, onCancelar])

  if (!aberto) return null

  return (
    <div
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="confirmacao-titulo"
      onClick={onCancelar}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-coffee/60 backdrop-blur-sm"
    >
      <div
        onClick={(event) => event.stopPropagation()}
        className="w-full max-w-sm rounded-md bg-cream-soft p-8 text-center shadow-[0_18px_50px_-20px_rgba(75,54,33,0.35)] ring-1 ring-line"
      >
        <h2
          id="confirmacao-titulo"
          className="font-display text-2xl text-coffee"
        >
          {titulo}
        </h2>

        <p className="mt-3 font-body text-[0.92rem] leading-relaxed text-coffee-soft">
          {descricao}
        </p>

        {erro && (
          <p
            role="alert"
            className="mt-4 rounded-sm border border-[#a4533f]/30 bg-[#a4533f]/[0.06] px-3 py-2 font-body text-[0.8rem] font-medium text-[#a4533f]"
          >
            {erro.message}
          </p>
        )}

        <div className="mt-8 flex justify-center gap-3">
          <button
            type="button"
            ref={botaoCancelarRef}
            onClick={onCancelar}
            className="rounded-sm border border-line-strong px-6 py-3 font-body text-[0.7rem] font-semibold uppercase tracking-[0.2em] text-coffee-soft transition-colors duration-300 hover:border-coffee-soft"
          >
            {textoCancelar}
          </button>

          <button
            type="button"
            disabled={ocupado}
            onClick={onConfirmar}
            className="rounded-sm bg-[#a4533f] px-6 py-3 font-body text-[0.7rem] font-semibold uppercase tracking-[0.2em] text-cream-soft shadow-md transition-all duration-300 hover:bg-[#8f4636] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {ocupado ? 'Excluindo…' : textoConfirmar}
          </button>
        </div>
      </div>
    </div>
  )
}
