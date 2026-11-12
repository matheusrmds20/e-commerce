import { useCallback, useMemo, useState } from 'react'
import ToastContext from './toast-context'
import { CloseIcon } from '../components/Icons'

const VARIANTES = {
  sucesso: {
    borda: 'border-forest/40',
    icone: 'h-2 w-2 bg-forest',
  },
  erro: {
    borda: 'border-[#a4533f]/40',
    icone: 'h-2 w-2 bg-[#a4533f]',
  },
  informacao: {
    borda: 'border-gold/40',
    icone: 'h-2 w-2 bg-gold-dark',
  },
}

const LADO = {
  sucesso: 'Sucesso',
  erro: 'Atenção',
  informacao: 'Saiba',
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const remover = useCallback((id) => {
    setToasts((atual) => atual.filter((t) => t.id !== id))
  }, [])

  /** Exibe uma notificação transitória. `duracao` em ms; 0 = não fecha sozinho. */
  const showToast = useCallback(
    (mensagem, { tipo = 'informacao', duracao = 3200 } = {}) => {
      const id = Date.now() + Math.random().toString(36).slice(2)
      setToasts((atual) => [...atual, { id, mensagem, tipo }])
      if (duracao > 0) {
        window.setTimeout(() => remover(id), duracao)
      }
    },
    [remover],
  )

  const contextValue = useMemo(
    () => ({
      toast: showToast,
      sucesso: (mensagem, opcoes) =>
        showToast(mensagem, { tipo: 'sucesso', ...opcoes }),
      erro: (mensagem, opcoes) =>
        showToast(mensagem, { tipo: 'erro', ...opcoes }),
      informacao: (mensagem, opcoes) =>
        showToast(mensagem, { tipo: 'informacao', ...opcoes }),
    }),
    [showToast],
  )

  return (
    <ToastContext.Provider value={contextValue}>
      {children}

      {/* Região de notificações: confirmar em tela cheia e anunciar para leitores */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="pointer-events-none fixed right-4 top-4 z-[100] flex w-[min(92vw,22rem)] flex-col gap-2 sm:top-5 sm:right-5"
      >
        {toasts.map((t) => {
          const classe = VARIANTES[t.tipo] || VARIANTES.informacao
          return (
            <div
              key={t.id}
              role="status"
              className={`pointer-events-auto flex items-start gap-3 rounded-md border bg-cream-soft px-4 py-3 shadow-md ${classe.borda}`}
            >
              <span
                aria-hidden="true"
                className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${classe.icone}`}
              />
              <p className="flex-1 font-body text-sm text-coffee">
                <span className="sr-only">{LADO[t.tipo]}: </span>
                {t.mensagem}
              </p>
              <button
                type="button"
                onClick={() => remover(t.id)}
                aria-label="Dispensar notificação"
                className="shrink-0 rounded-full p-1 text-coffee-faint hover:bg-cream-deep hover:text-coffee transition-colors"
              >
                <CloseIcon className="h-4 w-4" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}