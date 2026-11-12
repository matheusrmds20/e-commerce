import { useEffect, useRef } from 'react'
import { CloseIcon } from './Icons'

/**
 * Diálogo de confirmação — substitui o `window.confirm` do navegador.
 *
 * Rende com o mesmo idioma dos demais modais do Papiro (overlay, cantos,
 * tipografia) e fecha com ESC. O foco inicial vai ao botão "confirmar" para
 * valores de risco baixo (o usuário já clicou em "Excluir"); a opção menos
 * agressiva ("cancelar") segue à esquerda.
 *
 * Props:
 * - aberto: controla visibilidade (se `false`, não renderiza).
 * - titulo: título do diálogo.
 * - mensagem: explica o que será feito.
 * - confirmarTexto / cancelarTexto: rótulos dos botões.
 * - perigo: `true` deixa o botão de confirmar no tom de erro (exclusões).
 * - onConfirmar / onCancelar: callbacks. `onConfirmar` pode ser async — nesse
 *   caso o botão mostra estado de carregamento.
 */
export default function ConfirmDialog({
  aberto,
  titulo = 'Confirmar ação',
  mensagem,
  confirmarTexto = 'Confirmar',
  cancelarTexto = 'Cancelar',
  perigo = false,
  onConfirmar,
  onCancelar,
}) {
  const botaoConfirmarRef = useRef(null)

  // Focus no botão de confirmar e fecha com ESC.
  useEffect(() => {
    if (!aberto) return
    botaoConfirmarRef.current?.focus()

    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && onCancelar) onCancelar()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [aberto, onCancelar])

  if (!aberto) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-titulo"
      aria-describedby="confirm-dialog-mensagem"
      className="fixed inset-0 z-[90] flex items-center justify-center p-4 bg-coffee/60 backdrop-blur-sm"
      onClick={(e) => {
        // Clique no backdrop = cancelar.
        if (e.target === e.currentTarget && onCancelar) onCancelar()
      }}
    >
      <div className="w-full max-w-md rounded-md border border-line bg-cream-soft shadow-xl overflow-hidden">
        {/* Cabeçalho */}
        <div className="flex items-center justify-between border-b border-line bg-cream px-6 py-4">
          <h2
            id="confirm-dialog-titulo"
            className="font-display text-xl font-normal text-coffee"
          >
            {titulo}
          </h2>
          <button
            type="button"
            onClick={onCancelar}
            aria-label="Fechar"
            className="rounded-full p-2 text-coffee-soft hover:bg-cream-deep hover:text-coffee transition-colors"
          >
            <CloseIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Mensagem */}
        <div className="px-6 py-5">
          <p
            id="confirm-dialog-mensagem"
            className="font-body text-sm leading-relaxed text-coffee-soft"
          >
            {mensagem}
          </p>
        </div>

        {/* Ações */}
        <div className="flex items-center justify-end gap-3 border-t border-line px-6 py-4 bg-cream/50">
          <button
            type="button"
            onClick={onCancelar}
            className="rounded-sm border border-line-strong px-4 py-2.5 font-body text-xs font-semibold uppercase tracking-wider text-coffee-soft hover:bg-cream-deep transition-colors"
          >
            {cancelarTexto}
          </button>
          <button
            type="button"
            ref={botaoConfirmarRef}
            onClick={onConfirmar}
            className={`rounded-sm px-6 py-2.5 font-body text-xs font-semibold uppercase tracking-wider text-cream-soft transition-colors shadow-sm ${
              perigo
                ? 'bg-[#a4533f] hover:bg-[#823d2d]'
                : 'bg-forest hover:bg-forest-soft'
            }`}
          >
            {confirmarTexto}
          </button>
        </div>
      </div>
    </div>
  )
}